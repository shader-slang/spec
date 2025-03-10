Semantic Checking [check]
=================

<div class=issue>
The intention of this chapter is to establish the formalisms and notations that will be used for expressing typing judgements and other semantic-checking rules in this specification.

The notation being used here is aligned with how papers in the PLT world on type theory, semantics, etc. present a language.
</div>

Contexts [check.context]
--------

A <dfn>context</dfn> is an ordered sequence of zero or more <dfn>context entries</dfn>.
[=Context entries=] include <dfn>bindings</dfn> of the name of a variable (an [[=identifier=]]) to its type.

```.checking

    Context :
        ContextEntry*
    
    ContextEntry :
        Binding
    
    Binding :
        Identifier : Type // variable
        Identifer = TypedValue // alias
```

A context |c| <dfn>binds</dfn> an identifier |n| if |c| contains one or more [=bindings=] with |n| on the left-hand side.

Issue: We need to describe here the process by which an identifier resolves to a [=binding=], including overloaded, etc.
The discussion here will have to be a forward reference to the algorithms to be given later.

Expressions [check.expr]
-----------

Slang use a variation on a bidirectional type-checking algorithm.

There are two main steps used when checking expressions.
Each form of expression may define rules for resolving, checking, or both.

<div class="issue">
We need to define what checked expressions, resolved expressions, and (parsed) expressions are.

A parsed expression is what you get out of the relevant parsing rules for `Expression`.

A checked expression is a limited subset of forms that includes stuff like:

* typed values
* declaration references
* calls

A typed value evaluates to itself, with no side effects.

A resolved expression is either a checked expression *or* one of a few cases that need further context:

* overloaded declaration references
* overloaded calls
* initializer lists

We also need to drill into the representation of types and values...

</div>

### Resolving [check.expr.resolve]

Resolving an [=expression=] in a context results in a <dfn>resolved expression</dfn>.

Note: Resolving is used in places where an expression needs to have some amount of validation performed, but an expected type for the expression is not available.

To resolve an [=expression=] |e| when the form of |e| does not define a resolving rule:

* Extend the context with a fresh type variable |T|
* Return the result of checking |e| against |T|

### Checking [check.check]

Checking a [=resolved expression=] against a type results in a checked expression.

Note: Checking is used in places where the type that an expression is expected to have is known.

To check an [=expression=] |e| against a type |T| when form of |e| does not define a checking rule:

* Let |re| be the result of resolving |e|
* Return the result of coercing |re| to |T|

OLD TEXT:
A <dfn>checking judgement</dfn> determines that, given a [=context=] |c|, an [=expression=] |e|, and a [=type=] |t|, |e| <dfn>checks against</dfn> |t| in context |c|.


Statements [check.stmt]
----------

Statement also use [=checking judgements=].
A checking judgement for a statement determines that [=statement=] |s| <dfn>checks</dfn> in [=context=] |c|.

Declarations [check.decl]
------------

Declarations also use [=checking judgements=].
A checking judgement for a declaration determines that [=declaration=] _d_ [[=checks=]] in [=context=] |c|.

Checking of a declaration may modify the context |c| to include additional bindings.
