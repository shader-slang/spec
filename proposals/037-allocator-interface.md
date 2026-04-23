SP #037: IAllocator interface for dynamic memory allocation
=================

An `IAllocator` interface should be added into the core module. This interface
would provide various dynamic memory allocation operations. Along with the
interface, two CPU-target-only implementations should be added: `StackFrameAllocator`
and `SystemHeapAllocator`.

Currently, there is no direct way to allocate memory in the CPU targets, other
than manually forward-declaring the C standard library function `malloc()` and
using it. To make dynamic memory operations more ergonomic, this proposal aims
to make memory allocation a part of the core module and add a way to explicitly
perform stack allocations on CPU targets.

Status
------

Status: Implemented

Implementation: [PR 10608](https://github.com/shader-slang/slang/pull/10608)

Author: Julius Ikkala

Reviewer: Yong He

Background
----------

With the [deprecation of the unary `&`-operator](https://github.com/shader-slang/slang/pull/10280),
the CPU targets (whether C++ or LLVM-based) are in trouble when needing to call
foreign C functions that use pointers for return values. Previously, one would
typically just declare a local variable and use the `&`-operator to get a
pointer to it.

Considering typical GPU hardware architectures, it makes sense that one cannot
have a pointer to a local variable. Registers aren't usually addressable and
emulating a stack with global memory is not a great idea for performance.

One can make the same case for CPU hardware as well. The expectation that local
variables are allocated in "the stack memory" is often incorrect and partly
stems from C / C++. Local variables can exist in registers only. If a pointer is
actually needed, it forces those local variables to be stack-allocated, imposing
an extra performance cost.

Instead, we could move to a different model, where local variables aren't
addressable at all on any targets, including the CPU targets. On targets where
efficient stack allocations are possible, we could instead provide a method
to explicitly make memory allocations in the stack memory.

Support for explicit stack allocations would eliminate one use case for
`&`/`__getAddress()` and make the performance cost and target limitations of
requiring stack allocation more visible to the user.

At the same time, we also have essentially no approach for dynamic memory
allocation in Slang on CPU targets other than to call foreign C functions to do
so. The ability to perform heap allocations could greatly improve the ergonomics
of Slang on CPUs.

Related Work
------------

C and C++ allow performing stack allocations with `alloca()` and heap
allocations with `malloc()` and `calloc()`. Additionally, `std::allocator<T>`
exists to allow custom memory allocation strategies with container types, and is
very similar in spirit to the proposed `IAllocator` interface.

Additionally, CUDA has `cudaMalloc()` to allocate device memory.

Rust's `Allocator` trait serves the same purpose as the proposed `IAllocator`
interface. Zig also has an `Allocator` interface for the same purpose.

In related work, stack allocations are usually not under the same
interface/trait as heap allocations. Many languages don't even provide a method
to perform such allocations dynamically, and only do them implicitly when
creating local variables.

Proposed Approach
-----------------

Introduce an `IAllocator` interface in the core module, that would define functions
to allocate, deallocate and resize memory allocations. It provides six methods:

* `Ptr<T> allocate<T>(size_t count)` for allocating an array `T[count]`
* `void free<T>(Ptr<T> data)` for deallocating a previous allocation
* `Ptr<T> reallocate<T>(Ptr<T> data, size_t oldCount, size_t newCount)` for resizing a previous allocation
* `Ptr<void> alignedAllocate(size_t bytes, uint alignment)` for allocations with dynamic alignment requirements
* `void alignedFree(Ptr<void> data)` for deallocating memory acquired via `alignedAllocate`
* `void close()` for deallocating all allocated memory

It is possible to create user-defined allocators conforming to the `IAllocator`
interface.

A `StackFrameAllocator` is added so that the user can perform allocations in
the stack frame of the function where `StackFrameAllocator.allocate<T>(count)`
is called. It behaves similarly to `(T*)alloca(size * sizeof(T))` in C.

A `SystemHeapAllocator` is added to perform heap allocations. It can be called
as `SystemHeapAllocator.allocate<T>(count)`. `SystemHeapAllocator` provides
functionality equivalent to `malloc()`, `free()` and `realloc()` in C.

Detailed Explanation
--------------------

The following use cases were considered when designing the below `IAllocator` interface:

* Generic heap allocators on CPUs
* Stack allocations on CPUs
* Arena/region allocators on GPUs and CPUs

Add `IAllocator` interface that defines methods for dynamic memory allocations:
```slang
public enum MemoryAllocationError
{
    OutOfMemory,
    AlignmentIsTooLarge
}

public interface IAllocator<AddressSpace addrSpace>
{
    Ptr<T, Access.ReadWrite, addrSpace, L>
        allocate<T, L:IBufferDataLayout = DefaultDataLayout>(int count = 1) throws MemoryAllocationError;

    Ptr<T, Access.ReadWrite, addrSpace, L> reallocate<T, L:IBufferDataLayout = DefaultDataLayout>(
        Ptr<T, Access.ReadWrite, addrSpace, L> oldPtr,
        size_t oldCount,
        size_t newCount
    ) throws AllocationError {
        // default impl deferring to allocate<T> and free<T>.
    }

    void free<T, L:IBufferDataLayout = DefaultDataLayout>(Ptr<T, Access.ReadWrite, addrSpace, L> data)
    {
        // default no-op impl
    }

    Ptr<void, Access.ReadWrite, addrSpace>
        alignedAllocate(size_t bytes, uint alignment) throws MemoryAllocationError
    {
        // default impl using allocate<T> and aligning manually
    }

    void alignedFree(Ptr<void, Access.ReadWrite, addrSpace> data)
    {
        // default impl using free<T>
    }

    void close()
    {
        // default no-op impl
    }
}
```

The address space is specified as a generic parameter of the allocator, because
it is conceivable that someone could want an allocator for e.g. shared memory,
once shared memory pointers are in a better shape.

The only function that needs to be implemented by an allocator is
`allocate(size_t count)`. `free()` is optional, and the default
implementation should be a no-op. This is necessary for stack and arena
allocators, where deallocation is handled in bulk instead of per-pointer.

`reallocate()` also has a default implementation that simply allocates a new
pointer, copies old data and releases the old pointer.

`close()` should reset the allocator and de-allocate everything.

`alignedAllocate(size_t bytes, size_t alignment)` should allocate a pointer that
is aligned to the given `alignment`. Such aligned pointers are not compatible
with `free()` or `reallocate()`, and must be freed using `alignedFree(Ptr<T>)`.

A `StackFrameAllocator` implementation should be added. It should define a
`static` implementation for `allocate`. `allocate` should lower to `kIROp_Alloca`,
which should be extended to accept an alignment operand as well. Reliance on an
IR instruction is required, as the `alloca` instruction needs to be generated
directly in the existing function. Implementing that with inline LLVM IR is not
possible at the moment.

A `SystemHeapAllocator` should be added in a similar way, with the interface
implemented with static functions and no data members. It can be implemented
using inline C++ and LLVM IR and call `malloc()` and friends.

Both `StackFrameAllocator` and `SystemHeapAllocator` must
`[require(cpp_cuda_llvm)]`. They should conform to
`IAllocator<AddressSpace.Device>`.

With the allocators and deprecation of `&` in place, the LLVM emitter can be
simplified considerably. As local variables are no longer addressable, their
layout no longer matters, and they can always use the native layout instead of
following `-fvk-use-*-layout`. If the user needs an address to a struct with a
specific layout, they can use the allocator interface to allocate one.

Alternatives Considered
-----------------------

There are many alterations that could be made to the allocator interface. The
arguments for or against these alternatives may clear up during the
implementation of the feature.

We could rely on `alignedAllocate` and `alignedFree` to implement `allocate` and
`free`; however, that prevents some potential optimizations, as those functions
operate with a runtime-specified alignment, whereas `allocate` knows the type
and its alignment at compile-time.

The `IAllocator` interface itself may be considered unnecessary and similar
functionality could be added as free functions, such as `__alloca()`,
`__malloc()`, `__free()` and so on. However, if one wants to write generic code
that can operate with various different allocation methods, the `IAllocator`
interface is useful.

The `L:IBufferDataLayout` parameter could be removed, and `DefaultDataLayout`
could be assumed. This is less flexible, but it is unclear if there's really a
need to be able to allocate types in any other layout than the default. However,
there's not really any cost to supporting other layouts other than making the
interface slightly uglier. The user of the interface will also not need to
interact with the layout parameter if they don't care about it, as
`DefaultDataLayout` can be specified as the default value for `L`.
