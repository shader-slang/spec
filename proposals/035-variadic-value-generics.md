SP #035: Variadic Generic Value Parameters
==========================================

This proposal extends Slang's variadic generics (SP #007) to support variadic *value* parameters in addition to variadic type parameters. A variadic value parameter declares a pack of compile-time integer (or enum) values that can be used in generic types and functions.

Status
------

Status: Implemented.

Author: Yong He.

Implementation: [PR 10415](https://github.com/shader-slang/slang/pull/10415)

Background
----------

SP #007 introduced variadic generic type parameters, enabling types and functions to accept an arbitrary number of type arguments. This has been used successfully for tuples, `IFunc`, `printf`, and other use cases.

However, there are scenarios where a generic needs to be parameterized by a variable number of compile-time *values* rather than types. A motivating example is a multi-dimensional array or tensor type parameterized by its dimensions:

```
struct Tensor<let each D : int>
{
    int getRank() { return countof(D); }
}

Tensor<2, 3, 4> t; // A 2x3x4 tensor
```

Without variadic value parameters, users must define separate types for each possible number of dimensions (`Tensor1D<N>`, `Tensor2D<M, N>`, `Tensor3D<L, M, N>`, etc.), or use a fixed-size array of dimensions that loses compile-time type safety.

Other use cases include:
- Compile-time shape descriptors for GPU buffer layouts
- Statically-sized multi-dimensional containers
- Compile-time configuration packs (e.g., a set of feature flags or channel counts)

Related Work
------------

C++ supports non-type template parameter packs (`template<int... Ns>`), which this feature mirrors conceptually. Swift's variadic generics (which SP #007 follows) only support type parameter packs, not value parameter packs. This proposal extends Slang beyond Swift's model to also support value packs.

Proposed Approach
-----------------

### Syntax

A variadic value parameter is declared using `let each` followed by the parameter name and element type:

```
struct Dims<let each D : int> { ... }
```

An alternative traditional syntax is also supported, mirroring the existing `int N` syntax for scalar value parameters:

```
struct Dims<each int D> { ... }
```

Both syntaxes create a `GenericValuePackParamDecl` AST node. The parameter's type is `ValuePackType(elementType)`.

### Instantiation

A variadic value generic is instantiated by providing zero or more compile-time constant values:

```
Dims<>          // empty pack
Dims<4>         // single element
Dims<2, 3, 4>   // three elements
```

At the AST level, `Dims<1, 2, 3>` evaluates to `GenericAppDeclRef(Dims, args=[ConcreteIntValPack(1, 2, 3)])`.

### `countof`

`countof` returns the number of elements in a value pack, just as it does for type packs:

```
struct Dims<let each D : int>
{
    int getDimCount() { return countof(D); }
}
```

### `expand` and `each`

The `expand` and `each` keywords work with value packs the same way they work with type packs. Use `each D` inside an `expand` expression to refer to individual elements of the value pack:

```
struct Dims<let each D : int>
{
    void print()
    {
        expand printf("%d\n", each D);
    }
}
```

`each D` can be used to instantiate other generic types:

```
struct Wrapper<let N : int> { int get() { return N; } }

struct WrapAll<let each D : int>
{
    void printValues()
    {
        expand printf("%d\n", Wrapper<each D>().get());
    }
}
```

Arithmetic on pack elements is supported:

```
expand add(s, (each D) + 1);
```

### Forwarding and Combining Value Packs

Value packs can be forwarded as generic arguments:

```
void printDims<let each D : int>(Dims<D> d) { d.print(); }
```

Multiple packs can be combined:

```
Dims<A, B> merge<let each A : int, let each B : int>()
{
    return Dims<A, B>();
}
```

`expand` can be used in generic arguments to transform pack elements:

```
Dims<A, expand (each B) + 1> transform<let each A : int, let each B : int>()
{
    return Dims<A, expand (each B) + 1>();
}
```

### Mixed Scalar and Pack Parameters

A generic can have both scalar value parameters and value pack parameters:

```
int weightedSum<let scale : int, let each D : int>()
{
    int s = 0;
    expand add(s, scale * each D);
    return s;
}
```

### Generic Argument Deduction

Value pack parameters can be deduced from function arguments:

```
void printDims<let each D : int>(Dims<D> d) { d.print(); }

void test()
{
    Dims<10, 20, 30> d;
    printDims(d); // D is deduced as {10, 20, 30}
}
```

### Element Type

The element type of a value pack can be any type valid for scalar generic value parameters, including integer types and enums:

```
enum Color { Red, Green, Blue }

struct ColorSet<let each C : Color>
{
    void print()
    {
        expand printf("%d\n", int(each C));
    }
}
```

### Restrictions

- Value pack parameters must appear after all non-pack parameters. A diagnostic is emitted if this rule is violated.
- Same as variadic type parameters, when multiple value pack parameters are present, the number of arguments at specialization site must be evenly divisible by the number of packs.

Detailed Explanation
--------------------

### AST Representation

A variadic value parameter is represented by `GenericValuePackParamDecl`, which inherits from `VarDeclBase` (like `GenericValueParamDecl`). Its type is `ValuePackType(elementType)`, a new AST type that wraps the element type and allows the type system to distinguish pack parameters from scalar parameters.

A concrete pack of values is represented by `ConcreteIntValPack`, which holds a list of `IntVal` operands. This mirrors `ConcreteTypePack` for type packs. `ConcreteIntValPack` has flattening semantics: nested packs are automatically flattened during construction via `ASTBuilder::getIntValPack()`.

The `ExpandIntValPack` and `EachIntVal` nodes mirror `ExpandType` and `EachType` for value-level expansion and indexing. `ASTBuilder::getExpandIntValPack()` and `getEachIntVal()` apply identity folding rules:
- `expand each D` => `D`
- `each expand P` => `P`

### Generalized `ExpandType`

The `ExpandType` node's captured pack operands have been widened from `Type*` to `Val*`. This allows a single `ExpandType` to capture both type pack references (`DeclRefType(GenericTypePackParamDecl)`) and value pack references (`DeclRefIntVal(GenericValuePackParamDecl)`). The substitution logic in `ExpandType::_substituteImplOverride` handles both `ConcreteTypePack` and `ConcreteIntValPack` as concrete pack types.

### Generalized `CountOfIntVal`

The `SizeOfLikeIntVal` base class has been widened from `Type*` to `Val*` for its operand. This allows `CountOfIntVal` to store a value pack reference directly (as a `DeclRefIntVal`) rather than requiring a type. `CountOfIntVal::tryFoldOrNull` handles `ConcreteTypePack`, `TupleType`, and `ConcreteIntValPack`.

### IR Representation

A new IR type `IRValuePackType(elementType)` represents the type of a generic value pack parameter in IR generics. When a generic is lowered, each `GenericValuePackParamDecl` becomes an `IRParam` whose type is `IRValuePackType(elementType)`.

When the generic is specialized (e.g., `Dims<1, 2, 3>`), the specialization argument for the pack parameter is `MakeValuePack(1, 2, 3)` whose type is `TypePack(int, int, int)`. The existing IR specialization infrastructure handles `MakeValuePack` captures in `IRExpand`, and `maybeSpecializeCountOf` resolves `countof(MakeValuePack(...))` by counting elements in the `TypePack` data type.

### Argument Matching

The trailing pack detection in `matchArgumentsToParams` uses `isPackType()` which recognizes both `isTypePack()` and `ValuePackType`. When a single argument's type is already a pack type, it is passed through directly (no `PackExpr` wrapping). Value pack arguments are constant-folded via `tryConstantFoldExpr`, which handles `PackExpr`, `ExpandExpr`, `EachExpr`, and `DeclRefExpr(GenericValuePackParamDecl)`.

### Constraint Solving

`TryUnifyIntParam` in the constraint system has been extended to handle `GenericValuePackParamDecl` declarations, creating constraints when a value pack parameter is unified with a concrete value. The constraint solving phase accumulates `ConcreteIntValPack` solutions for value pack parameters and builds the final generic arguments.

Alternatives Considered
-----------------------

Given we have the existing system for variadic type parameters, introducing variadic value parameters is a natural and incremental extension to Slang's generics system. For this reason, we are not considering any other alternative solutions.
