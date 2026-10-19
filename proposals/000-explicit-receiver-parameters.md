SP #000: Explicit Receiver Parameters
=================

We propose to allow the receiver (`this`) parameter of a declaration to be written *explicitly*.
An explicit receiver parameter declaration makes it easier for developers to apply a non-default parameter-passing mode to that parameter, using the same modifier keywords as are used for other parameters.


Status
------

- Status: Design Review
- Implementation: -
- Author: Theresa Foley
- Reviewer: -

Background
----------

Slang is primarily a procedural language, but provides some mechanisms for authoring code with an object-oriented style.
One of the most important such mechanisms is the ability to define methods (member functions) that take an implicit *receiver parameter* named `this`.
Consider the following simple example:

```slang
public struct Counter
{
    internal int _value = 0;

    public int get()
    {
        return this._value;
    }

    [mutating]
    public void increment(int amount = 1)
    {
        this._value += amount;
    }
}
```

Here we can see that code in the body of the `Counter.get` and `Counter.increment` methods can access `this`, the implicit parameter that represents the receiver of a method call.
Other code can call these methods on an expression of type `Counter`; e.g.:

```slang
var myCounter : Counter = Counter();

let initialValue = myCounter.get();
myCounter.increment(99);
let finalValue = myCounter.get();
```

In a call expression like `myCounter.increment(99)`, the expression `99` is the argument for the ordinary parameter `amount` of `Counter.increment`, while the expression `myCounter` is the argument for the implicit receiver parameter of `Counter.increment`.

The object-oriented convenience syntax in Slang can often be understood best in terms of how these constructs can be desugared into more "flat" C-style procedural code.
For example, the `Counter` example above could be desugared into the following flattened form:

```slang
public struct Counter
{
    internal int _value = 0;
}

public int Counter_get(Counter counter)
{
    return counter._value;
}

public void Counter_increment(inout Counter counter, int amount = 1)
{
    counter._value += amount;
}
```

The desugaring process not only turns the implicit `this` parameters in the original example into explicit parameters, but it also highlights how the implicit receiver parameter of the `[mutating]` method `Counter.increment` uses the `inout` parameter-passing mode (whereas the receiver parameter of `Counter.get` used the default `in` mode).

But what if we want a receiver parameter to use a different parameter passing mode?
Slang currently supports additional parameter-passing modes that are not officially supported, but likely will be soon.
The `borrow` mode (currently spelled `__constref`, which is a bad and misleading name for many reasons) can improve performance over `in` when a parameter is a large value type.
The `ref` mode (currently spelled `__ref`) is needed when a function requires a memory location to be passed in, and the possibility of copy-in/copy-out that comes with `inout` would not be acceptable (e.g., for atomic operations).
Parameter-passing modes like these can make sense to apply to a receiver parameter, just as they can make sense for other parameters.

A similar challenge arises for the `no_diff` modifier used with Slang's automatic differentiation support.
Marking an ordinary parameter as `no_diff` indicates that automatic differentiation should not try to differentiate with respect to that parameter.
There can, of course, be cases where the receiver parameter of a method is one that should not be differentiated.

For both parameter-passing modes and parameter modifiers like `no_diff`, Slang developers must currently learn and use different syntactic conventions when working with receiver parameters as opposed to ordinary parameters, because when receiver parameters are *implicit* there is no parameter declaration to attach a modifier like `ref` or `inout` to.

Related Work
------------

There are many languages in which receiver parameters may be written explicitly, and some where they *must* be written explicitly.
We will briefly survey some such languages, along with the apparent design motivations for their choices.

We will look at cases where a language has a method call syntax of some sort (e.g., `x.f(y,z)`), and there is a parameter that matches with the argument `x` - that is what we will consider to be a *receiver parameter*, whether or not the language considers it such.

### Python

A Pythonic version of the earlier `Counter` example might be:

```python
class Counter:
    def __init__(self):
        self.value = 0

    def increment(self, amount):
        self.value += amount

counter = Counter()
counter.increment(1)
```

In Python the declaration of a receiver parameter is no different from other parameter declarations.
By convention a receiver parameter in Python is named `self`, but that is not something that the language requires or considers, semantically.

An expression like `counter.increment` in Python forms a bound method.
In this case, the bound method is effectively a closure which will supply the receiver (`counter`) as the first argument to `Counter.increment`.
As such, the syntax `counter.increment(1)` is roughly equivalent to `Counter.increment(counter, 1)`.

Python's approach to receiver parameters is appropriate for a highly dynamic language.
Rather than add dedicated syntax related to receivers (e.g., by making `self` a keyword)  Python instead puts most of the complexity in the runtime meta-machinery for things like member access (`counter.increment`).

Python, like many other dynamic languages, does not support implicit lookup of instance members inside of an instance method body (that is, considering lookups like `self.value` for an identifier expression `value`).
The lack of implicit lookup like this is both an intentional design choice (to rely on lexical scoping alone) and a byproduct of not having any special language-level concept of a receiver parameter.

### Rust

A Rust equivalent of the counter example might be:

```rust
struct Counter { value: i32 }

impl Counter
{
    fn get(&self) -> i32 { self.value }

    fn increment(&mut self, amount: i32)
    {
        self.value += amount;
    }

    fn into_value(self) -> i32 { self.value }
}

fn main()
{
    let mut counter = Counter { value: 0 };
    counter.increment(1);
}
```

Rust requires explicit receiver parameter declarations for subroutines that can be invoked with method-call syntax.
Receiver parameter declarations in Rust appear inside of the `()`-enclosed parameter list along with ordinary parameter declarations, but do not use the exact same syntax as ordinary parameters.
Receiver parameters in Rust must be named `self`, and `self` is a keyword.
A receiver parameter in Rust must always be the first parameter in the list.

A key part of the motivation for using explicit receiver parameter declarations in Rust is to allow users to specify the passing mode for a parameter.
A Rust user can specify a by-value parameter with `self`, an immutable shared borrow (passed by reference) with `&self`, and an exclusive mutable borrow (by reference) with `&mut self`.
These are actually shorthand for more explicit forms like `self: &mut Self` which more directly mirror the syntactic form of ordinary parameter declarations.

In Rust, `impl` blocks on a type (similar to Slang `extension`s) are used to introduce operations that are associated with a type.
An `impl` block may introduce functions both with and without a receiver parameter; only the functions with a receiver parameter may be called using method-call syntax, while others must be called as ordinary functions within the type's namespace.

A call like `counter.increment(1)` in Rust could instead be written as `Counter::increment(&mut counter, 1)`.
Every function with a receiver parameter can be called like one without, so declaring a receiver parameter is just a way to enable an alternative call syntax.
Method call syntax like `counter.increment(1)` provides convenience compared to `Counter::increment(&mut counter, 1)` because the type scope to look up the operation in can be inferred, and the use of `&` or `&mut` on arguments (to match the parameter-passing convention of the corresponding parameter) can be elided for a receiver argument.

Beyond using explicit receiver parameters to choose between by-value and by-reference (borrow) semantics, Rust also allows receiver parameters to use types other than `Self`, such as a declaration `self: Box<Self>`.
The types allowed for receiver parameters are explicitly defined, so users cannot use an `impl` for a type `Foo` to declare a `self: Bar` using some arbitrary other type `Bar`.

### Swift

A Swift version of `Counter` might be:

```swift
struct Counter
{
    var value = 0

    borrowing func get() -> Int { self.value }

    mutating func increment(_ amount: Int)
    {
        self.value += amount
    }

    consuming func intoValue() -> Int { self.value }
}

var counter = Counter()
counter.increment(1)
```

Swift uses implicit receiver parameters, always named `self` and having type `Self`.
The parameter-passing mode for a receiver parameter is indicated using modifiers on the function declaration itself, such as `borrowing`, `mutating`, and `consuming` above.
Note that terms like `borrowing` and `consuming` in Swift do not correspond exactly to how comparable concepts are defined in Rust or Slang; we are primarily considering the role they play as modifiers that affect parameter-passing behavior.
The default conventions for the mode of parameters (including receivers) can vary across declaration kinds in Swift.

The keywords that Swift uses to indicate receiver parameter-passing modes sometimes mirror those used to indicate the mode of an ordinary parameter (e.g., for `borrowing` and `consuming`) and at other times are unique to the receiver-parameter case (e.g., `mutating` methods correspond to `inout` parameters, and a `nonmutating` accessor corresponds to a parameter with the default mode).

Similar to Rust, a Swift method call like `counter.increment(1)` allows the receiver argument (`counter`) to be passed to a receiver parameter by-reference without an explicit `&` at the call site (which would be required for an argument to an ordinary `inout` parameter).

### C#

In C# a receiver parameter (`this`) is implicit for ordinary method declarations.
A `readonly` modifier can be applied to a method on a value type, to indicate that the receiver parameter should be a read-only reference.

Extension methods in C# may include declarations with an explicit receiver.
For example, here is a version of the `Counter` example using extension methods:

```csharp
public struct Counter
{
    public int Value;
}

public static class CounterExtensions
{
    public static void Increment(this ref Counter self, int amount)
    {
        self.Value += amount;
    }
}
```

A `static class` in C# can be used for some of the same things as a Rust `impl` or Slang/Swift `extension` - notably, adding new operations to an existing type.
In an extension method like `Increment` above, a receiver parameter is marked by using `this` as a modifier;
the declaration otherwise appears like an ordinary parameter declaration, including having a user-defined name.
An explicit receiver parameter on an extension method is thus very similar to an ordinary parameter for the purposes of a method *definition*.

An extension method can be called with method-call syntax: `counter.Increment(1)` comparable to `CounterExtensions.Increment(ref counter, 1)`.
Here as in Rust and Swift, we see that syntax that would be mandatory for an ordinary argument (`ref counter`) when passed to a by-reference parameter is not required when that argument is the receiver in method-call syntax.
Similar to associated functions for a type in Rust, an extension method in C# can be invoked with either method-call or ordinary function-call syntax.

C# 14 supports `extension` blocks, which allow a single receiver parameter declaration to be shared by multiple members. E.g.:

```csharp
public static class CounterExtensions
{
    extension(ref Counter self)
    {
        public void Increment(int amount) { self.Value += amount; }
    }
}
```

An explicit receiver can use `ref`, `in`, or `ref readonly` parameter-passing modes, using the same syntax that would be used to indicate these modes on ordinary parameters.


### C++

C++ historically only supported implicit receiver parameters.
A trailing `const` after a method signature can be used to change the implicit `this` parameter's type to a pointer to a `const` instance of the enclosing type.
The default type of a receiver parameter is a pointer to a mutable instance.

With C++23 *explicit object parameters* can be introduced by using `this` at the start of a parameter list.
For example, here is a version of the `Counter` example in C++:

```cpp
struct Counter
{
    int value = 0;

    int get() const { return this->value; }

    void increment(this Counter& self, int amount)
    {
        self.value += amount;
    }

    int getCopy(this Counter self) { return self.value; }
};

int main()
{
    Counter counter;
    counter.increment(1);
}
```

The `get` method above uses an implicit receiver named `this` (and a trailing `const` to make the content of `this` read-only), while `increment` and `getCopy` both explicitly declare a receiver parameter, with a user-defined type and name.

C++ allows the type of an explicit receiver parameter to use a template parameter, so that it may be deduced based on the actual type and qualifiers of a receiver (e.g., when a base-type method is invoked on an instance of a derived type).

A method with an explicit receiver parameter in C++ cannot be `virtual`, and in practice is more like an ordinary function that happens to support method-call syntax, than an alternative syntax for existing C++ method declarations.
In particular, taking the address of a method with an explicit receiver parameter yields an ordinary function pointer, whereas for a traditional non-static method the result would be a pointer-to-member-function.

### Java

Java supports explicit receiver declarations as an option:

```java
class Counter
{
    int value;

    void increment(Counter this, int amount)
    {
        this.value += amount;
    }
}
```

The purpose of explicit receiver parameters in Java is deliberately very narrow.
An explicit receiver parameter allows for annotations to be placed on that parameter's type (e.g., `@SomeTag Counter this`).
An explicit receiver parameter must be named with the keyword `this`, and must be declared using the type of the enclosing class.

Java also allows an explicit receiver parameter to appear on a constructor of a non-`static` inner class; such a parameter makes explicit the instance of the enclosing outer class that is being used to construct an instance of the inner class.
As with the preceding case, this syntax allows annotations to be attached to that parameter.
In most other extended-C-family languages, nested/inner types are always `static`, so this is very much a corner case.

Proposed Approach
-----------------

We propose to allow an explicit receiver parameter to be declared on:

- non-static method declarations
- non-static `operator()` declarations
- accessor declarations inside non-static subscript/property declarations

Here is a variation of the `Counter` example with explicit receiver parameters:

```slang
public struct Counter
{
    internal int _value = 0;

    public int get(this)
    {
        return this._value;
    }

    public void increment(inout this, int amount = 1)
    {
        this._value += amount;
    }
}
```

In the simplest case, an explicit receiver parameter declaration is just the keyword `this`.
The keyword can be preceded by modifiers for parameter-passing modes (`in`, `borrow`, `ref`, etc.) and other modifiers like `no_diff` that need to be applicable to all parameters (both ordinary and receiver parameters).

Method-call syntax like `counter.increment(1)` continues to work the same independent of whether `Counter.increment` had an explicit or implicit receiver parameter.

A receiver parameter declaration may also be written using ordinary parameter declaration syntax, but with the keyword `this` in place of the parameter name:

```slang
public void increment(inout This this, int amount = 1)
{
    this._value += amount;
}
```

The modern parameter declaration syntax may also be used, and explicit receiver parameters are also allowed when declaring functions using the modern syntax:

```slang
public func increment(this: inout This, amount: int = 1)
{
    this._value += amount;
}
```

The type of an explicit receiver parameter must be the keyword `This` - not just a type expression equivalent to `This`.

An explicit receiver parameter may only be the first parameter in a parameter list.

When an explicit receiver parameter is declared for a `set` accessor, the new-value parameter must also be explicitly declared:

```slang
property width : float
{
    get(this: This)
    {
        return xMax - xMin;
    }

    set(this: inout This, newWidth: float)
    {
        xMax = xMin + newWidth;
    }
}
```

Declarations of interface requirements may have an explicit receiver parameter, for requirements that have a receiver:

```slang
interface ICounter
{
    int get(this);

    void increment(inout this);
}
```

Detailed Explanation
--------------------

### Parsing

An explicit `this` parameter declaration should be parsed anywhere in a parameter list, and rejection of invalid uses should be left to semantic analysis.

When parsing a legacy-style parameter declaration, if the lookahead is `this` when the parameter name would be expected, the resulting parameter should be an explicit receiver parameter.
The easiest way to handle this will be to allow `this` where a declarator is expected, and then rule out invalid declaration names in semantic analysis (any explicit declaration named `this` that isn't a parameter declaration is invalid, and any parameter declaration named `this` is an explicit receiver parameter declaration).

When parsing a parameter, after modifiers have been parsed, if the lookahead is `this`, a receiver parameter should be parsed.
If the next token after `this` is `:`, then a type ascription clause should be parsed and a modern-style explicit receiver parameter results.
Otherwise the streamlined explicit receiver syntax should be parsed.

### Semantic Checking

During semantic checking of a parameter list, an explicit receiver parameter declaration should be detected and validated:

- The type of the declaration must be exactly `This` (syntactically), except in the case of the streamlined syntax, where no type is spelled and the type is just implicitly `This`

- An explicit receiver parameter declaration must only be the first parameter in a parameter list

- The only modifiers allowed on an explicit receiver parameter are modifiers for determining a parameter-passing mode, and `no_diff`.

- An explicit receiver parameter declaration must only appear on a declaration that would otherwise have been considered to have an *implicit* receiver parameter.
  For example, a `static` method cannot have an explicit receiver parameter.

- The effective parameter-passing mode of a receiver parameter must not be `out`

When computing the effective parameter information for the receiver parameter of a declaration, an explicit receiver parameter should be used to determine that information, if one is present.
Otherwise, the computation of effective receiver parameter information will proceed as it used to, based on modifiers/attributes on the declaration itself.

If a declaration has an explicit receiver parameter, it is an error for that declaration to have any modifiers/attributes (such as `[mutating]`) that are meant to apply to an implicit receiver parameter.

### Other Areas

All other areas of compilation should use only the calculated effective receiver parameter information for a declaration, independent of whether such a parameter was implicit or explicit.
For example, explicit receiver parameter declarations should have no impact on:

- lookup
- semantic checking of calls
- name mangling
- lowering from a checked AST to Slang IR

Alternatives Considered
-----------------------

### Keep Using Modifiers or Attributes Instead

The main alternative to adding explicit receiver parameters would be to simply *not* add them, and to continue to use additional attributes (like `[mutating]` and `[nonmutating]`) to represent all of the additional parameter-passing modes that we introduce, as well as any other modifiers that might need to pertain to (implicit) receiver parameters.

Either option adds complexity to the language, and adds concepts that users must learn.

The precedent from Swift shows that, by carefully picking the spellings of modifiers used for parameter-passing modes, ordinary explicit parameters and implicit receiver parameters can use the same modifiers.
Following Swift, and the existing Slang precedent, the following cases seem clear for a modifier-based design:

- `in` for ordinary parameters becomes `nonmutating` for receivers
- `inout` for ordinary parameters becomes `mutating` for receivers
- `borrowing` applies to both ordinary parameters and receivers
- `consuming` applies to both

Note that there is likely no need for a receiver mode equivalent to `out` - such an operation could only be invoked on an uninitialized location.

The hard part, then, is deciding what spellings to use for by-reference parameter-passing modes.
Slang has been trending toward the C#-inspired `ref` / `ref readonly` style, but those read more cleanly on explicit parameters than they do on a method declaration itself.
Notably, for legacy C-style function declarations, a `ref` modifier would appear to pertain to the result type of the function and not to the implicit receiver, e.g.:

```slang
struct Counter
{
    ref int incrementAndGet() {...}
}
```

Realistically, the other Swift-y modifiers would also risk looking like they apply to the result rather than the receiver when used with legacy C-style declarations:

```slang
struct Counter
{
    consuming int intoValue() {...}
}
```

In the above example, it really looks like `consuming` applies to `int`, while a `consuming func` or `mutating func` reads more naturally.

While explicit receiver parameters are arguably a larger change to the language, they also have the benefit of making the language more uniform/regular: all parameters can have explicit declarations, and all parameters can have their mode (or other relevant modifiers) specified using the same syntax.
We also consider that explicit receiver parameters are better aligned with some of the future directions we might want to explore.

### Make Explicit Receiver Parameters Required

This proposal creates a situation where there are two ways to do something: both explicit and implicit receiver parameters are allowed, and the attributes that apply to implicit receiver parameters are left in place.

Attributes like `[mutating]` should be considered for deprecation and removal after explicit receiver parameters have been in place long enough for us to know how developers feel about them.

*If* we ever wanted to consider fully removing support for implicit receiver parameters from Slang, it would not be something we could do until after *many* language versions, and with strong evidence about user preferences.

### "Unified Function Call Syntax"

Many developers and language implementers have talked about the notion of "unified function call syntax" (UFCS), referring to the idea that a method call like `x.f(a,b,c)` and an ordinary call like `f(x,a,b,c)` can (or should) be different syntaxes with the same underlying meaning.
In a hypothetical version of Slang with UFCS, a developer could simply provide all of the operations for a type as ordinary function declarations rather than nested member declarations.

In a hypothetical version of Slang with UFCS, the `Counter` example might be:

```slang
public struct Counter
{
    internal int _value = 0;
}

public int get(Counter counter)
{
    return counter._value;
}

public void increment(inout Counter counter, int amount = 1)
{
    counter._value += amount;
}

internal void example(inout Counter counter)
{
    let oldValue = get(counter);  // ordinary call syntax
    counter.increment();          // method call syntax
    let newValue = counter.get(); // method call syntax
}
```

A UFCS approach could address many of the same concerns that our proposal does.
The UFCS-style `get` and `increment` operations above do not have explicit "receiver" parameters, and instead the first ordinary parameter of each (`counter`) serves a similar purpose.
A modifier like `inout` can be used on the first parameter of `increment`, and apply to a call site like `counter.increment()`.

We do not consider UFCS to be a good fit for Slang.
As a practical matter, changing Slang's lookup rules to *truly* unify the meaning of `x.f(a,b,c)` and `f(x,a,b,c)` in all cases would be a daunting task - at present `x.f` and a bare `f` each look up the name `f` in entirely different scopes.
We also think that it is not a good design choice to have every "free" function (global or namespace-scope) be automatically and implicitly usable with method-call syntax.
We think that it is a good thing for the programmer defining an operation to be able to control whether their operation should be usable with method-call syntax or not.



Future Directions
-----------------

This proposal is intentionally as small as we think is possible, while still providing useful functionality.
The main thing that our proposed explicit receiver parameters enable is using the same modifiers (for things like parameter-passing modes) on both ordinary parameters and receiver parameters.

In this section we will describe a few possible directions for future language extensions that intersect with explicit receiver parameters as proposed here.

### Ordinary Functions with Receiver Parameters

When the Slang compiler considers a method-call expression like `x.f(a,b,c)` during semantic checking, it currently only looks up the name `f` in the context of the type `X` of the expression `x` (finding both members declared in the declaration for `X`, as well as `extension`s that apply to `X`).

A conservative extension of that behavior, without going as far as unified function-call syntax (as discussed above in the alternatives considered), would be to allow ordinary global- or namespace-scope function declarations to define receiver parameters.
In the simplest terms, any parameter named `this` would be considered a receiver parameter, and any function with a receiver parameter would be considered as a candidate callee for calls made with method-call syntax.

If this future direction was followed, the `Counter` example might be:

```slang
public struct Counter
{
    internal int _value = 0;
}

public int get(Counter this)
{
    return this._value;
}

public void increment(inout Counter this, int amount = 1)
{
    this._value += amount;
}

internal void example(inout Counter counter)
{
    let oldValue = get(counter);  // ordinary call syntax
    counter.increment();          // method call syntax
    let newValue = counter.get(); // method call syntax
}
```

In the example above, the `get` and `increment` operations are callable with method-call syntax, while the `example` operation is only callable with ordinary call syntax (an expression like `counter.example()` would be diagnosed as an error).

In the context of a method call like `x.f(a,b,c)` the lookup for `f` would consider both the existing scopes it does today (based on the static type `X` of the receiver expression `x`), as well as any in-scope bindings for `f` that could be found via ordinary lexical lookup, and which have a receiver parameter.
Because the new bindings that would be considered are only those using the new syntax for receiver parameters on ordinary functions, backwards compatibility would be maintained.

### Allowing Other Receiver Parameter Positions

This proposal restricts an explicit receiver parameter to always be the first declaration in a parameter list.
There is no technical reason why this has to be the case, so it would be worthwhile to consider whether relaxing the restriction could be worthwhile, or if there are genuine design reasons to maintain the restriction.

Changing the position of an explicit receiver parameter would only be impactful when calls use ordinary function-call syntax (e.g., `Counter.increment(counter, 1)`).
If the preceding future direction of allowing free functions to have receiver parameters were adopted, this case might be more common.

The counter example is one where a receiver-first convention fits both the style of object-oriented method calls (`counter.increment(1)`) and also reads cleanly as an ordinary call: `increment(counter, 1)` reads naturally as "increment `counter` by 1."
If we were to add Swift-style parameter labels to Slang, it would be natural to expose syntax like `counter.increment(by: 1)` and `increment(counter, by: 1)`.

A case where a different convention might be called for is an expression like `canvas.draw(shape)`.
In this case a call expression like `draw(shape, canvas)` is arguably more fluent: "draw the `shape` to the `canvas`".
Adding parameter labels would make this ordering even more obviously preferable: `draw(shape, to: canvas)`.

There are many operations that fit this pattern where the "natural" receiver for an OOP-style method call is not actually the *object* (in the grammatical sense) of the operation, when it is explained in English and, instead, the natural receiver is described in a prepositional phrase after the grammatical object. E.g:

- find `text` in `str` - `str` is the "natural" receiver
- append `element` to `list` - `list` is the natural receiver
- write `data` into `buffer` at `offset` - `buffer` is the natural receiver

It is likely that allowing receiver parameters at positions other than the start of a parameter list would only be considered if we are *also* considering adding support for Swift-style parameter labels.

### "Unscoped" Member Declarations

Above we considered the idea of letting an operation declared *outside* of a type/interface declaration be usable with method-call syntax.
Here we touch on a kind of inverse: allowing an operation declared *inside* of a type/interface to be called with ordinary call syntax (or operator syntax), without having to qualify it with the name of the containing type/interface.

While this future direction would intersect with explicit receiver parameters, it is actually easiest to motivate with operator declarations.
Consider trying to declare an `interface` for types that support a `+` operator (ignoring that there are such interfaces already provided by Slang).
It would be very appealing to write code like the following:

```slang
interface IAddable
{
    static This operator+(This left, This right);
}

struct MyType : IAddable
{
    int data = 0;
    static MyType operator+(MyType left, MyType right) { ... }
}

T sumOfThreeThings<T : IAddable>(T a, T b, T c)
{
    return a + b + c;
}
```

The above code doesn't work at all in Slang today.
The declaration of `operator+` in `IAddable` is not visible to lookup in `sumOfThreeThings`.
Instead, developers who want to define interfaces like these are pushed to write workaround logic like the following:

```slang
interface IAddable
{
    static This add(This left, This right);
}

T operator+ <T : IAddable>(T left, T right)
{
    return T.add(left, right);
}

struct MyType : IAddable
{
    int data = 0;
}

MyType operator+(MyType left, MyType right)
{ ... }

extension MyType : IAddable
{
    static MyType add(MyType left, MyType right) { return left + right; }
}


T sumOfThreeThings<T : IAddable>(T a, T b, T c)
{
    return a + b + c;
}
```

The author of `IAddable` ends up making up an ordinary (non-operator) name for the interface requirement, and then has to define a helper "dispatcher" `operator` declaration.
The author of a concrete type like `MyType` will typically start by defining an ordinary `operator` overload for their type (often out of a desire to not "pay for" the hypothetical overheads of interface dispatch, while actually polluting and expanding the set of overloads that the compiler has to wade through), and then must define additional named operations to make their interface conformance work.

A simple idea that could make the simpler code work while retaining backwards compatibility would be to have a modifier (we'll call it `UNSCOPED` as a placeholder; a better name would be needed) that causes a member declaration inside of a type/interface/extension to be visible to lookup from *outside* of that declaration:

```slang
interface IAddable
{
    UNSCOPED static
    This operator+(This left, This right);
}

struct MyType : IAddable
{
    int data = 0;

    UNSCOPED static
    MyType operator+(MyType left, MyType right) { ... }
}

T sumOfThreeThings<T : IAddable>(T a, T b, T c)
{
    return a + b + c;
}
```

The same `UNSCOPED` approach would also apply to ordinary named interface requirements (e.g., a `sin` requirement for numeric types would not need a secondary dispatcher), and also to non-`static` operations - so long as they have an explicit receiver parameter.
