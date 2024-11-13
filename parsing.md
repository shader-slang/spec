Parsing {#parse}
=======

<div class=issue>
The intention of this chapter is to establish the overall rules for the recursive-descent parsing strategy needed for Slang's grammar.

Slang attempts to thread the needle by supporting the familiar C-like syntax of existing shading languages, while \emph{also} support out-of-order declarations.
The parsing strategy is necessarily complicated as a result, but we hope to isolate most of the details to this chapter so that the grammar for each construct can be presented in its simplest possible fashion.
</div>

<dfn>Parsing</dfn> is the process of matching a sequence of tokens from the lexical grammar with a rule of the abstract syntax grammar.

Contexts {#parse.context}
--------

Parsing is always performed with respect to a \SpecRef{context}, which determines which identifiers are bound, and what they are bound to.

The <dfn>initial context</dfn> for parsing includes bindings for syntax rules corresponding to each declaration, statement, and expression keyword defined in this specification.

\begin{Example}
An \code{if} expression begins with the \code{if} keyword, so the initial context contains a binding for the identifier \code{if} to a syntax rule that parses an \code{if} expression. 
\end{Example}

The initial context also includes bindings for the declarations in the Slang standard library.
Implementations may include additional bindings in the initial context.


Strategies {#parse.strat}
----------

Parsing is always performed in one of two modes: unordered or ordered.
Unless otherwise specified, each grammar rule matches its sub-rules in the same mode.

### Ordered ### {#parse.strat.ordered}

Parsing in <dfn>ordered</dfn> mode interleaves parsing and semantic analysis.
When the parser is in ordered mode and attempts to match the \SynRef{Declaration}, \SynRef{Statement}, or \SynRef{Expression} rules, and the lookahead is an \SynRef{Identifier}, it first looks up that identifier in the context.

\begin{itemize}
\item If the identifier is bound to a syntax rule \MetaVar{S}, then the parser only considers productions that can start with \MetaVar{S}.
\item Otherwise, it first matches the \SynRef{Term} rule, and then based on whether the result of checking that term is a type or a value, it either considers only productions starting with a \SynRef{Type} or those starting with an \SynRef{Expression}.
\end{itemize}

If the parser is in ordered mode and is about to match the \SynRef{DeclarationBody} rule, it switches to unordered mode before matching that rule, and switches back to ordered mode afterward.

### Unordered ### {#parse.strat.unordered}

In <dfn>unordered</dfn> mode, semantic analysis is deferred.

When the parser is in unordered mode and attempts to match the \SynRef{Declaration} rule, and the lookahead is an \SynRef{Identifier}, it first looks up that identifier in the context.

\begin{itemize}
\item If the identifier is bound to a syntax rule \MetaVar{S}, then the parser only considers productions that can start with \MetaVar{S}.
\item Otherwise, it considers only productions that start with a \SynRef{TypeSpecifier}.
\end{itemize}
    
\begin{Syntax}
\SynDefine{BalancedTokens} \\
    \SynRef{BalancedToken}\SynStar

\SynDefine{BalancedToken} \\
    \lstinline|{| \SynRef{BalancedTokens} \lstinline|}| \\
    | \lstinline|(| \SynRef{BalancedTokens} \lstinline|)| \\
    | \lstinline|[| \SynRef{BalancedTokens} \lstinline|]| \\
    | \SynComment(any token other than \lstinline|{|, \lstinline|}|, \lstinline|(|, \lstinline|)|, \lstinline|[|, \lstinline|]|)
\end{Syntax}

A <dfn>balanced</dfn> rule in the grammar is one that meets one of the following criteria:
\begin{itemize}
\item starts with a \lstinline|{| and ends with a \lstinline|}|
\item starts with a \lstinline|(| and ends with a \lstinline|)|
\item starts with a \lstinline|[| and ends with a \lstinline|]|
\end{itemize}

Whenever the parser is in ordered mode and would attempt to match a balanced rule \MetaVar{R}, it instead matches the \SynRef{BalancedToken} rule and saves the token sequence that was matched.
Those tokens are then matched against \MetaVar{R} as part of semantic analysis, using the context that the checking rules specify.

Angle Brackets {#parse.angle}
--------------

### Opening Angle Brackets ### {#parse.angle.open}

\SubSubSection{Ordered Mode}{ordered}

If the parser is in ordered mode with a lookahead of \code{<}, and it could match that token as part of either an \SynRef{InfixExpression} or a \SynRef{SpecializeExpression}, then it considers the term that has been matched so far:

\begin{itemize}
\item If the term has a generic type or overloaded type, then the \SynRef{SpecializeExpression} case is favored.
\item Otherwise the \SynRef{InfixExpression} case is favored.
\end{itemize}

\SubSubSection{Unordered Mode}{unordered}

If the parser is in ordered mode with a lookahead of \code{<}, and it could match that token as part of either an \SynRef{InfixExpression} or a \SynRef{SpecializeExpression}, then it first attempts to match the \SynRef{GenericArguments} rule. If that rule is matched successfully, then the new lookahead token is inspected:

\begin{itemize}
\item If the lookahead token is an \SynRef{Identifier}, \lstinline|(|, \SynRef{Literal}, or \SynRef{PrefixOperator}, then roll back to before the \code{<} was matched and favor the \SynRef{InfixExpression} rule.
\item Otherwise, use the generic arguments already matched as part of matching the \SynRef{SpecializeExpession} rule.
\end{itemize}

### Closing Angle Brackets ### {#parse.angle.close}

If the parser is attempting to match the closing \code{>} in the \SynRef{GenericParameters} or \SynRef{GenericArguments} rules, and the lookahead is any token other than \code{>} that starts with a greater-than character (\code{>=}, \code{>>}, or \code{>>=}), then it splits the opening \code{>} off and matches it, replacing the lookahead with a token comprised of the remaining characters (\code{=}, \code{>}, or \code{>=}).
