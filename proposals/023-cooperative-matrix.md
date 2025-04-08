# SP #023: Cooperative Matrix

This proposal introduces support for cooperative matrices in Slang.

## Status

Status: Design Review

Implementation: [PR 6565](https://github.com/shader-slang/slang/pull/6565)

Author: Darren Wihandi

Reviewer: TBD

## Background

This proposal adds cooperative matrix types and operations. These are matrices where storage and computations are spread across a set of invocations such as a subgroup.
This gives the implementation flexibility in how to store and execute matrix multiplication operations - the matrices "cooperate" behind the scenes.
The primary objective is to accelerate matrix multiply-accumulate (MMA) operations, which are critical for machine learning workloads.
For example, the implementation may decide to use dedicated tensor acceleration hardware and MMA instructions.

## Semantics

* Cooperative matrices are explicitly defined to operate at a group scope. Storage and computations are spread across a set of invocations.
* A fully occupied subgroup with uniform control flow is required. Results are undefined under thread divergence.
* Individual components can be accessed, but how they are stored and distributed across the invocations is implementation-dependent.
* The order of arithmetic operations in these functions is implementation-dependent. The SPIR-V extension specifies that the internal precision of floating-point operations is defined by the client API.

## Slang API

### Cooperative Matrix Type

The core of this feature is the `CoopMat` type:

```hlsl
struct CoopMat<T : __BuiltinArithmeticType, let S : CoopMatScope, let M : int, let N : int, let R : CoopMatMatrixUse> : IArray<T>, IArithmetic
{
    // Zero constructor.
    __init();
    // Broadcast.
    __init(T t);
    // Coercion.
    __init<V : __BuiltinArithmeticType>(CoopMat<V, S, M, N, U> other);

    // Array-like access to access components owned by the current invocation.
    T __subscript(int index);

    // Number of components owned by the current invocation.
    int length();
}
```

For initialization there are several options:

* default initialization, with undefined values `CoopMat<float, CoopMatScope::Subgroup, 16, 16, CoopMatMatrixUse::MatrixA>()`
* broadcast initialization `CoopMat<float, CoopMatScope::Subgroup, 16, 16, CoopMatMatrixUse::MatrixA>(0.0)`
* casting initialization `CoopMat<float, CoopMatScope::Subgroup, 16, 16, CoopMatMatrixUse::MatrixA>(CoopVec<half, CoopMatScope::Subgroup, 16, 16, CoopMatMatrixUse::MatrixA>(0))`

Cooperative matrix components owned by the current invocation can be indexed with the subscript operator.
This can be used to read and write the component.
There is no compile-time bounds checking of indices. The index must be less than .length() to avoid undefined behavior.

* `CoopMat<int, CoopMatScope::Subgroup, 16, 16, CoopMatMatrixUse::MatrixA>(0)[2] == 546`

Other operations include:

* binary operators `+`, `-`, `*`, `/`, `%`, these behave as elementwise operations
* unary negation `-`
* comparison operators `==`, `!=`, `<`, `>`, `<=`, `>=`, implementing a lexicographic ordering. Note that these are performed on components owned by the current invocation and not
on the whole matrix.

It's also possible to set values in mutable cooperative matrices with `fill(T
t)` and `copyFrom(CoopMat<V, S, M, N, U> other)`.

## Basic Usage

### Loading and Storing Cooperative Matrices

Cooperative matrices can by loaded and stored from the following buffers:

* `[RW]StructuredBuffer`
* `[RW]ByteAddressBuffer`
* `T*` pointers, which represents physical storage pointers.
* `ConstBufferPointer<T>`
* `groupshared` arrays

Loading done using the static member function `load(Buffer buffer, uint element, uint stride, CoopMatMatrixLayout matrixLayout)` and through the `coopMatLoad` function.
`element` provides the starting index in the buffer where the data begins. For `[RW]ByteAddressBuffer`, the element type is a 4-byte unsigned integer.
The full intrinsics are as so:

```hlsl
CoopMat<T, S, M, N, R> load(ByteAddressBuffer buffer, uint element, uint stride, CoopMatMatrixLayout matrixLayout);
CoopMat<T, S, M, N, R> load(RWByteAddressBuffer buffer, uint element, uint stride, CoopMatMatrixLayout matrixLayout);
CoopMat<T, S, M, N, R> load(StructuredBuffer<T> buffer, uint element, uint stride, CoopMatMatrixLayout matrixLayout);
CoopMat<T, S, M, N, R> load(RWStructuredBuffer<T> buffer, uint element, uint stride, CoopMatMatrixLayout matrixLayout);
CoopMat<T, S, M, N, R> load(T* buffer, uint element, uint stride, CoopMatMatrixLayout matrixLayout);
CoopMat<T, S, M, N, R> load(ConstBufferPointer<T> buffer, uint element, uint stride, CoopMatMatrixLayout matrixLayout);
CoopMat<T, S, M, N, R> load<let U : int>(__constref groupshared T[U] buffer, uint element, uint stride, CoopMatMatrixLayout matrixLayout);
```

Storing can be done through the member function `store(Buffer buffer, uint element, uint stride, CoopMatMatrixLayout matrixLayout)`.
The full intrinsics are as so:

```hlsl
void store(RWByteAddressBuffer buffer, uint element, uint stride, CoopMatMatrixLayout matrixLayout);
void store(RWStructuredBuffer<T> buffer, uint element, uint stride, CoopMatMatrixLayout matrixLayout);
void store(T* buffer, uint element, uint stride, CoopMatMatrixLayout matrixLayout);
void store(ConstBufferPointer<T> buffer, uint element, uint stride, CoopMatMatrixLayout matrixLayout);
void store(__ref groupshared T[U] buffer, uint element, uint stride, CoopMatMatrixLayout matrixLayout);
```

### Matrix Multiplication and Accumulation

```hlsl
CoopMat<V, S, M, N, R> coopMatMulAdd(CoopMat<T, S, M, K, CoopMatMatrixUse::A> matA, CoopMat<U, S, K, N, CoopMatMatrixUse::B>, CoopMat<V, S, M, N, CoopMatMatrixUse::Accumulator> matC, CoopMatMatrixOperands operands = CoopMatMatrixOperands::None);
```

`coopMatMulAdd` perform a matrix multiply of `matA` and `matB`, then component-wise add of `matC`. The order of operations is implementation-dependent and precision is defined by Vulkan.
The dimensions of `matA`, `matB`, and `matC`, must form a valid matrix multiply(eg. number of column of `matA` must match number of rows of `matB`) and they must have the 
same scope. `matA`'s use must be `CoopMatMatrixUse::A`, `matB`'s use must be `CoopMatMatrixUse::B`, and `matC`'s use must be `CoopMatMatrixUse::MatrixAccumulator`.

### Enums and Constants

```hlsl
enum CoopMatScope
{
    Device = 1,
    Workgroup = 2,
    Subgroup = 3,
    QueueFamily = 5,
};

enum CoopMatMatrixUse
{
    MatrixA = 0,
    MatrixB = 1,
    MatrixAccumulator = 2,
};

enum CoopMatMatrixLayout
{
    RowMajor = 0,
    ColumnMajor = 1,
};

enum CoopMatMatrixOperands
{
    None = 0x0,
    MatrixASigned = 0x1,
    MatrixBSigned = 0x2,
    MatrixCSigned = 0x4,
    MatrixResultSigned = 0x8,
    SaturatingAccumulation = 0x10,
};
```

## SPIR-V Translation

Cooperative vector operations in Slang are directly translated to their
corresponding SPIR-V instructions:

* `CoopMat<T, S, M, N, R>` corresponds to OpTypeCooperativeMatrixKHR
* `CoopMat<T, S, M, N, R>.load` corresponds to OpCooperativeMatrixLoadKHR
* `CoopMat<T, S, M, N, R>.store` corresponds to OpCooperativeMatrixStoreKHR
* `CoopMat<T, S, M, N, R>.length` corresponds to OpCooperativeMatrixLength
* `coopMatMulAdd` corresponds to OpCooperativeMatrixMulAddKHR

## Translation for other targets

As of time of writing, there is no plan to support other targets.

## References

* SPIRV cooperative matrix extension [specification](https://github.khronos.org/SPIRV-Registry/extensions/KHR/SPV_KHR_cooperative_matrix.html). This specificationcontains more information on what cooperative matrices
do and how they perform under the hood.
* GLSL cooperative matrix extension [specification](https://github.com/KhronosGroup/GLSL/blob/main/extensions/khr/GLSL_KHR_cooperative_matrix.txt). This specification contains more detailed information, and the Slang intrinsics
proposed in this document are an exact one-to-one match with those in GLSL.

