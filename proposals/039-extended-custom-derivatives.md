SP #039: `__func_extension` Shorthand for Function Extensions
====================

This PR proposes a special way of defining a function that is associated with another function. 
At the time of this proposal, the primary use-case for this is to define custom derivatives for the auto-diff system.

The current approach uses decorators (e.g. `[BackwardDerivativeOf(func)]`) to link related functions together, but this is limited in flexibility. Our auto-diff backend allow much more flexible derivatives to be defined, but there is no language mechanism to leverage this.

The new version proposes a way to define custom derivatives that: 
1. can provide separate forward and backward passes separately by returning continuations from the forward pass that can store captured intermediate values.
2. can, like types, be defined conditionally on type constraints.

For example:
```slang
float foo(float x) { return x * x * x; }

// Similar to the current style of defining a fwd_diff, but without a decorator.
__func_extension fwd_diff(foo)(DifferentialPair<float>) -> DifferentialPair<float>
{ 
    return diffPair(foo(x), 3.0 * x * x);
}

// "New style" backward derivative that can return a continuation.
__func_extension apply(foo)(float x) -> Tuple<float, IFunc<void, out float, float>>
{ 
    float sqr = x * x;
    return makeTuple(
        sqr * x, 
        (out float x_grad, float out_grad) => {
            x_grad = out_grad * 3.0 * sqr;
        });
}

//
// Note: the example assumes that lambdas can have out parameters (they currently can't, and
// IFunc's operator() doesn't support out parameters either). This is a vision for how 
// this system could work in the future with extensions to both lambdas and IFunc. 
// For now, the user will define a separate struct with operator() and return that.
//
```


Status
------

Status: Design Review

Implementation: Pending

Author: Sai Praveen Bangaru

Reviewer: 

Background
----------

### Need for More Flexible Custom Derivatives
Slang auto-diff's primary strength is the ability to define **fine-grained custom derivatives** that seamlessly work with its auto-diff system. Presently, the custom derivative system operates through a set of four attributes: `[BackwardDerivative(func)], [ForwardDerivative(func)], [BackwardDerivativeOf(func)], and [ForwardDerivativeOf(func)]`. 
These attributes link the original function to its derivative implementations. However, this approach has limitations in terms of flexibility and expressiveness.

#### 1. Inability to pass extra information from the forward pass to the backward pass
Presently, the backward derivative of a function must always be a single monolithic function that takes both the original function's inputs and the output gradient, and produces the input gradients. Example:
```slang
// Slang's custom derivative system:
[BackwardDerivativeOf(foo)]
float foo_backward(float x, float out_grad)
{
    return out_grad * 3.0 * x * x;
}

// auto-generated code:
float main_bwd()
{
    // forward pass
    foo(...)
    bar(...)
    // ... other forward operations ...

    // backward pass
    // ... other operations in reverse ...
    foo_backward(...) // Complex functions have to 
                      // recompute any necessary values.
    bar_backward(...)
}
```

Other auto-diff frameworks work differently, where the derivative consists of a forward pass that can optionally store information, which is then used by a separate "back-prop" function whose only input is the output gradient. Effectively, the forward pass is augmented (typically called an "apply" function in PyTorch) to produce a continuation that stores any extra information necessary for a more optimal backward pass.

Example of more flexible derivatives that a user might want to **manually write**:
```slang
float foo(float x) { return x * x * x; }
float my_foo_apply(float x, out float saved_sqr_val)
{
    saved_sqr_val = x * x;
    return saved_sqr_val * x;
}
float my_foo_backprop(float saved_sqr_val, float out_grad)
{
    return out_grad * 3.0 * saved_sqr_val;
}

float main_bwd_manual()
{
    // forward pass
    float x = 3.0;
    float saved_sqr_val;
    float out = my_foo_apply(x, saved_sqr_val);
    // ... other forward operations ...

    // backward pass
    // ... other operations in reverse ...
    float out_grad = ...;
    float x_grad = my_foo_backprop(saved_sqr_val, out_grad);
}
```

#### 2. Inability to define derivatives for specific specializations of a generic function
Slang is often used for both differentiable and non-differentiable contexts. We have 100s of methods that are defined generically over any arithmetic type, but may not be differentiable under all cases. 
Currently, this results in massive duplication, with most standard library methods getting two versions:
```slang
T sqr<T : IArithmetic>(T x) { return x * x; }

[ForwardDerivative(sqr_fwd)]
T sqr<T : IFloat>(T x) { return x * x; }
DifferentialPair<T> sqr_fwd<T : IFloat>(DifferentialPair<T> x) { return diffPair(x.p * x.p, 2.0 * x.p * x.d); }
```
Note that the second example must fully replicate the body of the original function, it's not sufficient to simply forward to the original function (e.g. `T sqr<T : IFloat>(T x) { return sqr_iarithmetic(x); }`) since that method is non-differentiable. 

If we had a way to define custom derivatives conditionally, just like we can define differentiability for types conditionally through the extension system, that would make it much simpler to express derivatives.

### Implementation Details of the Current Decorator-Based System

Under-the-hood, our compiler allows functions to implement interfaces, which is how differentiability of functions is currently expressed. The `IForwardDifferentiable<Func>`, `IBackwardDifferentiable<Func>` are used to describe how a function is differentiable. 
Our compiler presently converts decorators into extensions: 
```slang
[ForwardDerivativeOf(foo)]
DifferentialPair<float> foo_forward(DifferentialPair<float> x)
{
    return diffPair(foo(x.p), 2.0 * x.p * x.d);
}
```

becomes

```slang
extension foo : IForwardDifferentiable<foo>
{
    // fwd_diff is a requirement of the IForwardDifferentiable interface
    DifferentialPair<float> fwd_diff(DifferentialPair<float> x)
    {
        return diffPair(foo(x.p), 2.0 * x.p * x.d);
    }
}
```

In practice, particularly for backward derivatives, this can get quite ugly since `IBackwardDifferentiable` has a lot of requirements that are synthesized.

Proposed Approach
-----------------

The core of the proposal is providing a user-friendly syntax that de-sugars very early into `extension` declarations that can feed into the differentiable type system. While it's possible to directly use the `extension` syntax (even right now!), it is very verbose and unwieldy, requiring the user to use function interfaces. 

It also causes confusion since `extension` is typically used for types not functions. While this may seem like a nitpick, Slang allows things like overloading for functions, so we need something fundamentally different to distinguish between the two types of extensions.

Further, it is unwieldy to require users to specify the specific trait name (e.g. `IForwardDifferentiable`) that the extension implements, when it can be inferred more or less 100% of the time. Since we don't really allow users to define their own function interfaces, we can make sure requirement names are unique, and use that to figure out which function interface the user is talking about.

### `__func_extension` Keyword

To keep things contained in the codebase, we propose a new keyword and an associated `Decl` to represent this sort of extension until it can be checked and disambiguated into a classic extension.

`__func_extension` is a new keyword that allows defining functions that are associated with another function. 

The proposed syntax is as follows:
```
__func_extension<?generic_definition> <builtin_operator>(<?base_type>::<func_name><?generic_specializations>)(<parameters>) -> <?return_type> 
{
    <function_body>
}
```
where "?" denotes optional components.

Note that this uses the 'new-style' of function definition (i.e. similar to `func <func_name>(<params>) -> <ret_type> { ... }`) instead of C-style definitions.
Slang already supports this style so we can re-use most existing infrastructure.

This allows us to define relatively complex derivatives. E.g. of a definition that only applies to a specific specialization:
```slang
T foo<T : IArithmetic>(T x) { return x * x; }

__func_extension<T : IFloat> fwd_diff(foo<T>)(DifferentialPair<T>) -> DifferentialPair<T>
{ 
    return diffPair(foo(x), 2.0 * x * x.d);
}

void main()
{
    int i = 3;
    fwd_diff(foo<int>)(x); // error: no 'fwd_diff' on foo<int>

    float f = 3.0;
    fwd_diff(foo<float>)(diffPair(f, 1.0)); // ok, uses the extension defined above
}
```

Under the hood, during `SemanticsDeclBasesVisitor`, we want `__func_extension` to check its target and convert itself into a regular `ExtensionDecl` that slots into the existing function interfaces system. The resulting extension then proceeds through regular extension checking.

E.g. the above example would desugar into (simplified; see detailed AST below for full generic form):
```slang
// Auto-synthesized by "de-sugaring" __func_extension into an extension
extension<T : IFloat> foo<T> : IForwardDifferentiable<foo<T>>
{
    DifferentialPair<T> fwd_diff(DifferentialPair<T> x)
    { 
        return diffPair(foo(x), 2.0 * x * x.d);
    }
}
```
#### Extensions for Member Methods
Fairly often, we want to define derivatives for member methods (e.g. accessors on `Tensor<T>` or operations on `CoopVec<T>` or `Vector<T>`). This should "just work" by allowing the user to reference the member method statically. `fwd_diff()`/`bwd_diff()` already allow this when parsing & resolving the target.
```slang
__func_extension<T : __BuiltinFloatingPointType> fwd_diff(CoopVec<T>.exp)(
    DifferentialPair<CoopVec<T>> dpthis) // Effective "this" type becomes first explicit parameter 
    -> DifferentialPair<CoopVec<T>>
{
    return diffPair(dpthis.p.exp(), dpthis.d * dpthis.p.exp());
}
```

### Implementation Details (for existing `fwd_diff`/`bwd_diff` style)

We want the following flow:


E.g. source code for a forward differentiable definition:
```slang
T foo<T : IArithmetic>(T x) { return x * x * x; }
__func_extension<T : IFloat> fwd_diff(foo<T>)(DifferentialPair<T>) -> DifferentialPair<T>
{ 
    return diffPair(foo(x), 3.0 * x * x);
}
```

After parsing
```slang
GenericDecl
{
    members = 
    {
        GenericTypeParamDecl
        {
            name = "T"
        },
        GenericTypeConstraintDecl
        {
            subType = VarExpr("T")
            constraint = VarExpr("IArithmetic")
        },
    }

    inner = FuncExtensionDecl ; new type of decl
    {
        target = ForwardDifferentiateExpr(base=GenericAppExpr(base=VarExpr("foo"), args=[VarExpr("T")])),
        inner = FuncDecl
        {
            name = "fwd_diff",
            parameters = [ParamDecl{name="x", type=GenericAppExpr(base=VarExpr("DifferentialPair"), args=[VarExpr("T")])}],
            returnType = GenericAppExpr(base=VarExpr("DifferentialPair"), args=[VarExpr("T")]),
            body = ...
        }
    }
}

```

When checking, we first need to check the target of the func-extension-decl with the parameter types as context. This follows the existing logic for resolving a call to `fwd_diff(foo<T>)` which infers any generic arguments and narrows down the overload set to a specific function.

After that, `target` is a higher-order-expr with a concrete function reference.

At this point, we can convert it into an extension decl within the same generic signature
```llvm
GenericDecl
{
    members =
    {
        %T = GenericTypeParamDecl
        {
            name = "T"
        },
        %T_is_IArithmetic = GenericTypeConstraintDecl
        {
            subType = DeclRef(%T)
            constraint = DeclRef(%IArithmetic)
        },
    }
    inner = ExtensionDecl
    {
        ; foo<T>
        target = DeclRefType(
            GenericAppDeclRef(
                base=DeclRef(%foo), 
                args=[DeclRef(%T), Lookup(%IFloat, %T_is_IArithmetic)]))
        members = 
        {
            ; Auto-inserted based on special-case analysis of "ForwardDifferentiateExpr"
            InheritanceDecl
            {
                ; IForwardDifferentiable<foo<T>>
                type = GenericAppDeclRef(
                    base=DeclRef(%IForwardDifferentiable), 
                    args=[
                        ; foo<T>
                        GenericAppDeclRef(
                            base=DeclRef(%foo), 
                            args=[DeclRef(%T), Lookup(%IFloat, %T_is_IArithmetic)]), 
                        DiffTypeInfoWitness(...)])
            },
            FuncDecl
            {
                name = "fwd_diff",

                ; Parameters, return type and body are copied over as-is.
                parameters = [ParamDecl{name="x", type=GenericAppDeclRef(base=DeclRef(%DifferentialPair), args=[DeclRef(%T)])}],
                returnType = GenericAppDeclRef(base=DeclRef(%DifferentialPair), args=[DeclRef(%T)]),
                body = ...
            }
        }
    }
}
```

### Implementation Details (for `apply` methods)

The `apply` higher-order expression allows users to define a custom forward pass that returns a minimal context, which the backward pass can use instead of recomputing intermediate values. This maps onto the existing `IBackwardDifferentiable` interface.

#### Example

```slang
float foo(float x) { return x * x * x; }

__func_extension apply(foo)(float x) -> Tuple<float, FooContext>
{
    let sqr = x * x;
    return makeTuple(sqr * x, FooContext(sqr));
}

struct FooContext
{
    float sqr;
    void operator()(inout DifferentialPair<float> dpx, float out_grad)
    {
        dpx = diffPair(dpx.p, out_grad * 3.0 * sqr);
    }
}
```

#### Desugaring

A new higher-order expression `ApplyExpr` is needed to represent `apply(fn)` in the AST (analogous to `ForwardDifferentiateExpr` for `fwd_diff(fn)`). Checking proceeds the same way: the target is resolved to a concrete function reference, and the `__func_extension` is converted into an `ExtensionDecl` implementing `IBackwardDifferentiable`.

The key difference from `fwd_diff` is that `IBackwardDifferentiable` has multiple requirements that must be satisfied:

| Requirement | How It's Filled |
|---|---|
| `MinimalContext` | Inferred from the return type of `apply`. If the return is `Tuple<RetType, MinCtxType>`, then `MinimalContext = MinCtxType`. |
| `BwdCallable` | Set to the same type as `MinimalContext`. |
| `apply_bwd` | The user-provided function body. |
| `remat` | Synthesized as an identity function (`MinimalContext -> BwdCallable` is trivial since they are the same type). |
| `BwdCallable : IBwdCallable<foo>` | A conformance extension is synthesized for the `MinimalContext` type, mapping its `operator()` to the `IBwdCallable<foo>` requirement. |
| `bwd_diff` (legacy) | Synthesized from `apply_bwd` + `remat` + `BwdCallable.operator()` as usual. |

The desugared form of the above example:
```slang
extension foo : IBackwardDifferentiable<foo>
{
    typealias MinimalContext = FooContext;
    typealias BwdCallable = FooContext;  // Same as MinimalContext

    // User-provided apply body
    Tuple<float, FooContext> apply_bwd(float x)
    {
        let sqr = x * x;
        return makeTuple(sqr * x, FooContext(sqr));
    }

    // Trivial identity — MinimalContext and BwdCallable are the same type
    FooContext remat(FooContext ctx) { return ctx; }

    // bwd_diff is auto-synthesized from apply_bwd + remat + BwdCallable.operator() as usual.
}

// Auto-synthesized conformance for the context type
extension FooContext : IBwdCallable<foo>
{ /* operator() will get pulled from the struct definition */ }
```