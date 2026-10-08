# Try expression

## Syntax

`try` expression:

> *`try-expr`* = **`'try'`** *`call-expr`*

### Parameters

- *`call-expr`* is an expression that may throw. The expression must be a
  [call expression](expressions-operators.md#call-expression) or application of a [unary operator](expressions-operators.md).

### Description

The `try` operator evaluates a [call expression](expressions-operators.md#call-expression) that may throw. When the call
returns without throwing, the `try` operator passes the return value through as is. When the call throws,
control is transferred to a matching [catch handler](statements-do-catch.md) according to the rules described
in the [throw statement](statements-throw.md).

A `try` covers only its immediate operand. If the operand contains a subexpression that may also throw, that
subexpression requires its own `try`.

It is an error if the [call expression](expressions-operators.md#call-expression) in the operand cannot throw.

See also [do-catch statement](statements-do-catch.md) and [throw statement](statements-throw.md).

> 📝 **Remark 1:** A `try` expression is currently limited to [function](declarations-functions.md) calls,
> [static](types-struct.md#static-member-function) and
> [non-static member function](types-struct.md#nonstatic-member-function)
> calls, and [operator](expressions-operators.md) invocations. GitHub issue
> [#13492](https://github.com/shader-slang/slang/issues/13492) tracks enabling error handling for all
> types of callable objects.

> 📝 **Remark 2:** A `try` expression on an operator is currently limited to unary
> [operators](expressions-operators.md). A potentially throwing binary operator may be invoked using the
> call form, see the examples below. GitHub issue
> [#13491](https://github.com/shader-slang/slang/issues/13491) tracks a possible solution that would allow
> `try` on all operator expression types.

## Examples

`try` and potentially throwing calls:

```slang
enum MyErrorType
{
    OverflowError,
}

int checkedIncrement(int i) throws MyErrorType
{
    if (i == int.maxValue)
        throw MyErrorType.OverflowError;

    return ++i;
}

struct OutputElement
{
    int onceIncremented;
    int twiceIncremented;
}

StructuredBuffer<int> input;
RWStructuredBuffer<OutputElement> output;

[numthreads(1,1,1)]
void main(uint3 tid : SV_DispatchThreadID)
{
    do
    {
        // checkedIncrement() may throw, so the call must
        // be in a try expression
        output[tid.x].onceIncremented = try checkedIncrement(input[tid.x]);

        // Every potentially throwing call must have a matching 'try'
        output[tid.x].twiceIncremented =
            try checkedIncrement(try checkedIncrement(input[tid.x]));
    }
    catch (MyErrorType err)
    {
        // TODO: overflow handling
    }
}
```

`try` and throwing operators:

```slang
enum MyErrorType
{
    OverflowError,
}

struct MyCheckedInt
{
    int value;
}

__prefix
MyCheckedInt operator++(inout MyCheckedInt i) throws MyErrorType
{
    if (i.value == int.maxValue)
        throw MyErrorType.OverflowError;

    ++i.value;
    return i;
}

__postfix
MyCheckedInt operator++(inout MyCheckedInt i) throws MyErrorType
{
    MyCheckedInt ret = i;
    try ++i;
    return ret;
}

MyCheckedInt operator + (MyCheckedInt a, MyCheckedInt b) throws MyErrorType
{
    // check for positive overflow
    if (a.value > 0 && b.value > (int.maxValue - a.value))
        throw MyErrorType.OverflowError;

    // check for negative overflow
    if (a.value < 0 && b.value < (int.minValue - a.value))
        throw MyErrorType.OverflowError;

    return { a.value + b.value };
}

StructuredBuffer<int> input;
RWStructuredBuffer<int> output;

[numthreads(1,1,1)]
void main(uint3 tid : SV_DispatchThreadID)
{
    do
    {
        MyCheckedInt checkedInt = { input[tid.x] };

        // throwing unary operators can be invoked with 'try'
        // using the operator form
        try checkedInt++;
        try ++checkedInt;

        // throwing binary operators can be invoked with 'try'
        // only using the call form
        checkedInt = try operator+(checkedInt, MyCheckedInt(100));

        output[tid.x] = checkedInt.value;

    }
    catch (MyErrorType err)
    {
        // TODO: overflow handling
    }
}
```
