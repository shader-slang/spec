# Expressions  [expr]

 **Expressions** are terms that can be  **evaluated** to produce values.
This section provides a list of the kinds of expressions that may be used in a Slang program.

<div class="issue">
We need a place to define a  **term** and note how it can be either an expression or a  **type expression**.

A  **specialize expression** might occur in either the expression or type expression grammar.
</div>

In general, the order of evaluation of a Slang expression proceeds from left to right.
Where specific expressions do not follow this order of evaluation, it will be noted.

Some expressions can yield  **l-values**, which allows them to be used on the left-hand-side of assignment, or as arguments for `out` or `in out` parameters.

## Literal Expressions  [expr.lit]

Literal expressions are never l-values.

### Integer Literal Expressions  [expr.lit.int]

An integer literal expression consists of a single IntegerLiteral token.

```.checking
	\DerivationRule{
		\begin{trgather}
        \CheckConforms{\ContextVarA,\alpha}{\alpha}{`IFromIntegerLiteral`}{\ContextVarB}
		\end{trgather}	
	}{
		\SynthExpr{\ContextVarA}{i}{\alpha}{\ContextVarB}
	}
```

To check an unsuffixed integer literal _lit_ against type _T_:

* Validate that _T_ conforms to `IFromIntegerLiteral`, yielding conformance witness `w`
* Let _f_ be a declaration reference to `IFromIntegerLiteral.init` looked up through `w`
* Return the checked expression _f_ `(` _lit_ `) :` _T_

Issue: We need a description of how suffixed integer literals have their type derived from their suffix.

### Floating-Point Literal Expressions  [expr.lit.float]

A floating-point literal expression consists of a single FloatingPointLiteral token.

```.checking
	\DerivationRule{
		\begin{trgather}
        \CheckConforms{\ContextVarA,\alpha}{\alpha}{`IFromFloatingPointLiteral`}{\ContextVarB}
		\end{trgather}	
	}{
		\SynthExpr{\ContextVarA}{f}{\alpha}{\ContextVarB}
	}
```

Note:
An unsuffixed floating-point literal synthesizes a type that is a fresh type variable $\alpha$, constrained to conform to `IFromFloatingPointLiteral`.


Issue: We need a description of how suffixed floating-point literals have their type derived from their suffix.
    
### Boolean Literal Expressions  [expr.lit.bool]

Note:
    Boolean literal expressions use the keywords `true` and `false`.

    
```.syntax
	BooleanLiteralExpression
        `true` | `false`
```

The expression `true` resolves to the typed Boolean value `true : Bool`.

The expression `false` resolves to the typed Boolean value `false : Bool`.

### String Literal Expressions  [expr.lit.string]

Note:
A string literal expressions consists of one or more string literal tokens in a row.


```.syntax
	StringLiteralExpression
        StringLiteral+
```

```.checking
	\DerivationRule{
	}{
		\SynthExpr{\ContextVarA}{\overline{s}}{`String`}{\ContextVarA}
	}\\
```

## Identifier Expressions  [expr.ident]

```.syntax
	IdentifierExpression
        Identifier
        | `operator` Operator
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

## Member Expression  [expr.member]

```.syntax
	MemberExpression
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

## This Expression  [expr.this]

```.syntax
	ThisExpression => `this`
```

```.checking
	\DerivationRule{
	}{
		\SynthExpr{\ContextVarA}{`this`}{`This`}{\ContextVarB}
	}	
```


Note:
In contexts where a `this` expression is valid, it refers to the implicit instance of the closest enclosing type declaration.
The type of a `this` expression is always `This`.


Issue: This section needs to deal with the rules for when `this` is mutable vs. immutable.

## Parenthesized Expression  [expr.paren]

Note:
An expression wrapped in parentheses (`()`) is a parenthesized expression and evaluates to the same value as the wrapped expression.


```.syntax
	ParenthesizedExpression := 
        `(` Expression `)`
```

If expression _e_ resolves to _er_ then the parenthesized expression `(` _e_ `)` resolves to _er_.

## Call Expression  [expr.call]

```.syntax
    CallExpression
        Expression `(` (Argument `,`)* `)`

    Argument
        Expression
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
% ### Mutability  [expr.call.mutable]
%
%If a `[mutating]` instance is being called, the argument for the implicit `this` %parameter must be an l-value.
%
%The argument expressions corresponding to any `out` or `in out` parameters of the %callee must be l-values.
%\end{verbatim}

## Subscript Expression  [expr.subscript]

```.syntax
	SubscriptExpression
		Expression `[` (Argument `,`)* `]`
```

<div class=issue>
To a first approximation, a subscript expression like `base[a0, a1]` is equivalent to something like `base.subscript(a0, a1)`.
That is, we look up the `subscript` members of the `base` expression, and then check a call to the result of lookup (which might be overloaded).

Unlike simple function calls, a subscript expression can result in an  *l-value*, based on what accessors the `subscript` declaration that is selected by overload resolution has.
</div>

%A subscript expression invokes one of the subscript declarations in the type of %the base expression. Which subscript declaration is invoked is resolved based on %the number and types of the arguments.
%
%A subscript expression is an l-value if the base expression is an l-value and if %the subscript declaration it refers to has a setter or by-reference accessor.
%
%Subscripts may be formed on the built-in vector, matrix, and array types.

## Initializer List Expression  [expr.init-list]

```.syntax
	InitializerListExpression
		`{` (Argument `,`)* `}`
```

If the sequence of arguments _args_ resolves to _resolvedArgs_, then the initializer list expression `{` _args_ `}` resolves to the resolved initializer list expression `{` _resolvedArgs_ `}`.

Note: An initializer-list expression can only appear in contexts where it will be coerced to an expected type.

## Cast Expression  [expr.cast]

```.syntax
	CastExpression
		`(` TypeExpression `)` Expression
```

Note:
A  **cast expression** attempts to coerce an expression to a desired type.

To resolve a  *cast expression* `(` _t_ `)` _e_:

* Let _checkType_ be the result of checking _t_ as a type
* Let _checkedExpr_ be the result of checking _e_ against _checkType_
* Return _checkedExpr_

<div class=issue>
The above rule treats a cast exprssion as something closer to a type ascription expression, where it expects the underlying expression to be of the desired type, or something implicitly convertible to it.

In contrast, we want a cast expression to be able to invoke \emph{explicit} conversions as well, which are currently not something the formalism encodes.
</div>

\begin{Legacy}
### Legacy: Compatibility Feature  [expr.cast.compatiblity]

As a compatiblity feature for older code, Slang supports using a cast where the base expression is an integer literal zero and the target type is a user-defined structure type:

```
MyStruct s = (MyStruct) 0;    
```

The semantics of such a cast are equivalent to initialization from an empty initializer list:

```
MyStruct s = {};
```

\end{Legacy}

## Assignment Expression  [expr.assign]

```.syntax
	AssignmentExpression
        n:Expression `=` e:Expression
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

## Operator Expressions  [expr.op]

### Prefix Operator Expressions  [expr.op.prefix]

<div class="issue">
This section defines the terms:  **prefix operator**.
</div>

```.syntax
	PrefixOperatorExpression
        PrefixOperator Expression

    PrefixOperator
        `+` // identity
        | `-` // arithmetic negation
        | `\~` // bit\-wise Boolean negation
        | `!` // Boolean negation
        | `++` // increment in place
        | `--` // decrement in place
```

```.checking
	\DerivationRule{
        \begin{trgather}
        \SynthCall{\ContextVarA}{`operator`op}{expr}{type}{\ContextVarB
        \end{trgather}
	}{
		\SynthExpr{\ContextVarA}{op\ expr}{type}{\ContextVarB}
	}

	\DerivationRule{
        \begin{trgather}
            \CheckCall{\ContextVarA}{`operator`op}{expr}{type}{\ContextVarB
        \end{trgather}
	}{
		\CheckExpr{\ContextVarA}{op\ expr}{type}{\ContextVarB}
	}
```

Note:
A prefix operator expression is semantically equivalent to a call expression to a function matching the operator, except that lookup for the function name only considers function declarations marked with the `prefix` modifier.


Issue: The notation here needs a way to express the restrictions on lookup that are used for prefix/postfix operator names.

## Postfix Operator Expressions  [expr.op.postfix]

```.syntax
	PostfixOperatorExprssion
        Expression PostfixOperator

    PostfixOperator
        | `++` // increment in place
        | `--` // decrement in place
```

```.checking
	\DerivationRule{
        \begin{trgather}
        \SynthCall{\ContextVarA}{`operator`op}{expr}{type}{\ContextVarB
        \end{trgather}
	}{
		\SynthExpr{\ContextVarA}{expr op}{type}{\ContextVarB}
	}

	\DerivationRule{
        \begin{trgather}
            \CheckCall{\ContextVarA}{`operator`op}{expr}{type}{\ContextVarB
        \end{trgather}
	}{
		\CheckExpr{\ContextVarA}{expr op}{type}{\ContextVarB}
	}
```

Note:
Postfix operator expressions have similar rules to prefix operator expressions, except that in this case the lookup of the operator name will only consider declarations marked with the `postfix` modifier.


### Infix Operator Expressions  [expr.op.infix]

<div class="issue">
The syntax here should introduce the term:  **infix expression**.
</div>


```.syntax
	InfixOperatorExpression
        Expression InfixOperator Expression

    InfixOperator
        | `*` // multiplication
        | `/` // division
        | `\%` // remainder of division
        | `+` // addition
        | `-` // subtraction
        | `<<` // left shift
        | `>>` // right shift
        | `<` // less than
        | `>` // greater than
        | `<=` // less than or equal to
        | `>=` // greater than or equal to
        | `==` // equal to
        | `!=` // not equal to
        | `&` // bitwise and
        | `^` // bitwise exclusive or
        | `|` // bitwise or
        | `&&` // logical and
        | `||` // logical or
        | `+=`		// compound add/assign
        | `-=`    	// compound subtract/assign
        | `*=`    	// compound multiply/assign
        | `/=`    	// compound divide/assign
        | `\%=`    	// compound remainder/assign
        | `<<=`   	// compound left shift/assign
        | `>>=`   	// compound right shift/assign
        | `&=`    	// compound bitwise and/assign
        | `\|=`   	// compound bitwise or/assign
        | `^=`    	// compound bitwise xor/assign
        | `=`    	// assignment
        | `,`		// sequence

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
%| `\_\_`	| Or 				| logical or |
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
        \SynthCall{\ContextVarA}{`operator`op}{left right}{type}{\ContextVarB
        \end{trgather}
	}{
		\SynthExpr{\ContextVarA}{left op right}{type}{\ContextVarB}
	}

	\DerivationRule{
        \begin{trgather}
            \CheckCall{\ContextVarA}{`operator`op}{left right}{type}{\ContextVarB
        \end{trgather}
	}{
		\CheckExpr{\ContextVarA}{left op right}{type}{\ContextVarB}
	}
```

With the exception of the assignment operator (`=`), an infix operator expression like `left + right` is equivalent to a call expression to a function of the matching name `operator+(left, right)`.

### Conditional Expression  [expr.op.cond]

```.syntax
	ConditionalExpression
        n:Expression `?` n:Expression `:` e:Expression
```

To check the conditional expression _cond_ `?` _t_ `:` _e_ against expected type _T_:

* Let _checkedCond_ be the result of checking _cond_ against `Bool`
* Let _checkedThen_ be the result of checking _t_ against _T_
* Let _checkedElse_ be the result of checking _e_ against _T_
* Return the checked expression _checkedCond_ `?` _checkedThen_ `:` _checkedElse_

To check the conditional expression _ce_:

* Extend the context with a fresh type variable _T_
* Return the result of checking _ce_ against _T_

