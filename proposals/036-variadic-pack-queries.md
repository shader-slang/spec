SP #036: Variadic Pack Queries and `nonempty(...)`
==================================================

We should add built-in pack-query operators to Slang so that code can inspect
and structurally decompose type packs and value packs. In particular, this
proposal adds `__first(P)`, `__last(P)`, `__trimFirst(P)`, and `__trimLast(P)`,
along with a `where nonempty(P)` generic constraint that can be used to prove
that a pack is non-empty.

These operations fill an important expressivity gap in Slang's variadic
generics. Proposal [007](007-variadic-generics.md) introduced `expand`/`each`
and the notion of type packs and value packs, but it did not provide a way to
inspect the front or back of a pack. Without that capability, it is difficult
to express recursive or "sliding window" relationships over packs, especially
for library code that wants to stay entirely inside the type system.

Status
------

Status: Implemented

Implementation: [PR 10444](https://github.com/shader-slang/slang/pull/10444)

Author: Yong He

Reviewer: TBD

Background
----------

Slang already supports variadic generics with `each` and `expand`, including
both type packs and value packs. This allows users to write declarations like:

```slang
void f<each T>(expand each T values) { ... }
int g<let each D : int>() { ... }
```

and to build pack-shaped types and values with `expand`.

However, there is currently no way to ask basic structural questions about a
pack:

- What is the first element of the pack?
- What is the last element of the pack?
- What remains after removing the first or last element?

Those questions come up naturally when a user wants to express relationships
between adjacent pack elements, or write APIs that recurse over a pack one
element at a time.

For example, consider a library that wants to describe a multi-layer network in
terms of a value pack of layer sizes:

```slang
struct Layer<int InSize, int OutSize> { ... }

typealias MLP<let each D : int> =
    Tuple<expand Layer<each __trimLast(D), each __trimFirst(D)>>;
```

This pattern requires a way to talk about the pack with its first or last
element removed. Similarly, a library may want to talk about the type of the
first element in a type pack:

```slang
struct FirstTypeHolder<each T> where nonempty(T)
{
    __first(T) value;
}
```

There is also an important safety question: operations like "take the first
element" are partial. For an empty pack, `__first(P)` and `__last(P)` have no
meaning. The language therefore needs a way to express and check that a pack is
known to be non-empty.

Related Work
------------

Many languages and metaprogramming systems have some notion of decomposing or
indexing a variadic sequence:

- C++ variadic templates support pack expansion, and newer work in the language
  adds pack indexing. These features solve similar problems, but at the syntax
  level are oriented around template metaprogramming rather than Slang's
  first-class pack values and types.
- Functional languages commonly model sequence decomposition using
  "head"/"tail"-style operations. The proposed `__first` and `__trimFirst`
  operators deliberately mirror that style because it is direct and familiar.
- Swift's variadic generics provide strong prior art for pack-shaped generic
  programming, which also informed proposal [007](007-variadic-generics.md).

This proposal intentionally chooses a small set of direct structural queries
instead of a larger meta-programming feature such as a general-purpose fold.

Proposed Approach
-----------------

We propose to add four built-in pack-query operators:

- `__first(P)`
- `__last(P)`
- `__trimFirst(P)`
- `__trimLast(P)`

These operators are available on:

- generic type packs,
- generic value packs,
- concrete type packs,
- concrete value packs,
- tuple types and tuple values,
- pack-shaped results produced by `expand`.

We also propose to add a generic constraint form:

```slang
where nonempty(P)
```

where `P` is a generic type pack parameter or generic value pack parameter.

The intent is:

- `__first(P)` returns the first element of `P`
- `__last(P)` returns the last element of `P`
- `__trimFirst(P)` returns `P` with its first element removed
- `__trimLast(P)` returns `P` with its last element removed

`__first(P)` and `__last(P)` are partial operations and therefore require the
compiler to prove that `P` is non-empty. `__trimFirst(P)` and `__trimLast(P)` are
total operations and yield an empty pack when applied to an empty pack.

The operators use reserved builtin names with a leading `__` instead of plain
names like `first` or `trimHead`. This avoids parser ambiguity and shadowing
problems in type contexts, while still leaving room for user-defined functions
named `first`, `last`, etc.

Detailed Explanation
--------------------

### Syntax

The pack-query operators use the following syntax:

```text
pack-query-expr
    ::= '__first' '(' expr ')'
     |  '__last' '(' expr ')'
     |  '__trimFirst' '(' expr ')'
     |  '__trimLast' '(' expr ')'
```

The `expr` operand is interpreted according to context. In expression context it
is an ordinary expression that evaluates to a pack-shaped value or tuple. In
type context it is a type expression whose resulting type is pack-shaped.

The non-empty constraint uses the syntax:

```text
where-clause
    ::= ...existing forms...
     |  ['optional'] 'nonempty' '(' identifier ')'
```

This proposal deliberately specifies that `optional nonempty(...)` is invalid.
It may be parsed for consistency with existing `where`-clause machinery, but it
is rejected by semantic checking.

### Valid Operands

The operand `P` of a pack-query operator may denote any of the following:

- a type pack,
- a value pack,
- a tuple type,
- a tuple value,
- a pack-shaped expression formed from `expand`,
- a pack query result such as `__trimFirst(P)`.

The result category follows the operand:

- If `P` is a type pack or tuple type, then `__first(P)` and `__last(P)` yield a
  type, while `__trimFirst(P)` and `__trimLast(P)` yield a type pack.
- If `P` is a value pack or tuple value, then `__first(P)` and `__last(P)` yield
  a value, while `__trimFirst(P)` and `__trimLast(P)` yield a value pack.

### Semantics on Empty Packs

These operators have the following abstract behavior on a pack `[p0, p1, ..., pn]`:

- `__first([p0, p1, ..., pn]) = p0`
- `__last([p0, p1, ..., pn]) = pn`
- `__trimFirst([p0, p1, ..., pn]) = [p1, ..., pn]`
- `__trimLast([p0, p1, ..., pn]) = [p0, ..., p(n-1)]`

For the empty pack `[]`:

- `__first([])` is invalid
- `__last([])` is invalid
- `__trimFirst([]) = []`
- `__trimLast([]) = []`

For singleton packs `[p0]`:

- `__trimFirst([p0]) = []`
- `__trimLast([p0]) = []`

If the compiler can prove that a pack operand is empty, then `__first(P)` and
`__last(P)` are diagnosed as errors.

### Proving Non-Emptiness

`__first(P)` and `__last(P)` are only well-formed when the compiler can prove
that `P` is non-empty.

That proof may come from:

- a concrete non-empty tuple or concrete non-empty pack,
- a structural form that is statically known to be non-empty,
- a generic constraint `where nonempty(P)`.

The `nonempty(P)` constraint is valid only when `P` is a direct reference to a
generic pack parameter declared in the current generic declaration. In
particular:

- `where nonempty(T)` is valid when `T` is a type pack parameter
- `where nonempty(D)` is valid when `D` is a value pack parameter
- `where nonempty(int)` is invalid
- `where nonempty(__trimFirst(T))` is invalid
- `where nonempty(P)` is invalid if `P` comes from an outer generic rather than
  the current one

Specializing a generic that declares `where nonempty(P)` with an empty pack
argument for `P` is an error.

### Type-Expression Composition

Pack queries in type position are ordinary type expressions and continue to
participate in member lookup and generic application.

Examples:

```slang
__first(T).Element
__first(Tuple<A, B>)::Nested
__last(Tuple<C, D>)::Nested<int>
```

This is an important part of the feature. A queried type should behave like any
other type expression in the grammar, including:

- instance-style type member lookup with `.`,
- static member type lookup with `::`,
- generic application with `<...>`.

If `__first(T)` is known to conform to some interface, then associated-type
lookup through that interface should work the same way it would for any other
type satisfying the same constraint.

### Generic Constraints on Packs

Existing conformance constraints continue to work with packs. For example:

```slang
struct S<each T>
    where expand each T : IFoo
{}
```

The addition in this proposal is that users can now also constrain pack
cardinality:

```slang
struct S<each T>
    where expand each T : IFoo
    where nonempty(T)
{
    __first(T).Assoc value;
}
```

The conformance constraint states that each element of `T` conforms to `IFoo`,
while `nonempty(T)` makes it legal to query the first element.

### Symbolic Representation and IR

These operators must remain representable until generic specialization.

For example:

```slang
int firstValue<let each D : int>() where nonempty(D)
{
    return __first(D);
}
```

Even before `D` is specialized to a concrete pack, the body of `firstValue`
must lower into IR. Therefore, the compiler must represent unresolved pack
queries symbolically in both the front-end and the IR.

Similarly, `nonempty(P)` participates in generic constraint checking and generic
application. It therefore lowers to a witness-like placeholder in IR, even
though it does not correspond to a runtime operation. This placeholder exists so
that generic argument lists and substitution environments continue to line up
with the declared constraint list.

Once a pack query reaches a concrete pack or tuple, it should fold to the
obvious concrete result.

### Diagnostics

The compiler should produce distinct diagnostics for the main invalid cases:

- applying `__first` or `__last` to a known-empty pack,
- applying a pack query to an operand that is not pack-shaped,
- using `__first` or `__last` on a generic pack without proof of non-emptiness,
- using `nonempty(...)` on something other than a direct pack parameter of the
  current generic,
- using `optional nonempty(...)`.

Alternatives Considered
-----------------------

### Use unprefixed names like `first` and `last`

We considered surface syntax without a builtin prefix:

```slang
first(T)
last(T)
trimHead(T)
trimTail(T)
```

This alternative is superficially nicer, but it interacts poorly with name
lookup and type parsing. A user-defined declaration named `first` could shadow
the builtin form in expression contexts, and type parsing would need extra
special cases to keep `Foo<first(T)>` working reliably.

Using `__first`, `__last`, `__trimFirst`, and `__trimLast` makes the syntax
unambiguous and preserves the ability for users to define their own `first`,
`last`, etc. without affecting the builtin forms.

### Make `__first([])` produce a sentinel value

We considered whether `__first([])` or `__last([])` should produce some
distinguished error type or default value. This approach was rejected because it
would hide a structural error in generic metaprogramming and make reasoning
about pack structure less precise.

Instead, the operations remain partial and require proof of non-emptiness.

### Infer non-emptiness without an explicit constraint

We considered relying entirely on structural inference, without adding a new
constraint form. While some cases are indeed provably non-empty from structure
alone, an explicit `nonempty(P)` is still valuable because:

- it lets API authors state their intent directly,
- it provides a clear diagnosis when a generic is specialized with an empty
  pack,
- it avoids requiring every use-site to reconstruct the same proof.

### Add a more general fold/reduce feature at the same time

We considered adding pack queries together with a more general fold-like
operation over packs. While the two features are related, they solve different
problems and have very different design surfaces.

This proposal intentionally keeps the scope to first/last/trim operations and
the proof machinery needed to use them safely.

Future Directions
-----------------

This proposal does not attempt to solve all pack metaprogramming use cases.
Possible follow-on work includes:

- a fold or reduction form over packs,
- richer compile-time reasoning about pack cardinality,
- additional pack queries such as length-dependent slicing,
- generalized structural constraints over packs beyond non-emptiness.
