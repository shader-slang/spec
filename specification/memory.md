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
