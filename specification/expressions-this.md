# This Expression

The **`this`** expression refers to the _implicit instance parameter_ of the enclosing
[struct](types-struct.md), [class](types-class.md), or [enum](types-enum.md) type. It is valid in the
following contexts:

- body of a [non-static member function](types-struct.md#nonstatic-member-function)
- body of a [constructor](types-struct.md#constructor)
- body of a [subscript operator](types-struct.md#subscript-op) accessor (`get` or `set`)
- body of a [property](types-struct.md#property) accessor (`get` or `set`)
- body of a [function call operator](types-struct.md#function-call-op)

The type of **`this`** is [`This`](types-this.md).

The argument to the implicit instance parameter is:

- For a constructor, the object being constructed. For example, the variable initialized by a
  [variable declaration](declarations-variable.md), or the temporary object created by a constructor
  [call expression](expressions-operators.md#call-expression).
- For any other context, the object operand of the expression that invokes the member: a
  [call expression](expressions-operators.md#call-expression) of a non-static member function or function
  call operator, a subscript expression of a subscript operator accessor, or a member access expression of a
  property accessor.

When **`this`** is in the body of a non-static member function, constructor, subscript operator accessor,
property accessor, or function call operator declared in a [type extension](types-extension.md), it refers to
the implicit instance of the type being extended.

When **`this`** is in a
[`[mutating]`](https://docs.shader-slang.org/en/latest/external/core-module-reference/attributes/mutating.html)
context, it is an [L-value](expressions-value-categories.md). Otherwise, it is an
[R-value](expressions-value-categories.md). An L-value **`this`** provides read/write access to data members,
and it can be passed as an argument to an `out`/`inout`/`__ref` parameter.

> 📝 **Remark:** By default, constructors, property setters, and subscript setters are `[mutating]`, whereas
> non-static member functions, function call operators, property getters, and subscript getters are
> [`[nonmutating]`](https://docs.shader-slang.org/en/latest/external/core-module-reference/attributes/nonmutating.html).

## Examples

Pass **`this`** to a generic function:

```slang
interface ITrivialPhysicsObject
{
    // unit: m
    property position : float3 { get; set; }

    // unit: m/s
    property velocity : float3 { get; }

    [mutating] void advanceTime(float deltaSecs);
}

struct PointParticle : ITrivialPhysicsObject
{
    float3 position;
    float3 velocity;

    [mutating] void advanceTime(float deltaSecs)
    {
        // Pass the enclosing struct instance to updatePosition. Since
        // the non-static member function is declared as [mutating],
        // `this` is an L-value, so it can be passed as an argument to
        // an `inout` parameter.
        updatePosition(this, deltaSecs);
    }
}

void updatePosition<T>(inout T physObj, float deltaSecs)
    where T : ITrivialPhysicsObject
{
    physObj.position += physObj.velocity * deltaSecs;
}

RWStructuredBuffer<PointParticle> particles;
uniform float timeDelta;

[numthreads(1,1,1)]
void updatePointParticlePositions(uint3 tid : SV_DispatchThreadID)
{
    // Invoke non-static member function `PointParticle.advanceTime`.
    // Object `particles[tid.x]` is passed as the argument to
    // the implicit instance parameter, so it becomes
    // `this` in the context of `PointParticle.advanceTime()`.
    particles[tid.x].advanceTime(timeDelta);
}
```
