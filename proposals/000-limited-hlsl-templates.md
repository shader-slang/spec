SP #000: Limited HLSL Templates
===============================

This proposal extends the HLSL-flavored dialect implemented by the Slang compiler with a deliberately limited form of `template` declaration.

A *limited HLSL template* is a parametric declaration whose body is checked after template arguments have been supplied.
It provides familiar HLSL/C++-style `template<...>` spelling and permits unconstrained, duck-typed bodies without requiring the author to first define Slang interfaces.

The templates proposed here are not C++ templates.
In particular, we do not propose that Slang should support template specialization (explicit or partial specialization), template partial ordering, argument-dependent lookup, or lazy checking of individual members of type template instantiations.
These choices are deliberate, both to keep the scope of the implementation in check, and also to ensure that limited templates are a coherent compatibility extension to Slang's HLSL-flavored dialect, rather than a pile of bolted-on C++-isms.

Status
------

Status: Design Review (Draft)

Implementation: None.

Author: Theresa Foley

Reviewer: TBD.

Background
----------

Slang's language design deliberately eschews templates and uses generics with interface constraints instead.
This choice is consistent with the goal for Slang to be a modern language that supports principled software engineering with explicit interfaces and strong ahead-of-time checks at module boundaries.

As the HLSL language has evolved to adopt C++-style templates, the principled design choice to use generics for Slang has created tension with another of the language's goals: ease of adoption for users of existing GPU shading languages such as HLSL and GLSL.
Developers who have adopted templates in their HLSL codebases now find that they cannot use Slang on their code as-is, resulting in a barrier to adoption.

Some developers even maintain code that they want to be able to compile as multiple different languages: some combination of Slang, HLSL, GLSL, C++, etc.
In such cases, a developer is limited to the "lowest common denominator" of what all the chosen languages support, and may prefer that all of the languages they use converge toward a common syntax and set of features (usually, such developers wish everything could be more like C++).

It is important to note that the Slang project has never promised that the Slang toolchain retain the ability to ingest HLSL code as the HLSL language continues to evolve; neither has the project ever proposed a roadmap toward convergence with C++.
The stated intent for the language was a divergent evolutionary path that heads toward capabilities more consistent with modern languages like Rust and Swift.
Indeed, the architecture of the Slang toolset and the design of many existing language features would make convergence with current HLSL or C++ comparable in complexity to a complete reboot of the project.

The question at hand is how much the Slang language design can or should bend to maintain an on-ramp from HLSL, without going past a point of diminishing returns.

Related Work
------------

In order to understand this proposal it is necessary to first understand how generics and templates differ.
While both language mechanisms apply to some overlapping use cases, and often use similar `<>`-based syntax, they differ in key ways that have far-reaching impact.

> Note:
> In the context of Slang, the application of a generic to arguments is typically referred to as "specialization" of the generic.
> In the C++ world, the corresponding concept is *instantiation*, and the term "specialization" is used for other language mechanisms.
> In an effort to avoid potential confusion for readers, this proposal uniformly uses the term "instantiation" to refer to application of a generic or template to arguments, even when discussing the Slang language.

### Generics

Many modern "post-C++" languages provide *generics* as a mechanism for parametric polymorphism: Slang, Rust, Swift, C#, Java, etc.
Generics have similar semantics and restrictions across these languages, even when implementations may differ greatly.

The following is a simple generic function declaration in Slang:

```slang
void invokeTwice<T : IExecutable>(T value)
{
    value.execute();
    value.execute();
}
```

Generics may have type parameters - e.g., the parameter `T` on `invokeTwice`.
Some languages - including Slang - also allow for generic value parameters.

The body of a generic declaration like `invokeTwice` is checked *once* at declaration time, independent of any instantiations.
Operations on a generic parameter type, or an expression of such a type (e.g., `value`), are only permitted when there are *constraints* on the generic parameters that justify the validity of those operations.
In the example above, the `: IExecutable` syntax declares a constraint on the generic type parameter `T`: a valid argument for `T` must be a type that is known to conform to `IExecutable`.

The constraints on generic type parameters are expressed using a declaration construct that groups together a related family of operations;
in Slang, this is an `interface` declaration:

```slang
interface IExecutable
{
    void execute();
}
```

The naming of the corresponding construct differs between languages: `interface` in Slang, C#, and Java; `trait` in Rust; `protocol` in Swift.
We will use the term *interface* to uniformly refer to this concept, in keeping with Slang terminology.
In each case, though, the same construct that is used to define constraints on generic type parameters is *also* used by the language mechanism for dynamic dispatch (e.g., `dyn MyTrait` in Rust or `some YourProtocol` in Swift).

Checking the body of a declaration once, against an explicit contract, is a defining characteristic of generics.
Some of the benefits of the mechanism include more predictable compile-time diagnostics, support for separate compilation, and making the requirements of a declaration explicit in its signature.

A key downside to generics is that they require the operations to be performed on (values of) generic parameter types to be codified as explicit interfaces, and that explicit conformances of types to those interfaces be introduced.
If code requires a complex operational contract, then the interface construct may need additional features to express it (e.g., associated types in Slang, Rust, and Swift).
In the limit, an operational contract may either be impossible to express with the interface construct the language provides, or the work required to express the contract and conformances to it could be prohibitive.

### Templates

Templates are a quintessential feature of C++, and have been adopted spiritually in some languages, such as D, that aspire to improve on C/C++ while retaining a high degree of conceptual compatibility and familiarity for developers.
While templates exist in languages beyond C++, we focus our discussion specifically on C++ templates, because they are overwhelmingly the most popular and well-known design for templates.

Here is the `invokeTwice` example from the previous section, rendered in idiomatic C++:

```hlsl
template<typename T>
void invokeTwice(T const& value)
{
    value.execute();
    value.execute();
}
```

Superficially, this definition is quite similar to the Slang version, with the most notable difference being the removal of any constraint on `T`.
Importantly, the C++ `invokeTwice` is conceptually "duck-typed," in that an expression like `value.execute()` does not statically refer to a specific and pre-declared operation, known to the author of `invokeTwice`.

In a simple case like this, the trade-off of templates compared to generics is clear.
The most important benefit is that a developer need not codify the operational contract that `invokeTwice` required of `T`, nor must they explicitly opt types into conformance to that contract.
In exchange, the developer loses full declaration-time checking of `invokeTwice`, compatibility with separate compilation, and clarity of the requirements in the declaration signature.

#### Concepts

As of C++20, C++ supports the `concept` and `requires` constructs, which allow templates to express some constraints on type parameters.
While concepts cover some similar ground to interfaces in Slang, there are key differences:

- Concepts support improved checking at the use/instantiation site of templates, but do not enable ahead-of-time checking of the definition of a concept-constrained templated declaration.

- In C++ the mechanisms that define operational contracts for run-time polymorphism (e.g., `virtual` functions) and for compile-time polymorphism (concepts) are separate, while in Slang/Rust/Swift/etc. a single construct serves both purposes.

This proposal does not consider use cases of C++ templates that involve or call for concepts.
We assume that a developer who explicitly wants and uses concept constraints on their C++ templates would not balk at being asked to use explicit interface constraints on their Slang generics.

#### Advanced Templates and Metaprogramming

Simple code like the `invokeTwice` example is just the tip of the iceberg of what C++ templates can be used to express.
The ability to define multiple distinct *specializations* of a templated declaration in C++, along with rules like SFINAE (including `enable_if`), allows C++ templates to express complex introspection and synthesis of code.

While there are many codebases that build upon or rely on these more advanced capabilities of C++ templates, we are intentionally *not* trying to cover such use cases with the current proposal.
There are many ways to express compile-time computation and program manipulation; C++ templates have proven to be sufficient for many such tasks, but they are not strictly *necessary*.
Indeed, facilities like `constexpr` and `consteval` in C++, along with proposals for compile-time reflection and metaprogramming, show a desire for language mechanisms that are more humane and tailored to these use cases, rather than always using the `template` hammer.

We believe compile-time evaluation, reflection, and metaprogramming could make for good additions to Slang, but we are not inclined to argue for C++ templates as the ideal language mechanism for expressing those features.

Proposed Approach
-----------------

We propose to extend Slang's HLSL-flavored dialect so that it supports templates in addition to the existing support for generics.
We will refer to these as *limited HLSL templates*, or just *templates* where the meaning is clear, to distinguish them from other implementations of templates such as those in C++.

### Goals

Limited HLSL templates attempt to balance two competing design goals:

- We want to increase the amount of existing HLSL code that the Slang toolset can ingest as-is, or with minimal modifications.

- We want the additions we make to the HLSL-flavored dialect to be consistent with the existing Slang language design, and possible to implement in the compiler with an appropriate amount of effort.

### Overview

A template declaration consists of the `template` keyword, a template parameter list, and one declaration:

```slang
template<typename T>
T twice(T value)
{
    return value + value;
}
```

A templated declaration is parsed once, as part of its enclosing module.
The declaration is semantically checked once for each instantiation that is required, e.g.:

```slang
float a = twice<float>(1.0f); // Explicit argument.
float b = twice(2.0f);        // T is inferred as float.
```

In the above example, the first call to `twice<float>` results in a new instantiation being required that was not needed before; as a result the Slang compiler checks the declaration of `twice` with `T` equal to `float`.
The second call to `twice` results in the same instantiation being required, and re-uses the instantiated declaration that was previously checked.

If the arguments (explicit or inferred) to a template instantiation result in the templated declaration failing to check, an error is diagnosed:

```slang
struct NotAddable {}

let notAddable = NotAddable();
let bad = twice(notAddable); // ERROR
```

### Availability

Template declarations are only available in source files whose input language is HLSL, where "HLSL" here means the HLSL-flavored language dialect implemented by the Slang compiler.
A user of the Slang toolchain can opt into this dialect when using `slangc` on the command line by putting their code in `.hlsl` files (which will auto-detect/enable the HLSL-flavored dialect) or by using `-lang hlsl`.
A user of the Slang compilation API opts into the HLSL-flavored dialect by passing in `SLANG_SOURCE_LANGUAGE_HLSL` as the language when adding a source unit.

We do not propose to expose or enable template declarations for the Slang language, or for the GLSL-flavored dialect supported by the Slang toolset.
Templates are a compatibility feature only, intended as an on-ramp to allow developers to more easily migrate their legacy codebases over to the Slang toolset, after which they can incrementally port their code to use the Slang language.

### Constraints / Assumptions

In order to make limited HLSL templates as consistent as possible with the existing language design, we take on the following constraints:

- A template instantiation is identified just by the template declaration being named (after possible overload resolution) and the identities of the arguments (whether explicit or inferred).
  In particular, the lexical/semantic context of the instantiation site is not relevant.

- Instantiation of a template results in a complete declaration, and is checked as it would be in the lexical/semantic context of the original template declaration, just with the template parameter names bound to the specific argument values for the instantiation.

- As a corollary of the above, the semantics of name lookup and conformance search are the same inside of a template as in any other Slang code.

Notably, Slang does not currently have any form of "argument-dependent lookup" like C++ has, where lookup of a non-member function takes into account the types of the arguments.
For example, in C++ a call like `f(x)` could potentially consider a declaration named `f` inside of the namespace that declared the type of `x`, even if that declaration wouldn't have been in scope for unqualified lookup otherwise.

We assume that if limited HLSL templates result in developers wanting some kind of argument-dependent lookup behavior for Slang, then that behavior should be proposed and implemented as a universal rule for lookup in Slang, and not a template-specific feature.

### Template Parameters

The initial version of limited HLSL templates only supports type parameters and value parameters of a restricted set of types:

```slang
template<typename T, int N>
struct FixedArray
{
    T values[N];
}
```

The proposed grammar is:

```text
template-declaration
    : 'template' '<' template-parameter-list '>' declaration

template-parameter-list
    : template-parameter (',' template-parameter)*

template-parameter
    : ('typename' | 'class') identifier template-default?
    | type-expression identifier template-default?

template-default
    : '=' expression
```

A template declaration must have at least one parameter.
An empty parameter list (`template<>`) is rejected with a diagnostic that notes the user may be attempting to declare an explicit specialization, which is not supported.

As in C++ `typename` and `class` have identical meaning in a template parameter list.
`class` does not constrain the argument to a class type.

Explicit and inferred template arguments are determined using the existing generic argument machinery.
Any parameters that remain without arguments are then completed in parameter order using defaults.
If an explicit or inferred argument is available for a parameter, its default expression is not checked or evaluated for that instantiation.
Otherwise, the default expression is checked and evaluated using the template arguments already determined for that instantiation.
The result must be a proper type for a type parameter, or a value of the parameter's declared type for a value parameter.
Failure to form a required default makes the template application invalid; during overload candidate enumeration, it makes that candidate not applicable without immediately emitting its diagnostics.

Value parameters are limited to the types that are currently supported for generic value parameters: Boolean, integer, and enumeration types.
The declared type of a template value parameter must not reference any other parameters of the same template.
The type for a template value parameter is checked and validated once, as part of checking the template declaration itself, rather than once per instantiation.

Template parameters do not support interface conformance constraints, and template declarations do not support `where` clauses.
There is no analogue of C++ concepts.
A Slang developer who wants a more explicit and checked contract for their declaration's parameters should use a generic instead.

### Declarations that may be templates

We propose that the initial implementation of limited HLSL templates should support:

- Function declarations, including global/namespace functions, methods of concrete types / extensions, and operator functions.

- Constructor (`__init`) declarations.

- Nominal product type declarations: `struct` and `class`

- Type aliases: `typealias` and `typedef`

A templated declaration is only allowed in a context where a comparable non-templated declaration would be allowed.

No restrictions are made on the use of templates nested inside a declaration that is itself a template (e.g., a templated `struct` declaration may contain a templated method declaration).

The members (requirements) of an `interface` declaration must not be templates.

Templates of other declaration kinds not listed here are not allowed.

A template declaration must not be explicitly declared `public`.
An unannotated template declaration is still accepted in language modes where declarations are public by default for legacy compatibility, but a template cannot be instantiated from another module.
If a template from another module would otherwise be selected, an error is diagnosed at that use.

### Template Arguments

When considering the application of a template to arguments, a template behaves semantically much like a generic that doesn't place any constraints on its parameters.

#### Explicit Template Arguments

A template is applied to explicit arguments using the same syntax as for generics:

```slang
FixedArray<float, 4> values;
float result = twice<float>(value);
```

No changes are made to the parser: the same strategy is used to parse a postfix `base<args...>` as before, and the distinction between when `base` is a generic vs. template declaration is handled entirely during semantic checking.

Arguments to a template are checked in the same fashion as arguments to a generic, based on whether each corresponding parameter is a type or value parameter.
Because the types of all template value parameters are checked once, ahead of time, an argument expression for a value parameter can be checked against the expected type without any instantiation being required.

#### Inferred Template Arguments

When using call syntax (`base(args...)`) template arguments are inferred in the same cases where they would be inferred for generics.
Template argument inference uses the same logic as for inference of generic arguments, treating a template like a generic with no constraints.

### Overload Resolution

A declaration-reference to a template declaration participates in overload resolution in much the same way as for a declaration-reference to a generic declaration.
The key additional detail is that after template arguments are inferred, additional checks must be performed to determine what the actual parameter types of a candidate function/callee are.

The overall flow of overload resolution is as follows:

- During lookup, a template (or generic) declaration may be found and included in the overload set for an identifier expression or member expression.

- During candidate enumeration, if a declaration-reference to a template (or generic) is being processed, argument inference is attempted for suitable template (or generic) arguments.

  - If argument inference fails, the candidate is marked as not applicable; this applies to both generics and templates.

  - If argument inference succeeds, and the candidate is a template, then a suitable instantiation of that template is created (or re-used), but not yet fully checked.
    Instead, checking is only applied to those parts of the instance that are strictly required for performing matching and ranking of overload candidates (more on this below).
    Diagnostics that arise during this step are buffered on the instance, rather than emitted eagerly to the output sink.
    If these checks fail (produce any errors), the candidate is marked as not applicable.

  - Otherwise, if the candidate has not yet been marked as not applicable, then candidate enumeration proceeds recursively with the new declaration reference (to the instantiated generic or template).

- Once all candidates have been enumerated, ordinary Slang overload resolution ranks the resulting candidates according to their signatures, and attempts to identify a unique best match.

  - If no candidates were applicable, then diagnostics are emitted to explain the situation, including information on candidates that were considered and why they were rejected.

  - If there are multiple applicable candidates, but no unique best candidate (according to the ranking criteria), then a diagnostic is emitted to explain the situation, including information on the applicable candidates that created the ambiguity.

  - If there is a unique best applicable candidate, then it is selected. If that candidate was the result of instantiating a template, then the chosen template instance is marked as being part of the module and will be fully checked.
    Some of the checking must be completed before the overloaded call site can finish checking (e.g., we must know the result type of the chosen candidate), while other kinds of checks can wait until later (e.g., checking the body of a function).

Note that if a template instantiation is created/requested as part of overload resolution, it is only marked/considered as part of the module to be checked if it is selected as the best candidate.
Template instantiations that are requested but not selected for one overloaded call site may later be selected at another call site, or requested and checked as part of some other expression.
If a given template instantiation is only ever requested as part of overload resolution, but never selected nor used in other expression contexts, then it will not get checked any further.

#### Is this SFINAE?

The proposed rules for overload resolution divide checking of a template instantiation into two de facto phases:

- First, the "overloading-relevant signature" of an instantiation is checked as part of determining whether an overload candidate should be considered viable/applicable.

- Second, the rest of an instantiation is checked only if it was chosen as a result of overload resolution, or used via explicit application.

Failures that arise only during the first phase are not diagnosed as errors for the purposes of overload resolution;
in practice, then, these "substitution failures" are not errors.
So, yes, these rules are comparable to the C++ SFINAE concept.

Our intention in this proposal is to make limited HLSL templates useful enough for practical cases, while not opening the floodgates to C++-style template metaprogramming.

The key design decision that must be made is what constitutes the "overloading-relevant signature" of a declaration.
Our proposed rules are that for functions (and function-like declarations like constructors), we only consider those properties that are relevant to determining whether a candidate is viable, and for ranking of candidates:

- The number of parameters

- The type of each parameter

- The parameter-passing mode of each parameter (`inout`, `out`, etc.)

- Whether each given parameter has a default (but not the default-argument-value expression itself)

- The type and parameter-passing mode of the implicit `this` parameter (if any).

Of this information, the main things that can fail validation are the types of function parameters.

For type declarations (whether `struct`, `typealias`, etc.) we consider the "overloading-relevant signature" to be empty/trivial.

Notably our proposed rules leave the following out of scope for overloading relevance:

- The member declarations of a type declaration

- The bases clause of a type declaration (e.g., the interfaces a `struct` declares conformance to)

- The body of a function-like declaration

- The declared result type of a function-like declaration

If Slang's overload-resolution scheme were ever changed to be bidirectional and take result type into account, then the declared result type of a function-like declaration would change to be part of the overloading-relevant signature.

This proposal does not add template partial ordering or any template-specific specificity rules.
If existing Slang overload rules cannot distinguish two instantiated candidate signatures, the call is ambiguous.

Detailed Explanation
--------------------

We present the details here by sketching where the addition of templates intersects the current `slangc` implementation.

### AST Representation

The class hierarchy of AST nodes should be expanded around generic declarations (`GenericDecl`) to introduce the following structure:

- A base class for *parameterized declarations* (`ParameterizedDecl`), which includes a list of parameters and an inner declaration

  - A subclass for generic declarations (the existing `GenericDecl`), which also supports constraints on its parameters

  - A subclass for template declarations (`TemplateDecl`)

> Note: the term "parameterized declaration" is perhaps too generic;
> a function declaration also has parameters, and is thus also "parameterized."
> In this context we mean to capture that both generics and templates are approaches for trying to achieve *parametric polymorphism*.
>
> Better names for us to use for this concept are welcome.

Similarly, the existing classes for `GenericTypeParamDecl` and `GenericValueParamDecl` should be split into matching hierarchies, so that we can (if necessary) tell generic parameters apart from template parameters.

The existing `DeclRefType`/`DeclRefIntVal` can be used to represent references to template type/value parameters.
Typically, symbolic references to template parameters are not used (since a template will be instantiated with specific values).
The main case where we anticipate using symbolic references to template parameters is when forming the inference signature of a templated declaration (discussed below).

### Parser

The parser needs to be extended with a new `template` syntax declaration, to be included in the parsing environment when parsing input using the HLSL-flavored dialect.

A `template` declaration's parsing behavior will be largely similar to that for the existing internal-use-only `__generic` construct.
The main differences relate to the specific syntax that we propose for template parameters, so that they more closely match existing HLSL/C++.

No other parser changes are required.
Sites where a template is referenced/used can use all of the existing AST nodes and their parsing rules.
E.g., a `SpecializeExpr` can represent any expression of the form `base<args...>`, whether the base turns out to be a template or a generic.

### Semantic Checking

Almost all of the work of integrating templates into the compilation pipeline is in the semantic checking stage.

For the purposes of understanding semantic checking, it is important to keep in mind the distinction between a template declaration and an *instantiation* of a template declaration:

- A template declaration is the syntactic construct starting with `template` that the user actually wrote, and it has its own custom checking rules, just like how functions, `struct`s, etc. all have their own checking rules.

- An instantiation of a template declaration is the result of applying a template to values for its arguments.
  A single template declaration may result in several different instantiations being created from it.
  Each instantiation of a template owns a distinct cloned copy of the inner declaration from the template.

Note that the cloned inner declaration for a template instantiation is just an ordinary declaration (a `Decl`) and supports all the same machinery for semantic checking that it would in the non-templated case.
For example, an instantiation of a templated `struct` declaration just owns an ordinary `StructDecl`, like any other.

A key principle in our proposed approach is that we try to avoid special-cased interactions between templates and other kinds of declarations:

- Existing rules for how/when declarations are checked do not treat template declarations as a special case.
  For example, the rules for how/when the member declarations of a `struct` declaration are checked do not distinguish template declarations from other kinds of member declarations.

- The rules for template declarations are, as much as possible, independent of what the kind of the inner declaration is.

- The rules for instantiations of a template are, as much as possible, independent of what the kind of the (cloned) inner declaration is.

- As much as possible, the (cloned) inner declaration of a template instantiation is treated just like any other declaration would be, independent of its origin in a template.

One final principle is that we try to leverage existing semantic-checking behavior for generic declarations as much as possible, by reframing that behavior as applying to all parameterized declarations.
We only specify behavior here for template declarations in those cases where templates require different or additional checking rules from those used for generics.

#### Checking a Template Declaration

Checking a template declaration involves validating each template parameter declaration and computing the inference signature of the inner declaration.

##### Template Parameters

For template value parameters, the type of the parameter is checked once for the template declaration, and not for each instantiation;
if the type expression for a value parameter refers to any other parameter of the template, an error should be diagnosed.

Default-argument-value expressions for template parameters are not checked at this step.

Checking a template declaration does not cause its inner declaration to be checked.
One special-case rule applied at this step is that if the inner declaration (recursively) contains any function bodies for which parsing was deferred (meaning they are stored as just a sequence of tokens), then those bodies should be parsed once, as part of checking the template declaration, so that they are not parsed on a per-instantiation basis.
To put this in other terms: a parse error inside of a template's inner declaration should be diagnosed once and only once, rather than once per instantiation.

> Note:
>
> It is potentially viable to perform some amount of checking of the inner declaration of a template ahead of time, when checking the template itself, rather than per-instantiation.
> For example, non-dependent names could be looked up and resolved to their (possibly overloaded) bindings, with errors being diagnosed for undefined names.
>
> We do not propose such an implementation approach at present, and leave it as possible future quality-of-implementation work.

##### Computing the Inference Signature

The *inference* signature of a template declaration is derived from its inner declaration, with no dependence on a specific instantiation with concrete argument values.
An inference signature comprises zero or more bundles of parameter information.
If the inner declaration is a callable declaration, then each bundle will correspond to one explicitly-declared parameter of the inner declaration; if the inner declaration is not callable, then the inference signature will be empty.

Each parameter information bundle in the inference signature comprises:

- The parameter-passing mode of the parameter

- Whether the parameter has a default-argument-value expression (but not the specific value)

- A *pattern type*: a `QualType` representing known information about the parameter's type, with symbolic or placeholder information stored in place of sub-terms that reference or depend on template parameters.

- Optionally, internal failure information describing why a valid pattern type could not be derived for this parameter

A pattern type may have two different kinds of placeholders in it:

- Symbolic references to template parameters (e.g., `T`); these are represented as `DeclRefType`/`DeclRefIntVal` values, comparable to symbolic references to generic parameters

- Sub-expressions or values *derived from* template parameters (e.g., `T::Element`); these are represented as indeterminate/unknown values.
  The semantics of an indeterminate/unknown-value expression are comparable to those for an error expression, just without needing to originate from a diagnosed error.

The inference signature of a template is computed by checking the declared type of each parameter (if any) of the inner declaration to derive the appropriate pattern type, in an environment that binds the template parameter names to symbolic `Value`s representing them (much like how checking of a generic declaration is performed with the generic parameter names bound to symbolic values).

An inference signature exists only to facilitate template argument inference.
It cannot establish that a template declaration or any instantiation is valid or invalid, and the actual checked declaration for a concrete instantiation remains the authoritative semantic representation.
The symbolic and indeterminate values used in an inference signature are valid only within that artifact and must not escape into an instantiated declaration, the instantiation cache, ordinary semantic-checking state, or IR lowering.

Checking performed to construct an inference signature is speculative and does not emit diagnostics.
Any diagnostics produced while deriving it are buffered and discarded; a part of the signature that cannot be derived is instead represented as indeterminate or non-deducible.
A genuine error encountered during this process will be diagnosed if and when it is encountered while checking a concrete instantiation.
This policy avoids introducing a partial two-phase checking model in which the same error could be diagnosed both for the template declaration and for each instantiation.

Checking a type expression to derive a pattern type re-uses the same checking logic that already exists for checking type expressions in other contexts.
The primary additions required for type-expression checking are:

- Identifier expressions that resolve to a template parameter should result in a checked expression holding the symbolic `Value` of that parameter.

- Operations such as member lookup should result in an expression representing an indeterminate or unknown value, if the base of the member lookup is any of:
  - a symbolic reference to a template type parameter (e.g., `T`)
  - an expression whose type is a template type parameter (e.g., `thing` where `thing` is of type `T`)
  - an expression representing an indeterminate/unknown value
  - an expression whose type is an indeterminate/unknown value

  Comparable rules are needed when the base of a call expression is in one of the above cases, or when one of the arguments to an overload call is in one of the above cases, etc.
  These rules are comparable to the handling of error expressions and error types in the compiler today.

- Searches for interface conformance or subtype witnesses always succeed when either of the type/interface operands is a symbolic reference to a template type parameter, or an indeterminate/unknown value.
  The witness returned is a placeholder for an indeterminate/unknown witness.

The result of checking a pattern type is a `Type`/`QualType` such that the parts that can be statically determined without knowledge of the specific values of template parameters are present, but parts that depend on template parameters are left symbolic/unknown.
For example, given a declaration like:

```slang
template<typename T>
void f(vector<T::Element,3> p) { ... }
```

The inference signature for the template `f` would include a pattern type for parameter `p` such that the information `vector<..., 3>` is present in the pattern type, but the sub-expression for `T::Element`, which depends on the unknown value of the template parameter `T`, is left indeterminate/unknown.

#### Referencing a Template Declaration

An identifier expression that resolves to a template declaration (or where one of its overloaded meanings is a reference to a template declaration) results in a declaration-reference to that template declaration, just as happens for a generic declaration or any other declaration; no special-case rules are used.
The type of such a declaration-reference will be a unique non-proper type (`TemplateType`) akin to how the type of a declaration-reference to a generic decl is handled (using `GenericDeclRefType`).

#### Finding or Creating a Template Instantiation

An *instantiation* of a template is identified uniquely by:

- its *origin*: a declaration-reference to a template declaration (`DeclRef<TemplateDecl>`)

- its arguments: a sequence of semantic values (`Value`) corresponding to the parameters of the template declaration

The per-module semantic checking context should include a deduplication cache for template instantiations.
When checking logic needs an instantiation it should first find an existing instantiation in the cache, or create and register an instantiation if a cached one is not found.

A template instantiation should be represented as a durable object that carries the origin, arguments, and additional state.
In particular a template instantiation should track:

- The origin

- The arguments

- A cloned copy of the inner declaration of the origin; note that because declarations are stateful in the Slang compiler's semantics-checking logic, this cloned declaration may be either unchecked, checked, or somewhere in between, as tracked by its check state (`DeclCheckState`)

  The clone's parent link and enclosing scope chain must reproduce the lexical context of the origin, including access to any enclosing type declaration needed to determine a method's `this` type.
  This requirement does not imply that the clone is inserted into the ordinary member list of that parent.

- A lookup environment/scope that captures both the lexical and semantic context of the origin, as well as bindings mapping the parameter names of the origin template to the argument values of the instantiation.

- A checking status specific to the instantiation, along with a buffer containing diagnostics produced while checking the instantiation's cloned inner declaration.
  The buffer of diagnostics is primarily needed to provide the necessary SFINAE-like semantics during overload resolution.

The per-module semantic-checking context should also maintain an ordered collection of committed template instantiations, separate from the ordinary declaration lists used for lookup.
This collection keeps committed clones alive and allows the remaining checking and IR-lowering stages to enumerate them.
An implementation may additionally store or index the instances originating from a template on its `TemplateDecl`, but committed clones must not become ordinary overload candidates merely because they have been instantiated.

Note that an instantiation that has been created is not automatically or necessarily one that has been selected/committed.
The possible states that an instantiation may be in include:

- Just created

- Checking the overloading-relevant signature

- Checked the overloading-relevant signature successfully; any diagnostics produced are stored in the buffer of diagnostics

- Checked the overloading-relevant signature with errors; any diagnostics produced are stored in the buffer of diagnostics

- Committed; the instantiation has been determined to be needed/used and must eventually be fully checked.
  The cloned inner declaration has been registered in the module's collection of committed template instantiations.

The "checking" state above exists primarily to facilitate detection of circularity in checking and avoid infinite regress/recursion.

The semantic-checking context must also track the active template-expansion depth and the total number of template instantiations created for a compilation.
Before starting a nested expansion, the compiler checks an implementation-defined maximum expansion depth; before registering a new instance, it checks an implementation-defined maximum instance count.
Exceeding either limit is diagnosed and the requested expansion fails.
The "checking" state detects direct cycles involving the same instance, while these limits also bound recursion that continually produces instances with distinct arguments.

#### Checking a Template Instantiation

Checking of a template instantiation primarily involves advancing its cloned inner declaration to an appropriate check state (e.g., `DeclCheckState::FullyChecked`).
The relevant logic should not need to care about the kind of the inner declaration (function vs. type, etc.).

##### Checking the Overloading-Relevant Signature

Overload resolution requires that specific information about a template instantiation's inner declaration has been checked (e.g., the types of function parameters).

We propose to introduce a dedicated check state to represent that a declaration's overloading-relevant signature has been checked (e.g., `DeclCheckState::OverloadingRelevantSignatureChecked`).
Checking of callable declarations such as function declarations will need to be split so that only the overloading-relevant information is checked for this new state, while other information (e.g., default-argument-value expressions for parameters, the result type of a function, etc.) are only checked as part of the existing check state corresponding to checking the fully "header"/signature of a declaration.

When a request is made to check the overloading-relevant signature of a template instantiation, the behavior depends on the current state of the instantiation:

- If the state is "committed," or "checked" (with or without errors), there is nothing to do and the state stays as-is.

- If the state is "checking," then a circularity has occurred and must be diagnosed.

- Otherwise, the state is "just created."

  The declaration should be shifted into the "checking" state, and then the existing machinery (`ensureDecl`) should be used to advance the inner declaration to the appropriate state (`OverloadingRelevantSignatureChecked`), while capturing any diagnostics that are emitted into the buffer for the instantiation.

  Once the checking is complete, the buffer of diagnostics should be inspected and the instantiation should be shifted into the appropriate "checked" state (with or without errors).

> Note: While diagnostics related to the inner declaration of the instantiation must be buffered up, if the process of checking the overloading-relevant signature leads to other declarations needing to be checked (via `ensureDecl`), then those checks should be performed with the ordinary (unbuffered) diagnostic sink for the semantic-checking context, since they are not diagnostics related to the instantiation itself.

##### Committing a Template Instantiation

A committed template instantiation must eventually be fully checked, just as for any other declaration in a module.

If a request is made to commit a template instantiation that is already in the "committed" state, nothing is done.
Otherwise, the cloned inner declaration is registered in the per-module collection of committed template instantiations.
Its parent and scope links continue to reflect the lexical context of the origin, but it is not inserted as an ordinary child that participates in member lookup, redeclaration checking, or overload enumeration.
The identity used for semantic references and eventual name mangling must incorporate both the origin template and its argument values, even when two instantiations would otherwise have identical ordinary declaration signatures.
Any buffered diagnostics pertaining to the instantiation must be flushed to the appropriate sink for the semantic-checking context, so that they become visible to the user of the compiler.
Any subsequent diagnostics related to checking the inner declaration will be emitted like normal (without buffering on the tracking object for the instantiation).

The proposed implementation eagerly advances the cloned inner declaration to `DeclCheckState::FullyChecked` when the instantiation is first committed.
Deferring that work until a later compiler phase would be semantically valid if it produced the same result, but eager checking gives users diagnostics at the first use that requires the instantiation and in the least surprising order.

> Note: As a quality-of-implementation detail, diagnostics related to a template instantiation should ideally be able to note the context in which that instantiation was requested.
> We do not consider such a mechanism to be strictly required for a first experimental version of template support, but it is clearly required for something properly usable.

Note that in the case where the inner declaration of a template is a type declaration such as a `struct`, the proposed rules implicitly mean that:

- The members of a templated type declaration are checked eagerly for each instantiation, instead of only when referenced.

- If a templated type declaration contains a nested member that is also a template declaration, then that nested template declaration is also checked eagerly.
  Note, however, that checking of the nested template declaration itself only checks its parameters, as discussed above; the body of a templated member declaration nested inside of a templated type is still only checked when required for an instantiation of that nested template.
  No special logic is required to ensure this behavior; it just falls out.

#### Explicit Application

When checking an explicit expression of the form `base<args...>` (a `SpecializeExpr`), each meaning of `base` may refer to any parameterized declaration, whether a generic or template declaration.

##### Non-Overloaded Base

If `base` resolves to a single parameterized declaration, the argument expressions are checked against their corresponding parameters using the same overall logic used today for generic declarations, generalized to the case of any parameterized declaration.

An argument corresponding to a type parameter is checked as a type expression.
An argument corresponding to a value parameter is checked against the type of that parameter and resolved to a value (`Value`).

If the explicit application must yield a complete specialization, a missing argument is completed from the default-argument-value expression for the corresponding parameter, if any.
In the case of a templated declaration, that default-argument-value expression is checked and resolved to a value, using the lexical/semantic context of the template declaration-reference extended with a scope that binds the parameter names of the template to the argument values known so far.
When an explicit application is the callee of a call expression, explicitly supplied arguments instead provide initial solutions for argument inference, and remaining arguments may be inferred from the call before defaults are applied.

Once the argument values have all been checked, a corresponding instantiation of the origin template declaration-reference is found or created, and then committed.
The result of checking the explicit application is then a declaration-reference to the cloned inner declaration for that instantiation.

##### Overloaded Base

If `base` is overloaded, the existing overload-resolution flow for explicit application of generic declarations should be generalized to parameterized declarations.
Each parameterized candidate is considered independently: the explicit arguments are applied to its parameters, any remaining arguments are inferred from an enclosing call when applicable, and defaults are used only after explicit arguments and inference.
A failure for one candidate rejects that candidate without immediately emitting its diagnostics.

For a generic candidate with a complete argument list, this process forms a specialized declaration-reference as it does today.
For a template candidate with a complete argument list, it finds or creates an uncommitted instantiation and forms a declaration-reference to its cloned inner declaration after checking its overloading-relevant signature.
The resulting candidates participate in the existing overload matching and ranking rules.
Only a selected template instantiation is committed; if no candidate is applicable, or if there is no unique best candidate where one is required, the existing no-applicable-overload or ambiguity diagnostic is emitted with template-specific candidate-rejection information as appropriate.

#### Argument Inference

Argument inference should be changed to operate on an arbitrary parameterized declaration, so that it applies consistently to both templates and generics.

When argument inference is applied to a template declaration, the inference signature of the template should be used as the source of information about the parameters of an inner callable declaration.
The argument types at the call site will be matched/"unified" with the pattern types stored in the inference signature.

During matching/"unification", placeholders in a pattern type will be handled as follows:

- A symbolic reference to a template parameter will be treated the same as a symbolic reference to a generic parameter, for the purposes of matching; the corresponding argument type will be recorded into the bounds/constraint information for the corresponding argument being inferred.

- An indeterminate/unknown value will cause no further matching, but will not report an inference failure.

In practice, this means that inference can make use of a parameter type that directly references a template parameter, but not one that uses an expression derived from a template parameter.
Consider:

```slang
template<typename T>
void yes(T y) { ... }

template<typename T>
void no(T.Element n) { ... }

struct ConcreteType {
    typealias Element = int;
    int getElement() { ... }
}

...
let c : ConcreteType = ...;
yes(c); // infers T = ConcreteType
no(c.getElement()); // inference fails
```

In the case of the function `yes`, the inference engine attempts to match `ConcreteType` with `T`, and is able to make an inference.
In the case of the function `no`, the inference engine attempts to match `int` with `T.Element`, and is not able to infer any information about `T`.

#### Overload Resolution

During candidate enumeration for overload resolution, a declaration-reference to a parameterized declaration should trigger argument inference.
If argument inference fails, the candidate is not applicable/viable.

If argument inference succeeds for a parameterized declaration then:

- For a generic declaration we simply form a specialized declaration-reference, given the base generic declaration reference and the argument values.

- For a template declaration, we find or create a suitable instantiation and then request checking of its overloading-relevant signature.

  - If checking of the overloading-relevant signature fails, then the candidate is not applicable/viable.

  - If checking of the overloading-relevant signature succeeds, then a declaration-reference is formed to the inner declaration of the candidate.

In either case, if the candidate is still applicable/viable, we have a new declaration reference to continue recursively with candidate enumeration.

Since a candidate derived from a templated declaration holds a declaration-reference to the inner declaration from some instantiation (e.g., a declaration reference to a `FuncDecl`), it can be compared/ranked against the declaration-references for other candidates just like any existing kind of candidate.
No special template-specific logic is required when comparing or ranking candidates.

In the case where a single candidate is chosen as the best, and that candidate was derived from a template instantiation, that instantiation is committed before checking of the overloaded call expression returns.

### Interaction with Modules

We propose that templates should only be usable from the same module where they were defined.
This proposed limitation is orthogonal to the *visibility* of a template declaration.

In a source unit that uses Slang's "legacy mode" visibility rules (which is the norm for source units in the HLSL dialect), the default visibility of a declaration is `public`, while in units that use the modern visibility rules, the default is `internal`.
Any attempt to mark a template declaration as explicitly `public` should be diagnosed, noting that even if a template declaration is made public, it will not be usable from other modules.

The language rule is that an instantiation cannot be selected from outside the module that defines its template declaration.
The exact point at which the compiler rejects such a candidate depends on whether checking the overloading-relevant signature can operate reliably on a template declaration AST loaded from a serialized module.
The preferred implementation may inspect the external declaration provisionally and then diagnose an error if its instantiation would be selected; a simpler implementation may reject the external candidate before checking its overloading-relevant signature.
An implementation spike should resolve which strategy is practical, after which the rejection point and diagnostics must be deterministic and must not depend on incidental availability of serialized AST state.

### Interaction with Generics

Having an HLSL-flavored dialect with both generics and templates creates the possibility that a template will be nested under a generic, or vice versa.
While we consider such situations to be unlikely in practice, the dialect rules and compiler implementation must have some answer on how they should behave.

#### Direct Nesting

Direct nesting of generics and templates should be disallowed, just like direct nesting of a generic under another generic is disallowed.
Put simply, if the inner declaration of a parameterized declaration is itself a parameterized declaration, an error should be diagnosed.
All of the following declarations should result in an error being diagnosed:

```slang
__generic<T>
void generic_generic<U>() {}

template<typename T>
template<typename U>
void template_template() {}

template<typename T>
void template_generic<U>() {}

__generic<T>
template<typename U>
void generic_template() {}
```

Note that without template declarations, the only way to create such an improper nesting situation would have been with the internal-use-only `__generic` syntax.
If the rejected syntax resembles a C++ explicit or partial specialization, such as `template<typename T> struct Foo<int, T>`, the diagnostic should include a note that template specialization is not supported.

#### Generics Under a Template

A generic declaration nested indirectly under a template (e.g., a generic method inside a templated `struct` declaration) should Just Work under the semantics defined so far, with no extra implementation complexity.
A Slang generic is just another ordinary kind of declaration, and the rules we have defined here are almost entirely agnostic to the kinds of declarations under a template.

#### Templates Under a Generic

The one truly non-trivial case is when a template is nested under a generic, such as in the following example:

```slang
struct MyContainer<T>
{
    template<typename U>
    [mutating] void append(U value) { ... }
}
```

We propose that for the first version of template support, indirect nesting of a template declaration anywhere under a generic declaration should be diagnosed as an error.

We believe that the semantics of template-under-generic nesting can be made sound, and may even fall out naturally from our overall implementation strategy, but we do not think that template support should be contingent on having a working solution for this case.

Alternatives Considered
-----------------------

### Implement C++-compatible templates

We empathize with developers who want a highly portable C++ front-end for GPU graphics programming; we think that such a tool would be great to have in the ecosystem.
The harsh reality, however, is that the Slang language is different from C++ by design, and the Slang compiler codebase uses a fundamentally different architecture than a standards-conformant C++ compiler would.

We have taken the time to seriously investigate what would be required to bring together a C++-compatible front-end such as Clang with the things that make the Slang language and toolset great (wide cross-platform portability, autodiff, and modern language features).
Our conclusion is that the effort required would be prohibitive—comparable to a full re-implementation of the Slang compiler.

The Slang language is not C++, and was never intended to be.
For better or worse, developers who need or want C++ compatibility should use a C++ compiler.

### Do not add templates

Adding template support to the Slang toolset comes with very real costs and risks, and should not be undertaken lightly.

First, template support introduces new rules to the HLSL-flavored dialect and new code paths to the compiler;
that added complexity risks making the dialect harder for developers to learn and use, and the compiler harder to maintain and support, even for developers who have no interest in or use for templates.

Second, templates were never intended to be part of the Slang language design; they are not compatible with the original vision we had for Slang.
It is possible that adding template support to the Slang toolset could result in developers using its HLSL-flavored dialect favoring templates over alternatives, such as generics, that we believe are better long-term solutions.
We must carefully evaluate whether adding templates would serve the mission of the Slang project, to help GPU and graphics developers migrate toward better programming models and more scalable GPU code architecture.

Finally, there is a risk that adding some amount of template support to the Slang codebase will confuse developers, leading them to think that high levels of C++ compatibility, or eventual convergence with C++, are goals of the project.
If adding templates is a "one and done" that improves our on-ramp for developers with existing/legacy HLSL codebases, that may be fine;
if the result is a flood of developers asking for more C++ compatibility features, rather than engaging with the Slang language on its own terms, that may create a kind of identity crisis for the language/project.

On balance, we believe that adding templates to the Slang toolset is worth it, but only with the very specific guardrails this proposal puts in place:

- Template support is intentionally restricted in ways that minimize the impact on the compiler codebase, and thus on the expected costs for ongoing maintenance.
  Wherever possible, template support piggybacks on existing support for generics in the dialect rules and compiler implementation.

- Template support is only enabled for the HLSL-flavored dialect, and is not being proposed as a feature of the Slang language itself (nor as a value-add feature for the GLSL-flavored dialect).
  The goal of this proposal is to support ingestion of *existing* code, and not to enable developers writing new codebases in Slang to fall back on old habits.

This proposal is ultimately about scaffolding: we intend to introduce structures that allow more developers to come into the Slang ecosystem, with the full knowledge and intention that in the long run these structures should not be needed.
The HLSL- and GLSL-flavored dialects are already examples of scaffolding that the Slang project has introduced to help developers migrate their codebases to the Slang language.
As those dialects move into deprecation and eventual removal, template support should expire with them.
