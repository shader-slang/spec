Type Conversions {#conv}
================

\begin{TODO}

Broadly this chapter needs to do two things:

\begin{itemize}
\item Define the semantic rules for implicit type coercion and explicit type conversion.
\item Specify the implicit coercions that are defined for the basic Slang types, and their costs.
\end{itemize}

The latter part (the builtin implicit coercions and their costs) can be a simple table, once the rules are properly defined.

From a big-picture perspective, the implicit type coercion rules when coercing something of type \code{From} to type \code{To} are something like:

\begin{itemize}
\item If \code{From} and \code{To} are identical types, then coercion succeeds, with no cost.
\item If \code{From} is a subtype of \code{To}, then coercion succeeds, with a cost that relates to how "far" apart the types are in an inheritance hierarchy.
\item If neither of the above applies, look up \kw{init} declarations on type \code{To}, filtered to those that are marked as suitable for implicit coercion, and then perfom overload resolution to pick the best overload. The cost is the cost that was marked on the chosen \kw{init} declaration.
\end{itemize}

The overload resolution rules rely on checking implicit type coercions, and the implicit type coercion rules can end up checking an overloaded \kw{init} call.
The specification must explain how to avoid the apparant possibility of infinite recursion.
The simplest way to avoid such problems is to specif that the overload resolution for the \kw{init} call above uses a modified form where only subtyping, and not implicit coercion, is allowed for arguments.

Explicit type conversion follows the same overall flow as the implicit case, except it does not filter the candidates down to only those marked as usable for implicit coercion.

\end{TODO}