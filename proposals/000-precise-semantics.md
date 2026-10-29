# SP #000: Semantics for `precise` in Slang

We propose a definition of `precise` that restricts floating-point contraction and reassociation, together with an explicit way for functions to inherit those restrictions from their callers.
The definition builds on GLSL's function-local propagation rules.
It extends those rules with opt-in specialization so that developers can use ordinary helper functions and generic numeric code without making the behavior depend on inlining.

## Status

Status: Design Review.
This is an initial proposal, with remaining design decisions listed at the end.

Author: Theresa Foley.

Implementation: Not implemented.
This proposal addresses [Slang issue #13324](https://github.com/shader-slang/slang/issues/13324).

The new attribute spellings in this document are provisional.
Examples using those attributes illustrate proposed syntax and are not programs that the current compiler accepts.
The sections on compiler integration describe a proposed implementation, separately from the language semantics.

## Background

Floating-point expressions that are mathematically equal can produce different results after rounding.
For example, a compiler may evaluate `a * b + c` using either a multiplication followed by an addition, or a fused multiply-add with one rounding step.
Reassociating `(a + b) + c` as `a + (b + c)` can also change the result.

Those differences matter when two computations need to agree.
A depth prepass and a later rendering pass may compute the same vertex position in shaders that otherwise do different work.
A tessellation algorithm may compute a shared boundary from either of two adjacent patches.
Contraction of only one product in a symmetric expression can destroy the equality that the algorithm relies on.

Slang accepts `precise` today, but its effects depend on which declaration is qualified, the transformations performed before emission, and the compilation target.
The implementation records declaration decorations, transfers some of them during SSA construction, and performs a backward propagation walk in the direct SPIR-V emitter.
That arrangement leaves gaps when declarations disappear, when an intrinsic hides arithmetic, or when a computation crosses a function call.
The proposal replaces those incidental boundaries with a language contract.

We distinguish two tasks:

1. Define where a precision request applies within a function, including through intermediate storage and expressions.
2. Define which function declarations explicitly permit a caller's request to affect computations in the called function.

The first task should have useful semantics without the second.
The second should reuse the same rules inside each specialized function, rather than introduce unrestricted inference across a program's call graph.

## Proposed Approach

### What `precise` Requests

A `precise` declaration requests that the compiler preserve the grouping of contributing floating-point arithmetic and not implicitly contract separate arithmetic operations.
A *demand* is a restriction that a consumer requires for the evaluation of an expression.
Assigning to a precise destination places a demand on the expression computing the assigned value.
The compiler may still eliminate dead computations and perform transformations that preserve the applicable evaluation contract.
The request does not require increased precision.

For this draft, reassociation includes algebraic rearrangements that change the specified arithmetic dependencies, such as factoring `a * b + a * c` into `a * (b + c)`.
Replacing a division with separately specified reciprocal and multiplication operations is likewise not justified merely because the expressions are equal over real numbers.
An implementation may still choose a target-permitted implementation of the original division operation.
That operation's numerical accuracy and exceptional-value behavior remain governed by the target and compilation options.

Consider this example:

```slang
float compute(float a, float b, float c, float d)
{
    float product = a * b;
    precise float sum = product + c;
    float result = sum * d;
    return result;
}
```

The multiplication producing `product` and the addition producing `sum` are subject to the request.
The compiler cannot fuse those two operations.
The multiplication producing `result` does not become precise merely because it reads `sum`.
Propagation runs backward from the assignment into `sum`; it does not run forward from every use of `sum`.

We use *precise* as a convenient description of that restriction.
The formal model below represents restrictions as floating-point optimization policies, so that future modifiers can request other combinations of restrictions.

### Supported Targets and Source Dialects

We propose the same minimum meaning for `precise` in Slang and its HLSL- and GLSL-flavored input dialects.
The intended target mappings are GLSL `precise`, HLSL `precise`, and SPIR-V `NoContraction` on the contributing arithmetic.
HLSL's native modifier imposes additional restrictions, which remain valid stronger behavior on that target.

Some targets do not provide a way to impose the minimum contract on their downstream compiler.
For those targets, Slang accepts the declaration, emits an unsupported-feature warning, and can produce output without promising the requested numerical behavior.
Suppressing the warning does not add the missing target capability.
The target-support documentation must distinguish a supported restriction from an accepted but ignored request.
This proposal does not add per-operation emulation for every target.

The modifier alone does not request preservation of NaNs, infinities, signed zero, or denormals.
It does not establish a rounding mode, a ULP bound for special functions, or bitwise agreement across devices and compilation targets.
Those properties remain subject to the target and compilation options.

### Declaration Applicability

The proposed `precise` modifier applies to local and global variable declarations, fields, parameter declarations, and function results.
It can qualify aggregates and non-floating-point storage as well as floating-point storage.
For example, `precise int index = int(a * b + c);` places a demand on the floating-point producer without requiring a floating-point constraint on the integer conversion itself.
It does not introduce a distinct numeric type or qualify a type declaration.

A function-result modifier specifies the fixed declared policy of the conceptual output place representing its result.
A parameter modifier specifies a policy within the function implementing that parameter, for both copied-value and reference parameter modes.
In particular, `precise` on an input parameter does not impose a caller-side demand in this proposal.
The receiver follows the same parameter rules, although a spelling for explicitly qualifying an implicit receiver remains a syntax decision.

The function-level inheritance attribute applies to callable declarations and interface requirements.
It requires a result or at least one writable parameter, including a writable receiver; otherwise there is no output from which to inherit a policy.
The per-output form, if exposed, applies to a result or writable parameter.
These contracts do not select overloads based on a caller's policy demand, and declarations cannot be overloaded solely by changing policy annotations.

### Places and Assignments

A *place* is a storage location to which an expression can refer, such as a local variable, a structure field, or an array element.
The declaration of `sum` above makes that variable a precise place.
Fields and elements of a precise aggregate are precise places as well.
A field can also have its own declared restriction even when its enclosing variable does not.

Initialization, ordinary assignment, compound assignment, and increment or decrement all write places.
A restriction on the destination applies to the expression computing the written value.
For `total *= factor`, that computation includes the old value of `total`, the value of `factor`, and the multiplication.

A demand on an expression also applies to its contributing subexpressions.
For a value-producing built-in subscript `values[index]`, the demand applies to both `values` and `index`.
A cast propagates the demand to its operand.
Consequently, an integer expression can carry a demand back to floating-point arithmetic:

```slang
float lookup(float values[8], float a, float b, float c)
{
    precise float selected = values[int(a * b + c)];
    return selected;
}
```

The cast and integer index do not themselves need floating-point restrictions.
The multiplication and addition forming the index do.
The expression's type does not terminate propagation.

When propagation reaches a read from a local place, the compiler infers an effective policy for that place within the current function.
That policy can affect other assignments to the place.
The conservative reference model includes every assignment to an inferred-precise local, including an earlier assignment overwritten before the precise use.
An implementation may prove that a particular overwritten computation is irrelevant and avoid restricting it.
Developers should not rely on every such refinement being performed.

A whole-aggregate write also writes its contained fields or elements.
It must honor their declared restrictions even when no explicit projection appears:

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

The first initializer supplies `result.first`, so its multiplication and addition are constrained.
The compiler may conservatively restrict the complete initializer, but may not overlook the declared restriction on `first`.
The same contained-write rule applies to aggregate assignment and return.
Call outputs use the separate call rule below, which accounts for contained destination policies without inspecting an ordinary callee's body.

### Function Boundaries

Ordinary functions are boundaries for propagation into their bodies.
Consider this example:

```slang
float multiplyThenOffset(float x, float scale, float offset)
{
    return x * scale + offset;
}

float caller(float a, float b, float c, float scale, float offset)
{
    precise float result =
        multiplyThenOffset(a * b + c, scale, offset);
    return result;
}
```

The arithmetic forming `a * b + c` is in `caller` and receives the demand.
The arithmetic inside `multiplyThenOffset` does not.
The latter function would need its own precise output or an explicit policy-inheritance attribute.
Ordinary inlining must not change this language rule.

The same rule applies to method calls.
The receiver is an argument, including when the compiler supplies it implicitly.
Its parameter-passing mode determines whether it is an input, an output, or both.
Lambdas and methods declared inside a local type have their own function bodies for this analysis.
Textual nesting does not merge their scopes.

A call can produce outputs through its result and through writable arguments.
Restrictions on any of those outputs place a demand on every input argument expression:

```slang
void produce(float input, out float output)
{
    output = input * input + 1.0f;
}

float caller(float a, float b, float c)
{
    precise float result;
    produce(a * b + c, result);
    return result;
}
```

The input multiplication and addition in `caller` receive the demand.
The arithmetic in `produce` remains outside the caller's propagation scope.
An output-only argument contributes a destination policy, but its previous contents are not input values.
An `inout` or read-write reference argument participates in both roles.

### Functions That Inherit Output Policy

We propose an attribute, provisionally `[InheritFloatingPointPolicy]`, that gives a function one implicit optimization-policy parameter shared by its outputs.
At a call site, the compiler combines the policies required for the result and writable arguments and specializes the function for that policy.

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

The first call uses a version whose result is treated as if it had been explicitly declared precise.
The multiplication and addition producing that result are constrained.
The second call uses the default policy unless another use introduces a demand.
The compiler may share versions with identical policy arguments; it does not change the ordinary version when a precise call is encountered.

The attribute applies a policy to outputs and propagates backward from them.
It does not impose that policy on every computation in the function.
For example, unrelated arithmetic used only to update an ordinary global variable need not become precise.
Explicitly precise locals remain precise in every version.

The general model also supports separate implicit parameters for selected outputs.
Each affected output would be treated as if it had been explicitly declared with the policy requested for that output.
A shared function-level parameter deliberately combines those demands, so it can restrict more arithmetic than independent output parameters.
The syntax and initial availability of per-output annotations remain design decisions.
The semantics of the two forms are distinguished below.

For example, suppose an attributed function writes `a * b` to one output and `c * d` to another.
If only the first destination is precise, the shared attribute passes the precise policy for both outputs and constrains both products.
With independent annotations on those outputs, only the first product would be required to inherit that policy.
In either form, the conservative caller-side rule demands all input actual expressions because at least one output is precise.

### Control Flow

The initial proposal does not infer demands from control dependence.
An assignment into a precise place inside an `if` or loop does not, by itself, restrict the condition controlling its execution.
The same applies to conditional `break`, `continue`, and early return.
A demanded conditional expression propagates to its possible result expressions, but not automatically to its condition.

A condition can still receive a demand through an ordinary expression dependency.
For example, a comparison passed as an input argument to a demanded call is an input expression.
An eager selection intrinsic follows the ordinary call rule; a conditional expression follows the rule above.
These rules do not promise that every decision affecting a precise value is numerically stable.
A developer who needs that property can explicitly qualify the computations forming those decisions.

## Related Work

### GLSL `precise` and `invariant`

GLSL provides separate qualifiers for arithmetic restrictions and output invariance.
An `invariant` output must agree across programs under specified matching-input and matching-computation conditions.
Those conditions include relevant texture state, operation ordering, types, precision qualifiers, and control flow.
The qualifier permits optimizations performed consistently across the matching computations.

GLSL `precise` constrains arithmetic contributing to a qualified destination.
It preserves grouping and operator consistency, prohibits reassociation and implicit multiply-add contraction, and propagates backward within a function.
It excludes selection and iteration predicates.
A caller's precise destination does not constrain an ordinary callee's body.
Qualifying an aggregate qualifies its members recursively.
An explicit `fma` is treated as one operation, with consistency requirements for precise uses.
These contracts are specified separately in [GLSL 4.60, sections 4.8, 4.9, and 8.3](https://registry.khronos.org/OpenGL/specs/gl/GLSLangSpec.4.60.html#variance-and-the-invariant-qualifier).

The [ARB_gpu_shader5 rationale, issues 22–24](https://registry.khronos.org/OpenGL/extensions/ARB/ARB_gpu_shader5.txt), motivates `precise` through symmetric tessellation calculations.
Its function boundary lets programmers combine restricted and unrestricted subcomputations deliberately.
A precise input formal affects assignments inside its function, not the caller's argument expression.
The rationale permits assignment-specific propagation: one required assignment does not implicitly qualify every assignment to the same intermediate.
Our conservative place model allows that broader propagation, while permitting implementations to prove that particular assignments do not contribute.

Slang does not currently support GLSL's `invariant` qualifier.
This proposal does not introduce it or claim the same invariance contract.
Restricting arithmetic can help developers construct matching computations, but does not replace the conditions under which an invariance guarantee applies.

The glslang reference implementation performs an AST worklist analysis over assignments and structure-member paths before SPIR-V emission.
Its behavior is useful implementation precedent, but not a substitute for the GLSL language rules.
For example, current parameter handling discards `precise` on non-output formals, and the ordinary expression traversal can include ternary predicates.
These observations are pinned to glslang revision `e7917c4ff6c660aba47b2df0c84f123d5bb1c3ce`: [propagation](https://github.com/KhronosGroup/glslang/blob/e7917c4ff6c660aba47b2df0c84f123d5bb1c3ce/glslang/MachineIndependent/propagateNoContraction.cpp#L791), [formal parameters](https://github.com/KhronosGroup/glslang/blob/e7917c4ff6c660aba47b2df0c84f123d5bb1c3ce/glslang/MachineIndependent/ParseHelper.cpp#L6933), and [conditional traversal](https://github.com/KhronosGroup/glslang/blob/e7917c4ff6c660aba47b2df0c84f123d5bb1c3ce/glslang/MachineIndependent/IntermTraverse.cpp#L194).

### HLSL and DXC's DXIL Path

[Microsoft's HLSL documentation](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx-graphics-hlsl-variable-syntax) gives `precise` a broader contract than the minimum proposed for Slang.
It preserves separate operations and evaluation order and restricts unsafe transformations that disregard NaNs or infinities.
The demand propagates backward from qualified destinations; reading a precise variable does not automatically constrain subsequent computations.
The documentation recommends qualifying shader outputs.
It does not establish universal guarantees for rounding, denormals, or transcendental functions.

An explicit [HLSL `mad`](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/mad) may use a fused or unfused implementation for a precise result, provided its behavior is consistent across shaders on that hardware.
That differs from contracting multiplication and addition written as separate operations.

DXC's primary Direct3D path produces DXIL.
Before storage elimination, it records precision requests with temporary `dx.attribute.precise.*` calls.
Its propagation pass follows operands, contributing stores, and control dependencies.
It clears fast-math flags on affected arithmetic and comparisons and attaches `!dx.precise` to relevant floating-point calls.
The marker representation and broader propagation are implementation mechanisms, rather than a complete independent language specification.
See [marker construction](https://github.com/microsoft/DirectXShaderCompiler/blob/0d6c746365d1baf45cadc0b4cd8ab9cf79dc84bf/lib/HLSL/HLModule.cpp#L1033), [propagation](https://github.com/microsoft/DirectXShaderCompiler/blob/0d6c746365d1baf45cadc0b4cd8ab9cf79dc84bf/lib/HLSL/DxilPrecisePropagatePass.cpp#L112), and [flag clearing](https://github.com/microsoft/DirectXShaderCompiler/blob/0d6c746365d1baf45cadc0b4cd8ab9cf79dc84bf/lib/DXIL/DxilModule.cpp#L2081), pinned to DXC revision `0d6c746365d1baf45cadc0b4cd8ab9cf79dc84bf`.

DXC's early inlining enables caller-side demands to affect many user helpers.
Its implementation explicitly identifies cloning as unfinished work for surviving calls with mixed precision demands.
Thus observed propagation across a helper is not evidence of a complete interprocedural algorithm.
The proposed Slang attribute makes that behavior an explicit contract with specialized versions, independent of ordinary inlining.
See [DXC's cloning discussion](https://github.com/microsoft/DirectXShaderCompiler/blob/0d6c746365d1baf45cadc0b4cd8ab9cf79dc84bf/lib/HLSL/DxilGenerationPass.cpp#L900).

DXC's SPIR-V backend uses a separate analysis with different call boundaries.
It can propagate from precise formals to actual arguments, but a caller's demanded return does not constrain an ordinary callee's body.
It does not provide the DXIL pass's control-dependence analysis.
We therefore distinguish DXIL precedent from the behavior of DXC's alternative target.
See [the SPIR-V visitor](https://github.com/microsoft/DirectXShaderCompiler/blob/0d6c746365d1baf45cadc0b4cd8ab9cf79dc84bf/tools/clang/lib/SPIRV/PreciseVisitor.cpp#L252).

### Ongoing Clang HLSL Support

As of October 29, 2026, [Clang's simplified implementation proposal](https://github.com/llvm/llvm-project/pull/234462) remains open.
It would compile an entire translation unit with strict floating-point settings when `precise` occurs, rather than infer selective restrictions.
The [full-feature tracking issue](https://github.com/llvm/llvm-project/issues/100776) still identifies specification and design work.
The translation-unit approach is an interim implementation strategy and does not define DXC's selective behavior or the proposed Slang contract.

### SPIR-V and Floating-Point Environment Controls

[SPIR-V `NoContraction`](https://registry.khronos.org/SPIR-V/specs/unified1/SPIRV.html#DecorationNoContraction) prohibits combining arithmetic operations and reassociating them.
It does not independently establish the broader numerical environment described by HLSL `precise`.
For example, `SignedZeroInfNanPreserve` is an entry-point execution mode parameterized by floating-point width, with scope beyond a local expression.
Slang will not enable that mode merely because a declaration uses `precise`.
Future work on stronger numerical guarantees should expose those requirements deliberately.

## Detailed Semantics

### Policies and Their Ordering

Let `U` be the set of floating-point optimization permissions represented by this model.
A policy `P` is a subset of `U`.
An absent explicit restriction uses `U`.
The precise policy removes permissions for implicit contraction and reassociation.
Other numerical properties need not become policy elements merely because they are controlled by a floating-point compilation option.

Policy `A` is at least as restrictive as `B` when `A ⊆ B`.
The meet under inclusion is intersection; the join is union.
Combining demands therefore computes intersections.
The reference solution is the greatest assignment of allowed sets satisfying the constraints below: the solution retaining the most permissions.
An implementation can start with `U`, insert explicit restrictions, and repeatedly intersect until no set changes.
For a finite permission set and a finite function representation, that process terminates.

Policies describe permissions, not obligations to optimize.
An implementation can emit separate operations even when contraction is permitted.
The reference model also provides a quality-of-implementation baseline for avoiding unnecessary restrictions and testing Slang's emitted code.
It does not guarantee that a downstream optimizer will use every permission Slang leaves available.

### Expressions, Places, and Declarations

For a function `F`, define:

| Notation | Meaning |
| --- | --- |
| `E(e)` | The effective policy for expression `e` in `F`. |
| `D(d)` | The declared policy of storage declaration `d`, possibly containing a symbolic output-policy parameter. |
| `L(F, p)` | The effective policy for place `p` within `F`. |
| `C` | The compilation-option policy, stored separately from the policies above. |

For a place introduced by declaration `d`, `L(F, p) ⊆ D(d)`.
Declarations without an explicit restriction use `D(d) = U`.
An effective policy inferred in `F` does not modify `D(d)` or the effective policy inferred for the same place in another function.
For example, inferring a restriction when `F` reads an ordinary global does not constrain another function's assignments to that global.
An explicitly restricted global declaration constrains accesses that refer to that declaration within the analyzed function, including aliases established from that place within the function.
An incoming ordinary reference parameter starts from its own declaration's policy; the analysis does not import a caller's declaration policy merely because the parameter can refer to that caller's storage.

The policy of an expression that identifies a place is distinct from the place's policy.
In particular, reading an explicitly precise variable does not automatically make the containing expression precise.
Instead, a demanded read requires `L(F, p) ⊆ E(read(p))`.
That direction propagates demands backward to assignments without introducing forward propagation from a variable.

The initial conservative model may group all components of a local aggregate or all elements of an array when inferring `L`.
Explicit member declarations retain their own declared policies.
Implementations may distinguish more places when they can preserve every required restriction.
Neither this grouping nor inference introduces propagation into another function.

A place denotes storage as accessed through the declarations and parameters of the function being analyzed, rather than the spelling of one expression or the address-valued temporary produced by lowering.
Within a function, demands must account for reads and writes that can refer to the same storage, including indirect accesses through references or pointers.
An implementation may conservatively group potentially aliasing places.
If more than one declaration can supply the accessed storage, the conservative declared restriction is the intersection of the policies that can apply.
Grouping can add restrictions but cannot justify missing a possible contributing write.

Across a call boundary, the callee's parameter declaration supplies its local declared policy.
Passing a precise actual place to an ordinary reference or output parameter does not automatically transfer the actual declaration's policy into the body.
The explicit call rules determine which policies cross that boundary.
These rules add no synchronization or cross-invocation determinism guarantee.

### Local Constraint Rules

The following rules define the reference propagation within a function.
Each rule adds restrictions; no rule removes an explicit restriction.

| Construct | Policy constraints or behavior |
| --- | --- |
| Initialization or assignment to `p` from `r` | `E(r) ⊆ L(F, p)`. An assignment expression used as a value also propagates its expression demand to the assigned value. |
| Whole-aggregate write | Treat the write as writes to its affected contained places. Apply each destination policy to the matching input component; conservatively, apply their intersection to the whole input expression. Containment means fields and elements, not following pointers stored inside them. |
| Compound assignment or increment/decrement | Apply the assignment rule to the value computation, including the old destination value and the operator's other inputs. |
| Return of `r` | Treat the function's result as an output place and apply `E(r) ⊆ L(F, result)`. |
| Read from `p` | `L(F, p) ⊆ E(read(p))`. All assignments to the grouped place participate in the reference solution. |
| Built-in arithmetic, comparison, logical or bitwise operation, conversion, constructor, or bit reinterpretation | Each value operand has a policy at least as restrictive as the expression's policy. Only operations with relevant floating-point behavior acquire floating-point constraints. |
| Value-producing field or component projection | The base expression receives the projected expression's demand. Conservative inference can consequently restrict other components of the base. |
| Value-producing array subscript | Both the base and the index receive the result expression's demand. |
| Value-producing built-in dereference | Both the expression computing the address and the conceptual read of the addressed place receive the demand. Thus `*(pointer + index)` propagates to the same address computations as `pointer[index]`. |
| Address-valued expression, including address-taking | A demand propagates to evaluated operands that compute the address, including indices in a projected place. Taking an address does not by itself demand the stored contents. |
| Place projection from `p` | The projected place's effective policy is at least as restrictive as `L(F, p)` and any declared policy on the selected member. Forming a destination address alone does not demand its index arithmetic. |
| Conditional expression | Both possible result expressions receive the result demand. The condition receives no demand merely for selecting a result. |
| Conditional statement or loop | No additional edge from an assignment to its controlling predicates is introduced. |
| Function call | Apply the input/output rules in the next section. An ordinary call does not expose its body to the caller's analysis. |

For `&&` and `||`, a demand on the Boolean result reaches both operand expressions, including the operand that also controls evaluation of the other.
Their operands contribute to the logical value.
This does not add an edge from an ordinary `if` or loop assignment to a predicate used only to control execution.
An unevaluated type query has no demand edge to a value computation that the query does not evaluate.
For a sequencing expression, only the expression supplying its result receives the result demand; side effects still obey the separate write rules.

User-defined operators, property accessors, and subscript accessors follow their checked callable contracts.
They do not become built-in projections merely because their syntax resembles one.
Standard-module functions implementing primitive arithmetic need explicit policy-inheritance contracts when propagation must cross their calls.

The rules do not require preserving a computation that can be removed without an observable effect.
An implementation may also prove that an assignment or component cannot contribute to a demanded value and avoid the conservative restriction.
Tests of selectivity should use independent computations so that incidental sharing does not obscure the intended boundary.

### Calls and Policy Arguments

An *input* parameter is one whose incoming value may be read by the call.
An *output* parameter is one through which the call may write.
Parameter-passing modes determine those roles; a parameter can have both.
The same classification applies to an explicit or implicit receiver.

For a call, let `R` be its result-expression policy, or `U` when no result is demanded.
For each output actual place `p_i`, let `O_i` be the intersection of the effective policies of that place and the contained places that the parameter may write.
For a scalar place, this is simply `L(F, p_i)`.
This definition includes a precise field inside an otherwise ordinary aggregate.
The reference model includes every contained place the parameter's passing mode allows writing; it does not inspect the callee to narrow that set.
Writing a stored pointer value is distinct from writing through that pointer.
The input/output classification concerns declared parameter modes, rather than every memory side effect a function might perform.
The combined output demand is:

```text
Q = R ∩ O_0 ∩ O_1 ∩ ...
```

Every input actual expression `a` satisfies `E(a) ⊆ Q`.
Output-only actuals contribute their destination policies without demanding their old contents.
When a parameter reads storage through a reference, its input is modeled as a read of the incoming stored value, not merely evaluation of an address.
That read applies the read rule to the actual place.
For a projected input such as `values[index]`, it also applies the value-producing projection rule, including the index demand.
An `inout` actual receives both this input treatment and the output-place treatment.
An output-only actual has no such conceptual read, so forming its destination does not automatically demand its index arithmetic.
None of these caller-side rules inspects expressions inside an ordinary callee.
Calls through function values follow the callable contract represented by those values; a cast or conversion cannot silently add policy inheritance.

For an ordinary function, no policy argument is passed into its body.
Its output declarations and internal declarations provide its own fixed demands.
An explicit `precise` input formal has only that local meaning in this proposal; it does not impose a new requirement on caller arguments.

For the shared function-level attribute, the compiler passes `Q` as the one implicit policy argument.
For independent per-output annotations, it passes `R` for the result and `O_i` for the corresponding annotated output.
Unannotated outputs retain their fixed declared policies.
If an output also has an explicit restriction, substitution combines that restriction with the policy argument by intersection.

Call-site policy arguments are computed after the caller's local constraints reach their fixed point.
Analyzing a callee does not feed newly discovered demands back into its callers.
In particular, a precise local in a callee can restrict that function's formal parameter without implicitly strengthening the corresponding actual argument.
That limitation keeps analysis local and leaves input-policy contracts as separate future work.

For each concrete policy-argument tuple, the callee's effective policies are those obtained by applying the same local rules with its output-policy parameters substituted.
A demand reaching a call inside that body follows the called declaration's contract in turn.
Unannotated calls remain boundaries even inside an attributed function.

### Compilation Options and Operation Semantics

The operational permission set for an expression is `E(e) ∩ C`.
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

> The floating-point policy required for this output does not propagate into this function.

The message describes a boundary, not proof that the function produces an unsuitable result.
The function may already contain explicit precise computations.
For per-output contracts, an attribute on an unrelated output does not suppress the warning.
Calls through interfaces use the requirement contract.
Standard-provided functions are excluded from this migration warning, except that the legacy compatibility path should expose a boundary at the user implementation.

An explicit acknowledgement attribute on the function can suppress the warning without adding policy inheritance.
The spelling and the interaction with globally restrictive compilation options remain to be selected.
The warning must not appear or disappear merely because ordinary inlining succeeds.

### Inferred Restrictions on Local Variables

A second optional diagnostic can identify a local declaration without an explicit modifier when the reference analysis infers a more restrictive place policy.
Its purpose is to make indirect restrictions visible at declaration granularity.
For example, it could explain that `product` in the first example is constrained because its value contributes to `sum`.

The compiler needs an explicit correspondence between the declared local and the analyzed place to emit that diagnostic reliably.
It must not reconstruct storage identity from source locations after SSA conversion.
A future front-end analysis could provide better coverage; a backend implementation needs preserved declaration identity and provenance.

We propose that an acknowledgement attribute on a local declaration, if introduced, suppress only this diagnostic.
It must not relax the local's effective policy or stop a demand from a precise consumer.
A modifier that stops backward propagation would weaken the guarantee for the eventual precise output and is not proposed here.
This distinction avoids suggesting that a local spelling can override the contract requested for its eventual output.

## Compiler Integration

### Representation Before Policy Resolution

The front end checks the applicability and compatibility of policy-inheritance attributes and records declared policies.
AST-to-IR lowering represents attributed functions as ordinary `IRFunc` instructions with additional policy-contract metadata.
It does not encode the implicit policy parameters as ordinary Slang generic parameters.

The compiler also needs to preserve explicit policy requests, the identity of relevant storage declarations, and the original function boundaries.
It must preserve which expression operands receive a demand.
In particular, converting a conditional expression to an eager selection instruction, or the reverse, must not change whether its predicate receives a demand.
The producer must record that distinction before lowering erases it; source locations are not a substitute for semantic provenance.
A proposed `makePrecise(value)` instruction records a demand without changing the value.
For the general policy model, the operation needs an associated policy operand or an equivalent representation.
Assignments through fields, arrays, swizzles, and output parameters must preserve the same declared-place information as direct assignments.

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
| Local policy inference | With a function's policy arguments fixed, solve its local constraints to a fixed point. Record settled policy arguments at calls without consulting the bodies of called functions. |
| Policy specialization | Clone ordinary specialized `IRFunc` bodies as needed for canonical policy-argument tuples and analyze those versions locally. Reuse a version only when its original function and complete policy tuple match. |
| Constrained operations | Replace resolved demands with policy attributes on the affected operations and preserve requirements on later intrinsic expansions. No unresolved demand may reach an unaware arithmetic optimization. |
| Performance optimization and target lowering | Respect operation attributes together with the separately stored compilation-option policy. Preserve those contracts through inlining, scalarization, intrinsic expansion, and legalization. |
| Emission | Map constrained operations and global options to supported target mechanisms; diagnose unsupported guarantees. |

Policy specialization is its own transformation after ordinary generic specialization.
It may use an ad hoc cache and work queue for specialized function copies.
The local-inference and policy-specialization rows form one work-queue process, rather than two single whole-program sweeps.
The process starts from reachable functions without implicit policy parameters and from entry points with fixed policy arguments.
An inherited policy parameter on an entry point receives `U` because there is no Slang caller to supply an output demand; explicit restrictions on its outputs still apply.
Serialized Slang modules retain policy contracts and bodies for specialization when linked into an output program.
Analyzing a version settles its local policies, records its callee policy tuples, and schedules any versions not yet analyzed.
Each new version runs the same local inference with its own fixed policy arguments.
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

The initial regression suite should verify both required constraints and deliberate boundaries.
SPIR-V checks should associate `NoContraction` with the relevant instructions, rather than count decorations across unrelated arithmetic.
Generated HLSL/GLSL and IR-level checks are also needed to expose losses before downstream compilation.

| Area | Representative coverage |
| --- | --- |
| Local expressions | Initializers, reassignment, compound updates, phi values, loops, logical/bitwise expressions, and demand propagation through casts and bit reinterpretation. |
| Places | Qualified fields, whole-aggregate initialization/copy/return, qualified aggregates, array reads and writes, dynamic indices, vector components, swizzled assignments, and potentially aliasing indirect accesses. |
| Selectivity | Independent unrestricted arithmetic remains unmarked; a precise read does not constrain later consumers; overwritten assignments exercise conservative inference and optional refinement. |
| Function boundaries | Caller argument arithmetic is constrained while an ordinary callee remains opaque, with and without inlining; lambdas and locally declared methods retain independent scopes. |
| Outputs and receivers | Returns, `out`, `inout`, incoming stored values through references, projected read/write actuals, precise contained output fields, implicit receivers, multiple outputs, and an unused result. |
| Policy-specialized calls | Default and precise calls to the same helper, nested attributed calls, explicit precise locals in a default version, and reuse independent of call order. |
| Interfaces | Matching and missing contracts, generic requirements, alternative overloads, genuine default bodies, and rejection through forwarding synthesis. |
| Numeric compatibility | Strict `slang.numerics` and standard core conformances; only enumerated legacy user conformances receive the documented exception. |
| Diagnostics | Boundary warnings and suppressions, inferred-local diagnostics where provenance is available, stable reporting across inlining, and no semantic relaxation from acknowledgement. |
| Target contracts | Direct SPIR-V, generated HLSL/DXIL and GLSL, global-option interaction, unsupported-target diagnostics, and intrinsic consistency cases. |

## Alternatives Considered

### Propagation Through Every Function

Unrestricted interprocedural propagation resembles behavior developers observe after DXC inlining.
It would also make existing helpers inherit restrictions without annotations.
It requires broader specialization or analysis and makes it harder to express an intentional unrestricted subcomputation.
Explicit output-policy parameterization exposes the choice in the function's contract.

### Giving Input Parameters Caller-Side Policies

A future extension could make `precise` on an input parameter constrain the corresponding actual expression.
That would support wrappers intended to impose a demand on their callers.
It differs from GLSL's input-formal rule and from the output-policy parameterization proposed here.
We defer it rather than infer caller obligations from arbitrary precise locals in callees.

### Distinct Meanings by Input Dialect

Slang could assign HLSL inputs the broader HLSL numerical contract and GLSL inputs the narrower GLSL one.
We instead propose one minimum restriction with obvious target equivalents.
Stronger numerical environments would use separately specified controls.

### A Qualified Numeric Type

A type wrapper could make explicit declarations and projections easier to retain.
Ordinary forward type propagation does not express the required backward demands through unqualified intermediates.
It also does not independently resolve ordinary call boundaries or per-output specialization.
The policy model therefore describes storage and computations directly.

### Restricting Every Operation in a Function or Program

A blanket restriction can avoid some missed demands and is a useful explicit compilation option.
Applying it implicitly because one local is precise would unnecessarily affect unrelated arithmetic.
It also prevents programmers from identifying which computations the language actually requires to be constrained.

### Automatic Forwarding Adapters for Strict Requirements

An attributed forwarding method cannot establish a contract merely by calling an unannotated method.
Validated adapters may be possible, but the initial strict matching rule keeps the required behavior inspectable.
The legacy-core exception is temporary compatibility behavior with an explicitly weaker guarantee.

## Decisions Remaining for Design Review

The following decisions remain open without changing the central model:

1. Final spellings for function-level inheritance, per-output inheritance, and diagnostic acknowledgements, and whether independent outputs are exposed initially.
2. The complete `mad`/`fma` contracts, the reduction order promised by precise `dot`/`mul`, and consistency through changes in operand representation.
3. The exact legacy core numeric requirement list and the semantic representation of standard-provided conformance ownership.
4. Which declaration-based diagnostics can be supported reliably by the initial IR phase, and whether a shared front-end analysis is practical.
5. The callable representation and supported initial boundary for policy-parametric function values and genuinely open runtime dispatch.

Implementing GLSL `invariant`, exporting input-policy demands, admitting validated forwarding adapters, and defining stronger floating-point environments are future work.
