




Execution {#exec}
=========

A <dfn>runtime session</dfn> is a context for loading and execution of Slang code.
A [=runtime session=] exists within the context of a <dfn>process</dfn> running on some <dfn>host</dfn> machine.
For some implementations, a [=runtime session=] may be the same as a [=process=], but this is not required.

A [=runtime session=] has access to one or more distinct <dfn>devices</dfn> on which work may be performed.
Different [=devices=] in a [=runtime session=] may implement different <dfn>architectures</dfn>, each having its own machine code format(s).
For some implementations, the [=host=] may also be a [=device=], but this is not required.

<div class="issue">
We need to define what it means to "execute" statements and to "evaluate" expressions...
</div>

When a strand invokes an invocable entity |f|, it executes the body of |f| (a statement).
As part of executing a statement, a strand may execute other statements, and evaluate expressions.
A strand evaluates an expression to yield a value, and also for any side effects that may occur.

Strands {#exec.strand}
-------

A <dfn>strand</dfn> is a logical runtime entity that executes Slang code.
The state of a strand consists of a stack of [=activation records=], representing invocations that the strand has entered but not yet exited.

A strand may be realized in different ways by different devices, runtime systems, and compilation strategies.

Note: The term "strand" was chosen because a term like "thread" is both overloaded and charged.
On a typical CPU [=architecture=], a strand might map to a thread, or it might map to a single SIMD lane, depending on how code is compiled.
On a typical GPU [=architecture=], a strand might map to a thread, or it might map to a wave, thread block, or other granularity.

Note: An implementation is allowed to "migrate" a strand from one thread to another.

A strand is <dfn>launched</dfn> for some [=invocable=] declaration |D|, with an initial stack comprising a single activation record for |D|, a

Activation Records {#exec.activation}
------------------

An <dfn>activation record</dfn> represents the state of a single invocation of some [=invocable=] declaration by some strand.
An [=activation record=] for [=invocable=] declaration |D| by strand |S| consists of:

* A value for each parameter of |D|

* The location |L| within the [=body=] of |D| that |S|'s execution has reached for that invocation

* A value for each local variable of |D| that is in scope at |L|

Waves {#exec.wave}
-----

A <dfn>wave</dfn> is a set of one or more [=strands=] that execute concurrently.
At each point in its execution, a strand belongs to one and only one [=wave=].

Waves are guaranteed to make forward progress independent of other waves.
Strands that belong to the same wave are not guaranteed to make independent forward progress.

Note: A runtime system can execute the strands of a wave in "lock-step" fashion, if it chooses.

Strands that are [=launched=] to execute a [=kernel=] as part of a [=dispatch=] will only ever be in the same wave as strands that were launched as part of the same [=dispatch=].

Every [=wave=] |W| has an integer <dfn>wave size</dfn> |N| > 0.
Every strand that belongs to |W| has an integer <dfn>lane ID</dfn> |i|, with 0 <= |i| < |N|.
Distinct strands in |W| have distinct [=lane IDs=].

Note: A wave with [=wave size=] |N| can have at most |N| strands that belong to it, but it can also have fewer.
This might occur because a partially-full wave was launched, or because strands in the wave terminated.
If strands in a wave have terminated, it is possible that there will be gaps in the sequence of used lane IDs.

Two strands that are launched for the same kernel for the same node of the same pipeline configuration as part of the same dispatch will belong to waves with the same wave size.

Note: Wave sizes can differ across target platforms, pipeline stages, and even different optimization choices made by a compiler.

Uniformity {#exec.uniformity}
----------

A <dfn>collective</dfn> operation is one that require multiple strands to coordinate.
A [=collective=] operation is only guaranteed to execute correctly when the required subset of strands all <dfn>participate</dfn> in the operation together.

### Tangle ### {#exec.uniformity.tangle}

Any strand begins execution of an entry point as part of a <dfn>tangle</dfn> of strands.
The [=tangle=] that a strand belongs to can change over the course of its execution.
When a strand executes a collective operation, it [=participates=] with those strands that are part of the same tangle.

When a strand executes a conditional control-flow operation, it branches to a destination that can depend on a condition value.
When the strands of a tangle execute a conditional control-flow operation, each strand in the tangle becomes part of a new tangle with exactly those strands that branch to the same destination.

A <dfn>control-flow region</dfn> is a pair of nodes (|E|, |M|) in the control-flow graph of a function, such that either:

* |E| dominates |M|
* |M| is unreachable

A node |N| in the control-flow graph of a function is inside the region (|E|, |M|) if |E| dominates |N| and |M| does not dominate |N|.

A <dfn>structured region</dfn> is a [=control-flow region=] that is significant to the Slang language semantics.

For each function body, there is a [=structured region=] (|Entry|, |Exit|) where |Entry| is the unique entry block of the function's control-flow graph, and |Exit| is a unique block dominated by all points where control flow can exit the function body.

Each conditional control-flow operation has a <dfn>merge point</dfn>,
and defines a structured region (|C|, |M|) where |C| is the control-flow operation and |M| is its [=merge point=].

A strand <dfn>breaks out of</dfn> a control-flow region (|E|, |M|) if it enters the region (by branching to |E|) and then subsequently exits the region by branching to some node |N|, distinct from |M|, that is not inside the region.

Note: We define the case where a strand [=breaks out of=] a region, but not the case where a strand exits a region normally.
The motivation for this choice is that a strand that goes into an infinite loop without exiting a region needs to be treated the same as a strand that exits that region normally.

When the strands in a tangle enter a structured control-flow region (|E|, |M|), all of the strands in the tangle that do not break out of that region form a new region at |M|.

### Dynamic Uniformity ### {#exec.uniformity.dynamic}

Uniformity must be defined relative to some granularity of grouping for strands: e.g., per-strand, per-wave, per-block, etc.

When the strands in a tangle evaluate some expression, we say that the result is dynamically per-|G| for some granularity of group |G|, if for any two strands in the tangle that are in the same |G|, those strands compute the same value for that expression.

We say that a tangle is executing code dynamically per-|G| uniform when for every |G|, either all of the strands in that |G| are in the tangle, or all of them are not in that tangle.

### Static Uniformity ### {#exec.uniformity.static}

A value in a Slang program (such as the result of evaluating an expression) is statically per-|G|, for some granularity of group |G|, if it can be proved, using the rules in this specification, that the value will always be dynamically per-|G| at runtime.

We say that control-flow is statically per-|G| uniform at some point in a program if it can be proved, using the rules in this specification, that at runtime any stand at that point would be part of a tangle that is per-|G| uniform.

TODO: Okay, now we actually need to write just such rules...



# GPUs # {#gpu}

## Dispatches ## {#gpu.dispatch}

Work is issued to a GPU device in the form of <dfn>commands</dfn>.
A <dfn>dispatch</dfn> is a [=command=] that causes a GPU device to execute a specific [=pipeline instance=].

A dispatch determines:

* The [=pipeline instance=] |P| to execute
* A value for each of the [=dispatch parameters=] of |P|
* A value for each of the [=uniform shader parameters=] of |P|

### Pipeline Instance ### {#exec.gpu.pipeline}

A <dfn>pipeline instance</dfn> is an instance of some [=pipeline type=], and consists of:

* A set of zero or more [=stage instances=]

* A [=bundle=]

The [=kernels=] of any [=programmable=] [=stage instances=] in a [=pipeline instance=] must be compatible with the [=bundle=] of the [=pipeline instance=].

#### Pipeline Types #### {#exec.gpu.pipeline.type}

A <dfn>pipeline type</dfn> is a category of workloads that a GPU can support.
Slang supports the following pipeline types:

* [=rasterization pipelines=]
* [=compute pipelines=]
* [=ray-tracing pipelines=]

Each [=pipeline type=] |PT| defines:

* Zero or more <dfn>dispatch parameters</dfn>, each having a name and a type

* A set of [=stage types=]

* A set of <dfn>associated record types</dfn>

* Validation rules for [=pipeline instances=] of type |PT|

### Stage Instances ### {#exec.gpu.pipeline.stage}

A <dfn>stage instance</dfn> is an instance of some [=stage type=] |ST|, and consists of:

* A [=kernel=] |K| for |ST|, if |ST| is [=programmable=].

* Values for each of the [=fixed-function parameters=] of |ST| that are not included in |K|

#### Stage Types #### {#exec.gpu.pipeline.stage.type}

A <dfn>stage type</dfn> is a type of stage that may appear in [=pipeline instances=].

Each [=stage type=] belongs to a single [=pipeline type=].

A [=stage type=] is either <dfn>programmable</dfn> or it is <dfn>fixed-function</dfn>.

A stage has zero or more <dfn>fixed-function parameters</dfn>, each having a name and a type

A [=stage type=] is either required, optional, or instanceable.

#### Signatures #### {#exec.gpu.pipeline.stage.signature}

The signature of a programmable stage consists of its uniform signature and its varying signature.

The uniform signature of a programmable stage is a sequence of types.

A programmable stage has a set of boundaries.
Each programmable stage has an input boundary and an output boundary.

The varying input signature of a programmable stage is its signature along its input boundary;
The varying output signature of a programmabel stage is its signature along its output boundary;

The varying signature of a programmable stage comprises the boundary signature of that stage along each of its boundaries.

To compute the signature of a stage |S| with a kernel based on a function |f|:

* Initialize the uniform signature of |S| to an empty sequence
* Initailize the boundary signature of |S| along each of its boundaries to an empty sequence
* If |f| has an implicit `this` parameter then:
  * Append the type of the `this` parameter to the uniform signature of |S|
* For each explicit parameter |p| of |f|:
  * If |p| is `uniform`, then:
    * Add the type of |p| to the uniform signature of |S|
  * Otherwise:
    * TODO: handling of semantics!
    * Add |p| to the varying signature of |S|
* Add the result type |R| to the varying output signature of |S|
  * TODO: need to handle semantics on |f| as semantics on the result...

The default way to add a parameter |p| to the varying signature of some stage |S| is:

* If the direction of |p| is `in` or `inout`, then add |p| to the varying input signature of |S|
* If the direction of |p| is `out` or `inout`, then add |p| to the varying output signature of |S|


### Records ### {#exec.gpu.pipeline.record}

A <dfn>record</dfn> is an instance of an [=associated record type=] of a [=pipeline type=].
Data is passed between the [=stage instances=] of a [=pipeline instance=] in the form of [=records=].

The varying input and output signature of a [=stage instance=] is defined with respect to the [=associated record types=] of the corresponding [=pipeline type=].

A [=stage instance=] depends on the [=associated record types=] that are part of its signature.
A [=pipeline instance=] depends on the [=associated record types=] that are part of its [=stage instances=].

A programmable stage has a set of boundaries.
Every programmable stage has an input boundary and an output boundary.

A record type signature is a sequence of pairs (|T|, |s|), where |T| is a type and |s| is a semantic.
The varying signature of a programmable stage along one of its boundaries is a record type signature.



For each [=associated record type=] |R| that a [=pipeline instance=] |P| depends on, if there are [=stage instances=] |A| and |B| in |P| such that |A| outputs |R| and |B| inputs |R|, then the configuration of |R| for |B| must be a prefix of the configuration of |A|.


#### Compute #### {#exec.gpu.pipeline.compute}

A <dfn>compute pipeline</dfn> instance is a [=pipeline instance=] with a single [=stage instance=] of [=stage type=] `compute`.
The `compute` [=stage type=] is [=programmable=].

A [=dispatch=] of a [=compute pipeline=] instance is a <dfn>compute dispatch</dfn>.
A [=compute dispatch=] invokes its kernel for each strand in a <dfn>block</dfn> of strands.
The number and organization of strands in a [=block=] is determined by a <dfn>block shape</dfn>.
A [=block shape=] comprises its rank |N|, a positive integer, and its extent, a positive integer, along each axis |i|, where 0 <= |i| < |N|.
Typical GPU platforms support block shapes with ranks up to 3.

An entry point for the `compute` stage may use a `[numthreads]` attribute to specify the block shape to be used by pipeline configurations using that entry point.

The strands in a block are executed concurrently.

Each block of strands that executes a compute entry point is part of a <dfn>grid</dfn> of blocks.
The number and organization of blocks in a [=grid=] is determined by a <dfn>grid shape</dfn>.
A [=grid shape=] comprises its rank |N|, a positive integer, and its extent, a positive integer, along each axis |i|, where 0 <= |i| < |N|.
Typical GPU platforms support grid shapes with ranks up to 3.

The blocks in a grid may be executed concurrently, but this is not guaranteed.

#### Rasterization #### {#exec.gpu.pipeline.raster}

A <dfn>rasterization pipeline</dfn> instance is a [=pipeline instance=].

##### Index Fetch ##### {#exec.gpu.pipeline.raster.stage.fetch.index}



##### Vertex Fetch ##### {#exec.gpu.pipeline.raster.stage.fetch.vertex}

Vertex fetch is a [=fixed-function=] stage.

This stage takes as input an `VertexIndex` record, and produces as output an `AssembledVertex` record.

* For each attribute of the `AssembledVertex` record, fetch data from the corresponding vertex stream, using either the instance ID or vertex ID (based on configuration).

##### Vertex Shader ##### {#exec.gpu.pipeline.raster.stage.vertex}

The `vertex` [=stage type=] is [=programmable=].

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

##### Primitive Assembly ##### {#exec.gpu.pipeline.raster.stage.primitive-assembly}

A primitive consists of a primitive topology and N vertices, where N matches the requirements of that primitive topology.

This stage takes as input coarse vertex records from a preceding stage.
It produces as output primitives of coarse vertex records.

##### Tessellation ##### {#exec.gpu.pipeline.raster.stage.tess}

###### Hull Shader ###### {#exec.gpu.pipeline.raster.stage.tess.hull}

This stage takes as input a patch primitive of coarse vertex records.
It produces as output a patch primitive of control point records a patch record.

###### Domain Shader ###### {#exec.gpu.pipeline.raster.stage.tess.domain}

This stage takes as input a patch primitive of control point records, and a patch record.
It outputs a fine vertex record.

##### Geometry Shader ##### {#exec.gpu.pipeline.raster.stage.geometry}

This stage takes as input a primitive of vertex records (either coarse or fine vertices, depending on what preceding stages are enabled).
As output, a geometry shader may have one or more output streams, each having a coresponding type of record.
For each output stream, a strand executing a geometry shader may output zero or more records of the corresponding type.

If one of the output streams of the geometry shader is connected to the rasterizer stage, then that output stream corresponds to raster vertex records.

##### Mesh Shading ##### {#exec.gpu.pipeline.raster.stage.mesh}

##### Rasterizer ##### {#exec.gpu.pipeline.raster.stage.rasterizer}

The rasterizer is a [=fixed-function=] stage.

This stage takes as input a primitive of raster vertex records, and determines which pixels in a render target that primitive covers.
The stage outputs zero or more raster fragment records, one for each covered pixel.

##### Depth/Stencil Test ##### {#exec.gpu.pipeline.raster.stage.depth-stencil-test}

##### Fragment Shader ##### {#exec.gpu.pipeline.raster.stage.fragment}

This stage takes as input a raster fragment record, and produces as output either:

* One `ShadedFragment` record
* One `ShadedFragment` record and N `ShadedFragment.Sample` records

##### Blend ##### {#exec.gpu.pipeline.raster.stage.blend}

This stage takes as input a `ShadedFragment` record (possibly including its `ShadedFragment.Sample`) and a `Pixel` record, and produces as output a `Pixel` record.

#### Ray Tracing #### {#exec.gpu.pipeline.ray-tracing}

TODO: define the stages of the <dfn>ray-tracing pipeline</dfn>.


Source and Binary Stability {#stability}
===========================

<div class="issue">
This section needs to define what it means for something to be _stable_ vs. <dfn>fragile</dfn>.
</div>