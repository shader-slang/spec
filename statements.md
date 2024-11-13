Statements {#stmt}
==========

A <dfn>statement</dfn> is an entity in the abstract syntax that describes actions to be taken by a thread.
Statements are executed for their effect, rather than evaluated to produce a value.

\begin{Syntax}
	\SynDefine{Statement} \\
		\SynRef{ExpressionStatement} \\
		| \SynRef{DeclarationStatement} \\
		| \SynRef{BlockStatement} \\
		| \SynRef{EmptyStatement} \\
		| \SynRef{IfStatement} \\
		| \SynRef{SwitchStatement} \\
		| \SynRef{CaseStmt} \\
		| \SynRef{ForStatement} \\
		| \SynRef{WhileStatement} \\
		| \SynRef{DoWhileStatement} \\
		| \SynRef{BreakStatement} \\
		| \SynRef{ContinueStatement} \\
		| \SynRef{ReturnStatement} \\
		| \SynRef{DiscardStatement} \\
		| \SynRef{LabeledStatement} \\
\end{Syntax}

Expression Statement {#stmt.expr}
--------------------

An <dfn>expression statement</dfn> evaluates an expression, and then ignores the resulting value.

\begin{Syntax}
	\SynDefine{ExpressionStatement} \\
		\SynRef{Expression} \code{;}
\end{Syntax}

\begin{Checking}
\DerivationRule{
	\SynthExpr{\ContextVarA}{\ExprVarE}{\TypeVarT}{\ContextVarB}
}{
	\CheckStmt{\ContextVarA}{\ExprVarE \code{;}}{\ContextVarB}
}
\end{Checking}

An implementation may diagnose a warning when execution of an expression statement cannot have side effects.

Declaration Statement {#expr.decl}
---------------------

A <dfn>declaration statement</dfn> introduces a declaration into the current scope.
	
\begin{Syntax}
	\SynDefine{DeclarationStatement} \\
		\SynRef{Declaration}
\end{Syntax}

\begin{Checking}
	\DerivationRule{
		\CheckDecl{\ContextVarA}{\MetaVar{D}}{\ContextVarB}
	}{
		\CheckStmt{\ContextVarA}{\MetaVar{D}}{\ContextVarB}
	}
\end{Checking}
	
Only the following types of declarations may be used in a declaration statement:

\begin{itemize}
\item \SynRef{VariableDeclaration}
\end{itemize}

Block Statement {#stmt.block}
---------------

A <dfn>block statement</dfn> executes each of its constituent statements in order.

\begin{Syntax}
	\SynDefine{BlockStatement} \\
		\lcurly \SynRef{Statement}\SynStar \rcurly
\end{Syntax}


\begin{Checking}

	\DerivationRule{
		\CheckStmts{\ContextVarA}{ \bar{\MetaVar{S}} }{\ContextVarB}
	}{
		\CheckStmt{\ContextVarA}{ \lcurly \bar{\MetaVar{S}} \rcurly }{\ContextVarA}
	}

	\DerivationRule{
		\begin{trgather}
		\CheckStmt{\ContextVarA}{ \MetaVar{S} }{\ContextVarB} \\
		\CheckStmts{\ContextVarB}{ \bar{\MetaVar{T}} }{\ContextVarC}
		\end{trgather}
	}{
		\CheckStmts{\ContextVarA}{ \MetaVar{S}\ \bar{\MetaVar{T}} }{\ContextVarC}
	}

\end{Checking}

Note: Declarations in a block statement are visible to later statements in the same block, but not to earlier statements in the block, or to code outside the block.	

Empty Statement {#stmt.empty}
---------------

\begin{Description}
	Executing an empty statement has no effect.
\end{Description}
	
\begin{Syntax}
	\SynDefine{EmptyStatement} \\
		\code{;}
\end{Syntax}

\begin{Checking}
	\CheckStmt{\ContextVarA}{ \code{;} }{\ContextVarA}
\end{Checking}

Conditional Statements {#stmt.cond}
----------------------

### If Statement ### {#stmt.if}

An <dfn>\code{if} statement</dfn> executes a sub-statement conditionally.

\begin{Syntax}
	\SynDefine{IfStatement} \\
		\code{if} \code{(} \SynRef{Condition} \code{)}
		\SynRef{Statement}
		\SynRef{ElseClause}\SynOpt \\

	\SynDefine{Condition}
		\SynRef{Expression}
		| \SynRef{LetDeclaration} \\

	\SynDefine{ElseClause}
		\code{else} \SynRef{Statement} \\
	
\end{Syntax}

\begin{Checking}

	\DerivationRule{
		\begin{trgather}
		\CheckExpr{\ContextVarA}{\ExprVarE}{\code{Bool}}{\ContextVarB} \\
		\CheckStmt{\ContextVarB}{\MetaVar{T}}{\ContextVarC} \\
		\end{trgather}	
	}{
		\CheckStmt{\ContextVarA}{\code{if(} \ExprVarE \code{)} \MetaVar{T}}{\ContextVarA}
	}

	\DerivationRule{
		\begin{trgather}
		\CheckExpr{\ContextVarA}{\ExprVarE}{\code{Bool}}{\ContextVarB} \\
		\CheckStmt{\ContextVarB}{\MetaVar{T}}{\ContextVarC} \\
		\CheckStmt{\ContextVarB}{\MetaVar{E}}{\ContextVarD}
		\end{trgather}	
	}{
		\CheckStmt{\ContextVarA}{\code{if(} \ExprVarE \code{)} \MetaVar{T} \code{else} \MetaVar{E}}{\ContextVarA}
	}
	
\end{Checking}

If the condition of an \code{if} statement is an expression, then it is evaluated against an expected type of \code{Bool} to yield a value \MetaVar{C}.
If \MetaVar{C} is \code{true}, then the \SynRef{ThenClause} is executed.
If \MetaVar{C} is \code{false} and there is a \SynRef{ElseClause}, then it is executed.

If the condition of an \code{if} statement is a \code{let} declaration, then that declaration must have an initial-value expression.
That initial-value expression is evaluated against an expected type of \lstinline[style=SlangCodeStyle]|Optional<$\MetaVar{T}$>|, where \MetaVar{T} is a fresh type variable, to yield a value \MetaVar{D}.
If \MetaVar{D} is \lstinline[style=SlangCodeStyle]|Some($\MetaVar{C}$)|, then the \SynRef{ThenClause} is executed, in an environment where the name of the \code{let} declaration is bound to \MetaVar{C}.
If \MetaVar{D} is \code{null} and there is a \SynRef{ElseClause}, then it is executed.

### Switch Statement ### {#stmt.switch}

A <dfn>\code{switch} statement</dfn> conditionally executes up to one of its <dfn>alternatives</dfn>, based on the value of an expression.
	
\begin{Syntax}
	\SynDefine{SwitchStatement} \\
		\code{switch} \code{(} \SynRef{Expression} \code{)}
		\lcurly\ \SynRef{SwitchAlternative}\SynPlus \rcurly\ \\

	\SynDefine{SwitchAlternative} \\
		\SynRef{SwitchAlternativeLabel}\SynPlus \SynRef{Statement}\SynPlus

	\SynDefine{SwitchAlternativeLabel}
		\SynRef{CaseClause}
		| \SynRef{DefaultClause} \\
	
	\SynDefine{CaseClause}
		\code{case} \SynRef{Expression} \code{:} \\
	
	\SynDefine{DefaultClause}
		\code{default} \code{;} \\
\end{Syntax}

\begin{Checking}
	\DerivationRule{
		\begin{trgather}
		\SynthExpr{\ContextVarA}{\ExprVarE}{\TypeVarT}{\ContextVarB} \\
		\CheckCase{\ContextVarB}{\bar{\MetaVar{C}}}{\TypeVarT} \\
		\end{trgather}	
	}{
		\CheckStmt{\ContextVarA}{\code{switch(} \ExprVarE \code{) \{} \bar{\MetaVar{C}} \code{\}}}{\ContextVarA}
	}
\end{Checking}

\begin{Description}
A \code{switch} statement is checked by first checking the expression, and then checking each of the alternatives against the type of that expression.
\end{Description}

\begin{Checking}
	\DerivationRule{
		\begin{trgather}
		\CheckCaseLabel{\ContextVarA}{\overline{label}}{\TypeVarT} \\
		\CheckStmts{\ContextVarA}{stmts}{\ContextVarB} \\
		\end{trgather}	
	}{
		\CheckCase{\ContextVarA}{\overline{label}\ {stmts}}{\TypeVarT} \\
	}\vspace{1em}

	\DerivationRule{
	}{
		\CheckCaseLabel{\ContextVarA}{\code{default:}}{\TypeVarT} \\
	}\vspace{1em}

	\DerivationRule{
		\CheckExpr{\ContextVarA}{expr}{\TypeVarT}{\ContextVarB}
	}{
		\CheckCaseLabel{\ContextVarA}{\code{case}\ expr\ \code{:}}{\TypeVarT} \\
	}\vspace{1em}

\end{Checking}

\begin{Description}
A \code{case} clause is valid if its expression checks against the type of the control expressio nof the \code{switch} statement.
\end{Description}

A \code{switch} statement may have at most one \code{default} clause.

If the type of the controlling expression of a \code{switch} statement is a built-in integer type, then:

\begin{itemize}
\item The expression of each \code{case} clause must be a compile-time constant expression.
\item The constant value of the expression for each \code{case} clause must not be equal to that of any other \code{case} clause in the same \code{switch}.
\end{itemize}

Each alternative of a \code{switch} statement must exit the \code{switch} statement via a `break` or other control transfer statement.
"Fall-through" from one switch case clause to another is not allowed.

\begin{Description}
Semantically, a \code{switch} statement is equivalent to an ``\code{if} cascade'' that compares the value of the conditional expression against each \code{case} clause,
\end{Description}

Loop Statements {#stmt.loop}
---------------

### For Statement ### {#stmt.for}

\begin{Syntax}
	\SynDefine{ForStatement} \\
		\code{for} \code{(} \\
		\SynVar[initial]{Statement}\SynOpt \code{;} \\
		\SynVar[condition]{Expression}\SynOpt \code{;} \\
		\SynVar[sideEffect]{Expression}\SynOpt \code{)} \\
		\SynVar[body]{Statement}
\end{Syntax}


\begin{Checking}
	\DerivationRule{
		\begin{trgather}
		\CheckStmt{\ContextVarA}{init}{\ContextVarB} \\
		\CheckExpr{\ContextVarB}{cond}{\code{Bool}}{\ContextVarC} \\
		\SynthExpr{\ContextVarC}{iter}{T}{\ContextVarD} \\
		\CheckStmt{\ContextVarD}{body}{\ContextVarE} \\
		\end{trgather}	
	}{
		\CheckStmt{\ContextVarA}{\code{for(}\ init \code{;}\ cond \code{;}\ iter \code{)} body}{\ContextVarA} \\
	}
\end{Checking}

Issue: The checking judgements above aren't complete because they don't handle the case where \emph{cond} is absent, in which case it should be treated like it was \code{true}.

### While Statement ### {#stmt.while}


\begin{Syntax}
	\SynDefine{WhileStatement} \\
		\code{while} \code{(}
		\SynVar[condition]{Expression}\SynOpt \code{)}
		\SynVar[body]{Statement}
\end{Syntax}


\begin{Checking}
	\DerivationRule{
		\begin{trgather}
		\CheckExpr{\ContextVarA}{cond}{\code{Bool}}{\ContextVarB} \\
		\CheckStmt{\ContextVarB}{body}{\ContextVarC} \\
		\end{trgather}	
	}{
		\CheckStmt{\ContextVarA}{\code{while(}\ cond \code{)} body}{\ContextVarA} 
	}
\end{Checking}

### Do-While Statement ### {#stmt.do-while}

A <dfn>do-while statement</dfn> uses the following form:

\begin{Syntax}
	\SynDefine{DoWhileStatement} \\
		\code{do} \SynVar[body]{Statement} \\
		\code{while} \code{(} \SynVar[condition]{Expression}\SynOpt \code{)} \code{;}		
\end{Syntax}


\begin{Checking}
	\DerivationRule{
		\begin{trgather}
			\CheckStmt{\ContextVarA}{body}{\ContextVarB} \\
			\CheckExpr{\ContextVarA}{cond}{\code{Bool}}{\ContextVarC} \\
		\end{trgather}	
	}{
		\CheckStmt{\ContextVarA}{\code{do} body \code{while(}\ cond \code{);}}{\ContextVarA} 
	}
\end{Checking}

Control Transfer Statements {#stmt.control}
---------------------------

### Break Statement ### {#stmt.break}

\begin{Syntax}
	\SynDefine{BreakStatement}
		`break` \SynVar[label]{Identifier}\SynOpt \code{;} \\
\end{Syntax}

\begin{Description}
A `break` statement without a \SynRef{label} transfers control to after the end of the closest lexically enclosing switch statement or loop statement.

A `break` statement with a \SynRef{label} transfers control to after the end of the lexically enclosing switch or loop statement labeled with a matching \SynRef{label}.
\end{Description}

\begin{Checking}
	\DerivationRule{
		\ContextLookup{\ContextVarA}{\BreakLabel}{\textunderscore}
	}{
		\CheckStmt{\ContextVarA}{`break`\code{;}}{\ContextVarA} 
	} \\

	\DerivationRule{
		\ContextContains{\ContextVarA}{\BreakLabel: label}
	}{
		\CheckStmt{\ContextVarA}{`break` label\code{;}}{\ContextVarA} 
	}
\end{Checking}

<div class=issue>
Issue: The checking rules for `break`-able statements should add a suitable item to the context used for checking their body statements, which will be matched by the rules above.

We also need to define the context-containment rule that is being used to look up the `break` item in the context.
</div>

### Continue Statement ### {#stmt.continue}

\begin{Syntax}
	\SynDefine{ContinueStatement}
		\code{continue} \SynVar[label]{Identifier}\SynOpt \code{;} \\
\end{Syntax}

\begin{Description}
A \code{continue} statement transfers control to the start of the next iteration of a loop statement.
In a for statement with a side effect expression, the side effect expression is evaluated when \code{continue} is used:
\end{Description}

\begin{Checking}
	\DerivationRule{
		\ContextLookup{\ContextVarA}{\ContinueLabel}{\textunderscore}
	}{
		\CheckStmt{\ContextVarA}{\code{continue}\code{;}}{\ContextVarA} 
	} \\

	\DerivationRule{
		\ContextContains{\ContextVarA}{\ContinueLabel: label}
	}{
		\CheckStmt{\ContextVarA}{\code{continue} label\code{;}}{\ContextVarA} 
	}
\end{Checking}

### Return Statement ### {#stmt.continue}

\begin{Description}
	A \code{return} statement transfers control out of the current function.
\end{Description}
	
\begin{Syntax}
	\SynDefine{ReturnStatement}
		\code{return} \SynRef{Expression}\SynOpt \code{;} \\
\end{Syntax}

\begin{Checking}
	\DerivationRule{
		\begin{trgather}
		\ContextLookup{\ContextVarA}{\ResultType}{type} \\
		\CheckExpr{\ContextVarA}{expr}{type}{\ContextVarB} \\
		\end{trgather}
	}{
		\CheckStmt{\ContextVarA}{\code{return} expr \code{;}}{\ContextVarB} 
	}
\end{Checking}

\begin{Checking}
	\DerivationRule{
		\CheckStmt{\ContextVarA}{\code{return Unit();}}{\ContextVarB} 
	}{
		\CheckStmt{\ContextVarA}{\code{return}\code{;}}{\ContextVarB} 
	}
\end{Checking}

\begin{Description}
	A \code{return} statement without an expression is equivalent to a \code{return} of a value of type \code{Unit}.
\end{Description}

### Discard Statement ### {#stmt.discard}

\begin{Syntax}
	\SynDefine{DiscardStatement}
		\code{discard} \code{;} \\
\end{Syntax}

\begin{Description}
A \code{discard} statement can only be used in the context of a fragment shader, in which case it causes the current invocation to terminate and the graphics system to discard the corresponding fragment so that it does not get combined with the framebuffer pixel at its coordinates.

Operations with side effects that were executed by the invocation before a \code{discard} will still be performed and their results will become visible according to the rules of the platform.	
\end{Description}

\begin{Checking}
	\DerivationRule{
	}{
		\CheckStmt{\ContextVarA}{\code{discard;}}{\RequireCap{fragment},\ContextVarB} 
	}
\end{Checking}

\begin{Incomplete}
The intent of the above rule is that checking a \code{discard} statement will add the \code{fragment} capability to the context, so that it can be checked against the capabilities of the surrounding function/context.
However, the way the other statement rules handle the context, they do not allow for anything in the context to flow upward/outward in that fashion.
It may be simplest to have the process of collecting the capabilities required by a function body be a different judgement than the type checking rules.
\end{Incomplete}
	