# Name Lookup

Name lookup is the procedure for resolving a name. The result is a declaration denoted by that name.

## Grammar

Name:

> *`name`* = *`unqualified-name`* | *`global-name`*

Unqualified name:

> *`unqualified-name`* = *`identifier`*

Name in global namespace:

> *`global-name`* = **`'::'`** *`identifier`*

Namespace identifier when *`identifier`* names a namespace:

> *`namespace-identifier`* = *`identifier`*

Type identifier expression when *`identifier`* names a type:

> *`type-identifier`* = *`identifier`*

Member identifier when *`identifier`* names a member of a [`struct`](types-struct.md), a
[`class`](types-class.md), an [`enum`](types-enum.md), a [`namespace`](TODO.md), a
[`vector`](types-vector-and-matrix.md), or a [`matrix`](types-vector-and-matrix.md):

> *`member-identifier`* = *`identifier`*

Non-static member lookup:

> *`value-expr`* **`'.'`** *`member-identifier`*

Static member lookup:

> (*`namespace-identifier`* | *`simple-type-spec`* | *`value-expr`*) **`'.'`** *`member-identifier`*

Compatibility static member lookup:

> (*`namespace-identifier`* | *`simple-type-spec`*) **`'::'`** *`member-identifier`*

Pointer member lookup:

> *`pointer-value-expr`* **`'.'`** *`member-identifier`*

Compatibility pointer member lookup:

> *`pointer-value-expr`* **`'->'`** *`member-identifier`*

> 📝 **Remark 1:** Accessing a static member through a value with `::`, or through a pointer with `->`, is
> deprecated and not listed here.

### Parameters

- *`identifier`* is a [lexical identifier](lexical-structure.md).
- *`simple-type-spec`* is a [type expression](types.md) that names a type but does not declare one.
- *`value-expr`* is a [value expression](expressions.md).
- *`pointer-value-expr`* is a [value expression](expressions.md) that has a [pointer type](types-pointer.md).

> 📝 **Remark 2:** Relationships between identifiers and value and type expressions:
> - [Identifier expression](expressions-identifier.md) is a *`value-expr`*.
> - *`type-identifier`* is a [*`simple-type-spec`*](types.md).

## Description

There are two kinds of name lookup in Slang:
- [unqualified name lookup](#unqualified-name-lookup), in which the name has no prefix as a qualifier.
- [member lookup](#member-lookup), in which the lookup is performed in the context of:
  - a [`namespace`](TODO.md). This includes *`global-name`* lookup.
  - a [`struct`](types-struct.md), a [`class`](types-class.md), or an [`enum`](types-enum.md) type.
  - a value of a [`struct`](types-struct.md), a [`class`](types-class.md), or an [`enum`](types-enum.md) type.

A member is static when it is:
- a [`namespace`](TODO.md).
- a member of a [`namespace`](TODO.md). This includes [variables](declarations-variable.md),
  [bindings](declarations.md), and [functions](declarations-functions.md) that are not members of a type.
- a [static data member](types-struct.md) or a
  [static member function](types-struct.md#static-member-function).
- a named constant of an [enumeration](types-enum.md).
- a [type](types.md), a [type alias](types.md#alias), or an [associated type](types-interface.md).

A member is non-static when it is:
- a non-static [data member](types-struct.md) or
  [member function](types-struct.md#nonstatic-member-function) of a
  [`struct`](types-struct.md), a [`class`](types-class.md), or an [`enum`](types-enum.md).

The left-hand side operand of the static member lookup is either a value or a type. When the operand is a
value, the lookup is performed on the type of the value and the value is ignored.

The left-hand side operand of the non-static member lookup is a value of a [`struct`](types-struct.md),
[`class`](types-class.md), or [`enum`](types-enum.md) type.

The left-hand side operand of a pointer member lookup is a [pointer-typed](types-pointer.md) value. Static and
non-static member lookups are performed on the dereferenced value.

The recommended operator for all member access is `.`. Operators `::` and `->` are provided for compatibility.

The name lookup procedure consists of the following steps:

1. [Unqualified name lookup](#unqualified-name-lookup) or [member lookup](#member-lookup) is performed. The
   result is a set of declarations referred to by the name.
2. The [lookup result](#lookup-result) is processed, and the set is narrowed down to a single declaration. It
   is an error if this cannot be done.

> 📝 **Remark 3:** Unqualified lookup does not consider visibility. Inaccessible declarations are filtered out
> in [overload resolution](expressions-overload-resolution.md) and [lookup result](#lookup-result) handling.

<a id="unqualified-name-lookup"></a>
## Unqualified Name Lookup

The lookup procedure is expected to differ significantly between Slang 2018–2026 and Slang 202c.

### Common for All Slang Language Versions

Given an identifier, the unqualified name lookup searches the current [scope](basics-scope.md) and then the
enclosing scopes, up to and including the global namespace.

The enclosing scopes of a declaration include the scopes of the types, `extension` declarations, and generic
declarations that contain it. For example, in the body of a member function, the members of the enclosing type
are found by unqualified lookup. See [scope](basics-scope.md) for the details on scopes.

Lookup has a context-based filter:
- In value and type expression lookups, variable, function, type, and namespace declarations are looked
  up. All other declarations are ignored.
- In [attribute expression](attributes.md) lookups, the lookup uses a two-step approach:
  1. Only attribute declarations are looked up. All other declarations are ignored.
  2. If no results were found in step 1, then for name `Foo`, `FooAttribute` is looked up as a type.
- In [semantic expression](shaders-and-kernels.md) lookups, only semantic declarations are looked up. All
  other declarations are ignored.

> 📝 **Remark 4:** `slangc` also has modifier syntax declarations and attribute syntax declarations. These are
> `slangc` internals and outside the scope of this document.

> 📝 **Remark 5:** [Capability expression](shaders-and-kernels.md) lookups use a separate non-scoped lookup
> procedure for capability definitions. These are `slangc` internals and outside the scope of this document.

> 📝 **Remark 6:** In attribute lookup, `FooAttribute` is expected to be a struct type, providing a
> user-defined attribute.

### Slang 2018–2026

Lookup searches one scope at a time. The declarations that `using namespace` declarations make visible in a
scope, and the declarations of imported modules in the same namespace, are searched together with that
scope. Lookup terminates early if the first non-empty per-scope lookup result contains a single
non-overloadable declaration. Otherwise, lookup continues in the enclosing scopes and combines the results.

A `using namespace` declaration adds all declarations in that namespace to the scope of the `using namespace`
declaration.

The [`cbuffer`](types-special.md#cbuffer-and-tbuffer) and [`tbuffer`](types-special.md#cbuffer-and-tbuffer)
declarations without an instance name, and the unscoped [`enum`](types-enum.md) declarations, are
_transparent_. Their members are looked up as if they were in the same scope as the declaration itself. An
`enum` is unscoped when it has the
[\[UnscopedEnum\]](https://docs.shader-slang.org/en/latest/external/core-module-reference/attributes/unscopedenum-08.html)
attribute or when it is compiled with the `-unscoped-enum` option.

> ⚠️ **Warning 1:** The Slang 2018–2026 name lookup, overload resolution, and declaration shadowing rules have
> several caveats. `slangc` diagnoses these issues as warnings on a best-effort basis.

### Slang 202c

This section is incomplete.

> 📝 **Remark 7:** Name lookup improvements for Slang 202c are tracked by GitHub issue
> [#13979](https://github.com/shader-slang/slang/issues/13979).

<a id="member-lookup"></a>
## Member Lookup

Given a base expression and an identifier, the member lookup returns all members associated with that
identifier.

If the base expression is:
- a namespace, declarations in the namespace are considered.
- a `struct`, `class`, or `enum` type, the static members of the type are considered.
- a value of a `struct`, `class`, or `enum` type, the static and non-static members of the type are
  considered.
- a value of pointer type, the static and non-static members of the pointed-to type are considered.
- a value of an [interface](types-interface.md) type, or of a generic type parameter constrained by an
  interface, the requirements of the interface are considered.

A special case of member lookup is the lookup for a global name (*`global-name`*), that is, the `::` prefix
before the identifier. This denotes a lookup in the [global namespace](basics-scope.md).

The members of a type include the members that [`extension`](types-extension.md) declarations add to the type,
and the members inherited from its base types.

> ⚠️ **Warning 2:** Accessing a static member through a value with `::`, or through a pointer with `->`, is
> deprecated and may be removed in a future Slang language version.

> 📝 **Remark 8:** Associated types and the `This` type are looked up as members. See
> [interfaces](types-interface.md), [generics](generics.md), and [`This` type](types-this.md).

> 📝 **Remark 9:** For values of [`vector`](types-vector-and-matrix.md) and
> [`matrix`](types-vector-and-matrix.md) types, swizzle expressions can combine multiple members. These are
> handled separately. See [Vector and Matrix Types](types-vector-and-matrix.md) for details.

> 📝 **Remark 10:** See [scope](basics-scope.md) for a detailed description of type scopes, including nested
> scopes and inherited members.

<a id="lookup-result"></a>
## Lookup Result

The result handling is expected to differ significantly between Slang 2018–2026 and Slang 202c.

### Slang 2018–2026

Unqualified name lookup or member lookup results in a set of candidate declarations. The set is narrowed down
to a single declaration as follows:

1. Declarations that are not accessible from the referencing location are removed.
2. Declarations that do not fit the context of the name are removed:
   - Where a type is expected, only type declarations are kept.
   - Where a value of a known type is expected, declarations whose values cannot be converted to that type
     are removed.
3. If the name is called, [overload resolution](expressions-overload-resolution.md) selects the best candidate
   among the remaining declarations. Declarations that cannot be called with the given arguments are not
   candidates.
4. Otherwise, if a single declaration remains, the name refers to that declaration.
5. Otherwise, it is an error: either no declarations remain, or the reference is ambiguous.

### Slang 202c

This section is incomplete. See Remark 7.

## Examples

Basic name lookup:

```slang
RWStructuredBuffer<int> output;

[numthreads(1,1,1)]
void main(uint3 tid : SV_DispatchThreadID)
{
    // First, an unqualified name lookup is performed for 'tid'.
    // 'tid' is found in the scope of the function parameters, and it
    // denotes the first parameter.
    //
    // Then, 'x' is looked up in the type of the value referenced by 'tid'. Since
    // 'tid' is of type vector<uint, 3>, it has the member 'x'. 'x' refers
    // to the first vector element (element index 0).
    let v = tid.x;

    // The left side of the assignment performs a member lookup in the
    // global namespace, which has the static member 'output'. 'output'
    // refers to a variable of type RWStructuredBuffer<int>, which
    // declares a subscript operator. That operator is used for the
    // assignment.
    //
    // The argument for the subscript operator is 'v'. This is an
    // unqualified name lookup, and 'v' is found in the current scope (the
    // let declaration).
    ::output[v] = 1;
}
```

Overloaded callable lookup:

```slang
uint myFunc(uint i)
{
    return i + 1;
}

uint myFunc(int i)
{
    return (uint)(i * 123);
}

uint myFunc(uint i, uint j)
{
    return i + j;
}

uint myFunc(int i, int j)
{
    return i + j;
}

RWStructuredBuffer<uint> output;

[numthreads(1,1,1)]
void main(uint3 tid : SV_DispatchThreadID)
{
    // In the right side, myFunc is called with two arguments, types: uint, uint
    //
    // The unqualified name lookup finds the following declarations:
    // 1. uint myFunc(uint i)
    // 2. uint myFunc(int i)
    // 3. uint myFunc(uint i, uint j)
    // 4. uint myFunc(int i, int j)
    //
    // Declarations 1 and 2 are not considered in overload resolution, since
    // they cannot be called by two argument.
    //
    // Of the remaining candidates, declaration 3 is the best, since it does not
    // require argument conversions whereas declaration 4 does. Hence, the
    // declaration 3 is selected as the target for the call expression.
    let v = myFunc(tid.x, tid.y);

    output[0] = v;
}
```
