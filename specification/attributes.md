Modifiers [mod]
=========

Issue: This chapter needs to list the built-in attributes that impact the language semantics, and also to specify the rules for how user-define attributes are defined and used.

```.syntax
Modifier
    => Attribute
    => KeywordModifier
    => SuffixModifier
```

Attributes [mod.attr]
==========

```.syntax
Attribute
    => `[` AttributeName AttributeArguments? `]`

AttributeName
    => Identifier (`.` Identifier)*

AttributeArguments
    => `(` Argument* `)`
```

```.syntax
KeywordModifier
    => TypeModifier
    => InterpolationModifier
    => /* ... */
```

Semantics [mod.semantic]
=========

```.syntax
SuffixModifier
    => `:` Semantic
    => `:` PackOffset
    => `:` Register
    => `:` BitFieldWidth
```

Interpolation Control
=====================

An **interpolation mode modifier** is one of:

| Modifier | Description |
|----------|-------------|
| `linear` (default) | linear interpolation |
| `nointerpolation` | constant interpolation |

Any *interpolation mode modifier* conflicts with any other *interpolation mode modifier*.

A **perspective correction modifier** is one of:

| Modifier | Description |
|----------|-------------|
| `noperspective` | perspective-correction disabled |
| none (default) | perspective-correction enabled |

The `nointeroplation` modifier conflicts with any *perspective correction modifier*.

An **interpolation location modifier** is one of:

| Modifier | Description |
|----------|-------------|
| `centroid` | interpolate at centroid of a fragment's samples |
| `sample` | interpolate at each of a fragment's samples |
| none (default) | interpolate at one of fragment's samples |

The `nointeroplation` modifier conflicts with any *interpolation location modifier*.

Geometry Shader Input Primitive Type
====================================

A **geometry shader input primitive type modifier** is one of:

| Modifier | Description |
|----------|-------------|
| `point` | ... |
| `line` | ... |
| `lineadj` | ... |
| `triangle` | ... |
| `triangleadj` | ... |

Matrix Layout Control
=====================

A **matrix layout modifier** is one of:

| Modifier | Description |
|----------|-------------|
| `row_major` | *row-major* layout |
| `column_major` | *column-major* layout |

Format Control
==============

```.syntax
TypeModifier
    => FormatModifier
    => MatrixLayoutModifier
    => `const`
```


```.syntax
FormatModifier
    => `unorm`
    => `snorm`
```

Fodder
======

```

// Tessellation
[domain]
[maxtessfactor]
[outputcontrolpoints] // HS output control point count
[outputtopology] // (HS) tessellator output topology
[partitioning] // (HS) partitioning scheme
[patchconstantfunc] // HS "patch-constant function"

// Geometry
[instance]
[maxvertexcount]


// Fragment
[earlydepthstencil]

// Compute
[numthreads]
groupshared

// Legacy
shared

// Mesh Shader
indices
vertices
primitives

// General
[shader]
[allow_uav_condition]
globallycoherent
[branch]
[call]
[fastopt]
[flatten]
[forcecase]
[loop]
[unroll]
[clipplanes] // not supported (?)
[RootSignature] // not supported (?)
precise
uniform
export

// TODO:
payload
rapayload
wavesensitive
wavesize
waveopsincludehelperlanes

[nodelaunch(LaunchType)]

```