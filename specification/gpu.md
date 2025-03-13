# GPUs [gpu]

# Dispatches [gpu.dispatch]

Work is issued to a GPU device in the form of **commands**.
A **dispatch** is a *command* that causes a GPU device to execute a specific *pipeline instance*.

A dispatch determines:

* The *pipeline instance* _P_ to execute
* A value for each of the *dispatch parameters* of _P_
* A value for each of the *uniform shader parameters* of _P_

# Pipelines [gpu.pipeline]

## Pipeline Types [gpu.pipeline.type]

A **pipeline type** is a category of workloads that a GPU can support.
Slang supports the following pipeline types:

* *rasterization pipelines*
* *compute pipelines*
* *ray-tracing pipelines*

Each *pipeline type* _PT_ defines:

* Zero or more **dispatch parameters**, each having a name and a type

* A set of *stage types*

* A set of **associated record types**

* Validation rules for *pipeline instances* of type _PT_

## Pipeline Instances [gpu.pipeline.instance]

A **pipeline instance** is an instance of some *pipeline type*, and consists of:

* A set of zero or more *stage instances*

* A *bundle*

The *kernels* of any *programmable* *stage instances* in a *pipeline instance* must be compatible with the *bundle* of the *pipeline instance*.

### Stages [gpu.pipeline.stage]

#### Stage Types [exec.gpu.pipeline.stage.type]

A **stage type** is a type of stage that may appear in *pipeline instances*.

Each *stage type* belongs to a single *pipeline type*.

A *stage type* is either **programmable** or it is **fixed-function**.

A stage has zero or more **fixed-function parameters**, each having a name and a type

A *stage type* is either required, optional, or instanceable.

#### Stage Instances [gpu.pipeline.stage.instance]

A **stage instance** is an instance of some *stage type* _ST_, and consists of:

* A *kernel* _K_ for _ST_, if _ST_ is *programmable*.

* Values for each of the *fixed-function parameters* of _ST_ that are not included in _K_


### Signatures [exec.gpu.pipeline.stage.signature]

The **signature** of a *programmable stage* consists of its *uniform signature* and its *varying signature*.

The **uniform signature** of a *programmable stage* is a sequence of *types*.

A *programmable stage* has a set of **boundaries**.
Each *programmable stage* has an input *boundary* and an output boundary.

The varying input signature of a programmable stage is its signature along its input boundary;
The varying output signature of a programmabel stage is its signature along its output boundary;

The varying signature of a programmable stage comprises the boundary signature of that stage along each of its boundaries.

To compute the signature of a stage _S_ with a kernel based on a function _f_:

* Initialize the uniform signature of _S_ to an empty sequence
* Initailize the boundary signature of _S_ along each of its boundaries to an empty sequence
* If _f_ has an implicit `this` parameter then:
  * Append the type of the `this` parameter to the uniform signature of _S_
* For each explicit parameter _p_ of _f_:
  * If _p_ is `uniform`, then:
    * Add the type of _p_ to the uniform signature of _S_
  * Otherwise:
    * TODO: handling of semantics!
    * Add _p_ to the varying signature of _S_
* Add the result type _R_ to the varying output signature of _S_
  * TODO: need to handle semantics on _f_ as semantics on the result...

The default way to add a parameter _p_ to the varying signature of some stage _S_ is:

* If the direction of _p_ is `in` or `inout`, then add _p_ to the varying input signature of _S_
* If the direction of _p_ is `out` or `inout`, then add _p_ to the varying output signature of _S_


## Records [exec.gpu.pipeline.record]

A **record** is an instance of an *associated record type* of a *pipeline type*.
Data is passed between the *stage instances* of a *pipeline instance* in the form of *records*.

The varying input and output signature of a *stage instance* is defined with respect to the *associated record types* of the corresponding *pipeline type*.

A *stage instance* depends on the *associated record types* that are part of its signature.
A *pipeline instance* depends on the *associated record types* that are part of its *stage instances*.

A programmable stage has a set of boundaries.
Every programmable stage has an input boundary and an output boundary.

A record type signature is a sequence of pairs (_T_, _s_), where _T_ is a type and _s_ is a semantic.
The varying signature of a programmable stage along one of its boundaries is a record type signature.



For each *associated record type* _R_ that a *pipeline instance* _P_ depends on, if there are *stage instances* _A_ and _B_ in _P_ such that _A_ outputs _R_ and _B_ inputs _R_, then the configuration of _R_ for _B_ must be a prefix of the configuration of _A_.


## Compute [exec.gpu.pipeline.compute]

A **compute pipeline** instance is a *pipeline instance* with a single *stage instance* of *stage type* `compute`.
The `compute` *stage type* is *programmable*.

A **compute dispatch** is a *dispatch* of a *compute pipeline instance*.

### Blocks

A *compute dispatch* invokes its kernel for each strand in a **block** of strands.
The number and organization of strands in a *block* is determined by a **block shape**.
A *block shape* consists of its rank _N_, a positive integer, and its extents, a vector of _N_ positive integers.

Note: Typical GPU platforms support block shapes with ranks up to 3.

Every *strand* in a *block* _b_ has a **strand ID**, a vector of _N_ non-negative integers, where _N_ is the rank of the block shape of _b_.
For a *strand* _s_ in *block* _b_, _s.strandID_ is in [0, _b.shape.extents[i]_) for all _i_ in [0,_b.shape.rank_).

The *strands* in a *block* are guaranteed to execute concurrently.

### Grids

Each *block* of *strands* that execute a compute entry point is part of a **grid** of blocks.
The number and organization of blocks in a *grid* is determined by a **grid shape**.
A *grid shape* consists its rank _N_, a positive integer, and its extent, a positive integer, along each axis _i_, where 0 <= _i_ < _N_.

Note: Typical GPU platforms support grid shapes with ranks up to 3.

Every *block* in a *grid* _g_ has a **block ID**, a vector of _N_ non-negative integers, where _N_ is the rank of the grid shape of _g_.
For a *block* _b_ in *grid* _g_, _b.blockID_ is in [0, _g.shape.extents[i]_) for all _i_ in [0,_g.shape.rank_).

The *blocks* in a *grid* may be executed concurrently, but this is not guaranteed.

### Attributes

#### `[numthreads]`

An entry point for the `compute` stage may have a `[numthreads]` attribute.
If present, a `[numthreads]` attribute determines the *block shape* of compute pipelines using that entry point.

### Signature

A `compute` stage has the following boundaries:

* An input boundary with associated record type `ComputeInput`
* An output boundary with associated record type `ComputeOutput`

The `ComputeOutput` record type of a `compute` stage must be empty.

The `ComputeInput` record type of a `compute` stage must not contain any entries with a user semantic.

The `ComptueInput` record type of a `compute` stage may contain entries of the form:

* ( _T_ , `SV_DispatchThreadID`, 0 )
* ( _T_ , `SV_GroupID`, 0 )
* ( _T_, `SV_GroupIndex`, 0 )
* ( _T_, `SV_GroupThreadID`, 0 )

TODO: Need a compact notation for specifying system-value semantics, because otherwise the writing will get overly verbose.

```
in @ComputeInput SV_GroupID<N> : vector<uint,N>;
in @ComputeInput SV_GroupIndex : uint;
in @ComputeInput SV_GroupThreadID<N> : vector<uint,N>
in @ComputeInput SV_DispatchThreadID<N> : vector<uint,N>
```


## Rasterization [exec.gpu.pipeline.raster]

A **rasterization pipeline** instance is a *pipeline instance*.

### Rasterization System Values

TODO: There are system values that can appear on vertices of whatever geometry-related stage comes last.

```
out @RasterVertex SV_Position : float4;
out @RasterVertex SV_RenderTargetArrayIndex : uint;
out @RasterVertex SV_ViewPortArrayIndex : uint;
out @RasterVertex SV_ClipDistance : float4[];
out @RasterVertex SV_CullDistance : float4[];
```

### Index Fetch [exec.gpu.pipeline.raster.stage.fetch.index]



### Vertex Fetch [exec.gpu.pipeline.raster.stage.fetch.vertex]

Vertex fetch is a *fixed-function* stage.

This stage takes as input an `VertexIndex` record, and produces as output an `AssembledVertex` record.

* For each attribute of the `AssembledVertex` record, fetch data from the corresponding vertex stream, using either the instance ID or vertex ID (based on configuration).

### Vertex Shader [exec.gpu.pipeline.raster.stage.vertex]

A given dispatch may invoke the kernel for the `vertex` stage one or more times for each vertex ID and instance ID.

#### Signature

The `vertex` *stage type* is *programmable*.

A `vertex` stage has the following boundaries:

* An input boundary with associated record type `AssembledVertex`
* An output boundary with associated record type `CoarseVertex`

#### System Values

```
in @AssembledVertex SV_VertexID : uint;
in @DrawInstance SV_InstanceID : uint;
in @View SV_ViewID : uint;
```

### Primitive Assembly [exec.gpu.pipeline.raster.stage.primitive-assembly]

A primitive consists of a primitive topology and N vertices, where N matches the requirements of that primitive topology.

This stage takes as input coarse vertex records from a preceding stage.
It produces as output primitives of coarse vertex records.

### Tessellation [exec.gpu.pipeline.raster.stage.tess]

#### Hull Shader [exec.gpu.pipeline.raster.stage.tess.hull]

This stage takes as input a patch primitive of coarse vertex records.
It produces as output a patch primitive of control point records a patch record.

##### Attributes

An entry point for the `hull` stage must have a `[patchconstantfunc]` attribute.

TODO: specify how the patch-constant function gets identified, etc.

TODO: add the other attributes...

##### Signature

The varying signature of a `hull` entry point is determined as follows:

* For any `in` parameter of type `InputPatch<`_T_`,`_N_`>`, _T_ contributes to the `CoarseVertex` record type
* Any other `in` parameters contribute to the `HullInput` record type
* `out` parameters contribute to the `ControlPoint` record type

The varying signature of a patch-constant function is determined as follows:

* For any `in` parameters of type `OutputPatch<`_T_`,`_N_`>`, _T_ contributes to the `ControlPoint` record type
* Any other `in` parameters contribute to the `PatchConstantInput` record type
* `out` parameters contribute to the `Patch` record type

The varying signature of a `hull` stage is the union of the varying signatures of the `hull` entry point and the patch-constant function.

TODO: Need to specify that the `ControlPoint` type and _N_ on input to the patch-constant function must match those output by the hull shader.

The `HullInput` boundary of a `hull` stage must not have any elements with user semantics.

The `PatchConstantInput` boundary of a `hull` stage must be empty.

##### System Values

The `HullInput` record type supports the following system values:

```
    => `SV_PrimitiveID`
    => `SV_OutputControlPointID`
```

The `Patch` record type supports the following system values:

```
    => `SV_TessFactor`
    => `SV_InsideTessFactor`
```




#### Domain Shader [exec.gpu.pipeline.raster.stage.tess.domain]

This stage takes as input a patch primitive of control point records, and a patch record.
It outputs a fine vertex record.

##### System Values

```
    => `SV_DomainLocation`
```

### Geometry Shader [exec.gpu.pipeline.raster.stage.geometry]

This stage takes as input a primitive of vertex records (either coarse or fine vertices, depending on what preceding stages are enabled).
As output, a geometry shader may have one or more output streams, each having a coresponding type of record.
For each output stream, a strand executing a geometry shader may output zero or more records of the corresponding type.

If one of the output streams of the geometry shader is connected to the rasterizer stage, then that output stream corresponds to raster vertex records.

#### System Values

```
    => `SV_GSInstanceID`
```

### Mesh Shading [exec.gpu.pipeline.raster.stage.mesh]

### Rasterizer [exec.gpu.pipeline.raster.stage.rasterizer]

The rasterizer is a *fixed-function* stage.

This stage takes as input a primitive of raster vertex records, and determines which pixels in a render target that primitive covers.
The stage outputs zero or more raster fragment records, one for each covered pixel.

### Depth/Stencil Test [exec.gpu.pipeline.raster.stage.depth-stencil-test]

### Fragment Shader [exec.gpu.pipeline.raster.stage.fragment]

#### Signature

This stage takes as input a raster fragment record, and produces as output either:

* One `ShadedFragment` record
* One `ShadedFragment` record and N `ShadedFragment.Sample` records

> TODO:
>
> * For any input elements, need to consider its interpolation mode.
>   If `sample` interpolation is requested, then the input goes to the `Sample`
>   record type; otherwise the `Fragment` record type.
>
>     * Then need a little fixup after that step to deal with system values
>       that would have been binned into the `Fragment` record but that
>       should go elsewhere.

#### System Values

Input:

```
in @Sample SV_SampleIndex : uint;

in @RasterPrimitive SV_IsFrontFace : bool;

in @Fragment SV_Coverage : ???;
in @Fragment SV_InnerCoverage : ???;

// TODO: these could have @Fragment or @Sample rate,
// depending on how they are qualified
in @Sample SV_Barycentrics : float3;
in @Sample SV_Depth : float;
```

Output:

```
    => `SV_Target`
    => `SV_Depth`
    => `SV_DepthLessEqual`
    => `SV_DepthGreaterEqual`
    => `SV_StencilRef`
```

### Blend [exec.gpu.pipeline.raster.stage.blend]

This stage takes as input a `ShadedFragment` record (possibly including its `ShadedFragment.Sample`) and a `Pixel` record, and produces as output a `Pixel` record.

## Ray Tracing [exec.gpu.pipeline.ray-tracing]

TODO: The trickiest part here is setting up the relevant record types, since a single pipeline instance may use a variety of different ray payloads, hit attributes, etc. The only constraints that can be given are really related to when the results of a `TraceRay` might be undefined because of a mismatch in record types between entry points that get invoked.

# Fodder [gpu.fodder]

> Note:
>
> This section is being used to collect material that probably belongs in the "GPU" chapter, but that doesn't currently have a home in the way it has been organized so far.

```.semantic
PipelineType
    => `RASTERIZATION`
    => `COMPUTE`
    => `RAYTRACING`
    => `WORKGRAPH`

ShaderStage
    => RasterizationPipelineShaderStage
    => ComputeShaderStage
    => RayTracingShaderStage
    => WorkGraphShaderStage

RasterizationPipelineShaderStage
    => `fragment`

PreRasterizationShaderStage
    => TraditionalPreRasterizationShaderStage
    => MeshPreRasterizationShaderStage

TraditionalPreRasterizationShaderStage
    => `vertex`
    => TessellationShaderStage
    => `geometry`

TessellationShaderStage
    => `hull`
    => `domain`

MeshPreRasterizationShaderStage
    => `mesh`
    => `amplification`

ComputeShaderStage
    => `compute`

RayTracingShaderStage
    => `raygen`
    => `intersection`
    => `anyhit`
    => `closesthit`
    => `miss`
    => `callable`

WorkGraphShaderStage
    => `node`

Semantic
    => SemanticName SemanticIndex

SemanticIndex
    => NaturalNumber

SemanticName
    => UserSemanticName
    => SystemSemanticName

UserSemanticName
    => String

SystemSemanticName
    => `SV_VertexID`
    => `SV_InstanceID`
    => `SV_Position`
    => `SV_RenderTargetArrayIndex`
    => `SV_ViewPortArrayIndex`
    => `SV_ClipDistance`
    => `SV_CullDistance`
    => `SV_OutputControlPointID`
    => `SV_DomainLocation`
    => `SV_PrimitiveID`
    => `SV_GSInstanceID`
    => `SV_SampleIndex`
    => `SV_IsFrontFace`
    => `SV_Coverage`
    => `SV_InnerCoverage`
    => `SV_Target`
    => `SV_Depth`
    => `SV_DepthLessEqual`
    => `SV_DepthGreaterEqual`
    => `SV_StencilRef`
    => `SV_DispatchThreadID`
    => `SV_GroupID`
    => `SV_GroupIndex`
    => `SV_GroupThreadID`
    => `SV_TessFactor`
    => `SV_InsideTessFactor`
    => `SV_ViewID`
    => `SV_Barycentrics`
    => `SV_ShadingRate`
    => `SV_CullPrimitive`
    => `SV_StartVertexLocation`
    => `SV_StartInstanceLocation`
```

| Stage | Boundary | Record Type |
|-------|----------|-------------|
| `vertex` | `in` | `AssembledVertex` |
| `vertex` | `out` | `CoarseVertex` |
| `hull` | `in` | `HullInput` |
| `hull` | `out` | `HullOutput` |
| `hull` | input control points | `CoarseVertex` |
| `hull` | output control points | `ControlPoint` |
| `hull` | patch constant function | `Patch` |
| `domain` | `in` | `Patch` |
| `domain` | input control points | `ControlPoint` |
| `domain` | output | `FineVertex` |
| `geometry` | `in` | `GeometryInput` |
| `geometry` | `out` | `GeometryOutput` |
| `geometry` | input vertices | `FineVertex` |
| `geometry` | output stream 0 | `RasterVertex` |
| `geometry` | output stream _i_ | `StreamOutputVertex_i` |
| `fragment` | `in` | `RasterVertex` |
| `fragment` | `out` | `Fragment` |
| `mesh` | `in` | `MeshInput` |
| `mesh` | ??? | `MeshOutputVertex` |
| `mesh` | ??? | `MeshPrimitive` |
| `amplification` | ??? | ??? |
| `compute` | `in` | `ComputeInput` |
| `compute` | `out` | `ComputeOutput` |