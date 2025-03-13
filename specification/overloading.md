Overload Resolution [overload]
===================

<div class=issue>
This chapter needs to describe how to disambiguate an overloaded lookup result.
Overload resolution comes up primarily in two places:


* When the typing rules attempt to coerce an overloaded expression to some type.
* When attempting to call an overloaded expression as a function.


(Hypothetically it can also arise for a generic specialization `F<A,B,...>` as well, so the rules need to be ready for that case)

The first of the two cases is the easier one by far, with an outline of it's semantics being:


* \emph{Filter} the candidates to only those that can be coerced successfully to the desired type.
* Select the best candidate among the remaining ones, based on priority.
  *  The relative "distance" of declarations needs to factor in (more derived vs. more base, imported vs. local, etc.)
  *  Additionally, the relative cost of the type conversions applied (if any) may be relevant.


The second case (overloaded calls) is superficially similar, in that we can filter the candidates to the applicable ones and then pick the best.
The definition of ``best'' for an overloaded call is more subtle and needs care to not mess up developer expectations for things like simple infix expressions (since event infix `operator+` is handled as an overloaded call, semantically).

A few basic principles that guide intuition:


* For every candidate we should know the conversion/cost associated with each argument position, as well as the conversion/cost associated with the function result position (if we are in a checking rather than synthesis context).
* One overload candidate is strictly better than another if it is better at at least one position (one argument, or the function result), and not worse at any position.
* When choosing between candidates that are equally good, a few factors play in:
  *  The relative "distance" of declarations (as determined by lookup)
  *  Which candidates required defaulting of arguments (and how many)
  *  Candidates that required implicit specialization of a generic vs. those that didn't
  *  For two candidates that required implicit specialization of a generic, which of them is ``more general'' than the other.


Generally, a function $f$ is ``more general'' than another function $g$ if for every set of arguments that $g$ is applicable to, $f$ is also applicable, but not vice versa.

Also: it doesn't exactly belong in this chapter, but something needs to document the rules for when two function declarations are considered to have the same signature (or at least conflicting signatures), so that errors can be diagnosed when trying to redefine a function.

</div>

If:

* _f_ synthesizes function type `(` _params_ `)` `->` _result_
* _args_ matches against _params_ with cost _argsCost_
* _result_ is implicitly convertible to _T_ with cost _resultCost_

then the invocation _f_ `(` _args_ `)` checks against _T_ with cost (_argsCost_, _resultCost_)

If:

* _g_ synthesizes generic type `<` _genericParams_ `>` `->` _result_
* _genericArgs_ are fresh solver variables
* the specialization _g_ `<` _genericArgs `>` synthesizes type _specialized_ with cost _specializationCost_
* the type `_specialized_

then the invocation _g_ `(` )