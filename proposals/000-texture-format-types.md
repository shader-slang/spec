SP #000: Texture Format Types
=============================

This proposal introduces standard-library texture format descriptor types such as
`rgba16f`, `rgba8ui`, and `r32f` that can be used as the element argument to
Slang texture types. These types let users write the desired storage format
directly in the texture type, while preserving the existing texture data type
used by shader code.

Status
------

Status: Implementation In-Progress.

Implementation: https://github.com/shader-slang/slang/pull/11163

Author: Yong He

Reviewer:

Background
----------

Slang texture types such as `Texture2D<T>` and `RWTexture2D<T>` are implemented
in the standard library as aliases of an internal `_Texture` type. The internal
type carries a `format` value parameter so backends can distinguish storage
formats such as `rgba16f`, `rgba8ui`, or `r32f`.

That `format` value is not a good user-facing interface. It is an integer, it is
the last generic parameter of an internal type, and users are not expected to know
which integer value maps to each image format. As a result, users have tended to
write texture types in terms of only the shader-visible data type, such as
`RWTexture2D<float4>` or `RWTexture2D<uint4>`, and then rely on backend-specific
format inference or attributes where needed.

This is awkward for APIs such as Vulkan, Metal, and WebGPU, where storage texture
format is part of the resource type seen by the backend. It also makes reflection
less precise: the shader-visible data type `float4` does not say whether the
underlying storage is `rgba32f`, `rgba16f`, `rgba8unorm`, or another format that
is read or written as four floating-point components.

Proposed Approach
-----------------

The standard library should define one sealed type per supported texture storage
format. For example:

```slang
RWTexture2D<rgba16f> hdrOutput;
RWTexture2D<rgba8ui> idOutput;
Texture2D<rgba8> colorInput;
```

A texture format descriptor type conforms to a standard-library interface that
describes both the storage format and the shader-visible data type:

```slang
interface ITexelDataType
{
    associatedtype Element : __BuiltinArithmeticType;
    static const int elementCount;
}

interface ITexelElement
{
    associatedtype Element : __BuiltinArithmeticType;
    associatedtype DataType : ITexelDataType where DataType.Element == Element;
    static const int elementCount;
    static const int format;
}
```

Existing texel data types such as `float`, `float2`, `float4`, `int4`, and
`uint4` also conform to `ITexelElement`, with `DataType` equal to themselves and
`format` equal to `0`. A format value of `0` means "unspecified" and preserves
the legacy behavior where a backend or compiler pass may infer a default format.

Texture aliases should accept `T : ITexelElement` and lower to the internal
texture type using `T.DataType` as the shader-visible element type and `T.format`
as the storage format:

```slang
typealias RWTexture2D<T : ITexelElement = float4> =
    _Texture<T.DataType, __Shape2D, false, false, 0, readWrite, false, false, T.format>;
```

The exact `_Texture` parameters are an implementation detail, but the observable
semantics are:

* `RWTexture2D<rgba16f>` reads and writes `float4` values and has storage format
  `rgba16f`.
* `RWTexture2D<rgba8ui>` reads and writes `uint4` values and has storage format
  `rgba8ui`.
* `RWTexture2D<float4>` remains valid source code. Its storage format is
  unspecified at the type level unless the compiler infers a default format or a
  format attribute is used.
* Two texture types with different nonzero format operands are distinct types,
  even if their `DataType` is the same.

Detailed Explanation
--------------------

### Format descriptor types

For each image format supported by Slang, the standard library should define a
format descriptor type whose name matches the image format spelling, for example
`r32f`, `rg32f`, `rgba16f`, `rgba8`, `rgba8ui`, and `r32i`.

Each descriptor specifies:

* `Element`: the scalar type used by shader operations.
* `elementCount`: the number of scalar elements in the shader-visible data type.
* `DataType`: the shader-visible scalar or vector type.
* `format`: the internal image format enum value.

For example, conceptually:

```slang
struct rgba16f : ITexelElement
{
    typealias Element = float;
    typealias DataType = float4;
    static const int elementCount = 4;
    static const int format = /* rgba16f image format enum value */;
}

struct rgba8ui : ITexelElement
{
    typealias Element = uint;
    typealias DataType = uint4;
    static const int elementCount = 4;
    static const int format = /* rgba8ui image format enum value */;
}
```

The descriptor type is not the value type returned by texture operations.
Texture operations use `DataType`. For example:

```slang
RWTexture2D<rgba16f> tex;
float4 value = tex[int2(0, 0)];
```

### Legacy data-type arguments

Existing programs that write `Texture2D<float4>` or `RWTexture2D<uint>` should
continue to compile. These types conform to both `ITexelDataType` and
`ITexelElement`, with:

```slang
typealias DataType = ThisType;
static const int format = 0;
```

This allows source compatibility while giving new code a more precise spelling
when the storage format matters.

For writable/storage textures, the compiler may infer conventional default
formats from legacy data-type arguments when targeting APIs that require a
format. For example, `RWTexture2D<float4>` may infer `rgba32f`, and
`RWTexture2D<int4>` may infer `rgba32i`. Such inference is a compatibility
feature. New code should prefer explicit format descriptor types whenever the
resource format is known.

### Type identity and overload resolution

The storage format is part of the texture type. Therefore:

```slang
void writeHDR(RWTexture2D<rgba16f> tex);

RWTexture2D<float4> a;
RWTexture2D<rgba16f> b;

writeHDR(b); // OK
writeHDR(a); // Error: format is not known to be rgba16f
```

This rule prevents accidentally passing an unformatted or differently formatted
texture to code that depends on a specific storage representation.

### Reflection and backend behavior

Reflection should report the format carried by the texture type when it is
nonzero. Format attributes and backend-specific inference are fallbacks only
when the texture type itself has an unspecified format.

Backends should likewise treat the texture type's format operand as the source of
truth. If the format operand is nonzero, it determines the emitted SPIR-V image
format, Metal texture format/access constraints, WGSL storage texture format, and
any related capabilities. If the operand is zero, existing fallback behavior is
preserved.

Alternatives Considered
-----------------------

### Keep exposing the integer `format` parameter

The internal `_Texture` type already has a `format` value parameter. Exposing
that parameter directly would avoid adding new descriptor types, but it would
make users write non-obvious integer constants in type arguments and would expose
an implementation detail of the core module.

### Use attributes only

An attribute such as `[format("rgba16f")] RWTexture2D<float4>` can describe the
same resource, but it separates the format from the type. That makes generic
constraints, overloads, type aliases, and reflection less direct. A format that
is semantically part of the texture type should be represented in the type.

### Make `rgba16f` be an alias for `float4`

If `rgba16f` were merely a type alias for `float4`, then `RWTexture2D<rgba16f>`
would be indistinguishable from `RWTexture2D<float4>`. The proposal needs the
storage format to participate in type identity, so a distinct descriptor type is
required.

### Require explicit formats everywhere

The language could reject `RWTexture2D<float4>` and require
`RWTexture2D<rgba32f>` or another explicit format. That would be clearer for new
code, but it would break a large amount of existing HLSL-style code. This
proposal keeps legacy data-type arguments valid while encouraging explicit
format descriptor types for new code.
