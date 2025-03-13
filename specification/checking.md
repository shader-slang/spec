Semantic Checking [check]
=================

> Issue:
>
> The intention of this chapter is to establish the formalisms and notations that will be used for expressing typing judgements and other semantic-checking rules in this specification.
>
> The notation being used here is aligned with how papers in the PLT world on type theory, semantics, etc. present a language.

Contexts [check.context]
--------

A **context** is an ordered sequence of zero or more **context entries**.
*Context entries* include **bindings** of the name of a variable (an *identifier*) to its type.

```.checking

    Context :
        ContextEntry*
    
    ContextEntry :
        Binding
    
    Binding :
        Identifier : Type // variable
        Identifer = TypedValue // alias
```

A context _c_ **binds** an identifier _n_ if _c_ contains one or more *bindings* with _n_ on the left-hand side.

Issue: We need to describe here the process by which an identifier resolves to a *binding*, including overloaded, etc.
The discussion here will have to be a forward reference to the algorithms to be given later.

Expressions [check.expr]
-----------

Slang use a variation on a bidirectional type-checking algorithm.

There are two main steps used when checking expressions.
Each form of expression may define rules for synthesis, checking, or both.

> Issue:
> We need to define what checked expressions, resolved expressions, and (parsed) expressions are.
> 
> A parsed expression is what you get out of the relevant parsing rules for `Expression`.
> 
> A checked expression is a limited subset of forms that includes stuff like:
> 
> * typed values
> * declaration references
> * calls
> 
> A typed value evaluates to itself, with no side effects.
> 
> A resolved expression is either a checked expression *or* one of a few cases that need further context:
> 
> * overloaded declaration references
> * overloaded calls
> * initializer lists
> 
> We also need to drill into the representation of types and values...

```.semantics
CheckedExpression
    => TypedValue // includes declaration references
    => CheckedExpression `(` CheckedExpression* `)`
    => `let` Identifier `=` CheckedExpression `in` CheckedExpression

IntermediateExpression
    => CheckedExpression
    => `OverloadSet` CheckedExpression*
    => `InitializerList` IntermediateExpression*
    => `OverloadedCall` IntermediateExpression `(` IntermediateExpression* `)`

Expression
    => ParsedExpression
    => IntermediateExpression
```


### Synthesis [check.expr.synth]

**Synthesizing** an *expression* in a *context* may yield some *intermediate expression*.

Note: Synthesis is used in places where an expression needs to have some amount of validation performed, but an expected type for the expression is not available.

To *synthesize* an *expression* _e_ in context _c_, when the syntactic form of _e_ does not have an explicit synthesis rule that applies:

* Extend _c_ with a fresh type variable _t_
* Return the result of checking _e_ against _t_ in _c_

### Checking [check.check]

**Checking** an *expression* against a *type* in a *context* may yield a *checked expression*.

Note: Checking is used in places where the type that an expression is expected to have is known.

To check an *expression* _e_ against a type _T_ when form of _e_ does not define a checking rule:

* Let _se_ be the result of synthesizing _e_
* Return the result of implicitly coercing _se_ to a _T_

Type Expressions [check.type]
----------------

*Type expressions* are syntactically a subset of *expressions*.

To check an expression _e_ **as a type**, check it against the type `TYPE`.

Statements [check.stmt]
----------

Statement also use *checking judgements*.
A checking judgement for a statement determines that *statement* _s_ **checks** in *context* _c_.

Declarations [check.decl]
------------

Declarations also use *checking judgements*.
A checking judgement for a declaration determines that *declaration* _d_ *checks* in *context* _c_.

Checking of a declaration may modify the context _c_ to include additional bindings.
