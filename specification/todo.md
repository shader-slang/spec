Slang Specification TODO List
=============================

* General
  * Need a preprocessing tool to scrape the input files and transform certain bits of Slang-specific notation over to bikeshed-friendly forms
    * Lexical grammar
    * AST grammar
    * Semantics-related judgements

* Introduction

* Lexical Analysis
  * Need rules for how leading/trailing trivia gets associated with tokens
  * Need correct (Unicode) definitions for identifier characters
  * Probably need to introduce intended forms for documentation comments (even if handling of those comments by tools is not specified)
  * Proper lexical syntax blocks needed for some productions:
    * Comments (especially block comments)
    * Numeric literals
      * Handling of suffixes
      * Handling of the ways that radix affects allowed digits
      * Interpretation of literal suffixes should be moved to semantic checking of the corresponding expressions
    * Text literals
      * Need escape sequences to be documented
      * Need proper grammar for strings and characters
    * Punctuation
      * Text is treating it like there's a table when there no longer is
        * But still need some verbiage to make clear that the comments in those grammar productions establish *definitions* for the relevant tokens

* Preprocessor
  * Need to make a decision between two clear options:
    * Add a normative reference to an existing preprocessor
    * Actually specify what our preprocessor does
  * Need to at least include non-normative descriptiosn of each directive

* Semantic Checking
  * This section is only skeletal, and needs to be written in a more complete fashion...
  * The primary task here (which informs a great many subsequent sections) is that we need to pick the terminology and *notation* that we will use to describe the semantic checking rules (which includes all the type-checking rules)
  * At the very least, this section should be defining what a *context* is, how contexts are extended, etc.
  * Much like for the grammar stuff, we need to pick a working notation to use for expressing judgements, and then later on we need to add (custom) tooling to scrape the input files for uses of that notation and replace it with bikeshed-friendly forms (e.g., HTML tables if we want to match WGSL).

* Parsing
  * This section is more-or-less reasonable, but will probably need to be revisited over time to ensure that it is sufficiently formal to actually define/constrain the parser implementatin.
  * The discussion of handling angle brackets in unordered mode needs to be vetted against the implementation, but is also likely to change if/when the implementation changes

* Execution Model
  * This section needs to be written from scratch, and it is difficult to predict how long that might take. I should look at the WGSL spec to see how much detail they end up going into. The GLSL "spec" is probably also a good point of reference.
  * We clearly don't want to be in the business of defining a full memory model in our spec, so we need to find some way to have a normative reference or whatever allows us to use reasonably precise terminology without having to define everything.
  * This section needs to define some notions of memory *ownership*, which overlaps heavily with the memory model, but is not the same thing.
  * Similarly, we end up needing a divergence and reconvergence model, which is something that is seldom formalized (correctly).
  * We need to decide how formal we want to be about the dynamic semantics (aka "runtime behavior") of the language. This section needs to define the terminology and notation that will be used to describe the behavior of constructs in the later sections.
  * This section needs to define what things like entry points *are*, but we need some subsequent section to define the checking rules related to entry points for particular pipeline stages

* Modules
  * Should actually give a grammar for primary and secondary source units here, rather than the more loose version down in the "Declarations" section
  * Otherwise this section is decent enough for now.

* Declarations
  * Need to handle the rules for when two function declarations (including generic functions) do or don't conflict
  * The text here related to environments and bindings should be excised and instead should reference the "Semantic Checking" section
  * This section lacks almost any semantic-checking judgements for the syntactic forms that get introduced
    * We need to devise the right form for these judgements to take, given our out-of-order semantic checking rules. Specifically, we cannot easily have the checking rules for declarations inject new bindings into a context when their sub-forms need to be checked the context that is the *output* of all that checking... We need to look at how papers on object calculi handle the formalization of lookup in order to work around the apparent circularity
    * We need to devise and put in place a strategy for how to share the core checking logic around generic declarations between all the different potentially-generic declaration forms.
      * So far, the best idea we've kicked around is to have what amounts to a "desugars-to" judgement that rewrites the surface syntax over to a form that makes generic declarations an explicit wrapper around whatever is underneath.
    * We need to devise a way to have the checking rules for the "traditional" syntax for various constructs be defined in terms of the rules for the "modern" forms. The hypothetical desugars-to judgement might be the answer for this case as well.
  * We need some kind of rules around what declarations are allowed to contain what other kinds of declarations in their bodies.
  * The discussion of directions needs to be cleaned up and we need to ensure that it matches our implementation, and connects to whatever ownership model we define in the execute model section.
  * Need to define rules for checking definitive initialization.
  * Need to define rules for checking control-flow validity
  * Need to determine how to factor out the common pieces of various declaration forms in a logical way (parameter lists, generic parameters & where clauses, declaration bodies, statement bodies, etc.)
  * The extension declaration section here is entirely informal and needs a full rewrite.
  * The "Generics" section here is entirely informal and needs a full rewrite.

* Attributes (/ Modifiers / Qualifiers / Decorations / ...)
  * This section needs to define all the built-in forms that can modify things, their meanings, and their restrictions (what they can apply to)
  * This includes major things like `[shader(...)]`, `SV_*` semantics, etc.

* Visibility Control
  * This section needs to be written
  * Visibility interacts in fundamental ways with lookup, so it may need to be part of the same overall section
  * We need to define the rules for what the implicit visibility of declarations is
  * We 

* Statements
  * This section has a provisional form of some type-checking judgements, but it needs an overhaul
  * This section has provisional forms of the behavior (dynamic semantics) of various forms, but that needs a rewrite pass to match whatever our decisions are about notation

* Expressions
  * This chapter currently ignores precedence as it would impact parsing
    * Need a proper hierarchy of basic, prefix, postfix, etc. expressions
    * Need a specified strategy for handling infix operator precedence (which should leave the door open to user-defined operators down the line...)
  * Checking rules in this section need to be converted to whatever our chosen notation ends up being (and many rules remain to be written)
  * The identifier expression case has un-ported text that belongs in the overloading and lookup sections, but that text is all informal.
  * The member expression case has informal text that needs to be formalized somwhere in the lookup section
  * Need to specify the mutability of `this` expressions
  * Need to specify the circumstances under which `this` can be referenced (i.e., not in static contexts... which means defining what a "static context" is)
  * Call expressions need to include syntax for mentioning a direction at a call site
    * The informal text here needs to be replaced
    * We now have proper function types, and thus need to describe how calls work on more than just function declarations
    * We need to specify the semantics of "calling" a type
    * It is unclear which of the above belongs in the expressions chapter and which belongs in the overloading chapter
  * subscript expressions
    * there is no formal specification given here
  * initializer list expressions
    * The checking rules here punt and delegate all the real work to rules for "constructing" a value that don't currently exist. Those rules either need to be spelled out here, in the conversion section, or in a new section entirely.
  * cast expression
    * The checking rules here aren't right, and need to be fixed; casts, constructor calls, and initializer lists should all bottleneck through a common piece of semantic logic
  * assignment
    * Writing correct checking rules here requires having a way to encode the l-value vs. r-value distinction in the formalized type system, which requires us to make decisions in the "Semantic Checking" chapter.
  * prefix/postfix operators
    * Need to provide rules on how lookup for operator functions in these cases filter down to only explicit prefix/postfix declarations
  

* Extensions
  * The entire chapter needs to be written
  * The main task of this chapter is unrelated to etensions: we need to define the *linearization* algorithm that takes a type and turns it into a list (or other structure) of *facets* that can be used for more direct lookup.
  * Also need rules for instantiating an extension at some type, and determining whether such an extension is or isn't applicable

* Lookup
  * This entire chapter needs to be written
  * This needs to deal with all the issues the Slang compiler implementation faces
    * Lookup in the context of some type (whether into the type isself or one of its instances).
      * Interacts with linearization
        * Need rules for deciding which declarations of matching name are "better" than which others (related to overloading, but distinct in most ways)
      * Interacts with the structure of modules (modules need linearization too)
      * Interacts with visibility
      * Interacts with "transparent" declarations
      * Interacts with overloading (the way things do/don't shadow)
      * Interacts with "special" kinds of declarations that don't technically have names (e.g., `init` declarations), but need lookup-like behavior
      * Interacts with mutability of the declaration(s) found
    * Lookup in a context itself, given a "bare" identifier expression
      * Often delegates to the type-based lookup, based on the surrounding declaration scopes (types, modules, etc.)
        * Needs to handle the difference between static and instance contexts for lookup
      * Also needs to handle local scopes (unless we formalize them as akin to type-based scopes... but that would probably be a Bad Idea)

* Overloading
  * Entire chapter needs to be written
  * Expect non-trivial interactions between these rules and the bidirectional nature of type-checking
  * "Simple" case is when an overloaded expression is being coerced to an expected type
    * Also needs to handle type-vs-value distinctions (may have an overload set that mixes type and non-type declarations)
    * Need to define a "better"-ness metric to compare candidates that takes into account
      * "distance" of declarations, in terms of lookup
      * cost of conversions (if any)
  * Harder case is overloaded calls (including calls to constructors, subscript expressions, etc.)
    * Need rules for matching arguments to parameters of candidates
      * Named argument support goes here
      * Validation of type and mutability of arguments
      * Parameters with default values need to be handled
        * Need to define rules for when/where/how default-value expression is evaluated
    * Need to loop in generic argument inference
    * Need to define a "better"-ness metric for call candidates that considers
      * "distance" of declarations in lookup
      * conversion cost of arguments and result
      * generic instantiations (favor non-generic over generic, rank different generics)
      * variadics

* Generics
  * Entire chapter needs to be written
  * Need rules for inference of implied constraints on a generic, based on declaration signature
  * Need rules for validation and canonicalization of constraints on generic declarations
  * Need rules to validate explicit specializations of a generic (including validating constraint satisfaction)
  * Need rules for inference of generic arguments when a generic is used without explicit specialization
    * Likely interaction with checking of applicability of `extension`s

* Types
  * Current text is not actually usable as spec text; this is effectively a chapter that needs to be written from scratch
  * The secondary task of this section is to catalog the main varieties of type supported by Slang. Much of this will actually be text that belongs in the core library documentation, but it can start here before being moved there, if needed.
  * The primary task of this chapter is to define the representation and notation to be used in the formalism, since these are what almost all of the rules/judgements that we are talking about will traffic in.
    * We also need notions of certain key concepts around types like copyability, movability, sized-ness, etc.
  

* Subtyping
  * Entire chapter needs to be written
  * This chapter needs to define the is-a-subtype-of relationship between types
    * Needs to handle inheritance (at least someday)
    * Needs to handle mutability (r-value vs. l-value) if our formal type system encodes such things (and it probably has to)
    * Needs to be able to represent the covariance of certain built-in type constructors
  * May also need to define a type identity or equality relationship
  * *Definitely* needs to define (or refer to) some kind of value-equality relationship to deal with generics that have value parameters
    * This likely turns into an equality test on expressions, which would need to include constant-folding rules, or delegate to such rules defined elsewhere
      * Thus, the formal notation needs some way to describe *values* and not just types (I know that's semi-obvious, but it needs to be noted so we remember to account for it)

* Interfaces
  * This chapter needs to be written
  * Need to define rules for deciding whether a concrete type conforms-to an interface (or conjunction)
    * These rules can be based on linearization
  * Also need to define rules for *validating* that a concrete type declaration satisfies the requirements of an interface it claims to conform to
    * Requires writing down rules for how we synthesize satisfying declarations for requirements
      * Big wrinkle in that is synthesis around generic requirements
  * Need to define rules for canonicalization of interface conjunctions here

* Conversion
  * This chapter needs to be written
  * Needs to handle both implicit type coercion and explicit type conversion (and establish consistent terminology for the rest of the spec); ideall the judgements for the two can be shared as much as possible
  * Need to define how coercion/conversion of `From` to `To` is semantically implemented
    * Interacts with type identity/equality and subtyping rules
      * Also Interacts with interface conforms-to rules
    * Interacts with lookup in order to find constructors to apply
      * Need to handle the potential circularity there...
  * Need to have the rules ascribe *costs* to all of the above, since costs will end up being used for overload resolution, etc.
  * While they are in practice core library code, this section should define the implicit conversion cases between builtin types, and their associated costs

* Capabilities
  * This entire chapter needs to be written
  * ...

* Autodiff
  * This chapter needs to be written
  * Tess is not (currently) qualified to do the work estimates here...


* Completely Unhandled Stuff
  * Definitions of constant-ness properties that we need (rates, etc.)
  * Stability rules (what changes can break source, IR, and binary compatibility between separately-compiled modules?)
  * `throws` functions and error handling