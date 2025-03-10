Layout [SECTION.layout]
======

<div class="issue">
We clearly need a chapter on the guarantees Slang makes about memory layout.
</div>

Types in Slang do not necessarily prescribe a single <dfn>layout</dfn> in memory.
The discussion of each type will specify any guarantees about [=layout=] it provides; any details of layout not specified here may depend on the target platform, compiler options, and context in which a type is used.
