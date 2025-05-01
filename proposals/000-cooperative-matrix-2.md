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

- HLSL: HLSL supports Cooperative vector and Cooperative Matrix 1 at the time of writing this document.


Proposed Approach
-----------------
Introduce new types and functions in Slang to provide first-class support for cooperative matrices and tensors, closely following the new SPIRV features, but integrated with Slang's type system and generics.

Three new types are needed: CoopMat, TensorLayout and TensorView. The types use a few generic arguments whose values must be compile-time constants.

### New types

#### CoopMat

CoopMat represents a GPU-optimized matrix type enabling distributed, high-performance matrix operations across hardware scopes.

- CoopMat<T, S, M, N, R>: Cooperative matrix type parameterized by element type, scope, dimensions, and matrix use.
  - T: The element type (e.g., float, int, half)
  - S: The hardware scope (see CoopMatScope) over which the matrix is distributed
  - M: The number of rows in the matrix
  - N: The number of columns in the matrix
  - R: The matrix use (see CoopMatMatrixUse), indicating its role in matrix operations
  - implements IArray<T:IArithmetic> and IArithmetic.

Note that a cooperative matrix must be declared with one of three "uses": MatrixA, MatrixB, or MatrixAccumulator. Each operation specialized for cooperative matrices expects specific uses for its operands. For example, a matrix declared as MatrixA cannot be used as MatrixB.

#### TensorLayout

While not directly analogous, TensorLayout can be loosely compared to the concept of a "subregion" in texture handling. It defines a smaller section of the structure and organization of data within a cooperative matrix tensor.

- TensorLayout<Dim, ClampMode>: Describes the layout of a tensor for addressing.
  - Dim: The number of dimensions of the tensor layout (e.g., 2 for a 2D tensor).
  - ClampMode: The clamping or boundary mode for tensor addressing (see CoopMatClampMode).
  - It can hold following data for each dimension: blockSize, layoutDimension, stride, offset and span. [See SPIRV spec](https://github.khronos.org/SPIRV-Registry/extensions/NV/SPV_NV_cooperative_matrix2.html) for more explanation.

#### TensorView

Similarly, TensorView can be thought of as somewhat similar to a "TextureView" in texture handling. It allows for reinterpreting or accessing a given cooperative matrix tensor in a specific way without modifying the underlying data.

- TensorView<Dim, HasDimensions, p0, p1 ... p{Dim-1} >: Describes a view into a tensor.
  - Dim: The number of dimensions of the tensor view.
  - HasDimensions: Boolean indicating whether explicit dimensions are set for the view.
  - p0, p1, ... p{Dim-1}: A compile-time list specifying the permutation of dimensions for the view. Each pi indicates which source dimension is mapped to the i-th dimension of the view.
  - It can hole following data: permutation, viewDimension, viewStride, clipRowOffset, clipRowSpan, clipColOffset, clipColSpan. [See SPIRV spec](https://github.khronos.org/SPIRV-Registry/extensions/NV/SPV_NV_cooperative_matrix2.html) for more explanation.

TensorView takes (N + 2) number of generic arguments where N is a value given as a first generic argument. As an example, when the first value is 2, TensorView must use 4 generic arguments. More examples will be `TensorView<1, false, 0>`, `TensorView<2, true, 0, 1>` and `TensorView<3, false, 0, 2, 1>`.

The first generic argument to `TensorView` indicates the dimensionality, and the trailing values indicates the re-ordering of the dimension. A common use cases are `TensorView<2, false, 0, 1>` for row-major-matrix load and store, and `TensorView<2, false, 1, 0>` for column-major-matrix load and store.

Note that TensorLayout and TensorView are only for loading and storing of CoopMat instances.

### New Enums

- MemoryScope: Specifies the hardware scope over which the data is distributed.
  - CrossDevice: Scope crosses multiple devices.
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

- CoopMatClampMode: Specifies the clamping or boundary mode for tensor addressing.
  - Undefined: No clamping mode specified.
  - Constant: Clamp to a constant value.
  - ClampToEdge: Clamp to the edge of the tensor.
  - Repeat: Repeat the tensor data (wrap around).
  - RepeatMirrored: Repeat the tensor data with mirroring at the boundaries.

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
    let matC = CoopMatCType.Load(inputC, elementOffset, stride, CoopMatMatrixLayout::RowMajor);

    // ( 3.0 * 5.0 ) * 16 + 1.0 = 241.0
    // CHECK-COUNT-256: 241.0
    let result = coopMatMulAdd(matA, matB, matC);

    // Store the result to a ByteAddressBuffer.
    result.Store(outputBuffer, 0, 16, CoopMatMatrixLayout::RowMajor);
}
```

### Hello World Example 2
```
ByteAddressBuffer input;
RWStructuredBuffer<float> outputBuffer;

typealias CoopMatType = CoopMat<float, CoopMatScope::Subgroup, 32, 32, CoopMatMatrixUse::MatrixAccumulator>;

[numthreads(32, 1, 1)]
void computeMain()
{
    // Create a 2D tensor layout with clamp-to-edge mode
    TensorLayout<2, CoopMatClampMode::ClampToEdge> tensorLayout;
    tensorLayout = tensorLayout.setDimension(16, 16);
    tensorLayout = tensorLayout.setStride(32, 1);

    // Create a tensor view with explicit dimensions
    TensorView<2, true, 0, 1> tensorView;
    tensorView = tensorView.setDimension(16, 16);
    tensorView = tensorView.setClip(0, 8, 0, 8);

    // Load a cooperative matrix from a tensor buffer using the layout and view
    let mat = CoopMatType.Load(input, 0, tensorLayout, tensorView);

    // Store the matrix back to the buffer
    mat.Store(outputBuffer, 0, tensorLayout, tensorView);
}
```

Detailed Explanation
--------------------

**Note**: "AnyBuffer" means some or all variants of "RWByteAddressBuffer", "ByteAddressBuffer", "RWStructuredBuffer", "StructuredBuffer", "groupshared array" "array" and/or "pointer".

### Interface implementations of CoopMat

CoopMat implements IArray<T:IArithmetic> and IArithmetic. For the required implementation, CoopMat acts as a one-dimensional array. IArithmetic operations will be performed element-wise. Comparing two cooperative matrices will be done lexicographically.

### Member functions of CoopMat

Cooperative matrices are accessed as one-dimensional arrays in terms of language syntax. You can retrieve the length of the matrix using the `GetLength()` method and access individual elements using the bracket accessor (`[]`) for both reading and writing operations.

```
struct CoopMat
{
    void fill(T t);
    void copyFrom<U>(CoopMat<U, S, M, N, R> other);
    static int GetRowCount();
    static int GetColumnCount();
    static uint GetLength();
};
```

- Load
```
struct CoopMat
{
    static This Load<let matrixLayout : CoopMatMatrixLayout>(AnyBuffer buffer, uint element, uint stride);
    static This Load<let matrixLayout : CoopMatMatrixLayout, U : IArithmetic, let V : int>(__constref groupshared U[V] data, uint element, uint stride);
};
```

- Store
```
struct CoopMat
{
    void Store<let matrixLayout : CoopMatMatrixLayout>(AnyRWBuffer buffer, uint element, uint stride);
    void Store<let matrixLayout : CoopMatMatrixLayout, U : IArithmetic, let V : int>(__ref groupshared U[V] data, uint element, uint stride);
};
```

- Transpose operation

  `Transpose()` Converts a cooperative matrix to from CoopMatMatrixUse::MatrixAccumulator to CoopMatMatrixUse::MatrixB and transposes the matrix.
```
struct CoopMat
{
    CoopMat<T, S, N, M, CoopMatMatrixUse::MatrixB> Transpose();
};
```

- Reduce operations
  - `ReduceRow()`: Reduce across each row of the matrix.
  - `ReduceColumn()`: Reduce across each column of the matrix.
  - `ReduceRowAndColumn()`: Reduce across both rows and columns (full matrix reduction).
  - `ReduceTwoByTwo()`: Reduce over each 2x2 block within the matrix.
```
struct CoopMat
{
    __generic<
        let RN : int>
    CoopMat<T, S, M, RN, CoopMatMatrixUse::MatrixAccumulator> ReduceRow(
        functype(T, T) -> T combineOp);

    __generic<
        let RM : int>
    CoopMat<T, S, RM, N, CoopMatMatrixUse::MatrixAccumulator> ReduceColumn(
        functype(T, T) -> T combineOp);

    __generic<
        let RM : int,
        let RN : int>
    CoopMat<T, S, RM, RN, CoopMatMatrixUse::MatrixAccumulator> ReduceRowAndColumn(
        functype(T, T) -> T combineOp);

    CoopMat<T, S, M / 2, N / 2, CoopMatMatrixUse::MatrixAccumulator> ReduceTwoByTwo(
        functype(T, T) -> T combineOp);
};
```

`combineOp` is a user-defined function that returns a type `T` and takes two arguments whose types are also `T`. In other words, the function takes two input values and reduces them to one value.

### CoopMat with TensorLayout and TensorView

Load and store can be performed with TensorLayout, TensorView and a user-defined function.

```
struct CoopMat
{
    __generic<
        let Dim : uint32_t,
        let ClampMode : CoopMatClampMode>
    static This Load(
        AnyBuffer buf,
        uint elementOffset,
        TensorLayout<Dim, ClampMode> tensorLayout);

    __generic<
        let Dim : uint32_t,
        let ClampMode : CoopMatClampMode,
        let DimView : uint32_t,
        let HasDimensions : bool,
        let p0 : uint32_t = 0xff,
        let p1 : uint32_t = 0xff,
        ...>
    static This Load(
        AnyBuffer buf,
        uint elementOffset,
        TensorLayout<Dim, ClampMode> tensorLayout,
        TensorView<DimView, HasDimensions, p0, p1, ...> tensorView);

    __generic<
        U,
        let Dim : uint32_t,
        let ClampMode : CoopMatClampMode>
    static This Load(
        AnyBuffer buf,
        uint elementOffset,
        TensorLayout<Dim, ClampMode> tensorLayout,
        functype(const U*, uint32_t[Dim], uint32_t[Dim]) -> T decodeFunc);

    __generic<
        U,
        let Dim : uint32_t,
        let ClampMode : CoopMatClampMode,
        let DimView : uint32_t,
        let HasDimensions : bool,
        let p0 : uint32_t = 0xff,
        let p1 : uint32_t = 0xff,
        ...>
    static This Load(
        AnyBuffer buf,
        uint elementOffset,
        TensorLayout<Dim, ClampMode> tensorLayout,
        TensorView<DimView, HasDimensions, p0, p1, ...> tensorView,
        functype(const U*, uint32_t[Dim], uint32_t[Dim]) -> T decodeFunc);
};
```

`decodeFunc` is a user-defined function that allows to decode if it was encoded.
 - A function (or functor) whose return type matches the matrix element type.
 - The first parameter, `U`, is a pointer to the encoded buffer data for the element.
 - The second parameter is a uint32_t[Dim] array for block coordinates.
 - The third parameter is a uint32_t[Dim] array for coordinates within the block.
 - All parameters are read-only.
 - The function is called for each matrix element, and its return value is stored in the result.

Currently the decodeFunc is not allowed to be used with sharedmemory.

An example of `decodeFunc` will be,
```
__generic<
    T : __BuiltinArithmeticType,
    U,
    let Dim : uint32_t>
T decodeFunc(
    const U* ptr,  // pointer to the encoded data for the element
    const uint32_t[Dim] blockCoord,   // block coordinates
    const uint32_t[Dim] coordInBlock  // coordinates within the block
);
```

```
__generic<
    let Dim : uint32_t,
    let ClampMode : CoopMatClampMode>
void Store(
    AnyRWBuffer buf,
    uint elementOffset,
    TensorLayout<Dim, ClampMode> tensorLayout);

__generic<
    let Dim : uint32_t,
    let ClampMode : CoopMatClampMode,
    let DimView : uint32_t,
    let HasDimensions : bool,
    let p0 : uint32_t = 0xff,
    let p1 : uint32_t = 0xff,
    ...>
void Store(
    AnyRWBuffer buf,
    uint elementOffset,
    TensorLayout<Dim, ClampMode> tensorLayout,
    TensorView<DimView, HasDimensions, p0, p1, ...> tensorView);
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
    CoopMat<W, S, M, N, CoopMatMatrixUse::MatrixAccumulator> matC);
```

### Map-Element operation

Applies an operation to each element of cooperative matrices.

There are two variants to perform map-element operation: one is with a member function `CoopMat` type and another is with a member function of `Tuple` type.

```
struct CoopMat<...>
{
    // One matrix case.
    CoopMat<T, S, M, N, R> MapElement(
        IFunc<T, uint32_t, uint32_t, T> mapOp);
};

extension<
    each Ts : __BuiltinArithmeticType,
    let M : int,
    let N : int,
    let R : CoopMatMatrixUse>
Tuple<expand CoopMat<each Ts, M, N, R>>
{
    // For multiple matrices.
    __generic<
        T : __BuiltinArithmeticType>
    CoopMat<T, M, N, R> MapElement(
        IFunc<T, uint32_t, uint32_t, expand each Ts> mapOp);
};
```

`mapOp` is a user-defined function that implements `IFunc<T, uint32_t, uint32_t, T0, T1, ...>`.
 - The first parameter is the row index (uint32_t row) of the current matrix element.
 - The second parameter is the column index (uint32_t col) of the current matrix element.
 - The next parameters (T0, T1, ...) are the corresponding elements from each input cooperative matrix at position (row, col).
 - The return value is used as the value for the output matrix at (row, col).

An example of `mapOp` will be as following,
```
CoopMat<float, ...> matA, matB, matC;

let r1 = matA.MapElement((uint32_t x, uint32_t y, float a) => a * a);

let myMapOp = (uint32_t x, uint32_t y, float a, float b, float c) => (a + b) * c;
let r2 = (matA, matB, matC).MapElement(myMapOp);
```

### Generic arguments for TensorLayout

There are five member functions to modify the internal values of TensorLayout. The number of the parameters for the member functions depends on the value of the first generic argument. To support this syntax, we will use `extension` and define the member functions with different number of arguments.

```
__generic<
    let Dim : uint32_t,
    let ClampMode : CoopMatClampMode = CoopMatClampMode::Undefined>
struct TensorLayout
{};

__generic<let ClampMode : CoopMatClampMode>
extension TensorLayout<1, ClampMode>
{
    This BlockSize(uint32_t blockSize0);
    This Stride(uint32_t stride0);
    This Dimension(uint32_t dim0);
    This Slice(uint32_t offset0, uint32_t span0);
    This ClampValue(CoopMatClampMode clampMode);
}

__generic<let ClampMode : CoopMatClampMode>
extension TensorLayout<2, ClampMode>
{
    This BlockSize(uint32_t blockSize0, uint32_t blockSize1);
    This Stride(uint32_t stride0, uint32_t stride1);
    This Dimension(uint32_t dim0, uint32_t dim1);
    This Slice(uint32_t offset0, uint32_t span0, uint32_t offset1, uint32_t span1);
    This ClampValue(CoopMatClampMode clampMode);
}

__generic<let ClampMode : CoopMatClampMode>
extension TensorLayout<..., ClampMode>
{
    This BlockSize(uint32_t blockSize0, uint32_t blockSize1, ...);
    This Stride(uint32_t stride0, uint32_t stride1, ...);
    This Dimension(uint32_t dim0, uint32_t dim1, ...);
    This Slice(uint32_t offset0, uint32_t span0, uint32_t offset1, uint32_t span1, ...);
    This ClampValue(CoopMatClampMode clampMode);
}
```

### Member functions of TensorLayout

The `TensorLayout` class provides a set of functions to define and manipulate the layout of a tensor in a cooperative matrix.

- This BlockSize(uint32_t blockSize0, ...);
- This Stride(uint32_t stride0, ...);
- This Dimension(uint32_t dim0, ...);
- This Slice(uint32_t offset0, uint32_t span0, ...);
- This ClampValue(CoopMatClampMode clampMode, ...);

The `BlockSize` function specifies the size of a block, where a block is conceptually similar to a 4x4 block used in texture compression (e.g., DXT).

The `Stride` function defines the number of blocks to the next block in each dimension. For the innermost dimension, the stride will be most likely 1, and the next outer dimension will have a stride equal to the number of columns, and so on.

The `Dimension` function sets the overall size of the tensor in each dimension.

The `Slice` function allows extracting a subset of the tensor by specifying offsets and spans for each dimension, enabling efficient sub-tensor operations.

Finally, the `ClampValue` function configures the clamping behavior using the `CoopMatClampMode` enumeration, which determines how out-of-bound accesses are handled.

### Generic arguments for TensorView

As explained earlier, TensorView takes (N + 2) number of generic arguments where N is a value used as the first generic argument. We could make use of variadic generic value if Slang supports it, but it will be still difficult to define the relationship between a value to the number of generic arguments.

To achieve the same syntax as GLSL does, we will use `extension` feature with a fixed number of maximum dimension value. TensorView will be declared with a fixed number of generic argument. The unwanted arguments will have a default value.

```
__generic<
    let Dim : uint32_t,
    let HasDimensions : bool,
    let p0 : uint32_t = 0xff,
    let p1 : uint32_t = 0xff
    ...>
struct TensorView
{
    __init()
    {
        static_assert((0 >= Dim) != (p0 < Dim), "TensorView::Dimension[0] out of range");
        static_assert((1 >= Dim) != (p1 < Dim), "TensorView::Dimension[1] out of range");
        ...
    }
};

__generic<
    let HasDimensions : bool,
    let p0 : uint32_t>
extension TensorView<1, HasDimensions, p0>
{
... implement ...
};

__generic<
    let HasDimensions : bool,
    let p0 : uint32_t,
    let p1 : uint32_t>
extension TensorView<2, HasDimensions, p0, p1>
{
... implement ...
};

__generic<
    let HasDimensions : bool,
    let p0 : uint32_t,
    let p1 : uint32_t,
    ...>
extension TensorView<..., HasDimensions, p0, p1, ...>
{
... implement ...
};
```

* Note: We will limit the max number of dimension to 5, since that is the current limit for SPIRV.

### Member functions of TensorView

Currently TensorView is always used with TensorLayout for loading and storing CoopMat instances. And TensorView overrides the values set for TensorLayout.

- This Dimension(uint32_t dim0, ...);
- This Stride(int stride0, ...);
- This Clip(uint clipRowOffset, uint clipRowSpan, uint clipColOffset, uint clipColSpan);

References
----------

- GLSL_NV_cooperative_matrix
- GLSL_NV_cooperative_matrix2
- SPV_KHR_cooperative_matrix
- SPV_NV_cooperative_matrix2
- SPV_NV_tensor_addressing

