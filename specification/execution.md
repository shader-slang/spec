# Memory  [memory]

Values of  *storable* types may be stored into and loaded from memory.
A proper type _T_ is  **storable** if _T_ conforms to `IStorable`.

## Memory Locations  [memory.location]

Memory logically consists of a set of  **memory locations**, each of which can hold an 8-bit byte.
Each memory location is part of one and only one  **address space**.

Two sets of  *memory locations* overlap if their intersection is non-empty.

## Memory Accesses  [memory.access]

A  **memory access** is an operation performed by a  *strand* on a set of  *memory locations* in a single  *address space*.
A  *memory access* has a  *memory access mode*.

### Memory Access Modes  [memory.access.mode]

A  **memory access mode** is one of: `read`, `write`, or `modify`.

## Memory Model  [memory.model]

<div class="issue">
We need to find an existing formal memory model to reference and use.
</div>

# Layout  [SECTION.layout]

<div class="issue">
We clearly need a chapter on the guarantees Slang makes about memory layout.
</div>

Types in Slang do not necessarily prescribe a single  **layout** in memory.
The discussion of each type will specify any guarantees about  *layout* it provides; any details of layout not specified here may depend on the target platform, compiler options, and context in which a type is used.


# Storage  [storage]

## Concrete Storage Locations  [storage.concrete]

A  **concrete storage location** with layout *L* for storable type _T_ comprises a set of contiguous  *memory locations*, in a single  *address space*, where a value of type _T_ with layout *L* can be stored.

### Reference Types  [storage.concrete.type]

A  **reference type** is written _m_ `ref` _T_ where _m_ is a  *memory access mode* and _T_ is a storable type.

<div class="issue">
How do we get layout involved here?
</div>

#### Type Conversion  [storage.concrete.type.conversion]

An expression of reference type `modify` `ref` _T_ can be implicitly coerced to type `read` `ref` _S_ if _T_ is subtype of _S_.

An expression of reference type `modify` `ref` _T_ can be implicitly coerced to type `write` `ref` _S_ if _S_ is subtype of _T_.

An expression of reference type `read` `ref` _T_ can be implicitly coerced to type _T_.

## Abstract Storage Locations  [storage.abstract.location]

An  **abstract storage location** is a logical place where a value of some proper type _T_ can reside.

A  *concrete storage location* is also an  *abstract storage location*.

Example: A local variable declaration like `var x : Int;` defines an  *abstract storage location*, and a reference to `x` will have the  *abstract storage reference type* `read modify Int`.

Abstract Storage Access  [storage.abstract.access]
-----------------------

An  **abstract storage access** is an operation performed by a  *strand* on an  *abstract storage location*.
Each  *abstract storage access* has an  *abstract storage access mode*.

Access Mode  [storage.abstract.access.mode]
-----------

An  **abstract storage access mode** is either `get`, `set`, or a  *memory access mode*.

Abstract Storage References  [storage.abstract.reference.type]
---------------------------

An  **abstract storage reference type** is written _m_ _T_ where _T_ is a proper type and _m_ is a set of one or more  *abstract storage access modes*.


> ###### Issue ######
>
> Some of the access types imply others, and it is inconvenient to have to write all explicitly in those cases.
> For example:
> 
> * If you have `read` access, you can also perform a `get` (if the stored type is copyable).
> * If you have `modify` access, you can also perform a `write`.
> * If you hae `modify` or `write` access, you can also perform a `set` (if the stored type is copyable).
> 
> (Having `modify` access doesn't let you perform a `read` or `get`, because it implies the possibility of write-back which could in principle conflict with > other accesses)

Type Conversion  [storage.abstract.reference.type.conversion]
---------------

An expression with  *reference type* `read` `ref` _T_ can be implicitly coerced to an  *abstract storage reference type* `read` _T_.

An expression with  *reference type* `write` `ref` _T_ can be implicitly coerced to an  *abstract storage reference type* `write` _T_.

An expression with  *reference type* `modify` `ref` _T_ can be implicitly coerced to an  *abstract storage reference type* `read write modify` _T_.

An expression with  *abstract storage reference type* _a_ _T_ can be implicitly coerced to  *abstract storage reference type* _b_ _T_ if _b_ is a subset of _a_.

An expression with an abstract storage type _m_ _T_ can be implicitly coerced to an abstract storage type _m_ _S_ if all of the following are true:

* _S_ is a subtype of _T_ unless _m_ does not contain any of `write`, `modify`, and `set`
* _T_ is a subtype of _S_ unless _m_ does not contain any of `read`, `modify`, and `get`

## Containment  [storage.location.contain]

An abstract storage location may contain other abstract storage locations.

Two  *abstract storage locations* overlap if they are the same location, or one transitively contains the other.

An abstract storage location of an array type _T_`[`_N_`]` contains _N_ storage locations of type _T_, one for each element of the array.

An abstract storage location of a `struct` type _S_ contains a distinct storage location for each of the  *fields* of _S_.


### Conflicts  [storage.access.conflict]

An  *abstract storage access* performed by a strand begins at some point _b_ in the execution of that strand, and ends at some point _e_ in the execution of that strand.
The interval of an  *abstract storage access* is the half-open interval [_b_, _e_).

The intervals [|a0|, |a1|) and [|b0|, |b1|) overlap if either:

* |a0| happens-before |b0| and |b0| happens-before |a1|
* |b0| happens-before |a0| and |a0| happens-before |b1|

Two  *abstract storage accesses* _A_ and _B_ overlap if all of the following:

* The  *abstract storage location* of _A_ overlaps the  *abstract storage location* of _B_
* The interval of _A_ overlaps the interval of _B_

Two distinct  *abstract storage accesses* _A_ and _B_ conflict if all of the following:

* _A_ and _B_ overlap
* At least one of the accesses is a `write`, `modify`, or `set`

## Expressions That Reference Storage  [storage.expr]

<div class="issue">
This text really belongs in the relevant sections about type-checking each of these expression forms.
</div>

Rather than evaluating to a value, of an expression may evaluate to an abstract storage location, along with restrictions on the kinds of access allowed to that location.
An expression that evaluates to an abstract storage location does not constitute an abstract storage access to that location.

Examples of expressions that evaluate to an abstract storage location include:

* An identifier expression that names some variable _v_

* A member-access expression _x_._m_ where _x_ is an abstract storage location of some struct type _S_ and _m_ is a field of _S_

* A member-access expression _x_._p_ where _p_ is a property

* A subscript exrpession _x_`[`_i_`]` that resolves to an invocation of a `subscript` declaration

Examples of expressions that perform an abstract storage access include:

* An assignment _dst_ `=` _src_ performs a write to _dst_. It also performs a read from _src_ if _src_ is an abstract storage location.

* A call `f(... a ... )` where argument `a` is an abstract storage location performs an abstract storage access based on the direction of the corresponding parameter:

  * An `in` parameter performs a read access that begins and ends before the strand enters the body of `f`

  * An `out` parameter begins a write access before the call begins, and ends it after the call returns. The abstract storage location `a` must have been uninitialized before the call, and will be initialized after the call.

  * An `inout` parameter begins a modify access before the call that ends after the call returns. The abstract storage location `a` must have been initialized before the call.

  * TODO: `ref` etc.

# Program Lifecycle  [lifecycle]

## Compilation  [lifecyle.compilation]

A Slang  **compiler** is a tool that is invoked on Slang source code to produce  **object code**.

Object code produced by a Slang compiler from one toolchain may be incompatible with tools from other toolchains, other versions of the same toolchain, or across target platforms supported by the toolchain.

Note: This specification does not prescribe the language or format of object code that a particular toolchain implementation has to use.
Object code might use a toolchain-specific IR, a portable intermediate language, or a format that is compatible with another existing toolchain (e.g., the object code format used by a C toolchain on the target).

A  *compiler* implementation must support being invoked on an entire Slang source module, potentially comprising multiple source units, to produce object code for that entire module.
A  *compiler* implementation may support being invoked on source code at other granularities: e.g., on a subset of the source units of a module.

When compiling code that is part of a Slang module _M_, the output of a compiler implementation must not depend on any non- *fragile* information in the modules that _M_ depends on.

## Linking  [lifecycle.linking]

A  **static library** is a unit of code suitable for distribution or re-use.
Static libraries created by a toolchain should be usable with later versions of that same toolchain.

A  **binary** is a unit of  **loadable code** that is either an  **executable** or a  **dynamic library**.

Note: We need to refer to  *executables* and  *dynamic libraries* somewhere in the text.

A Slang  **linker** is a tool that is invoked on one or more inputs, consisting of units of  *object code* and  *static libraries*, to produce a  *static library* or a  *binary*.

A binary may contain  *loadable code* for zero or more Slang modules.

Note: it is possible that a linked binary might contain both code compiled from Slang as well as code generated from other languages, or by other tools.

It is invalid for a binary to contain code for non- *fragile* symbols from a Slang module _M_ while also having external dependencies on symbols from _M_.
A  *linker* may fail with an error rather than produce an invalid binary.

Note: In practice, a linked binary has to either contain all of a given Slang module, or none of it.
The nuance is that  *fragile* symbols, such as inlinable functions, from a module _M_ might get copied into object code for a module _N_ that depends on _M_, and thus end up in a binary for _N_.

## Loading  [lifecycle.loading]

A Slang runtime must support  **loading**  *binaries* into a  *runtime session*, and resolving dependencies between them.

 *Loading* of a binary containing definitions of non-fragile symbols from Slang module _M_ must fail if any external symbol that _M_ depends on has not already been loaded into the process.

 *Loading* of a binary containing non-fragile symbols from module _M_ may fail if any binary containing definition of non-fragile symbols from _M_ has already been loaded into the process.

It is valid to load a binary containing fragile symbols from module _M_ even if other binaries containing one or more of those symbols has already been loaded, and even if the definitions of those fragile symbols differ between the binaries.
References to fragile symbols may resolve at runtime to any definition of those symbols that was compiled into object code that made its way into the binaries that are loaded.

If Slang code is stored in a  *binary* for a  *host*, then that code may be loaded as part of initialization of a  *process* for a  *host*  *executable*.

If a  *module* of Slang code is loaded programmatically, a Slang runtime must return a  *mirror* reflecting that module.

## Runtime Reflection  [lifecyle.reflection]

A Slang runtime may support reflection of  *modules* that have been loaded into a  *runtime session*.

A  **mirror** is a runtime value that reflects some entity in a Slang codebase.
A  *mirror* is created and managed by a  *runtime session*, and reflects entities in the code that has been loaded into that runtime session.
A  *mirror* that reflects an _X_ is also called an _X_  *mirror*.

Example: A  *module*  *mirror* is a  *mirror* that reflects a  *module*.

A  *mirror* may reflect:

* A module
* A declaration
* A reference to a declaration
* A type
* A value

A  *mirror* is not the same as the entity it reflects.

## Bundling  [lifecycle.bundling]

<div class="issue">
This concept needs a proper name.
</div>

A  **bundle** is a runtime entity composed from a sequence of distinct runtime entities where each element in the sequence is one of:

* A module
* An entry point (a fully specialized reference to an entry point declaration)
* A witness to conformance relationship of a type to an interface
* A bundle

A Slang runtime must support creation of a  *bundle* from a sequence of  *mirrors* reflecting the runtime entities to be bundled.

The entry points in a bundle are the entry points in the input sequence.

The modules in a bundle are the set of modules in the input sequence, the modules referenced by the entities in the input sequence, and the transitive closure of modules imported by those.

The global uniform shader parameters of a bundle are the global uniform shader parameters declared in modules in the bundle.

The entry point uniform shader parameters of a bundle are the entry-point uniform shader parameters declared by entry points in the bundle.

The shader parameters of a bundle are the global uniform shader parameters of the bundle and the entry-point uniform shader parameters of the bundle.

A  **kernel** is a runtime entity created from a bundle, an entry point in that bundle, and a target device.

A kernel created from a bundle _B_ is compatible with kernels created from a bundle _BX_ where _BX_ was created from an input sequence that started with _B_.

# Execution  [exec]

A  **runtime session** is a context for loading and execution of Slang code.
A  *runtime session* exists within the context of a  **process** running on some  **host** machine.
For some implementations, a  *runtime session* may be the same as a  *process*, but this is not required.

A  *runtime session* has access to one or more distinct  **devices** on which work may be performed.
Different  *devices* in a  *runtime session* may implement different  **architectures**, each having its own machine code format(s).
For some implementations, the  *host* may also be a  *device*, but this is not required.

<div class="issue">
We need to define what it means to "execute" statements and to "evaluate" expressions...
</div>

When a strand invokes an invocable entity _f_, it executes the body of _f_ (a statement).
As part of executing a statement, a strand may execute other statements, and evaluate expressions.
A strand evaluates an expression to yield a value, and also for any side effects that may occur.

## Strands  [exec.strand]

A  **strand** is a logical runtime entity that executes Slang code.
The state of a strand consists of a stack of  *activation records*, representing invocations that the strand has entered but not yet exited.

A strand may be realized in different ways by different devices, runtime systems, and compilation strategies.

Note: The term "strand" was chosen because a term like "thread" is both overloaded and charged.
On a typical CPU  *architecture*, a strand might map to a thread, or it might map to a single SIMD lane, depending on how code is compiled.
On a typical GPU  *architecture*, a strand might map to a thread, or it might map to a wave, thread block, or other granularity.

Note: An implementation is allowed to "migrate" a strand from one thread to another.

A strand is  **launched** for some  *invocable* declaration _D_, with an initial stack comprising a single activation record for _D_, a

## Activation Records  [exec.activation]

An  **activation record** represents the state of a single invocation of some  *invocable* declaration by some strand.
An  *activation record* for  *invocable* declaration _D_ by strand _S_ consists of:

* A value for each parameter of _D_

* The location _L_ within the  *body* of _D_ that _S_'s execution has reached for that invocation

* A value for each local variable of _D_ that is in scope at _L_

## Waves  [exec.wave]

A  **wave** is a set of one or more  *strands* that execute concurrently.
At each point in its execution, a strand belongs to one and only one  *wave*.

Waves are guaranteed to make forward progress independent of other waves.
Strands that belong to the same wave are not guaranteed to make independent forward progress.

Note: A runtime system can execute the strands of a wave in "lock-step" fashion, if it chooses.

Strands that are  *launched* to execute a  *kernel* as part of a  *dispatch* will only ever be in the same wave as strands that were launched as part of the same  *dispatch*.

Every  *wave* _W_ has an integer  **wave size** _N_ > 0.
Every strand that belongs to _W_ has an integer  **lane ID** _i_, with 0 <= _i_ < _N_.
Distinct strands in _W_ have distinct  *lane IDs*.

Note: A wave with  *wave size* _N_ can have at most _N_ strands that belong to it, but it can also have fewer.
This might occur because a partially-full wave was launched, or because strands in the wave terminated.
If strands in a wave have terminated, it is possible that there will be gaps in the sequence of used lane IDs.

Two strands that are launched for the same kernel for the same node of the same pipeline configuration as part of the same dispatch will belong to waves with the same wave size.

Note: Wave sizes can differ across target platforms, pipeline stages, and even different optimization choices made by a compiler.

## Uniformity  [exec.uniformity]

A  **collective** operation is one that require multiple strands to coordinate.
A  *collective* operation is only guaranteed to execute correctly when the required subset of strands all  **participate** in the operation together.

### Tangle  [exec.uniformity.tangle]

Any strand begins execution of an entry point as part of a  **tangle** of strands.
The  *tangle* that a strand belongs to can change over the course of its execution.
When a strand executes a collective operation, it  *participates* with those strands that are part of the same tangle.

When a strand executes a conditional control-flow operation, it branches to a destination that can depend on a condition value.
When the strands of a tangle execute a conditional control-flow operation, each strand in the tangle becomes part of a new tangle with exactly those strands that branch to the same destination.

A  **control-flow region** is a pair of nodes (_E_, _M_) in the control-flow graph of a function, such that either:

* _E_ dominates _M_
* _M_ is unreachable

A node _N_ in the control-flow graph of a function is inside the region (_E_, _M_) if _E_ dominates _N_ and _M_ does not dominate _N_.

A  **structured region** is a  *control-flow region* that is significant to the Slang language semantics.

For each function body, there is a  *structured region* (|Entry|, _Exit_) where _Entry_ is the unique entry block of the function's control-flow graph, and _Exit_ is a unique block dominated by all points where control flow can exit the function body.

Each conditional control-flow operation has a  **merge point**,
and defines a structured region (_C_, _M_) where _C_ is the control-flow operation and _M_ is its  *merge point*.

A strand  **breaks out of** a control-flow region (_E_, _M_) if it enters the region (by branching to _E_) and then subsequently exits the region by branching to some node _N_, distinct from _M_, that is not inside the region.

Note: We define the case where a strand  *breaks out of* a region, but not the case where a strand exits a region normally.
The motivation for this choice is that a strand that goes into an infinite loop without exiting a region needs to be treated the same as a strand that exits that region normally.

When the strands in a tangle enter a structured control-flow region (_E_, _M_), all of the strands in the tangle that do not break out of that region form a new region at _M_.

### Dynamic Uniformity  [exec.uniformity.dynamic]

Uniformity must be defined relative to some granularity of grouping for strands: e.g., per-strand, per-wave, per-block, etc.

When the strands in a tangle evaluate some expression, we say that the result is dynamically per-_G_ for some granularity of group _G_, if for any two strands in the tangle that are in the same _G_, those strands compute the same value for that expression.

We say that a tangle is executing code dynamically per-_G_ uniform when for every _G_, either all of the strands in that _G_ are in the tangle, or all of them are not in that tangle.

### Static Uniformity  [exec.uniformity.static]

A value in a Slang program (such as the result of evaluating an expression) is statically per-_G_, for some granularity of group _G_, if it can be proved, using the rules in this specification, that the value will always be dynamically per-_G_ at runtime.

We say that control-flow is statically per-_G_ uniform at some point in a program if it can be proved, using the rules in this specification, that at runtime any stand at that point would be part of a tangle that is per-_G_ uniform.

TODO: Okay, now we actually need to write just such rules...



# GPUs  [gpu]

## Dispatches  [gpu.dispatch]

Work is issued to a GPU device in the form of  **commands**.
A  **dispatch** is a  *command* that causes a GPU device to execute a specific  *pipeline instance*.

A dispatch determines:

* The  *pipeline instance* _P_ to execute
* A value for each of the  *dispatch parameters* of _P_
* A value for each of the  *uniform shader parameters* of _P_

### Pipeline Instance  [exec.gpu.pipeline]

A  **pipeline instance** is an instance of some  *pipeline type*, and consists of:

* A set of zero or more  *stage instances*

* A  *bundle*

The  *kernels* of any  *programmable*  *stage instances* in a  *pipeline instance* must be compatible with the  *bundle* of the  *pipeline instance*.

#### Pipeline Types  [exec.gpu.pipeline.type]

A  **pipeline type** is a category of workloads that a GPU can support.
Slang supports the following pipeline types:

*  *rasterization pipelines*
*  *compute pipelines*
*  *ray-tracing pipelines*

Each  *pipeline type* _PT_ defines:

* Zero or more  **dispatch parameters**, each having a name and a type

* A set of  *stage types*

* A set of  **associated record types**

* Validation rules for  *pipeline instances* of type _PT_

### Stage Instances  [exec.gpu.pipeline.stage]

A  **stage instance** is an instance of some  *stage type* _ST_, and consists of:

* A  *kernel* _K_ for _ST_, if _ST_ is  *programmable*.

* Values for each of the  *fixed-function parameters* of _ST_ that are not included in _K_

#### Stage Types  [exec.gpu.pipeline.stage.type]

A  **stage type** is a type of stage that may appear in  *pipeline instances*.

Each  *stage type* belongs to a single  *pipeline type*.

A  *stage type* is either  **programmable** or it is  **fixed-function**.

A stage has zero or more  **fixed-function parameters**, each having a name and a type

A  *stage type* is either required, optional, or instanceable.

#### Signatures  [exec.gpu.pipeline.stage.signature]

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


### Records  [exec.gpu.pipeline.record]

A  **record** is an instance of an  *associated record type* of a  *pipeline type*.
Data is passed between the  *stage instances* of a  *pipeline instance* in the form of  *records*.

The varying input and output signature of a  *stage instance* is defined with respect to the  *associated record types* of the corresponding  *pipeline type*.

A  *stage instance* depends on the  *associated record types* that are part of its signature.
A  *pipeline instance* depends on the  *associated record types* that are part of its  *stage instances*.

A programmable stage has a set of boundaries.
Every programmable stage has an input boundary and an output boundary.

A record type signature is a sequence of pairs (_T_, _s_), where _T_ is a type and _s_ is a semantic.
The varying signature of a programmable stage along one of its boundaries is a record type signature.



For each  *associated record type* _R_ that a  *pipeline instance* _P_ depends on, if there are  *stage instances* _A_ and _B_ in _P_ such that _A_ outputs _R_ and _B_ inputs _R_, then the configuration of _R_ for _B_ must be a prefix of the configuration of _A_.


#### Compute  [exec.gpu.pipeline.compute]

A  **compute pipeline** instance is a  *pipeline instance* with a single  *stage instance* of  *stage type* `compute`.
The `compute`  *stage type* is  *programmable*.

A  *dispatch* of a  *compute pipeline* instance is a  **compute dispatch**.
A  *compute dispatch* invokes its kernel for each strand in a  **block** of strands.
The number and organization of strands in a  *block* is determined by a  **block shape**.
A  *block shape* comprises its rank _N_, a positive integer, and its extent, a positive integer, along each axis _i_, where 0 <= _i_ < _N_.
Typical GPU platforms support block shapes with ranks up to 3.

An entry point for the `compute` stage may use a `[numthreads]` attribute to specify the block shape to be used by pipeline configurations using that entry point.

The strands in a block are executed concurrently.

Each block of strands that executes a compute entry point is part of a  **grid** of blocks.
The number and organization of blocks in a  *grid* is determined by a  **grid shape**.
A  *grid shape* comprises its rank _N_, a positive integer, and its extent, a positive integer, along each axis _i_, where 0 <= _i_ < _N_.
Typical GPU platforms support grid shapes with ranks up to 3.

The blocks in a grid may be executed concurrently, but this is not guaranteed.

#### Rasterization  [exec.gpu.pipeline.raster]

A  **rasterization pipeline** instance is a  *pipeline instance*.

##### Index Fetch  [exec.gpu.pipeline.raster.stage.fetch.index]



##### Vertex Fetch  [exec.gpu.pipeline.raster.stage.fetch.vertex]

Vertex fetch is a  *fixed-function* stage.

This stage takes as input an `VertexIndex` record, and produces as output an `AssembledVertex` record.

* For each attribute of the `AssembledVertex` record, fetch data from the corresponding vertex stream, using either the instance ID or vertex ID (based on configuration).

##### Vertex Shader  [exec.gpu.pipeline.raster.stage.vertex]

The `vertex`  *stage type* is  *programmable*.

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

##### Primitive Assembly  [exec.gpu.pipeline.raster.stage.primitive-assembly]

A primitive consists of a primitive topology and N vertices, where N matches the requirements of that primitive topology.

This stage takes as input coarse vertex records from a preceding stage.
It produces as output primitives of coarse vertex records.

##### Tessellation  [exec.gpu.pipeline.raster.stage.tess]

###### Hull Shader  [exec.gpu.pipeline.raster.stage.tess.hull]

This stage takes as input a patch primitive of coarse vertex records.
It produces as output a patch primitive of control point records a patch record.

###### Domain Shader  [exec.gpu.pipeline.raster.stage.tess.domain]

This stage takes as input a patch primitive of control point records, and a patch record.
It outputs a fine vertex record.

##### Geometry Shader  [exec.gpu.pipeline.raster.stage.geometry]

This stage takes as input a primitive of vertex records (either coarse or fine vertices, depending on what preceding stages are enabled).
As output, a geometry shader may have one or more output streams, each having a coresponding type of record.
For each output stream, a strand executing a geometry shader may output zero or more records of the corresponding type.

If one of the output streams of the geometry shader is connected to the rasterizer stage, then that output stream corresponds to raster vertex records.

##### Mesh Shading  [exec.gpu.pipeline.raster.stage.mesh]

##### Rasterizer  [exec.gpu.pipeline.raster.stage.rasterizer]

The rasterizer is a  *fixed-function* stage.

This stage takes as input a primitive of raster vertex records, and determines which pixels in a render target that primitive covers.
The stage outputs zero or more raster fragment records, one for each covered pixel.

##### Depth/Stencil Test  [exec.gpu.pipeline.raster.stage.depth-stencil-test]

##### Fragment Shader  [exec.gpu.pipeline.raster.stage.fragment]

This stage takes as input a raster fragment record, and produces as output either:

* One `ShadedFragment` record
* One `ShadedFragment` record and N `ShadedFragment.Sample` records

##### Blend  [exec.gpu.pipeline.raster.stage.blend]

This stage takes as input a `ShadedFragment` record (possibly including its `ShadedFragment.Sample`) and a `Pixel` record, and produces as output a `Pixel` record.

#### Ray Tracing  [exec.gpu.pipeline.ray-tracing]

TODO: define the stages of the  **ray-tracing pipeline**.


# Source and Binary Stability  [stability]

<div class="issue">
This section needs to define what it means for something to be _stable_ vs.  **fragile**.
</div>