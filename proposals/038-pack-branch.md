SP #038: Pack Branch
====================

This proposal introduces a built-in type form:

```slang
__packBranch(pack, emptyType, nonEmptyType)
```

`__packBranch` selects `emptyType` when `pack` is known to be empty and
`nonEmptyType` when `pack` is known to be non-empty. When the pack's cardinality
is not yet known, the compiler keeps the branch symbolic and carries one crucial
extra fact while checking the non-empty branch: inside `nonEmptyType`, the pack
is assumed to be non-empty.

That branch-local assumption is the missing piece that makes recursive
metaprogramming over variadic packs practical in Slang. It allows users to write
natural recursive shapes over `__first(...)` and `__trimFirst(...)` without
forcing the compiler to guess whether those operations are valid.

Status
------

Status: Implemented

Implementation: [PR 10533](https://github.com/shader-slang/slang/pull/10533)

Author: Yong He

Reviewer: Theresa Foley

Background
----------
Slang already supports variadic generics, pack expansion, and pack queries
(introduced in [SP 036](036-variadic-pack-queries.md)) such
as `__first`, `__last`, `__trimFirst`, and `__trimLast`. It also supports
`where nonempty(P)` constraints for packs. Those features are enough to talk
about packs, but they do not provide a way to express a recursive type that
stops when a pack becomes empty.

This gap shows up immediately in recursive pack-driven type definitions. For
example, consider a node chain that should recurse on the tail of a variadic
integer pack until there are no elements left:

```slang
struct EmptyNode {}

struct EvalNode<let Head : int, let each Tail : int>
{
    __packBranch(Tail, EmptyNode, EvalNode<__first(Tail), __trimFirst(Tail)>) rest;
}
```

For a concrete instantiation like `EvalNode<4, 8, 16>`, a user can see that the
shape terminates:

- `EvalNode<4, 8, 16>`
- `EvalNode<8, 16>`
- `EvalNode<16>`
- `EmptyNode`

However, the compiler must validate the recursive branch before specialization
finishes. That means it needs a symbolic way to say "the recursive branch only
exists when `Tail` is non-empty." Without such a mechanism, the compiler cannot
justify that `__first(Tail)` and `__trimFirst(Tail)` are valid in the recursive
branch.

This limitation also appears in more interesting pack-driven programs. For
example, users may want to express an MLP-like recursive layer chain over a pack
of layer sizes:

```slang
struct EmptyNode<let N : int> : ILayerChain<N> { ... }

struct EvalNode<let Head : int, let each Tail : int> : ILayerChain<Head>
    where nonempty(Tail)
{
    typealias Rest = __packBranch(
        __trimFirst(Tail),
        EmptyNode<__first(Tail)>,
        EvalNode<__first(Tail), __trimFirst(Tail)>);

    Layer<Head, __first(Tail)> firstLayer;
    Rest restLayers;
}

struct MLP<let Head : int, let each Tail : int>
{
    typealias Layers = __packBranch(Tail, EmptyNode<Head>, EvalNode<Head, Tail>);
    Layers layers;
}
```

Here again, the interesting program shape is not "fold some values." It is
"select the base type when the pack is empty, otherwise select the recursive
type and allow non-empty-only pack queries in that branch."

At the same time, enabling these recursive forms means the compiler must be able
to distinguish valid structurally decreasing recursion from truly non-terminating
recursion. For example:

```slang
struct LoopField<each T>
{
    LoopField<T, int> next;
}
```

does not shrink the pack, and:

```slang
int recurse<let x : int>()
{
    return recurse<x + 1>();
}
```

also never terminates even though it does not repeat the exact same generic
arguments. Supporting pack recursion safely therefore requires both a symbolic
branching form and explicit recursion guards.

Related Work
------------

C++ templates often solve "empty pack vs non-empty pack" by partial
specialization or overload sets that decompose a pack into `Head, Tail...`.
That approach is powerful, but it relies on a template-matching system that is
more macro-like than Slang's current generic model.

Functional languages and theorem-proving-oriented languages often provide
pattern matching or conditional type computation over list-like type structures.
Those systems usually come with richer predicate reasoning and proof terms.

This proposal intentionally chooses a smaller, targeted feature. Rather than
introducing a general predicate language for types, it adds the one piece of
branching needed to make pack-based recursive types expressible and checkable in
Slang today.

Proposed Approach
-----------------

We propose a built-in type form:

```slang
__packBranch(pack, emptyType, nonEmptyType)
```

where `pack` is a type pack or value pack expression.

The typing rule is:

- If `pack` is known to be empty, the result is `emptyType`.
- If `pack` is known to be non-empty, the result is `nonEmptyType`.
- Otherwise, the result is a symbolic pack-branch type that records all three
  operands.

`__packBranch` also behaves like an ordinary type for facet/interface
computation. In particular, if both `emptyType` and `nonEmptyType` have some
facet such as `: IFoo`, then `__packBranch(pack, emptyType, nonEmptyType)` also
has that facet, remaining symbolic until specialization determines which branch
is taken.

The critical semantic rule is that `nonEmptyType` is checked under a local
assumption that `pack` is non-empty. Under that assumption, the following become
valid on that specific pack:

- `__first(pack)`
- `__last(pack)`
- `__trimFirst(pack)`
- `__trimLast(pack)`
- `nonempty(pack)`

That rule makes patterns like the following valid:

```slang
typealias EvalHelper<let Head : int, let each Tail : int> =
    __packBranch(Tail, EvalLeaf<Head>, EvalNode<Head, Tail>);

struct EvalNode<let Head : int, let each Tail : int> : IEvalNode where nonempty(Tail)
{
    typealias Next = EvalHelper<__first(Tail), __trimFirst(Tail)>;
    typealias Result = Next.Result;
}
```

When `Tail` is empty, `EvalHelper` resolves to `EvalLeaf<Head>`. When `Tail` is
non-empty, it resolves to `EvalNode<Head, Tail>`, and that recursive case is
well-typed because the `nonempty(Tail)` fact is available while checking it.

Examples
--------

The following examples illustrate the most important intended uses of
`__packBranch`.

### Basic Type Selection and Shared Facets

```slang
interface IStaticInt
{
    static int get();
}

struct IntConst<let N : int> : IStaticInt
{
    static int get() { return N; }
}

int chooseType<let each S : int>()
{
    // If `S` is empty, the selected type is `IntConst<1>`.
    // If `S` is non-empty, the selected type is `IntConst<2>`.
    //
    // Both branches conform to `IStaticInt`, so the PackBranch type
    // also supports `.get()` before specialization picks a branch.
    return __packBranch(S, IntConst<1>, IntConst<2>).get();
}

// chooseType<>()    -> 1
// chooseType<4>()   -> 2
```

### Branch-Local Non-Empty Assumption

```slang
interface IStaticInt
{
    static int get();
}

struct IntConst<let N : int> : IStaticInt
{
    static int get() { return N; }
}

typealias HeadOrZero<let each D : int> =
    __packBranch(
        D,
        IntConst<0>,          // Used when `D` is empty.
        IntConst<__first(D)>  // Valid here because this branch is checked
                              // under the assumption that `D` is non-empty.
    );

// HeadOrZero<>        -> IntConst<0>
// HeadOrZero<7, 9>    -> IntConst<7>
```

This is the essential semantic rule of the feature: the non-empty branch can use
non-empty-only pack queries on the tested pack.

### Recursive Node Chain

```slang
interface INode
{
    __init();
    int sum();
}

struct EmptyNode : INode
{
    __init() {}
    int sum() { return 0; }
}

struct EvalNode<let Head : int, let each Tail : int> : INode
{
    int headValue;

    __init()
    {
        headValue = Head;
    }

    // If `Tail` is empty, recursion stops with `EmptyNode`.
    // Otherwise we recurse on the first tail element and the trimmed tail.
    __packBranch(Tail, EmptyNode, EvalNode<__first(Tail), __trimFirst(Tail)>) rest = {};

    int sum()
    {
        return headValue + rest.sum();
    }
}

// EvalNode<4>         -> 4 + 0
// EvalNode<4, 8, 16>  -> 4 + 8 + 16 + 0
```

This is a direct example of structurally decreasing recursion over a pack. Each
non-empty step consumes one element from `Tail`, so specialization makes
progress toward the empty branch.

### Recursive Value Aggregation

```slang
interface IEval
{
    static const int value;
}

struct Empty : IEval
{
    static const int value = 0;
}

struct SumNode<let Head : int, let each Tail : int> : IEval
{
    typealias Next = __packBranch(
        Tail,
        Empty,                                  // Base case: no more values to add.
        SumNode<__first(Tail), __trimFirst(Tail)> // Recursive case: add the head
                                                 // and continue with the tail.
    );

    static const int value = Head + Next.value;
}

typealias Sum<let each vals : int> =
    __packBranch(
        vals,
        Empty,                                   // Sum<> = 0
        SumNode<__first(vals), __trimFirst(vals)> // Sum<1,2,3,4> = 1 + Sum<2,3,4>
    );

static const int sum = Sum<1, 2, 3, 4>.value; // folds to 10
```

This example shows that `__packBranch` also supports recursive compile-time
value computation, not just recursive field or associated-type structure. It is
also a useful tooling case: editors and language services should still be able
to surface the folded result of expressions like `Sum<1, 2, 3, 4>.value`.

### MLP-Style Recursive Layer Chain

```slang
interface ILayerChain<let InSize : int>
{
    associatedtype Output;
    __init();
    Output eval(int[InSize] input);
}

struct EmptyNode<let N : int> : ILayerChain<N>
{
    typealias Output = int[N];

    __init() {}

    Output eval(int[N] input)
    {
        // The empty chain is the base case: it returns its input unchanged.
        return input;
    }
}

struct EvalNode<let Head : int, let each Tail : int> : ILayerChain<Head>
    where nonempty(Tail)
{
    typealias Rest = __packBranch(
        __trimFirst(Tail),
        EmptyNode<__first(Tail)>,                 // Exactly one layer size remains.
        EvalNode<__first(Tail), __trimFirst(Tail)> // More than one size remains.
    );

    typealias Output = Rest.Output;

    Layer<Head, __first(Tail)> firstLayer = {};
    Rest restLayers = {};

    __init() {}

    Output eval(int[Head] input)
    {
        // Apply the first layer, then recurse through the rest of the chain.
        return restLayers.eval(firstLayer.eval(input));
    }
}

struct MLP<let Head : int, let each Tail : int>
{
    // `Tail` determines whether the network is just the base case or a
    // recursive chain of layers.
    typealias Layers = __packBranch(Tail, EmptyNode<Head>, EvalNode<Head, Tail>);
    typealias Output = Layers.Output;
}
```

This example shows why the feature needs to work for real recursive types, not
just for one-step pack inspection. The result type and the field layout both
depend on recursively branching over the remaining pack of layer sizes.

Detailed Explanation
--------------------

### Front-End Semantics

The parser introduces a dedicated syntax form for `__packBranch`, and semantic
checking lowers it to a dedicated semantic type representation.

The semantic checker first computes whether the pack cardinality is:

- known empty,
- known non-empty, or
- not yet known.

Cardinality information can come from:

- concrete type packs and value packs,
- pack expansions whose captured packs are known,
- explicit `where nonempty(...)` constraints on generic pack parameters,
- and the temporary local assumption created while checking the non-empty branch
  of a surrounding `__packBranch`.

If the cardinality is already known, the checker can immediately select the
appropriate branch type. If the cardinality is unknown, it produces a symbolic
`PackBranchType(pack, emptyType, nonEmptyType)`.

An important detail is that the branch must preserve the identity of the pack it
tests. For value packs in particular, the compiler cannot simply branch on the
pack's type. Two distinct symbolic packs can have the same tuple/value-pack type
while needing different specialization behavior. The semantic form therefore
stores the actual symbolic pack operand.

### Interface Conformance and Symbolic Inheritance

`__packBranch` must behave like an ordinary type in lookup, inheritance, and
interface checking. If both branches provide the same facet or interface
conformance, the compiler constructs a symbolic witness for the branch as a
whole.

For example, if both `emptyType` and `nonEmptyType` conform to some interface
`I`, then `__packBranch(pack, emptyType, nonEmptyType)` should also conform to
`I`. The implementation represents this with a dedicated
`PackBranchSubtypeWitness` that keeps:

- the pack being tested,
- the witness for the empty branch,
- and the witness for the non-empty branch.

This keeps conformance symbolic until specialization later proves which branch
is taken.

### IR Representation

The implementation lowers `PackBranchType` to a dedicated IR instruction:

```text
PackBranch(pack, emptyType, nonEmptyType)
```

The same idea is used for symbolic subtype witnesses.

The other key IR change is that non-empty-only pack queries now take an explicit
proof object operand. Instead of treating "this pack is known non-empty" as
hidden side information, IR makes it explicit:

```text
NonEmptyPackWitness(pack)
ExtractFirstFromPack(pack, NonEmptyPackWitness(pack))
TrimFirstOfPack(pack, NonEmptyPackWitness(pack))
```

and similarly for `__last` and `__trimLast`.

This design also matches generic constraints. A `where nonempty(P)` constraint
is represented as requiring an explicit witness value for `P`, so generic
application, overload resolution, and substitution all thread the same proof
object through the system.

### Why the Explicit Witness Matters

The explicit `NonEmptyPackWitness(pack)` is more than a cleanup of the IR. It is
what allows valid recursive pack structures to specialize in an ordinary,
well-founded way.

Consider:

```slang
struct EvalNode<let Head : int, let each Tail : int>
{
    __packBranch(Tail, EmptyNode, EvalNode<__first(Tail), __trimFirst(Tail)>) rest;
}
```

When specializing `EvalNode<4, 8, 16>`, the compiler should take the non-empty
branch for `Tail = (8, 16)`, then compute:

- `__first((8, 16)) -> 8`
- `__trimFirst((8, 16)) -> (16)`

and continue with a strictly smaller pack.

With an explicit witness operand, those pack queries are just ordinary IR
instructions whose legality and dependencies are visible in the graph. The
specializer only folds them when the pack operand itself has become concrete and
non-empty. The next recursive step therefore operates on a new concrete pack,
with a new witness tied to that smaller pack.

This is important because an earlier design relied on side-band blocking state
inside specialization to avoid re-entering active pack branches. That approach
is fragile: it tries to encode semantic facts outside the IR graph, and it can
interfere with a legitimate decreasing recursion pattern by making the
specializer reason about "currently active branch state" instead of simply
specializing explicit operands.

By making the non-empty proof explicit:

- a valid recursive branch does not need ad hoc blocking to avoid looping,
- the specializer can treat pack queries like ordinary foldable instructions,
- and progress is naturally tied to the pack operand becoming smaller and more
  concrete.

This does not eliminate the need for recursion guards. Ill-formed recursive
definitions like `LoopField<T, int>` or unbounded generic evaluation like
`recurse<x + 1>()` are still possible, and the implementation diagnoses those
cases with explicit recursion-depth limits. The point is narrower: explicit
non-empty witnesses prevent the compiler's representation of valid pack
recursion from itself creating a specialization loop.

### Specialization Behavior

IR specialization only folds `PackBranch` when the pack operand is known to be
empty or non-empty. If the cardinality is still unknown, the branch stays
symbolic.

That behavior is deliberate. It means a recursive shape can be represented early
without forcing specialization to guess. Once the pack becomes concrete,
specialization collapses the branch, folds the witness-based pack queries, and
continues normally.

### Diagnostics and Recursion Limits

This proposal makes recursive types easier to express, which increases the need
for robust failure modes on bad recursion patterns. The implementation therefore
adds or relies on bounded-recursion diagnostics in multiple places, including:

- generic evaluation,
- generic specialization,
- type layout,
- differentiable-type registration,
- and recursive field/type lowering.

The goal is that well-founded recursion becomes expressible, while non-terminating
forms fail with diagnostics instead of hanging or overflowing the stack.

Alternatives Considered
-----------------------

### 1. A special-purpose `fold(pack, initialValue, stepExpr)`

One alternative is to add a pack fold form such as:

```slang
fold(pack, initialValue, stepExpr)
```

At first glance, this looks attractive because many recursive pack algorithms
can be read as "if the pack is empty, use the initial value; otherwise consume
one element and continue."

The problem is that type-checking such a feature is much harder than the
`__packBranch` case we actually need.

In a realistic fold design, `stepExpr` would need to reference concepts like:

- the current aggregator value or type,
- the current element,
- and the rest of the pack.

Those entities do not have a fixed type across all iterations:

- the type of `currentAggregator` after step `i` depends on the first `i`
  elements of the pack,
- the type of `restOfPack` changes on every step,
- and operations like `__first(restOfPack)` or `__trimFirst(restOfPack)` are only
  legal when `restOfPack` is known to be non-empty at that particular step.

In other words, checking `fold` would require the compiler to verify a whole
family of step applications whose types evolve during the iteration. For the
type-level recursive examples that motivate this feature, that is close to
requiring a dependent typing rule for the accumulator and the remaining pack.

For example, if the fold is used to build a recursive node chain or MLP-like
layer chain, the "accumulator type" after each step is itself a new type whose
shape depends on the previously consumed prefix and the current tail. The
compiler would need to prove that `stepExpr` remains well-typed for an unknown
number of iterations, under changing assumptions about the tail pack.

That is much more than "branch on whether this pack is empty." It amounts to a
general typed reduction framework for packs. It is not a good fit for Slang's
current semantic model, and it would likely require substantially more machinery
than this feature needs.

By contrast, `__packBranch` asks the checker to reason about exactly one
structural step:

- either the pack is empty and we use `emptyType`,
- or it is non-empty and we check `nonEmptyType` under that one local
  assumption.

That targeted rule is enough to express recursive pack types naturally, while
remaining feasible to implement in the current compiler.

### 2. A general `type_if(pred, trueType, falseType)`

Another alternative is a more general conditional type form:

```slang
type_if(pred, trueType, falseType)
```

This looks more uniform than `__packBranch`, but it misses the crucial semantic
requirement for the motivating use cases.

Suppose a user writes:

```slang
type_if(nonempty(P), EvalNode<__first(P), __trimFirst(P)>, EmptyNode)
```

The true branch is only well-typed if the checker is allowed to assume that
`P` is non-empty while checking it. A general `type_if` that merely carries an
arbitrary predicate value does not automatically provide that assumption.

To make `type_if` work for this use case, Slang would need a much more general
predicate system with branch-local reasoning. The compiler would need to answer
questions like:

- what predicates are allowed,
- how predicates normalize or compare for equality,
- when one predicate implies another,
- how proof objects are represented,
- and how branch-specific assumptions are lowered to IR and carried through
  specialization.

Once we need all of that, `type_if` is no longer a small generalization of
`__packBranch`; it is the start of a much broader proof and predicate framework.

`__packBranch(pack, emptyType, nonEmptyType)` is intentionally narrower. It
packages both the test and the one branch-local proof rule we need:

- the predicate is specifically "is this pack empty or non-empty?",
- and the non-empty branch is checked under an assumption about that exact pack.

That specialization is what makes the feature implementable now. A more general
`type_if` may still be worth exploring in the future, but it should be designed
as part of a broader predicate system rather than introduced prematurely for the
pack-recursion use case.
