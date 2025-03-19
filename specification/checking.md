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

Slang expressions are validated across two steps: *preparation* and *checking*.

```.semantics
CheckedExpression
    => TypedValue // includes declaration references
    => CheckedExpression `(` CheckedExpression* `)`
    => `let` Identifier `=` CheckedExpression `in` CheckedExpression

PreparedExpression
    => CheckedExpression
    => OverloadSet
    => `$InitializerList` PreparedExpression*

Expression
    => ParsedExpression
    => PreparedExpression
```


### Preparation [check.expr.prep]

**Preparing** an *expression* in a *context* yields a *prepared expression*, or diagnoses an error.

> Issue:
>
> It has been a struggle to pick an appropriate term for this operation.
>
> More or less, the idea is that we can "poke" an expression and ask it to check itself as much as it can without committing to any difficult decisions.
> It is possible that the result will be a fully-checked expression with a single clear type, but it is *also* possible that the result will be something like an overload set that cannot be resolved to a single expression with a single type without some help.
>
> Those familiar with bidirectional type-checking might see this as similar to a synthesis judgement, but what we are descriving here is different in two main ways:
>
> * The first, incidental, difference is that the *preparation* step yields not just a *type* but an entire *expression*.
>
> * The second, more important, difference is that *preparing* an expression does not necessarily yield a typed result; it is also possible for preparation to throw up its hands and say that it just doesn't know.
>
> When preparation fails to produce a fully typed expression, additional context is required to finish the job (or, if additional context isn't available, an error must be diagnosed).
> One might wonder: why have the checking rules withold such information, if it is available?
>
> Thinking about function calls helps make the design choices clear.
> Consider a trivial call _f_ `(` _a_ `)`.
> If we *prepare* each of _f_ and _a_, then each can either yield a fully-typed expression, or not.
> Thus there are four cases:
>
> * If _f_ and _a_ both prepare into fully-typed expressions, then everything is easy. We can try to implicitly convert _a_ to the type expected by the parameter of _f_, and the overall type is the result type of _f_.
>
> * If _f_ prepares into a fully-typed expression, but _a_ does not (imagine _a_ is an *initializer list*), then things are *still* easy. We can do the same implicit conversion as the previous case, so that checking of _a_ now has additional context to resolve the ambiguity (e.g., we know what type to construct from the initializer list).
>
> * If _a_ prepares into a fully-typed expression, but _f_ does not (imagine _f_ is an *overload set*), then things are harder, but we can still exploit the information we *do* have. We can *filter* the *overload* set for _f_ down to just the *candidates* that can be called on a single argument with the type of _a_.
>
> * If *neither* of _a_ or _f_ prepares into a fully-typed expression, we are in the hardest case. We can filter the candidates of _f_ down into those with the right arity. Filtering any further requires a kind of back-and-forth exchange of information between the candidates for _f_ and the form of the argument _a_.
>
> For the third and fourth of these options, it  becomes useful to have information from the context surrounding the call expression: namely, the type (if any) that the call is expected to produce.
>
> Note how by including the *preparation* step, the semantic-checking rules are able to tailor a solution to each of these four cases. A classic problem for bidirectional type-checking systems is whether the function or the arguments "go first" in the synthesis judgement, but here we get to try both options and see if either bears fruit.
> 


### Checking [check.check]

**Checking** an *expression* against a *type* in a *context* may yield a *checked expression*, or diagnoses an error.

Note: Checking is used in places where the type that an expression is expected to have is known.

To check an *expression* _e_ against a type _T_ when form of _e_ does not define a checking rule:

* Let _pe_ be the result of *preparing* _e_
* Return the result of *implicitly converting* _pe_ to _T_

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
