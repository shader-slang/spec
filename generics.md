Generics {#generic}
========

<div class=issue>
This chapter needs to define the key semantic-checking operations that relate to generics, including:

\begin{itemize}
\item Inference of \emph{implied constraints} on a generic declaration, based on the signature of that declaration.

\item Validation and canonicalization of constraints on generic declarations.

\item Validation of explicit specialization of a generic (e.g., `G<A,B>`), which includes validating that the constraints on the generic are satisfied by the parameters.

\item Inference of generic arguments in contexts where a generic function is called on value arguments (without first specializing it).
\end{itemize}

</div>