SP #026: Initialization Behavior in Slang 2026
==============================================

We propose to streamline and clarify the semantics and language rules around initialization/construction of values in the Slang 2026 language version.

This change would simplify the task of learning and understanding the behavior of the language, but comes at the cost of dropping some inherited language behaviors, and losing compatibility with some idioms that are currently commonplace in Slang codebases.

Status
------

Status: Design Review

Implementation: ---

Author: Theresa Foley, Yong He

Reviewer: ---

Background
----------

Slang currently has a combination of various constructs and behaviors related to initialization, some inherited and some invented.
It can be difficult for a user of the language - even one who is an experienced programmer - to determine which behaviors apply in which cases.
Indeed, the authors of this proposal are sometimes surprised to hear from users about how Slang compiled their code.

### Constructing a Value

When a user wants to create an instance of a `struct` type `Thing`, they have three main ways that they can accomplish the task:

#### Constructor Calls

A *constructor call* involves calling a type like a function, as in `Thing()`, `Thing(a)` or `Thing(a,b,c)`

A constructor call with zero arguments (e.g., `Thing()`) or with two or more arguments (e.g., `Thing(a,b)`) is compiled by looking up the constructor (`__init`) declarations on `Thing` that are visible in the current scope and checking a call to the resulting overload set.

A constructor call with exactly one argument (e.g., `Thing(a)`) is treated as an alias for an explicit cast `(Thing) a`.

#### Explicit Casts

An explicit cast like `(Thing) a` is compiled by checking for various built-in type conversion rules in the compiler (e.g., it will turn into a no-op if `a` is an expression of type `Thing`).
If none of the built-in rules applies, then it falls back to lookup constructor declarations on thing and checking a call to them (just like the constructor-call syntax would for the cases with other numbers of arguments).

#### Initializer Lists

A C-style *initializer list* like `{}` or `{a, b, c}`, can only be used in a context where the initializer-list expression will be coerced to some type expected in the context (usually because it appears as the initial-value expression for a variable of type `Thing`).

If a type is a built-in scalar, vector, matrix, or array type, or if the type is determined by the Slang compiler to be "C-style", then it will use traditional C-style initializer-list checking, where e.g., a `struct` with fields `{ float4 x; int3 y; }` can be initialized using an initializer list with seven values and no nesting: `{a, b, c, d, e, f, g, h}`.
This kind of initializer-list processing requires the compiler to operate at the level of the fields of a type, and bypasses concepts like "constructors."
If there aren't enough expressions in the initializer list to fully initialize a value of the desired type, the compiler *default initializes* the remainder.

A `struct` type qualifies as C-style if all of its fields are accessible to any code that can access the type, it has no user-defined constructors, and has no concrete base types.
(There may be other criteria, but this author is unsure)

If a type is not considered C-style, then coercion of an initializer list (as in `(Thing){a,b,c}`) is *mostly* equivalent to a constructor call like `Thing(a,b,c)`.
(The author is genuinely unsure if a singleton initializer list like `(Thing){a}` will get checked as a cast `(Thing)a` just like the constructor call `Thing(a)` would, or if it bypasses that special case)

The "mostly* in the preceding paragraph reflects the fact that if a suitable constructor overload is not found for the argument list consisting of the elements of the initializer list, then the overloads will be tried with a more aggressive strategy where any constructor parameters that are of a *default-initializable* type (one that has a zero-argument constructor) are treated as if they have a default argument value.
(Again, the author needs somebody to tell it whether this is accurate to what the compiler implements today)

### Declaring a Variable (Local or Global)

When user code declares an ordinary variable (a local, function- or type-scope `static`, or a non-shader-parameter global/`namespace`-scope variable), it may include an explicit initial-value expression:

    Thing t = someExpression;
    // or:
    var t = someExpression;
    // or:
    let t = someExpression;

In this case, the variable is *fully initialized* starting at the point of declaration.

When a variable is declared *without* an explicit initial-value expression:

    Thing t;

then this variable is either *fully uninitialized* starting at the point of the declaration (and must be initialized before use, or else the code is invalid), or it might be *fully initialized*.
If there is a zero-argument constructor for `Thing` that is in scope at the point of declaration, then the `Thing t;` declaration is equivalent to:

    Thing t = Thing();

### Constructors

The constructors of a user-defined type `Thing` may come from a few places:

* The explicit `__init` declarations in type `Thing`

* Explicit `__init` declarations in `extension`s of `Thing`

* A compiler-synthesized "primary" constructor for `Thing`

* Constructors on an `interface` `IWhatever` that `Thing` is known/declared to conform to.

The body of a user-defined constructor largely behaves like a function where the `this` parameter is an `out` parameter.
In principle the same validation that makes sure functions fully initialize their `out` parameters will also validate that a constructor fully initializes `this`.

Constructors that are introduced via an `interface` conformance may cause the compiler to synthesize an implementation of a matching constructor to satisfy the interface conformance, even if the type does not have any explicit `__init` declarations.

The compiler will only synthesize a primary constructor for a type if it doesn't have any explicit `__init` declarations directly in its body.
It also won't synthesize a constructor for a type that has a concrete base type.
The synthesized primary constructor for `Thing` will have a parameter for each of the fields of `Thing`, and those parameters will have default argument-value expressions if the corresponding field of `Thing` either (1) has an initial-value expression or (2) is of a type that has a zero-argument constructor.

Many built-in types (such as basic scalars and vectors) declare explicit constructors, but do not define a zero-argument constructor, so fields of these types must be explicitly initialized to be able to be defaulted as part of a synthesized constructor, but notably they *are* able to be default-initialized as part of the `{}` initializer list syntax.

### Bypassing Constructors Entirely

Suppose we have a `struct` like the following, with an explicit user-defined constructor:

    public struct Basis
    {
        public float3 tangentU;
        public float3 tangentV;
        public float3 normal;

        __init(float3 tangentU, float3 tangentV)
        {
            this.tangentU = tangentU;
            this.tangentV = tangentV;
            this.normal = cross(tangentU, tangentV);
        }
    }

The intention of this type's constructor is clear: it wants to be setting up an orthonormal basis.

If a user of the module that defines `Basis` declares a variable like:

    Basis b;

then this variable will start out fully uninitialized, because the type does not receive a synthesized default constructor.
The user can then go on to write to the individual fields, one-by-one:

    Basis b;
    b.tangentU = u;
    b.tangentV = v;
    b.normal = u - v; // close enough, right?

Per the C-like language rules inherited by Slang, the variable `b` is *fully initialized* after that sequence of statements, even though no constructor for `Basis` ever ran.
Even if the `Basis` type left its fields `public` and mutable, its constructor was still intended to guide programmers toward correct usage, but it is unable to help the hapless user in this case, because nothing stopped the user from bypassing the constructor.

Things get even more confusing if the creator of `Basis` revises their type so that one or more of the fields are replaced with `property` declarations:

    public struct Basis
    {
        public float3 tangentU;
        public float3 tangentV;

        public property float3 normal
        {
            get { return _normal; }
            set(newValue) { _normal = newValue; }
        }

        internal float3 _normal;

        __init(float3 tangentU, float3 tangentV)
        {
            this.tangentU = tangentU;
            this.tangentV = tangentV;
            this.normal = cross(tangentU, tangentV);
        }
    }

As far as the creator of `Basis` can see, they haven't changed the public API of their type in a way that should break source compatibility.
But in practice the user code from before will now give an error:

    Basis b;
    b.tangentU = u;
    b.tangentV = v;
    b.normal = u - v; // ERROR: can't invoke `Basis.normal.set` on value `b` that is not fully initialized

The `set` accessor for `normal` takes its `this` parameter as an `inout Basis`, and an `inout` parameter requires a fully-initialized value as input (and is required to yield a fully-initialized value as output).

### Summary

We hope that it is apparent that Slang currently has too many different-but-overlapping ways to express initialization, with too many nuances of semantics for users to keep track of.
Developers who build and maintain shader code libraries on a much larger scale that the toy `Basis` example need to deal with the ways that a small change in one type declaration may lead to unexpected errors in a superficially unrelated part of a user's codebase.

Related Work
------------

### C++

C++ has many of the same issues that Slang faces (and this makes sense, as contributors to Slang often find themselves pressured to make the language more and more like C++).
Unlike Slang, though, C++ implements a far-reaching restriction, so that most variable declarations of the form `Thing t;` are only valid if `Thing` has a default constructor, and produce an error diagnostic otherwise.

The C++ approach is expedient in many ways, but in practice it leads to most types in the standard library (and typical user codebases) having default constructors, even when there is no truly reasonable default value for those types.
Most C++ types have some kind of "initialized" state that represents being de facto empty, invalid or, well, *uninitialized*.
A `std::unique_ptr` may help with managing object lifetimes, but it can still be just as null as any other pointer, and crash your program just the same.

### Rust

Rust generally forces developers to fully initialize any variable/value before they use it.
A variable declaration without an initializer introduces an uninitialized variable.

Rust has a few utilities that help to make the requirement to fully initialize things ahead of time less onerous:

* The `Default` trait allows types to easily opt into having a reasonable/safe default value that can be used in places where a variable might otherwise be left uninitialized. Note that the Rust compiler does not auto-magically initialize variables that are declared without an initializer just because their type conforms to `Default`. Furthermore, the `Default` trait exposes a special-case factor function that is separate from the ordinary means of initializing values.

* The `MaybeUninit<T>` type represents a storage location sufficient to hold a value of type `T` that might or might not contain such a value. When accessing that location, code can use `assume_init()` if they know the location has been initialized already, and may use `MaybeUninit::new` to help store a value of type `T` into the location. This idiom allows programmers to manipulate things like large arrays without forcing up-front initialization (which may even be impossible, depending on `T`), but forces them to be explicit about when and where they are making assumptions.

Rust's model for construction of values is simple enough that the notion of "constructor" is basically inapplicable.
Any given user-defined type has one and only one "constructor," which requires all of its members/values to be specified explicitly; everything else is just factory functions layered on top of that.
As such, there is no directly equivalent in Rust to the idea of putting default values on field declarations in a `struct`.

### Swift

Like Rust, Swift forces developers to fully initialize a variable before they use it.
The one exception is that variables with an optional type (expressed as `T?` in Swift) get an implicit default initial value of being empty (`nil`).

Unlike Rust, Swift has a carefully designed system of constructors that ensures that objects are fully initialized even with features like the ability to inherit certain constructors from a base class.

A user-defined type in Swift can get a synthesized constructor much like what Slang tries to generate, but an important difference is that Swift supports named arguments, so that call sites to a constructor are easier to read when constructing types with many fields.
The synthesized constructor in Swift only allows arguments to be elided for fields that have explicit default-value expressions; there is no system by which other fields of user-defined types might get initialized implicitly (except for the special-casing of optionals).

Swift provides some low-level APIs for accessing uninitialized memory, along the lines of what Rust has, but these kinds of APIs in Swift often feel closer to C-style programming than the style of Rust.

Proposed Approach
-----------------

We propose that in Slang 2026, the wide space of options for how initialization is expressed and performed should be narrowed down to a smaller and more carefully designed subset, that is compatible with the over-arching vision for Slang.
In this section we will discuss the major concepts that work together to implement initialization.

### Declaring a Variable

A local/global variable with an initial-value expression is initialized upon declaration; one *without* an initial-value expression is uninitialized.
That's it; no magic implicit construction semantics, and no in-between states.

A variable that is uninitialized becomes initialized the first time that it is used as the left-hand operand of an assignment expression (infix `=`), or is passed as an argument for an `out` parameter.

Any other expression that refers to a variable before it is initialized is an error, and should be diagnosed.
The compiler's current analysis pass for detecting uninitialized variables must be implemented to be rock-solid for this use case.

(Similarly, any attempt to return from a the body of a function-like declaration when one of its `out` parameters is uninitialized is an error)

Notable case of expression that are an error when applied to an uninitialized variable:

* Field/property access, even when on the left-hand side of an assignment. The statement `v.x = 0;` is invalid if `v` is not initialized.

* Method calls on the variable (`v.doThing()`), including to `[mutating]` methods that might otherwise write valid values into the variable.

* Array subscripting (`v[i]`), even when used to initialize the elements of an array.

* Passing the variable as an argument for a function parameter with a "direction" other than `out`. Notably, passing an uninitialized variable to an `inout` parameter is an error.

### Constructors

#### Explicit User-Defined Constructors

Similar to the current state of affairs, if a user-defined type declaration includes one or more explicit `__init` declarations, then the compiler will not attempt to synthesize any constructors.

Unlike the current state of affairs, the `this` parameter of a constructor is *not* equivalent to an `out` parameter;
writing to the individual fields of an `out` parameter one-by-one would violate the rules above for access to an uninitialized value, but a constructor is allowed/expected to do just that.

Borrowing terminology from Swift, we say that a user-defined constructor must be either a *designated* constructor, or a *convenience* constructor.
Put simply, convenience constructors are just wrappers around other constructors, while designated constructors are where things "bottom out" and actually have to initialize `this`.

The body of a convenience constructor must conform to the following sequence of operations:

1. Zero or more statements that do not access `this` or any of its members.

2. A call `__init(a, b, c, ...);` to another constructor of the same type.

3. Zero or mor statements that are allowed to access `this` as a fully-initialized value

The body of a designated constructor must conform to the following sequence of operations:

1. Zero or more statements that may assign to fields of the current type through `this`, but may not otherwise access `this` (notably: cannot access derived fields).
  At the end of these statements, all fields of the current type that do not have a default-value expression must be fully initialized.
  (The rest will then be initialized to their default values)

2. If the current type has a concrete base type, then a call `super(a, b, c, ...)` to a constructor of the base type.

3. Zero or more statement that are allowed to access `this` as a fully-initialized value

#### Synthesized Constructor

If a user-defined type doesn't declare any explicit `__init` declarations directly in its body, it is a candidate for having a constructor synthesized.
The synthesized constructor gets a parameter for each field, with the corresponding type and name.
Each parameter is optional only if the corresponding field has a default value expression.

The synthesized constructor is a designated constructor.
It initializes each direct field of the type in declaration order, to either the value of the coresponding parameter (if an argument was provided), or using the default-value expression for that field (if no argument was provided).
Then it invokes the constructor of the concrete base type (if there is one) with zero arguments.

The synthesized constructor will have the same visibility as the type itself (e.g., if the type is `public`, the constructor will be `public`, etc.).

Synthesis of a constructor will not be performed if any of the following conditions is true:

* The type has a concrete base type and that concrete base type does not have a constructor that can be invoked with zero arguments.

* One or more of the fields of the type have lower visibility than the type itself.

### Initializing/Constructing a Value

Given a type `Thing`, an instance of `Thing` is constructed by invoking one it its constructors, with syntax like `Thing(a, b, c)`.

A key distinction from existing Slang is that we propose to support *named arguments* in calls to constructors (and call operations in general).
A named argument consists of an identifier for the label/name, a colon (`:`), and then an expression.
E.g., one could conceivably write `float3(x: 0, y: 1, z: 2)` as a particularly verbose way of writing `float3(0,1,2)`.

The combination of the synthesized constructor provided for simple types and support for named arguments allows users to express something akin to what *designated initializers* in C/C++ enable:

    struct Wave
    {
        float phase = 0.0;
        float amplitude = 1.0;
    }

    let w = Wave(
        phase: pi/2,
        amplitude: 9999);

    let v = Wave(
        amplitude: -1);

Note how the use of named arguments allows a user to provide values for just the fields they care to explicitly initialize; the others will get their default values (if they have them).
If a user attempts to call a synthesized constructor without an argument corresponding to a non-optional parameter (a field without a default value), an error will be diagnosed (as for any overload-resolution failure):

    struct Sphere
    {
        float3 origin; // no default
        float radius = 1;
    }

    let s = Sphere(radius: 12); // ERROR: no argument provided for required parameter `origin`

#### Convenient Syntax For Default-Initialization

In the context of the proposed new semantics "default initialization" merely refers to initializing something with a zero-argument constructor call for its type, like:

    Wave myWave = Wave();

or:

    MyComplicatedMaterialType material = MyComplicatedMaterialType();

That last example shows how it can be tedious to repeat the type name between both the declaration and the initial-value expression.
When declaring a local variable, use of `let` or `var` can often allow the repetition to be eliminated:

    var material = MyComplicatedMaterialType();

but when declaring a field in a `struct` type, many programmers do not feel comfortable leaving the type off of the declaration (and indeed Slang may someday enforce that an explicit type is always required on fields).

For these cases, we propose to introduce a new kind of literal expression: a *default-value* literal.
A default-value literal expression is expressed as just the identifeir `default`:

    var material : MyComplicatedMaterialType = default;

A `default` expression may only be used in contexts where it will be coerced to some specific type (similar to how initializer lists work in Slang today), and when a `default` expression is coerced to some type `Thing`, it will be equivalent to a constructor call with zero arguments: `Thing()`.

The use of `default` expressions will be the preferred/idiomatic way to declare that a `struct` field should have a default value that matches a default-initialized value of its type.

In order to facilitate use of `default` expressions in generic contexts, the core module will define an interface:

    interface IDefaultable
    {
        __init();
    }

Types can opt-in to support for this interface, but the compiler will *not* automatically treat all types that support a zero-argument constructor call as conforming to `IDefaultable`; it is an explicit `interface`, like any other.

Detailed Explanation
--------------------

This section will primarily cover some nitty-gritty details that would have made the previous section even longer than it already is.

### Making it Clear: The Common Idiom That Won't Work Any More

While it is just a consequence of the proposed semantics, rather than a separate rule, it is important to be clear that with this proposal code will no longer be able to construct a value in the way that is idiomatic for a *lot* of C/C++ codebases, e.g.:

    Wave w;
    w.amplitude = 100.0;
    w.phase = 0.0;

In this example, the attempt to assign to `w.amplitude` will be diagnosed as an error, because `w` is being accessed when it is uninitialized.

Disallowing such a commonly-used idiom may turn out to be something that user's get upset about, or even cannot tolerate.
However, it is important to note that as soon as one tries to support this kind of idiomatic C-like code, special-case rules and hacks need to creep their way into the language semantics in an attempt to make that code Just Work as users intend.

If we have any aspiration to drop the hacky mess of approaches we have today, we pretty much *have* to abandon support for this idiom.

### Constructors Calls and Casts

We propose to keep the current special-case rule where `Thing(a)` is treated as a synonym for `(Thing) a` and first tries built-in type coercion rules before falling back to a constructor call.
There are plenty of valid reasons why code might end up, e.g., casting a value to its own type (it can easily happen as code evolves), and our past experience has been that *not* treating `Thing(a)` and `(Thing) a` as semantically equivalent ends up confusing users.

### Initializer Lists

We propose that `{}`-enclosed initializer list syntax should still be supported, at least for the forseeable future, even in Slang 2026.
However, unlike the situation in current Slang, an initializer-list expression `{a,b,c}` that gets coerced to type `Thing` will be entirely semantically equivalent to `Thing(a,b,c)`.
We will drop support for the C-style initializer list handling rules, and the special-case rules for forcing zero-initialization even on fields that didn't specify a default value.

The empty initializer list `{}` will be semantically equivalent to a `default` expression.

While initializer lists will be *allowed*, the Slang tools, documentation, etc. should default to showing examples that use only constructor-based initialization or `default` expressions (which should be explained as a shorthand for a zero-argument constructor call).

### Arrays: The Elephant in the Room

Arrays are the main case where it seems impossible to abide by the intialization rules being proposed here.
Simple code like the following would now be invalid:

    int a[10];
    for(int i = 0; i < 10; i++)
        a[i] = someFunc(i); // ERROR: `a` is being accessed while uninitialized

This proposal may live or die by the issue of supporting arrays cleanly.

First, it is important to note that in cases where the element type of the array can be default-constructed, an array can be initialized with `default`:

    Thing t[10] = default; // works if `Thing()` is valid

We will also plan to support convenient intialization of an array with a single repeated value:

    var indices = int[100]( -1 ); // 100 values, all equal to -1

Beyond these simple cases, we believe that we can support many more powerful cases by exploiting recently added support for anonymous functions ("lambdas") in Slang.
The earlier example:

    int a[10];
    for(int i = 0; i < 10; i++)
        a[i] = someFunc(i);

could instead be expressed as a single line like:

    let a = int[10]( (int i) => someFunc(i) );

This plus other higher-order operations, like `map()` and a way to define an array's contents by induction (akin to a `fold()`), could allow many use cases that currently rely on array mutation to be supported in the new world of stringent intialization checks.

#### Eventually: Dynamically-Sized Arrays

Another convience feature is probably long-overdue for addition to the core module is some kind of dynamically-sized array type with a fixed upper bound.
With such a type, a user could write, e.g.:

    BoundedSizeDynamicArray<int, 10> a; // or whatever the type gets called...
    for(int i = 0; i < 10; i++)
        a.add( someFunc(i) );

The implementation of such a type in the core module would be largely straightforward, and the core module could take care of whatever delicate interactions it needs to have with the compiler to reassure it that values are consistently initialized before they are accessed.

Alternatives Considered
-----------------------

The only real alternative we have considered so far is to give up, and resign ourselves from slowly sliding into the realm that C++ occupies where almost all types support being implicitly default-constructed, but often to a state that is literally or figuratively equivalent to a null pointer.

"When every variable is 'intialized', none of them are."
