SP #042: Pipeline Ray Tracing API Structural Dispatch
=====================================================

Status
------

Status: Draft Proposal.

Author:

Reviewer:

Scope
-----

Scope: pipeline ray tracing only. Inline ray tracing and ray queries are intentionally out of
scope for this first design.

This proposal sketches a new Slang ray tracing API that treats Metal as a first-class target
while preserving the D3D and Vulkan pipeline model. The central idea is to make the shader source
declare a conceptual shader binding table, or SBT, as structured Slang types. D3D and Vulkan can
continue to use the native host-created SBT. Metal can use the same structure to synthesize the
post-trace closest-hit and miss dispatch logic that Metal programmers normally write by hand.

Catalog
-------

- [1. Challenges Extending Current Slang Ray Tracing To Metal](#1-challenges-extending-current-slang-ray-tracing-to-metal)
  - [1.1 Dispatch Model Gap](#11-dispatch-model-gap)
  - [1.2 Metal Function Table And Function Buffer Resource Mismatch](#12-metal-function-table-and-function-buffer-resource-mismatch)
  - [1.3 Metal Tag List And Reachability](#13-metal-tag-list-and-reachability)
  - [1.4 Reserved Challenges](#14-reserved-challenges)
- [2. Proposed API Sketch](#2-proposed-api-sketch)
  - [2.1 Overview](#21-overview)
  - [2.2 Detailed Component Descriptions](#22-detailed-component-descriptions)
    - [2.2.1 Resolving The Dispatch Model Gap With A Conceptual SBT](#221-resolving-the-dispatch-model-gap-with-a-conceptual-sbt)
    - [2.2.2 Resolving The Metal Function Table And Function Buffer Resource Mismatch With TraceProgramDescriptor](#222-resolving-the-metal-function-table-and-function-buffer-resource-mismatch-with-traceprogramdescriptor)
    - [2.2.3 Resolving The Metal Tag-List Issue With Context Types](#223-resolving-the-metal-tag-list-issue-with-context-types)
  - [2.3 Writing Stages As Interface-Conforming Types](#23-writing-stages-as-interface-conforming-types)
- [3. Migration Examples](#3-migration-examples)
  - [3.1 Migrating Existing Metal Code To The New API](#31-migrating-existing-metal-code-to-the-new-api)
  - [3.2 Migrating Existing Slang D3D/Vulkan Ray Tracing Code](#32-migrating-existing-slang-d3dvulkan-ray-tracing-code)
  - [3.3 Host Reflection Patterns](#33-host-reflection-patterns)
- [4. Open Design Questions](#4-open-design-questions)

## 1. Challenges Extending Current Slang Ray Tracing To Metal

### 1.1 Dispatch Model Gap

D3D and Vulkan expose ray tracing as a pipeline-stage model. A trace call enters traversal, and
the driver or hardware uses host-created SBT records to select miss, any-hit, intersection, and
closest-hit shaders. The closest-hit function is not directly called from ray-generation source.

Metal exposes a different model. `intersector.intersect(...)` returns an `intersection_result`.
AnyHit and custom Intersection behavior can still be dispatched during traversal through Metal's
function table or function buffer, but Miss and ClosestHit are ordinary post-trace shader logic
written by the user.

Figure 1 shows the key mismatch: D3D/Vulkan assign stage dispatch to the host SBT and the
driver/hardware, while Metal assigns Miss and ClosestHit dispatch to shader code after
`intersect(...)` returns. A portable Slang API needs enough structure to synthesize that Metal
post-trace dispatch without changing the native D3D/Vulkan model.

<a id="fig-dispatch-model-gap"></a>
![D3D and Vulkan SBT dispatch compared with Metal user-specified post-trace miss and closest-hit dispatch](figures/042-ray-tracing-api/dispatch-model-gap.svg)

*Figure 1. Dispatch model gap: D3D and Vulkan select pipeline stages through host-created SBT records, while Metal requires user-written post-trace dispatch for Miss and ClosestHit.*

### 1.2 Metal Function Table And Function Buffer Resource Mismatch

Metal introduces `intersection_function_table` and `intersection_function_buffer` resource types
that are visible to shader code and must be bound from host code when traversal needs custom
intersection behavior. This is different from the D3D/Vulkan SBT model. The SBT is built by host
code, but it is not a shader-visible resource and shader code does not declare a binding point for
it.

This creates an asymmetric programming model. Metal shader code may need a parameter that
represents a function table or function buffer. D3D/Vulkan shader code has no corresponding
parameter, even though host code still needs to build SBT records. A portable Slang API therefore
needs a way to describe this logical binding without forcing D3D/Vulkan targets to expose a fake
shader resource.

### 1.3 Metal Tag List And Reachability

This proposal uses the term **reachability** to describe the shader binding table entries that a
single trace call can access. The trace call supplies dispatch parameters, traversal contributes
geometry and instance information, and the target selects one of the SBT records. Those selectable
records are the entries reachable from that trace call.

In existing D3D/Vulkan-style ray tracing models, this reachability is determined by host-created
binding data. The shader source contains the trace call, but the SBT records and the binding edges
from those records to AnyHit, Intersection, ClosestHit, and Miss shaders are provided by host code.
Therefore, as shown in Figure 2, the complete reachability set is not known from shader source at
ordinary compile time.

<a id="fig-reachability-definition"></a>
![Reachability is the set of SBT entries that one trace call can select](figures/042-ray-tracing-api/reachability-definition.svg)

*Figure 2. Reachability definition: the reachable entries are the SBT records one trace call can select at runtime, but in the existing model that set is determined by host-created binding data.*

Metal adds a second constraint: each custom intersection function reachable from an intersector
must have a compatible `[[intersection(...)]]` tag list. Native Metal can validate a mismatch at
pipeline build time because the user writes both the intersector tags and the function tags in
source. Figure 3 shows why this works: pipeline build sees the intersector tags, function tags,
and host bindings together.

<a id="fig-native-metal-tag-validation"></a>
![Native Metal can validate explicit intersector and custom intersection function tags at pipeline build time](figures/042-ray-tracing-api/native-metal-tag-validation.svg)

*Figure 3. Native Metal tag validation: the user-authored tag lists give pipeline build enough information to reject incompatible host bindings.*

Slang does not currently expose that Metal tag system. When lowering AnyHit or Intersection entry
points to Metal, Slang must synthesize `[[intersection(...)]]` tags for the generated Metal
functions. The compiler can see trace sites and stage entry points, but in the existing model it
cannot see the host binding edges that determine which stage entries are reachable from each trace
site.

Figure 4 shows the information-flow problem. If two trace sites lower to different Metal tag
sets, and several AnyHit or Intersection entries may be bound by the host, the compiler cannot
know whether a generated function needs tag set A, tag set B, or another tag set. Emitting no tag,
or emitting a tag inferred from the wrong trace site, can make the generated Metal pipeline fail
to build.

<a id="fig-slang-tag-synthesis-gap"></a>
![Slang cannot synthesize Metal intersection tags when host binding data owns reachability](figures/042-ray-tracing-api/slang-tag-synthesis-gap.svg)

*Figure 4. Slang tag synthesis gap: Slang must emit Metal `[[intersection(...)]]` tags before host binding data reveals which AnyHit or Intersection entries are reachable from each trace site.*

### 1.4 Reserved Challenges

Other details remain important, but they are not the main shape of this proposal:

- Metal has limitations on custom attributes returned from custom intersection functions.
- Metal has multiple `intersect(...)` overload families, including no-dispatch, function-table,
  and function-buffer forms.
- Device user data should be modeled in a way that maps to non-pointer targets.

Those issues can be handled after the dispatch and tag-reachability model is settled.

## 2. Proposed API Sketch

### 2.1 Overview

The proposed API asks shader authors to describe a trace program in source:

1. Define payload and context types.
2. Write miss, closest-hit, any-hit, and intersection logic as structs that implement Slang
   interfaces.
3. Group those stage structs into ordered hit, miss, and callable group lists.
4. Use `rt::RayTracer<ProgramLayout>`, `rt::RayTraversalDesc`, and
   `rt::TraceProgramDescriptor<ProgramLayout>` from ray-generation code.

The group declarations are the source-level conceptual SBT. They are visible to the compiler and
to reflection. Host code can query `ITraceProgramLayout` reflection to build D3D/Vulkan SBT
records or Metal function tables/function buffers from the same grouping contract, so the grouping
logic does not need to be duplicated outside shader source. Figure 5 gives a high-level view of
this API shape.

<a id="fig-api-overview"></a>
![API overview](figures/042-ray-tracing-api/api-overview.svg)

*Figure 5. Proposed API overview: users define contexts, stage structs, and grouped dispatch metadata in an `ITraceProgramLayout`; host code uses reflection of that same program layout to build D3D/Vulkan SBT records and Metal function tables/function buffers.*

The running example uses the same prototype files listed above. The older structural-dispatch
sketches in this directory are retained as design history and are not the source shape described
by this proposal.

### 2.2 Detailed Component Descriptions

#### 2.2.1 Resolving The Dispatch Model Gap With A Conceptual SBT

The dispatch solution is to declare the SBT structure in shader source. At this layer, the key
concepts are ordered groups, group lists, a trace program layout, a descriptor, and traversal
parameters. A slot is the zero-based position of a group in its corresponding list.

Simplified API shape:

```slang
namespace rt
{
    public struct RayTraversalDesc
    {
        public RayDesc ray;
        public uint instanceMask;
        public uint sbtOffset;
        public uint sbtStride;
        public uint missIndex;
    }

    public interface IHitGroup
    {
        associatedtype Context : IHitGroupContext;
        associatedtype ClosestHit : IClosestHitShader<Context>;
        associatedtype AnyHit : IAnyHitShader<Context>;
        associatedtype IntersectionAttributes;
        associatedtype Intersection : IIntersectionShader<Context, IntersectionAttributes>;
    }

    public interface IMissGroup
    {
        associatedtype Context : IMissGroupContext;
        associatedtype Miss : IMissShader<Context>;
    }

    public interface ICallableGroup { ... }

    public struct HitGroupList<TraceContext, each HitGroup> { ... }
    public struct MissGroupList<TraceContext, each MissGroup> { ... }
    public struct CallableGroupList<TraceContext, each CallableGroup> { ... }

    public interface ITraceProgramLayout
    {
        associatedtype TraceContext : ITraceContext;
        associatedtype MissGroups : IMissGroupList<TraceContext>;
        associatedtype HitGroups : IHitGroupList<TraceContext>;
        associatedtype CallableGroups : ICallableGroupList<TraceContext>;
    }

    public struct TraceProgramDescriptor<ProgramLayout>
        where ProgramLayout : ITraceProgramLayout
    {}

    public struct RayTracer<ProgramLayout>
        where ProgramLayout : ITraceProgramLayout
    {
        public void trace(
            RayTraversalDesc desc,
            AccelerationStructure<
                ProgramLayout.TraceContext.ASKind,
                ProgramLayout.TraceContext.Motion> scene,
            TraceProgramDescriptor<ProgramLayout> descriptor,
            inout ProgramLayout.TraceContext.Payload payload);
    }
}
```

This simplified shape omits some details, but keeps the current naming and ownership model:
`ITraceProgramLayout` is the schema, `TraceProgramDescriptor<ProgramLayout>` is the value-level
descriptor, and `RayTraversalDesc` carries per-trace SBT-style indices.

The compiler-synthesized closest-hit slot calculation still follows the D3D/Vulkan SBT
calculation. This is not a user-facing API; it is shown only as the conceptual formula Slang will
generate for Metal:

```slang
slot = instanceContribution + geometryContribution * desc.sbtStride + desc.sbtOffset;
```

For D3D and Vulkan, these fields are mostly descriptive:

- `RayTraversalDesc.sbtOffset` maps to D3D `RayContributionToHitGroupIndex` and Vulkan
  `sbtRecordOffset`.
- `RayTraversalDesc.sbtStride` maps to D3D `MultiplierForGeometryContributionToHitGroupIndex` and
  Vulkan `sbtRecordStride`.
- `RayTraversalDesc.missIndex` maps to the native miss shader index.
- The native driver or hardware still performs the SBT lookup.

For Metal, this API becomes executable structure:

- Slang lowers `RayTracer<ProgramLayout>.trace(...)` to `intersector.intersect(...)`.
- Slang uses `RayTraversalDesc.missIndex` to synthesize miss dispatch.
- Slang synthesizes the internal hit-group slot calculation to dispatch closest-hit.
- Slang uses the same hit-group list slots to validate and emit Metal function-table or
  function-buffer entries for any-hit and custom intersection functions.

Conceptual Metal lowering:

```slang
let result = metalIntersector.intersect(desc.ray, scene, descriptor, payload);

if (!result.isNone)
{
    uint geometryContribution = __rtGetGeometryContribution<ProgramLayout>(result);
    uint instanceContribution = __rtGetInstanceContribution<ProgramLayout>(result);
    uint slot = instanceContribution + geometryContribution * desc.sbtStride + desc.sbtOffset;

    switch (slot)
    {
    case 0:
        PrimaryTriangleClosestHit().invoke(makeClosestHitInput(...));
        break;
    case 1:
        PrimaryCurveClosestHit().invoke(makeClosestHitInput(...));
        break;
    case 2:
        PrimarySphereClosestHit().invoke(makeClosestHitInput(...));
        break;
    }
}
```

The important property is that Metal closest-hit dispatch is not invented independently. It is
generated from the same conceptual SBT slots that the host uses for D3D and Vulkan.

Alternative considered: require users to write a structural Metal-like dispatch function.

```slang
struct PrimaryClosestHitDispatcher
{
    void invoke(rt::ClosestHitInput<PrimaryTraceContext> input)
    {
        switch (input.geometryIndex)
        {
        case 0: shadeOpaqueTriangle(input); break;
        case 1: shadeCurve(input); break;
        case 2: shadeSphere(input); break;
        }
    }
}
```

Slang could analyze this user-written dispatch logic and reflect enough metadata for D3D/Vulkan
host code to reconstruct the SBT. This is closer to the normal Metal mental model, but it is a
harder compiler problem:

- The compiler must recognize and preserve the user's dispatch structure.
- Reflection depends on successful control-flow analysis.
- Dynamic dispatch tables, buffer lookups, and helper functions complicate extraction.
- Small shader-code changes could affect host reflection in surprising ways.

The proposed design chooses the reverse direction: users declare the SBT structure directly, then
Slang synthesizes Metal dispatch. This is simpler to validate and easier to reflect.

#### 2.2.2 Resolving The Metal Function Table And Function Buffer Resource Mismatch With TraceProgramDescriptor

Metal introduces `intersection_function_table` and `intersection_function_buffer` as resource
types that can be visible to shader code and bound from host code. D3D and Vulkan instead use an
SBT. The SBT is also built by host code, but it is not a shader-visible resource, so shader code
does not declare an SBT binding point.

Before defining the Slang abstraction, it is useful to review the structure of these target
objects. Metal's `intersection_function_table` is a host-bound resource-object table containing
custom intersection function entries and resource bindings visible to those functions. Metal's
`intersection_function_buffer` is the buffer form of the same candidate-hit dispatch idea. In the
function-buffer path, the useful mental model is a pair of physical inputs:

- a function-buffer table indexed by traversal, where each selected entry names one custom
  intersection function;
- a user-data buffer that can carry records, generated slot maps, bindless resources, and callable
  visible-function-table values.

This section focuses on the `intersection_function_buffer_arguments` path because it is the more
general form for the proposed portable abstraction. Metal's `intersection_function_table` is a
special-case resource type relative to `intersection_function_buffer_arguments`; it follows the
same candidate-hit dispatch idea, and support for it can be added as a restricted lowering path
without changing the core `TraceProgramDescriptor<ProgramLayout>` model.

D3D and Vulkan do not expose an equivalent shader-visible function table or function buffer.
Their comparable structure is the host-created SBT. It is useful to view the SBT as one
host-side database with separate hit-group, miss, and callable sections. A hit-group record can
name ClosestHit, AnyHit, and Intersection shaders together, while the miss and callable sections
are one-dimensional lists.

Figure 6 compares the two binding models. The Metal panel shows a shader-visible function buffer
and user-data buffer. The D3D/Vulkan panel shows the SBT as one host-side object with hit-group,
miss, and callable sections.

<a id="fig-binding-resource-comparison"></a>
![Metal function buffer compared with D3D and Vulkan shader binding table](figures/042-ray-tracing-api/binding-resource-comparison.svg)

*Figure 6. Binding resource comparison: (a) Metal uses a shader-visible function buffer plus user data; (b) D3D/Vulkan use one host-side SBT object with hit-group, miss, and callable sections, and no shader binding point.*

The previous subsection already makes the two sides share the same conceptual layout: the shader
source declares a `ProgramLayout`, and host code can reflect that layout to build the target-side
records. The remaining mismatch is purely about binding. Metal needs a shader-visible resource
for the function table or function buffer path, while D3D/Vulkan need no corresponding shader
parameter.

The proposed answer is to introduce an opaque resource type:

```slang
struct TraceProgramDescriptor<ProgramLayout>
    where ProgramLayout : ITraceProgramLayout
{
}
```

`TraceProgramDescriptor<ProgramLayout>` is described by `ProgramLayout`, but it does not itself
declare the trace context. Its job is to represent the target-specific descriptor object derived from
the reflected program layout.

On Metal, `TraceProgramDescriptor<ProgramLayout>` lowers to the physical resources needed by the
selected Metal traversal path. For the general function-buffer path, that means a function buffer
plus generated user data, matching the Metal panel in Figure 6. Host code binds those physical Metal
resources to the opaque Slang descriptor and uses reflection of `ProgramLayout` to populate the
custom intersection functions, record data, generated slot maps, bindless resources, and callable
visible-function-table values.

On D3D and Vulkan, `TraceProgramDescriptor<ProgramLayout>` does not need to lower to a shader-visible
resource. The native SBT remains a host-side object, as shown in the D3D/Vulkan panel in Figure 6.
Host code still uses the same `ProgramLayout` reflection to build hit-group, miss, and callable
SBT records, but shader code does not receive a Metal-style function-table or function-buffer
object.

#### 2.2.3 Resolving The Metal Tag-List Issue With Context Types

With the descriptor abstraction separated, the tag-list issue still needs a way to answer: "which
trace object, hit shader, and intersection function share the same semantic requirements?" The
proposed answer is a context type. A trace context defines the properties of a trace family:

```slang
interface ITraceContext
{
    associatedtype Payload;
    associatedtype ASKind;
    associatedtype Motion;
    static const RayDataTags dataTags;
    static const int maxLevels;
}
```

A hit group context can specialize the trace context with a primitive kind and a record type:

```slang
interface IHitGroupContext
{
    associatedtype TraceContext : ITraceContext;
    associatedtype Primitive : IIntersectionPrimitive;
    associatedtype Record;
}
```

A trace program layout connects the ray tracer and every grouped shader through the same trace
context:

```slang
struct PrimaryTraceContext : rt::ITraceContext
{
    typealias Payload = RadiancePayload;
    typealias ASKind = rt::InstanceAS;
    typealias Motion = rt::NoMotion;
    static const rt::RayDataTags dataTags = rt::RayDataTags::Triangle;
    static const int maxLevels = 0;
}

struct PrimaryTriangleContext : rt::IHitGroupContext
{
    typealias TraceContext = PrimaryTraceContext;
    typealias Primitive = rt::TrianglePrimitive;
    typealias Record = PrimaryHitRecord;
}

struct PrimaryMissContext : rt::IMissGroupContext
{
    typealias TraceContext = PrimaryTraceContext;
    typealias Record = PrimaryMissRecord;
}

struct PrimaryMissGroup : rt::IMissGroup
{
    typealias Context = PrimaryMissContext;
    typealias Miss = PrimaryMiss;
}

struct PrimaryTriangleGroup : rt::IHitGroup
{
    typealias Context = PrimaryTriangleContext;
    typealias ClosestHit = PrimaryTriangleClosestHit;
    typealias AnyHit = PrimaryTriangleAnyHit;
    typealias IntersectionAttributes = rt::NoAttributes;
    typealias Intersection = rt::NoIntersection<PrimaryTriangleContext>;
}

struct PrimaryTraceProgramLayout : rt::ITraceProgramLayout
{
    typealias TraceContext = PrimaryTraceContext;

    typealias MissGroups = rt::MissGroupList<
        TraceContext,
        PrimaryMissGroup>;

    typealias HitGroups = rt::HitGroupList<
        TraceContext,
        PrimaryTriangleGroup>;

    typealias CallableGroups = rt::NoCallableGroups<TraceContext>;
}

rt::TraceProgramDescriptor<PrimaryTraceProgramLayout> gPrimaryDescriptor;

[shader("raygeneration")]
void rayGen()
{
    RadiancePayload payload;
    rt::RayTracer<PrimaryTraceProgramLayout> tracer;
    tracer.trace(desc, scene, gPrimaryDescriptor, payload);
}
```

This gives the compiler a source-level relationship:

- `RayTracer<PrimaryTraceProgramLayout>` identifies one `ITraceProgramLayout`.
- `PrimaryTraceProgramLayout.TraceContext` defines the trace-wide Metal tags.
- Every group in `PrimaryTraceProgramLayout.HitGroups` is constrained to that trace context.
- Any-hit and intersection stage structs receive input types derived from the same context.

Figure 7 shows how the trace program layout connects the trace call to the grouped stage structs.

<a id="fig-context-reachability"></a>
![Context connects ray tracer and hit shaders](figures/042-ray-tracing-api/context-reachability.svg)

*Figure 7. Context reachability contract: the trace program layout connects `RayTracer<ProgramLayout>`, the trace-wide context, hit groups, and stage input types so the compiler has a source-visible relationship.*

This does not prove that arbitrary host data is correct. If the host builds an SBT or Metal
function table that violates the reflected program layout, the program can still be wrong. The
goal is to make the shader-side contract explicit enough that:

- Slang can generate Metal tags for reachable custom intersection functions.
- Slang can reject shader declarations that are inconsistent inside the program layout.
- Reflection can expose the expected table to host code.
- Validation layers or Slang runtime helpers can compare host records against the reflected
  contract.

### 2.3 Writing Stages As Interface-Conforming Types

In the new model, miss, closest-hit, any-hit, and intersection logic are not written as independent
entry points. They are written as ordinary structs that conform to built-in stage interfaces.

Example:

```slang
struct PrimaryTriangleClosestHit
    : rt::IClosestHitShader<PrimaryTriangleContext>
{
    void invoke(rt::ClosestHitInput<PrimaryTriangleContext> input)
    {
        input.payload.color = float4(input.distance, 0.0, 0.0, 1.0);
    }
}

struct PrimaryTriangleAnyHit
    : rt::IAnyHitShader<PrimaryTriangleContext>
{
    void invoke(rt::AnyHitInput<PrimaryTriangleContext> input)
    {
        if (isTransparent(input.triangle))
            input.ignoreHit();
    }
}

struct PrimarySphereIntersection
    : rt::IIntersectionShader<PrimarySphereContext, SphereHitAttributes>
{
    rt::IntersectionReturn<PrimarySphereContext, SphereHitAttributes>
    invoke(rt::IntersectionInput<PrimarySphereContext> input)
    {
        SphereHitAttributes attr;
        float t = intersectSphere(input, attr);
        return rt::IntersectionReturn<PrimarySphereContext, SphereHitAttributes>::accept(t, attr);
    }
}
```

The compiler is responsible for lowering these structs to the target form:

- D3D and Vulkan: generated native entry points and hit groups, connected to SBT records.
- Metal: generated intersection functions for any-hit/custom-intersection behavior, plus a
  generated post-trace closest-hit dispatch switch.

The user writes one source-level model. The target backend chooses the appropriate pipeline shape.

## 3. Migration Examples

### 3.1 Migrating Existing Metal Code To The New API

Existing Metal users often write post-trace logic directly:

```metal
kernel void rayGen(...)
{
    intersector<instancing, triangle_data> tracer;
    tracer.assume_geometry_type(geometry_type::triangle);

    auto result = tracer.intersect(ray, scene, intersectionFunctionBuffer, payload);

    if (result.type == intersection_type::none)
    {
        miss(payload);
    }
    else
    {
        uint slot = result.geometry_id;

        switch (slot)
        {
        case 0: shadeOpaqueTriangle(payload, result); break;
        case 1: shadeAlphaTriangle(payload, result); break;
        case 2: shadeProceduralSphere(payload, result); break;
        }
    }
}
```

With the proposed API, the user moves the manually dispatched operations into stage structs and
declares the trace program layout structurally. The list order defines the slots:

```slang
struct PrimaryMissGroup : rt::IMissGroup
{
    typealias Context = PrimaryMissContext;
    typealias Miss = PrimaryMiss;
}

struct PrimaryOpaqueTriangleGroup : rt::IHitGroup
{
    typealias Context = PrimaryTriangleContext;
    typealias ClosestHit = PrimaryOpaqueTriangleClosestHit;
    typealias AnyHit = rt::NoAnyHit<PrimaryTriangleContext>;
    typealias IntersectionAttributes = rt::NoAttributes;
    typealias Intersection = rt::NoIntersection<PrimaryTriangleContext>;
}

struct PrimaryAlphaTriangleGroup : rt::IHitGroup
{
    typealias Context = PrimaryTriangleContext;
    typealias ClosestHit = PrimaryAlphaTriangleClosestHit;
    typealias AnyHit = PrimaryAlphaTriangleAnyHit;
    typealias IntersectionAttributes = rt::NoAttributes;
    typealias Intersection = rt::NoIntersection<PrimaryTriangleContext>;
}

struct PrimarySphereGroup : rt::IHitGroup
{
    typealias Context = PrimarySphereContext;
    typealias ClosestHit = PrimarySphereClosestHit;
    typealias AnyHit = rt::NoAnyHit<PrimarySphereContext>;
    typealias IntersectionAttributes = SphereHitAttributes;
    typealias Intersection = PrimarySphereIntersection;
}

struct PrimaryTraceProgramLayout : rt::ITraceProgramLayout
{
    typealias TraceContext = PrimaryTraceContext;

    typealias MissGroups = rt::MissGroupList<
        TraceContext,
        PrimaryMissGroup>;             // miss[0]

    typealias HitGroups = rt::HitGroupList<
        TraceContext,
        PrimaryOpaqueTriangleGroup,     // hitGroup[0]
        PrimaryAlphaTriangleGroup,      // hitGroup[1]
        PrimarySphereGroup>;            // hitGroup[2]

    typealias CallableGroups = rt::NoCallableGroups<TraceContext>;
}

rt::TraceProgramDescriptor<PrimaryTraceProgramLayout> gPrimaryDescriptor;
```

Ray-generation code becomes:

```slang
[shader("raygeneration")]
void rayGen()
{
    RadiancePayload payload;

    rt::RayTraversalDesc desc;
    desc.ray = makeRay();
    desc.instanceMask = 0xff;
    desc.sbtOffset = 0;
    desc.sbtStride = 3;
    desc.missIndex = 0;

    rt::RayTracer<PrimaryTraceProgramLayout> tracer;
    tracer.trace(desc, scene, gPrimaryDescriptor, payload);
}
```

For Metal, Slang generates code that is equivalent to the user's old post-trace dispatch, but the
source of truth is now `PrimaryTraceProgramLayout.HitGroups` and
`PrimaryTraceProgramLayout.MissGroups`.

Metal host migration:

1. Query `PrimaryTraceProgramLayout` through Slang reflection.
2. For each hit group list position, discover its any-hit and intersection stage structs.
3. Build the Metal intersection function buffer or function table using the reflected slot
   mapping.
4. For function-buffer dispatch, configure Metal's index calculation consistently with
   `RayTraversalDesc`:

```metal
intersector.set_geometry_multiplier(desc.sbtStride);
intersector.set_base_id(desc.sbtOffset);
```

This keeps Metal's any-hit and custom-intersection dispatch aligned with Slang's generated
closest-hit dispatch.

### 3.2 Migrating Existing Slang D3D/Vulkan Ray Tracing Code

Existing Slang code usually has independent pipeline entry points:

```slang
[shader("raygeneration")]
void rayGen()
{
    RadiancePayload payload;

    TraceRay(
        scene,
        flags,
        instanceMask,
        rayContributionToHitGroupIndex,
        multiplierForGeometryContributionToHitGroupIndex,
        missShaderIndex,
        ray,
        payload);
}

[shader("miss")]
void miss(inout RadiancePayload payload)
{
    payload.color = backgroundColor;
}

[shader("closesthit")]
void closestHit(inout RadiancePayload payload, BuiltInTriangleIntersectionAttributes attr)
{
    payload.color = shadeTriangle(attr);
}
```

The migrated shader keeps the same conceptual data, but moves stage bodies into typed structs:

```slang
struct PrimaryMissContext : rt::IMissGroupContext
{
    typealias TraceContext = PrimaryTraceContext;
    typealias Record = PrimaryMissRecord;
}

struct PrimaryMiss : rt::IMissShader<PrimaryMissContext>
{
    void invoke(rt::MissInput<PrimaryMissContext> input)
    {
        input.payload.color = backgroundColor;
    }
}

struct PrimaryTriangleClosestHit
    : rt::IClosestHitShader<PrimaryTriangleContext>
{
    void invoke(rt::ClosestHitInput<PrimaryTriangleContext> input)
    {
        input.payload.color = shadeTriangle(input.triangle);
    }
}
```

The old trace parameters map directly to fields in `RayTraversalDesc`:

```slang
rt::RayTraversalDesc desc;
desc.ray = ray;
desc.instanceMask = instanceMask;
desc.sbtOffset = rayContributionToHitGroupIndex;
desc.sbtStride = multiplierForGeometryContributionToHitGroupIndex;
desc.missIndex = missShaderIndex;

rt::RayTracer<PrimaryTraceProgramLayout> tracer;
tracer.trace(desc, scene, gPrimaryDescriptor, payload);
```

D3D/Vulkan host migration:

1. Query `PrimaryTraceProgramLayout` through Slang reflection.
2. For each reflected miss group, add a miss record at its list position.
3. For each reflected hit group, add a hit group record at its list position.
4. Use the same application data that previously produced `rayContributionToHitGroupIndex`,
   `multiplierForGeometryContributionToHitGroupIndex`, and `missShaderIndex`.

The native SBT model is not replaced. The new shader declarations make the intended SBT layout
visible to Slang, which enables Metal lowering and gives host code a single reflected contract.

### 3.3 Host Reflection Patterns

The reflection API shape is not finalized. The expected information is:

```cpp
struct ReflectedTraceProgramLayout
{
    TypeReflection* traceContextType;
    List<ReflectedMissGroup> missGroups;
    List<ReflectedHitGroup> hitGroups;
    List<ReflectedCallableGroup> callableGroups;
};

struct ReflectedMissGroup
{
    int slot;
    EntryPointReflection* generatedMissEntryPoint;
};

struct ReflectedHitGroup
{
    int slot;
    TypeReflection* hitContextType;
    EntryPointReflection* generatedClosestHitEntryPoint;
    EntryPointReflection* generatedAnyHitEntryPoint;
    EntryPointReflection* generatedIntersectionEntryPoint;
};

struct ReflectedCallableGroup
{
    int slot;
    TypeReflection* callableContextType;
    EntryPointReflection* generatedCallableEntryPoint;
};
```

Pattern A: D3D/Vulkan native SBT.

```cpp
auto programLayout = reflection->findTraceProgramLayout("PrimaryTraceProgramLayout");

for (auto miss : programLayout.missGroups)
{
    sbt.setMissRecord(miss.slot, miss.generatedMissEntryPoint);
}

for (auto hit : programLayout.hitGroups)
{
    sbt.setHitGroup(
        hit.slot,
        hit.generatedClosestHitEntryPoint,
        hit.generatedAnyHitEntryPoint,
        hit.generatedIntersectionEntryPoint);
}
```

The application still controls geometry contribution, instance contribution, stride, and offset.
The reflected slots tell the application which shader group belongs at each slot.

Pattern B: Metal intersection function buffer.

```cpp
auto programLayout = reflection->findTraceProgramLayout("PrimaryTraceProgramLayout");

for (auto hit : programLayout.hitGroups)
{
    if (hit.generatedAnyHitEntryPoint || hit.generatedIntersectionEntryPoint)
    {
        functionBuffer.setFunction(
            hit.slot,
            hit.generatedIntersectionOrAnyHitFunction);
    }
}
```

The generated Metal ray-generation code uses the same slot to dispatch closest-hit after
`intersect(...)`. The host does not need to provide a separate closest-hit dispatch table for
Metal because closest-hit dispatch is synthesized by Slang.

Pattern C: Metal intersection function table.

Metal's ordinary function table path is less flexible than the function-buffer path because
shader code cannot set the same base-id and geometry-multiplier values in the same way. It can
still be supported for restricted layouts, for example:

- the acceleration structure already contains the expected function-table offsets,
- the shader uses a fixed `RayTraversalDesc` layout,
- or the backend can prove that the table index matches the reflected hit-group slot.

Function-buffer lowering is the preferred general path for matching D3D/Vulkan SBT index
calculation.

Pattern D: Manual host construction without reflection.

A developer can still build the table by reading the shader source if the project chooses a fixed
layout convention:

```slang
typealias HitGroups = rt::HitGroupList<
    TraceContext,
    PrimaryOpaqueTriangleGroup,     // hitGroup[0]
    PrimaryAlphaTriangleGroup,      // hitGroup[1]
    PrimarySphereGroup>;            // hitGroup[2]
```

Reflection is strongly preferred because it removes duplicated source-of-truth in host code and
enables validation, but the layout is intentionally visible and reviewable in shader source.

## 4. Open Design Questions

- Exact reflection API names and ownership model.
- Exact generated entry-point naming rules for D3D and Vulkan.
- Whether Metal ordinary function-table lowering should be a restricted feature or a fully
  supported path.
- How to represent custom intersection attributes on Metal when native return-value limits are
  insufficient.
- How much runtime validation Slang should provide between reflected `ITraceProgramLayout` data and
  host-created SBT or Metal function-buffer state.
