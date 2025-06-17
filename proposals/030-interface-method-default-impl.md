# SP#030: Default Implementation of Interface Methods

## Status

Status: In Experiment

Implementation: [PR 7439](https://github.com/shader-slang/slang/pull/7439)

Author: Yong He

Reviewer: 

## Background

Often times, an interface method is implemented trivially for all but a few conforming types. This arises most often when an existing interface
is extended to support an additional feature that is only provided or meaningful for a new type that conforms to the interface. Currently, a
developer must manually duplicate the trivial implementation for all existing types after extending the interface, which is a laborious process.

This proposal is to allow interface methods to have a default implementation, that will be used by a conforming type to satisfy the interface
requirement, if the conforming type does not provide its own implementation of the method. Note that other types of requirements, such as properties, subscript operators, associated types and associated constants are not covered by this proposal and default implementation for these types of requirements will remain unsupported.

## Proposed Solution

We propose to allow interface methods to have a body that serves as the default implementation:

```slang
interface IFoo
{
    int getVal()
    {
        return 0;
    }
}

struct Impl : IFoo
{
    // OK, using IFoo.getVal() to satisfy the requirement.
}

struct Impl2 : IFoo
{
    // OK, overriding the default implementation.
    override int getVal() { return 1; }
}
```

Both static and non-static methods can have default implementations.

A default implementation can be marked as `[Differentiable]` for automatic differentiation.

Default implementations is treated as if it is an ordinary function generic on `This` type. The `IFoo` interface above will
be interpreted by the compiler as:

```slang
interface IFoo
{
    [HasDefaultImpl(IFoo_getVal_defaultImpl)]
    int getVal(); // the requirement.
}

// pseudo syntax:
__generic<This:IFoo>
int IFoo_getVal_defaultImpl(this:This)
{
    return 0;    
}

struct Impl : IFoo
{
    .getVal := IFoo_getVal_defaultImpl<Impl>;
}
```

Note that a method in a confirming type that overrides the default implementation in the interface must be explicitly marked as `override`. Overriding a function that is not declared in any base interfaces is an error.

### `override` in Interfaces

A method with a default implementation in an interface cannot be marked `override`, and will not 
override any requirements in the base interfaces. Consider the following:

```slang
interface IBase
{
    int getVal() { return 0; }
}
interface IDerived : IBase
{
    int getVal() { return 1; }
}
sttruct Impl : IDerived {}

int testBase<T:IBase>(T v)
{
    return v.getVal();
}
void main()
{
    Impl impl = {};
    printf("%d\n", testBase(impl));
}
```

Should the output be `0` (calling `IBase.getVal`) or `1` (calling `IDerived.getVal`)? Both behaviors are reasonable.
For simplicity, the current decision is to treat `IBase.getVal` and
`IDerived.getVal` as distinct requirements, so calling `testBase(impl)` should return `0`, and calling `testDerived(impl)` should return `1`.
That is, the existence of `IDerived.getVal` will not override the requirement from `IBase.getVal`.

Using `override` keyword on an interface method is considered an error.

### Constructors

For simplicity, constructors/initializers are not allowed to have a defualt implementation in interfaces.

### Storage Accessors

`get`, `set` and other storage accessors for properties or subscript operations are not allowed to have a default implementation in interfaces.

## Related Work

Default implementations are proven to be a useful feature and are commonly supported in modern languages. They are allowed in Rust traits Swift protocols, and C# interfaces (since C# 8.0).
