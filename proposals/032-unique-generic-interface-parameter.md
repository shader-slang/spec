# SP#032: Unique Generic Interface Parameters

## Status

Status: Design Review
Implementation:
Author: Yong He
Reviewer: Theresa Foley, Kai Zhang

## Summary

This proposal introduces a `unique` modifier for generic parameters on an `interface`. This modifier enforces that any concrete type can only conform to that interface with a single, specific generic argument. This new constraint allows the compiler to safely support certain kinds of generic `extension`s that are currently considered dangerous, thereby reducing code duplication and improving expressiveness for common patterns.

## Motivation

The Slang language currently supports generic extensions of the form:

```slang
interface IFoo<T> {}
extension<T, U:IFoo<T>> U { /* ... */ }
```

This pattern is powerful but has been moved to "dangerous territory" and now generates a warning (`Target type U is not dependent on T directly`). The reason for this is that the compiler can only apply an extension to a given type with a single specialization. If a type conforms to the same generic interface multiple times, the choice of which extension to apply becomes ambiguous.

For example, consider the following type:

```slang
struct MyType : IFoo<int>, IFoo<float> {}
```

If we try to use an instance of `MyType` in a context that relies on the generic extension, the compiler cannot uniquely determine whether to apply `extension<int>` or `extension<float>`. The current behavior is to pick the first encountered specialization, which can lead to surprises.

However, there are many legitimate and important use cases for this kind of extension, particularly with interfaces that are conceptually unique per type, such as `IBuffer<T>`, `IArray<T>`, or `IGrid<int DIM>`. In these cases, a user knows that a type will never implement, for instance, both `IBuffer<int>` and `IBuffer<float>`. The current warning discourages these valid patterns and forces users into more verbose or duplicative code.

This proposal aims to resolve this tension by allowing developers to formally declare the uniqueness of an interface's generic parameter. By doing so, we can turn the ambiguous multi-conformance case into a compile-time error and safely enable the powerful generic extension pattern for well-behaved interfaces.

## Proposed Solution

We propose introducing a new contextual keyword, `unique`, which can be applied to a generic parameter in an `interface` declaration.

```slang
// A new 'unique' keyword can modify a generic type parameter.
interface IBuffer<unique T>
{
    T load(int index);
    void store(int index, T value);
}
```

The `unique` keyword introduces a new semantic rule:
**A type cannot have multiple conformances to an interface with a `unique` parameter that differ only by the argument to that `unique` parameter.**

With this rule, the previously problematic example would now become a compile-time error:

```slang
// This declaration is now illegal because 'T' in IBuffer is unique.
struct MyBuffer : IBuffer<int>, IBuffer<float> {}

// ERROR: Type 'MyBuffer' cannot conform to both 'IBuffer<int>'
// and 'IBuffer<float>' because the generic parameter 'T' on
// 'IBuffer' is declared as unique.
```

By enforcing this uniqueness at the type definition site, we provide a strong guarantee to the compiler. This guarantee allows us to safely remove the warning for generic extensions that rely on such interfaces. The following extension would now be considered safe and would not generate a warning:

```slang
// This extension is now safe, as any type 'U' can only
// conform to IBuffer<T> for a single, specific 'T'.
extension<T, U : IBuffer<T>> U
{
    T loadFirst() { return this.load(0); }
}
```

This solution provides developers with a tool to express their design intent clearly, improves type safety, and enables powerful, non-duplicative generic programming patterns.

## Detailed Design

### Syntax

The grammar for `interface` declarations will be modified to optionally allow the `unique` keyword before a generic parameter's name.

```
generic-parameter ::= unique? type-parameter-name
                    | ...
```

This keyword is only valid for generic parameters on an `interface` declaration.

### Compiler Checks

The primary implementation mechanism is a new check performed during semantic analysis, specifically when a type's inheritance list is computed.

1.  When resolving the inheritance for a type `D`, the compiler gathers all its direct and indirect base types (interface conformances).
2.  The compiler will then scan this list for multiple instances of the same generic interface, e.g., `I<A_1, B_1, ...>` and `I<A_2, B_2, ...>`.
3.  If such multiple conformances are found, it will check the declaration of `interface I`. For each generic parameter `P_i` declared as `unique`, it will compare the corresponding arguments (e.g., `A_1` and `A_2`).
4.  If `A_1` is not identical to `A_2` for a `unique` parameter, the compiler will issue a hard error.

### Interaction with Generic Extensions

The compiler check that currently produces a warning for extensions like `extension<T, U:IFoo<T>>` will be relaxed. If the constraint on `U` (i.e., `IFoo<T>`) involves an interface where the parameter `T` is marked `unique`, the warning should be suppressed. The compiler can confidently determine that for any given `U`, there is only one possible `T` that can satisfy the constraint, thus resolving the ambiguity.

## Alternatives Considered

### Maintain the Status Quo

We could leave the warning in place. This is the simplest option but is suboptimal as it discourages useful, safe patterns and leaves the potential for ambiguity-related bugs in user code that ignores the warning.

### Use Associated Types to Enforce Uniqueness

It is possible to achieve uniqueness by reframing the interface using associated types instead of generic parameters. For example:

```swift
// Original
interface IBuffer<T> { ... }

// Alternative with associated type
interface IBufferWithAssociatedType
{
    associatedtype Element;
    Element load(int index);
    void store(int index, Element value);
}
```

A concrete type can only define the `Element` type alias once, naturally enforcing uniqueness.

  * **Pros:** This works within the existing language semantics without new keywords.
  * **Cons:** This approach significantly degrades ergonomics. A function signature that was once simple and clear:
    ```swift
    void processIntBuffer<B : IBuffer<int>>(B buffer);
    ```
    becomes much more verbose and less intuitive:
    ```swift
    void processIntBuffer<B : IBufferWithAssociatedType>(B buffer)
        where B.Element == int;
    ```
    While functionally equivalent, this syntax is more burdensome for developers and harms readability. The `unique` proposal provides the same safety guarantees with a much better user experience.

### Higher-Kinded Types

The problem space has some overlap with higher-kinded types. A more advanced generic system could potentially offer alternative ways to abstract over "buffer-like" types. However, this is a much larger and more complex feature that would require significant design and implementation effort. Furthermore, it is not clear that it would cleanly solve this specific extension ambiguity problem without introducing its own complexities. The `unique` keyword provides a targeted, simple, and effective solution to the problem at hand.

### Keyword Naming
    The keyword `unique` is proposed as it clearly communicates the intent. However, the final name is open to discussion. An alternative like `associated` was briefly considered to hint at the link to associated types, but `unique` was deemed more direct.

## Future Directions and Unresolved Questions

### Deprecating Free-Form Generic `extension`

The discussion that led to this proposal also highlighted a broader issue with the current `extension` mechanism. While this proposal makes `extension<T, U:IFoo<T>>` safer by introducing `unique` parameters, it is worth considering another powerful, and potentially problematic, form of extension: free-form generic `extension.

This pattern takes the form:

```slang
extension<T : IFoo> T : IBar { /* ... */ }
```

This declaration states: "For any type `T` that conforms to `IFoo`, automatically make `T` also conform to `IBar`." While this can be a tool for reducing boilerplate, it introduces several significant problems that complicate the language and make code harder to reason about. This is particularly problematic with checking of `unique` keyword introduced in this proposal.

For example, with this code:
```slang
interface IFoo<T> {}
interface IBar {}
struct Impl : IFoo<int>, IBar {}

// this extension will make Impl conform to two different IFoo!
extension<T:IBar> T: IFoo<float> {} 
```
It will be difficult for the compiler to find out who to blame for the duplication.

The free form extension feature was originally implemented as a workaround to absence of default interface method implementations. Now that Slang is now supporting default interface methods with [SP #030](030-interface-method-default-impl.md), this main use of free-form generic extensions now has a better substitute and should be deprecated instead.
