# GPUs [gpu]

## Dispatches [gpu.dispatch]

Work is issued to a GPU device in the form of **commands**.
A **dispatch** is a *command* that causes a GPU device to execute a specific *pipeline instance*.

A dispatch determines:

* The *pipeline instance* _P_ to execute
* A value for each of the *dispatch parameters* of _P_
* A value for each of the *uniform shader parameters* of _P_

### Pipeline Instance [exec.gpu.pipeline]

A **pipeline instance** is an instance of some *pipeline type*, and consists of:

* A set of zero or more *stage instances*

* A *bundle*

The *kernels* of any *programmable* *stage instances* in a *pipeline instance* must be compatible with the *bundle* of the *pipeline instance*.

#### Pipeline Types [exec.gpu.pipeline.type]

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

### Stage Instances [exec.gpu.pipeline.stage]

A **stage instance** is an instance of some *stage type* _ST_, and consists of:

* A *kernel* _K_ for _ST_, if _ST_ is *programmable*.

* Values for each of the *fixed-function parameters* of _ST_ that are not included in _K_

#### Stage Types [exec.gpu.pipeline.stage.type]

A **stage type** is a type of stage that may appear in *pipeline instances*.

Each *stage type* belongs to a single *pipeline type*.

A *stage type* is either **programmable** or it is **fixed-function**.

A stage has zero or more **fixed-function parameters**, each having a name and a type

A *stage type* is either required, optional, or instanceable.

#### Signatures [exec.gpu.pipeline.stage.signature]

The signature of a programmable stage consists of its uniform signature and its varying signature.

The uniform signature of a programmable stage is a sequence of types.

A programmable stage has a set of boundaries.
Each programmable stage has an input boundary and an output boundary.

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


### Records [exec.gpu.pipeline.record]

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


#### Compute [exec.gpu.pipeline.compute]

A **compute pipeline** instance is a *pipeline instance* with a single *stage instance* of *stage type* `compute`.
The `compute` *stage type* is *programmable*.

A *dispatch* of a *compute pipeline* instance is a **compute dispatch**.
A *compute dispatch* invokes its kernel for each strand in a **block** of strands.
The number and organization of strands in a *block* is determined by a **block shape**.
A *block shape* comprises its rank _N_, a positive integer, and its extent, a positive integer, along each axis _i_, where 0 <= _i_ < _N_.
Typical GPU platforms support block shapes with ranks up to 3.

An entry point for the `compute` stage may use a `[numthreads]` attribute to specify the block shape to be used by pipeline configurations using that entry point.

The strands in a block are executed concurrently.

Each block of strands that executes a compute entry point is part of a **grid** of blocks.
The number and organization of blocks in a *grid* is determined by a **grid shape**.
A *grid shape* comprises its rank _N_, a positive integer, and its extent, a positive integer, along each axis _i_, where 0 <= _i_ < _N_.
Typical GPU platforms support grid shapes with ranks up to 3.

The blocks in a grid may be executed concurrently, but this is not guaranteed.

#### Rasterization [exec.gpu.pipeline.raster]

A **rasterization pipeline** instance is a *pipeline instance*.

##### Index Fetch [exec.gpu.pipeline.raster.stage.fetch.index]



##### Vertex Fetch [exec.gpu.pipeline.raster.stage.fetch.vertex]

Vertex fetch is a *fixed-function* stage.

This stage takes as input an `VertexIndex` record, and produces as output an `AssembledVertex` record.

* For each attribute of the `AssembledVertex` record, fetch data from the corresponding vertex stream, using either the instance ID or vertex ID (based on configuration).

##### Vertex Shader [exec.gpu.pipeline.raster.stage.vertex]

The `vertex` *stage type* is *programmable*.

The signature of a vertex stage is:

* One `AssembledVertex` record as input

* One `CoarseVertex` record as output

This stage takes as input one `AssembledVertex` record, and produces as output one `CoarseVertex` record.

Given an entry point function for the `vertex` stage:

* Iterate over its entry-point parameters
  * If the parameter is `uniform`, then add it to the uniform signature
  * If the parameter is `in` or `inout`, then add it to the `AssembledVertex` record signature
  * If the parameter is `out` or `inout`, then add it to the `CoarseVertex` record signature

A given dispatch may invoke the kernel for the `vertex` stage one or more times for each vertex ID and instance ID.

##### Primitive Assembly [exec.gpu.pipeline.raster.stage.primitive-assembly]

A primitive consists of a primitive topology and N vertices, where N matches the requirements of that primitive topology.

This stage takes as input coarse vertex records from a preceding stage.
It produces as output primitives of coarse vertex records.

##### Tessellation [exec.gpu.pipeline.raster.stage.tess]

###### Hull Shader [exec.gpu.pipeline.raster.stage.tess.hull]

This stage takes as input a patch primitive of coarse vertex records.
It produces as output a patch primitive of control point records a patch record.

###### Domain Shader [exec.gpu.pipeline.raster.stage.tess.domain]

This stage takes as input a patch primitive of control point records, and a patch record.
It outputs a fine vertex record.

##### Geometry Shader [exec.gpu.pipeline.raster.stage.geometry]

This stage takes as input a primitive of vertex records (either coarse or fine vertices, depending on what preceding stages are enabled).
As output, a geometry shader may have one or more output streams, each having a coresponding type of record.
For each output stream, a strand executing a geometry shader may output zero or more records of the corresponding type.

If one of the output streams of the geometry shader is connected to the rasterizer stage, then that output stream corresponds to raster vertex records.

##### Mesh Shading [exec.gpu.pipeline.raster.stage.mesh]

##### Rasterizer [exec.gpu.pipeline.raster.stage.rasterizer]

The rasterizer is a *fixed-function* stage.

This stage takes as input a primitive of raster vertex records, and determines which pixels in a render target that primitive covers.
The stage outputs zero or more raster fragment records, one for each covered pixel.

##### Depth/Stencil Test [exec.gpu.pipeline.raster.stage.depth-stencil-test]

##### Fragment Shader [exec.gpu.pipeline.raster.stage.fragment]

This stage takes as input a raster fragment record, and produces as output either:

* One `ShadedFragment` record
* One `ShadedFragment` record and N `ShadedFragment.Sample` records

##### Blend [exec.gpu.pipeline.raster.stage.blend]

This stage takes as input a `ShadedFragment` record (possibly including its `ShadedFragment.Sample`) and a `Pixel` record, and produces as output a `Pixel` record.

#### Ray Tracing [exec.gpu.pipeline.ray-tracing]

TODO: define the stages of the **ray-tracing pipeline**.
