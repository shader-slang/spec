# SP#029: `Conditional<T, bool hasValue>` Type

## Status

Status: Design Review

Implementation: [PR 7327](https://github.com/shader-slang/slang/pull/7327)

Author: Yong He

Reviewer: Theresa Foley, Kai Zhang

## Background

In some situations, it is necessary to ensure fields in a struct type can be removed during specialization if it is not used. For example, exclusion of unused fields in vertex output/fragment input is necessary on platforms where performance is sensitive to the number of declared vertex-fragment interpolants.

While Slang has supported generics for a long time, developers are still unable to use generics to conditionally include a struct field. As a result, developers often resort to preprocessor defines to achieve this goal, which does not work well with the rest of the codebase that uses generics, and misses the opportunity to benefit from the compile time improvements from modules and link-time specialization. In this proposal, we add a `Conditional<T, bool hasValue>` type, such that if `hasValue` is `false`, a field of such type will be eliminated by the compiler during specialization.

## Proposed Solution

We propose to add the following declaration to the core module:

```slang

struct Conditional<T, bool hasValue>
{
    internal T storage[hasValue];

    __implicit_conversion($(kConversionCost_ValToOptional))
    [__unsafeForceInlineEarly]
    __init(T val) { if (hasValue) storage[0] = val;}

    [__unsafeForceInlineEarly]
    public Optional<T> get()
    {
        if (hasValue)
        {
            return Optional<T>(storage[0]);
        }
        else
        {
            return none;
        }
    }

    [__unsafeForceInlineEarly]
    [mutating]
    public void set(T value)
    {
        if (hasValue)
            storage[0] = value;
    }
}

extension<T> Optional<T>
{
    __implicit_conversion($(kConversionCost_ImplicitDereference))
    __generic<bool condHasValue>
    [__unsafeForceInlineEarly]
    __init(Conditional<T, condHasValue> condVal)
    {
        if (condHasValue)
            this = Optional<T>(condVal.storage[0]);
        else
            this = none;
    }
}
```

## Highlights

1. `Conditional<T>` is implemented with an array whose size might be 0.
1. `Conditional<T>` can be implicitly converted to/from `Optional<T>`, allowing it to be used in `if (let ...)` statement.
1. Setting value to `Conditional<T, false>` has no effect.
1. `Conditional<T, hasValue>` always have the same alignment and size as `T[hasValue?1:0]`.

With `Conditional`, a vertex type can be defined as:

```slang
interface IVertex
{
    property float3 position{get;}
    property Optional<float3> normal{get;}
    property Optional<float3> color{get;}
}

struct Vertex<bool hasNormal, bool hasColor> : IVertex
{
    private float3 m_position;
    private Conditional<float3, hasNormal> m_normal;
    private Conditional<float3, hasColor> m_color;

    property float3 position
    {
        get { return m_position; }
    }
    property Optional<float3> normal
    {
        get { return m_normal; }
    }
    property Optional<float3> color
    {
        get { return m_color; }
    }
}
```

In this example, `Vertex` type is parameterized on `hasNormal` and `hasColor`. If `hasNormal` is false, the `m_normal` field will be eliminated in the target code, allowing a specialized vertex shader to declare minimum output fields. For example, a vertex shader
can be defined as follows:

```slang
[shader("vertex")]
Vertex<hasNormal, hasColor> vertMain<bool hasNormal, bool hasColor>(VertexIn inputVertex)
{
    ...
}
```

## Alternative Approaches

It is also possible to use different types for each optional field. For example, we can define a set of helper types as:

```slang
interface IConditional<T>
{
    static const bool hasValue;
    property Optional<T> value {get;}
}
struct Real<T> : IConditional<T>
{
    static const bool hasValue = true;
    T valueStorage;
    property Optional<T> value { get { return valueStorage; } }
}
struct No<T> : IConditional<T>
{
    static const bool hasValue = false;
    property T value { get { return none; } }
}
```

With these helpers, the above `Vertex` type can also be defined with each field being different types:

```
struct Vertex<Normal : IConditional<float3>, Color : IConditional<float3>>
{
    private float3 m_position;
    private Normal m_normal;
    private Color m_color;

    property float3 position
    {
        get { return m_position; }
    }
    property Optional<float3> normal
    {
        get { if (m_normal.hasValue) return m_normal.value; else return none; }
    }
    property Optional<float3> color
    {
        get { if (m_color.hasValue) return m_color.value; else return none; }
    }
}
```

With this, the entrypoint can be defined as:

```slang
[shader("vertex")]
Vertex<Normal, Color> vertMain<Normal : IConditional<float3>, Color : IConditional<float3>>(VertexIn inputVertex)
{
    ...
}
```

And `vertMain` can then be specialized with `vertMain<Real<float3>, No<float3>>`. This can achieve the same goals, but it is
less direct and require more complex type signature in specialization arguments.

The Metal shading language allows structs and entrypoint parameters to be conditional via its `[[function_constant(name)]]` syntax. For example,
```c++
constant bool normal_defined [[function_constant(0)]]; 
constant bool color_defined [[function_constant(1)]]; 

struct Vertex
{ 
    float4 position [[attribute(0)]]; 
    float3 normal   [[attribute(1), 
                      function_constant(normal_defined)]]; 
    float3 color    [[attribute(2), 
                      function_constant(color_defined)]]; 
}; 
```

In the code above, `Vertex::normal` is only declared if `normal_defined` is set to `true` during compilation. While this attribute
based solution achieves the same goal, it leaves out the possibility of writing code that uses the `normal` field while `normal_defined` is
set to `false`. Since the existence of the value is not encoded in the types, the compiler frontend cannot provide any help to make
sure the code is not accessing fields that won't exist. Slang's approach of encoding the `hasValue` info as a type parameter and combining
the support with `Optional<T>` allows the language to ensure all uses of conditional fields are guarded with a static check on the existence
of the field.

As of writing, conditional fields that affect the data layout of the type are not known to be supported in any major CPU
programming languages.
