SP #021: Cooperative Matrix and Tensor Types
=======================

Status
------

Status: Design Review

Implementations:
 - cooperative_matrix is completed with d0b6a0b1ab49b5958015f31364c5ad73d9cd03eb
 - cooperative_matrix_2 is in prototype stage

Author: Jae Hyuk Kwak

Reviewer: TBD

Background
----------

Recent SPIR-V and GLSL extensions (notably SPV_KHR_cooperative_matrix, SPV_NV_cooperative_matrix2, and SPV_NV_tensor_addressing) introduce advanced types and operations for cooperative matrix and tensor computations. These features enable efficient matrix-matrix and tensor operations on modern GPUs, especially for machine learning and graphics workloads.

Currently, Slang does not provide first-class support for these types or their associated operations. Users targeting these hardware features must rely on low-level SPIR-V or vendor-specific intrinsics, which is error-prone and less portable. This proposal aims to implement spirv backend with new Slang functionalities.


Related Work
------------

- GLSL: The GLSL_NV_cooperative_matrix2 extension introduces types like cooperative_matrixNV and a suite of functions for matrix/tensor operations, including variadic template-based APIs for elementwise and reduction operations. The proposed approach in this document is very similar to the GLSL syntax.

- SPIR-V: The extensions SPV_KHR_cooperative_matrix, SPV_NV_cooperative_matrix2, and SPV_NV_tensor_addressing define new opcodes and capabilities for these types and operations.

- Other shading languages: HLSL support is currently limited to cooperative vector features, and cooperative matrix functionality is not supported yet.


Proposed Approach
-----------------
Introduce new types and functions in Slang to provide first-class support for cooperative matrices and tensors, closely following the new SPIRV features, but integrated with Slang's type system and generics.

Three new types are needed: CoopMat, CoopMatTensorLayout and CoopMatTensorView. The types use a few generic arguments whose values must be compile-time constants.

### New types

#### CoopMat

CoopMat represents a GPU-optimized matrix type enabling distributed, high-performance matrix operations across hardware scopes.

- CoopMat<T, S, M, N, R>: Cooperative matrix type parameterized by element type, scope, dimensions, and matrix use.
  - T: The element type (e.g., float, int, half)
  - S: The hardware scope (see CoopMatScope) over which the matrix is distributed
  - M: The number of rows in the matrix
  - N: The number of columns in the matrix
  - R: The matrix use (see CoopMatMatrixUse), indicating its role in matrix operations
  - implements IArray<T> and IArithmetic.

Note that a cooperative matrix must be declared with one of three "uses": MatrixA, MatrixB, or MatrixAccumulator. Each operation specialized for cooperative matrices expects specific uses for its operands. For example, a matrix declared as MatrixA cannot be used as MatrixB.

#### CoopMatTensorLayout

While not directly analogous, CoopMatTensorLayout can be loosely compared to the concept of a "subregion" in texture handling. It defines a smaller section of the structure and organization of data within a cooperative matrix tensor.

- CoopMatTensorLayout<Dim, ClampMode>: Describes the layout of a tensor for addressing.
  - Dim: The number of dimensions of the tensor layout (e.g., 2 for a 2D tensor).
  - ClampMode: The clamping or boundary mode for tensor addressing (see CoopMatClampMode).
  - Runtime states:
    - blockSize[Dim]: Block size for each dimension.
    - layoutDimension[Dim]: Logical size for each dimension.
    - stride[Dim]: Stride (in elements) for each dimension.
    - offset[Dim]: Offset for each dimension.
    - span[Dim]: Span for each dimension.

#### CoopMatTensorView

Similarly, CoopMatTensorView can be thought of as somewhat similar to a "TextureView" in texture handling. It allows for reinterpreting or accessing a given cooperative matrix tensor in a specific way without modifying the underlying data.

- CoopMatTensorView<Dim, HasDimensions, p0, p1 ... p{Dim-1} >: Describes a view into a tensor.
  - Dim: The number of dimensions of the tensor view.
  - HasDimensions: Boolean indicating whether explicit dimensions are set for the view.
  - p0, p1, ... p{Dim-1}: A compile-time list specifying the permutation of dimensions for the view. Each pi indicates which source dimension is mapped to the i-th dimension of the view.
  - Runtime states:
    - permutation[Dim]: Permutation of dimensions (compile-time constant).
    - viewDimension[Dim]: Logical size for each dimension in the view when HasDimensions is true.
    - viewStride[Dim]: Stride (in elements) for each dimension in the view.
    - clipRowOffset: Offset for the row clipping region.
    - clipRowSpan: Span for the row clipping region.
    - clipColOffset: Offset for the column clipping region.
    - clipColSpan: Span for the column clipping region.

CoopMatEnsorView takes (N + 2) number of generic arguments where N is a value given as a first generic argument. As an example, when the first value is 2, CoopMatTensorView must use 4 generic arguments. More examples will be `CoopMatTensorView<1, false, 0>`, `CoopMatTensorView<2, true, 0, 1>` and `CoopMatTensorView<3, false, 0, 2, 1>`.

The first generic argument to `CoopMatTensorView` indicates the dimensionality, and the tailing values indicates the re-ordering of the dimension. A common use cases are `CoopMatTensorView<2, false, 0, 1>` for row-major-matrix load and store, and `CoopMatTensorView<2, false, 1, 0>` for column-major-matrix load and store.

Note that CoopMatTensorLayout and CoopMatTensorView are only for loading and storing of CoopMat instances.

### New Enums

- CoopMatScope: Specifies the hardware scope over which the cooperative matrix is distributed.
  - Device: The entire device (all invocations on the device participate).
  - Workgroup: The current workgroup (all invocations in the workgroup participate).
  - Subgroup: The current subgroup (all invocations in the subgroup participate).
  - QueueFamily: The queue family scope (participation is defined by the queue family, rarely used).

- CoopMatMatrixUse: Indicates the intended use of the matrix in matrix operations.
  - MatrixA: The matrix is used as the left-hand (A) operand in a matrix multiplication.
  - MatrixB: The matrix is used as the right-hand (B) operand in a matrix multiplication.
  - MatrixAccumulator: The matrix is used as the accumulator (result) in a matrix multiplication.

- CoopMatMatrixLayout: Describes the memory layout of the matrix.
  - RowMajor: Matrix elements are stored in row-major order.
  - ColumnMajor: Matrix elements are stored in column-major order.

- CoopMatMatrixOperands: Flags that control special behaviors or properties for matrix operations.
  - None: No special behavior.
  - MatrixASigned: Treat MatrixA as signed.
  - MatrixBSigned: Treat MatrixB as signed.
  - MatrixCSigned: Treat the accumulator (MatrixC) as signed.
  - MatrixResultSigned: Treat the result as signed.
  - SaturatingAccumulation: Use saturating arithmetic for accumulation.

- CoopMatClampMode: Specifies the clamping or boundary mode for tensor addressing.
  - Undefined: No clamping mode specified.
  - Constant: Clamp to a constant value.
  - ClampToEdge: Clamp to the edge of the tensor.
  - Repeat: Repeat the tensor data (wrap around).
  - RepeatMirrored: Repeat the tensor data with mirroring at the boundaries.

- CoopMatReduceMask: Specifies the region over which the reduction operation is performed.
  - Row: Reduce across each row of the matrix.
  - Column: Reduce across each column of the matrix.
  - RowAndColumn: Reduce across both rows and columns (full matrix reduction).
  - TwoByTwo: Reduce over each 2x2 block within the matrix.

### Hello World Example 1
```
ByteAddressBuffer inputC; // { 1.f, 1.f, 1.f, ... }
RWStructuredBuffer<float> outputBuffer;

typealias CoopMatAType = CoopMat<float16_t, CoopMatScope::Subgroup, 16, 16, CoopMatMatrixUse::MatrixA>;
typealias CoopMatBType = CoopMat<float16_t, CoopMatScope::Subgroup, 16, 16, CoopMatMatrixUse::MatrixB>;
typealias CoopMatCType = CoopMat<float32_t, CoopMatScope::Subgroup, 16, 16, CoopMatMatrixUse::MatrixAccumulator>;

[numthreads(32, 1, 1)]
void computeMain()
{
    // Define two 16x16 matrices.
    let matA = CoopMatAType(3.h); // initialize all components
    let matB = CoopMatBType(5.h);

    // Load values from a ByteAddressBuffer.
    int elementOffset = 0;
    int stride = 16;
    let matC = CoopMatCType.load(inputC, elementOffset, stride, CoopMatMatrixLayout::RowMajor);

    // ( 3.0 * 5.0 ) * 16 + 1.0 = 241.0
    // CHECK-COUNT-256: 241.0
    let result = coopMatMulAdd(matA, matB, matC, CoopMatMatrixOperands::None);

    // Store the result to a ByteAddressBuffer.
    result.store(outputBuffer, 0, 16, CoopMatMatrixLayout::RowMajor);
}
```

### Hello World Example 2
```
ByteAddressBuffer input;
RWStructuredBuffer<float> outputBuffer;

typealias CoopMatType = CoopMat<float, CoopMatScope::Subgroup, 16, 16, CoopMatMatrixUse::MatrixAccumulator>;

[numthreads(32, 1, 1)]
void computeMain()
{
    // Create a 2D tensor layout with clamp-to-edge mode
    CoopMatTensorLayout<2, CoopMatClampMode::ClampToEdge> tl;
    tl.setDimension(16);
    tl.setStride(16);

    // Create a tensor view with explicit dimensions
    CoopMatTensorView<2, true, 0, 1> tv;
    tv.setDimension(16);
    tv.setClip(0, 8, 0, 8);

    // Load a cooperative matrix from a tensor buffer using the layout and view
    let mat = CoopMatType.load(input, 0, tl, tv);

    // Store the matrix back to the buffer
    mat.store(outputBuffer, 0, tl, tv);
}
```

Detailed Explanation
--------------------

**Note**: "AnyBuffer" means some or all variants of "RWByteAddressBuffer", "ByteAddressBuffer", "RWStructuredBuffer", "StructuredBuffer", "groupshared array" "array" and/or "pointer".

### Interface implementations of CoopMat

CoopMat implements IArray<T> and IArithmetic. For the required implementation, CoopMat acts as a one-dimensional array. IArithmetic operations will be performed element-wise. Comparing two cooperative matrices will be done lexicographically.

### Member functions of CoopMat

Cooperative matrices are accessed as one-dimensional arrays in terms of language syntax. You can retrieve the length of the matrix using the `getLength()` method and access individual elements using the bracket accessor (`[]`) for both reading and writing operations.

```
void fill(T t);
void copyFrom<U>(CoopMat<U, S, M, N, R> other)
static int getRowCount();
static int getColumnCount()
static uint getLength();
```

- Load
```
static This load(AnyBuffer buffer, uint element, uint stride, CoopMatMatrixLayout matrixLayout);
static This loadAny<U, let V : int>(__constref groupshared U[V] data, uint element, uint stride,  CoopMatMatrixLayout matrixLayout);
```

- Store
```
void store(RWAnyBuffer buffer, uint element, uint stride, CoopMatMatrixLayout matrixLayout);
void storeAny<U, let V : int>(__ref groupshared U[V] data, uint element, uint stride, CoopMatMatrixLayout matrixLayout);
```

### CoopMat with CoopMatTensorLayout and CoopMatTensorView

Load and store can be performed with CoopMatTensorLayout, CoopMatTensorView and a user-defined function.

```
__generic<
    let Dim : uint32_t,
    let ClampMode : CoopMatClampMode>
static This load(
    AnyBuffer buf,
    uint elementOffset,
    CoopMatTensorLayout<Dim, ClampMode> tensorLayout);

__generic<
    let Dim : uint32_t,
    let ClampMode : CoopMatClampMode,
    let DimView : uint32_t,
    let HasDimensions : bool>
static This load(
    AnyBuffer buf,
    uint elementOffset,
    CoopMatTensorLayout<Dim, ClampMode> tensorLayout,
    CoopMatTensorView<DimView, HasDimensions> tensorView);

__generic<
    let Dim : uint32_t,
    let ClampMode : CoopMatClampMode,
    FuncType : IFunc<T, T*, uint32_t[Dim], uint32_t[Dim]>>
static This load(
    AnyBuffer buf,
    uint elementOffset,
    CoopMatTensorLayout<Dim, ClampMode> tensorLayout,
    FuncType decodeFunc);

__generic<
    let Dim : uint32_t,
    let ClampMode : CoopMatClampMode,
    let DimView : uint32_t,
    let HasDimensions : bool,
    FuncType : IFunc<T, T*, uint32_t[Dim], uint32_t[Dim]>>
static This load(
    AnyBuffer buf,
    uint elementOffset,
    CoopMatTensorLayout<Dim, ClampMode> tensorLayout,
    CoopMatTensorView<DimView, HasDimensions> tensorView,
    FuncType decodeFunc);
```

`decodeFunc` is a user-defined function that allows to decode if it was encoded.
 - A function (or functor) whose return type matches the matrix element type.
 - The first parameter is a pointer to the raw buffer data for the element.
 - The second parameter is a uint32_t[Dim] array for block coordinates.
 - The third parameter is a uint32_t[Dim] array for coordinates within the block.
 - All parameters are read-only.
 - The function is called for each matrix element, and its return value is stored in the result.

An example of `decodeFunc` will be,
```
T decodeFunc(
    const T* ptr,  // pointer to the raw data for the element
    const uint32_t[Dim] blockCoord,   // block coordinates
    const uint32_t[Dim] coordInBlock  // coordinates within the block
);
```

**TODO**: It is unclear if we can use a raw memory pointer for the first parameter.

```
__generic<
    let Dim : uint32_t,
    let ClampMode : CoopMatClampMode>
void store(
    AnyBuffer buf,
    uint elementOffset,
    CoopMatTensorLayout<Dim, ClampMode> tensorLayout);

__generic<
    let Dim : uint32_t,
    let ClampMode : CoopMatClampMode,
    let DimView : uint32_t,
    let HasDimensions : bool>
void store(
    AnyBuffer buf,
    uint elementOffset,
    CoopMatTensorLayout<Dim, ClampMode> tensorLayout,
    CoopMatTensorView<DimView, HasDimensions> tensorView);
```

### Matrix Multiply-and-Accumulate operation

`coopMatMulAdd()` performs a linear-algebraic matrix multiply of A by B and then component-wise add C.

A, B, C and result matrices must use a same scope.

The component types of A, B, C, result matrices don't need to be same.

```
__generic<
    T : __BuiltinArithmeticType,
    U : __BuiltinArithmeticType,
    V : __BuiltinArithmeticType,
    W : __BuiltinArithmeticType,
    let S : CoopMatScope,
    let M : int,
    let K : int,
    let N : int>
CoopMat<T, S, M, N, CoopMatMatrixUse::MatrixAccumulator> coopMatMulAdd(
    CoopMat<U, S, M, K, CoopMatMatrixUse::MatrixA> matA,
    CoopMat<V, S, K, N, CoopMatMatrixUse::MatrixB> matB,
    CoopMat<W, S, M, N, CoopMatMatrixUse::MatrixAccumulator> matC,
    constexpr CoopMatMatrixOperands operands = CoopMatMatrixOperands::None);
```

### Reduce operation

`coopMatReduce()` computes a matrix where each element of the result matrix is computed from a row, column, or neighborhood of the source matrix depending on `reduceMake`.

```
__generic<
    T : __BuiltinFloatingPointType,
    let S : CoopMatScope,
    let M : int,
    let N : int,
    let RM : int,
    let RN : int,
    FuncType : IFunc<T, T, T>>
void coopMatReduce(
    out CoopMat<T, S, RM, RN, CoopMatMatrixUse::MatrixAccumulator> result,
    CoopMat<T, S, M, N, CoopMatMatrixUse::MatrixAccumulator> m,
    CoopMatReduceMask reduceMask,
    DecodeFuncType combineOp);
```

`combineOp` is a user-defined function that implements `IFunc<T, T, T>`, which means the function returns a type `T` and it takes two arguments whose types are also `T`. In other words, the function takes two input values and reduces them to one value.

### Per-Element operation

Applies an operation to each element of a cooperative matrix.

```
__generic<
    T : __BuiltinArithmeticType,
    let S : CoopMatScope,
    let M : int,
    let N : int,
    let R : CoopMatMatrixUse,
    each UserDataTypes,
    FuncType : IFunc<T, uint32_t, uint32_t, T, expand each UserDataTypes>>
void coopMatPerElement(
    out CoopMat<T, S, M, N, R> result,
    CoopMat<T, S, M, N, R> m,
    FuncType elemOp,
    expand each TP userData);
```

`elemOp` is a user-defined function that implements `IFunc<T, uint32_t, uint32_t, T, ... >`. The return type is `T` and the first and second parameters take row and column values respectively. the third paramter takes a value from the cooperative matrix at the given row and column. The user-defined function can take additional user-data.

### Transpose operation

Converts a cooperative matrix to from CoopMatMatrixUse::MatrixAccumulator to CoopMatMatrixUse::MatrixB and transposes the matrix.

```
__generic<
    T : __BuiltinArithmeticType,
    let S : CoopMatScope,
    let M : int,
    let N : int>
void coopMatTransposeNV(
    out CoopMat<T, S, N, M, CoopMatMatrixUse::MatrixB> result,
    CoopMat<T, S, M, N, CoopMatMatrixUse::MatrixAccumulator> m);
```

### Generic arguments for CoopMatTensorLayout

There are five member functions to modify the internal values of CoopMatTensorLayout. The number of the parameters for the member functions depends on the value of the first generic argument. To support this syntax, we will use `extension` and define the member functions with different number of arguments.

```
__generic<
    let Dim : uint32_t,
    let ClampMode : CoopMatClampMode = CoopMatClampMode::Undefined>
struct CoopMatTensorLayout
{};

__generic<let ClampMode : CoopMatClampMode>
extension CoopMatTensorLayout<1, ClampMode>
{
    void setBlockSize(uint32_t blockSize0);
    void setStride(uint32_t stride0);
    void setDimension(uint32_t dim0);
    void slice(uint32_t offset0, uint32_t span0);
    void setClampValue(CoopMatClampMode clampMode);
}

__generic<let ClampMode : CoopMatClampMode>
extension CoopMatTensorLayout<2, ClampMode>
{
    void setBlockSize(uint32_t blockSize0, uint32_t blockSize1);
    void setStride(uint32_t stride0, uint32_t stride1);
    void setDimension(uint32_t dim0, uint32_t dim1);
    void slice(uint32_t offset0, uint32_t span0, uint32_t offset1, uint32_t span1);
    void setClampValue(CoopMatClampMode clampMode);
}

__generic<let ClampMode : CoopMatClampMode>
extension CoopMatTensorLayout<..., ClampMode>
{
    void setBlockSize(uint32_t blockSize0, uint32_t blockSize1, ...);
    void setStride(uint32_t stride0, uint32_t stride1, ...);
    void setDimension(uint32_t dim0, uint32_t dim1, ...);
    void slice(uint32_t offset0, uint32_t span0, uint32_t offset1, uint32_t span1, ...);
    void setClampValue(CoopMatClampMode clampMode);
}
```

### Member functions of CoopMatTensorLayout

The `CoopMatTensorLayout` class provides a set of functions to define and manipulate the layout of a tensor in a cooperative matrix.

- void setBlockSize(uint32_t blockSize0, ...);
- void setStride(uint32_t stride0, ...);
- void setDimension(uint32_t dim0, ...);
- void slice(uint32_t offset0, uint32_t span0, ...);
- void setClampValue(CoopMatClampMode clampMode, ...);

The `setBlockSize` function specifies the size of a block, where a block is conceptually similar to a 4x4 block used in texture compression (e.g., DXT).

The `setStride` function defines the number of blocks to the next block in each dimension. For the innermost dimension, the stride will be always 1, and the next outer dimension will have a stride equal to the number of column, and so on.

The `setDimension` function sets the overall size of the tensor in each dimension.

The `slice` function allows extracting a subset of the tensor by specifying offsets and spans for each dimension, enabling efficient sub-tensor operations.

Finally, the `setClampValue` function configures the clamping behavior using the `CoopMatClampMode` enumeration, which determines how out-of-bound accesses are handled.

### Generic arguments for CoopMatTensorView

As explained earlier, CoopMatTensorView takes (N + 2) number of generic arguments where N is a value used as the first generic argument. We could make use of variadic generic value if Slang supports it, but it will be still difficult to define the relationship between a value to the number of generic arguments.

To achieve the same syntax as GLSL does, we will use `extension` feature with a fixed number of maximum dimension value. CoopMatTensorView will be declared with a fixed number of generic argument. The unwanted arguments will have a default value.

```
__generic<
    let Dim : uint32_t,
    let HasDimensions : bool,
    let p0 : uint32_t = 0xff,
    let p1 : uint32_t = 0xff
    ...>
struct CoopMatTensorView
{
    __init()
    {
        static_assert((0 >= Dim) != (p0 < Dim), "CoopMatTensorView::Dimension[0] out of range");
        static_assert((1 >= Dim) != (p1 < Dim), "CoopMatTensorView::Dimension[1] out of range");
        ...
    }
};

__generic<
    let HasDimensions : bool,
    let p0 : uint32_t>
extension CoopMatTensorView<1, HasDimensions, p0>
{
... implement ...
};

__generic<
    let HasDimensions : bool,
    let p0 : uint32_t,
    let p1 : uint32_t>
extension CoopMatTensorView<2, HasDimensions, p0, p1>
{
... implement ...
};

__generic<
    let HasDimensions : bool,
    let p0 : uint32_t,
    let p1 : uint32_t,
    ...>
extension CoopMatTensorView<..., HasDimensions, p0, p1, ...>
{
... implement ...
};
```

### Member functions of CoopMatTensorView

Currently CoopMatTensorView is always used with CoopMatTensorLayout for loading and storing CoopMat instances. And CoopMatTensorView overrides the values set for CoopMatTensorLayout.

- void setDimension(uint32_t dim0, ...);
- void setStride(int stride0, ...);
- void setClip(uint clipRowOffset, uint clipRowSpan, uint clipColOffset, uint clipColSpan);

References
----------

- GLSL_NV_cooperative_matrix
- GLSL_NV_cooperative_matrix2
- SPV_KHR_cooperative_matrix
- SPV_NV_cooperative_matrix2
- SPV_NV_tensor_addressing

