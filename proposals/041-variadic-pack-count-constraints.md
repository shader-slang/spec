SP #041: Variadic Pack Count Constraints
========================================

This proposal adds an oriented generic constraint for exact variadic pack
cardinality:

```slang
where countof(Pack) == IntExpr
```

The constraint lets a generic declaration state that a current generic type pack
or value pack has the same number of elements as a compile-time integer
expression. It is intentionally a pack-shape proof, not a general integer
equality system.

Status
------

Status: Implementation In-Progress
([shader-slang/slang#11571](https://github.com/shader-slang/slang/pull/11571)).

Author: Yong He

Reviewer:

Background
----------

Slang already supports variadic generic type parameters ([SP #007](007-variadic-generics.md)),
variadic generic value parameters ([SP #035](035-variadic-value-generics.md)),
and pack queries such as `countof`, `__first`, `__trimFirst`, and
`nonempty(...)` ([SP #036](036-variadic-pack-queries.md)).

Those features make it possible to define APIs over an arbitrary number of type
or value arguments, but they do not provide a way for an API to require an exact
pack size that is itself generic.

Motivation
----------

A real-world example is a tensor API whose rank is tracked by a generic integer.
The tensor wants a single `load` method that accepts exactly one integer index
per dimension:

```slang
struct Tensor<T, let Dimension : int>
{
    T load<each Index>(Index indices)
        where Index == int
        where countof(Index) == Dimension
    {
        ...
    }
}
```

Without an exact pack-count constraint, the library has to spell a separate
extension for each supported rank:

```slang
extension<T> Tensor<T, 1>
{
    T load(int i0) { ... }
}

extension<T> Tensor<T, 2>
{
    T load(int i0, int i1) { ... }
}

// ...and so on for every supported dimension.
```

That workaround bloats tensor libraries with repetitive overloads, expands the
overload set the compiler must consider, and slows compilation for an API whose
real requirement is simply "the number of indices equals the tensor dimension."

A smaller standalone example has the same shape:

```slang
void load<let N : int, each TIndex>(TIndex indices)
    where countof(TIndex) == N
{
    ...
}

void test()
{
    load<3>(1, 2, 3); // OK.
    load<2>(1, 2, 3); // Error: expected 2 pack elements, got 3.
}
```

The same issue appears when checking generic bodies before specialization. A
generic function may know abstractly that the pack `I` has count `N`, and it
should be able to forward that proof to another generic that requires the same
fact:

```slang
void bar<let N : int, each I>()
    where countof(I) == N
{
}

void foo<let N : int, each I>()
    where countof(I) == N
{
    bar<N, I>(); // OK. `foo`'s declared proof exactly matches `bar`'s requirement.
}
```

Without a first-class constraint and witness representation, the compiler can
validate concrete calls but cannot carry the abstract proof through generic
substitution.

Related Work
------------

C++ templates can express similar relationships using non-type template
parameters and template constraints, but those constraints are evaluated in the
template instantiation model rather than Slang's first-class generic and witness
system.

Swift's variadic generics motivate Slang's `each`/`expand` model, but Swift's
pack shape model is not directly applicable to Slang's existing generic value
parameters and witness lowering.

This proposal is closest to SP #036's `where nonempty(P)` constraint. Both
features introduce a small, targeted proof object for a specific pack-shape
fact. `nonempty(P)` proves that a direct pack parameter has at least one element.
`countof(P) == IntExpr` proves that a direct pack parameter has exactly a given
compile-time count.

Proposed Approach
-----------------

### Syntax

Add a generic constraint form:

```text
where-clause
    ::= ...existing forms...
     |  'countof' '(' pack-param ')' '==' int-expr
```

The syntax is deliberately oriented. The `countof(...)` operand must appear on
the left side:

```slang
void f<let N : int, each T>()
    where countof(T) == N // OK.
{}

void g<let N : int, each T>()
    where N == countof(T) // Error.
{}
```

Other comparison operators are not part of this feature:

```slang
void f<let N : int, each T>()
    where countof(T) != N // Error.
{}

void g<let N : int, each T>()
    where countof(T) >= N // Error.
{}
```

### Target Pack

The operand of `countof(...)` on the left side must be a direct reference to a
generic type pack parameter or generic value pack parameter declared by the
current generic declaration.

Valid examples:

```slang
void typePack<let N : int, each T>()
    where countof(T) == N
{}

void valuePack<let N : int, let each D : int>()
    where countof(D) == N
{}
```

Invalid examples:

```slang
void badTarget<let N : int>()
    where countof(int) == N // Error: not a pack parameter.
{}

void badShape<let N : int, each T>()
    where countof(__trimFirst(T)) == N // Error in this proposal.
{}
```

Nested generic declarations must constrain their own pack parameters. A nested
generic may refer to an outer pack in the expected count expression, but the
left-side pack being constrained must belong to the current generic:

```slang
struct Outer<let each D : int>
{
    void inner<each TIndex>(TIndex indices)
        where TIndex == int
        where countof(TIndex) == countof(D) // OK.
    {}

    void badInner<each TIndex>(TIndex indices)
        where TIndex == int
        where countof(D) == countof(TIndex) // Error: `D` is not current.
    {}
}
```

### Expected Count Expression

The right side must be a compile-time integer expression that folds to an
`IntVal`.

Examples:

```slang
where countof(T) == 3
where countof(T) == N
where countof(T) == countof(OuterPack)
where countof(T) == N - 1
```

The last example is allowed only as an exact expected-count expression. The
compiler does not derive algebraically equivalent facts from it.

### Concrete and Declared Witnesses

The implementation should represent a pack-count constraint as a generic
constraint declaration with a corresponding witness value.

At a concrete specialization, the compiler can fold the pack count:

```slang
void load<let N : int, each TIndex>(TIndex indices)
    where countof(TIndex) == N
{}

load<3>(1, 2, 3); // Produces a concrete pack-count witness.
```

While checking a generic body, the compiler may not know the concrete pack
count. In that case, the proof can come from a declared constraint in scope:

```slang
void bar<let N : int, each I>()
    where countof(I) == N
{}

void foo<let N : int, each I>()
    where countof(I) == N
{
    bar<N, I>(); // Uses `foo`'s declared pack-count witness.
}
```

A declared witness matches only the exact substituted pair:

- the constrained pack parameter, and
- the expected count `IntVal`.

Thus the following is invalid:

```slang
void badFoo<let N : int, let M : int, each I>()
    where countof(I) == N
{
    bar<M, I>(); // Error: the available proof is for `N`, not `M`.
}
```

### Oriented Proofs, Not Symmetric Equality

The constraint proves a fact about the pack named on the left side. It is not a
general equality theorem.

For example:

```slang
void bar<let N : int, each I>()
    where countof(I) == N
{}

struct S<each U>
{
    void ok<each T>(T args)
        where countof(T) == countof(U)
    {
        bar<countof(U), T>(); // OK: the requirement is about `T`.
    }

    void bad<each T>(T args)
        where countof(T) == countof(U)
    {
        bar<countof(T), U>(); // Error: no proof has been declared for `U`.
    }
}
```

Even though a human can see that equality is symmetric, this proposal does not
ask the compiler to use the declared proof backwards. A user who needs both
facts should declare both oriented constraints in the generic that owns the
corresponding packs.

### No Generic Argument Inference from Pack Count

Pack-count constraints are validation constraints. They do not infer ordinary
generic value arguments.

```slang
void load<let N : int, each TIndex>(TIndex indices)
    where countof(TIndex) == N
{}

load<3>(1, 2, 3); // OK.
load(1, 2, 3);    // Error: `N` is not inferred from `countof(TIndex)`.
```

This rule keeps the feature aligned with existing generic argument solving. It
also avoids turning `where` constraints into a source of integer equations.

Detailed Explanation
--------------------

### AST Representation

The compiler should introduce a declaration node such as
`GenericVariadicPackCountConstraintDecl`.

The declaration stores:

- the source location of the `where` clause,
- the checked left-side pack expression,
- the checked expected count expression, and
- the folded expected count `IntVal`.

The left-side pack expression must be a direct declaration reference to a
`GenericTypePackParamDecl` or `GenericValuePackParamDecl` whose parent is the
current `GenericDecl`.

### Witness Representation

The type system should introduce two witness forms:

- `DeclaredVariadicPackCountWitness`, which refers to a
  `GenericVariadicPackCountConstraintDecl`,
- `ConcreteVariadicPackCountWitness`, which records the constrained pack value
  and the expected count value that have already been proven equal.

Default substitution arguments for a generic should include a declared witness
for each pack-count constraint. This is what lets a generic body use its own
abstract constraint while calling another generic.

### Witness Solving

When solving a generic application, a pack-count witness depends on:

- the generic argument for the left-side pack parameter, and
- any generic arguments referenced by the expected count `IntVal`.

Once those dependencies are ready, witness solving proceeds in this order:

1. Substitute the current pack argument and expected count.
2. If `countof(pack)` folds concretely and equals the expected count, produce a
   `ConcreteVariadicPackCountWitness`.
3. Otherwise, search in-scope/default generic witness arguments for a
   `DeclaredVariadicPackCountWitness` whose substituted constrained pack and
   expected count exactly match the required proof.
4. If neither path succeeds, reject the specialization or overload candidate.

When overload resolution is speculative, a concrete mismatch should be recorded
as the focused failure reason so the selected failed candidate can diagnose
messages like:

```text
expected 2 elements, but pack argument has 3
```

### Generic Signature and Requirement Matching

Pack-count constraints participate in generic signature comparison and interface
requirement matching.

Two pack-count constraints match only when, after substituting the compared
generic signatures into the same parameter space:

- the constrained pack declaration is the same, and
- the expected count `IntVal` is equal under existing `IntVal` equality.

This exact matching rule preserves the oriented proof model. It also avoids
using a proof of `countof(I) == N` to satisfy a requirement for
`countof(I) == M`, even when both `N` and `M` are abstract value parameters.

### Lowering and IR

A pack-count constraint lowers as a hidden witness parameter, like other generic
constraint witnesses.

Declared witnesses lower through the substitution environment. Concrete
witnesses are proof-only values: they exist so generic argument lists and
substitution environments line up, but they do not require a runtime operation.

The IR does not need to encode a general integer equality solver. It only needs
to preserve the witness operand associated with the exact source constraint.

### Diagnostics

The compiler should diagnose at least the following cases:

- the left-side `countof(...)` operand is not a direct current-generic type or
  value pack parameter,
- the expected count expression does not fold to a compile-time integer value,
- a comparison operator other than `==` is used,
- `countof(...)` appears on the right side of a comparison,
- a concrete specialization provides a pack whose count differs from the
  expected count,
- an abstract specialization cannot prove the required pack-count witness.

Alternatives Considered
-----------------------

### General integer equality constraints

We considered a more general constraint form:

```slang
where IntExpr == IntExpr
```

Under that model, `countof(Pack) == N` would merely be one special case of
integer equality.

This is attractive mechanically because `countof(Pack)` already folds to an
`IntVal`. However, it opens the door to expectations that the compiler can
perform algebraic proof search. For example:

```slang
void bar<let N : int, each T>()
    where countof(T) == N
{}

void foo<let N : int, each T>()
    where countof(T) + 1 == N
{
    bar<N - 1, T>(); // Would require algebraic reasoning to prove.
}
```

A human can see that `countof(T) + 1 == N` implies
`countof(T) == N - 1`, but implementing that implication would require the
compiler to normalize, rearrange, and prove integer equations. That is far
beyond the intended scope of this feature.

The chosen design avoids that trap by requiring the exact pack-shape fact to be
written directly:

```slang
where countof(T) == N - 1
```

If a user writes the direct oriented fact, the compiler can carry it as a
declared witness. If the user writes an algebraically related fact, the compiler
does not derive a new one.

### Symmetric spelling

We considered accepting both:

```slang
where countof(T) == N
where N == countof(T)
```

This was rejected for the same reason as general integer equality. The feature
is easier to reason about when the constrained pack is always syntactically on
the left. The grammar therefore rejects `N == countof(T)` and tells the user to
write `countof(Pack) == IntExpr`.

### Symmetric witness use

We also considered allowing a declared witness for `countof(T) == countof(U)` to
prove requirements about either `T` or `U`.

That was rejected for the initial feature. The witness proves a constraint about
the left-side pack. If a callee requires `countof(U) == countof(T)`, then a
caller must have an exact declared proof for `U`, not merely a proof for `T`
whose expected count happens to mention `U`.

This rule may feel conservative, but it keeps witness matching local and avoids
introducing general equality reasoning through the back door.

### Inferring generic value parameters from pack counts

We considered allowing:

```slang
load(1, 2, 3)
```

to infer `N == 3` from `where countof(TIndex) == N`.

This was rejected for the initial feature. Pack-count constraints validate
already-solved arguments; they do not create new ordinary generic argument
constraints. That keeps generic inference predictable and avoids requiring a
larger integer-constraint solving system.

### Allowing arbitrary pack expressions as the target

We considered allowing constraints such as:

```slang
where countof(__trimFirst(T)) == N
```

This proposal does not include that generality. The left-side target must be a
direct current-generic pack parameter. More expressive structural pack
constraints may be useful in the future, but they should be designed together
with the pack-query and pack-recursion features that would consume them.

Future Directions
-----------------

Possible follow-on work includes:

- richer pack-shape constraints over structural pack expressions,
- optional inference of generic value parameters from concrete pack counts,
- a general predicate or integer-constraint system, if Slang ever needs one,
- better source-level sugar for declaring both oriented count facts when two
  packs are known to have the same count.

Each of those directions should be evaluated as a separate feature. This
proposal intentionally keeps the initial constraint narrow and exact.
