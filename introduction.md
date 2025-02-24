Introduction {#intro}
=====================

Scope {#intro.scope}
-----

This document is a specification for the Slang programming language.

Slang is language primarily designed for use in *shader programming*: performance oriented GPU programming for real-time graphics.

Conformance {#intro.conformance}
-----------

This document aspires to specify the Slang language, and the behaviors expected of conforming implementations, with a high level of rigor.

The open-source Slang compiler *implementation* may deviate from the language as specified here, in a few key ways:

* The implementation is necessarily imperfect, and can have bugs.
* The implementation may not fully support constructs specified here, or their capabilities may not be as complete as what is required by the specification.
* The implementation may support certain constructs that are experimental, deprecated, or are otherwise intentionally unspecified (or even undocumented).

Where practical, this document will call out known deviations between the language as specified, and the current implementation in the open-source Slang compiler.

<!-->

Document Conventions {#intro.conventions}
--------------------


```

The key words \textbf{must}, \textbf{must not}, \textbf{required}, \textbf{shall}, \textbf{shall not}, \textbf{should}, \textbf{should not}, \textbf{recommended}, \textbf{may}, and \textbf{optional} in this document are to be interpreted as described in \href{https://www.ietf.org/rfc/rfc2119.txt}{RFC 2119}.

The word "descriptive" in this document is to be interpreted as synonymous with "non-normative."
```

### Typographical Conventions ### {#intro.conventions.typographical}

```
This document makes use of the following conventions to improve readability:


    \item{When a term is introduced and defined, it will be in italics. For example: a <dfn>duck</dfn> is something that looks like a duck and quacks like a duck.}
    \item{Code fragments in Slang or other programming languages use a fixed-width font. For example: \code{a + b}.}
      * {References to language keywords are additionally rendered in bold. For example: `if`}

```

### Callouts ### {#intro.conventions.callouts}

```

This document uses a few kinds of <dfn>callouts</dfn>, which start bold word indicating the kind of callout. For example, the following is a note:

Note: Notes are rendered like this.

The kinds of callouts used in this document are:


    \item{\CalloutName{Example}s provide non-normative examples of how to use language constructs, or of their semantics.}
    \item{\CalloutName{Incomplete} callouts are non-normative markers of places where this document is lacking important information, or may be inaccurate.}
    \item{\CalloutName{Legacy} callouts are described below.}
    \item{\CalloutName{Limitation} callouts are used to provide non-normative discussion of how the Slang compiler implementation may deviate from the language as specified here.}
    \item{\CalloutName{Note}s give non-normative information that may help readers to understand and apply the normative information in the document.}
    \item{\CalloutName{Rationale} callouts provide non-normative explanations about *why* certain constructs, constraints, or rules are part of the language.}
    \item{\CalloutName{Syntax} callouts are described below.}
    \item{\CalloutName{Warning}s give non-normative information about language rules or programming practices that may lead to surprising or unwanted behavior.}

```

### Legacy Features ### {#intro.conventions.legacy}

```

Some features of the Slang language are considered <dfn>legacy</dfn> features.
The language supports these constructs, syntax, etc. in order to facilitate compatibility with existing code in other GPU languages, such as HLSL.

\CalloutName{Legacy} callouts are used for the description of legacy features. These callouts are normative.
```

### Grammar Productions ### {#intro.conventions.grammar}

```

The syntax and lexical structure of the language is described \textbf{Syntax} callouts using a notation similar to EBNF.


    \item{Nonterminals have names in camel case, and are rendered in italics. E.g., CallExpression}.}
    \item{Terminals in the syntax, both punctiation and keywords are rendered in a fixed-width font. E.g., `func`.}
    \item{A question mark as a suffix indicates that the given element is optional. E.g., Expression?}
    \item{An asterisk as a suffix indicates that a given element may be repeated zero or more times. E.g., Modifier*}
    \item{A plus as a suffix indicates that a given element may be repeated one or more times. E.g., AccessorDeclaration}+}
    \item{Parentheses in plain text (not fixed-width) are used for grouping. E.g., Expression (`,` Expression)}


Issue: Also need conventions for how code points are named in productions in the lexical structure.    
```

</-->

The Slang Standard Library {#intro.stdlib}
--------------------------

Many constructs that appear to users of Slang as built-in syntax are instead defined as part of the _standard library_ for Slang.
This document may, of neccessity, refer to constructs from the Slang standard library (e.g., the `Texture2D` type) that are not defined herein.

This document does not provide a normative definition of all of the types, functions, attributes, modifiers, capabilities, etc. that are defined in the Slang standard library.
The normative reference for standard-library constructs not defined in this document is the Slang Standard Library Reference.

Issue: Need to turn that into a link.

In cases where a language construct is described in *both* this specification and the Standard Library Reference, the construct has all the capabilities and restrictions defined in either source.
In cases where the two sources disagree, there is a correctness issue in one or the other.
