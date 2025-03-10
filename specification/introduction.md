Introduction [intro]
=====================

Scope [intro.scope]
-----

This document is a specification for the Slang programming language.

Slang is language primarily designed for use in *shader programming*: performance oriented GPU programming for real-time graphics.

Conformance [intro.conformance]
-----------

This document aspires to specify the Slang language, and the behaviors expected of conforming implementations, with a high level of rigor.

The open-source Slang compiler *implementation* may deviate from the language as specified here, in a few key ways:

* The implementation is necessarily imperfect, and can have bugs.
* The implementation may not fully support constructs specified here, or their capabilities may not be as complete as what is required by the specification.
* The implementation may support certain constructs that are experimental, deprecated, or are otherwise intentionally unspecified (or even undocumented).

Where practical, this document will call out known deviations between the language as specified, and the current implementation in the open-source Slang compiler.

The Slang Standard Library [intro.stdlib]
--------------------------

Many constructs that appear to users of Slang as built-in syntax are instead defined as part of the _standard library_ for Slang.
This document may, of neccessity, refer to constructs from the Slang standard library (e.g., the `Texture2D` type) that are not defined herein.

This document does not provide a normative definition of all of the types, functions, attributes, modifiers, capabilities, etc. that are defined in the Slang standard library.
The normative reference for standard-library constructs not defined in this document is the Slang Standard Library Reference.

Issue: Need to turn that into a link.

In cases where a language construct is described in *both* this specification and the Standard Library Reference, the construct has all the capabilities and restrictions defined in either source.
In cases where the two sources disagree, there is a correctness issue in one or the other.

Document Conventions [intro.conventions]
--------------------

### Terminology [intro.conventions.terminology]

The key words **must**, **must not**, **required**, **shall**, **shall not**, **should**, **should not**, **recommended**, **may**, and **optional** in this document are to be interpreted as described in [RFC 2199](https://www.ietf.org/rfc/rfc2119.txt).

Uses of the words "descriptive" and "information" in this document are to be interpreted as synonymous with "non-normative."

### Typographical Conventions [intro.conventions.typographical]

This document makes use of the following conventions to improve readability:

* When a term is introduced and defined, it will be in bold and italics. For example: a **duck** is something that looks like a *duck* and quacks like a *duck*.

* Code fragments in Slang or other programming languages use a fixed-width font. For example: `a + b`.

### Meta-Values and Meta-Types [intro.conventions.meta]

The specification defines a variety of concepts (e.g., grammar productions, types, and values) that are used to define the static and dynamic semantics of Slang code.
In many cases, these concepts exist only to serve this specification, and cannot be directly named or manipulated in Slang code itself.

We refer to these abstract concepts as **meta-values**. All *meta-values* are themselves *values*.
A **meta-type** is a *type* with instances that are all *meta-values*.

This specification may introduce a named *meta-value* in prose, or via grammar rules.
When a *meta-value* is introduced or referenced, it name may be rendered using one of the following conventions:

* A *meta-value* name may be rendered in italics and *UpperCamelCase*. E.g., <a lt="if statement">*IfStatement*</a>, <a lt="unit type">*UnitType*</a>

* When a *meta-value* corresponds to a named declaration, keyword, attribute, or other entity that can be referenced in Slang code, its name may be rendered in a fixed-width font. E.g., the <a lt="unit type">`Unit`</a> type.

* In prose, a *meta-value* name may be rendered as ordinary English, possibly with words that reference Slang language keywords in a fixed-width font. E.g., <a lt="if statement">`if` statement</a>, <a lt="unit type">unit type</a>.

In each case, the concept being referenced is the same; for example, the references <a lt="unit type">*UnitType*</a>, <a lt="unit type">`Unit`</a>, and <a lt="unit type">unit type</a> all refer to the same definition.

### Meta-Variables [intro.conventions.meta.var]

A **meta-variable** is a placeholder name that may represents an unknown *meta-value* of some *meta-type*.
A *meta-variable* is rendered in italics, and must either be in *lowerCamelCase*, or consist of a single letter (either upper- or lower-case).
For example, text might introduce a *meta-variable* named <var ignore>e</var> that represents an unknown *expression*.

The text that introduces a *meta-variable* may explicitly specify the *type* of that variable.
When the name of a *meta-variable* matches the name of a *type*, then it is implicitly a variable of the corresponding type.

### Patterns [intro.conventions.meta.pattern]

When introducing a *meta-value* that is an instance of some nonterminal in a grammar, this specification may express the value as a **meta-pattern**: a sequence of terminals and *meta-variables* that match the corresponding nonterminal.
For example, we might refer to "the *block statement* `{` _stmts_ `}`", implicitly introducing the *meta-variable* _stmts_ of type _Statements_.

The type of a *meta-variable* in a *meta-pattern* may be explicitly specified in prose, or it may be implicit from the position of the *meta-variable* and the grammar production being matched.

A pattern may also specify a type for a *meta-variable* by immediately suffixing the *meta-variable* with a colon and a *type* in _UpperCamelCase_.
For example, a reference to "the *block statement* `{` _stmts_:_Statements_ `}`" makes the type of _stmts_ more explicit.

### Characteristics of Meta-Values [intro.conventions.meta.characteristic]

A **characteristic** of a *meta-value* is a named property, attribute, or quality of that value.

### Callouts [intro.conventions.callouts]

This document uses a few kinds of **callouts**, which start bold word indicating the kind of callout. For example, the following is a note:

Note: Notes are rendered like this.

The kinds of *callouts* used in this document are:

<div class="issue">List the cases we end up using here</div>

### Traditional and Legacy Features [intro.conventions.traditional]

Some features of the Slang language are considered **traditional** or **legacy** features.
The language supports these constructs, syntax, etc. in order to facilitate compatibility with existing code in other GPU languages, such as HLSL.

Sections that introduce *traditional* or *legacy* features begin with a callout indicating the status of those features.

*Legacy* features are those that undermine the consistency and simplicity of the language, and complicate its implementation, for little practical benefit.
These features should be considered as candidates for removal in future versions of this specification.
Legacy features are optional, unless otherwise indicated.

*Traditional* features are those that may not represent the long-term design trajectory of the language, but that offer significant practical benefit to users of the language.
Traditional features are required, unless otherwise indicated.

## Context-Free Grammars [intro.grammar]

This specification uses *context-free grammars* to define:

* The lexical syntax of Slang

* The abstract syntax of Slang

* Representations for *meta-values* used in this specification

A **context-free grammar** consists of an alphabet of **terminal** symbols, and zero or more *productions*.
A **production** consists of a *left-hand side* and a *right-hand side*.

The **left-hand side** of a *production* consists of a single *nonterminal* symbol.
A *production* is **for** the *nonterminal* on its *left-hand side*.

The **right-hand side** of a *production* consists of an ordered sequence of zero or more *nonterminal* and *terminal* symbols.

A **chain production** is a *production* that has exactly one *nonterminal* symbol on its *right-hand side*.

Note: a chain production can have zero or more *terminals* on its *right-hand side*, in addition to the single *nonterminal*.

A **trivial production** is a *chain production* that has zero *terminals* on its *right-hand side*.
A *nonterminal* is abstract if all of the productions for that nonterminal are trivial productions.

A **nonterminal** of a *context-free grammar* is a *meta-type*.
An instance of a non-abstract *nonterminal* is the result of matching a *production* for that *nonterminal*, and consists of a sequence of matches for each of the terms on the *right-hand side* of that *production*.

An instance of an abstract *nonterminal* is an instance of one of the nonterminals on the right-hand side of one of its productions.

Note: If there exists a trivial production for *nonterminal* _A_ that has a *right-hand side* consisting of *nonterminal* _B_, then _B_ is a subtype of _A_.


### Notation [intro.grammar.notation]

This specification uses a notation inspired by Extended Backus-Naur Form to define *context-free grammars*.
The notation uses the following notational conventions:

#### Productions [intro.grammar.notation.production]

Issue: Need to write this up.

#### Terminals [intro.grammar.notation.terminal]

Terminals in the lexical and abstract syntax are rendered in a fixed-width font: e.g., `func`.

Terminals used in grammar rules for *meta-values* are rendered in bold: e.g., **extends**.

#### Nonterminals [intro.grammar.notation.nonterminal]

Nonterminals in grammar rules are named in upper camel case, and rendered in italics: e.g., *CallExpression*.
This convention is consistent with the notational conventions for *meta-types*.

A nonterminal on the right-hand side of a production may introduce a name for that nonterminal in lower camel case, using the same syntax as for *meta-variables* in *meta-patterns*. E.g., _base_ : _TypeExpression_.

#### Terminals [intro.grammar.notation.alternative]

A plain-text vertical bar is used to separate alternatives. E.g., _IntegerLiteral_ | _FloatingPointLiteral_

#### Optionals [intro.grammar.notation.optional]

A plain-text question mark (?) as a suffix indicates that the given element is optional. E.g., _Expression_?

#### Sequences [intro.grammar.notation.sequence]

A plain-text asterisk (\*) as a suffix indicates that a given element may be repeated zero or more times. E.g., _Modifier_ \*

A plain-text plus sign (+) as a suffix indicates that a given element may be repeated one or more times. E.g., _AccessorDeclaration_+

As an additional convenience, when an asertisk or plus is applied to a grouping where the last item in that grouping is a terminal consisting of a single comma (`,`), that phrase represents a repetition of *comma-separated* elements.

#### Grouping [intro.grammar.notation.grouping]

Plain-text parentheses are used for grouping. E.g., *Expression* (`,` *Expression*)

#### Exclusion [intro.grammar.notation.exclusion]

A plain-text minus (-) used as an infix operator matches input that matches its left operand but not its right operand.

#### Characteristics [intro.grammar.notation.characteristics]

A match for a *production* will have zero or more characteristics introduced by the *right-hand side* of that production.

If the *right-hand side* of a non-trivial *production* _P_ includes

* exactly one occurence of *nonterminal* _N_, or

* a *nonterminal* _N_ with a label _L_

then a match of that production has a characteristic with a name and type derived as follows:

* Let _label_ be either _L_, if it is present, or the name of _N_ otherwise

* If _N_ appears under a sequence (marked with * or +), then the type of the characteristic is **List<** _N_ **>**, and the name of the characteristic is the plural of _label_

* Otherwise, if _N_ appears under a "?", then the type of the characteristic is **Optional<** _N_ **>**, and the name of the characteristic is _label_

* Otherwise, the type of the characteristic is _N_, and the name of the characteristic is _label_

<div class="note">
As an example, given a grammar production like:

```.syntax
Boat := mainMast:Mast Mast* Sail* Hold?
```

Then a match for this production would be a boat with the following characteristics:

* its **main mast**, of type *Mast*
* its **sails**, a list of *Sail*s
* its **hold**, an <span class=allow-2119>optional</span> *Hold*

The term "Mast*" in the right-hand side of the production does not introduce a characteristic, because it is not the sole occurence of the non-terminal *Mast* on the right-hand side.
</div>
