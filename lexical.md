Lexical Structure {#lex}
=================

This chapter describes how a source unit is decomposed into a sequence of lexemes.

Source Units {#lex.source-unit}
------------

A <dfn>source unit</dfn> comprises a sequence of zero or more [[=characters=]].
For the purposes of this document, a <dfn>character</dfn> is defined as a [[!Unicode]] scalar value.

Note: A Unicode scalar value is a Unicode code point that is not a surrogate code point.

Implementations may accept source units stored as files on disk, buffers in memory, or any appropriate implementation-specified means.

Encoding {#lex.encoding}
--------

Implementations must support source units encoded using UTF-8, if they support any encoding of source units as byte sequences.

Implementations should default to the UTF-8 encoding for all text input/output.

Implementations may support additional implementation-specified encodings.

Phases {#lex.phase}
------

Lexical processing of a [[=source unit=]] proceeds *as if* the following steps are executed in order:

1. Line numbering (for subsequent diagnostic messages) is noted based on the locations of [[=line breaks=]]

2. [[=Escaped line breaks=]] are eliminated. No new [[=characters=]] are inserted to replace them. Any new [[=escaped line breaks=]] introduced by this step are not eliminated.

3. Each comment is replaced with a single space (U+0020)

4. The source unit is *lexed* into a sequence of [[=tokens=]] according to the lexical grammar in this chapter

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

A source unit is split into <dfn>lines</dfn>: non-empty sequences of [[=characters=]] separated by [[=line breaks=]].

Note: Line breaks are used as line separators rather than terminators; it is not necessary for a source unit to end with a line break.

#### Comments #### {#comment}

A <dfn>comment</dfn> is either a [[=line comment=]] or a [[=block comment=]].

A <dfn>line comment</dfn> comprises two forward slashes (`/`, U+002F) followed by zero or more characters that do not contain a [[=line break=]].
A [[=line comment=]] extends up to, but does not include, a subsequent [[=line break=]] or the end of the source unit.

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

A \SpecDef{radix specifier} is one of:

\begin{enumerate}
    \item{\Char{0x} or \Char{0X} to specify a \SpecDef{hexadecimal literal} (radix 16)}
    \item{\Char{0b} or \Char{0B} to specify a \SpecDef{binary literal} (radix 2)}
\end{enumerate}
When no radix specifier is present, a numeric literal is a \SpecDef{decimal literal} (radix 10).

/begin{Note}
Octal literals (radix 8) are not supported.
A \Char{0} prefix on an integer literal does *not* specify an octal literal as it does in C.
Implementations \emph{may} warn on integer literals with a \Char{0} prefix in case users expect C behavior.
/end{Note}

The grammar of the \SpecDef{digits} for a numeric level depend on its radix, as follows:

\begin{enumerate}
    \item{The digits of a decimal literal may include \Char{0} through \Char{9}}
    \item{The digits of a hexadecimal literal may include \Char{0} through \Char{9}, the letters \Char{A} through \Char{F} and \Char{a} through \Char{f}. The letters represent digit values 10 through 15.}
    \item{The digits of a binary literal may include \Char{0} and \Char{1}}
\end{enumerate}

Digits for all numeric literals may also include \lstinline{_}, which are ignored and have no semantic impact.

A \SpecDef{numeric literal suffix} consists of any sequence of characters that would be a valid identifier, that does not start with \Char{e} or \Char{E}.

\begin{Note}
A leading \Char{-} (U+002D) before a numeric literal is *not* part of the literal, even if there is no whitespace separating the two.
\end{Note}

\SubSubSection{Integer Literals}{int}

An \SpecDef{integer literal} consists of an optional radix specifier followed by digits and an optional numeric literal suffix.

The suffix on an integer literal may be used to indicate the desired type of the literal:

\begin{enumerate}
    \item{A \Char{u} suffix indicates the \code{UInt} type}
    \item{An \Char{l} or \Char{ll} suffix indicates the \code{Int64} type}
    \item{A `ul` or `ull` suffix indicates the \code{UInt64} type}
\end{enumerate}

\SubSubSection{Floating-Point Literals}{float}

A \SpecDef{floating-point literal} consists of either

\begin{enumerate}
    \item{An optional radix specifier, followed by digits, followed by a \Char{.} (U+002E), followed by optional digits, an optional exponent, and an optional numeric literal suffix.}
    \item{An optional radix specifier, followed by digits, an exponent, and an optional numeric literal suffix.}
    \item{A \Char{.} (U+002E) followed by digits, an optional exponent, and an optional numeric literal suffix.}
\end{enumerate}

A floating-point literal may only use dexicmal or hexadecimal radix.

The \SpecDef{exponent} of a floating-pointer literal consists of either \Char{e} or \Char{E}, followed by an optional \SpecDef{sign} of \Char{+} or \Char{-}, followed by decimal digits.

### Text Literals ### {#lex.lit.text}

\begin{Incomplete}
Need to document supported escape sequences.
\end{Incomplete}

\SubSubSection{String Literals}{string}

A \SpecDef{string literal} consists of a sequence of characters enclosed between two \Char{"}, with the constraint that any \Char{"} within the sequence must be escaped with \Char{\\}.

\SubSubSection{Character Literals}{char}

A \SpecDef{character literal} consists of a sequence of characters enclosed between two \Char{'}, with the constraint that any \Char{'} within the sequence must be escaped with \Char{\\}.

The sequence of characters within a character literal must represent a single character.

Operators and Punctuation {#lex.punctuation}
-------------------------

The following table defines tokens that are used as operators and punctuation in the syntax.
When a given sequence of characters could be interpreted as starting with more than one of the following tokens, the longest matching token is used.
The name or names given to tokens by this table may be used in the rest of this document to refer to those tokens.

\begin{tabular}{ |c|c| }
  \hline
  Token & Name(s) \\
  \hline
  \Char{`} & backtick \\
  \textasciitilde & tilde \\
  \Char{!} & exclamation mark \\
  \Char{@} & at sign \\
  \$ & dollar sign \\
  \Char{\%} & percent sign \\
  \^{} & caret \\
  \Char{&} & ampersand \\
  \Char{*} & asterisk, multiplication operator \\
  \Char{(} & left parenthesis \\
  \Char{)} & right parenthesis \\
  \Char{-} & minus sign, subtraction operator \\
  \Char{=} & equals sign, assignment operator \\
  \Char{+} & plus sign, addition operator \\
  \Char{[} & left square bracket, opening square bracket \\
  \Char{]} & right square bracket, closing square bracket \\
  \Char{\{} & left curly brace, opening curly brace \\
  \Char{\}} & right curly brace, closing curly brace \\
  \textbar & pipe \\
  \Char{;} & semicolon \\
  \Char{:} & colon \\
  \Char{,} & comma \\
  \Char{.} & dot \\
  \Char{<} & less-than sign, less-than operator \\
  \Char{>} & greater-than sign, greater-than operator \\
  \Char{/} & slash, division operator \\
  \Char{?} & question mark \\
  \Char{==} & double-equals, equal-to operator \\
  \Char{!=} & not-equal operator \\
  \Char{\%=} & modulo-assign operator \\
  \Char{+=} & add-assign operator \\
  \^{}\Char{=} & xor-assign operator \\
  \Char{&=} & and-assign operator \\
  \Char{*=} & multiply-assign operator \\
  \Char{-=} & subtract-assign operator \\
  \textbar\Char{=} & or-assign operator \\
  \Char{<=} & less-than-or-equal-to operator \\
  \Char{>=} & greater-than-or-equal-to operator \\
  \Char{/=} & divide-assign operator \\
  \Char{&&} & and-and operator \\
  \Char{--} & decrement operator \\
  \Char{++} & increment operator \\
  \textbar\textbar & or-or operator \\
  \Char{<<} & left shift operator \\
  \Char{>>} & right shift operator \\
  \Char{...} & ellipsis \\
  \Char{::} & double colon, scope operator \\
  \Char{->} & arrow \\
  \hline
\end{tabular}
