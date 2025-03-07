# Parsing  [parse]

<div class=issue>
The intention of this chapter is to establish the overall rules for the recursive-descent  *parsing* strategy needed for Slang's grammar.

Slang attempts to thread the needle by supporting the familiar C-like syntax of existing shading languages, while also support out-of-order declarations.
The parsing strategy is necessarily complicated as a result, but we hope to isolate most of the details to this chapter so that the grammar for each construct can be presented in its simplest possible fashion.
</div>

 **Parsing** is the process of matching a sequence of tokens from the lexical grammar with a rule of the abstract syntax grammar.

## Contexts  [parse.context]

Parsing is always performed with respect to a  *context*, which determines which identifiers are bound, and what they are bound to.

The  **initial context** for parsing includes bindings for syntax rules corresponding to each declaration, statement, and expression keyword defined in this specification.

Note: For example, an `if` expression begins with the `if` keyword, so the  *initial context* contains a binding for the identifier `if` to a syntax rule that parses an `if` expression. 

The initial context also includes bindings for the declarations in the Slang standard library.
Implementations may include additional bindings in the initial context.


## Strategies  [parse.strat]

Parsing is always performed in one of two modes:  *unordered* or  *ordered*.
Unless otherwise specified, each grammar rule matches its sub-rules in the same mode.

### Ordered  [parse.strat.ordered]

Parsing in  **ordered** mode interleaves parsing and semantic analysis.
When the parser is in ordered mode and is about to parse a  *declaration*,  *statement*, or  *expression*, and the lookahead is an Identifier, it first looks up that identifier in the context.


* If the identifier is bound to a syntax rule _s_, then the parser attempts to match the corresponding production in the grammar given here.

* Otherwise, the parser first matches a  *term*, and then based on whether the result of checking that term is a  *type* or an  *expression*, it either considers only productions starting with a  *type expression* or those starting with an  *expression*.

If the parser is in ordered mode and is about to parse a  *declaration body*, it switches to unordered mode before parsing the body, and switches back to ordered mode afterward.

### Unordered  [parse.strat.unordered]

In  **unordered** mode, semantic analysis is deferred.

When the parser is in unordered mode and is about to parse a  *declaration*, and the lookahead is an Identifier, it first looks up that identifier in the context.

* If the identifier is bound to a syntax rule _s_, then the parser attempts to match the corresponding production in the grammar given here.

* Otherwise, it considers only productions that start with a  *type specifier*.

 **Balanced tokens** are those that match the following production:

```.syntax
BalancedTokens :
    BalancedToken*

BalancedToken :
    `{` BalancedTokens `}`
    | `(` BalancedTokens `)`
    | `[` BalancedTokens `]`
    | /* any token other than `{`, `}`, `(`, `)`, `[`, `]` */
```

A  **balanced** rule in the grammar is one that meets one of the following criteria:

* starts with a `{` and ends with a `}`
* starts with a `(` and ends with a `)`
* starts with a `[` and ends with a `]`


Whenever the parser is in ordered mode and would attempt to match a  *balanced* rule _r_, it instead matches the  *balanced token* rule and saves the token sequence that was matched.
Those tokens are then matched against _r_ as part of semantic analysis, using the context that the checking rules specify.

## Angle Brackets  [parse.angle]

### Opening Angle Brackets  [parse.angle.open]

#### Ordered Mode  [parse.angle.open.ordered]

If the parser is in ordered mode with a lookahead of `<`, and it could match that token as part of either an  *infix expression* or a  *specialize expression*, then it considers the term that has been matched so far:

* If the term has a generic type or overloaded type, then the  *specialize expression* case is favored.
* Otherwise the  *infix expression* case is favored.


#### Unordered Mode  [parse.angle.open.unordered]

If the parser is in ordered mode with a lookahead of `<`, and it could match that token as part of either an   *infix expression* or a  *specialize expression*, then it first attempts to match the  *generic arguments* rule. If that rule is matched successfully, then the new lookahead token is inspected:


* If the lookahead token is an  *identifier*, `(`,  *literal*, or  *prefix operator*, then roll back to before the `<` was matched and favor the   *infix expression* rule.
* Otherwise, use the generic arguments already matched as part of matching the  *specialize expression* rule.


### Closing Angle Brackets  [parse.angle.close]

If the parser is attempting to match the closing `>` in the  *generic parameters* or  *generic arguments* rules, and the lookahead is any token other than `>` that starts with a `>` character (`>=`, `>>`, or `>>=`), then it splits the opening `>` off and matches it, replacing the lookahead with a token comprised of the remaining characters (`=`, `>`, or `>=`).
