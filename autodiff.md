Automatic Differentiation {#autodiff}
=========================

<div class=issue>
This chapter needs to specify:


\begin{itemize}
\item The built-in types and attributes related to automatic differentiation.
\item The rules applied when checking the body of a \code{[Differentiable]} function.
\item The semantics of the \code{fwd_diff} and \code{bwd_diff} operators, including how to determine the signature of the function they return.
\item The requirements of the \code{IDifferentiable} interface, and also the rules used to automatically synthesize conformance for it.
\end{itemize}
</div>