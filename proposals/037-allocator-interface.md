SP #037: IAllocator interface for dynamic memory allocation
=================

An `IAllocator` interface should be added into the core module. This interface
would provide various dynamic memory allocation operations. Along with the
interface, two CPU-target-only implementations should be added: `StackAllocator`
and `HeapAllocator`.

Currently, there is no direct way to allocate memory in the CPU targets, other
than manually forward-declaring the C standard library function `malloc()` and
using it. To make dynamic memory operations more ergonomic, this proposal aims
to make memory allocation a part of the core module and add a way to explicitly
perform stack allocations on CPU targets.

Status
------

Status: Design Review

Implementation: TBD

Author: Julius Ikkala

Reviewer: TBD

Background
----------

With the deprecation of the unary `&`-operator, the CPU targets (whether C++ or
LLVM-based) are in trouble when needing to call foreign C functions that use
pointers for return values. Previously, one would typically just declare a local
variable and use the `&`-operator to get a pointer to it.

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
to allocate, deallocate and resize memory allocations. It provides three
user-facing functions:
* `Ptr<T> allocate<T>(count)` for allocating an array `T[count]` 
* `void free<T>(Ptr<T> data)` for deallocating a previous allocation
* `Ptr<T> reallocate<T>(Ptr<T> data, size_t oldCount, size_t newCount)` for resizing a previous allocation

It is possible to create user-defined allocators conforming to the `IAllocator`
interface.

A `StackAllocator` is added so that the user can perform allocations in
the stack frame of the function where `StackAllocator.allocate<T>(count)` is
called. It behaves similarly to `(T*)alloca(size * sizeof(T))` in C.

A `HeapAllocator` is added to perform heap allocations. It can be called
as `HeapAllocator.allocate<T>(count)`. `HeapAllocator` provides functionality
equivalent to `malloc()`, `free()` and `realloc()` in C.

Detailed Explanation
--------------------

The following use cases were considered when designing the below `IAllocator` interface:
* Generic heap allocators on CPUs
* Stack allocations on CPUs
* Arena/region allocators on GPUs and CPUs

Add `IAllocator` interface that defines methods for dynamic memory allocations:
```slang
public enum AllocationError
{
    OutOfMemory
}

public interface IAllocator<AddressSpace addrSpace>
{
    Ptr<void, Access.ReadWrite, addrSpace>
        rawAllocate(size_t bytes, uint alignment) throws AllocationError;

    Ptr<void, Access.ReadWrite, addrSpace> rawReallocate(
        Ptr<void, Access.ReadWrite, addrSpace> prevPtr,
        size_t prevBytes,
        size_t bytes,
        uint alignment
    ) throws AllocationError {
        // default impl deferring to rawAllocate & rawFree
    }

    void rawFree(Ptr<void, Access.ReadWrite, addrSpace> data)
    {
        // default no-op impl
    }

    Ptr<T, Access.ReadWrite, addrSpace, L>
        allocate<T, L:IBufferDataLayout = DefaultDataLayout>(int count = 1) throws AllocationError
    {
        // default impl deferring to rawAllocate
    }

    Ptr<T, Access.ReadWrite, addrSpace, L> reallocate<T, L:IBufferDataLayout = DefaultDataLayout>(
        Ptr<T, Access.ReadWrite, addrSpace, L> oldPtr,
        size_t oldCount,
        size_t newCount
    ) throws AllocationError {
        // default impl deferring to rawReallocate
    }

    void free<T, L:IBufferDataLayout = DefaultDataLayout>(Ptr<T, Access.ReadWrite, addrSpace, L> data)
    {
        // default impl deferring to rawFree
    }

    void close()
    {
        // default no-op impl
    }
}

public typealias IDeviceAllocator = IAllocator<AddressSpace.Device>;
```

The address space is specified as a generic parameter of the allocator, because
it is conceivable that someone could want an allocator for e.g. shared memory,
once shared memory pointers are in a better shape. However, typically
allocations are expected to be made in device memory, so as a convenience, we 
can provide an `IDeviceAllocator` type alias.

The only function that needs to be implemented by an allocator is
`rawAllocate(size_t bytes, uint alignment)`. `rawFree()` is optional, and
the default implementation should be a no-op. This is necessary for stack and
arena allocators, where deallocation is handled in bulk instead of per-pointer.

`reallocate()` can also have a default implementation. Typed allocation
functions can be implemented with untyped allocators, by resolving the stride
and alignment of `T`.

`close()` should reset the allocator and de-allocate everything.

A `StackAllocator` implementation should be added. It should define a `static`
implementation for `rawAllocate`. `rawAllocate` should lower to `kIROp_Alloca`,
which should be extended to accept an alignment operand as well. Reliance on an
IR instruction is likely required, as the `alloca` instruction needs to be
generated directly in the existing function. Implementing that with inline LLVM
IR may not work correctly.

A `HeapAllocator` should be added in a similar way, with the interface
implemented with static functions and no data members. It can be implemented
using inline C++ and LLVM IR and call `aligned_alloc()` and friends.

Both `StackAllocator` and `HeapAllocator` must `[require(cpp_llvm)]`, at least
for now. They should conform to `IDeviceAllocator`.

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

The `alignment` parameter could be made optional and just set to whatever is the
maximum alignment expected by any instruction on the host. This is the path
partially taken by GCC and Clang when one calls `alloca()` or `malloc()`; both
align the address to 16 bytes on x86 CPUs.

Alternatively, alignment could always be inferred from `T` and
`IAlloca.rawAllocate()` could be removed.

The `IAllocator` interface itself may be considered unnecessary and similar
functionality could be added as free functions, such as `__alloca()`,
`__malloc()`, `__free()` and so on. However, if one wants to write generic code
that can operate with various different allocation methods, the `IAllocator`
interface is useful.

The `L:IBufferDataLayout` parameter could be removed, and `DefaultDataLayout`
could be assumed. This is less flexible, but it is unclear if there's really a
need to be able to allocate types in any other layout than the default.
