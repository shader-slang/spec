Statements [stmt]
==========

A **statement** is an entity in the abstract syntax that describes actions to be taken by a thread.
Statements are executed for their effect, rather than evaluated to produce a value.

```.syntax
Statement :
	ExpressionStatement
	| DeclarationStatement
	| BlockStatement
	| EmptyStatement
	| IfStatement
	| SwitchStatement
	| CaseStmt
	| ForStatement
	| WhileStatement
	| DoWhileStatement
	| BreakStatement
	| ContinueStatement
	| ReturnStatement
	| DiscardStatement
	| LabeledStatement
```

Expression Statement [stmt.expr]
--------------------

An **expression statement** evaluates an expression, and then ignores the resulting value.

```.syntax
ExpressionStatement :
	Expression `;`
```

```.checking
GIVEN context c, expression e
GIVEN e synthesizes type t in context c
THEN e `;` checks in context c
```

An implementation may diagnose a warning when execution of an *expression statement* cannot have side effects.

Declaration Statement [expr.decl]
---------------------

A **declaration statement** introduces a declaration into the current scope.
	
```.syntax
DeclarationStatement :
	Declaration
```

```.checking
GIVEN context c, declaration d
GIVEN declaration d checks in context c
THEN statement d checks in context c
```
	
Only the following types of declarations may be used in a *declaration statement*:


* VariableDeclaration


Block Statement [stmt.block]
---------------

A **block statement** executes each of its constituent statements in order.

```.syntax
BlockStatement :
	`{` Statement* `}`
```


```.checking

GIVEN context c
GIVEN statements s0,s1,...
GIVEN context d, a fresh sub-context of c
GIVEN s0,s1,... check in d
THEN `{` s0,s1,... `}` checks in c
```

Note: Declarations in a *block statement* are visible to later statements in the same block, but not to earlier statements in the block, or to code outside the block.	

Empty Statement [stmt.empty]
---------------

Executing an empty statement has no effect.
	
```.syntax
EmptyStatement :
	`;`
```

```.checking
GIVEN context c
THEN `;` checks in c
```

Conditional Statements [stmt.cond]
----------------------

### If Statement [stmt.if]

An **if statement** executes a sub-statement conditionally.

```.syntax
IfStatement :
	`if` `(` IfCondition `)`
	Statement
	ElseClause?

IfCondition :
	Expression
	| LetDeclaration

ElseClause :
	`else` Statement
	
```

```.checking

GIVEN context c, expression e, statement t
GIVEN e checks against `Bool` in c
GIVEN t checks in C
THEN `if(` e `)` t checks in c

GIVEN context c, expression e, statement t
GIVEN e checks against `Bool` in c
GIVEN t checks in C
GIVEN f checks in C
THEN `if(` e `)` t `else` f checks in c	
```

If the condition of an *if statement* is an expression, then it is evaluated against an expected type of `Bool` to yield a value _C_.
If _C_ is `true`, then the ThenClause is executed.
If _C_ is `false` and there is a ElseClause, then it is executed.

If the condition of an `if` statement is a `let` declaration, then that declaration must have an initial-value expression.
That initial-value expression is evaluated against an expected type of `Optional<T>`, where _T_ is a fresh type variable, to yield a value _D_.
If _D_ is `Some(_C_)`, then the ThenClause is executed, in an environment where the name of the `let` declaration is bound to _C_.
If _D_ is `null` and there is a ElseClause, then it is executed.

### Switch Statement [stmt.switch]


A **`switch` statement** conditionally executes up to one of its **alternatives**, based on the value of an expression.
	
```.syntax
SwitchStatement :
	`switch` `(` Expression `)`
	`{` SwitchAlternative+ `}`

SwitchAlternative :
	SwitchAlternativeLabel+ Statement+

SwitchAlternativeLabel :
	CaseClause
	| DefaultClause

CaseClause :
	`case` Expression `:`

DefaultClause
	`default` `:`
```

```.checking
GIVEN context c, expression e, switch alternatives a0,a1,...
GIVEN e synthesizes type t in c
GIVEN a0,a1,... check against t in c
THEN `switch(` e `) {` a0,a1,... `}` checks in c
```

Note:
A `switch` statement is checked by first checking the expression, and then checking each of the *alternatives* against the type of that expression.

```.checking
GIVEN context c, type t,
GIVEN switch alternative labels l0,l1,...
GIVEN statements s0,s1,...
GIVEN l0,l1,... check against t in c
GIVEN s0,s1,... check in c
THEN switch alternative l0,l1,... s0,s1,... checks in c

GIVEN context c, type t, expression e
GIVEN e checks against t in c
THEN `case` e `:` checks against t in c

GIVEN context c, type t
THEN `default:` checks against t in c
```

Note:
A `case` clause is valid if its expression *checks against* the type of the control expressio nof the `switch` statement.

A `switch` statement may have at most one `default` clause.

If the type of the controlling expression of a `switch` statement is a built-in integer type, then:


* The expression of each `case` clause must be a compile-time constant expression.
* The constant value of the expression for each `case` clause must not be equal to that of any other `case` clause in the same `switch`.


Each alternative of a `switch` statement must exit the `switch` statement via a `break` or other control transfer statement.
"Fall-through" from one switch case clause to another is not allowed.

Note:
Semantically, a `switch` statement is equivalent to an "`if` cascade" that compares the value of the conditional expression against each `case` clause,

Loop Statements [stmt.loop]
---------------

A **loop statement** executes a body statement one or more times.

### For Statement [stmt.for]

```.syntax
ForStatement :
	`for` `(`
	initial:Statement? `;`
	conditional:Expression? `;`
	sideEffect:Expression? `)`
	body:Statement
```


```.checking
GIVEN init checks in c
GIVEN cond checks against `Bool` in c
GIVEN iter synthesizes type t in c
GIVEN body checks in c
THEN `for(init;cond;iter) body` checks in c
```

Issue: The checking judgements above aren't complete because they don't handle the case where _cond_ is absent, in which case it should be treated like it was `true`.

### While Statement [stmt.while]


```.syntax
WhileStatement :
	`while` `(`
	conditional:Expression `)`
	body:Statement
```


```.checking
GIVEN cond checks against `Bool` in c
GIVEN body checks in c
THEN `while(cond) body` checks in c
```

### Do-While Statement [stmt.do-while]

A do-while statement uses the following form:

```.syntax
DoWhileStatement :
	`do` body:Statement
	`while` `(` conditional:Expression `)` `;`		
```


```.checking
GIVEN body checks in c
GIVEN cond checks againt `Bool` in c
THEN `do body while(cond);` checks in c
```

Issue: These simplified prose checking rules are leaving out all the subtlties of sub-contexts, etc.

Control Transfer Statements [stmt.control]
---------------------------

### `break` Statement [stmt.break]

A **break statement** is used to transfer control out of the context of some enclosing statement.
A *break statement* may optionally provide a **label**, to identify the enclosing statement.

```.syntax
BreakStatement :
	`break` label:Identifier? `;`
```

A *break statement* without a *label* transfers control to after the end of the closest lexically enclosing *switch statement* or *loop statement*.

A *break statement* with a *label* transfers control to after the end of the lexically enclosing *switch statement* or *loop statement* labeled with a matching *label*.

```.checking
GIVEN context c
GIVEN lookup of BREAK_LABEL in c yields label l
THEN `break;` checks in context c

GIVEN context c, label l
GIVEN c contains an entry of the form BREAK_LABEL = l
THEN `break l;` checks in context c
```

<div class=issue>
Issue: The checking rules for `break`-able statements should add a suitable item to the context used for checking their body statements, which will be matched by the rules above.

We also need to define the context-containment rule that is being used to look up the `break` item in the context.
</div>

### Continue Statement [stmt.continue]

```.syntax
ContinueStatement :
	`continue` label:Identifier? `;`
```

A `continue` statement transfers control to the start of the next iteration of a loop statement.
In a `for` statement with a side effect expression, the side effect expression is evaluated when `continue` is used:

```.checking
GIVEN context c
GIVEN lookup of CONTINUE_LABEL in c yields label l
THEN `continue;` checks in context c

GIVEN context c, label l
GIVEN c contains an entry of the form CONTINUE_LABEL = l
THEN `continue l;` checks in context c
```

### Return Statement [stmt.return]

A `return` statement transfers control out of the current function.

	
```.syntax
ReturnStatement :
	`return` Expression? `;`
```

```.checking
GIVEN context c, expression e
GIVEN lookup of RESULT_TYPE in c yields type t
GIVEN e checks against t in c
THEN `return e;` checks in c
```

```.checking
GIVEN context c
GIVEN lookup of RESULT_TYPE in c yield type t
GIVEN `Unit` is a subtype of t
THEN `return;` checks in c
```

Note: A `return` statement without an expression is equivalent to a `return` of a value of type `Unit`.


### Discard Statement [stmt.discard]

```.syntax
DiscardStatement :
	`discard` `;`
```

A `discard` statement may only be used in the context of a fragment shader, in which case it causes the current invocation to terminate and the graphics system to discard the corresponding fragment so that it does not get combined with the framebuffer pixel at its coordinates.

Operations with side effects that were executed by the invocation before a `discard` will still be performed and their results will become visible according to the rules of the platform.	


```.checking
GIVEN context c
GIVEN capability `fragment` is available in c
THEN `discard;` checks in c
```

Issue:
The intent of the above rule is that checking a `discard` statement will add the `fragment` capability to the context, so that it can be checked against the capabilities of the surrounding function/context.
However, the way the other statement rules handle the context, they do not allow for anything in the context to flow upward/outward in that fashion.
It may be simplest to have the process of collecting the capabilities required by a function body be a different judgement than the type checking rules.

