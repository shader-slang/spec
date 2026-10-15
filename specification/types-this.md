# This Type

The **`This`** type refers to the enclosing [struct](types-struct.md), [class](types-class.md), or
[enum](types-enum.md) type, or the concrete type conforming to an [interface](types-interface.md).

**`This`** may be used within the body of such a type declaration, including in the signatures of its members,
and within the body of an [extension](types-extension.md) of a struct or enum type, where it refers to the
extended type. In a nested type declaration, **`This`** refers to the innermost enclosing type.

In the contexts where the [`this` expression](expressions-this.md) is available, the type of `this` is `This`.

> 📝 **Remark:** The **`This`** type is often used to specify that an interface method has the same parameter
> or return type as the concrete implementing type. See the example below.

## Examples

Using the `This` type within an interface:

```slang
interface INegatable
{
    // Negates `v`. The type of `v` is the conforming type, the same
    // as the return type.
    static This negate(This v);
}

interface IIncrementableByOne
{
    // Increments a value by 1.
    static This incrementByOne(This v);
}

struct MyFloat : INegatable, IIncrementableByOne
{
    float value;

    // `INegatable` requires that `MyFloat` implements
    // function `negate` with a parameter and
    // return value that have the implementing type. The
    // implementing type here is, of course, `MyFloat`.
    //
    // Both `MyFloat` and `This` name the same type here. We
    // spell out `MyFloat` to show the equivalence.
    static MyFloat negate(MyFloat v)
    {
        return MyFloat(-v.value);
    }

    // `This` refers to `MyFloat` here, so we can use it
    // in place of `MyFloat`.
    static This incrementByOne(This v)
    {
        return This(v.value + 1.0);
    }
}

void negateBuffer<T : INegatable, U : IRWArray<T>>(U arr)
{
    for (int i = 0; i < arr.getCount(); ++i)
        arr[i] = T.negate(arr[i]);
}

void incrementBufferByOne<T : IIncrementableByOne, U : IRWArray<T>>(U arr)
{
    for (int i = 0; i < arr.getCount(); ++i)
        arr[i] = T.incrementByOne(arr[i]);
}

RWStructuredBuffer<MyFloat> floats;

[numthreads(1,1,1)]
void computeMain(uint3 tid : SV_DispatchThreadID)
{
    negateBuffer(floats);
    incrementBufferByOne(floats);
}
```
