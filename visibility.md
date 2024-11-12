Visibility Control {#vis}
==================

\begin{TODO}
This chapter needs to explain the rules for:

\begin{itemize}

\item What declarations in a module are visible to modules that \kw{import} it?

\item What are the modifiers that can be used to control visibility (\kw{public}, \kw{internal}, \kw{private}), and what are their semantics.

\item What is the inferred visibility of a declaration without an explicit modifier?

\item What are the rules about what modifiers are legal in what contexts?
\subitem E.g., a \kw{public} field should not be allowed in an \kw{internal} type.
\subitem E.g., a \kw{public} function should not be allowed to have a non-\kw{public} type used in its signature.

\item How is visibility controlled for interface conformances?

\end{itemize}
\end{TODO}