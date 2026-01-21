SP #034: Pointer Data Layouts
=============================

We should add data layout information to the `Ptr<T>` type.

Currently, accessing any data structure through a pointer generally assumes that
the data is in the native layout (in other words, scalar layout) unless
globally overridden by a compiler option on certain targets.

This prevents pointers from pointing to data stored using different data
layouts. This proposal suggests adding data layout information as an additional
template parameter to `Ptr` to fill this gap.

Status
------

Status: Design Review

Implementation: TBD

Author: Julius Ikkala

Reviewer: TBD

Background
----------

Data layouts (`IBufferDataLayout`) allow Slang to determine the memory layout of
a type. They affect the type alignment rules and structure padding. Currently,
five data layouts are available to users: `DefaultDataLayout`,
`Std140DataLayout`, `Std430DataLayout`, `ScalarDataLayout`, and `CDataLayout`.

Currently, data layouts can only be explicitly set for buffer types, such as
`RWStructuredBuffer` and `ConstantBuffer`. For example,
`RWStructuredBuffer<Foo, ScalarDataLayout>` would make the compiler assume that
the buffer's memory contains instances of `Foo` in the scalar data layout.

Pointers are an alternative to buffer types. They allow the user to simply pass
a pointer value to their data instead of going through the graphics API to bind
the data as a buffer.

Compared to buffer types, Slang's pointers have a gap in functionality with
regards to data layouts. They do not currently allow the user to specify the
data layout, which in practice usually leads to the data being assumed to be in
the scalar layout. This proposal attempts to fix this gap by allowing the user
to specify a data layout for pointers as well.

Annotating data layouts in pointers is also necessary to allow lowering buffer
types into pointers on CPU targets. Without this information, such a lowering
would erase layout information.

Related Work
------------

The author is not aware of prior work where data layouts are annotated as part
of the pointer. Related work usually achieves the same end result by instead
annotating data layouts in type declarations.

Many C compilers allow annotating a rudimentary data layout option, *packing*,
with an attribute in front of a structure type:

```c
struct __attribute__((packed)) Foo { ... }
```

Similarly, Rust annotates data layouts per-type, using a *representation*
attribute:
```rust
#[repr(C)]
struct Foo
{
    ...
}
```

Proposed Approach
-----------------

A new generic parameter should be added to the `Ptr` type, indicating the
data layout used when accessing data through the pointer. The type parameter
should satisfy `IBufferDataLayout` and default to `DefaultDataLayout`.

Detailed Explanation
--------------------

Instead of assuming the native layout for pointers, backends should determine
the layout from the pointer type. `DefaultDataLayout` should retain current
behavior in order to make this change non-breaking.

Support should be added on all targets that support both pointers and data
layouts; that is, SPIR-V and LLVM. Support is excluded from C++ and CUDA targets
because they do not support non-default data layouts. HLSL, GLSL, MSL and WGSL
targets are excluded as they do not support pointers.

Alternatives Considered
-----------------------

An alternative approach is to instead only define the canonical data layout in
the type declaration, such as:

```slang
[DataLayout(ScalarDataLayout)]
struct Foo
{
    vec3 a;
    float b;
}
```

Then, `Ptr<Foo>` would always use `ScalarDataLayout`. While this approach is
attractive for the mental model where a type fully defines the memory layout
and matches what most other languages opt for, it is not in line with existing
language features. In particular, `RWStructuredBuffer<T, IBufferDataLayout>`
allows defining the data layout used for `T` externally; both
`RWStructuredBuffer<Foo, Std430DataLayout>` and
`RWStructuredBuffer<Foo, ScalarDataLayout>` are legal.

The proposed approach is instead more in line with how buffer types define their
data layouts. This is crucial, because one motivation for this feature is the
lowering of buffer types to pointers on targets where such a transformation is
possible (CPU targets).

Still, it may be possible to add a `[DefaultLayout(...)]` in a separate proposal
later on that would allow defining the layout in the type declaration similar
to C or Rust. Such an annotation would override the meaning of
`DefaultDataLayout`. This is deferred to a separate proposal due to the 
complications involved with semantics that require more careful design:

```slang
[DefaultLayout(ScalarDataLayout)]
struct Foo
{
    vec3 a;
    float b;
}

[DefaultLayout(Std430DataLayout)]
struct Bar
{
    // What layout does `foo` have here? The user probably expects it to be in
    // `ScalarDataLayout`. If so, we would need to be able to mix and match
    // data layouts in a single struct.
    Foo foo;
    vec3 c;
}
```
