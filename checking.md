Semantic Checking {#check}
=================

\begin{TODO}
The intention of this chapter is to establish the formalisms and notations that will be used for expressing typing judgements and other semantic-checking rules in this specification.

The notation being used here is aligned with how papers in the PLT world on type theory, semantics, etc. present a language.




\end{TODO}

Contexts {#check.context}
--------

A \SpecDef{context} is an ordered sequence of zero or more \SpecDef{context entries}.
Context entries include \SpecDef{bindings} of the name of a variable (an identifier) to its type.

\begin{Syntax}
    \SynDefine{context}
        \ContextVarA, \ContextVarB, ... \SynComment{context variable} \\
        \SynOr $null$ \SynComment{empty context} \\
        \SynOr \SynRef{context}, \SynRef{binding}

    \SynDefine{binding}
        $name$ : $type$ \SynComment{variable} \\
        \SynOr $name$ :  \textsc{Exactly}($value$) \SynComment{alias}
\end{Syntax}


The notation:
\begin{center}
\ContextContains{\ContextVarA}{E}
\end{center}
indicates that the context \ContextVarA\ contains an entry matching $E$.

The notation:
\begin{center}
\ContextLookup{\ContextVarA}{k}{v}
\end{center}
indicates that the right-most entry in context \ContextVarA\ that has key $k$ maps to $v$.

Expressions {#check.expr}
-----------

Slang use a bidirectional type-checking algorithm.
There are two different judgements used when checking expressions.

### Synthesis ### {#check.synth}

The notation:
\begin{center}
\SynthExpr{\ContextVarA}{e}{t}{\ContextVarB}
\end{center}
means that under input context \ContextVarA, the expression $e$ \SpecDef{synthesizes} the type $t$, an yields output context \ContextVarB.

\begin{Description}
Synthesis judgements are used in places where an expression needs to be checked, but the expected type of the expression is not known.
In terms of implementation, \ContextVarA and $e$ are inputs, while $t$ and \ContextVarB are outputs.
\end{Description}

### Checking ### {#check.check}

The notation:
\begin{center}
\CheckExpr{\ContextVarA}{e}{t}{\ContextVarB}
\end{center}
means that under input context \ContextVarA, the expression $e$ \SpecDef{checks} against the type $t$, and yields output context \ContextVarB.

\begin{Description}
Checking judgements are used in places where the type that an expression is expected to have is known.
In terms of implementation, \ContextVarA, $e$, and $t$ are all inputs, and \ContextVarB is the only output.
\end{Description}


Statements {#check.stmt}
----------

The notation:
\begin{center}
\CheckStmt{\ContextVarA}{s}{\ContextVarB}
\end{center}
means that under input context \ContextVarA, checking of statement $s$ is successful, and yields output context \ContextVarB.

Declarations {#check.decl}
------------

The notation:
\begin{center}
\CheckDecl{\ContextVarA}{d}{\ContextVarB}
\end{center}
means that under input context \ContextVarA, checking of declaration $d$ is successful, and yields output context \ContextVarB.

