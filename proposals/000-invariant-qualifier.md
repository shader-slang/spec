SP #000: `invariant` Qualifier for Position Outputs
=================

We propose an `invariant` qualifier that marks a shader's position output as invariant: two shaders that compute the position from the same source expressions and the same inputs must produce bit-identical results, even when they are compiled as different pipelines.

This is what makes multi-pass rendering with an equality depth test work, for example a depth prepass followed by a color pass that tests with `EQUAL`. Every major graphics API has a way to ask for it, but Slang does not.

Status
------

Status: Design Review

Implementation: [shader-slang/slang#14389](https://github.com/shader-slang/slang/pull/14389)

Author: Oyintare Ebelo

Reviewer:

Background
----------

A depth prepass draws a mesh twice with different vertex shaders:

```hlsl
struct DepthOut { float4 pos : SV_Position; };
struct ColorOut { float4 pos : SV_Position; float2 uv : TEXCOORD0; float3 normal : NORMAL; };
```

Both compute `pos` with the same math, but the driver compiles them as separate programs. It may contract `a * b + c` into a fused multiply-add in one and not the other, or reorder operations differently, because each program's surrounding code differs. The positions then differ in the last bits, and an `EQUAL` or `GREATER_OR_EQUAL` depth test fails in streaks along triangle edges.

Slang cannot express the fix today:

- `invariant` is a parse error, and `[vk::invariant]` is an unknown attribute.
- `precise` is the closest existing feature, and on D3D it is the mechanism for this problem (see Related Work). But Slang's `precise` only reaches some arithmetic, inconsistently across targets ([shader-slang/slang#13324](https://github.com/shader-slang/slang/issues/13324)), and on SPIR-V it becomes `NoContraction` on individual instructions, never `Invariant` on the output.
- The only workaround is to patch the compiled SPIR-V to add the decoration, which does not help the other targets.

Related Work
------------

| Language / IR | Spelling | Where it is allowed | Guarantee |
| --- | --- | --- | --- |
| SPIR-V | `OpDecorate %var Invariant` | Any variable or block member. Vulkan allows it on `Output` and `Input`, and it has no effect on `Input`. | "expressions computing its value be computed invariantly with respect to other shaders computing the same expressions" (SPIR-V specification, `Invariant` decoration). |
| GLSL | `invariant gl_Position;` or `invariant out vec4 v;` | Any output, by declaration or redeclaration. `#pragma STDGL invariant(all)` marks every output. | GLSL 4.60 §4.8.1, with conditions on expressions, operand order, types, precision, texture state and control flow. |
| MSL | `[[invariant]]` | Vertex position output, and the position in mesh vertex attributes. Metal 2.1 and later. | Needs `MTLCompileOptions.preserveInvariance` (`-fpreserve-invariance`), which the MSL spec describes for vertex shaders: "If not set, [[invariant]] is ignored." |
| WGSL | `@invariant` | The `position` builtin. | Same position across programs and across invocations of the same entry point. The spec notes it "maps to the precise qualifier in HLSL, and the invariant qualifier in GLSL". |
| HLSL | `precise` on an output | A struct field, `out` parameter or return value. | Microsoft's docs say `precise` on an output "maintains result invariance for the modified output variable", for example to "match depth values over multiple passes". |

SPIRV-Cross and Tint both translate an invariant position to `precise` when they emit HLSL. The WebGPU group discussed the mapping in [gpuweb/gpuweb#893](https://github.com/gpuweb/gpuweb/issues/893), and Tint's HLSL writer notes that `precise` "is stricter and therefore provides the necessary guarantees".

Proposed Approach
-----------------

Add an `invariant` modifier for the position output of an entry point. A position output is a struct field, an `out` parameter or a function's return value with the `SV_Position` semantic.

```hlsl
struct VSOut
{
    invariant float4 pos : SV_Position;
    float2 uv : TEXCOORD0;
};

void vsMain(float3 p : POSITION, out invariant float4 pos : SV_Position) { ... }

invariant float4 vsReturn(float3 p : POSITION) : SV_Position { ... }
```

Two entry points that compute an `invariant` position the same way get bit-identical positions, however the rest of each program differs. The exact rule is under [Semantics](#semantics). Slang only emits the qualifier where it can keep that promise, and warns where it cannot.

| Target | Output |
| --- | --- |
| SPIR-V | `OpDecorate %gl_Position Invariant` |
| GLSL | `invariant gl_Position;`, or `invariant` on the `gl_Position` member of a mesh shader's output block |
| Metal | `[[position, invariant]]`, plus `-fpreserve-invariance` when Slang compiles the metallib |
| WGSL | `@invariant @builtin(position)` |
| HLSL | Qualifier dropped, with warning E56116, until `precise` is reliable (see [HLSL](#hlsl)) |

Detailed Explanation
--------------------

### Semantics

Take two entry points, A and B, each with an `invariant` position output. They may be in different modules, compiled separately and linked into different pipelines. For a given invocation, if:

1. the position is computed by the same source expressions in A and B, with the same operand order, types and precision,
2. every value those expressions read is the same: varying inputs, uniforms, constants, and texture and sampler state for any texture reads,
3. the control flow that decides which of those expressions run takes the same path,
4. A and B are compiled for the same target with the same floating-point options (`-fp-mode`, denormal modes),

then A and B write bit-identical positions. Everything else in A and B, including other outputs and code that does not feed the position, may differ. The same holds between two invocations of one entry point.

This is a promise about agreement, not accuracy. The position may still be computed with contraction or reassociation, as long as A and B get the same result.

For Slang this means two things:

- Slang's own passes (inlining, specialization, constant folding, CSE and dead code elimination) must turn the same source data flow for the position into the same emitted data flow, whatever code surrounds it.
- The emitted program must carry the target's invariance qualifier, so the downstream compiler and driver keep the guarantee from there.

Not covered:

- Different targets, devices or drivers.
- Different specializations. If generic arguments, specialization constants or preprocessor branches change the computation itself, condition 1 does not hold.
- Outputs other than the position.

### Where `invariant` is allowed

- On a struct field, a parameter, or a function (for its return value), with the `SV_Position` semantic. Anything else, including a global or a local with that semantic, is an error (E31233).
- Not on inputs. A parameter without `out` is an error (E31234).
- `invariant` stays usable as an identifier. It is only a keyword in modifier position, the same as `precise`.

### Stages

| Stage | SPIR-V, GLSL | Metal | WGSL | HLSL |
| --- | --- | --- | --- | --- |
| Vertex | Kept | Kept | Kept | Warning |
| Mesh | Kept | Emitted, see [Questions](#questions) | Stage not supported | Warning |
| Geometry, domain | Kept | Stage not supported | Stage not supported | Warning |

On WGSL, `out` parameters currently produce invalid output whether or not they are `invariant` (an existing issue). Struct fields and return values work.

### Structs shared between stages

A common pattern shares one struct between the vertex output and the fragment input:

```hlsl
struct VSOut { invariant float4 pos : SV_Position; float2 uv : TEXCOORD0; };

VSOut vsMain(...) { ... }
float4 psMain(VSOut input) : SV_Target { ... }
```

Rejecting `invariant` on the struct field would rule out this pattern, so the field is allowed and the qualifier applies only where the struct is an output. Fragment inputs get no qualifier on any target, and the HLSL warning does not fire for them. This matters on Metal, where `[[invariant]]` on a fragment input is a compile error.

### HLSL

`precise` on an output is D3D's invariance mechanism, so the natural lowering is `invariant` to `precise`. This proposal does not lower it yet, because Slang's `precise` does not reliably reach the arithmetic it should:

- On HLSL, GLSL and Metal, `precise` on a struct field is dropped.
- On SPIR-V it becomes `NoContraction` on some instructions and not others, depending on how the value is computed.

Emitting `precise` today would tell users the guarantee holds when it may not. Until `precise` is fixed ([shader-slang/slang#13324](https://github.com/shader-slang/slang/issues/13324)), Slang drops `invariant` on HLSL and warns (E56116) for each entry point with an invariant output. Once `precise` is reliable, `invariant` should lower to it on HLSL and the warning should go away.

### Relation to `precise`

`invariant` and `precise` are independent, and either can be used without the other.

- `precise` constrains how one program evaluates the arithmetic that feeds a value: no contraction, no reordering, IEEE rules for NaN and infinity.
- `invariant` constrains programs to agree on one output. It does not say how the result is computed.

On D3D, `precise` is used to get invariance because forbidding those optimizations makes the result deterministic. Other targets have a dedicated qualifier, so Slang keeps the two concepts separate and maps them per target. Using both on one output is allowed.

### Metal `preserveInvariance`

Metal only honors `[[invariant]]` when the library is compiled with `preserveInvariance`. When Slang compiles the metallib itself, it passes `-fpreserve-invariance`, but only when the shader uses `invariant`, because Apple describes the option as compiling vertex shaders conservatively. When an application compiles Slang's Metal source itself, it is responsible for setting the option, which the Metal target documentation says.

Alternatives Considered
-----------------------

### `[vk::invariant]` attribute

A Vulkan-only attribute would follow existing `vk::` attributes, but the concept exists on GLSL, Metal, WGSL and (through `precise`) HLSL. A target-specific spelling would leave those out.

### Reusing `precise`

Making `precise` on a position output also emit `Invariant` would need no new keyword, and it matches what `precise` means on D3D. But it would change existing SPIR-V, GLSL and Metal output for code that uses `precise` only for numerical behavior, and it would tie invariance to a feature that does not work reliably today.

### Allowing `invariant` on any output

GLSL and SPIR-V allow invariance on any output. Metal and WGSL only allow it on the position, so this proposal starts there and leaves other outputs to [Future Directions](#outputs-other-than-the-position).

### A module-wide switch

An equivalent of GLSL's `#pragma STDGL invariant(all)` or a compiler option would be simpler to adopt, but would mark every output, including ones Metal and WGSL cannot mark. A per-declaration qualifier says exactly which output needs the guarantee.

Future Directions
-----------------

### Outputs other than the position

Some techniques need other outputs to agree across passes. `SV_ClipDistance` is the clearest case: it decides which pixels are drawn, so a mismatch between a prepass and a later pass causes the same artifacts as a mismatched position. A later proposal could allow `invariant` on any output, emit it where the target supports it, and warn where it cannot keep the guarantee for that output. That only lifts an error, so it would not break code written against this proposal.

### Lowering to `precise` on HLSL

Once `precise` is fixed, lower `invariant` to `precise` on HLSL, as SPIRV-Cross and Tint do, and remove the warning.

Questions
---------

- **Metal mesh shaders.** The MSL spec lists `invariant` for mesh vertex attributes, but describes `-fpreserve-invariance` only for vertex shaders. Is the guarantee kept for mesh shaders, or should Slang warn there?
- **GLSL input.** Slang's GLSL compatibility mode does not accept `invariant gl_Position;` or `invariant out` declarations yet. Should this proposal cover them, including `#pragma STDGL invariant(all)`, or leave them to a follow-up?
- **Reflection.** An application that compiles Slang's Metal source itself has to know to set `preserveInvariance`. Should Slang report through reflection that an entry point uses `invariant`?
- **HLSL timing.** Should the `precise` lowering on HLSL wait for #13324, or land as an opt-in sooner?
