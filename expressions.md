Expressions {#expr}
===========

Expressions are terms that can be <dfn>evaluated</dfn> to produce values.
This section provides a list of the kinds of expressions that may be used in a Slang program.

In general, the order of evaluation of a Slang expression proceeds from left to right.
Where specific expressions do not follow this order of evaluation, it will be noted.

Some expressions can yield <dfn>l-values</dfn>, which allows them to be used on the left-hand-side of assignment, or as arguments for `out` or `in out` parameters.

Literal Expressions {#expr.lit}
-------------------

Literal expressions are never l-values.

### Integer Literal Expressions ### {#expr.lit.int}

An <dfn>integer literal expression</dfn> consists of a single IntegerLiteral token.

```.checking
	\DerivationRule{
		\begin{trgather}
        \CheckConforms{\ContextVarA,\alpha}{\alpha}{\code{IFromIntegerLiteral}}{\ContextVarB}
		\end{trgather}	
	}{
		\SynthExpr{\ContextVarA}{i}{\alpha}{\ContextVarB}
	}
```

Note:
An unsuffixed integer literal synthesizes a type that is a fresh type variable $\alpha$, constrained to conform to \code{IFromIntegerLiteral}.


Issue: We need a description of how suffixed integer literals have their type derived from their suffix.

### Floating-Point Literal Expressions ### {#expr.lit.float}

A <dfn>floating-point literal expression</dfn> consists of a single FloatingPointLiteral token.

```.checking
	\DerivationRule{
		\begin{trgather}
        \CheckConforms{\ContextVarA,\alpha}{\alpha}{\code{IFromFloatingPointLiteral}}{\ContextVarB}
		\end{trgather}	
	}{
		\SynthExpr{\ContextVarA}{f}{\alpha}{\ContextVarB}
	}
```

Note:
An unsuffixed floating-point literal synthesizes a type that is a fresh type variable $\alpha$, constrained to conform to \code{IFromFloatingPointLiteral}.


Issue: We need a description of how suffixed floating-point literals have their type derived from their suffix.
    
### Boolean Literal Expressions ### {#expr.lit.bool}

Note:
    Boolean literal expressions use the keywords `true` and `false`.

    
```.syntax
	BooleanLiteralExpression}
        `true` | `false`
```

```.checking
	\DerivationRule{
	}{
		\SynthExpr{\ContextVarA}{`true`}{`Bool`}{\ContextVarA}
	}\\
	\DerivationRule{
	}{
		\SynthExpr{\ContextVarA}{`false`}{`Bool`}{\ContextVarA}
	}\\
```


### String Literal Expressions ### {#expr.lit.string}

Note:
A string literal expressions consists of one or more string literal tokens in a row.


```.syntax
	StringLiteralExpression}
        StringLiteral+
```

```.checking
	\DerivationRule{
	}{
		\SynthExpr{\ContextVarA}{\overline{s}}{\code{String}}{\ContextVarA}
	}\\
```

Identifier Expressions {#expr.ident}
----------------------

```.syntax
	IdentifierExpression
        Identifier
        | \code{operator} Operator
```

```.checking
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
```

Issue: This presentation delegates the actual semantics of identifier expressions to the \textsc{Lookup} judgement, which needs to be explained in detail.

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

```.syntax
	MemberExpression}
        Expression `.` Identifier
```

<div class=issue>
The semantics of member lookup are similar in complexity to identifier lookup (and indeed the two share a lot of the same machinery).
In addition to all the complications of ordinary name lookup (including overloading), member expressions also need to deal with:

* Implicit dereference of pointer-like types.
* Swizzles (vector or matrix).
* Static vs. instance members.
</div>

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

```.syntax
	ThisExpression} 
        \code{this
```

```.checking
	\DerivationRule{
	}{
		\SynthExpr{\ContextVarA}{\code{this}}{\code{This}}{\ContextVarB}
	}	
```


Note:
In contexts where a `this` expression is valid, it refers to the implicit instance of the closest enclosing type declaration.
The type of a `this` expression is always \code{This}.


Issue: This section needs to deal with the rules for when `this` is mutable vs. immutable.

Parenthesized Expression {#expr.paren}
-------------

Note:
An expression wrapped in parentheses \code{()} is a <dfn>parenthesized expression</dfn> and evaluates to the same value as the wrapped expression.


```.syntax
	ParenthesizedExpression} 
        `(` Expression \code{)
```

```.checking
	\DerivationRule{
		\CheckExpr{\ContextVarA}{expr}{type}{\ContextVarB}
	}{
		\CheckExpr{\ContextVarA}{`(` expr `)`}{type}{\ContextVarB}
	}\vspace{1em}

	\DerivationRule{
		\SynthExpr{\ContextVarA}{expr}{type}{\ContextVarB}
	}{
		\SynthExpr{\ContextVarA}{`(` expr `)`}{type}{\ContextVarB}
	}	
```


Call Expression {#expr.call}
---------------

```.syntax
	CallExpression
        Expression `(` (Argument `,`)* \code{)

    Argument
        Expression \\
        | NamedArgument

    NamedArgument
        Identifier `:` Expression
```

```.checking
	\DerivationRule{
        \CheckCall{\ContextVarA}{f}{\overline{args}}{type}{\ContextVarB}
	}{
		\CheckExpr{\ContextVarA}{f `(` \overline{args} `)`}{type}{\ContextVarB}
	}\vspace{1em}

	\DerivationRule{
        \SynthCall{\ContextVarA}{f}{\overline{args}}{type}{\ContextVarB}
	}{
		\SynthExpr{\ContextVarA}{f `(` \overline{args} `)`}{type}{\ContextVarB}
	}	
```

Issue: These rules just kick the can down the road and say that synthesis/checking for call expressions bottlenecks through the \textsc{Call} judgements.

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

```.syntax
	SubscriptExpression
		Expression \code{[} (Argument `,`)* \code{]}
```

<div class=issue>
To a first approximation, a subscript expression like \code{base[a0, a1]} is equivalent to something like \code{base.subscript(a0, a1)}.
That is, we look up the `subscript` members of the \code{base} expression, and then check a call to the result of lookup (which might be overloaded).

Unlike simple function calls, a subscript expression can result in an l-value, based on what accessors the `subscript` declaration that is selected by overload resolution has.
</div>

%A subscript expression invokes one of the subscript declarations in the type of %the base expression. Which subscript declaration is invoked is resolved based on %the number and types of the arguments.
%
%A subscript expression is an l-value if the base expression is an l-value and if %the subscript declaration it refers to has a setter or by-reference accessor.
%
%Subscripts may be formed on the built-in vector, matrix, and array types.

Initializer List Expression {#expr.init-list}
---------------------------

```.syntax
	InitializerListExpression
		\code{\{} (Argument `,`)* \code{\}}
```

Note:
An initializer-list expression may only appear in contexts where it will be checked against an expected type.
There are no synthesis rules for initializer-list expressions.

An initializer-list expression is equivalent to constructing an instance of the expected type using the arguments.


```.checking
	\DerivationRule{
        \CheckConstruct{\ContextVarA}{type}{\overline{args}}{\ContextVarB
	}{
		\CheckExpr{\ContextVarA}{\code{\{} \overline{args} \code{\}}}{type}{\ContextVarB}
	}
```

Cast Expression {#expr.cast}
---------------

```.syntax
	CastExpression
		`(` TypeExpression `)` Expression
```

Note:
A <dfn>cast expression</dfn> attempts to coerce an expression to a desired type.


```.checking
	\DerivationRule{
        \CheckExpr{\ContextVarA}{expr}{type}{\ContextVarB}
	}{
		\SynthExpr{\ContextVarA}{`(` type `)` expr}{type}{\ContextVarB}
	}
```

Note:
A cast expression always synthesizes a type, since the type it produces is manifest in the expression.


<div class=issue>
The above rule treats a cast exprssion as something closer to a type ascription expression, where it expects the underlying expression to be of the desired type, or something implicitly convertible to it.

In contrast, we want a cast expression to be able to invoke \emph{explicit} conversions as well, which are currently not something the formalism encodes.
</div>

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

```.syntax
	AssignmentExpression
        \SynVar[destination]{Expression} `=` \SynVar[source]{Expression}
```

```.checking
	\DerivationRule{
        \begin{trgather}
        \SynthExpr{\ContextVarA}{dst}{`out` type}{\ContextVarB
        \CheckExpr{\ContextVarB}{src}{type}{\ContextVarB
        \end{trgather}
	}{
		\SynthExpr{\ContextVarA}{dst `=` src}{`out` type}{\ContextVarB}
	}

	\DerivationRule{
        \begin{trgather}
        \CheckExpr{\ContextVarA}{dst}{`out` type}{\ContextVarB
        \CheckExpr{\ContextVarB}{src}{type}{\ContextVarB
        \end{trgather}
	}{
		\CheckExpr{\ContextVarA}{dst `=` src}{type}{\ContextVarB}
	}
```

Note:
Assignment expressions support both synthesis and checking judgements.

In each case, the destination} expression is validated first, and then the source} expression.


Issue: The above rules pretend that we can write `out` before a type to indicate that we mean an l-value of that type.
We will need to expand the formalism to include \emph{qualified} types.

Operator Expressions {#expr.op}
--------------------

### Prefix Operator Expressions ### {#expr.op.prefix}

```.syntax
	PrefixOperatorExpression
        PrefixOperator Expression

    PrefixOperator
        \code{+} // identity
        | `-` // arithmetic negation
        | \code{\~} // bit\-wise Boolean negation
        | \code{!} // Boolean negation
        | \code{++} // increment in place
        | \code{--} // decrement in place
```

```.checking
	\DerivationRule{
        \begin{trgather}
        \SynthCall{\ContextVarA}{\code{operator}op}{expr}{type}{\ContextVarB
        \end{trgather}
	}{
		\SynthExpr{\ContextVarA}{op\ expr}{type}{\ContextVarB}
	}

	\DerivationRule{
        \begin{trgather}
            \CheckCall{\ContextVarA}{\code{operator}op}{expr}{type}{\ContextVarB
        \end{trgather}
	}{
		\CheckExpr{\ContextVarA}{op\ expr}{type}{\ContextVarB}
	}
```

Note:
A prefix operator expression is semantically equivalent to a call expression to a function matching the operator, except that lookup for the function name only considers function declarations marked with the \code{prefix} modifier.


Issue: The notation here needs a way to express the restrictions on lookup that are used for prefix/postfix operator names.

### Postfix Operator Expressions ### {#expr.op.postfix}

```.syntax
	PostfixOperatorExprssion
        Expression PostfixOperator}

    PostfixOperator
        | \code{++} // increment in place
        | \code{--} // decrement in place
```

```.checking
	\DerivationRule{
        \begin{trgather}
        \SynthCall{\ContextVarA}{\code{operator}op}{expr}{type}{\ContextVarB
        \end{trgather}
	}{
		\SynthExpr{\ContextVarA}{expr op}{type}{\ContextVarB}
	}

	\DerivationRule{
        \begin{trgather}
            \CheckCall{\ContextVarA}{\code{operator}op}{expr}{type}{\ContextVarB
        \end{trgather}
	}{
		\CheckExpr{\ContextVarA}{expr op}{type}{\ContextVarB}
	}
```

Note:
Postfix operator expressions have similar rules to prefix operator expressions, except that in this case the lookup of the operator name will only consider declarations marked with the \code{postfix} modifier.


### Infix Operator Expressions ### {#expr.op.infix}

```.syntax
	InfixOperatorExpression
        Expression InfixOperator} Expression

    InfixOperator
        | \code{*} // multiplication
        | `/` // division
        | \code{\%} // remainder of division
        | \code{+} // addition
        | `-` // subtraction
        | \code{<<} // left shift
        | \code{>>} // right shift
        | `<` // less than
        | `>` // greater than
        | \code{<=} // less than or equal to
        | \code{>=} // greater than or equal to
        | \code{==} // equal to
        | \code{!=} // not equal to
        | \code{&} // bitwise and
        | \code{^} // bitwise exclusive or
        | \code{|} // bitwise or
        | \code{&&} // logical and
        | \code{||} // logical or
        | \code{+=}		// compound add/assign
        | \code{-=}    	// compound subtract/assign
        | \code{*=}    	// compound multiply/assign
        | \code{/=}    	// compound divide/assign
        | \code{\%=}    	// compound remainder/assign
        | \code{<<=}   	// compound left shift/assign
        | \code{>>=}   	// compound right shift/assign
        | \code{&=}    	// compound bitwise and/assign
        | \code{\|=}   	// compound bitwise or/assign
        | \code{^=}    	// compound bitwise xor/assign
%        | `=`    	// assignment
%        | `,`		// sequence

```


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

```.checking
	\DerivationRule{
        \begin{trgather}
        \SynthCall{\ContextVarA}{\code{operator}op}{left right}{type}{\ContextVarB
        \end{trgather}
	}{
		\SynthExpr{\ContextVarA}{left op right}{type}{\ContextVarB}
	}

	\DerivationRule{
        \begin{trgather}
            \CheckCall{\ContextVarA}{\code{operator}op}{left right}{type}{\ContextVarB
        \end{trgather}
	}{
		\CheckExpr{\ContextVarA}{left op right}{type}{\ContextVarB}
	}
```

With the exception of the assignment operator (`=`), an infix operator expression like `left + right` is equivalent to a call expression to a function of the matching name `operator+(left, right)`.

### Conditional Expression ### {#expr.op.cond}

```.syntax
	ConditionalExpression
        \SynVar[condition]{Expression} \code{?} \SynVar[then]{Expression} `:` \SynVar[else]{Expression}
```

```.checking
	\DerivationRule{
        \begin{trgather}
        \CheckExpr{\ContextVarA}{cond}{`Bool`}{\ContextVarB
        \CheckExpr{\ContextVarB,\code{type} \alpha}{t}{type}{\ContextVarC
        \CheckExpr{\ContextVarC,\code{type} \alpha}{e}{type}{\ContextVarD
        \end{trgather}
	}{
		\CheckExpr{\ContextVarA}{cond \code{?} t `:` e}{type}{\ContextVarD}
	}\vspace{1em}
```

Note:
In both checking and synthesis judgements, the condition} of a conditional expression is checked against the `Bool` type.

In the checking judgement, the then} and else} expressions are both checked against the expected type.


```.checking
	\DerivationRule{
        \begin{trgather}
		\CheckExpr{\ContextVarA, \code{type} \alpha}{cond \code{?} t `:` e}{\alpha}{\ContextVarB
        \end{trgather}
	}{
		\SynthExpr{\ContextVarA}{cond \code{?} t `:` e}{\alpha}{\ContextVarB}
	}
```

Note:
In the synthesis direction, a fresh type variable $\alpha$ is introduced, and the expression is checked against that type.
The output context \ContextVarB of the checking step may include constraints on $\alpha$ introduced by checking the then} and else} expressions.

