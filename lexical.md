Lexical Structure {#lex}
=================

This chapter describes how a [=source unit=] is decomposed into a sequence of [[=lexemes=]].

Source Units {#lex.source-unit}
------------

A <dfn>source unit</dfn> comprises a sequence of zero or more [[=characters=]].
For the purposes of this document, a <dfn>character</dfn> is defined as a [[!Unicode]] scalar value.

Note: A Unicode scalar value is a Unicode code point that is not a surrogate code point.

Implementations may accept [=source units=] stored as files on disk, buffers in memory, or any appropriate implementation-specified means.

Encoding {#lex.encoding}
--------

Implementations must support [=source units=] encoded using UTF-8, if they support any encoding of [=source units=] as byte sequences.

Implementations should default to the UTF-8 encoding for all text input/output.

Implementations may support additional implementation-specified encodings.

Phases {#lex.phase}
------

Lexical processing of a [[=source unit=]] proceeds *as if* the following steps are executed in order:

1. Line numbering (for subsequent diagnostic messages) is noted based on the locations of [[=line breaks=]]

2. [[=Escaped line breaks=]] are eliminated. No new [[=characters=]] are inserted to replace them. Any new [[=escaped line breaks=]] introduced by this step are not eliminated.

3. Each comment is replaced with a single space (U+0020)

4. The [=source unit=] is *lexed* into a sequence of [[=tokens=]] according to the lexical grammar in this chapter

5. The lexed sequence of tokens is [[=preprocessed=]] to produce a new sequence of tokens

The final [[=token=]] sequence produced by this process is used as input to subsequent phases of compilation.

Lexemes {#lex.lexeme}
-------

A <dfn>lexeme</dfn> is a contiguous sequence of characters in a single [[=source unit=]].

<dfn>Lexing</dfn> is the process by which an implementation decomposes a [[=source unit=]] into zero or more non-overlapping [[=lexemes=]].

Every [[=lexeme=]] is either a [[=token=]] or it is [[=trivia=]].

```.lexical
Lexeme :
  Token
  | Trivia
  ;
```

### Trivia ### {#trivia}

<dfn>Trivia</dfn> are [[=lexemes=]] that do not appear in the abstract syntax; they are only part of the lexical grammar.
The presence or absence of [[=trivia=]] in a sequence of [[=lexemes=]] has no semantic impact, except where specifically noted in this specification.

```.lexical
Trivia :
  Whitespace
  | Comment
  ;
```

#### Whitespace #### {#whitespace}

<dfn>Whitespace</dfn> consists of [[=horizontal whitespace=]] and [[=line breaks=]].

```.lexical
Whitespace :
  HorizontalSpace
  | LineBreak
  ;
```

<dfn>Horizontal whitespace</dfn> consists of any sequence of space (U+0020) and horizontal tab (U+0009).

```.lexical
HorizontalSpace : (' ' | '\t')+ ;
```

##### Line Breaks ##### {#line}

A <dfn>line break</dfn> consists of a line feed (U+000A), carriage return (U+000D) or a carriage return followed by a line feed (U+000D, U+000A).

An <dfn>escaped line break</dfn> is a backslash (`\`, U+005C) follow immediately by a [[=line break=]].

A [=source unit=] is split into <dfn>lines</dfn>: non-empty sequences of [[=characters=]] separated by [[=line breaks=]].

Note: Line breaks are used as line separators rather than terminators; it is not necessary for a [=source unit=] to end with a line break.

#### Comments #### {#comment}

A <dfn>comment</dfn> is either a [[=line comment=]] or a [[=block comment=]].

A <dfn>line comment</dfn> comprises two forward slashes (`/`, U+002F) followed by zero or more characters that do not contain a [[=line break=]].
A [[=line comment=]] extends up to, but does not include, a subsequent [[=line break=]] or the end of the [=source unit=].

A <dfn>block comment</dfn> begins with a forward slash (`/`, U+002F) followed by an asterisk (`*`, U+0052). 
A [[=block comment=]] is terminated by the next instance of an asterisk followed by a forward slash (`*/`).
A [[=block comment=]] contains all [[=characters=]] between where it begins and where it terminates, including any [[=line breaks=]].

Note: [[=Block comments=]] do not nest.

It is an error if a [[=block comment=]] that begins in a [[=source unit=]] is not terminated in that [[=source unit=]].

### Tokens ### {#token}

<dfn>Tokens</dfn> are lexemes that are significant to the abstract syntax.

```.lexical
Token :
    Identifier
    | Literal
    | Operator
    | Puncutation
;
```

#### Identifiers #### {#ident}

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

The identifier consisting of a single underscore (`_`) is reserved by the language and must not be used by programs as a name in a declaration or binding.

Note: There are no other fixed keywords or reserved words recognized by the lexical grammar.

#### Literals #### {#literal}

```.lexical
Literal :
    NumericLiteral
    | TextLiteral
    ;
```

##### Numeric Literals ##### {#literal.numeric}

A <dfn>numeric literal</dfn> is either an [[=integer literal=]] or a [[=floating-point literal=]].

```.lexical
NumericLiteral :
    IntegerLiteral
    | FloatingPointLiteral
    ;
```

A <dfn>radix specifier</dfn> is one of:

* `0x` or `0X` to specify a <dfn>hexadecimal literal</dfn> (radix 16)
* `0b` or `0B` to specify a <dfn>binary literal</dfn> (radix 2)

When no radix specifier is present, a numeric literal is a <dfn>decimal literal</dfn> (radix 10).

Note:Octal literals (radix 8) are not supported.
A `0` prefix on an integer literal does *not* specify an octal literal as it does in C.
Implementations may warn on integer literals with a `0` prefix in case users expect C behavior.

The grammar of the <dfn>digits</dfn> for a numeric level depend on its radix, as follows:

* The digits of a decimal literal may include `0` through `9`
* The digits of a hexadecimal literal may include `0` through `9`, the letters `A` through `F` and `a` through `f`. The letters represent digit values 10 through 15.
* The digits of a binary literal may include `0` and `1`

Digits for all numeric literals may also include `_`, which are ignored and have no semantic impact.

A <dfn>numeric literal suffix</dfn> consists of any sequence of characters that would be a valid identifier, that does not start with `e` or `E`.

Note: A leading `-` (U+002D) before a numeric literal is *not* part of the literal, even if there is no whitespace separating the two.

#### Integer Literals #### {#int}

An <dfn>integer literal</dfn> consists of an optional radix specifier followed by digits and an optional numeric literal suffix.

The suffix on an integer literal may be used to indicate the desired type of the literal:

* A `u` suffix indicates the `UInt` type
* An `l` or `ll` suffix indicates the `Int64` type
* A `ul` or `ull` suffix indicates the `UInt64` type

#### Floating-Point Literals #### {#float}

A <dfn>floating-point literal</dfn> consists of either

* An optional radix specifier, followed by digits, followed by a `.` (U+002E), followed by optional digits, an optional exponent, and an optional numeric literal suffix.
* An optional radix specifier, followed by digits, an exponent, and an optional numeric literal suffix.
* A `.` (U+002E) followed by digits, an optional exponent, and an optional numeric literal suffix.

A floating-point literal may only use dexicmal or hexadecimal radix.

The <dfn>exponent</dfn> of a floating-pointer literal consists of either `e` or `E`, followed by an optional <dfn>sign</dfn> of `+` or `-`, followed by decimal digits.

### Text Literals ### {#lex.lit.text}

Issue: Need to document supported escape sequences.

#### String Literals #### {#string}

A <dfn>string literal</dfn> consists of a sequence of characters enclosed between two `"`, with the constraint that any `"` within the sequence must be escaped with `\`.

#### Character Literals #### {#char}

A <dfn>character literal</dfn> consists of a sequence of characters enclosed between two `'`, with the constraint that any `'` within the sequence must be escaped with `\`.

The sequence of characters within a character literal must represent a single character.

Operators and Punctuation {#lex.punctuation}
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
  | ```     // backtick
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
