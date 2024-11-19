Types {#type}
=====

<div class=issue>
The text of this chapter is largely still written in a more guide/reference style than in anything formal.

It is important to have the specification include a list of the major built-in types that this chapter currently documents, but those are not the only things relevant to types that need to be discussed.

A key concept that this chapter needs to discuss is that there are a few distinct \emph{kinds} of types that Slang traffics in:


* \emph{Proper} types, such as `Int` and \code{RWStructuredBuffer<Float>}, which can be used for local variables, function parameters, etc.

* \emph{Interface} types, which include both references to [=interface declaration=]s, but also conjunctions of interface types. Interface types are distinct from proper types. Interfaces can be used as constraints on generic type parameters, but proper types cannot. Similarly, an interface type is not semantically valid as a local variable or function parameter (the current Slang compiler simply translates such invalid usages to existential types, which are proper).

* \emph{Generic} types, which are the types of references to generic declarations. The current Slang language rules do not allow developers to utter generic types, and the semantics do not treat them as proper types. However, intermediate expressions of generic type can easily appear when checking Slang expressions.


The type-checking rules will likely need to be able to refer to certain other types that are not part of the user-exposed Slang type system.
From the judgements that have been sketched so far, it seems clear that we at least need:


* Some kind of ``type type'' or other way to refer to the logical ``type'' of an expression that itself names a (specific) type. This might be spelled $\textsc{Exactly}(...)$. So, for example, if the name \code{I} is bound as an alias for `Int` in a certain context, the typing judgements would determine $\code{I} : \textsc{Exactly}(`Int`)$.

* Some kind of ``overload group'' type, which represents that a given expression resolves only to a group of candidates, such that further disambiguation is needed. Such a type might be spelled $\textsc{Overloaded}(...)$, where the arguments are the types of the candidates.

* A set of ``reference'' types, such as `in`out Int}, that can be used to represent the value category (e.g., l-value vs. r-value) of an expression. Subtyping/coercion rules would then need to support, e.g., passing a `ref` Int} where an `in`out Int} is expected, etc.


</div>

This section defines the kinds of types supported by Slang.


Types in Slang do not necessarily prescribe a single <dfn>layout</dfn> in memory.
The discussion of each type will specify any guarantees about layout it provides; any details of layout not specified here may depend on the target platform, compiler options, and context in which a type is used.

Void Type {#type.unit}
---------

The type \code{void} contains no data and has a single, unnamed, value.

A \code{void} value takes up no space, and thus does not affect the layout of types.
Formally, a \code{void} value behaves as if it has a size of zero bytes, and one-byte alignment.

Scalar Types {#type.scalar}
------------

### Boolean Type ### {#type.bool}

The type \code{bool} is used to represent Boolean truth values: `true` and `false`.

The size of a \code{bool} varies across target platforms; programs that need to ensure a matching in-memory layout between targets should not use \code{bool} for in-memory data structures.
On all platforms, the \code{bool} type must be <dfn>naturally aligned</dfn> (its alignment is its size).

### Integer Types ### {#type.int}

The following integer types are defined:

\begin{tabular}{ |c|c| }
  \hline
  Name & Description \\
  \hline
  `int8_t` & 8-bit signed integer \\
  `int16_t` & 16-bit signed integer \\
  `int` & 32-bit signed integer \\
  `int64_t` & 64-bit signed integer \\
  \code{uint8\_t} & 8-bit unsigned integer \\
  \code{uint16\_t} & 16-bit unsigned integer \\
  \code{uint} & 32-bit unsigned integer \\
  \code{uint64\_t} & 64-bit unsigned integer \\
  \hline
\end{tabular}

All signed integers use two's complement representation.
All arithmetic operations on integers (both signed and unsigned) wrap on overflow/underflow.

All target platforms must support the `int`} and \code{uint} types.
Specific target platforms may not support the other integer types.

Issue: "target platforms" links outside the specification to target-compatibility.md

All integer types are stored in memory with their natural size and alignment on all targets that support them.

### Floating-Point Types ### {#type.float}

The following floating-point type are defined:

\begin{tabular}{ |c|c| }
  \hline
  Name & Description \\
  \hline
  \code{half} & 16-bit floating-point number (1 sign bit, 5 exponent bits, 10 fraction bits) \\
  \code{float} & 32-bit floating-point number (1 sign bit, 8 exponent bits, 23 fraction bits) \\
  \code{double} & 64-bit floating-point number (1 sign bit, 11 exponent bits, 52 fraction bits) \\
  \hline
\end{tabular}

All floating-point types are laid out in memory using the matching IEEE 754 standard format (\code{binary16}, \code{binary32}, \code{binary64}).
Target platforms may define their own rules for rounding, precision, denormals, infinities, and not-a-number values.

All target platforms must support the \code{float} type.
Specific targets may not support the other floating-point types.

Issue: "targets" links outside the specification to target-compatibility.md

All floating-point types are stored in memory with their natural size and alignment on all targets that support them.

Vector Types {#type.vector}
------------

A vector type is written as `vector<T, N>` and represents an \code{N}-element vector with elements of type \code{T}.
The <dfn>element type</dfn> \code{T} must be one of the built-in scalar types, and the <dfn>element count</dfn> \code{N} must be a specialization-time constant integer.
The element count must be between 2 and 4, inclusive.

A vector type allows subscripting of its elements like an array, but also supports element-wise arithmetic on its elements.
<dfn>Element-wise arithmetic</dfn> means mapping unary and binary operators over the elements of a vector to produce a vector of results:

```
vector<int,4> a = { 1, 2, 30, 40 };
vector<int,4> b = { 10, 20, 3, 4 };

-a; // yields { -1, -2, -30, -40 }
a + b; // yields { 11, 22, 33, 44 }
b / a; // yields { 10, 10, 0, 0 }
a > b; // yields { false, false, true, true }
```

A vector type is laid out in memory as \code{N} contiguous values of type \code{T} with no padding.
The alignment of a vector type may vary by target platforms.
The alignment of `vector<T,N>` will be at least the alignment of \code{T} and may be at most \code{N} times the alignment of \code{T}.

As a convenience, Slang defines built-in type aliases for vectors of the built-in scalar types.
E.g., declarations equivalent to the following are provided by the Slang standard library:

```
typealias float4 = vector<float, 4>;
typealias int8_t3 = vector<int8_t, 3>;
```

### Legacy Syntax ### {#type.vector.legacy}

For compatibility with older codebases, the generic \code{vector} type includes default values for \code{T} and \code{N}, being declared as:

```
struct vector<T = float, let N : int = 4> { ... }
```

This means that the bare name \code{vector} may be used as a type equivalent to \code{float4}:

```
// All of these variables have the same type
vector a;
float4 b;
vector<float> c;
vector<float, 4> d;
```

Matrix Types {#type.matrix}
------------

A matrix type is written as `matrix<T, R, C>` and represents a matrix of \code{R} rows and \code{C} columns, with elements of type \code{T}.
The element type \code{T} must be one of the built-in scalar types.
The <dfn>row count</dfn> \code{R} and <dfn>column count</dfn> \code{C} must be specialization-time constant integers.
The row count and column count must each be between 2 and 4, respectively.

A matrix type allows subscripting of its rows, similar to an \code{R}-element array of `vector<T,C>` elements.
A matrix type also supports element-wise arithmetic.

Matrix types support both <dfn>row-major</dfn> and <dfn>column-major</dfn> memory layout.
Implementations may support command-line flags or API options to control the default layout to use for matrices.

Note: Slang currently does not support the HLSL \code{row\_major} and \code{column\_major} modifiers to set the layout used for specific declarations.

Under row-major layout, a matrix is laid out in memory equivalently to an \code{R}-element array of `vector<T,C>` elements.

Under column-major layout, a matrix is laid out in memory equivalent to the row-major layout of its transpose.
This means it will be laid out equivalently to a \code{C}-element array of `vector<T,R>` elements.

As a convenience, Slang defines built-in type aliases for matrices of the built-in scalar types.
E.g., declarations equivalent to the following are provided by the Slang standard library:

```
typealias float3x4 = matrix<float, 3, 4>;
typealias int64_t4x2 = matrix<int64_t, 4, 2>;
```

Note: For programmers using OpenGL or Vulkan as their graphics API, and/or who are used to the GLSL language,
it is important to recognize that the equivalent of a GLSL \code{mat3x4} is a Slang \code{float3x4}.
This is despite the fact that GLSL defines a \code{mat3x4} as having 3 \emph{columns} and 4 \emph{rows}, while a Slang \code{float3x4} is defined as having 3 rows and 4 columns.
This convention means that wherever Slang refers to "rows" or "columns" of a matrix, the equivalent terms in the GLSL, SPIR-V, OpenGL, and Vulkan specifications are "column" and "row" respectively (\emph{including} in the compound terms of "row-major" and "column-major")
While it may seem that this choice of convention is confusing, it is necessary to ensure that subscripting with \code{[]} can be efficiently implemented on all target platforms.
This decision in the Slang language is consistent with the compilation of HLSL to SPIR-V performed by other compilers.

### Legacy Syntax ### {#type.matrix.legacy}

For compatibility with older codebases, the generic \code{matrix} type includes default values for \code{T}, \code{R}, and \code{C}, being declared as:

```
struct matrix<T = float, let R : int = 4, let C : int = 4> { ... }
```

This means that the bare name \code{matrix} may be used as a type equivalent to \code{float4x4}:

```
// All of these variables have the same type
matrix a;
float4x4 b;
matrix<float, 4, 4> c;
```

Structure Types {#type.struct}
---------------

Structure types are introduced with `struct` declarations, and consist of an ordered sequence of named and typed fields:

```
struct S
{
    float2 f;
    int3 i;
}
```

### Standard Layout ### {#type.struct.layout.standard}

The <dfn>standard layout</dfn> for a structure type uses the following algorithm:

* Initialize variables \code{size} and \code{alignment} to zero and one, respectively
* For each field \code{f} of the structure type:
  * Update \code{alignment} to be the maximum of \code{alignment} and the alignment of \code{f}
  * Set \code{size} to the smallest multiple of \code{alignment} not less than \code{size}
  * Set the offset of field \code{f} to \code{size}
  * Add the size of \code{f} to \code{size}

When this algorithm completes, \code{size} and \code{alignment} will be the size and alignment of the structure type.

Most target platforms do not use the standard layout directly, but it provides a baseline for defining other layout algorithms.
Any layout for structure types must guarantee an alignment at least as large as the standard layout.

### C-Style Layout ### {#type.struct.layout.c}

C-style layout for structure types differs from standard layout by adding an additional final step:

* Set `size` to the smallest multiple of `alignment` not less than `size`

This mirrors the layout rules used by typical C/C++ compilers.

### D3D Constant Buffer Layout ### {#type.struct.layout.d3d.cbuffer}

D3D constant buffer layout is similar to standard layout with two differences:

* The initial alignment is 16 instead of one}
* If a field would have <dfn>improper straddle</dfn>, where the interval \code{(fieldOffset, fieldOffset+fieldSize)} (exclusive on both sides) contains any multiple of 16, \emph{and} the field offset is not already a multiple of 16, then the offset of the field is adjusted to the next multiple of 16

Array Types {#type.array}
-----------

An <dfn>array type</dfn> is either a statically-sized or dynamically-sized array type.

A known-size array type is written `T[N]` where \code{T} is a type and \code{N} is a specialization-time constant integer.
This type represents an array of exactly \code{N} values of type \code{T}.

An unknown-size array type is written \code{T[]} where \code{T} is a type.
This type represents an array of some fixed, but statically unknown, size.

Note: Unlike in C and C++, arrays in Slang are always value types, meaning that assignment and parameter passing of arrays copies their elements.

### Declaration Syntax ### {#type.array.decl}

For variable and parameter declarations using traditional syntax, a variable of array type may be declared by using the element type \code{T} as a type specifier (before the variable name) and the `[N]` to specify the element count after the variable name:

```
int a[10];
```

Alternatively, the array type itself may be used as the type specifier:

```
int[10] a;
```

When using the `var` or `let` keyword to declare a variable, the array type must not be split:

```
var a : int[10];
```

<div class=note>
When declaring arrays of arrays (often thought of as "multidimensional arrays") a programmer must be careful about the difference between the two declaration syntaxes.
The following two declarations are equivalent:
```
int[3][5] a;
int a[5][3];
```
In each case, \code{a} is a five-element array of three-element arrays of `int`s.
However, one declaration orders the element counts as \code{[3][5]} and the other as \code{[5][3]}.
</div>

### Element Count Inference ### {#type.array.inference}

When a variable is declared with an unknown-size array type, and also includes an initial-value expression:

```
int a[] = { 0xA, 0xB, 0xC, 0xD };
```

The compiler will attempt to infer an element count based on the type and/or structure of the initial-value expression.
In the above case, the compiler will infer an element count of 4 from the structure of the initializer-list expression.
Thus the preceding declaration is equivalent to:

```
int a[4] = { 0xA, 0xB, 0xC, 0xD };
```

A variable declared in this fashion semantically has a known-size array type and not an unknown-size array type; the use of an unknown-size array type for the declaration is just a convenience feature.

### Standard Layout ### {#type.array.layout.std}

The <dfn>stride</dfn> of a type is the smallest multiple of its alignment not less than its size.

Using the standard layout for an array type \code{T[]} or `T[N]`:

* The <dfn>element stride</dfn> of the array type is the stride of its element type \code{T}
* Element \code{i} of the array starts at an offset that is \code{i} times the element stride of the array
* The alignment of the array type is the alignment of \code{T}
* The size of an unknown-size array type is unknown
* The size of a known-size array with zero elements is zero
* The size of a known-size array with a nonzero number \code{N} of elements is the size of \code{T} plus \code{N - 1} times the element stride of the array

### C-Style Layout ### {#type.array.layout.c}

The C-style layout of an array type differs from the standard layout in that the size of a known-size array with a nonzero number \code{N} of elements is \code{N} times the element stride of the array.

### D3D Constant Buffer Layout ### {#type.array.layout.d3d.cbuffer}

The D3D constant buffer layout of an array differs from the standard layout in that the element stride of the array is set to the smallest multiple of the alignment of \code{T} that is not less than the stride of \code{T}

This Type {#type.this}
---------

Within the body of a structure or interface declaration, the keyword \code{This} may be used to refer to the enclosing type.
Inside of a structure type declaration, \code{This} refers to the structure type itself.
Inside of an interface declaration, \code{This} refers to the concrete type that is conforming to the interface (that is, the type of `this`).

Opaque Types {#type.opaque}
------------

<dfn>Opaque</dfn> types are built-in types that (depending on the target platform) may not have a well-defined size or representation in memory.
Similar languages may refer to these as "resource types" or "object types."

The full list of opaque types supported by Slang can be found in the standard library reference, but important examples are:

* Texture types such as \code{Texture2D<T>}, \code{TextureCubeArray<T>}, and \code{RWTexture2DMS<T>}
* Sampler state types: \code{SamplerState} and \code{SamplerComparisonState}
* Buffer types like \code{ConstantBuffer<T>} and  \code{StructuredBuffer<T>}
* Parameter blocks: \code{ParameterBlock<T>}

Layout for opaque types depends on the target platform, and no specific guarantees can be made about layout rules across platforms.

Known and Unknown Size {#type.size}
----------------------

Every type has either known or unknown size.
Types with unknown size arise in a few ways:

* An unknown-size array type has unknown size
* A structure type has unknown size if any field type has unknown size

The use of types with unknown size is restricted as follows:

* A type with unknown size cannot be used as the element type of an array
* A type with unknown size can only be used as the last field of a structure type
* A type with unknown size cannot be used as a generic argument to specialize a user-defined type, function, etc. Specific built-in generic types/functions may support unknown-size types, and this will be documented on the specific type/function.
