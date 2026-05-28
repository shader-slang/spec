SP #040: Texture Format Types
=============================

This proposal introduces standard-library texture format descriptor types such as
`RGBA16F`, `RGBA8UI`, and `R32F` that can be used as the element argument to
Slang texture types. These types let users write the desired storage format
directly in the texture type, while preserving the existing shader-visible data
type used by texture operations.

Status
------

Status: Implementation In-Progress
([shader-slang/slang#11344](https://github.com/shader-slang/slang/pull/11344)).

Author: Yong He

Reviewer:

Background
----------

Slang texture types such as `Texture2D<T>` and `RWTexture2D<T>` are implemented
in the standard library as aliases of an internal `_Texture` type. The internal
type carries a `format` value parameter so backends can distinguish storage
formats such as `RGBA16F`, `RGBA8UI`, or `R32F`.

That `format` value is not a good user-facing interface. It is an integer, it is
the last generic parameter of an internal type, and users are not expected to know
which integer value maps to each image format. As a result, users have tended to
write texture types in terms of only the shader-visible data type, such as
`RWTexture2D<float4>` or `RWTexture2D<uint4>`, and then rely on backend-specific
format inference or attributes where needed.

This is awkward for APIs such as Vulkan, Metal, WebGPU, and CUDA-related
resource lowering, where storage texture format is part of the resource
information needed by the backend. It also makes reflection less precise: the
shader-visible data type `float4` does not say whether the underlying storage is
`RGBA32F`, `RGBA16F`, `RGBA8Unorm`, or another format that is read or written as
four floating-point components.

The format needs to propagate through normal type flow, including function call
boundaries, type aliases, generic code, and wrapper types such as
`DescriptorHandle<>`. Representing the format as part of the texture type gives
the compiler, reflection, and backends a single source of truth.

Proposed Approach
-----------------

The standard library should define one sealed type per supported texture storage
format. For example:

```slang
RWTexture2D<RGBA16F> hdrOutput;
RWTexture2D<RGBA8UI> idOutput;
Texture2D<RGBA8Unorm> colorInput;
```

A texture format descriptor type conforms to a standard-library interface that
describes the storage format and identifies the shader-visible data type:

```slang
interface ITexelData
{
    associatedtype Element : __BuiltinArithmeticType;
    static const int elementCount;
}

interface ITexelElement
{
    associatedtype DataType : ITexelData;
    static const int format;
}
```

`ITexelData` describes the type used by texture operations. `ITexelElement`
describes an element argument accepted by public texture aliases. The interfaces
are intentionally separate: a format descriptor is not itself a `float4` or
`uint4`, but it names a `DataType` that is used for texture loads and stores.

Existing texel data types such as `float`, `float2`, `float4`, `int4`, and
`uint4` conform to both `ITexelData` and `ITexelElement`, with `DataType` equal
to themselves and `format` equal to `0`. A format value of `0` means
"unspecified" and preserves the legacy behavior where a backend or compiler pass
may infer a default format.

Texture aliases should accept `T : ITexelElement` and lower to the internal
texture type using `T.DataType` as the shader-visible element type and `T.format`
as the storage format:

```slang
typealias RWTexture2D<T : ITexelElement = float4> =
    _Texture<T.DataType, __Shape2D, false, false, 0, readWrite, false, false, T.format>;
```

The exact `_Texture` parameters are an implementation detail, but the observable
semantics are:

* `RWTexture2D<RGBA16F>` reads and writes `float4` values and has storage format
  `RGBA16F`.
* `RWTexture2D<RGBA8UI>` reads and writes `uint4` values and has storage format
  `RGBA8UI`.
* `RWTexture2D<float4>` remains valid source code. Its storage format is
  unspecified at the type level unless the compiler infers a default format or a
  format attribute is used.
* Two texture types with different nonzero format operands are distinct types,
  even if their `DataType` is the same.

Detailed Explanation
--------------------

### Format descriptor names

Format descriptor types are ordinary Slang types, so their public names should
follow Slang type naming conventions rather than lower-case image-format token
spelling. The proposed names use a compact channel-width-format spelling:
`R32F`, `RG32F`, `RGBA16F`, `RGBA8Unorm`, `RGBA8UI`, and `R32I`.

The names are target-independent Slang type names, not direct copies of D3D,
Vulkan, Metal, or WebGPU enum spellings. They keep the familiar `R`/`RG`/`RGBA`
channel prefixes and format suffixes such as `F`, `I`, `UI`, `Unorm`, `Snorm`,
and `Srgb`, while avoiding backend-specific prefixes such as `DXGI_FORMAT_` or
Vulkan enum names.

### Format descriptor types

For each image format supported by Slang, the standard library should define a
format descriptor type. Each descriptor specifies:

* `DataType`: the shader-visible scalar or vector type.
* `format`: the internal image format enum value.

For example, conceptually:

```slang
struct RGBA16F : ITexelElement
{
    typealias DataType = float4;
    static const int format = /* RGBA16F image format enum value */;
}

struct RGBA8UI : ITexelElement
{
    typealias DataType = uint4;
    static const int format = /* RGBA8UI image format enum value */;
}
```

The descriptor type is not the value type returned by texture operations.
Texture operations use `DataType`. For example:

```slang
RWTexture2D<RGBA16F> tex;
float4 value = tex[int2(0, 0)];
```

When code needs scalar element information, it obtains it from `DataType` through
`ITexelData`. For example, `RGBA16F.DataType.Element` is `float` and
`RGBA16F.DataType.elementCount` is `4`.

### Legacy data-type arguments

Existing programs that write `Texture2D<float4>` or `RWTexture2D<uint>` should
continue to compile. These types conform to both `ITexelData` and
`ITexelElement`, with:

```slang
typealias Element = /* scalar element type */;
static const int elementCount = /* scalar count */;
typealias DataType = ThisType;
static const int format = 0;
```

This allows source compatibility while giving new code a more precise spelling
when the storage format matters.

For writable/storage textures, the compiler may infer conventional default
formats from legacy data-type arguments when targeting APIs that require a
format. For example, `RWTexture2D<float4>` may infer `RGBA32F`, and
`RWTexture2D<int4>` may infer `RGBA32I`. Such inference is a compatibility
feature. New code should prefer explicit format descriptor types whenever the
resource format is known.

### Type identity and conversion

The storage format is part of the texture type. Therefore:

```slang
void writeHDR(RWTexture2D<RGBA16F> tex);

RWTexture2D<float4> a;
RWTexture2D<RGBA16F> b;

writeHDR(b); // OK
writeHDR(a); // Error: format is not known to be RGBA16F
```

This proposal also does not define an implicit conversion from an explicitly
formatted texture type to the corresponding unspecified-format data-type texture.
For example:

```slang
void writeFloat4(RWTexture2D<float4> tex);

RWTexture2D<RGBA16F> b;
writeFloat4(b); // Error in this proposal.
```

Rejecting implicit format erasure keeps format information from being lost at
function boundaries, descriptor wrappers, and other places where this proposal is
intended to make the format available. Code that is intentionally polymorphic in
the format can be written generically over `T : ITexelElement`, with constraints
on `T.DataType` when the operation requires a particular shader-visible type.

### Reflection and backend behavior

Reflection should report the format carried by the texture type when it is
nonzero. Format attributes and backend-specific inference are fallbacks only
when the texture type itself has an unspecified format.

Backends should likewise treat the texture type's format operand as the source of
truth. If the format operand is nonzero, it determines the emitted SPIR-V image
format, Metal texture format/access constraints, WGSL storage texture format,
CUDA resource lowering information, and any related capabilities. If the operand
is zero, existing fallback behavior is preserved.

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
constraints, overloads, type aliases, descriptor wrapper types, and reflection
less direct. A format that is semantically part of the texture type should be
represented in the type.

### Make `RGBA32F` be an alias for `float4`

If `RGBA32F` were merely a type alias for `float4`, then
`RWTexture2D<RGBA32F>` would be indistinguishable from `RWTexture2D<float4>`.
That loses the ability to distinguish a known `RGBA32F` storage format from an
unspecified `float4` storage format.

This distinction matters even for formats whose memory representation appears to
match the shader-visible data type. Existing code uses `Texture2D<float4>` as a
format-agnostic type, and generic libraries often want to remain polymorphic in
the resource format. The proposal therefore keeps data types and format
descriptor types distinct.

### Require explicit formats everywhere

The language could reject `RWTexture2D<float4>` and require
`RWTexture2D<RGBA32F>` or another explicit format. That would be clearer for new
code, but it would break a large amount of existing HLSL-style code. This
proposal keeps legacy data-type arguments valid while encouraging explicit
format descriptor types for new code.
