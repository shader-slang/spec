# SP\#031: Coherent Pointer Operations & Pointer Access

## Status

Status: Design Review
Implementation:
Author: Ariel Glasroth
Reviewer:

## Background

### Introduction

GPUs have a concept known as coherent operations. Coherent operations flush cache for reads/writes so that when **thread A** modifies memory, **thread B** may read that memory, seeing all changes to memory done by a different thread. When flushing cache it is important to note that not all caches will be flushed. If a user wants coherence to `WorkGroup` memory, only the levels of cache up to `WorkGroup` memory will need to be flushed.

Additionally, pointers have a topic called 'access', the ability to mark a pointer as read-only or read-write. A read-only pointer is immutable (unable to modify the data pointed to), a read-write pointer allows reading & writing to the data the pointer points at.

### Prior Implementations Of Coherence

* HLSL – `globallycoherent` keyword can be added to declarations (`globallycoherent RWStructuredBuffer<T> buffer`). This keyword ensures coherence with all operations to a tagged object. Memory scope of coherence is device memory. `groupshared` objects are likely coherent, specification does not specify.
* GLSL – `coherent` keyword can be added to declarations (`coherent uniform image2D img`). This keyword ensures coherence with all operations to a tagged object. Memory scope of coherence is unspecified. Objects tagged with `shared` are [implicitly](https://www.khronos.org/opengl/wiki/Compute_Shader) `coherent`.
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

If we specify `MakePointerAvailable/MakePointerVisible` with `OpStore`/`OpLoad` to the memory scope `QueueFamily` we will solve this problem since we are flushing changes to a memory scope shared by the two threads. This additionally may be faster than the alternative of flushing to `Device` memory since a `QueueFamily` is a tighter scope than `Device`.

### Prior Implementations Of Access

* C/C++ – `const int* ptr` or `int const*` both mean the underlying data pointed to is constant
    * This will be equivalent to `Access::Read`
* C/C++ – `int* const` means the value of the pointer is constant
    * This will be equivalent to `const Ptr<T, ...> ptr`

### Compiler Support For Coherence

This is currently planned to be a high-level concept which does not map to anything in SPIR-V.

## Proposed Solution

### Frontend For Pointer Access

Pointer Access will be implemented through a new generic-argument `Access access` on our `Ptr` data-type. 
We will also expose pointer `AddressSpace`s.

```c#
enum Access : uint64_t
{
    ReadWrite = 0,
    Read = 1
    //...
}

enum AddressSpace : uint64_t
{
    Generic = 0x7fffffff,
    // Corresponds to SPIR-V's SpvStorageClassPrivate
    ThreadLocal = 1,
    Global,
    // Corresponds to SPIR-V's SpvStorageClassWorkgroup
    GroupShared,
    // Corresponds to SPIR-V's SpvStorageClassUniform
    Uniform,
    // specific address space for payload data in metal
    MetalObjectData,
    // Corresponds to SPIR-V's SpvStorageClassInput
    Input,
    // Same as `Input`, but used for builtin input variables
    BuiltinInput,
    // Corresponds to SPIR-V's SpvStorageClassOutput
    Output,
    // Same as `Output`, but used for builtin output variables
    BuiltinOutput,
    // Corresponds to SPIR-V's SpvStorageClassTaskPayloadWorkgroupEXT
    TaskPayloadWorkgroup,
    // Corresponds to SPIR-V's SpvStorageClassFunction
    Function,
    // Corresponds to SPIR-V's SpvStorageClassStorageBuffer
    StorageBuffer,
    // Corresponds to SPIR-V's SpvStorageClassPushConstant
    PushConstant,
    // Corresponds to SPIR-V's SpvStorageClassRayPayloadKHR
    RayPayloadKHR,
    // Corresponds to SPIR-V's SpvStorageClassIncomingRayPayloadKHR
    IncomingRayPayload,
    // Corresponds to SPIR-V's SpvStorageClassCallableDataKHR
    CallableDataKHR,
    // Corresponds to SPIR-V's SpvStorageClassIncomingCallableDataKHR
    IncomingCallableData,
    // Corresponds to SPIR-V's SpvStorageClassHitObjectAttributeNV
    HitObjectAttribute,
    // Corresponds to SPIR-V's SpvStorageClassHitAttributeKHR
    HitAttribute,
    // Corresponds to SPIR-V's SpvStorageClassShaderRecordBufferKHR
    ShaderRecordBuffer,
    // Corresponds to SPIR-V's SpvStorageClassUniformConstant
    UniformConstant,
    // Corresponds to SPIR-V's SpvStorageClassImage
    Image,
    // Represents a SPIR-V specialization constant
    SpecializationConstant,
    // Corresponds to SPIR-V's SpvStorageClassNodePayloadAMDX
    NodePayloadAMDX,
    // Default address space for a user-defined pointer
    UserPointer = 0x100000001ULL,
};

__generic<T, Access access = Access::ReadWrite, AddressSpace addrSpace = AddressSpace::UserPointer> 
struct Ptr
{
    //...
}
```

If a pointer is `Access::Read`, a user program may only read from the given pointer. If a pointer is `Access::ReadWrite`, a user program may read from a given pointer or write to it. 

### Frontend For Coherent Pointer Operations

We propose to implement coherence on a per-operation level for SPIR-V targets. This will be accomplished through new intrinsic methods to handle coherent load/store.

```c#
public enum MemoryScope : int32_t
{
    CrossDevice = 0,
    Device,
    Workgroup,
    Subgroup,
    Invocation,
    QueueFamily,
    ShaderCall,
    //...
}

// `ptr` is the value to be loaded.
// The `int alignment` parameter controls the alignment to load from a pointer with.
// The `MemoryScope scope` parameter controls the memory scope that an operation is coherent to.
[ForceInline]
[require(SPV_KHR_vulkan_memory_model)]
__generic<T, Access access, AddressSpace addrSpace> 
T loadCoherent(Ptr<T, access, addrSpace> ptr, int alignment, constexpr MemoryScope scope = MemoryScope::Device);

// Return a `CoopVec`, loaded from `ptr`.
[ForceInline]
[require(SPV_KHR_vulkan_memory_model, cooperative_vector)]
__generic<T : __BuiltinArithmeticType, let N : int, Access access, AddressSpace addrSpace>
CoopVec<T, N> coopVecLoadCoherent(Ptr<T, access, addrSpace> ptr, int offset, int alignment, constexpr MemoryScope scope = MemoryScope::Device);

// Return a `CoopMat`, loaded from `ptr`.
[ForceInline]
[require(SPV_KHR_vulkan_memory_model, cooperative_matrix)]
__generic<
    T : __BuiltinArithmeticType,
    let S : MemoryScope,
    let M : int,
    let N : int,
    let R : CoopMatMatrixUse,
    let matrixLayout : CoopMatMatrixLayout,
    let access : Access,
    let addrSpace : AddressSpace>
CoopMat<T, S, M, N, R> coopMatLoadCoherent(Ptr<T, access, addrSpace> ptr, uint element, uint stride, int alignment, constexpr MemoryScope scope = MemoryScope::Device);

// `ptr` is the dst for the store.
// `val` is the value to store into `ptr`.
// The `int alignment` parameter controls the alignment to load from a pointer with.
// The `MemoryScope scope` parameter controls the memory scope that an operation is coherent to.
[ForceInline]
[require(SPV_KHR_vulkan_memory_model)]
__generic<T, AddressSpace addrSpace> 
void storeCoherent(Ptr<T, Access::ReadWrite, addrSpace> ptr, T val, int alignment, constexpr MemoryScope scope = MemoryScope::Device);

// Store into `ptr` given `val`.
[ForceInline]
[require(SPV_KHR_vulkan_memory_model, cooperative_vector)]
__generic<T : __BuiltinArithmeticType, let N : int, AddressSpace addrSpace>
void coopVecStoreCoherent(Ptr<T, Access::ReadWrite, addrSpace> ptr, CoopVec<T, N> val, int offset, int alignment, constexpr MemoryScope scope = MemoryScope::Device);

// Store into `ptr` given `val`.
[ForceInline]
[require(SPV_KHR_vulkan_memory_model, cooperative_matrix)]
__generic<
    T : __BuiltinArithmeticType,
    let S : MemoryScope,
    let M : int,
    let N : int,
    let R : CoopMatMatrixUse,
    let matrixLayout : CoopMatMatrixLayout,
    let addrSpace : AddressSpace>
void coopMatLoadCoherent(Ptr<T, Access::ReadWrite, addrSpace> ptr, CoopMat<T, S, M, N, R> val, uint element, uint stride, int alignment, constexpr MemoryScope scope = MemoryScope::Device);
```

### Support For Coherent Workgroup Memory

Any access through a coherent-pointer to a `groupshared` object is coherent; since Slang does not currently support pointers to `groupshared` memory, this proposal will extend the existing `AddressSpace::GroupShared` implementation for pointers as needed.

### Casting Pointers

All pointers can be casted to each other. Casting must be explicit.

### Banned keyword usage

The following keyword use is disallowed:
* `globallycoherent T*`
* `coherent T*`.
* `const T*`, `T const*`, and `T* const`
* `Ptr<const T>`, `Ptr<coherent T>`, and `Ptr<globallycoherent T>`

### Explicitly allowed keywords

`const Ptr<int>` is permitted. This means that a `Ptr` is constant, the address the pointer is pointing at will not change.

### Order of Implementation

* Frontend for pointer changes
* Logic for pointer access
* Support casting explicitly between pointers
* Disallow `globallycoherent T*` and `coherent T*`
* Disallow `const T*`, `T const*`, and `T* const`
* Support for coherent buffers and textures
* Support for workgroup memory pointers.
* Support for coherent workgroup memory
* Support for coherent cooperative matrix & cooperative vector

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

5. Coherence as a generic argument

```c#
typedef Ptr<int, AddressSpace::UserPointer, Access::ReadWrite, CoherentScope::Device> DeviceCoherentPtrInt;
int main()
{
    DeviceCoherentPtrInt ptr = DeviceCoherentPtrInt(&processMemory[id.x]);
    output[id] = ptr[id];
}
```

## 
