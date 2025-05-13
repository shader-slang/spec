# Type System for Compile-Time and Run-Time Existential Values

This proposal adds `some` and `dyn` keyword for explicitly specifying whether or not an interface type can be used in dynamic dispatch.

## Status

Status: Design Review

Implementation: 

Author: Yong He

Reviewer: 

## Background

Currently, Slang allows interface types to be used directly to declare a variable, a function parameter, or a struct field. If the compiler is able to deduce the actual type of the var decl, it will specialize the code as if the variable is declared with the deduced type. If this type info is not known at compile time, our compiler will fallback to emit dynamic dispatch logic for the var decl. This can lead to surprises since the user can trigger dynamic dispatch logic unintentionally and pay for the runtime cost. This design violates Slang's philosophy that all non-trivial runtime overhead should only be introduced explicitly by the programmer. Another big down side is that our dynamic dispatch logic can only handle ordinary data types. If a type implementing an interface contains opaque types such as `Texture2D`, the dynamic dispatch pass will fail and give user confusing error messages. The decision of whether or not a variable or a type is allowed to be involved in dynamic dispatch has non-trivial effect in both runtime performance and coding restrictions. Therefore this should be modeled as a part of the type system.

## Proposed Solution

### Language Version

We introduce Slang language version 2026, which can be enabled with compiler flag -lang 2026. By default, the compiler assumes language version 2025. Many breaking changes in this proposal is behind language version 2026.

### Dynamic interface types

Interface types that can be used for dynamic dispatch must be qualified with the `dyn` keyword. Interface types decorated with the existing `[anyValueSize(n)]` attribute are assumed to be qualified with `dyn`. For example:

```
// Define an interface that can be used in dynamic dispatch.
dyn interface IFoo
{
    float compute(int x);
}
```

By default, a `dyn` interface is subject to the following restrictions, unless language version is 2025 or `-enable-experimental-dynamic-dispatch` flag is present:

1. The interface itself cannnot be generic.
1. It must not define any associated types.
1. It must not define any generic methods.
1. It must not define any mutating methods.
1. It cannot contain any methods that has a `some IFoo` return type, or has any `some IFoo` parameters.

Any type that conforms to one or more `dyn` interface is subject to these restrictions:

1. The type itself must be an ordinary data type, meaning that it cannot contain any fields that are opaque or non-copyable or unsized.

In addition, such types are subject to these restrictions unless language version is 2025 or `-enable-experimental-dynamic-dispatch` flag is present:

1. The type itself cannot be generic.

### Use of interface types

If a variable, a parameter or a struct field is declared to have an interface type or array of interface type, the var decl must be qualified with either the `some` keyword or the `dyn` keyword. If the var decl is not explicitly qualified with `some` or `dyn`, the compiler implicitly qualifieds the type as `some` when language version is 2026 or later, or as `dyn` in language version 2025.

The concrete type of a `some` qualified var decl must be compile-time deducible and will never involve in dynamic dispatch. The concrete type of a `dyn` qualified var decl may not be compile-time deducible and may involve in dynamic dispatch. 

The following rules apply to `some` and `dyn` qualifiers on var decls:

1. A `some IFoo` type is valid only if `IFoo` is an interface type.
1. A `some IFoo` type can only be used on a function parameter or a local variable. Struct fields or global variables cannot have a `some` type.
1. A `some IFoo` type cannot appear in any complex type expression. For example, `some IFoo*`, `some IFoo[2]`, `Tuple<some IFoo, some IFoo>` etc. are not allowed.
1. A local variable of `some IFoo` type cannot be assigned or initialized more than once throughout its lifetime.
1. If a function returns `some IFoo`, then all return statements must return values of exactly the same type.
1. If a function contains a `out some IFoo` parameter, then all values assignmened to the parameter must have exactly the same type.
1. Two different var decls of `some IFoo` type are considered to have **different** types.
1. A `dyn IFoo` type is valid only if `IFoo` is an interface type with `dyn` qualifier.
1. A value of `dyn` interface type cannot be assigned to a location of `some` interface type, but the opposite direction is OK.
1. Attempting to use a `dyn` or `some` typed value before initialization is an error.

Here is an example demonstrating the rules:

```
dyn interface IDyn
{
    // error: dyn interface cannot contain generic method.
    void computeGeneric<T>();

    void compute(float v);
}

interface IFoo
{
    [mutating]
    void computeFoo(float v);
}

struct Opaque : IDyn
{
    Texture2D b; // error: type conforming to dyn interface cannot be opaque.
    ...
}

// OK.
struct Opaque1 : IFoo
{
    ...    
}

struct Ordinary : IDyn
{}

void callee(some IFoo b) {}

void output(out some IFoo b) {}

void modify(inout some IFoo b) {}

void test(inout some IFoo out, some IFoo f)
{
    out = f; // error: type mismatch.
    out.computeFoo(1.0); // OK, calling mutable methods on a some type.
    dyn IFoo d = f; // OK, assigning `some IFoo` to `dyn IFoo`.
    some IFoo s = d; // error: type mismatch.
    callee(d); // error: type mismatch `dyn IFoo` and `some IFoo`.
    callee(f); // OK.

    some IFoo foo;
    output(foo); // OK, initializing `foo` the first time.
    modify(foo); // OK.
    output(foo); // error, initializing `foo` more than once.
    foo = ...; // error, assigning to `foo` more than once.

    some IFoo foo1;
    for (int i = 0; i < 1; i++)
    {
        // error, assigning to `foo1` inside a loop, potentially
        // initializing it more than once.
        output(foo1);
    }

    dyn Opaque v; // error, invalid type.
    dyn IFoo v1; // error, `IFoo` is not `dyn` interface.
}

some IFoo global; // error: cannot use some type in global variable.
struct Invalid
{
    some IFoo field; // error, cannot use some type in struct field.
}
```

### Implementing `dyn` type

A `dyn IFoo` type should be treated exactly like `IFoo` type as today, they will be represented as a `DeclRefType` referencing `IFoo`.
The existing type system should just work for the `dyn` case.

### Implementing `some` type

A `some` type declaration should be considered as its own `Decl` in Slang's type system. For example, consider the following code:

```
interface IFoo {}
void compute(some IFoo f1, some IFoo f2)
{
    ...
}
```

This should be translated into:

```
// Compiler should insert a `some_type` as a member of the function,
// and translate `f` to a `DeclRefType` referencing `__type_of_f_IFoo`.
//
void compute(__type_of_f1_IFoo f1, __type_of_f2_IFoo f2)
{
    some_type __type_of_f1_IFoo : IFoo;
    some_type __type_of_f2_IFoo : IFoo;
}
```

An interesting case is when the user declares a local variable of `some IFoo` type:

```
struct Concrete : IFoo {}

void output(out some IFoo f, some IFoo f1) { f = f1; }
void test()
{
    some IFoo o;
    Concrete c;
    output(o, c);
}
```

When checking this code, we will first convert the some types into actual decls:

```
void output(out __type_of_output_f_IFoo f, __type_of_output_f1_IFoo f1)
{
    unbound_some_type __type_of_output_f_IFoo : IFoo;
    some_type __type_of_output_f1_IFoo : IFoo;
    f = f1;
}
void test()
{
    unbound_some_type __type_of_test_o_IFoo : IFoo;
    __type_of_test_o_IFoo o;
    Concrete c;
    output(o);
}
```

Note that all local variables or `out` parameters of `some IFoo` type is converted into `unbound_some_type` decls. 
`in` or `inout` parameters of `some IFoo` type will be converted into `some_type` decls.
When checking the call to `output(o)` in `test()`, we will encounter a type mismatch, because
`o` is of type `__type_of_test_o_IFoo`, and `output`'s parameter type is `__type_of_output_f_IFoo`.
To allow this code to work, we will add a type coercion rule that enables a `DeclRefType` of a `some_type(IFoo)` or `unbound_some_type(IFoo)` to coerce into `unbound_some_type(IFoo)`.

Note that we will still disallow any coercions of `some_type` or `unbound_some_type` into a `some_type`, so we can still diagnose the type mismatches in cases like:

```
void test(inout some IFoo f1, some IFoo f2)
{
    f1 = f2; // error, type mismatch
}
```

In order to diagnose cases such as:

```
void test(some IFoo f1, some IFoo f2)
{
    some IFoo o;
    o = f1;
    o = f2; // should error here
}
```

We need to implement a separate check in an IR pass to ensure variables of `some` type is never written to more than once in its lifetime.

### Lowering to IR

Both `dyn` type and `some` type should lower to IR in the same way. That is, `some IFoo` and `dyn IFoo` should both lower to `%IFoo = IRInterfaceType`. Once we reach IR, there is no longer any distinction between `some` or `dyn` type.

The one exception is that variables or parameters of `some` type will be emitted with a IR decoration, so our IR validation pass can identify these variables or parameters and check if they are being written to more than once.
