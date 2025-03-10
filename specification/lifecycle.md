Program Lifecycle [lifecycle]
=================

Compilation [lifecyle.compilation]
-----------

A Slang **compiler** is a tool that is invoked on Slang source code to produce **object code**.

Object code produced by a Slang compiler from one toolchain may be incompatible with tools from other toolchains, other versions of the same toolchain, or across target platforms supported by the toolchain.

Note: This specification does not prescribe the language or format of object code that a particular toolchain implementation has to use.
Object code might use a toolchain-specific IR, a portable intermediate language, or a format that is compatible with another existing toolchain (e.g., the object code format used by a C toolchain on the target).

A *compiler* implementation must support being invoked on an entire Slang source module, potentially comprising multiple source units, to produce object code for that entire module.
A *compiler* implementation may support being invoked on source code at other granularities: e.g., on a subset of the source units of a module.

When compiling code that is part of a Slang module _M_, the output of a compiler implementation must not depend on any non-*fragile* information in the modules that _M_ depends on.

Linking [lifecycle.linking]
-------

A **static library** is a unit of code suitable for distribution or re-use.
Static libraries created by a toolchain should be usable with later versions of that same toolchain.

A **binary** is a unit of **loadable code** that is either an **executable** or a **dynamic library**.

Note: We need to refer to *executables* and *dynamic libraries* somewhere in the text.

A Slang **linker** is a tool that is invoked on one or more inputs, consisting of units of *object code* and *static libraries*, to produce a *static library* or a *binary*.

A binary may contain *loadable code* for zero or more Slang modules.

Note: it is possible that a linked binary might contain both code compiled from Slang as well as code generated from other languages, or by other tools.

It is invalid for a binary to contain code for non-*fragile* symbols from a Slang module _M_ while also having external dependencies on symbols from _M_.
A *linker* may fail with an error rather than produce an invalid binary.

Note: In practice, a linked binary has to either contain all of a given Slang module, or none of it.
The nuance is that *fragile* symbols, such as inlinable functions, from a module _M_ might get copied into object code for a module _N_ that depends on _M_, and thus end up in a binary for _N_.

Loading [lifecycle.loading]
-------

A Slang runtime must support **loading** *binaries* into a *runtime session*, and resolving dependencies between them.

*Loading* of a binary containing definitions of non-fragile symbols from Slang module _M_ must fail if any external symbol that _M_ depends on has not already been loaded into the process.

*Loading* of a binary containing non-fragile symbols from module _M_ may fail if any binary containing definition of non-fragile symbols from _M_ has already been loaded into the process.

It is valid to load a binary containing fragile symbols from module _M_ even if other binaries containing one or more of those symbols has already been loaded, and even if the definitions of those fragile symbols differ between the binaries.
References to fragile symbols may resolve at runtime to any definition of those symbols that was compiled into object code that made its way into the binaries that are loaded.

If Slang code is stored in a *binary* for a *host*, then that code may be loaded as part of initialization of a *process* for a *host* *executable*.

If a *module* of Slang code is loaded programmatically, a Slang runtime must return a *mirror* reflecting that module.

Runtime Reflection [lifecyle.reflection]
------------------

A Slang runtime may support reflection of *modules* that have been loaded into a *runtime session*.

A **mirror** is a runtime value that reflects some entity in a Slang codebase.
A *mirror* is created and managed by a *runtime session*, and reflects entities in the code that has been loaded into that runtime session.
A *mirror* that reflects an _X_ is also called an _X_ *mirror*.

Example: A *module* *mirror* is a *mirror* that reflects a *module*.

A *mirror* may reflect:

* A module
* A declaration
* A reference to a declaration
* A type
* A value

A *mirror* is not the same as the entity it reflects.

Bundling [lifecycle.bundling]
--------

<div class="issue">
This concept needs a proper name.
</div>

A **bundle** is a runtime entity composed from a sequence of distinct runtime entities where each element in the sequence is one of:

* A module
* An entry point (a fully specialized reference to an entry point declaration)
* A witness to conformance relationship of a type to an interface
* A bundle

A Slang runtime must support creation of a *bundle* from a sequence of *mirrors* reflecting the runtime entities to be bundled.

The entry points in a bundle are the entry points in the input sequence.

The modules in a bundle are the set of modules in the input sequence, the modules referenced by the entities in the input sequence, and the transitive closure of modules imported by those.

The global uniform shader parameters of a bundle are the global uniform shader parameters declared in modules in the bundle.

The entry point uniform shader parameters of a bundle are the entry-point uniform shader parameters declared by entry points in the bundle.

The shader parameters of a bundle are the global uniform shader parameters of the bundle and the entry-point uniform shader parameters of the bundle.

A **kernel** is a runtime entity created from a bundle, an entry point in that bundle, and a target device.

A kernel created from a bundle _B_ is compatible with kernels created from a bundle _BX_ where _BX_ was created from an input sequence that started with _B_.
