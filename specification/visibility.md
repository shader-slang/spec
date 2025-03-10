Visibility Control [vis]
==================

<div class=issue>
This chapter needs to explain the rules for:



* What declarations in a module are visible to modules that `import` it?

* What are the modifiers that can be used to control visibility (`public`, `internal`, `private`), and what are their semantics.

* What is the inferred visibility of a declaration without an explicit modifier?

* What are the rules about what modifiers are legal in what contexts?
  *  E.g., a `public` field should not be allowed in an `internal` type.
  *  E.g., a `public` function should not be allowed to have a non-`public` type used in its signature.

* How is visibility controlled for interface conformances?


</div>