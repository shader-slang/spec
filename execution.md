Execution Model {#exec}
===============

<div class=issue>
Even if we don't define a completely formal runtime semantics, we need sufficient terminology to be able to explain the intended semantics of language constructs, including things like \code{discard}, shared memory, wave-level ops, etc.

Key concepts that this chapter will need to discuss:

\begin{itemize}
\item A concept of systems that might be comprised of multiple \emph{devices}, and which might have multiple distinct \emph{memory spaces} that may or may not be shared.

\item The notion of a thread or invocation that runs Slang code in a largely scalar/sequential fashion.

\item Any notions of groupings of threads (quads, subgroups/waves/warps, thread blocks/workgroups, dispatches/grids/draws, etc.) that might have semantic consequences

\item A definition of what it means for execution to be \emph{convergent} for a grouping of threads, and what it means for data to be \emph{uniform} across such groups.

\item A definition of what memory \emph{objects} and/or \emph{locations} are, and the kinds of \emph{accesses} that may be performed to them (reads, writes, atomics, etc.).

\item Definitions of what an \emph{activation} of a function is, and how those activations comprise the call stack of a thread.

\item A definition of core GPU rendering concepts such as \emph{pipelines}, \emph{stages}, \emph{kernels}, \emph{varying} input/output, \emph{uniform} shader parameters, etc.
\end{itemize}

</div>

