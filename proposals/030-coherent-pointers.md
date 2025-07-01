# SP\#030: Coherent Pointers & Pointer Access

## Status

Status: Design Review  
Implementation:  
Author: Ariel Glasroth  
Reviewer:

## Background

### Introduction

GPUs have a concept known as coherent operations. Coherent operations flush cache for reads/writes so that when **thread A** modifies memory, **thread B** may read that memory, seeing all changes to memory done by a different thread. When flushing cache it is important to note that not all caches will be flushed. If a user wants coherence to `WorkGroup` memory, only the levels of cache up to `WorkGroup` memory will need to be flushed.

Additionally, pointers will be permitted to be marked as read-only or read/write. A read-only pointer will be immutable (unable to modify the data pointed to).

### Prior Implementations

* HLSL – `globallycoherent` keyword can be added to declarations (`globallycoherent RWStructuredBuffer<T> buffer`). This keyword ensures coherence with all operations to a tagged object. Memory scope of coherence is device memory. `groupshared` objects are likely coherent, specification does not specify.  
* GLSL– `coherent` keyword can be added to declarations (`coherent uniform image2D img`). This keyword ensures coherence with all operations to a tagged object. Memory scope of coherence is unspecified. Objects tagged with `shared` are [implicitly](https://www.khronos.org/opengl/wiki/Compute_Shader) `coherent`.  
* Metal – `memory_coherence::memory_coherence_device` is a generic argument to buffers. This argument ensures coherence with all operations to a tagged object. Memory scope of coherence is device memory.  
* WGSL – [All operations](https://www.w3.org/TR/WGSL/#private-vs-non-private) are coherent.

### SPIR-V Support For Coherence

Originally, SPIR-V supported coherent objects through the `coherent` type `Decoration`. Modern SPIR-V (`VulkanMemoryModel`) exposes this functionality differently to control coherence as a **per operation** functionality. Coherence is now done per operation through adding the memory operands `MakePointerAvailable`, `MakePointerVisible`, `MakeTexelAvailable`, and `MakeTexelVisible` to load and store operations. Users must additionally specify the memory scope to which an operation is coherent.  
	  
`MakePointerAvailable` is for memory stores of non textures, `OpStore`, `OpCooperativeMatrixStoreKHR` and `OpCooperativeVectorStoreNV`.. 

`MakePointerVisible` is for memory loads of non textures, `OpLoad`, `OpCooperativeMatrixLoadKHR` and `OpCooperativeVectorLoadNV`.

 `MakeTexelAvailableKHR` is for memory stores of textures, `OpImageWrite`, `OpImageSparseLoad`.

 `MakeTexelVisibleKHR` is for memory loads of textures, `OpImageRead`, `OpImageSparseRead`.

Additionally,  `MakePointer{Visible,Available}` support usage in `OpCopyMemory` and `OpCopyMemorySized`.

### Example

The simple use-case of this feature can be modeled with the following example: (1) We have **thread1** and **thread2** both reading/writing to the same `RWStructuredBuffer`. (2) **thread1** `OpStore`’s non-coherently into the buffer. (3) if **thread2** uses an `OpLoad` on the texture they may not see the change **thread1** made for 2 reasons:

1) **thread1** does not promise its writes are visible to other threads. Cached writes may not immediately flush to device memory.  
2) **thread2** may load from a cache, not device memory. This means we will not see the new value because the new value was written to device memory, not the intermediate cache.

If we specify `MakePointerAvailable/MakePointerVisible` with `OpStore`/`OpLoad`  to the memory scope `QueueFamily` we will solve this problem since we are flushing changes to a memory scope shared by the two threads. This additionally may be faster than the alternative of flushing to `Device` memory since a `QueueFamily` is a tighter scope than `Device`.

## Proposed Solution

### Frontend For Coherent Pointers & Pointer Access

We propose to implement coherence on a per-operation level for only SPIR-V targets. This will be accomplished through modifying `Ptr` to include the new generic argument `CoherentScope coherentScope`.

We also propose the new generic argument `Access access` to specify if a pointer is read-only or not.

```c#
public enum CoherentScope
{
    NotCoherent = 0xFF,
    CrossDevice = MemoryScope::CrossDevice,
    Device = MemoryScope::Device,
    Workgroup = MemoryScope::Workgroup,
    Subgroup = MemoryScope::Subgroup,
    Invocation = MemoryScope::Invocation,
    QueueFamily = MemoryScope::QueueFamily,
    ShaderCallKHR = MemoryScope::ShaderCallKHR,
    //...
}

public enum Access
{
    ReadWrite = 0, 
    Read = 1
}

__generic<T, uint64_t addrSpace=AddressSpace::UserPointer, Access access = Access::ReadWrite, CoherentScope coherentScope=CoherentScope::NotCoherent>
struct Ptr
{
    ...
}
```

If `coherentScope` is not `CoherentScope::NotCoherent`, all accesses to memory through this pointer will be considered coherent to the specified memory scope (example: `CoherentScope::Device` is coherent to the memory scope of `Device`).

If `access` is `Access::ReadWrite` a pointer can read/write to the data pointed to.
If `access` is `Access::Read`, a pointer will only be allowed to read from the data pointed to.

We will also provide a a type alias for user-convenience.

```c#
__generic<T, Access access = Access::ReadWrite>
typealias CoherentPtr = Ptr<T, AddressSpace::UserPointer, access, CoherentScope::Device>;
```

### Support For Coherent Buffers and Textures

Any access through a coherent-pointer to a buffer/texture is coherent.

```c#
RWStructuredBuffer<int> val; // Texture works as well.   
CoherentPtr<int, CoherentScope::Device> p = &val[0];
*p = 10; // coherent store
p = p+10;
int b = *p; //coherent load
int c = val[10] + *p; //allowed to use coherent and non-coherent simultaneously
```

### Support For Coherent Workgroup Memory

Any access through a coherent-pointer to a `groupshared` object is coherent; Since Slang does not currently support pointers to `groupshared` memory, this proposal will extend the existing `AddressSpace::GroupShared` implementation for pointers as needed.

### Support For Coherent Cooperative Matrix & Cooperative Vector

`CoopVec` and `CoopMat` load data into their respective data-structures from other objects using `CoopVec::Load`, `CoopVec::Store`, `CoopMat::Load`, and `CoopMat::Store`. Due to this design, we will add coherent operations to `CoopVec` and `CoopMat` by modifying `CoopVec::Load`, `CoopVec::Store`, `CoopMat::Load`, and `CoopMat::Store` to complete coherent operations if given a `CoherentPtr` as a parameter. Syntax required to use the method(s) will not change.

### Support Casting Pointers With Different `CoherentScope`

We will allow pointers with different `CoherentScope` to be explicitly castable to each other. For example, `CoherentPtr<int, CoherentScope::Device>` will be castable to `CoherentPtr<int, MemoryScope.Workgroup>`.

### Casting and Pointer access

We will not allow casting between pointers of different `Access`.

### Banned keywords

HLSL style `globallycoherent T*` and GLSL style `coherent T*` will be disallowed.

### Order of Implementation

* Frontend for coherent pointers & pointer access
* Logic for pointer access
* Support for coherent buffers and textures
* Support casting between pointers with different `CoherentScope`
* Support for workgroup memory pointers.
* Support for coherent workgroup memory  
* Support for coherent cooperative matrix & cooperative vector  
* disallow `globallycoherent T*` and `coherent T*`

## Future Work

### Supporting Aligned Loads

Users may choose to load coherently given a specific alignment. This will be supported through the `[Align(ALIGNMENT)]` decoration.

```c#
[Align(ALIGNMENT)]
struct MyType {...}

MyType* p  = ...;
...
let a = *p; // should be aligned load;
let b = p.member; // should be aligned load, with alignment derived from both `MyType` and `member`'s type.
```

When loading data from a pointer `p` Slang will honor the alignment and emit an `OpLoad` with the SPIR-V `Aligned` memory operand, providing the argument `ALIGNMENT`. This will function alongside `coherent` pointers.

### Additional Pointer Arguments

`Volatile` and `Const` are planned features for `Ptr`.

## Alternative Designs Considered

1. Using special methods (part of the `Ptr` type) to access coherent-operation functionality

```c#
T* ptr1 = bufferPtr1;
T* ptr2 = bufferPtr2;
var loadedData = coherentLoad(ptr1, scope = MemoryScope::Device);
coherentStore(ptr2, loadedData, scope = MemoryScope::Device);
```

2. Tagging types as coherent through a modifier

```c#
// Not allowed:
globallycoherent RWStructuredBuffer<T> bufferPtr1 : register(u0);

cbuffer PtrBuffer
{
    // We only allow coherent on pointers
    globallycoherent int* bufferPtr1;
}
```

3. ‘OOP’ approach, get a `CoherentPtr` from a regular `Ptr`. Any operation on a `CoherentPtr` will use the Coherent variant of a store/load.

```c#
[require(SPV_KHR_vulkan_memory_model)]
void computeMain()
{
    int* ptr = gmemBuffer;
    CoherentPtr<int, MemoryScope::Workgroup> ptr_workgroup = CoherentPtr<int, MemoryScope::Workgroup>(gmemBuffer);
    CoherentPtr<int, MemoryScope::Workgroup> ptr_device = CoherentPtr<int, MemoryScope::Workgroup>(gmemBuffer);


    ptr_workgroup[0] = output[1];
    ptr_workgroup = ptr_workgroup + 1;
    output[2] = ptr_workgroup[0];
    ptr_workgroup = ptr_workgroup - 1;
    output[3] = ptr_workgroup[3];


    ptr[10] = 10;
   
    ptr_device = ptr_device + 3;
    gmemBuffer[0] = 10;
    ptr_device[3] = output[3];
}
```

4. Modifier with parameter to specify memory-scope

```c#
cbuffer PtrBuffer
{
    int* bufferPtr1;
}
int main()
{
    coherent<WorkgroupMemory> int* bufferPtrWorkgroup = bufferPtr1;
    coherent<Device> int* bufferPtrDevice = bufferPtr1;
}
```

## 
