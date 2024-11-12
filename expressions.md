Expressions {#expr}
===========

Expressions are terms that can be \SpecDef{evaluated} to produce values.
This section provides a list of the kinds of expressions that may be used in a Slang program.

In general, the order of evaluation of a Slang expression proceeds from left to right.
Where specific expressions do not follow this order of evaluation, it will be noted.

Some expressions can yield \SpecDef{l-values}, which allows them to be used on the left-hand-side of assignment, or as arguments for `out` or `in out` parameters.

Literal Expressions {#expr.lit}
-------------------

Literal expressions are never l-values.

### Integer Literal Expressions ### {#expr.lit.int}

An \SpecDef{integer literal expression} consists of a single \SynRef{IntegerLiteral} token.

\begin{Checking}
	\DerivationRule{
		\begin{trgather}
        \CheckConforms{\ContextVarA,\alpha}{\alpha}{\code{IFromIntegerLiteral}}{\ContextVarB}
		\end{trgather}	
	}{
		\SynthExpr{\ContextVarA}{i}{\alpha}{\ContextVarB}
	}
\end{Checking}

\begin{Description}
An unsuffixed integer literal synthesizes a type that is a fresh type variable $\alpha$, constrained to conform to \code{IFromIntegerLiteral}.
\end{Description}

\begin{Incomplete}
We need a description of how suffixed integer literals have their type derived from their suffix.
\end{Incomplete}

### Floating-Point Literal Expressions ### {#expr.lit.float}

A \SpecDef{floating-point literal expression} consists of a single \SynRef{FloatingPointLiteral} token.

\begin{Checking}
	\DerivationRule{
		\begin{trgather}
        \CheckConforms{\ContextVarA,\alpha}{\alpha}{\code{IFromFloatingPointLiteral}}{\ContextVarB}
		\end{trgather}	
	}{
		\SynthExpr{\ContextVarA}{f}{\alpha}{\ContextVarB}
	}
\end{Checking}

\begin{Description}
An unsuffixed floating-point literal synthesizes a type that is a fresh type variable $\alpha$, constrained to conform to \code{IFromFloatingPointLiteral}.
\end{Description}

\begin{Incomplete}
We need a description of how suffixed floating-point literals have their type derived from their suffix.
\end{Incomplete}
    
### Boolean Literal Expressions ### {#expr.lit.bool}

\begin{Description}
    Boolean literal expressions use the keywords `true` and `false`.
\end{Description}
    
\begin{Syntax}
	\SynDefine{BooleanLiteralExpression}
        \code{true} \SynOr \code{false}
\end{Syntax}

\begin{Checking}
	\DerivationRule{
	}{
		\SynthExpr{\ContextVarA}{\code{true}}{\code{Bool}}{\ContextVarA}
	}\\
	\DerivationRule{
	}{
		\SynthExpr{\ContextVarA}{\code{false}}{\code{Bool}}{\ContextVarA}
	}\\
\end{Checking}


### String Literal Expressions ### {#expr.lit.string}

\begin{Description}
A string literal expressions consists of one or more string literal tokens in a row.
\end{Description}

\begin{Syntax}
	\SynDefine{StringLiteralExpression}
        \SynRef{StirngLiteral}\SynPlus
\end{Syntax}

\begin{Checking}
	\DerivationRule{
	}{
		\SynthExpr{\ContextVarA}{\overline{s}}{\code{String}}{\ContextVarA}
	}\\
\end{Checking}

Identifier Expressions {#expr.ident}
----------------------

\begin{Syntax}
	\SynDefine{IdentifierExpression} \\
        \SynRef{Identifier} \\
        \SynOr \code{operator} \SynRef{Operator} \\
\end{Syntax}

\begin{Checking}
	\DerivationRule{
        \SynthLookup{\ContextVarA}{name}{type}
	}{
		\SynthExpr{\ContextVarA}{name}{type}{\ContextVarA}
	}\vspace{1em}

	\DerivationRule{
        \CheckLookup{\ContextVarA}{name}{type}{\ContextVarB}
	}{
		\CheckExpr{\ContextVarA}{name}{type}{\ContextVarB}
	}\\
\end{Checking}

\begin{Incomplete}
This presentation delegates the actual semantics of identifier expressions to the \textsc{Lookup} judgement, which needs to be explained in detail.
\end{Incomplete}

%\begin{verbatim}
%When evaluated, this expression looks up `someName` in the environment of the %expression and yields the value of a declaration with a matching name.
%
%An identifier expression is an l-value if the declaration it refers to is mutable.
%
% ### Overloading ### {overload}
%
%It is possible for an identifier expression to be _overloaded_, such that it %refers to one or more candidate declarations with the same name.
%If the expression appears in a context where the correct declaration to use can be %disambiguated, then that declaration is used as the result of  the name %expression; otherwise use of an overloaded name is an error at the use site.
%
% ### Implicit Lookup ### {lookup.implicit}
%
%It is possible for a name expression to refer to nested declarations in two ways:
%
%* In the body of a method, a reference to `someName` may resolve to `this.%someName`, using the implicit `this` parameter of the method
%
%* When a global-scope `cbuffer` or `tbuffer` declaration is used, `someName` may %refer to a field declared inside the `cbuffer` or `tbuffer`
%\end{verbatim}

Member Expression {#expr.member}
-----------------

\begin{Syntax}
	\SynDefine{MemberExpression}
        \SynRef{Expression} \code{.} \SynRef{Identifier} \\
\end{Syntax}

\begin{Incomplete}
The semantics of member lookup are similar in complexity to identifier lookup (and indeed the two share a lot of the same machinery).
In addition to all the complications of ordinary name lookup (including overloading), member expressions also need to deal with:
\begin{itemize}
\item Implicit dereference of pointer-like types.
\item Swizzles (vector or matrix).
\item Static vs. instance members.
\end{itemize}

In both synthesis and checking modes, the base expression should first synthesize a type, and then lookup of the member should be based on that type.
\end{Incomplete}

%\begin{verbatim}
%When `base` is a structure type, this expression looks up the field or other %member named by `m`.
%Just as for an identifier expression, the result of a member expression may be %overloaded, and might be disambiguated based on how it is used.
%
%A member expression is an l-value if the base expression is an l-value and the %member it refers to is mutable.
%
% ### Implicit Dereference ### {dereference.implicit}
%
%If the base expression of a member reference is a _pointer-like type_ such as %`ConstantBuffer<T>`, then a member reference expression will implicitly %dereference the base expression to refer to the pointed-to value (e.g., in the %case of `ConstantBuffer<T>` this is the buffer contents of type `T`).
%
% ### Vector Swizzles ### {swizzle.vector}
%
%When the base expression of a member expression is of a vector type `vector<T,N>` %then a member expression is a _vector swizzle expression_.
%The member name must conform to these constraints:
%
%* The member name must comprise between one and four ASCII characters
%* The characters must be come either from the set (`x`, `y`, `z`, `w`) or (`r`, %`g`, `b`, `a`), corresponding to element indics of (0, 1, 2, 3)
%* The element index corresponding to each character must be less than `N`
%
%If the member name of a swizzle consists of a single character, then the %expression has type `T` and is equivalent to a subscript expression with the %corresponding element index.
%
%If the member name of a swizzle consists of `M` characters, then the result is a %`vector<T,M>` built from the elements of the base vector with the corresponding %indices.
%
%A vector swizzle expression is an l-value if the base expression was an l-value %and the list of indices corresponding to the characeters of the member name %contains no duplicates.
%
% ### Matrix Swizzles ### {swizzle.matrix}
%
%> Note: The Slang implementation currently doesn't support matrix swizzles.
%
% ### Static Member Expressions ### {member.static}
%
%When the base expression of a member expression is a type instead of a value, the %result is a _static member expression_.
%A static member expression can refer to a static field or static method of a %structure type.
%A static member expression can also refer to a case of an enumeration type.
%
%A static member expression (but not a member expression in general) may use the %token `::` instead of `.` to separate the base and member name:
%
%```hlsl
%// These are equivalent
%Color.Red
%Color::Red
%```
%\end{verbatim}

This Expression {#expr.this}
---------------

\begin{Syntax}
	\SynDefine{ThisExpression} 
        \code{this} \\
\end{Syntax}

\begin{Checking}
	\DerivationRule{
	}{
		\SynthExpr{\ContextVarA}{\code{this}}{\code{This}}{\ContextVarB}
	}	
\end{Checking}


\begin{Description}
In contexts where a \kw{this} expression is valid, it refers to the implicit instance of the closest enclosing type declaration.
The type of a \kw{this} expression is always \code{This}.
\end{Description}

\begin{Incomplete}
This section needs to deal with the rules for when \kw{this} is mutable vs. immutable.
\end{Incomplete}

Parenthesized Expression {#expr.paren}
-------------

\begin{Description}
An expression wrapped in parentheses \code{()} is a \SpecDef{parenthesized expression} and evaluates to the same value as the wrapped expression.
\end{Description}

\begin{Syntax}
	\SynDefine{ParenthesizedExpression} 
        \code{(} \SynRef{Expression} \code{)} \\
\end{Syntax}

\begin{Checking}
	\DerivationRule{
		\CheckExpr{\ContextVarA}{expr}{type}{\ContextVarB}
	}{
		\CheckExpr{\ContextVarA}{\code{(} expr \code{)}}{type}{\ContextVarB}
	}\vspace{1em}

	\DerivationRule{
		\SynthExpr{\ContextVarA}{expr}{type}{\ContextVarB}
	}{
		\SynthExpr{\ContextVarA}{\code{(} expr \code{)}}{type}{\ContextVarB}
	}	
\end{Checking}


Call Expression {#expr.call}
---------------

\begin{Syntax}
	\SynDefine{CallExpression} \\
        \SynRef{Expression} \code{(} (\SynRef{Argument} \code{,})\SynStar \code{)} \\

    \SynDefine{Argument} \\
        \SynRef{Expression} \\
        \SynOr \SynRef{NamedArgument} \\

    \SynDefine{NamedArgument} \\
        \SynRef{Identifier} \code{:} \SynRef{Expression}
\end{Syntax}

\begin{Checking}
	\DerivationRule{
        \CheckCall{\ContextVarA}{f}{\overline{args}}{type}{\ContextVarB}
	}{
		\CheckExpr{\ContextVarA}{f \code{(} \overline{args} \code{)}}{type}{\ContextVarB}
	}\vspace{1em}

	\DerivationRule{
        \SynthCall{\ContextVarA}{f}{\overline{args}}{type}{\ContextVarB}
	}{
		\SynthExpr{\ContextVarA}{f \code{(} \overline{args} \code{)}}{type}{\ContextVarB}
	}	
\end{Checking}

\begin{Incomplete}
These rules just kick the can down the road and say that synthesis/checking for call expressions bottlenecks through the \textsc{Call} judgements.
\end{Incomplete}

%\begin{verbatim}
%A _call expression_ consists of a base expression and a list of argument %expressions, separated by commas and enclosed in `()`:
%
%```hlsl
%myFunction( 1.0f, 20 )
%```
%
%When the base expression (e.g., `myFunction`) is overloaded, a call expression can %disambiguate the overloaded expression based on the number and type or arguments %present.
%
%The base expression of a call may be a member reference expression:
%
%```hlsl
%myObject.myFunc( 1.0f )
%```
%
%In this case the base expression of the member reference (e.g., `myObject` in this %case) is used as the argument for the implicit `this` parameter of the callee.
%
% ### Mutability ### {#expr.call.mutable}
%
%If a `[mutating]` instance is being called, the argument for the implicit `this` %parameter must be an l-value.
%
%The argument expressions corresponding to any `out` or `in out` parameters of the %callee must be l-values.
%\end{verbatim}

Subscript Expression {#expr.subscript}
--------------------

\begin{Syntax}
	\SynDefine{SubscriptExpression} \\
		\SynRef{Expression} \code{[} (\SynRef{Argument} \code{,})\SynStar \code{]}
\end{Syntax}

\begin{Incomplete}
To a first approximation, a subscript expression like \code{base[a0, a1]} is equivalent to something like \code{base.subscript(a0, a1)}.
That is, we look up the \kw{subscript} members of the \code{base} expression, and then check a call to the result of lookup (which might be overloaded).

Unlike simple function calls, a subscript expression can result in an l-value, based on what accessors the \kw{subscript} declaration that is selected by overload resolution has.
\end{Incomplete}

%A subscript expression invokes one of the subscript declarations in the type of %the base expression. Which subscript declaration is invoked is resolved based on %the number and types of the arguments.
%
%A subscript expression is an l-value if the base expression is an l-value and if %the subscript declaration it refers to has a setter or by-reference accessor.
%
%Subscripts may be formed on the built-in vector, matrix, and array types.

Initializer List Expression {#expr.init-list}
---------------------------

\begin{Syntax}
	\SynDefine{InitializerListExpression} \\
		\code{\{} (\SynRef{Argument} \code{,})\SynStar \code{\}}
\end{Syntax}

\begin{Description}
An initializer-list expression may only appear in contexts where it will be checked against an expected type.
There are no synthesis rules for initializer-list expressions.

An initializer-list expression is equivalent to constructing an instance of the expected type using the arguments.
\end{Description}

\begin{Checking}
	\DerivationRule{
        \CheckConstruct{\ContextVarA}{type}{\overline{args}}{\ContextVarB} \\
	}{
		\CheckExpr{\ContextVarA}{\code{\{} \overline{args} \code{\}}}{type}{\ContextVarB}
	}
\end{Checking}

Cast Expression {#expr.cast}
---------------

\begin{Syntax}
	\SynDefine{CastExpression} \\
		\code{(} \SynRef{TypeExpression} \code{)} \SynRef{Expression}
\end{Syntax}

\begin{Description}
A \SpecDef{cast expression} attempts to coerce an expression to a desired type.
\end{Description}

\begin{Checking}
	\DerivationRule{
        \CheckExpr{\ContextVarA}{expr}{type}{\ContextVarB}
	}{
		\SynthExpr{\ContextVarA}{\code{(} type \code{)} expr}{type}{\ContextVarB}
	}
\end{Checking}

\begin{Description}
A cast expression always synthesizes a type, since the type it produces is manifest in the expression.
\end{Description}

\begin{Incomplete}
The above rule treats a cast exprssion as something closer to a type ascription expression, where it expects the underlying expression to be of the desired type, or something implicitly convertible to it.

In contrast, we want a cast expression to be able to invoke \emph{explicit} conversions as well, which are currently not something the formalism encodes.
\end{Incomplete}

\begin{Legacy}
### Legacy: Compatibility Feature ### {#expr.cast.compatiblity}

As a compatiblity feature for older code, Slang supports using a cast where the base expression is an integer literal zero and the target type is a user-defined structure type:

```
MyStruct s = (MyStruct) 0;    
```

The semantics of such a cast are equivalent to initialization from an empty initializer list:

```
MyStruct s = {};
```

\end{Legacy}

Assignment Expression {#expr.assign}
----------

\begin{Syntax}
	\SynDefine{AssignmentExpression} \\
        \SynVar[destination]{Expression} \code{=} \SynVar[source]{Expression}
\end{Syntax}

\begin{Checking}
	\DerivationRule{
        \begin{trgather}
        \SynthExpr{\ContextVarA}{dst}{\code{out} type}{\ContextVarB} \\
        \CheckExpr{\ContextVarB}{src}{type}{\ContextVarB} \\
        \end{trgather}
	}{
		\SynthExpr{\ContextVarA}{dst \code{=} src}{\code{out} type}{\ContextVarB}
	}

	\DerivationRule{
        \begin{trgather}
        \CheckExpr{\ContextVarA}{dst}{\code{out} type}{\ContextVarB} \\
        \CheckExpr{\ContextVarB}{src}{type}{\ContextVarB} \\
        \end{trgather}
	}{
		\CheckExpr{\ContextVarA}{dst \code{=} src}{type}{\ContextVarB}
	}
\end{Checking}

\begin{Description}
Assignment expressions support both synthesis and checking judgements.

In each case, the \SynRef{destination} expression is validated first, and then the \SynRef{source} expression.
\end{Description}

\begin{Incomplete}
The above rules pretend that we can write \code{out} before a type to indicate that we mean an l-value of that type.
We will need to expand the formalism to include \emph{qualified} types.
\end{Incomplete}

Operator Expressions {#expr.op}
--------------------

### Prefix Operator Expressions ### {#expr.op.prefix}

\begin{Syntax}
	\SynDefine{PrefixOperatorExpression} \\
        \SynRef{PrefixOperator} \SynRef{Expression}

    \SynDefine{PrefixOperator} \\
        \code{+} \SynComment{identity} \\
        \SynOr \code{-} \SynComment{arithmetic negation} \\
        \SynOr \code{\~} \SynComment{bit\-wise Boolean negation} \\
        \SynOr \code{!} \SynComment{Boolean negation} \\
        \SynOr \code{++} \SynComment{increment in place} \\
        \SynOr \code{--} \SynComment{decrement in place} \\
\end{Syntax}

\begin{Checking}
	\DerivationRule{
        \begin{trgather}
        \SynthCall{\ContextVarA}{\code{operator}op}{expr}{type}{\ContextVarB} \\
        \end{trgather}
	}{
		\SynthExpr{\ContextVarA}{op\ expr}{type}{\ContextVarB}
	}

	\DerivationRule{
        \begin{trgather}
            \CheckCall{\ContextVarA}{\code{operator}op}{expr}{type}{\ContextVarB} \\
        \end{trgather}
	}{
		\CheckExpr{\ContextVarA}{op\ expr}{type}{\ContextVarB}
	}
\end{Checking}

\begin{Description}
A prefix operator expression is semantically equivalent to a call expression to a function matching the operator, except that lookup for the function name only considers function declarations marked with the \kw{prefix} modifier.
\end{Description}

\begin{Incomplete}
The notation here needs a way to express the restrictions on lookup that are used for prefix/postfix operator names.
\end{Incomplete}

### Postfix Operator Expressions ### {#expr.op.postfix}

\begin{Syntax}
	\SynDefine{PostfixOperatorExprssion} \\
        \SynRef{Expression} \SynRef{PostfixOperator}

    \SynDefine{PostfixOperator} \\
        \SynOr \code{++} \SynComment{increment in place} \\
        \SynOr \code{--} \SynComment{decrement in place} \\
\end{Syntax}

\begin{Checking}
	\DerivationRule{
        \begin{trgather}
        \SynthCall{\ContextVarA}{\code{operator}op}{expr}{type}{\ContextVarB} \\
        \end{trgather}
	}{
		\SynthExpr{\ContextVarA}{expr op}{type}{\ContextVarB}
	}

	\DerivationRule{
        \begin{trgather}
            \CheckCall{\ContextVarA}{\code{operator}op}{expr}{type}{\ContextVarB} \\
        \end{trgather}
	}{
		\CheckExpr{\ContextVarA}{expr op}{type}{\ContextVarB}
	}
\end{Checking}

\begin{Description}
Postfix operator expressions have similar rules to prefix operator expressions, except that in this case the lookup of the operator name will only consider declarations marked with the \kw{postfix} modifier.
\end{Description}

### Infix Operator Expressions ### {#expr.op.infix}

\begin{Syntax}
	\SynDefine{InfixOperatorExpression} \\
        \SynRef{Expression} \SynRef{InfixOperator} \SynRef{Expression}

    \SynDefine{InfixOperator} \\
        \SynOr \code{*} \SynComment{multiplication} \\
        \SynOr \code{/} \SynComment{division} \\
        \SynOr \code{\%} \SynComment{remainder of division} \\
        \SynOr \code{+} \SynComment{addition} \\
        \SynOr \code{-} \SynComment{subtraction} \\
        \SynOr \code{<<} \SynComment{left shift} \\
        \SynOr \code{>>} \SynComment{right shift} \\
        \SynOr \code{<} \SynComment{less than} \\
        \SynOr \code{>} \SynComment{greater than} \\
        \SynOr \code{<=} \SynComment{less than or equal to} \\
        \SynOr \code{>=} \SynComment{greater than or equal to} \\
        \SynOr \code{==} \SynComment{equal to} \\
        \SynOr \code{!=} \SynComment{not equal to} \\
        \SynOr \code{&} \SynComment{bitwise and} \\
        \SynOr \code{^} \SynComment{bitwise exclusive or} \\
        \SynOr \code{|} \SynComment{bitwise or} \\
        \SynOr \code{&&} \SynComment{logical and} \\
        \SynOr \code{||} \SynComment{logical or} \\
        \SynOr \code{+=}		\SynComment{compound add/assign} \\
        \SynOr \code{-=}    	\SynComment{compound subtract/assign} \\
        \SynOr \code{*=}    	\SynComment{compound multiply/assign} \\
        \SynOr \code{/=}    	\SynComment{compound divide/assign} \\
        \SynOr \code{\%=}    	\SynComment{compound remainder/assign} \\
        \SynOr \code{<<=}   	\SynComment{compound left shift/assign} \\
        \SynOr \code{>>=}   	\SynComment{compound right shift/assign} \\
        \SynOr \code{&=}    	\SynComment{compound bitwise and/assign} \\
        \SynOr \code{\|=}   	\SynComment{compound bitwise or/assign} \\
        \SynOr \code{^=}    	\SynComment{compound bitwise xor/assign} \\
%        \SynOr \code{=}    	\SynComment{assignment} \\
%        \SynOr \code{,}		\SynComment{sequence} \\

\end{Syntax}


%TODO: need to get the precedence groups from this table into the grammar rules.
%
%| Operator 	| Kind        | Description |
%|-----------|-------------|-------------|
%| `*`		| Multiplicative 	| multiplication |
%| `/`		| Multiplicative 	| division |
%| `%`		| Multiplicative 	| remainder of division |
%| `+`		| Additive 			| addition |
%| `-`		| Additive 			| subtraction |
%| `<<`		| Shift 			| left shift |
%| `>>`		| Shift 			| right shift |
%| `<` 		| Relational 		| less than |
%| `>`		| Relational 		| greater than |
%| `<=`		| Relational 		| less than or equal to |
%| `>=`		| Relational 		| greater than or equal to |
%| `==`		| Equality 			| equal to |
%| `!=`		| Equality 			| not equal to |
%| `&`		| BitAnd 			| bitwise and |
%| `^`		| BitXor			| bitwise exclusive or |
%| `\|`		| BitOr 			| bitwise or |
%| `&&`		| And 				| logical and |
%| `\|\|`	| Or 				| logical or |
%| `+=`		| Assignment  		| compound add/assign |
%| `-=`      | Assignment  		| compound subtract/assign |
%| `*=`      | Assignment  		| compound multiply/assign |
%| `/=`      | Assignment  		| compound divide/assign |
%| `%=`      | Assignment  		| compound remainder/assign |
%| `<<=`     | Assignment  		| compound left shift/assign |
%| `>>=`     | Assignment  		| compound right shift/assign |
%| `&=`      | Assignment  		| compound bitwise and/assign |
%| `\|=`     | Assignment  		| compound bitwise or/assign |
%| `^=`      | Assignment  		| compound bitwise xor/assign |
%| `=`       | Assignment  		| assignment |
%| `,`		| Sequencing  		| sequence |

\begin{Checking}
	\DerivationRule{
        \begin{trgather}
        \SynthCall{\ContextVarA}{\code{operator}op}{left right}{type}{\ContextVarB} \\
        \end{trgather}
	}{
		\SynthExpr{\ContextVarA}{left op right}{type}{\ContextVarB}
	}

	\DerivationRule{
        \begin{trgather}
            \CheckCall{\ContextVarA}{\code{operator}op}{left right}{type}{\ContextVarB} \\
        \end{trgather}
	}{
		\CheckExpr{\ContextVarA}{left op right}{type}{\ContextVarB}
	}
\end{Checking}

With the exception of the assignment operator (`=`), an infix operator expression like `left + right` is equivalent to a call expression to a function of the matching name `operator+(left, right)`.

### Conditional Expression ### {#expr.op.cond}

\begin{Syntax}
	\SynDefine{ConditionalExpression} \\
        \SynVar[condition]{Expression} \code{?} \SynVar[then]{Expression} \code{:} \SynVar[else]{Expression}
\end{Syntax}

\begin{Checking}
	\DerivationRule{
        \begin{trgather}
        \CheckExpr{\ContextVarA}{cond}{\code{Bool}}{\ContextVarB} \\
        \CheckExpr{\ContextVarB,\code{type} \alpha}{t}{type}{\ContextVarC} \\
        \CheckExpr{\ContextVarC,\code{type} \alpha}{e}{type}{\ContextVarD} \\
        \end{trgather}
	}{
		\CheckExpr{\ContextVarA}{cond \code{?} t \code{:} e}{type}{\ContextVarD}
	}\vspace{1em}
\end{Checking}

\begin{Description}
In both checking and synthesis judgements, the \SynRef{condition} of a conditional expression is checked against the \code{Bool} type.

In the checking judgement, the \SynRef{then} and \SynRef{else} expressions are both checked against the expected type.
\end{Description}

\begin{Checking}
	\DerivationRule{
        \begin{trgather}
		\CheckExpr{\ContextVarA, \code{type} \alpha}{cond \code{?} t \code{:} e}{\alpha}{\ContextVarB} \\
        \end{trgather}
	}{
		\SynthExpr{\ContextVarA}{cond \code{?} t \code{:} e}{\alpha}{\ContextVarB}
	}
\end{Checking}

\begin{Description}
In the synthesis direction, a fresh type variable $\alpha$ is introduced, and the expression is checked against that type.
The output context \ContextVarB of the checking step may include constraints on $\alpha$ introduced by checking the \SynRef{then} and \SynRef{else} expressions.
\end{Description}
