# Proposal 024: New Higher-Order Operator System (For Auto-Diff & Other Potential Features)

This proposal introduces a way to express higher order operations as interface requirements, by allowing interface and extensions to apply to functions. 
This proposal also contains examples of how this can be used to make the current auto-diff system more flexible by expressing intermediate context types, and allowing user-defined derivatives to be expressed as extensions that apply to specific specializations of a function.
    
## Status

Status: Design Review

Implementation: In Progress

Author: Sai Bangaru

Reviewer: TBD

## High-Level Goals

### 1. Make higher-order operations easily expressible in Slang. 

Slang now supports many higher-order operators, primarily for auto-diff (e.g. `fwd_diff` and `bwd_diff` ), which conceptually operate on functions (i.e. take “callables” as input and return “callables” as output)

Example: 
`fwd_diff(fn)` is a callable function that represents the forward-mode derivative of fn .

Often such operations may be synthesized by the compiler, or user-defined, and sometimes even a composition of other higher-order operations. 

Example (of how user-defined higher order operations currently work):
```csharp
float sqr(float a) { return a * a; }

// User-defined implementation for `fwd_diff(sqr)`
[ForwardDerivativeOf(sqr)]
DifferentialPair<float> sqr_fwd(DifferentialPair<float> a)
{
   return DifferentialPair<float>(a.p, 2 * a.p * a.d);
}
// The same implementation can be synthesized by the compiler, if a user-defined derivative is not available.

void main()
{
   fwd_diff(sqr)(...);
}

```


### 2. Support other higher order operations 

In the near future, we may want other higher-order operators such as `map<indices...>(fn)` for mapping a function over an array-like input, `DiffContext(fn)` for referring to a function’s intermediate derivative context, `bwd_prop`/`bwd_primal` for invoking the intermediate forward and backward steps within a `bwd_diff` call, and more.

## Problem

Our treatment of higher-order operators is currently quite messy. 

First, we lower higher-order operations directly to IR op-codes. 
Example: `fwd_diff(fn)` is always lowered to `IRForwardDifferentiate(funcInst)` , and then the backend is responsible for determining whether synthesis is required or there is a user-provided definition. 

Second, user-provided definitions are lowered as decorators on the referenced function. That is, a function foo with `[ForwardDerivativeOf(bar)]` will be lowered as a reference decoration `IRForwardDerivativeDecoration(foo_inst)` on the target bar. This implicitly assumes that a definition must apply to the whole function (and can’t apply to a subset of specializations). We need a more extension-like mechanism to properly express functions that only apply to a subset of possible specializations. This is necessary to support user defined derivatives for things like `CoopVec<T : __BuiltinFloatingPointType>::add()` while not affecting the more general `CoopVec<T : __BuiltinArithmeticType>::add()` .

Third, this system makes it quite difficult to add more higher-order operators to the language. Each new operation requires adding an additional front-end AST node, a new decorator for user-provided definitions, checking logic for the decorator and AST node, IR opcodes for both AST nodes, IR-side logic to find the user-provided definitions, etc..

Fourth, our mechanism for handling interface methods is quite ad-hoc. For each `[Differentiable]` interface method, we manually insert an additional set of interface requirements & add backend logic to make sure that the functions are synthesized as necessary. This part also gets increasingly more complex as more operations are added to the system

## Solution

### Functions can be used as types

Within the AST, it is okay to use a `DeclRef` to a `FuncDecl` as the base for a `DeclRefType` node. 

We need to modify various places in the system where there is a built-in assumption that the decl-ref should refer to a type-declaration (i.e. `StructDecl` , etc...)

For the most part, this should just work with the lookup system, conformance system etc.., since it is a subclass of Type 

### Function Interfaces (`__function_interface` )

We introduce a new (experimental) type of interface called `__function_interface` which behaves very similarly to interfaces and works with all the interface lookup logic within Slang. The primary difference is that function interfaces can only apply to functions (enforced during the `checkInterfaceConformance()` routine)

Internally, the `FunctionInterfaceDecl` is a sub-class of `InterfaceDecl` , so it can be used with existing interface/facets machinery.
We allow 

1. a new way to declare an interface requirement: `associatedfunction FuncTypeExpression reqName` which is just a regular function requirement but declared using a function-type-expression instead of the usual way `ResultType name(ParamTypes)` 
2. and associated types that map to built-in AST types (like `ForwardDerivativeFuncType` ) to be able to compute the required function type translations from within the compiler.

We can rewrite our entire auto-diff front-end in terms of function interfaces:
```csharp
// Available on all methods. Uses custom op-decls that are used by the semantics stage
// to do the type translations (since we don't really have a way to express this in
// Slang)
[auto]
__function_interface IFunctionTypeTranslations
{
   [magic_type(FunctionResultType)] // "Type" sub-class that resolves the type based on the "this-type" which here is the function on which __result_type is being invoked.
   associatedtype __result_type;

   // The remaining types compute a "FuncType"
   [magic_type(ForwardDerivativeFuncType)] 
   associatedtype __fwd_diff_func_type;

   [magic_type(BackwardDerivativeFuncType)]
   associatedtype __bwd_diff_func_type;

   [magic_type(EvalWithContextFuncType)]
   associatedtype __eval_with_context_func_type;

   [magic_type(BackwardPropFuncType)]
   associatedtype __bwd_prop_func_type;
}

__function_interface IForwardDifferentiable
{
    [SynthesisOp(kIROp_ForwardDifferentiate)] // Used for backend synthesis, if user definition is not provided.
    associatedfunction __fwd_diff_func_type(This) fwd_diff;
}

__function_interface IBackwardDifferentiable
{
    [SynthesisOp(kIROp_BackwardDifferentiate)]
    associatedfunction __bwd_diff_func_type(This) bwd_diff;
}

__function_interface IDifferentiableWithContext
{
    [SynthesisOp(kIROp_IntermediateContextType)]
    associatedtype DiffContext : IDiffContext<This>;

    [SynthesisOp(kIROp_EvalWithContext)]
    associatedfunction __eval_with_context_func_type(This) with_ctx;
}

// This one's a regular interface, so we need to plug the function into it as a
// specialization parameter. 
// `ftype` represents a function declaration that can be plugged in. `f` can also be
// a interface declaration.
// 
interface IDiffContext<f : func> : IDifferentiable
{
    [Differentiable] __result_type<f> result();
    [Differentiable] __bwd_prop_func_type(f) __call;
}
```

### Higher-order operators as syntax sugar for lookups

Higher-order operator application expressions like `op(func)` are now just syntax sugar for a lookup on the function like `func.op` . Internally, this represents a `LookupDeclRef` that works in the same way as if we were looking something up on a type, so most of our existing lookup infrastructure can be left unchanged. 

One additional case to handle is that func may refer to an overloaded group, so `func.op` will need to push the lookup into overload group to create a group of `LookupDeclRef` objects. (Type names can’t be overloaded so this case won’t already be handled)

Note: This does limit our higher-order expressions to operating on a single function, since we can’t really express `op(func1, func2)` as a “property” of one of the functions. This is probably fine for now, and we can always support things like de-sugaring to `func1.op(func2)` later if necessary.

### User-defined operator overloads as syntax sugar for extensions

In keeping with the “interface requirement” treatment for higher-order operators, we can define a new way to provide user-defined definitions, that work similar to operator overloads. 

Example:
```csharp
T foo<T : IArithmetic>(T x) { return x * x; }

// Operator definition. 
// Automatically inserts the InheritanceDecl so that `foo<T> : IForwardDifferentiable 
// where T : IArithmetic & IDifferentiable`
//
__generic<T : IArithmetic & IDifferentiable>
DifferentialPair<T> foo<T>.fwd_diff(DifferentialPair<T> dpx)
{ /* ... */ }

void main()
{
   fwd_diff(foo)(...) // -> Statically resolves to the user provided foo<T>.fwd_diff definition
}

Internally, this is just syntax sugar for an extension. (Mostly to avoid unnecessary verbosity)

extension<T> foo<T> : IForwardDifferentiable where T : IArithmetic & IDifferentiable
{  
   DifferentialPair<T> fwd_diff(DifferentialPair<T> dpx) { /* ... */ } 
}


Another example, this time for a more complex feature that we’d like to support: backward derivatives with context, where the eval_with_context returns a “diff context” object which can then be called at a later time to evaluate the backward derivative.

void foo<T : IArithmetic>(T x)
{
    return x * x;
}

/* 
 * Example version that defines a context type and then defines the primal_ctx function 
 */

// Define context type (which is a functor)
// Here's it's a name-less struct definition that is automatically assumed to conform to 
// "IDiffContext<foo<T>>" (expects a result() function and a __call() function)
//
__generic<T : IArithmetic & IDifferentiable>
typealias foo<T>.DiffContext
{
    T x;
    T _res;
    T result() { return _res; }
    void __call(out T.Differential dX, T.Differential dOut) 
    {
        dX = 2 * x * dOut;
    }
}

// Define the eval_with_context function  
__generic<T : IArithmetic & IDifferentiable>
foo<T>.DiffContext foo<T>.eval_with_context(T x)
{
    return foo<T>.DiffContext(
        x,
        foo<T>(x));
}

/* 
 * Alternative example for when we have lambdas (that support capture-by-value closure)
 */

// foo<T>.DiffContext can be inferred from return type.
__generic<T : IArithmetic & IDifferentiable>
foo<T>.DiffContext foo<T>.eval_with_context(T x)
{
    // Helper function to pack the result value and back-prop lambda into a single
    // struct type.
    //
    return ContextResultPair( 
        foo<T>(x),
        [=] (out T.Differential dX, T.Differential dOut)
        {
            dX = 2 * x * dOut;
        });
}
```


### Parsing of user-provided function operator implementations

We’ll try to parse this structure:

```csharp
MaybeGeneric
TypeString FunctionRefString.operator OperatorRefString(ParamList)
{ /* ... */ }
```

as a function operator overload declaration `FunctionOperatorOverloadDecl`:
```csharp
FunctionOperatorOverloadDecl
{
   resultType = VarExpr("TypeString")
   baseFunc = VarExpr("FunctionRefString") | GenericAppExpr(...)
   operatorName = VarExpr("OperatorRefString")
   members = (/* try parse ParamDecls as usual.. */)
}
```

`FunctionOperatorOverloadDecl` is a temporary declaration that, after checking, will be replaced with an `ExtensionDecl` 

### Checking of user-provided function operator implementations

This step is to verify that a definition of the form:

```csharp
__generic<T : IArithmetic & IDifferentiable>
DifferentialPair<T> foo<T>.fwd_diff(DifferentialPair<T> dpx)
{ /* ... */ }
```

can apply to `foo<T>` .

Since function-operator-decls will reference functions, we’ll want to check them in a stage after functions are ready for lookup.

The first phase will simply perform lookups on all the VarExpr s to turn them into `DeclRef`s or `OverloadGroup` objects.
```csharp
OuterGenericDecl // If any.
{
FunctionOperatorOverloadDecl
{
   resultType = DeclRefType(DeclRef(Decl(name="TypeString")))
   baseFunc = OverloadGroup([DeclRef(..), DeclRef(..)])
   operatorName = DeclRef(FuncDecl("fwd_diff")) // Need a decl not a decl-ref here.
   members = (/* check ParamDecls as usual */)
}
}
```

After checking, ideally, we want to immediately turn the `FunctionOperatorOverloadDecl` into an `ExtensionDecl`. However, we may not have a fully resolved `baseFunc` so we’ll need to test each possible candidate to find the right one.

This checking proceeds in this manner:

1. For each candidate in the overload-group:
    1. Calculate the expected function type by getting the type-expression for the operator decl (in this case the associated type `__fwd_diff_func_type(This)` , and substituting the candidate `baseFuncDeclRef` for `This`. This should cause the lookup to resolve to a `FuncType`. 
    2. Check that the FunctionOperatorOverloadDecl is compatible with the `FuncType`.
        1. This is typically achieved by constructing a set of VarExpr nodes with the given parameter types, and checking `InvokeExpr(DeclRef(FunctionOperatorOverloadDecl), fakeArgs)` 
    3. If yes, add to list of successful candidates.
2. If we have more than one successful candidate: Ambiguous (error)
3. If we have 0 successful candidates: Error
4. Otherwise, convert the `FunctionOperatorOverloadDecl` into a standard `ExtensionDecl` with a `FuncDecl` inside of it:


```csharp
OuterGenericDecl
{ // If any, this will just be the _same_ outer generic 
  // (avoid re-creating the decl so we don't have to re-write the generic args for the decl-refs inside the extension)

ExtensionDecl
{
    targetType = DeclRefType(candidateFuncDeclRef); // the 'type' here is a specialized function ref.
    members = [
              InheritanceDecl
              {
                     base = DeclRefType(DeclRef(InterfaceDecl("IForwardDifferentiable"))) // super-type is the parent interface type of the operator decl (e.g. Decl("fwd_diff"))
              }
              FuncDecl
              {
                     name = "fwd_diff" // operatorName 
                     resultType = /* checked result type */
                     members = [/* checked param decls */]
              }]
}

} // end outer generic
```

5. Check the `ExtensionDecl` up to `ReadyForConformances` state. (This should also automatically register the decl as an extension).

### Enhancements to visitExtensionDecl() 

In the new version, extensions need to account for the fact that `targetType` can be a `DeclRef` to a `FuncDecl` (instead of the usual types). 
However, they simply need to check that the `targetType` can be resolved to a proper `DeclRef` . Nothing extra is needed here.

`[Differentiable]` is syntax sugar for conformance to `IForwardDifferentiable & IBackwardDifferentiable & IDifferentiableWithContext` 

When checking the `[Differentiable]` attribute, we insert conformance-decls for `IForwardDifferentiable`, `IBackwardDifferentiable` and `IDifferentiableWithContext` , if one doesn’t already exist from a user-provided definition)

However, since we won’t be able to satisfy the requirement with a `FuncDecl` , the look-up will use the synthesized function decl represented by `SynthesizedFuncDecl` instead. The diff context type will use a similar `SynthesizedStructDecl` . These are subclasses of `FuncDecl` and `StructDecl` respectively, so they will work naturally with other checking & look-up infrastructure, while being lowered to specific IR op codes.

### Checking functions with `[Differentiable]` tag

Under the new system, a function with `[Differentiable]` tag is just a function that conforms to `IForwardDifferentiable`, `IBackwardDifferentiable` and `IDifferentiableWithContext`.

There are two steps to checking such a function:

1. In the `ModifiersChecked` state: Create extensions for these interfaces & use the new `SynthesizedFuncDecl` decl-type that denotes a function that should be synthesized in the backend.

  When checking a `FuncDecl` with a `DifferentiableAttribute` (i.e. from `[Differentiable]` ), we synthesize the conformances:

```csharp
OuterGenericDecl
{ // If any, put the `ExtensionDecl` inside the FuncDecl's parent container.
ExtensionDecl
{
    targetType = DeclRefType(funcDefaultDeclRef); // default decl-ref.
    members = [
              InheritanceDecl
              {
                     base = DeclRefType(DeclRef(InterfaceDecl("IForwardDifferentiable")))
              }
              InheritanceDecl
              {
                     base = DeclRefType(DeclRef(InterfaceDecl("IBackwardDifferentiable")))
              }
              InheritanceDecl
              {
                     base = DeclRefType(DeclRef(InterfaceDecl("IDifferentiableWithContext")))
              }
              IntrinsicSynthesizedFuncDecl
              {      
                     name = "fwd_diff" // operatorName 
                     intrinsicOp = kIROp_ForwardDifferentiate
                     resultType = /* ..empty.. */
                     members = [/* ..empty.. */]
                     funcTypeExp = TypeExp(
                        MemberExpr(ThisExpr,
                        VarExpr("__fwd_diff_func_type"))) // We'll stick a type expression instead of a resolved type because we need to wait until conformances are checked before being able to resolve This.__bwd_prop_func_type
              },
              IntrinsicSynthesizedFuncDecl
              {      
                     name = "bwd_diff" // operatorName 
                     intrinsicOp = kIROp_BackwardDifferentiate
                     // resultType & members... (same as above)
                     funcTypeExp = TypeExp(
                        MemberExpr(ThisExpr,
                        VarExpr("__bwd_diff_func_type")))
              },
              IntrinsicSynthesizedFuncDecl
              {      
                     name = "eval_with_context" // operatorName 
                     intrinsicOp = kIROp_EvalWithContext
                     // resultType & members... (same as above)
                     funcTypeExp = TypeExp(
                        MemberExpr(ThisExpr,
                        VarExpr("__bwd_prop_func_type")))
              },
              IntrinsicSynthesizedStructDecl
              {      
                     name = "DiffContext" // operatorName 
                     intrinsicOp = kIROp_DiffContextType
                     members = 
                     [
                          // no field declarations since these will need to be
                          // synthesized in the backend.
                          // however, we can have inheritance decls:
                          InheritanceDecl(superType =
                              GenericAppDeclRef(
                                  InterfaceDecl("IDiffContext"), 
                                  subst=[funcDeclRef])),
                          // Any synthesized func decls to satisfy the inheritance decl:
                          IntrinsicSynthesizedFuncDecl
                          {
                              name = "__call",
                              targetFunc = funcDeclRef,
                              intrinsicOp = kIROp_EvalWithContext,
                              funcTypeExpr = TypeExpr(
                                    MemberExpr(
                                      ThisExpr(), 
                                      VarExpr("__bwd_prop_func_type"))
                          }
                     ]
              },
]
}
}
```
2.  In the `DefinitionChecked` stage: we insert a “hook” that gets called from `CheckTerm()` each time an expression is successfully checked within the function body. 

* This hook will be used to lower the witness for `checkedType : IDifferentiable` and if the expression is a callable (`checkedType` is a `FuncType`), will also lower witnesses for `callableExpr : IForwardDifferentiable`, `callableExpr : IBackwardDifferentiable` and `callableExpr : IDifferentiableWithContext`. These witnesses will be stored in a table associated with the function. 
  * There can be variants of this.. (e.g. `[ForwardDifferentiable]` tag can just lower `IForwardDifferentiable` )
* During IR lowering, as the `checkedType` or `callableExpr` is lowered, a hoistable annotation is inserted directly after the lower IR inst. 
  * This is `IRTypeConformanceAnnotation(irType, diffWitness)` for types and `IRFuncConformanceAnnotation(irFunc, funcWitness)` for functions (each witness gets a separate annotation)
  * This system is similar to how the current `IRDifferentiableTypeAnnotation()` system works & it allows types and functions at all levels (generic/parametric/existential/etc..) to express their conformance without running into odd def-before-use issues.

Checking `[Differentiable]` interface requirements.

In the new system, an interface requirement that requires conformance to function interfaces (e.g. via `[Differentiable]` ) will be lowered just like an associated type with constraints. 

e.g.:

```csharp
interface IFoo
{
    [Differentiable] float foo(float a);
}

will get translated to (during the modifiers checking phase)

InterfaceDecl
{
    members = [
      FuncDecl
      {
          name = "foo"
         // ... usual foo definition ..
      },
      TypeConstraintDecl
      {
          subType = DeclRefType(DeclRef(FuncDecl("foo"))),
          superType = DeclRefType(DeclRef(InterfaceDecl("IForwardDifferentiable"))),
      },
      // .. similar type constraints for each function interface on foo .. 
}

This will lead to witness tables requirement keys being embedded into the lowered interface,
and any functions that satisfy the “foo” requirement will need to lower the associated witness tables.

Modifications to FuncDecl 

The existing FuncDecl type will be extended to include:

FuncDecl
{
 // ... other fields ...

 funcTypeExpr = TypeExp(...); // Optional field. 
                              // If func-type expr is present, 
                              // then during decl-header-checking phase, 
                              // the resulting FuncType will be used to fill in the
                              // function's resultType and ParamDecls, assuming 
                              // that these are _not_ present (otherwise we issue an
                              // error diagnostic due to ambiguity)

}
```

### Checking `SynthesizedFuncDecl`

`SynthesizedFuncDecl` is used to denote a func-decl whose body will be synthesized in the IR backend (e.g. a function marked `[Differentiable]` will have extensions defined that contain a `SynthesizedFuncDecl` )

The `SynthesizedFuncDecl` has the following structure:

```csharp
OuterGeneric
{
SynthesizedFuncDecl : public FuncDecl
{
    targetFunc = DeclRef(Decl("targetFnToTranslate"));
}
}
```

with special variants for intrinsic-based synthesis, which lower to the appropriate translation op-code during the lower-to-IR step:

```csharp
IntrinsicSynthesizedFuncDecl : public SynthesizedFuncDecl 
{
    intrinsicOp = kIROp_xyz; // op-code for lowering.
}
```

The checking process does not involve anything else for this type of declaration (just verifying that `targetFunc` is resolved)

### Checking `SynthesizedStructDecl`

`SynthesizedStructDecl` is used to denote a struct type whose members will be synthesized in the IR backend. 
Example structure of a `SynthesizedStructDecl` for the diff context type

```csharp
OuterGeneric
{
SynthesizedStructDecl : public StructDecl
{
    targetDecl = DeclRef(Decl("targetFn")); 
    members = 
    [
        // no field declarations since these will need to be synthesized in the backend.
        // however, we can have inheritance decls:
        InheritanceDecl(superType = GenericAppDeclRef(InterfaceDecl("IDiffContext"), subst=funcDeclRef)),
        // Any synthesized func decls to satisfy the inheritance decl:
        IntrinsicSynthesizedFuncDecl
        {
            name = "__call",
            targetFunc = funcDeclRef,
            intrinsicOp = kIROp_EvalWithContext,
            funcTypeExpr = TypeExpr(MemberExpr(ThisExpr(), VarExpr("__bwd_prop_func_type")) 
        }
    ]
}
}
```

### Representing synthesized functions through `SynthesizedFuncDecl`

When checking that  foo conforms to some IFuncInterface , if a user-provided definition does not exist, we will insert a `SynthesizedFuncDecl` that contains the enum value in `[SynthesisOp(irOpCode)]`. 

`SynthesizedFuncDecl` is a `FuncDecl` without a body (though it does contain synthesized `ParamDecl`s & a resultType ). The `ParamDecl`s are synthesized based on the function type from the translation op. 
E.g. `__fwd_diff_func_type(f)` returns a `FuncType` with qualified parameter & result types.

#### Lowering to IR: 
A `DeclRef` to a `SynthesizedFuncDecl` will be lowered into the appropriate IR translation op-code stored on the `SynthesizedFuncDecl` 
The synthesis op’s operand must be a fully resolved function (not a lookup-method-inst or a generic). Thus, it must be emitted at the outer-most level.

i.e. `IRForwardDifferentiate(IRSpecialize(...))` is valid, `IRSpecialize(IRForwardDifferentiate(...))` is not valid.

### More complex synthesis patterns as sub-classes of `SynthesizedFuncDecl`

Sometimes, instead of a “full” transformation (e.g. complete backward differentiation through `IRBackwardDifferentiate(fnInst)`), it is desirable to re-use a user-provided implementation for a different interface and using a lightweight wrapper to coerce the function to the correct form. 
As an example, if `func : IDifferentiableWithContext` , then it’s `bwd_diff` can be trivially constructed by calling `eval_with_context` and then calling the result to perform backprop. 

In this case, we do not want to emit a `IRBackwardDifferentiate` inst. Instead, we’d prefer to emit something like `IRComposeEvalContextAndBwdProp(evalCtxFnInst, ctxType)` . To represent this in the AST, we can use different sub-class of `SynthesizedFuncDecl` like `BwdDiffFromContextDecl : SynthesizedFuncDecl` & lower that to the new op-code. This decl will be created instead of a standard `SynthesizedFuncDecl` when checking conformance to `IDifferentiableWithContext` 


### Checking `InvokeExpr` expressions that involve `fn.operator(args)`

Invoking an operator member of a function with some arguments is a rather complex invoke resolution scenario.

Unlike a regular `MemberExpr` that involves a regular type, a function reference can be overloaded, and Slang allows generic parameter inference, so this overload group may contain unspecialized or partially specialized generic candidates.

To make things a bit more complex, we can’t be sure that `operator` is defined for a generic `fn` until we infer specialization parameters for `fn`, since the extension defining the operator may not apply.

However, the proposed solution is not too complex.

If `fn.operator` is already a resolved `DeclRef`, then the lookup system was able to find the right implementation.

Our main concern is when `fn.operator` is still a `MemberExpr(fnExpr, operatorName) `

Here, we have three possibilities, which we’ll see case-by-case:

* an `OverloadGroup` : 
    Create an OverloadGroup of candidates where each candidate is `MemberExpr(candidateExpr, operatorName)` and check each candidate. 
* a `DeclRef<GenericDecl>` (unspecialized): 
  * This is a more complex scenario since we are trying to infer generic arguments for the base `GenericDecl` , while simultaneously trying to find the correct implementation for `operatorName`.
There can be multiple possible implementations (via multiple extensions), so our strategy is to enumerate them while adding the unification constraints to the constraint system:
  * New type of lookup: Perform a lookup for `operatorName`  on the unspecialized generic with a new type of lookup function. Usually, we can’t look things up on unspecialized types since we don’t know what extensions apply. This will return a set of `LookupResultItem` objects which have the associated extension’s `targetType` embedded into them. These will be represented with a different new flavor (maybe `Constrained`)
E.g.: `extension bar<T : IFloat> : IForwardDifferentiable { void fwd_diff(DifferentiablePair<T> x) { /* .. */ } }` can be looked up via `bar.fwd_diff()` and will return a `LookupResultItem` that contains `bar<T : IFloat>` as a constraint type.
  * During overload resolution, if we encounter such a `Constrained` object, we will run generic inference on all of the parent generic containers. This is an important difference from the current `inferGenericArgs()` function which only considers the callable’s generic parent. 
  * The inference procedure is roughly the same, but we will use the same `ConstraintSystem` object and `TryUnifyTypes` of the function’s parameters with the arguments. The difference is that we use the resulting constraint system to create specialized decl-refs for each of the parent generic containers, and assemble that into a fully specialized decl-ref to the looked up function.
  * If unification/generic inference fails, then this candidate doesn’t work.
* a `PartiallyAppliedGenericExpr` :
  * Same as above, but we add the `knownGenericArgs` into the mix when solving constraint system.
