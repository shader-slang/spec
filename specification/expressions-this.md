# This Expression

A **`this`** expression refers to the receiver of the invocation or the value being constructed. It is
available in the following contexts:

- body of a [non-static member function](types-struct.md#nonstatic-member-function)
- body of a [constructor](types-struct.md#constructor)
- body of a [subscript operator](types-struct.md#subscript-op) accessor (`get` or `set`)
- body of a [property](types-struct.md#property) accessor (`get` or `set`)
- body of a [function call operator](types-struct.md#function-call-op)

The type of **`this`** is [`This`](types-this.md).

In the body of a non-static member function, subscript operator accessor, property accessor, or function call
operator, **`this`** is the implicit _receiver parameter_. A constructor has no receiver parameter; see
[`this` in a constructor](#this-in-constructor) below.

The argument to the receiver parameter **`this`** is determined at the call site as follows:

- When a [call expression](expressions-operators.md#call-expression) invokes a member function, the argument
  to **`this`** is the object to which the member function belongs.
- When a [call expression](expressions-operators.md#call-expression) invokes a call operator, the argument to
  **`this`** is the value of the callable expression.
- When a [subscript expression](expressions-operators.md#subscript-expression) invokes a subscript operator
  accessor, the argument to **`this`** is the value of the base expression.
- When a [member expression](expressions-operators.md#member-expression) invokes a property accessor, the
  argument to **`this`** is the object of the member expression: either the value of *`value-expr`* or the
  object pointed to by *`pointer-value-expr`*.

<a id="this-in-constructor"></a>

In the body of a constructor, **`this`** refers to the value being constructed. See
[constructors](types-struct.md#constructor) for details.

The **`this`** expression is mutable in the following contexts:

- body of a
  [`[mutating]`](https://docs.shader-slang.org/en/latest/external/core-module-reference/attributes/mutating.html)
  non-static member function, subscript operator accessor, property accessor, or function call operator
- body of a constructor

A mutable **`this`** is also an [L-value](expressions-value-categories.md), and therefore, it can be passed as
an argument to an `inout` parameter.

Otherwise, **`this`** is an immutable [R-value](expressions-value-categories.md).

> 📝 **Remark 1:** By default, property setters and subscript setters are `[mutating]`, whereas non-static
> member functions, function call operators, property getters, and subscript getters are
> [`[nonmutating]`](https://docs.shader-slang.org/en/latest/external/core-module-reference/attributes/nonmutating.html).
> In a constructor, **`this`** is always mutable.

> 📝 **Remark 2:** In contexts where **`this`** is available, [name lookup](basics-name-lookup.md) includes
> the members of **`this`**.

> 📝 **Remark 3:** An L-value object is required to call mutating non-static member functions, mutating
> subscript operator accessors, mutating property accessors, or mutating function call operators.

> 📝 **Remark 4:** When a [variable declaration](declarations-variable.md) triggers a constructor call, the
> result of the constructor provides the variable with its initial value. An explicit
> [initializer expression](expressions-initializer.md) may also invoke a constructor, in which case the
> result of the constructor call is the value of the expression.

## Examples

```slang
struct TestStruct
{
    // A private data member is accessible only from other members
    // of TestStruct.
    private int value;

    // Constructor
    __init(int initial)
    {
        this.value = initial;

        // Note that members are usually referred directly
        // instead of via `this`.
    }

    int getValue()
    {
        // This is a non-mutating member function, so
        // it can only read members via `this`.
        //
        // An assignment such as `value = 1;` would be an error.
        return value; // same as this.value
    }

    [mutating] void addToValue(int amount)
    {
        // This is a mutating member function, so
        // it can read and write to members via `this`.
        //
        // Note that `value` below is the same as `this.value`.
        value = value + amount;
    }

    [mutating] void refTest()
    {
        ++value;
    }

    int getMultipliedValue(int multiplier)
    {
        // A member function can invoke another member function.
        return getValue() * multiplier;

        // The above is equivalent to:
        //
        // return this.getValue() * multiplier;
        //
        // Hence, `this` in `getValue()` is the same object as `this`
        // in `getMultipliedValue()`.
        //
        // Note that getMultipliedValue() cannot invoke addToValue(int),
        // which requires a mutable object.
    }
}

RWStructuredBuffer<int> output;

[numthreads(1,1,1)]
void main(uint3 tid : SV_DispatchThreadID)
{
    // Declare a variable of type `TestStruct`. The declaration
    // invokes the constructor TestStruct(int).
    //
    // In the constructor body, `this` refers to the value being
    // constructed. The result of the constructor call becomes the
    // value of `obj`.
    TestStruct obj = { 3 };

    // Invoke member function obj.addToValue(int). In the member function
    // body, `this` refers to `obj`.
    obj.addToValue(5);

    // Stores 8 to output[0]
    output[0] = obj.getValue();

    // Declare an immutable variable of type `TestStruct`.
    let immutableObj : TestStruct = TestStruct(42);

    // Mutating members of an immutable object cannot be invoked
    // immutableObj.addToValue(1);  -- ERROR

    // Invoking non-mutating members is fine
    //
    // Stores 42 to output[1]
    output[1] = immutableObj.getValue();

    // In this expression, the initializer expression TestStruct(123)
    // invokes the constructor, and getValue() reads the private
    // member of the result of the constructor call.
    //
    // `this` in the TestStruct(int) constructor refers to the value
    // being constructed. `this` in TestStruct.getValue() refers to
    // the result of the constructor call.
    //
    // The result of the constructor call is an R-value. Therefore,
    // only non-mutating members may be invoked.
    //
    // Stores 123 to output[2]
    output[2] = TestStruct(123).getValue();
}
```

Passing **`this`** as an argument to a generic function:

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
    // the receiver parameter, so it becomes
    // `this` in the context of `PointParticle.advanceTime()`.
    particles[tid.x].advanceTime(timeDelta);
}
```
