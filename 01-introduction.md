Introduction
============

Scope
-----

This document is a reference for the Slang programming language.

Slang is language primarily designed for use in *shader programming*: performance oriented GPU programming for real-time graphics.

Conformance
-----------

This document is *not* intended to serve as a formal specification of Slang, but it *is* intended to document the language with a high level of rigor.
As such, the text often makes statements *as if* it is a specification, and defines behaviors expected of a conforming implementation.

The Slang compiler *implementation* may deviate from the language as documented here, in a few key ways:

* The implementation is necessarily imperfect, and can have bugs

* The implementation may not fully support constructs documented here, or their capabilities may not be as complete as what is documented

* The implementation may support certain constructs that are experimental, deprecated, or are otherwise intentionally undocumented

Where possible, this document will call out known deviations between the language as defined here and the implementation in the compiler.

Document Conventions
--------------------

The key words **must**, **must not**, **required**, **shall**, **shall not**, **should**, **should not**, **recommended**, **may**, and **optional** in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

The word "descriptive" in this document is to be interpreted as synonymous with "non-normative."

### Typographical Conventions

This document makes use of the following conventions to improve readability:

* When a term is introduced and defined, it will be in italics. For example: a *duck* is something that looks like a duck and quacks like a duck.

* Code fragments in Slang or other programming languages use a fixed-width font. For example: `a + b`.

* References to language keywords are in bold. For example: **`if`**.

### Callouts

This document uses a few kinds of *callouts*, which start bold word indicating the kind of callout. For example, the following is a note:

> **Note**: Notes are rendered like this.

The kinds of callouts used in this document, are:

* **Example**s provide non-normative examples of how to use language constructs, or of their semantics.

* **Incomplete** callouts are non-normative markers of places where this document is lacking important information, or may be inaccurate.

* **Legacy** callouts are described below.

* **Limitation** callouts are used to provide non-normative discussion of how the Slang compiler implementation may deviate from the language as documented here.

* **Note**s give non-normative information that may help readers to understand and apply the normative information in the document.

* **Syntax** callouts are described below.

* **Warning**s give non-normative information about language rules or programming practices that may lead to surprising or unwanted behavior.

### Legacy Features

Some features of the Slang language are considered *legacy* features.
The language supports these constructs, syntax, etc. in order to facilitate compatibility with existing code in other GPU languages, such as HLSL.

**Legacy** callouts are used for the description of legacy features. These callouts are normative.

### Grammar Productions

The syntax and lexical structure of the language is described **Syntax** callouts using a notation similar to EBNF.

* Nonterminals have names in camel case, and are rendered in italics. E.g., *CallExpression*.

* Terminals in the syntax, both punctiation and keywords are rendered in a fixed-width font. E.g., `func`.

* A question mark as a suffix indicates that the given element is optional. E.g., *Expression*?

* An asterisk as a suffix indicates that a given element may be repeated zero or more times. E.g., *Modifier* *

* A plus as a suffix indicates that a given element may be repeated one or more times. E.g., *AccessorDeclaration*+

* Parentheses in plain text (not fixed-width) are used for grouping. E.g., *Expression* (`,` *Expression*)*

> **Incomplete**: Also need conventions for how code points are named in productions in the lexical structure.

The Slang Standard Library
--------------------------

Many constructs that appear to users of Slang as built-in syntax are instead defined as part of the *standard library* for Slang.
This document may, of neccessity, refer to constructs from the Slang standard library (e.g., the `Texture2D` type) that are not defined herein.

This document does not provide a normative definition of all of the types, functions, attributes, modifiers, capabilities, etc. that are defined in the Slang standard library.
The normative reference for standard-library constructs *not* defined in this document is the Slang Standard Library Reference.

> **Incomplete**: Need to turn that into a link.

In cases where a language construct is documented in *both* this language reference and the Standard Library Reference, the construct has all the capabilities and restrictions defined in either reference.
In cases where the two references disagree, there is a correctness issue in one or the other.

Normative References
--------------------

> **Incomplete**: This section should list any external documents/specifications/etc. that are necessary in order to correctly interpret the information in this reference.