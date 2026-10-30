# Vector and Matrix Types

## Vector Types

A `vector<T, N>` represents a vector of `N` elements of type `T` where:
- `T` is a [fundamental scalar type](types-fundamental.md)
- `N` is an [instantiation-time constant integer](generics.md) in range [1, 4] denoting the number of elements.

The default values for `T` and `N` are `float` and `4`. This is for backwards compatibility.

### Element Access

An element of a vector is accessed by the following means:
- Using the subscript operator `[]` (index `0` denotes the first element).
- Using the member access operator `.` where the elements are named `x`, `y`, `z`, `w` corresponding to indexes `0`, `1`, `2`, `3`.

**Example:**
```slang
vector<int, 4> v = { 1, 2, 3, 4 };

int tmp;

tmp = v[0]; // tmp is 1
tmp = v.w;  // tmp is 4
v[1] = 9;   // v is { 1, 9, 3, 4 };
```

Multiple elements may be referenced by specifying two or more elements after the member access operator. This
is called a _swizzle expression_, and it can be used to:
- Extract multiple elements. The resulting type is a vector with the size equal to the number of selected
  elements. The same element may be specified multiple times.
- Assign multiple elements using a vector with the size equal to the number of selected elements. The
  vector expression must be an [L-value expression](expressions-value-categories.md), and the elements must
  be unique.

**Example:**
```slang
vector<int, 4> v = { 1, 2, 3, 4 };

int2 tmp2;
int3 tmp3;

tmp2 = v.xy;                   // tmp2 is { 1, 2 }
tmp3 = v.xww;                  // tmp3 is { 1, 4, 4 }
v.xz = vector<int, 2>(-1, -3); // v becomes { -1, 2, -3, 4 }
```

### Operators

When applying an unary arithmetic operator, the operator applies to all vector elements.

**Example:**
```slang
vector<int, 4> v = { 1, 2, 3, 4 };

vector<int, 4> tmp;
tmp = -v;   // tmp is { -1, -2, -3, -4 };
```

When applying a binary arithmetic operator where the other operand is scalar, the operation applies to all vector elements with the scalar parameter.

**Example:**
```slang
vector<int, 4> v = { 1, 2, 3, 4 };

vector<int, 4> tmp;
tmp = v - 1;   // tmp is { 0, 1, 2, 3 };
tmp = 4 - v;   // tmp is { 4, 3, 2, 1 };
```

When applying a binary assignment operator where the right-hand operand is scalar, the assignment applies to all vector element with the scalar parameter.

**Example:**
```slang
vector<int, 4> v = { 1, 2, 3, 4 };

v += 1;     // v becomes { 2, 3, 4, 5 };
v = 42;     // v becomes { 42, 42, 42, 42 };
```

When applying a binary arithmetic, assignment, or comparison operator with two vectors of same length, the operator is applied element-wise.

**Example:**
```slang
vector<int, 4> v1 = { 1, 2, 3, 4 };
vector<int, 4> v2 = { 5, 6, 7, 8 };

vector<int, 4> tmp;
tmp = v1;       // tmp is { 1, 2, 3, 4 };
tmp = v1 + v2;  // tmp is { 6, 8, 10, 12 };
tmp = v1 * v2;  // tmp is { 5, 12, 21, 32 };

vector<bool, 4> cmpResult;
cmpResult = (v1 == vector<int, 4>(1, 3, 2, 4));
// cmpResult is { true, false, false, true }

v1 -= v2;       // v1 becomes { -4, -4, -4, -4 };
```

### Standard Type Aliases

Slang provides type aliases for all vectors between size 1 and 4 for fundamental scalar types. The type alias has name `<fundamental_type>N` where `<fundamental_type>` is one of the fundamental types and `N` is the vector length.

**Example:**
```slang
float4 v = { 1.0f, 2.0f, 3.0f, 4.0f }; // vector<float, 4>
int32_t2 i2 = { 1, 2 }; // vector<int, 2>
bool3 b3 = { true, false, false }; // vector<bool, 3>
```

### Memory Layout

The memory layout of a vector type is `N` contiguous values of type `T` with no padding.

The alignment of a vector type is target-defined. The alignment of `vector<T, N>` is at least the alignment of `T` and at most `N` times the alignment of `T`.


## Matrix Types

Type `matrix<T, R, C>` represents a `R`×`C` matrix of elements of type `T` where:
- `T` is a [fundamental scalar type](types-fundamental.md)
- `R` is an [instantiation-time constant integer](generics.md) in range [1, 4] denoting the number of rows.
- `C` is an [instantiation-time constant integer](generics.md) in range [1, 4] denoting the number of columns.

The default values for `T`, `R`, `C` are `float`, `4`, `4`. This is for backwards compatibility.

### Row and Element Access

A row of a matrix is accessed by the subscript operator `[]` (index `0` denotes the first row). For
`matrix<T, R, C>`, the result type is `vector<T, C>`.

An element of a matrix is accessed by the following means:
- Using row access and selecting an element of the row vector.
- Using the member access operator `.` where individual elements are named `_mrc`, where `r` is the
  zero-based row index and `c` is the zero-based column index.
- Using the member access operator `.` where individual elements are named `_rc`, where `r` is the
  one-based row index and `c` is the one-based column index. For example, `_11` denotes the same element as
  `_m00`.

Similar to vectors, multiple elements of a matrix may be referenced with a swizzle expression, that is, by
specifying two or more elements after the member access operator. The resulting type is `vector<T, N>` where
`N` is the number of selected elements. The result is an [L-value expression](expressions-value-categories.md)
if the matrix expression is an L-value expression and the elements are unique.

**Example:**
```slang
matrix<int, 3, 4> m = {
    1,  2,  3,  4,  // row index 0
    5,  6,  7,  8,  // row index 1
    9, 10, 11, 12   // row index 2
};

let row1 = m[1];           // type: vector<int, 4>  value: { 5, 6, 7, 8 }
let vec1 = m._m00_m01_m12; // type: vector<int, 3>  value: { 1, 2, 7 }
let vec2 = m[2].wzyx;      // type: vector<int, 4>  value: { 12, 11, 10, 9 }

let elem1 = m._m21;        // type: int             value: 10
let elem2 = m[2][1];       // type: int             value: 10

m._m10_m03 = { 15, 14 };   // assign m[1][0] = 15 and m[0][3] = 14
m._12_23 = { 12, 17 };     // assign m[0][1] = 12 and m[1][2] = 17
```

### Operators

When applying an unary operator, the operator applies to all matrix elements.

When applying a binary operator, it is applied element-wise. Both the left-hand side and the right-hand side operands must be matrices of the same dimensions.

The [matrix multiplication](https://en.wikipedia.org/wiki/Matrix_multiplication) is performed using function `mul()`, which has the following basic forms:
- matrix/matrix form `mul(m1, m2)` where `m1` is an `M`×`N` matrix and `m2` is an `N`×`P` matrix. The result is an `M`×`P` matrix.
- vector/matrix form `mul(v, m)` where `v` is a vector of length `N` and `m` is an `N`×`P` matrix. The result is a vector of length `P`.
  - `v` is interpreted as a row vector, *i.e.*, a `1`×`N` matrix.
- matrix/vector form `mul(m, v)` where `m` is an `M`×`N` matrix and `v` is a vector of length `N`. The result is a vector of length `M`.
  - `v` is interpreted as a column vector, *i.e.*, an `N`×`1` matrix.

> 📝 **Remark 1:** The operator `*` performs element-wise multiplication. It should be used only when the element-wise multiplication of same-sized matrices is desired.

> 📝 **Remark 2:** The operator `*` differs from GLSL, where it performs matrix multiplication. When porting code from GLSL to Slang, replace matrix multiplications using `*` with calls to `mul()`.


### Standard Type Aliases

Slang provides type aliases for all matrices between 1 and 4 rows and columns for fundamental scalar
types. The type alias has name `<fundamental_type>RxC` where `<fundamental_type>` is one of the fundamental
types, `R` is the number of rows, and `C` is the number of columns.

**Example:**
```slang
// matrix<float, 4, 3>
float4x3 m = {
    1.1f, 1.2f, 1.3f,
    2.1f, 2.2f, 2.3f,
    3.1f, 3.2f, 3.3f,
    4.1f, 4.2f, 4.3f,
};
```


### Memory Layout

Matrix types support both _row-major_ and _column-major_ memory layout.
Implementations may support command-line flags or API options to control the default layout to use for matrices.

Under row-major layout, a matrix is laid out in memory equivalently to an `R`-element array of `vector<T,C>` elements.

Under column-major layout, a matrix is laid out in memory equivalent to the row-major layout of its transpose.
That is, the layout is equivalent to a `C`-element array of `vector<T,R>` elements.

> 📝 **Remark 1:** Slang currently does *not* support the HLSL `row_major` and `column_major` modifiers to set the
> layout used for specific declarations.

The alignment of a matrix is target-specified. In general, it is at least the alignment of the element and at
most the size of the matrix rounded up to the next power of two.


### Important Note for OpenGL, Vulkan, Metal, and WebGPU Targets

Slang considers matrices as rows of vectors (row major), similar to HLSL and the usual mathematical
conventions. However, many graphics APIs including OpenGL, Vulkan, Metal, and WebGPU consider matrices as
columns of vectors (column major).

Summary of differences

|                                    | Slang and HLSL   | GLSL, SPIR-V, MSL, WGSL |
|------------------------------------|------------------|-------------------------|
| Initializer element ordering       | Row major        | Column major            |
| type for float, 3 rows × 4 columns | `float3x4`       | `mat4x3` (or similar)   |
| Element access                     | `m[row][column]` | `m[column][row]`        |

However, for efficient element access with the subscript operator `[]`, Slang reinterprets columns as rows and
vice versa on these targets. That is, a Slang `float3x4` matrix type maps to a `mat3x4` matrix type in
GLSL. This also applies to row major and column major memory layouts. Similar reinterpretation is performed
also by other compilers when compiling HLSL to SPIR-V.

Perhaps most notably, this reinterpretation results in swapped order in matrix multiplication in target
code. For example:

Slang source code:
```slang
float4 doMatMul(float4x3 m, float3 v)
{
    return mul(m, v);
}
```

Translated GLSL target code:
```glsl
vec4 doMatMul_0(mat4x3 m_0, vec3 v_0)
{
    return (((v_0) * (m_0)));
}
```
