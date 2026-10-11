SP #032: Initialization Behavior in Slang 2026
================================================

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
If none of the built-in rules applies, then it falls back to looking constructor declarations on `Thing` and checking a call to them (just like the constructor-call syntax would for the cases with other numbers of arguments).

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

In Slang 2026, when a local or global variable is declared:

* if the variable declaration has an initial-value expression, the variable starts out fully initialized

* if the variable declaration does not have an initial-value expression, the variable starts out uninitialized

Note that unlike current Slang, the proposed new semantics are that *any* variable declared without an initial-value expression starts out uninitialized, and must be explicitly initialized.
There are no implicit "default construction" rules a la C++.

The change to eliminate C++-style default initialization of variables could be a surprising one, and might break some user code.
In order to mitigate this, it is vital that the Slang compiler diagnose errors whenever a potentially uninitialized variable is used, under the Slang 2026 language version.
The error diagnostics will help developers notice any cases where they were relying on the old C++-style behavior.
We can potentially include a note as part of the diagnostic, to hint developers at what might be underlying the problem and how best to fix it.

### Initializing a Variable

A variable that is uninitialized may become initialized by any of the following means:

* Assigning to that variable

* Passing the variable as the argument for an `out` parameter in a call

* Initializing each instance (non-`static`) field, in the case where the variable has a `struct` type

* Initializing each element, in the case where the variable has an array type

The field-by-field and element-by-element initialization cases have some restrictions, which are discussed further in the Detailed Design seciton.

### Use of an Uninitiailized Location

Any attempt to use a variable before it is fully intialized, that does not fall into one of the cases in the previous section (Initializing a Variable) is an error, and will be diagnosed.
The compiler's current analysis pass for detecting uninitialized variables must be improved to be rock-solid for this use case.

Notable case of expression that are an error when applied to an uninitialized variable:

* Passing the variable as an argument of a call, for a parameter that is not an `out` parameter. Notably, passing an uninitialized variable to an `inout` parameter is an error. Note that in Slang call operations include many cases:

    * Ordinary function calls

    * Method calls

    * Most operators (e.g., `a + b` is a call)

    * Invocation of constructors

    * Subscripting (`a[i]`) on anything other than an array

    * Property access (whether for read, write, or modify)

* Using the variable as the base for a method call (`v.doThing()`), even to `[mutating]` methods

* Using the variable as the right-hand-side operand of an assignment expression

* Using the variable as the operand of a `return`, `if`, `switch`, or other statement

Array subscript and `struct` field access are special-cases.
If a variable is uninitialized or partially initialized, and its type is compatible with element-by-element or field-by-field initialization, then:

* Writes to array elements and `struct` fields are alloweded

* A read or modification (read-modify-write) of an array element or `struct` field is allowed if the specific element or field is known to be initialized

### Failure to Initialize a Location

Returning normally from a function when one or more `out` parameters are not fully initialized is an error.

(Exiting a function via an error in a `try` context does not require `out` parameters to be fully initialized)

Constructors enforce comparable rules: each field of the type must be fully initialized by the end of the constructor.
The details for constructors are more complicated, and are discussed in the Detailed Design section below.

### Constructors

#### Explicit User-Defined Constructors

Similar to the current state of affairs, if a user-defined type declaration includes one or more explicit `__init` declarations, then the compiler will not attempt to synthesize any constructors.

Borrowing terminology from Swift, we say that a user-defined constructor must be either a *designated* constructor, or a *convenience* constructor.
Put simply, convenience constructors are just wrappers around other constructors, while designated constructors are where things "bottom out" and actually have to initialize `this`.

The body of a convenience constructor must contain the following, in order:

1. Zero or more statements that do not access `this` (implicitly or explicitly) or any of its members.

2. A call `__init(a, b, c, ...);` to another constructor of the same type; after this step `this` is fully initialized.

3. Zero or more statements that are allowed to access `this` normally.

The body of a designated constructor must contain the following, in order:

1. Zero or more statements that may write to the direct fields of the current type through `this`, but may not otherwise access `this` (notably: cannot access derived fields or call methods).
  At the end of these statements, all direct fields of the current type that do not have a default-value expression must be fully initialized.
  (The rest are then initialized to their default values)

2. If the current type has a concrete base type, then a call `super(a, b, c, ...)` to a constructor of the base type; after this step `this` is fully initialized.

3. Zero or more statement that are allowed to access `this` normally.

#### Synthesized Constructor

If a user-defined type doesn't declare any explicit `__init` declarations directly in its body, it is a candidate for having a constructor synthesized.

If a constructor is synthesized for a user-defined type, it has one parameter for each direct field, with the corresponding type and name.
Each parameter is optional only if the corresponding field has a default value expression.
The body of that construct initializes each field to either the corresponding parameter value (if an argument was provided) or the default-value expression for that field (otherwise).

The synthesized constructor gets the same visibility as the type itself (e.g., if the type is `public`, the constructor will be `public`, etc.).

Synthesis of a constructor will not be performed if any of the following conditions is true:

* The type has one or more explicit `__init` declarations in its body.

* The type has a concrete base type and that concrete base type does not have a constructor that can be invoked with zero arguments.

* One or more of the fields of the type have lower visibility than the type itself.

These restrictions are intended to keep things as simple as possible for now;
multiple ways of lessening the restrictions could be considered in the future.

### Constructing a Value

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

#### Alternative Syntaxes

The Slang 2026 language will continue to provide some other syntactic options for constructing values:

* A C-style cast expression like `(SomeType) someExpr` will continue to be equivalent to the constructor call like `SomeType(someExpr)`.

* An initializer-list expression like `{ a, b, c }` appearing in a context where a value of type `SomeType` is expected will be equivalent to looking up and invoking a constructor on `SomeType` with arguments `a, b, c`.

### Piecewise Initialization

It is common for code in C-like languages to declare a variable with no initial-value expression, and then fill in that variable *piecewise*: field-by-field or element-by-element.
For example, given a `struct` type like the following:

```hlsl
struct Ray
{
    float3 origin;
    float3 direction;
}
```

it is common for an application to declare and fill in a variable using code like:

```hlsl
Ray r;
r.origin = camera.position;
r.direction = camera.direction;
```

In some cases code using this kind of traditional idiom can be rewritten to use other approaches.
For example, the previous code block could be re-written to the following in Slang:

```hlsl
var r = Ray(
    origin: camera.position,
    direction: camera.direction);
```

Rewriting code to avoid piecewise initialization is not always trivial (especially for arrays), and developers are likely to be frustrated if idiomatic code they write out of habit stops being legal in Slang.

We propose to support piecewise initialization in Slang 2026, but only in specific cases.

#### Field-by-Field Initialization

A `struct` type `S` will be eligible for field-by-field initialization if:

* All of the fields of `S` are visible in the current context

* the body of `S` contains no user-defined constructors

* `S` contains no fields with default-value expressions

* the `struct` type that `S` inherits from (if any) is eligible for field-by-field initialization

An uninitialized variable of such a type `S` can be initialized by writing to each of its fields.

Note that in the case where a variable of type `S` is being initialized field-by-field no constructor for `S` gets called.
This is not an issue in practice, because the only designated constructor an eligible type could have would be the synthesized one, so there is no user-defined logic (such as invariant checking/enforcement) that gets skipped.

Similarly, when initializing a variable of type `S` field-by-field, it is an error to not initialize all of the fields of `S`;
no default-value expressions will be evaluated to initialize fields that get skipped, because an eligible type cannot have any such default-value expressions.

We expect that the Slang compiler can be made to do a good job of tracking per-field initialization state for variables of `struct` type and issue reliable diagnostics for access to uninitialized values at per-field granularity.

#### Element-by-Element Initialization

All array types are eligible for element-by-element initialization.

An unitialized variable of an array type can be initialized by writing to each of its elements.

Note that unlike the case for field-by-field initialization of `struct`s, we expect that the compiler work required to statically determine whether an array has been fully initialized via element-by-element writes is beyond what we are ready to implement in the short term.
For common idioms that initialize an array element-by-element using a loop, we expect that the compiler will often only be able to determine that an array *might* be fully initialized at some point, but not conclusively determine that it *must* be initialized.
Here's a simple example:

```hlsl
void f(int N)
{
    int a[10];
    for(int i = 0; i < N; ++i)
    {
        a[i] = f(i);
    }
    doSomethingWith(a, N);
}
```

There is no practical way for the Slang compiler to statically conclude that `a` is fully initialized at the time it gets passed into `doSomethingWith()`.

Even though it may frustrate users we propose that, when in doubt, the compiler should treat any access to a variable (even an array) that it cannot prove *must* be initialized as an error.
The next few sections discuss ways that a user might resolve such error cases, but we still expect this choice to be a difficult pill for users to swallow.

### When you just need the variable to be initialized...

In the preceding section we discussed how the Slang compiler will sometimes need to be conservative and issue errors for code that a programmer might known is correct, but where the compiler cannot statically rule out the possibility that an uninitialized variable/location might be accessed.

The typical workaround that programmers employ in such cases is to initialize a variable to some "safe" placeholder value to silence the compiler error.
We propose two language constructs to help in such cases.

#### Interface for "Safe" Default Values

We propose to add an `interface` to the Slang core module that is comparable to the Rust [`Default`](https://doc.rust-lang.org/std/default/trait.Default.html) trait.
As the docs for that trait say (emphasis added):

> Sometimes, you want to fall back to some kind of default value, and *don’t particularly care what it is*.

Our Slang variation on this theme is:

```
interface IDefaultable
{
    static property defaultValue : This { get; }
}
```

The basic scalar types in the core module will all implement `IDefaultable` (with a default value of `0`, `0.0`, or `false`, as appropriate), as will the `Optional<T>` type (default value is empty/null).
Built-in aggregate types like vectors, matrices, arrays, and tuples will conditionally implement `IDefaultable` when their elements do.

A user-defined `struct` can explicitly implement `IDefaultable`, but they can also declare conformance to `IDefaultable` and let the compiler synthesize the `defaultValue` property under the following conditions:

* If the type has a constructor that is callable with zero arguments, and that has visibility at least as high as the type itself, then `defaultValue` can be synthesized as a call to that constructor

* Otherwise, if the type has a synthesized constructor and all of its direct fields that do not have a default-value expression are of types that conform to `IDefaultable`, then `defaultValue` can be synthesized as a call to that constructor, with all non-optional parameters passed arguments that are default values of the corresponding type.

As an extremely special case (that we may end up regretting), any user-defined `struct` type that does not explictly declare conformance to `IDefaultable` but that could have a suitable conformance synthesized will be automatically modified to conform to `IDefaultable`.

Note user-defined `enum` types must explicitly declare and implement conformance to `IDefaultable`, if desired.

#### Concise Syntax for Default Values

We propose to allow the `default` keyword to be used as an expression in contexts where a value of a known type is expected.
When a `default` expression appears where a value of type `T` is expected, we require that the type `T` conforms to `IDefaultable`, and the expression is equivalent to `T.defaultValue`.

This allows a user to write something like:

```
Thing things[10] = default;
```

so long as the type `Thing` conforms to `IDefaultable` (whether explicitly or implicitly).

We hope that `default` expressions will become the idiomatic way to express that a variable, field, etc. should have a default value in cases where a more semantically-meaningful expression is not obvious or available.

#### A Way to Express Intentional Absence of Initialization

While `default` expressions will often be enough to silence the compiler in cases where it cannot statically determine that a variable is being properly initialized, there can still be cases where a developer might be unable to use `default`:

* Some types cannot meaningfully conform to `IDefaultable`, because they lack a safe default value. For example, variables of `class` type in Slang do not (or *will not*, considering that `class` support is still experimental) support being set to null. A more mundane example is the `Texture2D` type from the core module.

* In some performance-critical cases, a programmer might find that the cost of initializing a variable to `default` (no matter how minimal it might be) is too much to accept

To handle these cases, we propose to add a contextually-typed expression, akin to `default`, that explicitly expresses an intended lack of initialization.
The name to use for this construct should discussed thoroughly, but for now this proposal will use the spelling `UNININITIALIZED` and `UNSAFE_UNINITIALIZED`.

Given a declaration like:

```
int data[100] = UNINITIALIZED;
```

the Slang compiler front-end will refrain from emitting errors in cases where it sees `data` being used and cannot statically determine whether the variable is fully initialized or not.
Note that the compiler may still emit errors in cases where it can statically prove that uninitialized data would be accessed; the change in behavior is only for the case where the compiler's conservative analysis proved inconclusive.

In the Slang compiler back-end, a variable initialized to `UNINITIALIZED` will be treated just like any other uninitialized variable is treated today.
Note that for certain combinations of target platform and compiler options, the Slang compiler may still end up generating code that initializes an uninitialized variable, in order to avoid errors that arise when invoking a downstream compiler tool, or in order to avoid potential security issues.
The value(s) used for such "fallback initialization" are not guaranteed, but currently the compiler uses a zero/null value, whenever one exists for a type.

When compiling with debug information enabled, the compiler will continue to initialize otherwise-uninitialized variables.
In the future the compiler will likely be updated to use certain well-defined "garbage" values for fallback initialization in these cases.

Detailed Explanation
--------------------

Some of the material in this section will use phrasing and terminology that is either derived from, or intended for, the Slang language specification.
If things seem very pedantic and dry in places, please consider those as first-draft attempts at specification language.

### Named Arguments

This topic needs its own proposal, so it is not going to be covered here...

### Abstract Storage Locations

An *abstract storage location* is a logical place that may hold a value.
Memory locations (ranges of bytes in a single address space) are one example of an abstract storage location, but it is not assumed that all abstract storage locations reside in memory.

Each abstract storage location has a type, which determines what values may be stored there.

Evaluation of an expression of some type `T` may yield either a value of type `T` or a *reference* to an abstract storage location of type `T`.
Evaluation of an l-value expression will always yield a reference to an abstract storage location.

#### Containment

An abstract storage location may contain zero or more other abstract storage locations.
For example, an abstract storage location with a `struct` type will contain abstract storage locations for each of the instance (non-`static`) fields of that `struct` type.

#### Overlap

Two abstract storage locations may overlap, partially or completely.
For example, if Slang add support for `union` types, then in the following example:

```hlsl
struct A { float b; uint c; }
struct X { double y; int z; }
union U { A a; X x; }
U u;
```
the abstract storage location for `u.x.y` will likely overlap partially (but not completely) with `u.a.b`.

#### Initialization State

Any given abstract storage location may be in one of three states:

* **Fully Initialized**: the abstract storage location holds a value of the expected type.

* **Partially Initialized**: the abstract storage location does not hold a value of the expected type, but one or more of the abstract storage locations it contains are fully or partially initialized.

* **Uninitialized**: neither of the preceding two cases applies: the abstract storage does not hold a value of the expected type, and all of its contained storage locations are uninitialized.

#### Statically-Determined State

While during execution a given abstract location will always be in some specific state, during static semantic checking of Slang code a compiler must use a conservative approximation of the dynamic behavior.
In a given context, the compiler will represent its understanding of the potential initialization states of a given abstract storage location as one of:

* **Definitely fully initialized**: The compiler has statically determined that the location must be fully initialized in that context.

* **Definitely uninitialized**: The compiler has statically determined that the location must be uninitialized in that context.

* **Differing across fields**: The location is of `struct` type and the compiler has different static information about different fields (e.g., one might be definitely fully initialized while another is definitely uninitialized). The compiler must then track separate static state information for the (nested) locations of those fields.

* **Differing across elements**: The location is of array type and the compiler has different static information about different elements. The compiler will track static state information for sub-ranges of elements.

* **Intentionally uninitialized**: the compiler statically knows that the location was "initialized" with an `UNINITIALIZED` expression.

* **Indeterminate**: the compiler cannot statically determine anything useful about the initialization state of the location in this context. This could be because of something like a write into an array at an unknown index, or because the state of the location differs across control-flow paths.

* **Presumed fully initialized**: the compiler does not have sufficient information to determine a more refined state for the location in this context, but has been instructed to treat the location as fully initialized.

### Declaring a Local Variable

#### Without An Initial-Value Expression

When a local variable declaration, without an initial-value expression, like:

```hlsl
var a : float;
```

is executed, an abstract storage location is allocated and the identifier `a` is *bound* to that location.
Evaluation of an expression that refers to `a` will yield a reference to that storage location.
The compiler statically knows that `a` is definitely uninitialized after this declaraiton.

#### With An Initial-Value Expression

A local variable declared with an initial-value expression that is not an `UNINITIALIZED` expression, like:

```hlsl
var b : int = f(1);
```

is executed in the following steps:

* An abstract storage location is allocated and the name of the variable (`b`) is bound to it, just as for the case without an initial-value expression

* The initial-value expression (`f(1)`) is evaluated to yield a value

* That value is moved into the storage location

After these steps are complete, the compiler statically knows that `a` is definitely initialized.

### Initialization of an Uninitialized Location

For our purposes, a *write* to an abstract storage location occurs when either:

* The location is used as the left-hand operand of an assignment expression (infix `=`)

* The location is passed as an argument for an `out` parameter, as part of a call expression

After a write, the state of a storage location is fully initialized.

#### Definite Writes

If the destination storage location of a write can be statically determined, it is a *definite* write to that location.
For example, a simple assignment to a variable, or a field of a variable of `struct` type is always a definite write.
After a definite write, that storage location is statically known to be definitely fully initialized.

#### Indefinite Writes

If the destination storage location of a write cannot be statically determined, it is an *indefinite* write.
The most common case of an indefinite write is an assignment to an array element at a computed index, like `a[f()] = v`.

After an indefinite write, the static initialization state of any locations that could have been written to becomes indeterminate.
For example, after a write like `a[f()] = v`, every element of `a` is in an indeterminite initialization state, and thus so is the entire array `a`.
f it was not before.

### Use of an Uninitialized Location

When an expression or statement performs an access to a storage location (a read, write, or modify):

* If the statically-computed state of that location is definitely fully initialized or presumed fully initialized, then there is no problem.

* Otherwise, if the access is a write, then there is no problem.

* Otherwise, the compiler will diagnose an error.

Examples of operations that perform an access to a storage location include:

* When an expression that evaluates to a storage location is used as an argument to a call (including when using operator syntax like `a += b`) an access is performed on that location. The type of access depends on the "direction" of the corresponding parameter (`in`, `inout`, `out`, etc.).

* When an expression that evaluates to a storage location is used as the right-hand-side operand of the assignment operator, or as the initial-value expression for a variable declaration, a read access is performed on that location

* When an expression that evaluates to a storage location is used as the argument to a statement such as `return`, `if`, `switch`, etc., a read access is performed on that location

### Failure to Initialize an `out` Parameter

At any point where execution would exit the body of an invocable declaration (a function, constructor, property accessor, etc.) normally, for each effective `out` parameter of that declaration:

* If the static initialization state of that parameter is not definitely fully initialized or presumed fully initialized, then the compiler will diagnose an error.

Note: the effective parameters of a method include the implicit `this` parameter, and the effective parameters of an accessor include the parameters of the surrounding `property` or `__subscript`, etc.)

Note: execution exits a statement body *normally* when it reaches a `return` or "falls off the end." When execution exits the body due to an error thrown inside a `try` context, the checks for `out` parameters do not apply.

### Constructors Calls and Casts

The Slang language will continue to have the special case rule that a single-argument constructor call like `Thing(a)` is treated as a synonym for `(Thing) a`.
A cast (and thus a single-argument constructor call) will first try to apply certain built-in type coercion rules before falling back to looking up and invoking a constructor on `Thing`.

### Initializer Lists

C-style `{}`-enclosed initializer list syntax will still be supported in Slang 2026, but its semantics will be refined to be more consistent.
When an initializer-list expression `{a0, a1, ...}` is used in a context where a value of some type `T` is expected, the compiler will look up the constructor(s) for `T` and perform a potentially-overloaded call with the arguments `a0,a1,...`.

Note that an initializer-list expression with a single argument (`{a}`) is not fully equivalent to a constructor call `T(a)` (which is itself equivalent to the cast `(T) a`), because we do not merely desugar an initializer list into a constructor call expression, and instead look up and call the constructor directly.

Note that this translation presumes the existence of constructors on the core-module `Array` type that can handle the semantics we want.
For example, given an array type `T = X[N]` where the integer value of `N` can be statically determined, the type `T` must behave as if it has a constructor that takes `N` parameters of type `X`.
Requiring an array type to behave as if it has such a constructor, rather than handling that behavior as a special case for initializer lists, ensures that users can use constructor-call syntax to build the arrays they might otherwise use initializer-list syntax for.

The main open question is how the compiler should handle cases where an array of the form `T = X[N]` (again with the integer value of `N` statically determined), is being initialized using an initializer-list expression with fewer than `N` arguments (including the case of zero arguments).
As a starting point, we propose to let that case be an error.
If that simple answer proves unsatisfactory, then the core-module `Array` type could be extended so that when `X` conforms to `IDefaultable`, the type `X[N]` has a constructor that takes any number of arguments less than `N` (filling in the remaining elements with `X.defaultValue`).

A further extension, if we find that we need to provide even more backwards-compatibility behavior, would be to make a zero-argument initializer-list expression `{}` be semantically equivalent to a `default` expression.

Note that while initializer lists will still be *allowed* in Slang 2026, the Slang tools, documentation, etc. should default to showing examples that use only constructor-based initialization or `default` expressions.

Alternatives Considered
-----------------------

The only real alternative we have considered so far is to give up, and resign ourselves from slowly sliding into the realm that C++ occupies where almost all types support being implicitly default-constructed, but often to a state that is literally or figuratively equivalent to a null pointer.

"When every variable is 'intialized', none of them are."
