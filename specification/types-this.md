# This Type

The **`This`** type refers to the enclosing [struct](types-struct.md), [class](types-class.md),
[enum](types-enum.md), or [interface](types-interface.md) type.

**`This`** may be used within the body of such a type declaration, including in the signatures of its members,
and within the body of an [extension](types-extension.md) of a struct or enum type, where it refers to the
extended type. In a nested type declaration, **`This`** refers to the innermost enclosing type.

When the enclosing type is:

- a struct, class, or enum: **`This`** is that enclosing type.
- an interface: **`This`** is the concrete type conforming to that interface.

In the contexts where the [`this` expression](expressions-this.md) is available, the type of `this` is `This`.

## Examples

Interface with `This` type:

```slang
interface INegatable
{
    // Returns an object of the conforming type.
    This negate();
}

struct MyFloat : INegatable
{
    float value;

    This negate()
    {
        return This(-value);
    }

    // The above is the same as:
    //
    // MyFloat negate()
    // {
    //     return MyFloat(-value);
    // }
}

void negateBuffer<T : INegatable, U : IRWArray<T>>(U arr)
{
    for (int i = 0; i < arr.getCount(); ++i)
        arr[i] = arr[i].negate();
}

RWStructuredBuffer<MyFloat> floats;

[numthreads(1,1,1)]
void computeMain(uint3 tid : SV_DispatchThreadID)
{
    negateBuffer(floats);
}
```
