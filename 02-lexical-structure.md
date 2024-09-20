Lexical Structure
=================

This chapter describes how a source unit is decomposed into a sequence of tokens.

Source Units
------------

A _source unit_ comprises a sequence of zero or more characters.
For the purposes of this document, a _character_ is defined as a Unicode scalar value.

> **Note**: A Unicode scalar value is a Unicode code point that is not a surrogate code point.

> **TODO**: Need normative reference to the Unicode standard.

Implementations *may* accept source units stored as files on disk, buffers in memory, or any appropriate implementation-specified means.

Encoding
--------

Implementations *must* support source units encoded using UTF-8, if they support any encoding of source units as byte sequences.
Implementations *should* default to the UTF-8 encoding for all text input/output.
Implementations *may* support additional implementation-specified encodings.

Phases
------

Lexical processing of a source unit proceeds _as if_ the following steps are executed in order:

1. Line numbering (for subsequent diagnostic messages) is noted based on the locations of line breaks

2. Escaped line breaks are eliminated. No new characters are inserted to replace them. Any new escaped line breaks introduced by this step are not eliminated.

3. Each comment is replaced with a single space (U+0020)

4. The source unit is _lexed_ into a sequence of tokens according to the lexical grammar in this chapter

5. The lexed sequence of tokens is _preprocessed_ to produce a new sequence of tokens (Chapter 3)

The final token sequence produced by this process is used as input to subsequent phases of compilation.

Whitespace
----------

_Whitespace_ consists of horizontal whitespace and line breaks.

_Horizontal whitespace_ consists of space (U+0020) and horizontal tab (U+0009).

### Line Breaks

A _line break_ consists of a line feed (U+000A), carriage return (U+000D) or a carriage return followed by a line feed (U+000D, U+000A).

> **Legacy**:
>
> An _escaped line break_ is a backslack (`\`, U+005C) follow immediately by a line break.
>
> Before subsequent processing described in this chapter, all escaped line breaks are removed from a source unit.
> If new escaped line breaks are introduced by this step, they are not removed.

A source unit is split into _lines_ separated by line breaks.

> **Note**: Line breaks are used as line separators rather than terminators; it is not necessary for a source unit to end with a line break.

Comments
--------

A _comment_ is either a line comment or a block comment.

A _line comment_ comprises two forward slashes (`/`, U+002F) followed by zero or more characters that do not contain a line break.
A line comment extends up to, but does not include, a subsequent line break or the end of the source unit.

A _block comment_ begins with a forward slash (`/`, U+002F) followed by an asterisk (`*`, U+0052). 
A block comment is terminated by the next instance of an asterisk followed by a forward slash (`*/`).
A block comment contains all characters between where it begins and where it terminates, including any line breaks.
Block comments do not nest.
It is an error if a block comment that begins in a source unit is not terminated in that source unit.

> **Example**:
>
> ```hlsl
> // a line comment
> /* a block comment */
> ```

Identifiers
-----------

An _identifier_ begins with an uppercase or lowercase ASCII letter (`A` through `Z`, `a` through `z`), or an underscore (`_`).
After the first character, ASCII digits (`0` through `9`) may also be used in an identifier.

> **Syntax**:
>
> *Identifer* ::= *IdentifierStart* *IdentiferContinue* *
>
> *IdentifierStart* ::= `A`-`Z` | `a` - `z` | `_`
> *IdentifierContinue* ::= *IdentifierStart* | `0`-`9`

The identifier consistent of a single underscore (`_`) is reserved by the language and must not be used by programs as a name in a declaration or binding.

> **Note**:
>
> There are no other fixed keywords or reserved words recognized by the lexical grammar.

Literals
--------

### Numeric Literals

A _numeric literal_ is either an integer literal or a floating-point literal.

A _radix specifier_ is one of:

* `0x` or `0X` to specify a _hexadecimal literal_ (radix 16)
* `0b` or `0B` to specify a _binary literal_ (radix 2)

When no radix specifier is present, a numeric literal is a _decimal literal_ (radix 10).

> Note:
>
> Octal literals (radix 8) are not supported.
> A `0` prefix on an integer literal does *not* specify an octal literal as it does in C.
> Implementations *may* warn on integer literals with a `0` prefix in case users expect C behavior.

The grammar of the _digits_ for a numeric level depend on its radix, as follows:

* The digits of a decimal literal may include `0` through `9`
* The digits of a hexadecimal literal may include `0` through `9`, the letters `A` through `F` and `a` through `f`. The letters represent digit values 10 through 15.
* The digits of a binary literal may include `0` and `1`

Digits for all numeric literals may also include `_`, which are ignored and have no semantic impact.

A _numeric literal suffix_ consists of any sequence of characters that would be a valid identifier, that does not start with `e` or `E`.

> **Note**:
>
> A leading `-` (U+002D) before a numeric literal is *not* part of the literal, even if there is no whitespace separating the two.

#### Integer Literals

An _integer literal_ consists of an optional radix specifier followed by digits and an optional numeric literal suffix.

The suffix on an integer literal may be used to indicate the desired type of the literal:

* A `u` suffix indicates the `UInt` type
* An `l` or `ll` suffix indicates the `Int64` type
* A `ul` or `ull` suffix indicates the `UInt64` type

#### Floating-Point Literals

A _floating-point literal_ consists of either

* An optional radix specifier, followed by digits, followed by a `.` (U+002E), followed by optional digits, an optional exponent, and an optional numeric literal suffix.
* An optional radix specifier, followed by digits, an exponent, and an optional numeric literal suffix.
* A `.` (U+002E) followed by digits, an optional exponent, and an optional numeric literal suffix.

A floating-point literal may only use dexicmal or hexadecimal radix.

The _exponent_ of a floating-pointer literal consists of either `e` or `E`, followed by an optional _sign_ of `+` or `-`, followed by decimal digits.

### Text Literals

> **Incomplete**: Need to document supported escape sequences.

#### String Literals

A _string literal_ consists of a sequence of characters enclosed between two `"`, with the constraint that any `"` within the sequence must be escaped with `\`.

#### Character Literals

A _character literal_ consists of a sequence of characters enclosed between two `'`, with the constraint that any `'` within the sequence must be escaped with `\`.

The sequence of characters within a character literal must represent a single character.

Operators and Punctuation
-------------------------

The following table defines tokens that are used as operators and punctuation in the syntax.
When a given sequence of characters could be interpreted as starting with more than one of the following tokens, the longest matching token is used.
The name or names given to tokens by this table may be used in the rest of this document to refer to those tokens.

| Token | Name(s) |
|-------|------|
|   `` ` `` | backtick |
| `~` | tilde |
| `!` | exclamation mark |
| `@` | at sign |
| `$` | dollar sign |
| `%` | percent sign |
| `^` | caret |
| `&` | ampersand |
| `*` | asterisk, multiplication operator |
| `(` | left parenthesis |
| `)` | right parenthesis |
| `-` | minus sign, subtraction operator |
| `=` | equals sign, assignment operator |
| `+` | plus sign, addition operator |
| `[` | left square bracket, opening square bracket |
| `]` | right square bracket, closing square bracket |
| `{` | left curly brace, opening curly brace |
| `}` | right curly brace, closing curly brace |
| `|` | pipe |
| `;` | semicolon |
| `:` | colon |
| `,` | comma |
| `.` | dot |
| `<` | less-than sign, less-than operator |
| `>` | greater-than sign, greater-than operator |
| `/` | slash, division operator |
| `?` | question mark |
| `==` | double-equals, equal-to operator |
| `!=` | not-equal operator |
| `%=` | modulo-assign operator |
| `+=` | add-assign operator |
| `^=` | xor-assign operator |
| `&=` | and-assign operator |
| `*=` | multiply-assign operator |
| `-=` | subtract-assign operator |
| `|=` | or-assign operator |
| `<=` | less-than-or-equal-to operator |
| `>=` | greater-than-or-equal-to operator |
| `/=` | divide-assign operator |
| `&&` | and-and operator |
| `--` | decrement operator |
| `++` | increment operator |
| `||` | or-or operator |
| `<<` | left shift operator |
| `>>` | right shift operator |
| `...` | ellipsis |
| `::` | double colon, scope operator |
| `->` | arrow |
