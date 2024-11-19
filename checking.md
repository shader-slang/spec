Semantic Checking {#check}
=================

<div class=issue>
The intention of this chapter is to establish the formalisms and notations that will be used for expressing typing judgements and other semantic-checking rules in this specification.

The notation being used here is aligned with how papers in the PLT world on type theory, semantics, etc. present a language.
</div>

Contexts {#check.context}
--------

A <dfn>context</dfn> is an ordered sequence of zero or more <dfn>context entries</dfn>.
Context entries include <dfn>bindings</dfn> of the name of a variable (an [[=identifier=]]) to its type.

```.checking

    Context :
        ContextEntry*
    
    ContextEntry :
        Binding
    
    Binding :
        Identifier : Type // variable
        Identifer = Value // alias
```

A context |c| <dfn>binds</dfn> an identifier |n| if |c| contains one or more [=bindings=] with |n| on the left-hand side.

Issue: We need to describe here the process by which an identifier resolves to a binding, including overloaded, etc.
The discussion here will have to be a forward reference to the algorithms to be given later.

Expressions {#check.expr}
-----------

Slang use a bidirectional type-checking algorithm.
There are two different judgements used when checking expressions.

### Synthesis ### {#check.synth}

A <dfn>synthesis judgement</dfn> determines that, given a [=context=] |c| and an [=expression=] |e|, |e| <dfn>synthesizes</dfn> some [=type=] |t| in context |c|.

Issue: as written here, a synthesis judgement might actually have *side effects* on the context.
That needs to be specified somehow.

Note: Synthesis judgements are used in places where an expression needs to be checked, but the expected type of that expression in not known.
In algorithmic terms |c| and |e| are inputs, while |t| is an output.

### Checking ### {#check.check}

A <dfn>checking judgement</dfn> determines that, given a [=context=] |c|, an [=expression=] |e|, and a [=type=] |t|, |e| <dfn>checks against</dfn> |t| in context |c|.

Note: Checking judgements are used in places where the type that an expression is expected to have is known.
In algorithmic terms |c|, |e|, and |t| are all inputs.

Statements {#check.stmt}
----------

Statement also use [=checking judgements=].
A checking judgement for a statement determines that [=statement=] |s| <dfn>checks</dfn> in [=context=] |c|.

Declarations {#check.decl}
------------

Declarations also use [=checking judgements=].
A checking judgement for a declaration determines that [=declaration=] |d| [[=checks=]] in [=context=] |c|.

Checking of a declaration may modify the context |c| to include additional bindings.
