Expressions [expr]
===========

**Expressions** are terms that can be **evaluated** to produce values.
This section provides a list of the kinds of expressions that may be used in a Slang program.

> Issue:
>
> We need a place to define a **term** and note how it can be either an expression or a **type expression**.
>
> A **specialize expression** might occur in either the expression or type expression grammar.

In general, the order of evaluation of a Slang expression proceeds from left to right.
Where specific expressions do not follow this order of evaluation, it will be noted.

Some expressions can yield **l-values**, which allows them to be used on the left-hand-side of assignment, or as arguments for `out` or `in out` parameters.

Literal Expressions [expr.lit]
-------------------

Literal expressions are never l-values.

### Integer Literal Expressions [expr.lit.int]

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

### Floating-Point Literal Expressions [expr.lit.float]

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
    
### Boolean Literal Expressions [expr.lit.bool]

```.syntax
BooleanLiteralExpression
    => `true`
    => `false`
```

A boolean literal expression _b_ synthesizes the checked expression _b_ `: @Constant Bool`.

### String Literal Expressions [expr.lit.string]

Note:
A string literal expressions consists of one or more string literal tokens in a row.


```.syntax
	StringLiteralExpression
        StringLiteral+
```

A string literal expression _s_ synthesizes the checked expression _s_ `: @Constant String`.

Name Expressions [expr.name]
----------------------

```.syntax
NameExpression
    => Name
```

To *synthesize* a *name expression* _expr_:

* Let _overloadSet_ be the result of *looking up* the name of _expr_ in the current context

* Let _simplified_ be the result of *simplifying* _overloadSet_

* If _simplified_ is `$Error`, diagnose an error

* Return _simplified_

Member Expression [expr.member]
-----------------

```.syntax
MemberExpression
    => base:Expression `.` member:Name
```

To *synthesize* a *member expression* _expr_:

* Let _base_ be the result of synthesizing the base of _expr_

* Let _overloadSet_ be the result of *looking up* the member name of _expr_ in _base_

* Let _simplified_ be the result of *simplifying* _overloadSet_

* Return _simplified_

> Issue:
>
> These rules attempt to look up a member in an *intermediate expression*, while the *lookup* rules currently only handle lookup in a *checked expression*.
> There needs to be some rule to determine what happens when an attempt is made to look up a member in an intermediate expression such as an overload set.
>
> The current compiler implementation forces the base expression to resolve before performing lookup, but there is not strictly a reason why this always has to be the approach taken.

### Static Member Expression [expr.member.static]

```.syntax
StaticMemberExpression
    => base:Expression `::` member:Name
```

> Issue:
>
> Semantically, there is no reason to treat static member lookup as a special case. All that really gets added here is an assertion that `base` must not be an value-level expression (that is, it must be a type, module, etc.)

This Expression [expr.this]
---------------

### Syntax

```.syntax
ThisExpression
    => `this`
```

### Static Semantics

To *synthesize* a *`this` expression* _expr_:

* Let _overloadSet_ be the result of *looking up* `$this` in the current context

* Let _simplified_ be the result of *simplifying* _overloadSet_

* Return _simplified_

Parenthesized Expression [expr.paren]
-------------

### Syntax

```.syntax
ParenthesizedExpression
    => `(` Expression `)`
```

### Static Semantics

The parenthesized expression `(` _e_ `)` synthesizes _s_ if _e_ synthesizes _s_.

Call Expression [expr.call]
---------------

```.syntax
CallExpression
    => Expression `(` (Argument `,`)* `)`

Argument
    => Expression
    => NamedArgument

NamedArgument
    => Identifier `:` Expression
```

The call expression _f_ `(` _args_ `)` synthesizes _scall_ if:

* _f_ synthesizes _sf_
* The _args_ synthesize _sargs_
* Invocation of _sf_ on _sargs_ synthesizes _scall_

Subscript Expression [expr.subscript]
--------------------

```.syntax
SubscriptExpression
    => Expression `[` (Argument `,`)* `]`
```

The subscript expression _base_ `[` _args_ `]` synthesizes _scall_ if:

* _base_ synthesizes _sbase_
* The _args_ synthesize _sargs_
* Member lookup of `subscript` in _base_ synthesizes _ssub_
* Invocation of _ssub_ on _sargs_ synthesizes _scall_

Initializer List Expression [expr.init-list]
---------------------------

```.syntax
InitializerListExpression
    => `{` (Argument `,`)* `}`
```

The initializer-list expression `{` _args_ `}` synthesizes `{` _sargs_ `}` if:

* The _args_ synthesize _sargs_

The initializer-list expression `{` _args_ `}` checks against _t_ if:

* Invocation of _t_ on _args_ checks against _t_

Cast Expression [expr.cast]
---------------

```.syntax
CastExpression
    => `(` TypeExpression `)` Expression
```

A *cast expression* `(` _typeExp_ `)` _exp_ synthesizes _synExp_ if:

* checking _typeExp_ against `TYPE` yields _type_

* explicitly converting _exp_ to _type_ yields _synExp_

### Legacy: Compatibility Feature [expr.cast.compatiblity]

As a compatiblity feature for older code, Slang supports using a cast where the base expression is an integer literal zero and the target type is a user-defined structure type:

```
MyStruct s = (MyStruct) 0;    
```

The semantics of such a cast are equivalent to initialization from an empty initializer list:

```
MyStruct s = {};
```

Assignment Expression [expr.assign]
----------

```.syntax
AssignmentExpression
    => destination:Expression `=` source:Expression
```

Checking an assignment expression _dst_ `=` _src_ against type _t_ yields _checkedDst_ `=` _checkedSrc_ if:

* Checking _dst_ against `out` _t_ yields _checkedDst_
* Checking _src_ against _t_ yields _checkedSrc_

Note: Assignment does not have a synthesis rule, so an assignment in a context where an expected type is not available (the typical case) will be checked against a fresh type variable.

TODO: The above logic is missing the part where we need to actually invoke property getters/setters

Operator Expressions [expr.op]
--------------------

### Prefix Operator Expressions [expr.op.prefix]

```.syntax
PrefixOperatorExpression
    => PrefixOperator Expression

PrefixOperator
    => `+`      // identity
    => `-`      // arithmetic negation
    => `\~`     // bit\-wise Boolean negation
    => `!`      // Boolean negation
    => `++`     // increment in place
    => `--`     // decrement in place
```

A prefix operator expression _op_ _e_ desugars into `operator` `prefix` _op_ `(` _e_ `)`.

## Postfix Operator Expressions [expr.op.postfix]

```.syntax
PostfixOperatorExpression
    => Expression PostfixOperator

PostfixOperator
    => `++` // increment in place
    => `--` // decrement in place
```

A postifx operator expression _e_ _op_ desugars into `operator` `postfix` _op_ `(` _e_ `)`.

### Infix Operator Expressions [expr.op.infix]

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

An infix operator expression _left_ _op_ _right_ desugars into `operator` _op_ `(` _left_ `,` _right_ `)`.

TODO: The above rule implies incorrect handling of the short-circuiting `&&` and `||` operators.

### Conditional Expression [expr.op.cond]

```.syntax
ConditionalExpression
    => condition:Expression `?` then:Expression `:` else:Expression
```

A conditional expression _c_ `?` _t_ `:` _e_ checks against expected type _T_ if:

* _c_ checks against `Bool`
* _t_ checks against _T_
* _e_ checks against _T_

Fodder
======

> TODO:
>
> * `nullptr` literals
> * `none` literals
>
> * Variadics:
>   * `expand`
>   * `each`
>
> * `try` expr
> * `new` expr
>
> * `->` operator
> * `::` operator
>
> * expr `is` type
> * expr `as` type
>
> * Layout related:
>   * `sizeof`
>   * `alignof`
>   * `countof`
>
> * specialize (with `<>`)
>
> * autodiff exprs
>   * `__fwd_diff`
>   * `__bwd_diff`
>   * `no_diff`
>
> * type expression cases
>   * conjunctions: left `&` right
>   * modifier type
>   * pointer types: type `*`
>   * function types: `(` type* `)` `->` type
>   * tuple types