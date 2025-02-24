Memory {#mem}
======

Abstract Storage {#storage.abstract}
-------

An <dfn>abstract storage location</dfn> of some type |T| is a logical place where a value of type |T| can reside.

The content of an abstract storage location can either be in an initialized or uninitialized state.

Two [=abstract storage locations=] may overlap, or be disjoint.

An abstract storage location may contain other abstract storage locations, all of which is overlaps.
An abstract storage location of an array type |T|`[`|N|`]` contains |N| storage locations of type |T|, one for each element of the array, each disjoint from the others.
An abstract storage location of a struct type contains a distinct storage location for each of its [=fields=], disjoint from the others.

An abstract storage access is an operation performed by a [=strand=] that may read or write the contents of an abstract storage location.
Each abstract storage access may be a `read`, a `write`, or a `modify`.

An abstract storage access has some duration: there is a point in the execution of a strand where the access begins, and some later point where the access ends.

It is an error if there exist two abstract storage accesses |A| and |B| where all of the following are true:

* The locations accessed by |A| and |B| overlap
* One of the accesses begins after the other begins, but before it ends.
* At least one of the accesses is a `write` or `modify`

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

### Types of Abstract Storage Locations {#storage.abstract.types}

The following are the types of abstract storage locations:

* `read write ref` |T|: A [=concrete storage location=] of type |T|, which can be accessed via read or write operations.

* `write ref` |T|: A [=concrete storage location=] of type |T| which can be accessed only via read operations
* `read ref` |T|: A ...

* `read write` |T|: Abstract storage, read/write
* `write` |T|: Abstract storage, write-only
* `read` |T|: Abstract storage, read-only

An abstract storage location with any of `read`, `write`, `ref` access can be implicitly converted to one with fewer access modifiers.

Note: an abstract storage location type always has at least one access modifier; otherwise it would just be an ordinary value.

An abstract storage location that includes `read` access can be implicitly converted to a value of type |T|.


Concrete Storage {#storage.concrete}
----------------

Memory logically consists of a set of <dfn>memory locations</dfn>, each of which can hold an 8-bit byte.
Each memory location is part of one and only one <dfn>address space</dfn>.

A <dfn>concrete storage location</dfn> with layout _L_ for type |T| is an abstract storage location of type |T| that comprises a set of contiguous [=memory locations=], in a single [=address space=].

Values of types that conform to `IStorable` may be stored into and loaded from memory.

A <dfn>memory access</dfn> is an operation on a set of memory locations in a single address space, which may be either a read, a write, or both.
A [=memory access=] is performed by a single strand.


* Memory model
  * Memory locations
  * Address space
  * Memory model reference
  * "Abstract storage" vs "concrete storage"




Execution Model {#exec}
===============

Program Lifecycle {#exec.lifecycle}
-----------------

### Compilation ### {#exec.lifecyle.compilation}

A Slang <dfn>compiler</dfn> is a tool that is invoked on Slang source code to produce <dfn>object code</dfn>.

Object code produced by a Slang compiler from one toolchain need not be compatible with tools from other toolchains, other versions of the same toolchain, or across target platforms supported by the toolchain.

Note: This specification does not prescribe the language or format of object code that a particular toolchain implementation has to use.
Object code might use a toolchain-specific IR, a portable intermediate language, or a format that is compatible with another existing toolchain (e.g., the object code format used by a C toolchain on the target).

A [=compiler=] implementation must support being invoked on all of the source units that comprise a single Slang module, to produce object code for that entire module.
A [=compiler=] implementation may support being invoked on source code at other granularities: e.g., on a subset of the source units of a module.

When compiling code that is part of a Slang module |M|, the output of a compiler implementation must not depend on any non-[=fragile=] information in the modules that |M| depends on.

### Linking ### {#exec.lifecycle.linking}

A <dfn>static library</dfn> is a unit of code suitable for distribution or re-use.
Unlike object code, a static library created by a toolchain must be compatible with later versions of that same toolchain (TODO: nuance).

A <dfn>binary</dfn> is a unit of <dfn>machine code</dfn> that is either an <dfn>executable</dfn> or a <dfn>dynamic library</dfn>.

Note: We need to refer to [=executables=] and [=dynamic libraries=] somewhere in the text.

A Slang <dfn>linker</dfn> is a tool that is invoked on one or more inputs, consisting of units of [=object code=] and [=static libraries=], to produce a [=static library=] or a [=binary=].

A binary may contain [=machine code=] for zero or more Slang modules.

Note: it is possible that a linked binary might contain both code compiled from Slang as well as code generated from other languages, or by other tools.

It is invalid for a binary to contain code for non-[=fragile=] symbols from a Slang module |M| while also having external dependencies on symbols from |M|.
A [=linker=] may fail with an error rather than produce an invalid binary.

Note: In practice, a linked binary has to either contain all of a given Slang module, or none of it.
The nuance is that [=fragile=] symbols, such as inlinable functions, from a module |M| might get copied into object code for a module |N| that depends on |M|, and thus end up in a binary for |N|.



### Loading ### {#exec.lifecycle.loading}


A runtime system for Slang supports <dfn>loading</dfn> [=binaries=] into a [=process=], and resolving dependencies between them.
[=Loading=] of a binary containing definitions of non-fragile symbols from Slang module |M| must fail if any external symbol that |M| depends on has not already been loaded into the process.

[=Loading=] of a binary containing non-fragile symbols from module |M| may fail if any binary containing definition of non-fragile symbols from |M| has already been loaded into the process.

It is valid to load a binary containing fragile symbols from module |M| even if other binaries containing one or more of those symbols has already been loaded, and even if the definitions of those fragile symbols differ between the binaries.
References to fragile symbols may resolve at runtime to any definition of those symbols that was compiled into object code that made its way into the binaries that are loaded.

Execution {#exec.execution}
---------

An [=executable=] that contains Slang code is loaded and executed in the context of a <dfn>process</dfn>.
A process has access to one or more distinct <dfn>devices</dfn> on which some or all of the program's code may run.
The different [=devices=] in a process may implement different <dfn>architectures</dfn>, each having its own machine code format(s).

A <dfn>host</dfn> is a device that can execute general-purpose code, including code that coordinates the execution of other devices.

### Strands ### {#exec.strand}

A <dfn>strand</dfn> is a logical runtime entity that executes code in Slang or other languages.
The state of a strand includes:

* A <dfn>stack</dfn> of <dfn>activation records</dfn> for invocations of functions (TODO: callables?) that the strand has entered but not yet exited.

* A location within the code of the top-most [=activation record=] on the [=stack=], indicating what the strand will execute next.

A strand may be realized in different ways by different devices, runtime systems, and compilation strategies.

Note: The term "strand" was chosen because a term like "thread" is both overloaded and charged.
On a typical CPU [=architecture=], a strand might map to a thread, or it might map to a single SIMD lane, depending on how code is compiled.
On a typical GPU [=architecture=], a strand might map to a thread, or it might map to a wave, thread block, or other granularity.

### Waves ### {#exec.wave}

Every strand is part of some group called a <dfn>wave</dfn>.
Every strand belongs to one and only one [=wave=], for the duration of its execution.

A wave may comprise one or more strands.
The granularity of waves may differ across target platforms, pipeline stages, and even different optimization choices made by a compiler.
The same Slang code may be executed by the same processor in a single process with different wave sizes.

Strands within the same wave are not guaranteed to make independent forward progress.
For example, an implementation might choose to execute code in a "lock-step" fashion for the strands of a wave.

Waves are guaranteed to make independent forward progress.

### GPUs ### {#exec.gpu}

#### Pipelines ### {#exec.gpu.pipeline}

A GPU always executes program code in the context of a <dfn>pipeline configuration</dfn> that is based on some <dfn>pipeline</dfn>.
Examples of pipelines include rasterization, compute, and ray-tracing.

Descriptively, a [=pipeline configuration=] is as a directed graph of nodes, and a [=pipeline=] defines the constraints on valid configurations of that pipeline.

A pipeline defines a set of <dfn>stages</dfn> in which work for that pipeline can be executed.
Each node in a pipeline configuration is based on one of the [=stages=] of the corresponding pipeline.

A stage in a pipeline may define some amount of <dfn>fixed-function state</dfn> that must be set on each node based on that stage.
A stage may also require a <dfn>kernels</dfn> that must be set for nodes based on that stage.
The node must specify a [=kernel=] that was compiled for the corresponding stage.

A stage that requires any kernels is a <dfn>programmable</dfn> stage.
At stage that requires no kernels is a <dfn>fixed-function</dfn> stage.

Note: The nature of [=fixed-function state=] for any particular pipeline is out of scope of this specification.

Data is passed between the nodes of a pipeline configuration in the form of <dfn>records</dfn>.
One stage may output [=records=] of some type |R|, while another stage inputs [=records=] of type |R|.


A pipeline defines rules for the allowed topologies of pipeline configurations.
The exact nature of these rules for each pipeline are beyond the scope of this specification, but can include constraints on how many nodes are required or allowed to appear for each stage, and how those nodes may or must connect.

#### Dispatches ### {#exec.gpu.dispatch}

Work is issued to a GPU device in the form of <dfn>commands</dfn>.
A <dfn>dispatch</dfn> is a [=command=] that causes a GPU device to execute a specific [=pipeline configuration=] given some dispatch arguments.

A given dispatch determines the values of all uniform shader parameters that may be accessed by the kernels of the pipeline configuration.

#### Compute ### {#exec.gpu.pipeline.compute}

A compute pipeline supports only a single node, using the `compute` stage.
The `compute` stage is a [=programmable=] stage.

A [=dispatch=] of a compute pipeline configuration invokes its kernel for each strand in a <dfn>block</dfn> of strands.
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

The rasterization stage is a [=fixed-function=] stage.


#### Ray Tracing #### {#exec.gpu.pipeline.ray-tracing}

Uniformity {#exec.uniformity}
----------

A <dfn>collective</dfn> operation is one that require multiple strands to coordinate.
A [=collective=] operation is only guaranteed to execute correctly when the required subset of strands all <dfn>participate</dfn> in the operation together.

### Tangle ### {#exec.uniformity.tangle}

Any strand begins execution of an entry point as part of a <dfn>tangle</dfn> of strands.
The [=tangle=] that a strand belongs to can change over the course of its execution.
When a strand executes a collective operation, it [=participates=] with those strands that are part of the same tangle.

When a strand executes a conditional control-flow operation, it branches in a direction that can depend on a <dfn>condition value</dfn>.
When the strands of a tangle execute a conditional control-flow operation, those strands are grouped into one or more new tangles, according the following rules:

* Strands that compute the same [=condition value=] are guaranteed to be part of the same new tangle.

* Strands that branch to a different destination are guaranteed to be part of different new tangles.

* Strands that compute different [=condition values=], but that branch to the same destination may or may not be part of the same new tangle.

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

Source and Binary Stability {#stability}
===========================

<div class="issue">
This section needs to define what it means for something to be _stable_ vs. <dfn>fragile</dfn>.
</div>