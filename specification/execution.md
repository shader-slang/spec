Memory {#memory}
======

Values of [=storable=] types may be stored into and loaded from memory.
A proper type |T| is <dfn>storable</dfn> if |T| conforms to `IStorable`.

Memory Locations {#memory.location}
----------------

Memory logically consists of a set of <dfn>memory locations</dfn>, each of which can hold an 8-bit byte.
Each memory location is part of one and only one <dfn>address space</dfn>.

Two sets of [=memory locations=] overlap if their intersection is non-empty.

Memory Accesses {#memory.access}
---------------

A <dfn>memory access</dfn> is an operation performed by a [=strand=] on a set of [=memory locations=] in a single [=address space=].
A [=memory access=] has a [=memory access mode=].

### Memory Access Modes ### {#memory.access.mode}

A <dfn>memory access mode</dfn> is one of: `read`, `write`, or `modify`.

Memory Model {#memory.model}
------------

<div class="issue">
We need to find an existing formal memory model to reference and use.
</div>

Layout {#SECTION.layout}
======

<div class="issue">
We clearly need a chapter on the guarantees Slang makes about memory layout.
</div>

Types in Slang do not necessarily prescribe a single <dfn>layout</dfn> in memory.
The discussion of each type will specify any guarantees about [=layout=] it provides; any details of layout not specified here may depend on the target platform, compiler options, and context in which a type is used.


Storage {#storage}
=======

Concrete Storage Locations {#storage.concrete}
--------------------------

A <dfn>concrete storage location</dfn> with layout *L* for storable type |T| comprises a set of contiguous [=memory locations=], in a single [=address space=], where a value of type |T| with layout *L* can be stored.

### Reference Types ### {#storage.concrete.type}

A <dfn>reference type</dfn> is written |m| `ref` |T| where |m| is a [=memory access mode=] and |T| is a storable type.

<div class="issue">
How do we get layout involved here?
</div>

#### Type Conversion #### {#storage.concrete.type.conversion}

An expression of reference type `modify` `ref` |T| can be implicitly coerced to type `read` `ref` |S| if |T| is subtype of |S|.

An expression of reference type `modify` `ref` |T| can be implicitly coerced to type `write` `ref` |S| if |S| is subtype of |T|.

An expression of reference type `read` `ref` |T| can be implicitly coerced to type |T|.

Abstract Storage Locations {#storage.abstract.location}
--------------------------

An <dfn>abstract storage location</dfn> is a logical place where a value of some proper type |T| can reside.

A [=concrete storage location=] is also an [=abstract storage location=].

Example: A local variable declaration like `var x : Int;` defines an [=abstract storage location=], and a reference to `x` will have the [=abstract storage reference type=] `read modify Int`.

Abstract Storage Access {#storage.abstract.access}
-----------------------

An <dfn>abstract storage access</dfn> is an operation performed by a [=strand=] on an [=abstract storage location=].
Each [=abstract storage access=] has an [=abstract storage access mode=].

Access Mode {#storage.abstract.access.mode}
------------

An <dfn>abstract storage access mode</dfn> is either `get`, `set`, or a [=memory access mode=].

Abstract Storage References {#storage.abstract.reference.type}
---------------------------

An <dfn>abstract storage reference type</dfn> is written |m| |T| where |T| is a proper type and |m| is a set of one or more [=abstract storage access modes=].

<div class="issue">
Some of the access types imply others, and it is inconvenient to have to write all explicitly in those cases.
For example:

* If you have `read` access, you can also perform a `get` (if the stored type is copyable).
* If you have `modify` access, you can also perform a `write`.
* If you hae `modify` or `write` access, you can also perform a `set` (if the stored type is copyable).

(Having `modify` access doesn't let you perform a `read` or `get`, because it implies the possibility of write-back which could in principle conflict with other accesses)

</div>

### Type Conversion ### {#storage.abstract.reference.type.conversion}

An expression with [=reference type=] `read` `ref` |T| can be implicitly coerced to an [=abstract storage reference type=] `read` |T|.

An expression with [=reference type=] `write` `ref` |T| can be implicitly coerced to an [=abstract storage reference type=] `write` |T|.

An expression with [=reference type=] `modify` `ref` |T| can be implicitly coerced to an [=abstract storage reference type=] `read write modify` |T|.

An expression with [=abstract storage reference type=] |a| |T| can be implicitly coerced to [=abstract storage reference type=] |b| |T| if |b| is a subset of |a|.

An expression with an abstract storage type |m| |T| can be implicitly coerced to an abstract storage type |m| |S| if all of the following are true:

* |S| is a subtype of |T| unless |m| does not contain any of `write`, `modify`, and `set`
* |T| is a subtype of |S| unless |m| does not contain any of `read`, `modify`, and `get`

Containment {#storage.location.contain}
-----------

An abstract storage location may contain other abstract storage locations.

Two [=abstract storage locations=] overlap if they are the same location, or one transitively contains the other.

An abstract storage location of an array type |T|`[`|N|`]` contains |N| storage locations of type |T|, one for each element of the array.

An abstract storage location of a `struct` type |S| contains a distinct storage location for each of the [=fields=] of |S|.


### Conflicts ### {#storage.access.conflict}

An [=abstract storage access=] performed by a strand begins at some point |b| in the execution of that strand, and ends at some point |e| in the execution of that strand.
The interval of an [=abstract storage access=] is the half-open interval [|b|, |e|).

The intervals [|a0|, |a1|) and [|b0|, |b1|) overlap if either:

* |a0| happens-before |b0| and |b0| happens-before |a1|
* |b0| happens-before |a0| and |a0| happens-before |b1|

Two [=abstract storage accesses=] |A| and |B| overlap if all of the following:

* The [=abstract storage location=] of |A| overlaps the [=abstract storage location=] of |B|
* The interval of |A| overlaps the interval of |B|

Two distinct [=abstract storage accesses=] |A| and |B| conflict if all of the following:

* |A| and |B| overlap
* At least one of the accesses is a `write`, `modify`, or `set`

Expressions That Reference Storage {#storage.expr}
----------------------------------

<div class="issue">
This text really belongs in the relevant sections about type-checking each of these expression forms.
</div>

Rather than evaluating to a value, of an expression may evaluate to an abstract storage location, along with restrictions on the kinds of access allowed to that location.
An expression that evaluates to an abstract storage location does not constitute an abstract storage access to that location.

Examples of expressions that evaluate to an abstract storage location include:

* An identifier expression that names some variable _v_

* A member-access expression |x|.|m| where |x| is an abstract storage location of some struct type |S| and |m| is a field of |S|

* A member-access expression |x|.|p| where |p| is a property

* A subscript exrpession |x|`[`|i|`]` that resolves to an invocation of a `subscript` declaration

Examples of expressions that perform an abstract storage access include:

* An assignment |dst| `=` |src| performs a write to |dst|. It also performs a read from |src| if |src| is an abstract storage location.

* A call `f(... a ... )` where argument `a` is an abstract storage location performs an abstract storage access based on the direction of the corresponding parameter:

  * An `in` parameter performs a read access that begins and ends before the strand enters the body of `f`

  * An `out` parameter begins a write access before the call begins, and ends it after the call returns. The abstract storage location `a` must have been uninitialized before the call, and will be initialized after the call.

  * An `inout` parameter begins a modify access before the call that ends after the call returns. The abstract storage location `a` must have been initialized before the call.

  * TODO: `ref` etc.

Program Lifecycle {#lifecycle}
=================

Compilation {#lifecyle.compilation}
-----------

A Slang <dfn>compiler</dfn> is a tool that is invoked on Slang source code to produce <dfn>object code</dfn>.

Object code produced by a Slang compiler from one toolchain may be incompatible with tools from other toolchains, other versions of the same toolchain, or across target platforms supported by the toolchain.

Note: This specification does not prescribe the language or format of object code that a particular toolchain implementation has to use.
Object code might use a toolchain-specific IR, a portable intermediate language, or a format that is compatible with another existing toolchain (e.g., the object code format used by a C toolchain on the target).

A [=compiler=] implementation must support being invoked on an entire Slang source module, potentially comprising multiple source units, to produce object code for that entire module.
A [=compiler=] implementation may support being invoked on source code at other granularities: e.g., on a subset of the source units of a module.

When compiling code that is part of a Slang module |M|, the output of a compiler implementation must not depend on any non-[=fragile=] information in the modules that |M| depends on.

Linking {#lifecycle.linking}
-------

A <dfn>static library</dfn> is a unit of code suitable for distribution or re-use.
Static libraries created by a toolchain should be usable with later versions of that same toolchain.

A <dfn>binary</dfn> is a unit of <dfn>loadable code</dfn> that is either an <dfn>executable</dfn> or a <dfn>dynamic library</dfn>.

Note: We need to refer to [=executables=] and [=dynamic libraries=] somewhere in the text.

A Slang <dfn>linker</dfn> is a tool that is invoked on one or more inputs, consisting of units of [=object code=] and [=static libraries=], to produce a [=static library=] or a [=binary=].

A binary may contain [=loadable code=] for zero or more Slang modules.

Note: it is possible that a linked binary might contain both code compiled from Slang as well as code generated from other languages, or by other tools.

It is invalid for a binary to contain code for non-[=fragile=] symbols from a Slang module |M| while also having external dependencies on symbols from |M|.
A [=linker=] may fail with an error rather than produce an invalid binary.

Note: In practice, a linked binary has to either contain all of a given Slang module, or none of it.
The nuance is that [=fragile=] symbols, such as inlinable functions, from a module |M| might get copied into object code for a module |N| that depends on |M|, and thus end up in a binary for |N|.

Loading {#lifecycle.loading}
-------

A Slang runtime must support <dfn>loading</dfn> [=binaries=] into a [=runtime session=], and resolving dependencies between them.

[=Loading=] of a binary containing definitions of non-fragile symbols from Slang module |M| must fail if any external symbol that |M| depends on has not already been loaded into the process.

[=Loading=] of a binary containing non-fragile symbols from module |M| may fail if any binary containing definition of non-fragile symbols from |M| has already been loaded into the process.

It is valid to load a binary containing fragile symbols from module |M| even if other binaries containing one or more of those symbols has already been loaded, and even if the definitions of those fragile symbols differ between the binaries.
References to fragile symbols may resolve at runtime to any definition of those symbols that was compiled into object code that made its way into the binaries that are loaded.

If Slang code is stored in a [=binary=] for a [=host=], then that code may be loaded as part of initialization of a [=process=] for a [=host=] [=executable=].

If a [=module=] of Slang code is loaded programmatically, a Slang runtime must return a [=mirror=] reflecting that module.

Runtime Reflection {#lifecyle.reflection}
------------------

A Slang runtime may support reflection of [=modules=] that have been loaded into a [=runtime session=].

A <dfn>mirror</dfn> is a runtime value that reflects some entity in a Slang codebase.
A [=mirror=] is created and managed by a [=runtime session=], and reflects entities in the code that has been loaded into that runtime session.
A [=mirror=] that reflects an |X| is also called an |X| [=mirror=].

Example: A [=module=] [=mirror=] is a [=mirror=] that reflects a [=module=].

A [=mirror=] may reflect:

* A module
* A declaration
* A reference to a declaration
* A type
* A value

A [=mirror=] is not the same as the entity it reflects.

Bundling {#lifecycle.bundling}
--------

<div class="issue">
This concept needs a proper name.
</div>

A <dfn>bundle</dfn> is a runtime entity composed from a sequence of distinct runtime entities where each element in the sequence is one of:

* A module
* An entry point (a fully specialized reference to an entry point declaration)
* A witness to conformance relationship of a type to an interface
* A bundle

A Slang runtime must support creation of a [=bundle=] from a sequence of [=mirrors=] reflecting the runtime entities to be bundled.

The entry points in a bundle are the entry points in the input sequence.

The modules in a bundle are the set of modules in the input sequence, the modules referenced by the entities in the input sequence, and the transitive closure of modules imported by those.

The global uniform shader parameters of a bundle are the global uniform shader parameters declared in modules in the bundle.

The entry point uniform shader parameters of a bundle are the entry-point uniform shader parameters declared by entry points in the bundle.

The shader parameters of a bundle are the global uniform shader parameters of the bundle and the entry-point uniform shader parameters of the bundle.

A <dfn>kernel</dfn> is a runtime entity created from a bundle, an entry point in that bundle, and a target device.

A kernel created from a bundle |B| is compatible with kernels created from a bundle |BX| where |BX| was created from an input sequence that started with |B|.

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