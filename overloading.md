Overload Resolution {#overload}
===================

\begin{TODO}

This chapter needs to describe how to disambiguate an overloaded lookup result.
Overload resolution comes up primarily in two places:

\begin{itemize}
\item When the typing rules attempt to coerce an overloaded expression to some type.
\item When attempting to call an overloaded expression as a function.
\end{itemize}

(Hypothetically it can also arise for a generic specialization `F<A,B,...>` as well, so the rules need to be ready for that case)

The first of the two cases is the easier one by far, with an outline of it's semantics being:

\begin{itemize}
\item \emph{Filter} the candidates to only those that can be coerced successfully to the desired type.
\item Select the best candidate among the remaining ones, based on priority.
\subitem The relative "distance" of declarations needs to factor in (more derived vs. more base, imported vs. local, etc.)
\subitem Additionally, the relative cost of the type conversions applied (if any) may be relevant.
\end{itemize}

The second case (overloaded calls) is superficially similar, in that we can filter the candidates to the applicable ones and then pick the best.
The definition of ``best'' for an overloaded call is more subtle and needs care to not mess up developer expectations for things like simple infix expressions (since event infix \code{operator+} is handled as an overloaded call, semantically).

A few basic principles that guide intuition:

\begin{itemize}
\item For every candidate we should know the conversion/cost associated with each argument position, as well as the conversion/cost associated with the function result position (if we are in a checking rather than synthesis context).
\item One overload candidate is strictly better than another if it is better at at least one position (one argument, or the function result), and not worse at any position.
\item When choosing between candidates that are equally good, a few factors play in:
\subitem The relative "distance" of declarations (as determined by lookup)
\subitem Which candidates required defaulting of arguments (and how many)
\subitem Candidates that required implicit specialization of a generic vs. those that didn't
\subitem For two candidates that required implicit specialization of a generic, which of them is ``more general'' than the other.
\end{itemize}

Generally, a function $f$ is ``more general'' than another function $g$ if for every set of arguments that $g$ is applicable to, $f$ is \emph{also} applicable, but not vice versa.

Also: it doesn't exactly belong in this chapter, but something needs to document the rules for when two function declarations are considered to have the same signature (or at least conflicting signatures), so that errors can be diagnosed when trying to redefine a function.

\end{TODO}
