Lookup [lookup]
======

<div class=issue>

This chapter needs to document the rules for how names are looked up in two cases:


* Looking up a standalone Identifier as an expression or type expression, we need to look up in the current context.
* When looking up a name in some type, whether explicitly as part of a MemberExpression, or implicitly as part of lookup through `this` inside a type body.


The first kind of lookup is easily expressed as a recursion over the structure of contexts, but will often bottleneck through lookup in the context of some type (since code is so often nested under a type).
This kind of lookup also needs to deal with `import` declarations and the visibility rules for [=source units=] in the same module as one another.

The second kind of lookup requires access to a linearization of the type.
It potentially needs to deal with performing substitutions on the type/signature of a declaration that is found, so that it is adjusted for the `This` type it has been looked up through.

Both kinds of lookup need to deal with the possibility that a name will be \emph{overloaded}.
At this level, lookup should probably return the full set of all \emph{candidates} when overloading occurs, but retain enough structure in the lookup results that overload resolution can evaluate which should be prioritized over the others, based (e.g., picking members from a more-derived type over those from a base type).

The lookup rules here should be able to handle lookup of `init`, and `subscript` declaration via a synthesized name that cannot conflict with other identifiers (in case, e.g., a user has a struct with an ordinary field named \texttt{subscript}).

Lookup will also need to interact with visibility, by stripping out non-`public` bindings from `import`ed modules.

Note that this chapter does not need to deal with `extension` declarations, as they are handled as part of type linearization.

One important kind of subtlety to lookup is that upon finding a \emph{first} in-scope declaration of a name, we can inspect the category of that declaration to determine if overloading is even possible.
That is, if the first declaration found is in a category of declaration that doesn't support overloading (basically anything other than a `func`, `init`, or `subscript`), then that result can be used as-is as the result of lookup.

</div>
