# Formal Model for `precise` in Slang

This appendix accompanies [Semantics for `precise` in Slang](000-precise-semantics.md).
The main proposal gives the user-facing model and examples.
The material below preserves the detailed constraints, callable and interface contracts, compiler integration, and validation plan for implementers and design review.
It does not introduce a separate set of language semantics.

## The Restrictions

The `precise` modifier in Slang will restrict:

- optimization that would change the grouping/association of floating-point arithmetic
- optimizations that implicitly contract floating-point operations (e.g., contraction of a multiply and add into a fused multiply-add, with a single rounding step)

A precision demand restricts both the optimizations that the Slang compiler may perform on operations and also requires the Slang compiler to emit output code (where possible; see [Supported Targets](#supported-targets)) that imposes the same restrictions on any downstream compilers or runtime systems that consume that output code.

A precision demand does not:

- Affect the semantics of operations other than floating-point arithmetic
- Restrict the precision in ULPs of special functions, including trigonometry, etc.
- Guarantee that floating-point arithmetic will preserve the output of operations on non-finite values, signed zero, or denormalized values.
- Control rounding modes
- Guarantee bitwise agreement of floating-point operations across devices or compilation targets


## Supported Source Dialects

We propose the same minimum meaning for `precise` in Slang and its HLSL- and GLSL-flavored input dialects.

## Supported Targets

An operation computed under a `precise` demand will be mapped to the "obvious" construct on targets that support such a thing:

- GLSL `precise`
- HLSL `precise` (even though it has more restrictive semantics than Slang/GLSL `precise` when compiling for D3D)
- SPIR-V `NoContraction`

On targets where there is no way to impose fine-grained (e.g., per-operation) restrictions on floating-point optimization policies, the Slang compiler may either:

- Apply more broad (perhaps even whole-program) compilation options or flags that impose restrictions on floating-point optimization to match the requested policy.

- Diagnose an unsupported-feature warning and emit output code that does not encode/enforce the requested optimization policy.

The choice of which of these options to take may vary based on the chosen target and an implementer determination of the performance trade-offs involved.

## Policies and Their Ordering

While the `precise` policy is our focus in this proposal, we will define semantics in terms of a more general setting of *floating-point optimization policies*.

Given a universe `U` of floating-point optimizations/transformations that a compiler might be permitted to perform, a floating-point optimization policy `P` is a subset of `U`.
The `precise` policy is `U` with permissions for optimizations that involve implicit contraction and reassociation removed.

A policy `A` is at least as restrictive as `B` when `A ⊆ B`.
The meet under inclusion is intersection; the join is union.
Combining demands therefore computes intersections.

A declaration of a storage location (such as a variable) has a *declared* policy, based on the declaration and its modifiers.
Absent any modifiers that affect policy (such as `precise`) the declared policy of a declaration is `U` (all optimizations permitted).
The `precise` modifier on a declaration indicates that its declared policy is the `precise` policy.

Policies describe permissions, not obligations to optimize.
An implementation can emit separate operations even when contraction is permitted.
A Slang compiler producing an intermediate language cannot guarantee that a downstream compiler will make use of every permission that the Slang compiler leaves available.
The rules below distinguish restrictions that an implementation must apply from additional restrictions that it may apply to simplify propagation.
Avoiding restrictions beyond those permitted additions is a quality-of-implementation concern.

We model propagation using constraints that require one policy `P` to be at least as restrictive as another policy `Q`: `P ⊆ Q`.
The required constraints and permitted conservative additions determine which restrictions reach each computation.

## Required and Permitted Propagation

Because `precise` only defines a restriction on allowed optimizations, and optimizations are never guaranteed to be performed, a semantically valid implementation of `precise` could just apply a restriction globally, for an entire program.
That is obviously undesirable, so we need a way to define our expectations on what an implementation **should** do, as distinct from what it **must** do.

We will use the term *required propagation* when defining constraints, restrictions, and rules that an implementation **must** apply.
An implementation is incorrect if it ever performs (or emits code that allows a downstream compiler to perform) an optimization that was not permitted by policies computed entirely from required propagation.

We use the term *permitted conservative propagation* to define additional constraints or rules that an implementation **may** apply.
One example of a permitted conservative propagation rule is propagating a policy demand on a read operation to *all* assignments to a variable, rather than only those that might contribute to the value yielded by the read.

Valid user programs must only rely on required propagation rules.

A compiler implementation **should** apply optimization policies that lie somewhere between what is required and what is permitted.
We use the term "should" because this is ultimately a quality-of-implementation consideration, as an implementation that *never* optimizes floating-point arithmetic can still be semantically valid.

If we consider the specific case of `precise` operations and compilation to SPIR-V,  constraints on optimization policies result in zero or more operations being marked with the `NoContraction` decoration.
In such a scenario, we are saying that the markings emitted by a compiler should satisfy the relationship:

```text
required markings ⊆ emitted markings ⊆ permitted markings
```

The required markings are those obtained by solving the required constraints alone.
The permitted markings are those obtained by solving the required constraints together with every conservative addition from the permitted rules.
Both sets account separately for restrictions imposed by compilation options and the documented target mapping.

A missing required marking is a correctness error.
A marking outside the permitted set need not change the program's semantics, but is a quality-of-implementation issue because it exceeds the intended bounds on propagation.
These bounds concern restrictions on surviving computations; they do not require an implementation to retain dead computations or perform an optimization merely because it remains allowed.

An implementation starts with the required constraints as defined here, and may add in any permitted conservative constraints at its discretion.
For the resulting set of constraints, the *greatest solution under inclusion* is the most permissive assignment of optimization policies satisfying the constraints.
The compiler can compute it by starting from `U`, applying declared restrictions, and propagating intersections to a fixed point.
Propagation takes not only the required constraints into account, but also any permitted conservative constraints that an implementation added; a conservative addition of a constraint can thus trigger further required propagation.
For a finite permission universe `U` and a finite representation of a function, this process terminates.

This proposal is primarily concerned with computing the policy constraints on expressions and storage locations, but it is important to note that Slang and some downstream compilers also support restrictions on floating-point optimization being provided as compilation options, or specified module/program-wide.
An optimization must only be performed if it is allowed by both the compilation options and per-operation policy constraints.

## Expressions, Storage Locations, and Declarations

For a function `F`, define:

| Notation | Meaning |
| --- | --- |
| `E(e)` | The effective policy for expression `e` in `F`. |
| `D(d)` | The declared policy of storage declaration `d`, possibly containing a symbolic output-policy parameter. |
| `L(F, p)` | The effective policy for storage location `p` within `F`. |
| `C` | The compilation-option policy, stored separately from the policies above. |

For a storage location introduced by declaration `d`, `L(F, p) ⊆ D(d)`.
Declarations without an explicit restriction use `D(d) = U`.
An effective policy inferred in `F` does not modify `D(d)` or the effective policy inferred for the same storage location in another function.
For example, inferring a restriction when `F` reads an ordinary global does not constrain another function's assignments to that global.
An explicitly restricted global declaration constrains accesses that refer to that declaration within the analyzed function, including aliases established from that storage location within the function.
An incoming ordinary reference parameter starts from its own declaration's policy; the analysis does not import a caller's declaration policy merely because the parameter can refer to that caller's storage.

The policy of an expression that identifies a storage location is distinct from the storage location's policy.
In particular, reading an explicitly precise variable does not automatically make the containing expression precise.
Instead, a demanded read requires `L(F, p) ⊆ E(read(p))`.
That direction records the demands on the storage location without introducing forward propagation from a variable.
The write rules below distinguish declared restrictions from demands inferred from individual reads; the summary `L(F, p)` does not by itself require applying every inferred restriction to every write.

As permitted conservative propagation, an implementation may group all components/elements of a local aggregate/array as one logical storage location when inferring `L`.
Implementations may be more granular and distinguish more storage locations (e.g., per-component or per-element) so long as they still apply all of the constraints that are required.
Even without field qualifiers, a read under a precision demand can lead to an inferred restriction on an individual field or element.
Whole-aggregate writes and output arguments must respect the inferred restrictions applicable to those writes under the write rules below.

For the purposes of this proposal, a *root storage location* denotes the storage named by the declarations of parameters, locals, globals, etc. that are visible to the function being analyzed.
Distinct declarations (distinct locals, globals, or parameters) are treated as denoting distinct root storage locations for policy inference, even if they might alias at runtime.
An implementation must account for reads and writes that refer to all or part of a storage location, including cases where intermediate optimizations may have introduced potential aliasing between storage locations, or ambiguity about which root storage location a given pointer points into.
In such cases, an implementation must be conservative about how it applies constraints, rather than risk missing a possible contributing write to a storage location.

The policy that applies to a function parameter (for any parameter-passing mode, including by-reference parameters) is determined entirely by the function that declares the parameter.
Even when the argument, at a call site, refers to a storage location with one or more policy constraints (from the perspective of the caller), those constraints do not apply to the corresponding parameter in the callee.
Each parameter represents a distinct root storage location, independent of the storage locations named by arguments at call sites.

## Local Constraint Rules

The following table defines required propagation within a function.
It distinguishes a restriction originating at a declaration from one inferred from a read, because the latter need not apply to every write.
The permitted conservative additions are listed separately below.

| Construct | Policy constraints or behavior |
| --- | --- |
| Initialization or assignment to `p` from `r` | The expression `r` receives the declared policy of the destination, inherited through projections from the declaration that introduces the storage. It also receives demands propagated to this write from reads. An assignment expression used as a value propagates its expression demand to the assigned value. |
| Whole-aggregate write | Apply the write rules to the affected contained storage locations and the corresponding input components. Containment means fields and elements, not following pointers stored inside them. |
| Return of `r` | Treat the function's result as an output storage location and apply the write rules to `r`. |
| Read expression `u` from `p` | `L(F, p) ⊆ E(u)`. For each write that can contribute to the value of `u`, propagate the demand to the corresponding input expression `r` using `E(r) ⊆ E(u)`. For an aggregate write, `r` is the matching input component identified by the whole-aggregate rule, rather than necessarily the whole input expression. |
| Value-producing field or component projection | The base expression receives the projected expression's demand. |
| Value-producing array subscript | Both the base and the index receive the result expression's demand. |
| Value-producing built-in dereference | Both the expression computing the address and the conceptual read of the addressed storage location receive the demand. |
| Address-valued expression, including address-taking | A demand propagates to evaluated operands that compute the address, including indices in a projected storage location. Taking an address does not by itself demand the stored contents. |
| Storage location projection from `p` | The projected storage location's effective policy is at least as restrictive as `L(F, p)`. |
| Conditional expression `c?x:y` | Both possible result expressions receive the result demand. The condition receives no demand merely for selecting a result. |
| Conditional statement or loop | No additional edge from an assignment to its controlling predicates is introduced. |
| Function call | Apply the input/output rules in the next section. An ordinary call does not expose its body to the caller's analysis. |
| Lambda expression | Supply the expression's settled policy to every computation in the lambda's own body, analyzed separately as described in Lambda Body Policies. |

The following additional propagation is permitted when it simplifies analysis:

| Case | Permitted conservative propagation |
| --- | --- |
| Demand inferred from a read | Apply the demand to every write to the same storage location, including writes that cannot contribute to that read. An implementation using the location summary for all writes may apply `E(r) ⊆ L(F, p)` to every expression `r` written to `p`. |
| Aggregate storage | Treat fields, components, or elements of the same aggregate as one storage location. Reads contribute demands to the common summary, and the applicable demands propagate to writes; the shared policy does not propagate forward to consumers of ordinary reads. |
| Whole-aggregate write | Apply the intersection of the demands on the affected destination components to the entire input expression rather than only to the corresponding components. |

These conservative additions may be combined and their consequences propagated to a fixed point.
They do not permit propagation through an ordinary function boundary or into a controlling predicate merely because a precise computation depends on that predicate.

Note that the required-propagation table does not include syntactic forms that are either sugar for function calls (e.g., operator expressions `x +  y`, `a += b`, etc.) or can be modeled *as if* they desugar into calls (property/subscript access, constructor calls, method calls).
All of those cases use the same rules as for ordinary function calls.

For `&&` and `||`, a demand on the Boolean result reaches both operand expressions, including the operand that also controls evaluation of the other.
Their operands contribute to the logical value.
This does not add an edge from an ordinary `if` or loop assignment to a predicate used only to control execution.
An unevaluated type query has no demand edge to a value computation that the query does not evaluate.
For a sequencing expression ("operator comma"), only the expression supplying its result receives the result demand; side effects still obey the separate write rules.

Note that most arithmetic operations, including floating-point operations for scalars, vectors, and matrices, are defined as functions in the Slang standard modules.
These operations derive their semantics from the same function-call rules used for calls to user-defined functions.
Standard-module function declarations for relevant arithmetic operations will need explicit decisions about whether they get an `[InheritFloatingPointPolicy]` attribute, in order to properly propagate a developer's intuitive model for propagation through "built-in" operations.

Note that the rules defined in this proposal do not require preserving a computation that can be removed without an observable effect.
An implementation may prove that a write or component cannot contribute to a demanded read and omit that read-inferred demand unless it chooses the corresponding permitted conservative propagation.
Such a proof does not cancel a declared restriction on a surviving write or a dependency explicitly required by the rules, including function-call input dependencies and subscript index dependencies.

## Calls and Policy Arguments

An *input* parameter is one whose parameter-passing mode allows an incoming argument value to be read by the callee.
An *output* parameter is one whose parameter-passing mode allows the callee to write to a location that the caller can then read.
These definitions apply to both ordinary parameters and receiver parameters (whether implicit or explicit).
It is possible for a single parameter to be both an input and an output.

For a call, let `R` be its result-expression policy, or `U` when no result is demanded.
For each storage location `p_i` referred to by an output argument, let `O_i` be the intersection of the policies applied to the call's writes to that location and its writable contained storage locations, using the write rules above.
Declared restrictions always apply to those writes; read-inferred demands apply when the writes can contribute to the demanded reads, together with any permitted conservative propagation selected by the implementation.
An implementation that applies the location summary to every write can use `L(F, p_i)` for a scalar location, or intersect the summaries of the affected sub-locations for an aggregate.
The required call rules consider every contained storage location the parameter's passing mode allows writing; they do not inspect the callee to narrow that set.
Writing a stored pointer value is distinct from writing through that pointer.
The input/output classification concerns declared parameter modes, rather than every memory side effect a function might perform.
The combined output demand is:

```text
Q = R ∩ O_0 ∩ O_1 ∩ ...
```

As required propagation, every input argument expression `a` satisfies `E(a) ⊆ Q`, even when the callee does not use that input to compute an output.
Output-only arguments contribute their destination policies without demanding their old contents.
When a parameter reads storage through a reference, its input is modeled as a read of the incoming stored value, not merely evaluation of an address.
That read applies the read rule to the storage location referred to by the argument.
For a projected input such as `values[index]`, it also applies the value-producing projection rule, including the index demand.
An `inout` argument receives both this input treatment and the treatment for output storage locations.
An output-only argument has no such conceptual read, so forming its destination does not automatically demand its index arithmetic.

The caller-side rules depend only on the declared signature of the callee, and never on the computations in the body of the callee.
Calls through values of function type follow the same rules as for calls to a known callee.

Explicit `precise` qualifiers on the parameter declarations of a function declaration, or applied to the function declaration's result, only affect the computation of optimization policies within the body of that function declaration.
Such qualifiers do *not* impose policy demands on arguments at call sites to that function.
Semantically, `precise` qualifiers on function parameters or results are part of the *implementation* of the function and not truly part of the function *signature*.

> Note: A Slang implementation is encouraged to diagnose a warning when developers apply the `precise` qualifier to function parameters or results.
> While such use cases are well defined (and allowed in other similar GPU languages), their semantics are often surprising to programmers.
> We expect this to be a particular point of confusion for developers migrating from HLSL to Slang if they are used to the way that `precise` tends to work in DXC.

When a function declaration has an `[InheritFloatingPointPolicy]` attribute, that function has a single implicit *optimization policy parameter*.
Whether or not a function has an optimization policy parameter is part of its signature, but does not affect overload resolution.
When determining if two function declarations in a given scope conflict with one another, a difference in the presence/absence of an optimization-policy parameter does not make two declarations non-conflicting.

At a call site to a function without an optimization policy parameter, no policy argument is computed or provided.
The policy demands used in the body of the callee are unaffected by the call site.

At a call site to a function with a single implicit optimization policy parameter, the compiler implicitly passes `Q` as the argument for that policy parameter.
If per-output optimization-policy parameters are supported, then at a call site to a function with per-output policy parameters the compiler passes `R` for the result policy parameter and `O_i` for each corresponding annotated output policy parameter.

The policy arguments passed to a callee are determined only after propagation of constraints within the caller has reached a fixed point.
Note that there is no mechanism by which propagation analysis for a callee can feed back new demands to a caller, so it is always possible to reach a conclusive fixed-point result within a caller independent of its callees, even in the presence of optimization-policy parameters.
Support for callee function parameters to impose policy constraints on input arguments could be considered as future work.

A *policy specialization* consists of a reference to a function with one or more policy parameters, and a tuple of concrete policy arguments for those parameters.
Policy propagation analysis must be performed for each unique policy specialization that a program executes.
For the analysis of policy propagation for a given policy specialization key, the initial policy demand on each output parameter of the function (and the function's result) is constrained by the corresponding policy parameter.
If a parameter or result has a declared policy and is affected by a policy parameter, then its initial policy demand is the intersection of the two.

When performing policy propagation analysis for a policy specialization of a function, any calls within that body may pass policy arguments to a callee, and may require additional policy specializations.
Calls to functions without optimization-policy parameters are not handled specially when analyzing a policy specialization; such calls are still boundaries that prevent propagation of policies across functions.

> Note: While this proposal treats specialization for policy arguments as something demand-based like specialization of generics, so long as the only relevant policy is `precise` and we only support a single catch-all policy parameter on a declaration, it is reasonable for a compiler to simply compile two copies of each policy-parametric function and then select between them at call sites.

The type of a function with one or more policy parameters must take the existence of those policy parameters into account, just as a generic function is given a type that accounts for its generic parameters.
Similarly to the situation for a generic function, the type of a function with one or more policy parameters is not a proper type, and is not expressible with the `functype` syntax.
If an expression naming a function with a policy parameter is used in a context where an expression of proper type is expected, an implicit coercion will apply that specializes that function to any necessary policy arguments, yielding a value of a proper function type.
In such a case, all of the policy arguments for the function will be the policy that applies to the expression that named the function.

> Note: These rules consider the case where a function with a policy parameter is passed into a higher-order function.
> The body of the higher-order function will not have been compiled knowing that its parameter of function type would have a policy parameter, and thus analysis of that higher-order function would not know to pass a policy argument at call sites.
> Instead, the policy arguments must be bound by the code calling the higher-order function.
>
> Passing a function `f` with a policy parameter as an argument binds that policy where the function value is formed.
> A forwarding lambda such as `(x) => f(x)` selects the same specialization when its expression receives the same demand, using the lambda-body rule below.

## Lambda Body Policies

A lambda expression supplies its settled expression policy as an initial demand on every computation in its own body.
The body is analyzed as a separate function; its incoming body policy is distinct from the output-only policy parameter introduced by `[InheritFloatingPointPolicy]`.
An ordinary call in the body still follows its declared callable contract.

This body demand includes predicate computations and computations that do not contribute to the lambda's outputs.
Demanding a predicate in this way is direct initialization of its policy, not an edge added by control-dependence analysis.
A nested lambda expression receives the containing body's demand and supplies its settled policy to its own body in turn.
Named functions and methods declared inside a body remain separate ordinary boundaries.

The enclosing function determines the policy for each lambda expression without inspecting a higher-order callee.
A lambda body version is selected using that policy before its callable value is passed to another function.
The bound value retains the selected version when passed onward or returned; invocation does not rebind the policy.
The same enclosing analysis binds implicit policy arguments when coercing a policy-parametric function to a proper function value.

The body rule alone does not impose a demand on computations in the enclosing function that produced captured values.
The relationship between a demanded lambda expression and its captured values or capture initializers, especially reference captures, remains an explicit design question.
It must not be implemented by silently feeding the lambda body's inferred policies back into the enclosing function.

## Compilation Options and Operation Semantics

The *operational permission set* for an expression is `E(e) ∩ C`.

The local required/permitted permissions for an expression are computed using propagation based on the program text alone, and do not take into account the permission set `C` that is allowed via compilation options.
The operational permission set for an expression includes only those optimizations permitted by *both* the locally-computed permissions and compilation options.

Any Slang implementation that performs optimizations on floating-point operations must take `C` into account and only perform optimizations that are permitted by the operational permission set for an expression.
If `C` is not yet known (e.g., in a compiler that performs both front-end target-independent optimizations and back-end target-specific optimizations, and only receives `C` in the back end), an implementation must conservatively assume `C` could be the empty set.



The local required and permitted propagation bounds are computed independently of `C`.
Checks of emitted markings must also account for `C` and the documented target mapping; a globally restrictive option can hide differences between local propagation choices.
Relevant Slang passes consult `C` directly; the compiler does not run a pass that copies its permissions onto every IR instruction or propagates them through program dataflow.
Compilation-option policy is limited to controls supported for an output program as a whole, such as downstream compiler flags or target execution settings.
A target emitter may need repeated target annotations to express a global request without creating corresponding policy dataflow in Slang IR.

Local restrictions cannot be relaxed by a more permissive compilation option.
Existing global precise modes can continue imposing broader restrictions everywhere, together with their other numerical settings.
This proposal does not redefine an existing option bundle as an exact synonym for the local modifier.

A transformation involving several operations must respect the policies of all affected operations.
For example, a permitted addition does not authorize contracting its multiplication operand when that multiplication is constrained.
When lowering one operation into several, the lowering must preserve the original evaluation contract rather than mechanically assuming that copying one attribute is sufficient.

Policies also do not define the complete semantics of explicit numerical operations:

- A precise `mad` must use a consistent fused or unfused interpretation for a given target and operand types across shaders.
  Separately written multiplication and addition may not be contracted merely because an explicit `mad` is available.
- A proposed `fma` contract requests fused evaluation when the target exposes a way to require it, with documented fallback where that control is unavailable.
  The existing GLSL450 `Fma` instruction alone does not guarantee fusion; [`VK_KHR_shader_fma`](https://docs.vulkan.org/refpages/latest/refpages/source/VK_KHR_shader_fma.html) provides a stronger capability.
- Defining `dot` and matrix `mul` as chains of `mad` requires choosing the reduction order and preserving it through lowering.
  Native dot/matrix operations do not necessarily expose that choice.

The final `mad`/`fma` contracts, policy consistency under scalarization, and the reduction-order choice remain explicit design decisions.
The implementation must not silently turn the open reduction-order question into a language guarantee.

## Interfaces, Generics, and Compatibility

### Interface Requirements

An interface requirement can declare the same policy-inheritance contract as a concrete function.
A satisfying declaration must explicitly provide the corresponding contract in the same positions.
The initial implementation does not infer missing attributes.
If independent policy parameters are exposed, matching includes which output positions share parameters.

Consider this proposed example:

```slang
interface IPolynomial
{
    [InheritFloatingPointPolicy]
    float evaluate(float x);
}

struct Linear : IPolynomial
{
    float scale;
    float offset;

    [InheritFloatingPointPolicy]
    float evaluate(float x)
    {
        return scale * x + offset;
    }
}

[InheritFloatingPointPolicy]
float evaluateAt<T : IPolynomial>(T polynomial, float x)
{
    return polynomial.evaluate(x);
}

float useLinear(Linear polynomial, float x)
{
    precise float value = evaluateAt(polynomial, x);
    return value;
}
```

The assignment in `useLinear` gives the result of `evaluateAt<Linear>` a restrictive policy.
The demand reaches the call to the interface requirement.
The requirement's attribute supplies a policy argument for the satisfying `Linear.evaluate` implementation.
After ordinary type specialization selects that implementation, policy specialization can produce its constrained version without requiring inlining.
Removing the attribute from `Linear.evaluate` makes the conformance invalid.

Calls expressed through an interface use the requirement's contract.
Devirtualization must not add a guarantee absent from that contract merely because it discovers an implementation with an additional attribute.
Overload resolution must still consider other compatible candidates rather than reject a conformance upon finding one same-name declaration without the attribute.

### Forwarding Witnesses

Slang can synthesize a method with a requirement's exact signature and a body forwarding to a user method.
Policy inheritance must be an explicit capability of the user-supplied declaration selected to satisfy the requirement.
The compiler cannot establish that opt-in by attaching an attribute only to a generated adapter.
For example, omitting the attribute from `Linear.evaluate` above must not be repaired by generating a method conceptually equivalent to:

```slang
[InheritFloatingPointPolicy]
float synthesizedEvaluate(Linear polynomial, float x)
{
    return polynomial.evaluate(x);
}
```

The output demand would apply within the synthesized method and stop at its call to the unannotated `Linear.evaluate`.
The user-supplied implementation selected for the requirement would never receive the requested policy.
In contrast, a programmer may deliberately write an attributed wrapper containing an ordinary call; its explicit declaration makes that inner boundary the programmer's choice.
Neither case promises to constrain all transitively called functions.
For the initial implementation, strict policy-inheritance requirements therefore cannot be satisfied by this forwarding synthesis path.
A directly matching attributed declaration can satisfy the requirement.
A genuine attributed default implementation remains a function body that must obey its declared contract; it is not the same as manufacturing a forwarding witness.

Later work may admit adapters after proving that the selected callee supplies the contract and that result conversions, output temporaries, and receiver adaptation preserve its policy arguments.
That validation is outside the initial effort.

### Standard Numeric Interfaces

The `slang.numerics` module is experimental.
Its numeric requirements and standard conformances can be updated together to carry the explicit contracts needed for generic arithmetic.
Attributing only the outer operator wrappers would leave an ordinary boundary at the requirement call and would not provide the intended propagation.

Existing core numeric interfaces need a temporary compatibility exception because user code already supplies conformances without the attributes.
We propose strict matching for conformances provided by standard modules, while allowing existing forwarding synthesis for user conformances to a specifically enumerated set of legacy core numeric requirements.
The exception does not apply to arbitrary interfaces or to `slang.numerics`.

For a legacy user conformance, the generated forwarding method is a deliberate policy boundary at the call to the unannotated implementation.
The compiler must not claim that the inherited policy constrains arithmetic in that implementation.
The optional boundary diagnostic should identify the user implementation when a restrictive policy stops there.
This exception preserves compatibility with a weaker guarantee; it does not provide the strict contract through another mechanism.

The compiler must identify standard-provided conformances and legacy requirements from explicit semantic identities.
File paths, a user's module name, or a naming convention are insufficient authority for the exception.
The exact legacy requirement list must be audited before implementation.
The compatibility mechanism should be removed when the corresponding core interfaces can be removed.

### Calls That Cannot Be Specialized

Concrete generic witness calls can normally select an implementation during ordinary backend specialization.
For dispatch over a finite known set of implementations, policy specialization can produce a dispatcher that selects the corresponding policy version of each implementation.
Every generated forwarding call must preserve the contract.

Open runtime dispatch and separately supplied implementations require an additional agreement about how policy-specific implementations are provided.
An attribute alone cannot create a version of an unavailable body.
The initial implementation must reject an attributed call with an error when neither a body nor a target implementation honoring the requested policy is available.
Suppressing optional warnings cannot permit calling a nonexistent policy version.
This is distinct from the documented accepted-but-ignored behavior of local restrictions on an unsupported target.
Supporting that case through an ABI is separate work.

## Diagnostics

### Calls at a Policy Boundary

We propose an optional warning, disabled by default, for a call to a user-defined function when an output has a restrictive demand and the corresponding callable contract does not inherit it.
A possible message is:

> The floating-point policy applied to this output does not propagate into this function.

The message describes a boundary, not proof that the function produces an unsuitable result.
The function may already contain explicit precise computations.
The demand at the call may follow from required propagation or from permitted conservative propagation; the warning describes the policy applied by this compilation in either case.
For per-output contracts, an attribute on an unrelated output does not suppress the warning.
Calls through interfaces use the requirement contract.
Standard-provided functions are excluded from this migration warning, except that the legacy compatibility path should expose a boundary at the user implementation.

An explicit acknowledgement attribute on the function can suppress the warning without adding policy inheritance.
The spelling and the interaction with globally restrictive compilation options remain to be selected.
The warning must not appear or disappear merely because ordinary inlining succeeds.

### Inferred Restrictions on Local Variables

A second optional diagnostic can identify a local declaration without an explicit modifier when the implementation's chosen analysis infers a more restrictive policy for that storage location.
Its purpose is to make indirect restrictions visible at declaration granularity.
For example, it could explain that `product` in the [main proposal's backward-propagation example](000-precise-semantics.md#proposed-approach) is constrained because its value contributes to `sum`.
If the restriction instead results from permitted conservative propagation, such as grouping aggregate fields or considering overwritten writes, the diagnostic should explain that reason.
It should report restrictions inferred by the chosen analysis, rather than every restriction that some permitted conservative analysis could infer.

The compiler needs an explicit correspondence between the declared local and the analyzed storage location to emit that diagnostic reliably.
It must not reconstruct storage identity from source locations after SSA conversion.
A future front-end analysis could provide better coverage; a backend implementation needs preserved declaration identity and provenance.

We propose that an acknowledgement attribute on a local declaration, if introduced, suppress only this diagnostic.
It must not relax the local's effective policy or stop a demand from a precise consumer.
A modifier that stops backward propagation would weaken the guarantee for the eventual precise output and is not proposed here.
This distinction avoids suggesting that a local spelling can override the contract requested for its eventual output.

## Compiler Integration

### Representation Before Policy Resolution

The front end rejects `precise` on field declarations in `struct` and `class` types.
It checks the applicability and compatibility of policy-inheritance attributes and records declared policies on supported declarations.
AST-to-IR lowering represents attributed functions as ordinary `IRFunc` instructions with additional policy-contract metadata.
It does not encode the implicit policy parameters as ordinary Slang generic parameters.

The compiler also needs to preserve explicit policy requests, the identity of relevant storage declarations, and the original function boundaries.
It must preserve the association between a lambda expression and its generated body, and the policy binding performed when a function expression becomes a proper function value.
It must preserve which expression operands receive a demand.
In particular, converting a conditional expression to an eager selection instruction, or the reverse, must not change whether its predicate receives a demand.
The producer must record that distinction before lowering erases it; source locations are not a substitute for semantic provenance.
A proposed `makePrecise(value)` instruction records a demand without changing the value.
For the general policy model, the operation needs an associated policy operand or an equivalent representation.
Assignments through fields, arrays, swizzles, and output parameters must preserve the same information about the declared storage location as direct assignments.

The marker preserves a demand when storage disappears.
It does not, by itself, prevent an unaware optimizer from changing arithmetic inside its operand graph.
Until policy resolution finishes, earlier passes must preserve unresolved demands and the evaluation contract of their surviving contributors.
Sound dead-code elimination and simplification remain permitted.
Inlining implementation machinery for an operator must not accidentally make ordinary user calls transparent.

### Proposed Pipeline Intercept Points

We propose the following logical sequence.
The sequence states representation invariants rather than assuming that the current pass list already provides these divisions.

| Phase | Required behavior and result |
| --- | --- |
| Semantic checking and IR generation | Validate contracts, preserve declared policies, local declaration and user-call identities, and expression dependency roles; represent unresolved demands. |
| Ordinary specialization and language lowering | Complete ordinary generic and witness specialization with its necessary simplifications. Preserve function-boundary and policy metadata. Defer floating-point rewrites incompatible with unresolved demands. |
| Local policy inference | With a function's policy arguments fixed, solve the required constraints and selected permitted conservative additions to a fixed point. Record settled policy arguments at calls without consulting the bodies of called functions. |
| Policy specialization | Clone ordinary specialized `IRFunc` bodies as needed for canonical policy-argument tuples and analyze those versions locally. Reuse a version only when its original function and complete policy tuple match. |
| Constrained operations | Replace resolved demands with policy attributes on the affected operations and preserve requirements on later intrinsic expansions. No unresolved demand may reach an unaware arithmetic optimization. |
| Performance optimization and target lowering | Respect operation attributes together with the separately stored compilation-option policy. Preserve those contracts through inlining, scalarization, intrinsic expansion, and legalization. |
| Emission | Map constrained operations and global options to supported target mechanisms; diagnose unsupported guarantees. |

Policy specialization is its own transformation after ordinary generic specialization.
It may use an ad hoc cache and work queue for specialized function copies.
The local-inference and policy-specialization rows form one work-queue process, rather than two single whole-program sweeps.
The process starts from reachable functions whose incoming policies are fixed, including entry points.
A generated lambda body is scheduled after the enclosing analysis settles the policy of its lambda expression; it must not be analyzed as an unrestricted root merely because it lacks an output-policy parameter.
An inherited policy parameter on an entry point receives `U` because there is no Slang caller to supply an output demand; explicit restrictions on its outputs still apply.
Serialized Slang modules retain policy contracts and bodies for specialization when linked into an output program.
Analyzing a version settles its local policies, records its callee policy tuples, and schedules any versions not yet analyzed.
Each new version runs the same local inference with its own fixed policy arguments.
For a lambda, the version key also identifies its incoming body policy, which supplies initial demands throughout its own body.
The cache must distinguish this body policy from the output-only parameters of attributed function declarations.
There is no feedback from a callee's inferred policies to an already analyzed caller.
For a finite collection of ordinarily specialized functions and a finite policy domain, canonical tuple caching bounds the number of versions.
Policy specialization must not mutate the shared ordinary specialization when a later call requests a different policy.
The implicit parameters are a semantic model, not a requirement to extend the existing generic-specialization cluster.

The current compiler interleaves specialization, mandatory inlining, constant propagation, and simplification.
An implementation must audit those passes before treating the proposed sequence as established.
If preserving ordinary function boundaries through an early transformation is necessary, the producer must record that fact explicitly rather than recover it from the transformed call graph.

The following reference points describe the inspected compiler at revision `7be48fdef5999df5dd76f4883840ac0f86d2c4cd`.
They identify producers and consumers that an implementation must revisit, not a completed patch plan.

| Current implementation point | Relationship to the proposal |
| --- | --- |
| [`addVarDecorations`](https://github.com/shader-slang/slang/blob/7be48fdef5999df5dd76f4883840ac0f86d2c4cd/source/slang/slang-lower-to-ir.cpp#L3160) and [SSA decoration transfer](https://github.com/shader-slang/slang/blob/7be48fdef5999df5dd76f4883840ac0f86d2c4cd/source/slang/slang-ir-ssa.cpp#L695) | Preserve declared restrictions and their relationship to storage before promotion can remove a variable. Current decoration copying alone is not the proposed complete representation. |
| [Ordinary specialization loop](https://github.com/shader-slang/slang/blob/7be48fdef5999df5dd76f4883840ac0f86d2c4cd/source/slang/slang-ir-specialize.cpp#L1792) | Audit interleaved simplification and inlining before introducing the independent policy phase. |
| [`doesSignatureMatchRequirement`](https://github.com/shader-slang/slang/blob/7be48fdef5999df5dd76f4883840ac0f86d2c4cd/source/slang/slang-check-decl.cpp#L5704) and [forwarding synthesis](https://github.com/shader-slang/slang/blob/7be48fdef5999df5dd76f4883840ac0f86d2c4cd/source/slang/slang-check-decl.cpp#L7965) | Validate explicit policy contracts through direct matching and the synthesis fallback, with only the stated legacy exception. |
| [`computePreciseInsts`](https://github.com/shader-slang/slang/blob/7be48fdef5999df5dd76f4883840ac0f86d2c4cd/source/slang/slang-emit-spirv.cpp#L10653) | Replace emitter-specific demand inference with consumption of the shared resolved operation policy. |

### Rewriting and Emitting Constrained Operations

An operation's policy attribute must participate in instruction identity so that CSE cannot silently merge incompatible operation forms.
Builder support for copying attributes can make ordinary rewrites less error-prone.
Consumers must distinguish arithmetic operands from trailing attributes, and multi-operation rewrites need a semantic check of the complete transformation.

Intrinsic implementations using `spirv_asm` need explicit handling of both their input dependencies and the arithmetic they emit.
A direct SPIR-V backend must cover dot and matrix operations where applicable, as well as ordinary scalar/vector arithmetic.
Generated HLSL and GLSL must preserve the constraints even when output legalization changes the declarations that originally carried `precise`.
Emission should use the resolved operation contract rather than rerun a separate propagation analysis with different rules.

The global compilation-option policy remains separate throughout these steps.
Passes receive it through compilation context or explicit parameters.
Target-wide controls remain target-wide; they do not become a new graph of synthetic local declarations.

### A Possible Front-End Analysis

Once callable policy contracts are explicit, the local constraint rules do not inherently require examining callee bodies or knowing the final built-in arithmetic opcode.
A checked generic operator can refer to an attributed interface requirement before its implementation is known.
This makes a front-end policy analysis worth investigating, particularly for declaration-based diagnostics.

The initial implementation plan remains a separate post-specialization policy phase.
A front-end alternative must show how it represents policy-parameterized bodies, preserves demands through overloaded dispatch and later specialization, and produces the same restrictions as the language rules.
It should share those rules rather than introduce an independent approximation whose diagnostics contradict code generation.

## Validation Plan

The initial regression suite should verify required markings and the bounds of permitted conservative propagation.
On targets supporting the requested restrictions, a missing required marking is a correctness failure, while a marking outside the permitted set is a quality-of-implementation failure.
The expected sets must account for compilation options and the documented target mapping, including the separately diagnosed unsupported-target cases.
Tests that allow multiple permitted analysis choices should accept results within those bounds; tests for a particular implemented analysis can check its selected behavior more precisely.
The checks concern restrictions emitted by Slang, not whether a downstream optimizer exercises every permission that remains.
SPIR-V checks should associate `NoContraction` with the relevant instructions, rather than count decorations across unrelated arithmetic.
Generated HLSL/GLSL and IR-level checks are also needed to expose losses before downstream compilation.

| Area | Representative coverage |
| --- | --- |
| Declaration applicability | Rejection of `precise` on instance and `static` fields in both `struct` and `class` types; acceptance on supported declarations, including `static` locals. |
| Local expressions | Initializers, reassignment, compound updates, phi values, loops, logical/bitwise expressions, and demand propagation through casts and bit reinterpretation. |
| Storage locations | Whole-aggregate initialization/copy/return, qualified aggregates and their sub-locations, inferred restrictions on individual fields or elements, array reads and writes, dynamic indices, vector components, swizzled assignments, and potentially aliasing indirect accesses. |
| Selectivity | Required markings are present; independent arithmetic outside permitted propagation remains unmarked; a precise read does not constrain later consumers; overwritten writes and aggregate grouping exercise the permitted conservative additions. |
| Function boundaries | Caller argument arithmetic is constrained while an ordinary callee remains opaque, with and without inlining; named nested functions and locally declared methods remain boundaries. Lambda bodies are analyzed separately with the policies supplied by their expressions. |
| Function values and lambdas | Policy binding at value formation, bare functions versus forwarding lambdas, arithmetic and predicate computations in demanded lambdas, nested lambdas, ordinary calls inside lambdas, and bound values passed onward or returned. Capture cases require the separate capture-policy decision. |
| Outputs and receivers | Returns, `out`, `inout`, incoming stored values through references, projected read/write arguments, inferred restrictions on sub-locations of aggregate output arguments, implicit receivers, multiple outputs, and an unused result. |
| Policy-specialized calls | Default and precise calls to the same helper, nested attributed calls, explicit precise locals in a default version, and reuse independent of call order. |
| Interfaces | Matching and missing contracts, generic requirements, alternative overloads, genuine default bodies, and rejection through forwarding synthesis. |
| Numeric compatibility | Strict `slang.numerics` and standard core conformances; only enumerated legacy user conformances receive the documented exception. |
| Diagnostics | Boundary warnings and suppressions, explanations of required versus conservatively inferred restrictions, agreement with the chosen analysis where provenance is available, stable reporting across inlining, and no semantic relaxation from acknowledgement. |
| Target contracts | Direct SPIR-V, generated HLSL/DXIL and GLSL, global-option interaction, unsupported-target diagnostics, and intrinsic consistency cases. |

## Declared Field Policies as a Future Extension

The main proposal's [field-qualification extension](000-precise-semantics.md#allow-precise-on-fields) is outside the initial feature.
The following describes how it could extend these constraints.

This would be an extension of the proposed policy model, not a different formalism.
A field declaration `f` could supply a declared policy `D(f)`, adding `L(F, p.f) ⊆ D(f)` for a field sub-location `p.f` of aggregate storage `p`, alongside the existing constraint from the containing storage location.
Whole-aggregate writes and output-policy intersections would then account for those additional declared restrictions.
An inherited output policy would be combined with a field's declared policy by intersection.
The permission sets, fixed-point analysis, and function-boundary rules would remain the same.
We defer field qualification so that the initial implementation does not need to handle these additional declared restrictions.
