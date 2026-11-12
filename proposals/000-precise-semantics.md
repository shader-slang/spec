# SP #000: Semantics for `precise` in Slang

We propose semantics for the `precise` keyword in Slang, that programmers can use to restrict floating-point contraction and reassociation.
We also propose a way for functions to explicitly opt in to inheriting those restrictions from their callers.

## Status

- Status: Design Review
- Author: Theresa Foley (w/ agent)
- Implementation: Not implemented.
- Related Issue: [#13324](https://github.com/shader-slang/slang/issues/13324).

## Background

Expressions that are equal when evaluated mathematically, on real numbers, can produce results that are different when evaluated with values in a floating-point representation.
For example, reassociating `(a + b) + c` as `a + (b + c)` can change the result of evaluation.
The results of evaluating an expression like `a * b + c` can depend on whether it is implemented as a multiplication followed by an addition, or as a fused multiply-add operation, with only one rounding step.
Compiler optimizations for floating-point operations often make use of mathematical identities like these, even though they may change the value of an expression; exact preservation of values is often happily sacrificed in the name of performance.

Aggressive floating-point optimizations can create challenges, when a developer needs computations to agree.
For example, a depth-buffer-based renderer may perform a depth prepass followed by a later shading pass.
To ensure that both passes compute bit-identical pixel coverage and depth values, it is necessary for the same computation of vertex positions to yield identical values in distinct binary kernels.
Similar challenges arise for geometry processing algorithms like tessellation, which may need to ensure that computations made for primitives that share an edge will compute bit-identical values at positions along that shared edge, even if each computation orients the edge differently in its operations.

Slang accepts a `precise` keyword today, which has precedent in both HLSL and GLSL.
Unfortunately the current semantics of `precise` in Slang do not match either of those languages, and are not clearly specified nor consistently implemented.
Depending on how a program is expressed, what transformations are applied in the Slang compiler, and the compilation target itself, the Slang compiler may fail to respect a `precise` modifier that a user wrote, or may be overly conservative and apply restrictions on reassociation to more computations than a user would expect.

The problem of defining clear semantics for `precise` is made challenging by the fact that its presence is meant to restrict the optimizing transformations that are permitted, but the *absence* of `precise` does not in turn *guarantee* that such transformations will be performed.
It is easy for code to work as intended by coincidence rather than intention, and many existing codebases have become reliant on the undocumented implementation details of specific shader compilers.

## Related Work

### GLSL: `precise` and `invariant`

GLSL provides separate qualifiers for arithmetic restrictions and *output invariance*.

The `invariant` qualifier may be placed on an output of a GLSL program.
The concept of "invariance" in GLSL is based on the same concept in OpenGL.
Invariance in GLSL is, effectively, a guarantee that two mathematically equivalent computations, in different programs, will produce bit-identical output, under specific conditions.
The "specific conditions" can include various pieces of fixed-function rendering pipeline state, types used, operation ordering, etc.
Notably, an invariance guarantee does not, by itself, prohibit any specific optimizations; it only guarantees equivalence of results under the allowed conditions.

In GLSL the `precise` qualifier may be placed on the declaration of a *location* such as a variable, `out` function parameter, etc.
The `precise` keyword restricts the optimizations that may be performed to computations in a given function that contribute to the value in that location.
Specifically, `precise` in GLSL prohibits reassociation of computations and implicit contraction of multiply-add operations, preserves grouping, and ensures operator consistency.

GLSL provides an explicit `fma` function that describes a semantic multiply-add, and this operation is required to be implemented consistently in `precise` computations.
The GLSL specification does not mandate that `fma` be implemented via a fused multiply-add (despite the name), and only that it be *consistently* implemented for precise uses.

The semantics of `precise` in GLSL propagates backwards, within a given function.
Propagation considers only data dependencies and not control dependencies; predicates used for conditional selection/branching or iteration do not inherit a precise-ness constraint from computations that depend on those predicates.
Notably, when a call to a user-defined function is subject to a precise-ness constraint, it does *not* constrain computations in the body of a callee.

#### Reference Compiler Implementation

The reference GLSL compiler, glslang, implements `precise` using an AST-level worklist to analyze assignment operations and paths into storage locations (e.g., members of a `struct`-typed local variable), all before SPIR-V emission.
The glslang implementation does not exactly match the GLSL specification in certain cases: e.g., it discards `precise` qualifiers on non-output parameters, and allows a precise-ness constraint to propagate through the predicate of conditional (`?:`) expressions.

### HLSL

HLSL has a `precise` keyword with many similarities to GLSL's, but with a broader contract.
In HLSL, `precise` is defined to preserve separate operations (which includes disallowing contraction of multiplies and adds) and also restricts transformations that could change computed results in the presence of NaNs and infinities.

HLSL provides an explicit `mad` function for a multiply-add operation, which may have a fused or unfused implementation, so long as its behavior in a precise context is consistent on a given target platform.
Thus the HLSL `mad` seems to be largely consistent with GLSL `fma`.

As in GLSL, a `precise` qualifier in HLSL is applied to a destination (a function output, local variable, etc.) and the demand for precise-ness propagates backwards.
The semantics of `precise` in HLSL are not fully specified, and appear to depend significantly on the compiler implementation in use.

#### DXC to DXIL

On DXC's primary compilation path, precision requests are encoded into IR as explicit operations, before storage locations are eliminated, and then later propagated backward to relevant operations, at which point fast-math flags on those operations are cleared.
Notably, propagation considers control-dependence analysis, rather than just dataflow.

On the DXIL path, DXC performs aggressive inlining transformations before the propagation of precision demands occurs.
As a result, it is often the case that a precision demand within a caller function can propagate backward into computations in the body of a callee.
Even if this behavior is not specified by the HLSL language, many developers end up writing code that depends on it, whether knowingly or not.

#### DXC to SPIR-V

DXC's SPIR-V compilation path uses a different analysis from that used on the DXIL path.
Most importantly, the SPIR-V path propagates precision demands on a program representation that has different call boundaries than those used on the DXIL path, and does not propagate precision demands from callers to callees.
The SPIR-V path also does not consider control-dependence information during propagation.

#### Clang

At the time of writing this proposal, the HLSL implementation in Clang applies an interim strategy where use of `precise` causes an entire translation unit to be compiled with strict floating-point settings.
Specification and design work for how `precise` should work in that implementation and the version of HLSL it supports is not yet complete.

### SPIR-V

The SPIR-V intermediate language separately considers the restrictions placed on producers and consumers of SPIR-V code.
When considering transformations on floating-point operations, it is the responsibility of the producer to correctly emit instructions that describe what downstream transformations are permissible (or not), and the responsibility of the consumer to abide by those restrictions.

The `NoContraction` decoration can be applied to instructions to prohibit reassociation or combination of decorated operations by consumers.
The restrictions implied by `NoContraction` correspond closely to those of `precise` in GLSL, but do not establish the more broad restrictions of HLSL's `precise`.

The `SignedZeroInfNanPreserve` execution mode may be attached to an entry point in SPIR-V.
This execution mode restricts floating-point optimizations that SPIR-V consumers may apply to the call graph of that entry point, and thus has effects across function boundaries.

## Proposed Approach

We propose that `precise` in Slang restrict reassociation and implicit contraction of floating-point arithmetic.

The `precise` qualifier applies to declarations of storage, including variables (both local and global) and mutable parameters.
It may also be applied to the result of a function.
Notably, we propose that the `precise` qualifier should not be allowed on field declarations.

A value written to precise storage places a *precision demand* on the expression computing that value.
The demand propagates backward within the enclosing function:

```slang
float compute(float a, float b, float c, float d)
{
    float product = a * b;
    precise float sum = product + c;
    return sum * d;
}
```

The addition `product + c` and the multiplication computing `product` are precise.
The final `sum * d` is not: reading a precise variable does not make later computations precise.

We propose that, as in GLSL, a precision demand does not (by default) propagate across function-call boundaries.
A function call in a precise context constrains the input argument expressions to the call, but does not constrain arithmetic in the called function.
This choice makes it possible to analyze the propagation of precision demands precisely, even in the presence of separate compilation.

Because the restriction to function-local propagation of precision demands could be surprising for many users accustomed to the behavior of HLSL as compiled by DXC, we propose an attribute, provisionally named `[InheritFloatingPointPolicy]` that may be applied to a function, indicating that it should inherit the floating-point optimization policy requested at a call site.
This attribute makes a function *parametric* in the policy to use (where currently there are two policies to consider: `precise` and the default).

The following is an example of using `[InheritFloatingPointPolicy]`:

```slang
[InheritFloatingPointPolicy]
float multiplyThenOffset(float x, float scale, float offset)
{
    return x * scale + offset;
}

float caller(float a, float b, float c)
{
    precise float restricted = multiplyThenOffset(a, b, c);
    float ordinary = multiplyThenOffset(c, a, b);
    return restricted + ordinary;
}
```

The first call selects a version of `multiplyThenOffset` whose output is precise; the second selects its ordinary version.
The precision demand in place at each call site determines the version of the callee that is used.
This approach achieves the effect of interprocedural propagation, without relying on a compilation strategy that employs pervasive inlining.

When a lambda expression appears in a context that has a precision demand, the entire body of the lambda is subject to that demand;
this choice is intended to give calls to higher-order functions in `precise` contexts the semantics that programmers intuitively expect.
Similarly, when a policy-parametric function is used as a function value (such as when passing it as the argument to a higher-order function), the policy parameter is bound to the policy that is in effect at the use site.

Our proposed rules for `precise` control regrouping and contraction, rather than promising greater numerical accuracy or a complete floating-point environment.
In this way Slang's `precise` differs from HLSL's.
We propose that the current Slang compiler should use the same meaning of `precise` across all of the languages/dialects it supports, including its HLSL- and GLSL-flavored dialects, even when doing so causes a deviation from the defined semantics of HLSL or GLSL (or the specific implementation details of existing compilers for those languages).

When generating output code, a Slang compiler should map operations under a precision demand to the "obvious" corresponding mechanism on the target, where available: e.g., the `precise` keyword in output HLSL or GLSL source, and the `NoContraction` decoration in output SPIR-V.
We explicitly propose that a Slang compiler should *not* go to heroic lengths to fulfill precision demand on targets that either do not have a corresponding mechanism, or where the only corresponding mechanism is coarse-grained and thus could lead to surprising performance consequences.
A diagnostic should inform users when a Slang compiler is unable to fulfill a precision demand, and may inform the user of compilation options they can use to, e.g., apply a blanket policy for floating-point optimizations to an entire program.

The next section explains the user-facing rules and boundaries in more detail.
A separate appendix contains a formalism for propagation of precision constraints, and other information that is primarily intended to inform specification language and/or compiler implementation.

## Detailed Explanation

The rules below describe how to write code using the feature.
The [Formal Model appendix](000-precise-semantics-formal-model.md) contains the full policy lattice, constraint tables, specialization rules, diagnostics, compiler integration, and validation plan.

### Declarations and Storage Locations

The `precise` modifier is allowed on local variables, including `static` locals; global variables, including shader parameters; traditional-style function parameters; and traditional-style function declarations, where it applies to the result.
It qualifies the declaration, rather than introducing a different type such as `precise float`.
A declaration may have a non-floating-point or aggregate type: demands can propagate through integer conversions or aggregate values to earlier floating-point computations.

We propose to disallow `precise` on fields in both `struct` and `class` types, including `static` fields.
Field qualification could be a [later extension](#allow-precise-on-fields).
Fields, array elements, and vector components of a precise aggregate storage location are nevertheless precise sub-locations of that storage.

A precise parameter restricts writes to its storage inside the function.
A precise result restricts expressions returned by the function.
Neither imposes demands on arguments at call sites.
The compiler should warn about these qualifiers because callers can reasonably mistake them for an interprocedural contract.
No syntax is proposed for explicitly qualifying an implicit receiver parameter.

### Writes and Backward Propagation

Initialization and assignment to precise storage place a demand on the value being written.
Calls can also write storage through output arguments, as described below.
Compound assignments and increment/decrement expressions follow the call rules: in Slang they are calls to operators whose destination parameter can be read and written.

When a demanded expression reads an ordinary variable, that read places a demand on the computations that supplied its value.
In the first example, the demand on `sum` therefore reaches the initializer of `product`.
It can also reach the function parameters `a`, `b`, and `c`, but that does not constrain callers: these parameters are independent storage locations within `compute`.

There is a distinction between `precise` written on a declaration and a restriction inferred from a read.
A declared policy applies to every surviving write to that storage.
For a read-inferred demand, *required propagation* reaches writes that can contribute to the demanded read.
*Permitted conservative propagation* may also reach other writes to the same storage, including overwritten writes.
An implementation may similarly group fields or elements of an aggregate rather than distinguish them individually.

These permissions bound the intended conservatism of the compiler.
Missing a required restriction is a correctness problem; restrictions beyond the permitted propagation are a quality-of-implementation problem.
More freedom for the compiler to propagate demands means more restricted computations, and thus fewer optimizations permitted on those computations.
A program can rely on required propagation, but should not depend on a particular permitted conservative choice being made.

Developers can make their intent easier to review by using immutable intermediates or explicitly marking a mutable variable `precise` when all of its assignments should be restricted.
A demand may have no observable effect when it reaches only operations other than floating-point arithmetic.
Computations that have no observable effect may still be eliminated.

### Expressions and Calls

For a value-producing built-in array access `a[i]`, a demand reaches both `a` and `i`.
An integer result does not stop propagation: for example, floating-point arithmetic used to calculate an integer index can receive the demand.
Field and component selection propagate through their base expression.

Many other expressions follow the rules for function calls.
Operators, including compound assignments and increment/decrement, are calls; constructors, method calls, and property/subscript accessors behave as if expressed by calls.
A method's receiver counts as an argument, whether implicit or explicit, and its parameter-passing mode determines whether it is an input, an output, or both.
Standard-module arithmetic operations must expose the inheritance contracts needed to make ordinary scalar, vector, and matrix arithmetic follow these rules, including generic dispatch.

A demand on a call reaches every argument for an input parameter, even if the callee does not use that input to compute an output.
Input parameters include `in`, `borrow`/`__constref`, `consume`, `inout`, `ref`, and `ref readonly`.
For parameters that read storage through a reference, the demand concerns the incoming stored value, not just its address.

A call also receives a demand when it writes a value subject to a policy through an output argument.
Output parameters include `out`, `inout`, `ref`, and `ref writeonly`.
The call combines the demands on its result and all output writes, then propagates that combination to every input argument.
Thus `produce(x, p)` can demand `x` when `p` is precise, even if `produce` returns `void`.

An output-only argument supplies a destination, not an incoming value.
Merely forming a destination such as `values[index]` for an `out` parameter does not demand the index arithmetic.
An `inout` argument has both roles: its incoming value and its output destination participate.

None of these caller-side rules examines an ordinary callee's body.
For example:

```slang
float ordinaryHelper(float x, float scale, float offset)
{
    return x * scale + offset;
}

float useHelper(float a, float b, float c, float scale, float offset)
{
    precise float result = ordinaryHelper(a * b + c, scale, offset);
    return result;
}
```

The call's argument `a * b + c` is precise, but the multiplication and addition inside `ordinaryHelper` are not.
Inlining does not change that language boundary.
Named nested functions and methods declared inside local types are separate functions for the same purpose; the lambda rule below is an explicit exception.

### Functions That Inherit Output Policy

The proposed `[InheritFloatingPointPolicy]` attribute gives a function an implicit optimization-policy parameter.
At a call site, its argument combines the demand on the call's result with those on its output writes.
For the initial default/precise distinction, the compiler can provide ordinary and precise-output versions of the function.

The selected version behaves as if its result and output parameters had been declared with that policy.
Demands then propagate backward through the body using the same local rules as for explicit `precise` storage.
The attribute does not apply a blanket restriction to every computation in the function.
Calls inside the body still respect their own declarations: an ordinary call remains a boundary.
Explicit precise locals remain precise even in the ordinary version.

The initial function-level attribute shares one policy parameter across all outputs.
Giving individual outputs independent policy parameters is possible, but is not necessary to explain the initial feature.
Policy inheritance is part of the callable contract, but cannot by itself distinguish overloads.
A caller's policy arguments are determined by its own analysis; analyzing the callee does not feed additional demands back into the caller.

### Function Values and Lambdas

A policy-parametric function must be specialized before it can become a value of an ordinary function type.
The policy of the expression naming that function supplies the policy arguments.
This binding happens in the enclosing caller, before a higher-order function receives the callable.
The higher-order function does not choose a new policy when it later invokes that value.

A lambda expression similarly receives a policy from the expression context where it appears.
We propose that this policy apply to all computations in the lambda's own body, including arithmetic unrelated to its result and arithmetic used in predicates.
This is broader than the output-only effect of `[InheritFloatingPointPolicy]`.
Ordinary calls inside a demanded lambda still follow their declared contracts; the lambda rule does not make every transitively called function precise.

For example:

```slang
func apply(operation: functype(float)->float, x: float) -> float
{
    return operation(x);
}

[InheritFloatingPointPolicy]
float affine(float x)
{
    return x * 2.0f + 1.0f;
}

float useCallables(float x)
{
    precise float a = apply(affine, x);
    precise float b = apply((float y) => affine(y), x);
    precise float c = apply((float y) => y * 2.0f + 1.0f, x);
    return a + b + c;
}
```

The first call binds the precise output policy to `affine` before passing it to `apply`.
The second demands the forwarding lambda's body, whose call to `affine` selects the same policy specialization.
The third demands the arithmetic written directly in the lambda.
These cases work even though `apply` is ordinary: it receives the already-bound callable.
Additional arithmetic in `apply` itself would still need explicit precision or an inheritance attribute on `apply`.

A bound function value retains its policy when stored, passed onward, or returned.
A later invocation does not rebind it according to the invocation's context.
Backward propagation within the function containing the original value expression can still determine the policy supplied at that expression.

Lambda bodies are analyzed as separate functions with the policy supplied by their expressions.
A nested lambda expression inside a demanded body receives that demand and supplies it to its own body in turn.
A named function merely declared within the body remains an ordinary boundary.

The body rule does not by itself demand earlier computations in an enclosing function that produced a captured value.
The treatment of captured values, capture initializers, and reference captures needs to be specified separately; it is an open design question.

### Control Flow

An ordinary demand follows data dependencies, not control dependencies.
Writing a precise variable inside an `if` or loop does not demand the condition, nor conditions controlling `break` or `continue`.
A conditional expression `c ? x : y` demands its possible results, rather than `c` merely because it selects between them.
An eager selection function follows the ordinary call rules and therefore demands all input arguments, including its predicate.
Logical `&&` and `||` demands reach both operands because both contribute to the Boolean result.

Developers should mark floating-point computations used by important control decisions explicitly when they also need to be precise.
In a demanded lambda, predicate computations receive the lambda's body policy directly; this is not propagation through control dependence.

### Targets and Numerical Contracts

The proposed meaning is the same for Slang and its HLSL- and GLSL-flavored input dialects.
Slang would map the local restrictions to GLSL `precise`, HLSL `precise`, or SPIR-V `NoContraction`.
Native HLSL may impose additional restrictions.
On targets without suitable control, an implementation may use broader controls or diagnose an unsupported-feature warning and emit code that does not encode the requested restriction.
Suppressing that warning would not supply the missing guarantee.

Regrouping includes algebraic transformations such as factoring `a * b + a * c` into `a * (b + c)`, or replacing division with multiplication by an explicit reciprocal.
The modifier does not select rounding modes, promise preservation of exceptional values or denormals, control transcendental-function accuracy, or guarantee agreement across targets.
Global compilation options govern other floating-point choices and can impose stronger program-wide restrictions without changing local propagation.

The precise behavior of explicit `mad` and `fma`, and the reduction order of `dot` or matrix `mul`, still need their own numerical contracts.
Precision demands must preserve those operation contracts rather than treating all operations as interchangeable multiplication and addition.

### Interfaces, Diagnostics, and Implementation

An interface requirement can carry the inheritance attribute.
A satisfying declaration must explicitly provide the corresponding contract.
A synthesized forwarding method must not manufacture a successful conformance merely by receiving an attribute that never reaches the user's unannotated implementation.
The experimental `slang.numerics` interfaces can change accordingly; the proposed temporary compatibility exception for enumerated legacy core interfaces has a deliberately weaker guarantee.

We propose an optional warning when a demand stops at an ordinary user-defined function, and an optional diagnostic for locals that become constrained through inference.
The latter should explain the restrictions actually selected by the compiler, including permitted conservative choices.
Any acknowledgement attribute would suppress a diagnostic without relaxing precision demands.

Implementation must preserve the declared policies, original function boundaries, and lambda-expression/body relationships through lowering and ordinary generic specialization.
Policy resolution and specialization must finish before incompatible floating-point optimizations.
The appendix gives the proposed IR representation, pass ordering, target emission, interface checks, and regression coverage.

### Decisions Remaining for Design Review

The following decisions remain open without changing the central model:

1. Final spellings for function-level inheritance, per-output inheritance, and diagnostic acknowledgements, and whether independent outputs are exposed initially.
2. The complete `mad`/`fma` contracts, the reduction order promised by precise `dot`/`mul`, and consistency through changes in operand representation.
3. The exact legacy core numeric requirement list and the semantic representation of standard-provided conformance ownership.
4. Which declaration-based diagnostics can be supported reliably by the initial IR phase, and whether a shared front-end analysis is practical.
5. Capture-related propagation and the representation of policy-bound function values and lambdas, including genuinely open runtime dispatch.

Implementing GLSL `invariant`, exporting input-policy demands, admitting validated forwarding adapters, and defining stronger floating-point environments are future work.

## Alternatives Considered

### Propagate `precise` demands across function calls

Developers who are coming from HLSL to Slang are likely to be familiar with the de facto observed behavior of `precise` when using DXC.
These developers are likely to expect full interprocedural propagation of precision demands (even if that is not strictly what DXC promises or guarantees).

We could define the semantics of the Slang language such that precision demands propagate interprocedurally, either from caller to callee, callee to caller, or both.

We have chosen not to pursue this option.

The most important reason for our choice is that interprocedural propagation of precision demands seems difficult or impossible to reconcile with separate compilation, and support for true separate compilation is an over-arching goal of the Slang language.

Similarly, interprocedural propagation is easiest to implement in the context of a compiler that performs full inlining of an entire call graph, but the Slang language and compiler have an over-arching goal of avoiding reliance on pervasive inlining as a universal strategy for solving language design and compiler implementation challenges.
An interprocedural precision propagation pass that does not rely on pervasive inlining can be defined and authored, but it would be a much more significant implementation task than the kind of intraprocedural analysis we propose.

### Use types to represent requests for restrictions on floating-point optimizations

A wrapper type, like a hypothetical `NoContraction<float>` could provide arithmetic operations comparable to a plain `float`, but with a guarantee that operations performed on `NoContraction<...>` types will not be subject to reassociation or contraction.

A key benefit of using types to represent the kinds of restrictions that `precise` represents in HLSL/GLSL is that a type is more naturally compatible with generics.
A function that wants to be parametric in floating-point optimization policies could simply be parameterised over the type of floating-point scalar it will use (e.g., either `float` or `NoContraction<float>`).
There would then be no need for something like `[InheritFloatingPointPolicy]`, because an existing language mechanism - generics - can express the same thing.

A wrapper type would come with the challenge that, by default, it would propagate precision demands *forward* rather than backward, defying developer intuition from `precise`.
For example, given:

```slang
float usePreciseType(float a, float b, float c)
{
    NoContraction<float> result = a*b + c;
    return result;
}
```

Code such as the above would not do what users might hope and expect.
In practice, the expression `a*b + c` would be computed using the ordinary `float` type, and then the result would be converted to a `NoContraction<float>` value before assignment to the variable `result`.

There is a general principle of language design at play here, where things like requirements and availability tend to work when they flow forwards through dependencies (whether data or control dependencies), while *demands* tend to want to flow backwards.

A type-based design would need a mechanism for backward propagation to provide the behavior proposed here.

## Future Directions

### Allow `precise` on fields

Our proposal intentionally does not allow the `precise` qualifier to apply to the fields of `struct` and `class` types.
The reason for this choice is that it creates complications when a value is written to a storage location that is not itself a precise storage location, but transitively *contains* one.
For example, consider:

```slang
struct Pair
{
    precise float first;
    float second;
}

Pair makePair(float a, float b, float c, float d, float e, float f)
{
    Pair result = { a * b + c, d * e + f };
    return result;
}
```

In this example, the initialization of `result` is a write to a storage location that is not precise, but that storage location contains the precise storage location `result.first`.

In an example like the above, we must first have rules for determining when a storage location (like `result`) transitively contains a precise storage location.
That determination seems easy, when only considering a small example where all of the types are statically known, but it gets significantly more complicated in the presence of generics, `extern` types that are resolved at link time, etc.
A definition of the language rules for a case like this would need to take into account *when* a compiler should be performing propagation of precision demands, and what information it will have at that point.

The second complication that arises in an example like the above is that, intuitively, a user might expect that a precision demand would only be placed on the initializer for `first` (the expression `a * b + c`), but in order to have reasonably clean semantics, we would want to allow a compiler to place a precision demand on the entire expression being used to initialize `result`, leading to `d * e + f` also being restricted.
Such behavior would be semantically correct (it is always safe to optimize less), but feels like it defies programmer intent enough that *something* should be diagnosed in a case like this.

It is worth noting that the GLSL specification does not allow for `precise` on fields, probably for exactly these kinds of reasons.

Despite the unappealing task of precisely defining semantics for `precise` on fields, it turns out that putting `precise` on `struct` fields is allowed in HLSL and indeed has sometimes been specifically recommended to developers using HLSL.

If we resign ourselves to needing to support this idiom in Slang, it is worth noting that the work would be an extension of the existing model in this proposal, rather than something that requires an entirely new and different formalism.
The work would be unpleasant, but tractable.

### Allow policies to propagate from function parameters to callers

Our proposal provides an explicit opt-in feature that allows a callee function to inherit floating-point optimization policies for its outputs from a call site.
We have not, in this proposal, put forward a mechanism for allowing propagation across call sites in the other direction: from callees back to callers.

We can easily imagine a model in which `precise` (or an entirely new qualifier) on an input parameter becomes part of a function's signature and, at call sites, places a precision demand on argument expressions for that parameter.

We have not yet seen much evidence that this kind of propagation (from callee to caller) is widely needed, but if the need arises, it would be a somewhat natural extension of the existing rules we have defined.

Perhaps the most significant wrinkle to allowing both caller-to-callee propagation and callee-to-caller propagation is ensuring that the analysis can still be kept local to one function at a time.
If the constraints imposed by a callee-side input parameter (on caller-side argument expressions) could depend on a policy parameter passed from caller to callee, then a cycle is possible (since the caller-side argument for the policy parameter could depend on the policies applied to the ordinary arguments to the call).

### Automatically infer `[InheritFloatingPointPolicy]` when implementing interface requirements

Our proposal allows for interface requirements to use `[InheritFloatingPointPolicy]`, indicating that satisfying declarations must also be parametric in floating-point policy.

It is important that an implementation not allow a method without `[InheritFloatingPointPolicy]` to silently satisfy an interface requirement that has `[InheritFloatingPointPolicy]`, so we have proposed that attempts to do so should be diagnosed as errors.
A developer might reasonably ask: if a Slang compiler can diagnose an error in such a case, why can't it just automatically infer `[InheritFloatingPointPolicy]` on their method declaration when it is being used to satisfy an interface requirement?

There are various strong reasons why the Slang language does not currently allow a method declaration to implicitly inherit attributes or other context from an interface requirement it satisfies, but these reasons are not easy for a programmer *using* Slang to understand, and it behooves us to consider ways that we might smooth such rough edges over time.
