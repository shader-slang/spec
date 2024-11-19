Execution Model {#exec}
===============

<div class=issue>
Even if we don't define a completely formal runtime semantics, we need sufficient terminology to be able to explain the intended semantics of language constructs, including things like `discard`, shared memory, wave-level ops, etc.

Key concepts that this chapter will need to discuss:


* A concept of systems that might be comprised of multiple <dfn>devices</dfn>, and which might have multiple distinct <dfn>memory spaces</dfn> that may or may not be shared.

* The notion of a thread or invocation that runs Slang code in a largely scalar/sequential fashion.

* Any notions of groupings of threads (quads, subgroups/waves/warps, thread blocks/workgroups, dispatches/grids/draws, etc.) that might have semantic consequences

* A definition of what it means for execution to be <dfn>convergent</dfn> for a grouping of threads, and what it means for data to be <dfn>uniform</dfn> across such groups.

* A definition of what memory <dfn>objects</dfn> and/or <dfn>locations</dfn> are, and the kinds of <dfn>accesses</dfn> that may be performed to them (reads, writes, atomics, etc.).

* Definitions of what an <dfn>activation</dfn> of a function is, and how those activations comprise the call stack of a thread.

* A definition of core GPU rendering concepts such as <dfn>pipelines</dfn>, <dfn>stages</dfn>, <dfn>kernels</dfn>, <dfn>varying</dfn> input/output, [=uniform=] shader parameters, etc.


</div>

