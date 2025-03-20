Lexical Structure [CHAPTER.lex]
=================

This chapter describes how a *source unit* is decomposed into a sequence of *lexemes*.

Source Units [lex.source-unit]
------------

A **source unit** comprises a sequence of zero or more *characters*.
For the purposes of this document, a **character** is defined as a [[!Unicode]] scalar value.

Note: A Unicode scalar value is a Unicode code point that is not a surrogate code point.

Implementations may accept *source units* stored as files on disk, buffers in memory, or any appropriate implementation-specified means.

Encoding [lex.encoding]
--------

Implementations must support *source units* encoded using UTF-8, if they support any encoding of *source units* as byte sequences.

Implementations should default to the UTF-8 encoding for all text input/output.

Implementations may support additional implementation-specified encodings.

Phases [lex.phase]
------

Lexical processing of a *source unit* proceeds *as if* the following steps are executed in order:

1. Line numbering (for subsequent diagnostic messages) is noted based on the locations of *line breaks*

2. *Escaped line breaks* are eliminated. No new *characters* are inserted to replace them. Any new *escaped line breaks* introduced by this step are not eliminated.

3. Each comment is replaced with a single space (U+0020)

4. The *source unit* is <a lt=lex>lexed</a> into a sequence of *tokens* according to the lexical grammar in this chapter

5. The lexed sequence of tokens is _preprocessed_ to produce a new sequence of tokens

The final *token* sequence produced by this process is used as input to subsequent phases of compilation.

Lexemes [lex.lexeme]
-------

A **lexeme** is a contiguous sequence of characters in a single *source unit*.

**Lexing** is the process by which an implementation decomposes a *source unit* into zero or more non-overlapping *lexemes*.

Every *lexeme* is either a *token* or it is *trivia*.

```.lexical
Lexeme :
  Token
  | Trivia
  ;
```

### Trivia [lex.trivia]

**Trivia** are *lexemes* that do not appear in the abstract syntax; they are only part of the lexical grammar.
The presence or absence of *trivia* in a sequence of *lexemes* has no semantic impact, except where specifically noted in this specification.

```.lexical
Trivia :
  Whitespace
  | Comment
  ;
```

Note: Trivia is either *whitespace* or a *comment*.

#### Whitespace [lex.trivia.space]

**Whitespace** consists of *horizontal whitespace* and *line breaks*.

```.lexical
Whitespace :
  HorizontalSpace
  | LineBreak
  ;
```

**Horizontal whitespace** consists of any sequence of space (U+0020) and horizontal tab (U+0009).

```.lexical
HorizontalSpace : (' ' | '\t')+ ;
```

```.lexical
LineBreak
  => '\n'
  => '\r'
  => '\r' '\n'
```

##### Line Breaks [lex.trivia.space.line-break]

A **line break** consists of a line feed (U+000A), carriage return (U+000D) or a carriage return followed by a line feed (U+000D, U+000A).

An **escaped line break** is a backslash (`\`, U+005C) follow immediately by a *line break*.

A *source unit* is split into **lines**: non-empty sequences of *characters* separated by *line breaks*.

Note: Line breaks are used as *line* separators rather than terminators; it is not necessary for a *source unit* to end with a line break.

#### Comments [lex.trivia.comment]

```.lexical
Comment
    => LineComment
    => BlockComment
```

```.lexical
LineComment
    => `//` (CodePoint - LineBreak)*
```

```.lexical
BlockComment
    => `/*` BlockCommentContent `*/`

BlockCommentContent
  => ((CodePoint - `*`) | (`*` (CodePoint - `/`)))* `*`*
```

A **line comment** comprises two forward slashes (`/`, U+002F) followed by zero or more characters that do not contain a *line break*.
A *line comment* extends up to, but does not include, a subsequent *line break* or the end of the *source unit*.

A **block comment** begins with a forward slash (`/`, U+002F) followed by an asterisk (`*`, U+0052). 
A *block comment* is terminated by the next instance of an asterisk followed by a forward slash (`*/`).
A *block comment* contains all *characters* between where it begins and where it terminates, including any *line breaks*.

Note: *Block comments* do not nest.

It is an error if a *block comment* that begins in a *source unit* is not terminated in that *source unit*.

### Tokens [lex.token]

**Tokens** are lexemes that are significant to the abstract syntax.

```.lexical
Token :
    Identifier
    | Literal
    | Operator
    | Punctuation
;
```

#### Identifiers [lex.token.ident]

```.lexical
Identifier :
    IdentifierStart IdentifierContinue*
    ;

IdentifierStart :
    [A-Z]
    | [a-z]
    | '_'
    ;

IdentifierContinue :
    IdentifierStart
    | [0-9]
    ;
```
TODO: **identifier**.

The identifier consisting of a single underscore (`_`) is reserved by the language and must not be used by programs as a name in a declaration or binding.

Note: There are no other fixed keywords or reserved words recognized by the lexical grammar.

#### Literals [lex.token.lit]

```.lexical
Literal :
    NumericLiteral
    | TextLiteral
    ;
```

##### Numeric Literals [lex.token.num]

A **numeric literal** is either an *integer literal* or a *floating-point literal*.

```.lexical
NumericLiteral :
    IntegerLiteral
    | FloatingPointLiteral
    ;
```

```.lexical
RadixSpecifier
  => HexadecimalRadixSpecifier
  => BinaryRadixSpecifier
```

```.lexical
HexadecimalRadixSpecifier
  => `0` [xX]
```

```.lexical
BinaryRadixSpecifier
  => `0` [bB]
```

When no radix specifier is present, a numeric literal is a **decimal literal** (radix 10).

Note:Octal literals (radix 8) are not supported.
A `0` prefix on an integer literal is not used to specify an octal literal as it does in C.
Implementations may diagnose a warning on *integer literals* with a `0` prefix.

```.lexical
DecimalDigits
  => DecimalDigit (DecimalDigit | `_`)*

HexadecimalDigits
  => HexadecimalDigit (HexadecimalDigit | `_`)*

BinaryDigits
  => BinaryDigit (BinaryDigit | `_`)*

DecimalDigit
  => [0-9]

HexadecimalDigit
  => [0-9A-Fa-f]

BinaryDigit
  => [0-1]
```

The grammar of the *digits* for a numeric level depend on its radix, as follows:

* The *digits* of a *decimal literal* may include `0` through `9`
* The *digits* of a *hexadecimal literal* may include `0` through `9`, the letters `A` through `F` and `a` through `f`. The letters represent digit values 10 through 15.
* The *digits* of a *binary literal* may include `0` and `1`

```.lexical
NumericLiteralSuffix
  => Identifier
```

#### Integer Literals [lex.token.int]

```.lexical
IntegerLiteral
  => DecimalDigits NumericLiteralSuffix?
  => HexadecimalRadixSpecifier HexadecimalDigits NumericLiteralSuffix?
  => BinaryRadixSpecifier BinaryDigits NumericLiteralSuffix?
```

The suffix on an integer literal may be used to indicate the desired type of the literal:

* A `u` suffix indicates the `UInt` type
* An `l` or `ll` suffix indicates the `Int64` type
* A `ul` or `ull` suffix indicates the `UInt64` type

TODO: The suffixes should be documented in the type-checking rules.

#### Floating-Point Literals [lex.token.float]

A **floating-point literal** consists of either

```.lexical
FloatingPointLiteral
  => DecimalFloatingPointLiteral

DecimalFloatingPointLiteral
  => DecimalDigits `.` DecimalDigits? Exponent? NumericLiteralSuffix?
  => DecimalDigits Exponent NumericLiteralSuffix?
  => `.` DecimalDigits Exponent? NumericLiteralSuffix?

HexadecimalFloatingPointLiteral
  => HexadecimalRadixSpecifier HexadecimalDigits `.` HexadecimalDigits? Exponent? NumericLiteralSuffix?
  => HexadecimalRadixSpecifier HexadecimalDigits Exponent NumericLiteralSuffix?

Exponent
  => [eE]? Sign? DecimalDigits

Sign
  => `+`
  => `-`
```

### Text Literals [lex.token.text]

```.lexical
TextLiteral
    => StringLiteral
    => CharacterLiteral
```

#### Escape Sequences [lex.token.text.escape]

```.lexical
TextLiteralEscapeSequence
    => `\` `n`
    => `\` `r`
    => `\` `t`
```

Issue: This needs to be expanded to include all of the escape sequences.

#### String Literals [lex.token.text.string]

```.lexical
StringLiteral
    => `"` StringLiteralItem* `"`

StringLiteralItem
    => CodePoint - `"`
    => TextLiteralEscapeSequence
```

A **string literal** consists of a sequence of characters enclosed between two `"`, with the constraint that any `"` within the sequence must be escaped with `\`.

TODO: *string literal*

#### Character Literals [lex.token.text.char]

```.lexical
CharacterLiteral
    => `'` CharacterLiteralItem* `'`

CharacterLiteralItem
    => CodePoint - `'`
    => TextLiteralEscapeSequence
```


A **character literal** consists of a sequence of characters enclosed between two `'`, with the constraint that any `'` within the sequence must be escaped with `\`.

The sequence of characters within a *character literal* must represent a single character.

Operators and Punctuation [lex.token.punctuation]
-------------------------

The following table defines tokens that are used as operators and punctuation in the syntax.
When a given sequence of characters could be interpreted as starting with more than one of the following tokens, the longest matching token is used.
The name or names given to tokens by this table may be used in the rest of this document to refer to those tokens.

```.lexical

Punctuation :
  | `(`     // left parenthesis
  | `)`     // right parenthesis
  | `[`     // left square bracket, opening square bracket
  | `]`     // right square bracket, closing square bracket
  | `{`    // left curly brace, opening curly brace
  | `}`    // right curly brace, closing curly brace
  | `;`     // semicolon
  | `:`     // colon
  | `,`     // comma
  | `.`     // dot
  | `...`   // ellipsis
  | `::`    // double colon, scope operator
  | `->`    // arrow
    ;

Operator :
  | '`'     // backtick
  | `!`     // exclamation mark
  | `@`     // at sign
  | `$`     // dollar sign
  | `%`     // percent sign
  | `~`     //tilde
  | `^`     // caret
  | `&`     // ampersand
  | `*`     // asterisk, multiplication operator
  | `-`     // minus sign, subtraction operator
  | `=`     // equals sign, assignment operator
  | `+`     // plus sign, addition operator
  | `|`     // pipe
  | `<`     // less-than sign, less-than operator
  | `>`     // greater-than sign, greater-than operator
  | `/`     // slash, division operator
  | `?`     // question mark
  | `==`    // double-equals, equal-to operator
  | `!=`    // not-equal operator
  | `%=`    // modulo-assign operator
  | `+=`    // add-assign operator
  | `^=`    // xor-assign operator
  | `&=`    // and-assign operator
  | `*=`    // multiply-assign operator
  | `-=`    // subtract-assign operator
  | `|=`    // or-assign operator
  | `<=`    // less-than-or-equal-to operator
  | `>=`    // greater-than-or-equal-to operator
  | `/=`    // divide-assign operator
  | `&&`    // and-and operator
  | `--`    // decrement operator
  | `++`    // increment operator
  | `||`    // or-or operator
  | `<<`    // left shift operator
  | `>>`    // right shift operator
    ;

```

Associating Trivia With Tokens [lex.token.trivia]
------------------------------

Issue: We should define lexing in terms of producing a sequence of tokens-with-trivia instead of just lexemes.

Each token in a source unit may be prededed or followed by trivia:

```.lexical
TokenWithTrivia =
  LeadingTrivia Token TrailingTrivia

LeadingTrivia = Trivia*

TrailingTrivia = (Trivia - LineBreak)* LineBreak?
```

A compiler implementation must use the "maximal munch" rule when lexing, so that each *TokenWithTrivia* includes as many characters of *TrailingTrivia* as possible.

Note: Informally, the trailing trivia of a token is all the trivia up to the next line break, the next token, or the end of the source unit - whichever comes first.
The leading trivia of a token starts immediately after the trailing trivia of the preceding token, or at the beginning of the file if there is no preceding token.

Lexing decomposes a source unit into a sequence of zero or more tokens with trivia, as well as zero or more pieces of trivia that do not belong to any token:

```.lexical
LexicalSourceUnit =
  TokenWithTrivia* Trivia*
```

The terminals of the context-free grammar should be understood to be tokens with trivia.
A reference to a nonterminal _N_ in productions for the abstract syntax should be understood as matching the *TokenWithTrivia* rule, restricted to the case where the contained token is _N_.

Issue: We should probably make a dedicated **EOF** be part of the alphabet for input source units, so that the *LexicalSourceUnit* can be simpler to define.
E.g., "The alphabet of the lexical grammar comprises all Unicode scalar values, as well as the unique meta-value **EOF**."