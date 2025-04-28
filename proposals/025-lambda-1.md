# SP #025: Lambda Expressions (Immutable Capture)

This proposal adds initial support for lambda expressions in Slang.
The initial proposal is to support immutable capture of variables in the surrounding scope.
This means that the lambda can only read the values of the captured variables, not modify them.

## Status

Status: In Implementation

Implementation: [PR 6914](https://github.com/shader-slang/slang/pull/6914)

Author: Yong He

Reviewer: Theresa Foley

## Background

SP009 introduced `IFunc` interface to represent callable objects. This allowed Slang code to
pass around functions as first-class values by defining types that implement `IFunc`.
However, this approach is not very convenient for users, as it requires defining a new type for each function
that needs to be passed around.

This problem can be solved with lambda expressions, which enables the compiler to synthesize such
boilerplate types automatically. The recent cooperative matrix 2 SPIRV extension introduced several opcodes
such as Reduce, PerElement, Decode etc. that can expressed naturally with lambda expressions.

## Proposal

The proposal is to add the following syntax for lambda expressions:
```slang
(parameter_list) => expression
```

or

```slang
(parameter_list) => { statement_list }
```

Where `parameter_list` is a comma-separated list of parameters, same as those in ordinary functions,
and `expression` or `statement_list` defines the body of the lambda. For examples, these two lambdas
achieve similar results:

```slang
(int x) => return x > 0 ? x : 0

(int x) => {
    if (x > 0) {
        return x;
    } else {
        return 0;
    }
}
```

A lambda expression will evaluate to an annoymous struct type that implements the `IFunc` interface
during type checking. The return type of the lambda function is determined by the body expression (in the case
of the lambda expression contains a simple expression body), or the value of the return statements in the
case of a statement body. If the lambda function body contains more than one return statements, then the return
values from all return statements must be exactly the same.

In the future, we will also extend lambda expressions to allow them to conform to other interfaces including
`IDifferentiableFunc` or `IMutatingFunc`.

Lambda expressions can be used in positions that accepts an `IFunc`:

```
void apply(IFunc<int, float> x) {...}

void test()
{
    apply((float x)=>(int)x+1); // OK, passing lambda to `IFunc<int, float>`.
}
```

## Translation

Immutable lambda expressions translates into a struct type implementing the corresponding `IFunc` interface.
For example, given the following code:

```slang
void test()
{
    int c = 0;
    let lam = (int x) => x + c;
    int d = lam(2);
}
```

The compiler will translate it into:

```slang
void test()
{
    int c = 0;
    struct _slang_Lambda_test_0 : IFunc<int, int> {
        int c;
        __init(int in_c) {
            c = in_c;
        }
        int operator()(int x) {
            return x + c;
        }
    }
    let lam = _slang_Lambda_test_0(c);
    int d = lam.operator()(2);
}
```

## Environment Capturing

If a lambda expression references a part of the environment variable either explicitly through a member or subscript operation
or implicitly through `this` dereference, the entire object will be captured in the context. For example, given:

```slang
struct Composite
{
    int member1;
    float member2;
}

void test()
{
    Composite c = {};
    let lam = (int x) => x + c.member2;
    lam(2);
}
```

The generated `struct` type for the lambda expression will contain a member whose type is `Composite`, as in the following code:

```slang
void test()
{
    Composite c = {};
    struct _slang_Lambda_test_0 : IFunc<int, int> {
        // Lambda captures the entire object instead of just
        // `member1`.
        Composite c;
        __init(Composite in_c) {
            c = in_c;
        }
        int operator()(int x) {
            return x + c.member1;
        }
    }
    let lam = _slang_Lambda_test_0(c);
    lam.operator()(2);
}
```

The same rules applies to implicit `this` parameter as well:

```slang
struct Composite
{
    int member1;
    float member2;
    void apply()
    {
        let lam = (int x)=>{
            return x + member1; // captures the entire `this`.
        }
    }
}
```

## Restrictions

Lambda expression in this proposed version can only read captured variables, but not modify them.
For example:

```slang
void test()
{
    int c = 0;
    let lam = (int x) {
        c = c + 1; // Error: c is read-only here.
        return x + c;
    };
    int d = lam(3);
}
```

Once a mutable variable is captured by a lambda expression, the variable should not be modified
during the lifetime of the lambda expression, or the behavior is undefined. 
We plan to allow mutating captured variables in a future proposal.

The lifetime of a lambda expression should not outlive the scope where a lambda expression is defined,
or the behavior is undefined.

Lambda expression is not allowed to have mutable parameters, such as `inout` or `out` parameters in this version.

A variable whose type is `[NonCopyable]` cannot be captured in a lambda expression.

The type system does not infer the expected parameter or return types of a lambda expression from
the context where the lambda expression is used. This restriction may be relaxed in the future
by reworking Slang's type checking to be more bi-directional. For example, the following code is not
allowed:

```slang
// Error: cannot infer types of x,y and return type from `lam`'s type.
IFunc<float, int> lam = (x, y) => return x + y;
```

Slang also does not support implicit casting of lambda/function types. So the following code is not
allowed:

```slang
// Error: cannot convert `IFunc<float, float>` to `IFunc<float, int>`.
IFunc<float, int> lam = (float x) => x;
```

# Conclusion

This proposal adds limited support for lambda expressions that cannot mutate its captured environment.
Although being limited in functionality, this kind of lambda expressions will still be very useful
in many scenarios including the cooperative-matrix operations.
This version of lambda expressions is easy to implement, and we do not need to consider nuanced semantics
around object lifetimes in this initial design.

In the future, we should extend the semantics to allow automatic differentiation and captured variable mutation
to make lambda expressions more useful.