Type Linearization [lin]
==================

The **linearization** of a *type*, in a given *context*, comprises a sequence of *facets*.

Facets [lin.facet]
======

```.semantics
Facet
    => descendent:Value ancestor:DeclarationReference PriorityTag*
```

> A *facet* represents the fact that a given type has/provides access to the members of a given declaration.

Note: A *facet* is usable as a *witness* for the appropriate relationship. For example, a facet for an base type in the linearization of a derived type *is* the witness for the subtype relationship. Similarly, a facet for an interface in some concrete type *is* a witness for the conformance relationship.

Algorithm [lin.algo]
=========

To calculate the *linearizatin* of *type declaration reference* _d_ in *context* _C_:

* Let _id_ be a fresh *unique id*

* Let variable _resultLin_ be a an empty list of facets

* Let _directFacet_ be the facet _d_ _d_ `[` _id_ 1 `]`

* Add _directFacet_ to _resultLin_

* For each *declared base* _b_ of _d_:

  * Let variable _baseLin_ be a copy of the *linearization* of _b_ in _C_

  * For each _baseFacet_ in _baseLin_:

    * Set the descendent of _baseFacet_ to _d_

    * Add a *priority tag* with key _id_ and value 0 to _baseFacet_

  * Set _resultLin_ to the result of merging _resultLin_ and _baseLin_

* For each extension declaration _extDecl_ that is visible in _C_:

  * Attempt to apply _extDecl_ to _d_:

    * If the attempt succeeds, yielding *extension declaration reference* _extDeclRef_:

      * Let _extLin_ be a copy of the *linearization* of _extDeclRef_ in _C_

      * For each _baseFacet_ in _baseLin_:

        * Set the descendent of _baseFacet_ to _d_

        * Add a *priority tag* with key _id_ and value 0 to _baseFacet_

      * Set _resultLin_ to the result of merging _resultLin_ and _baseLin_

* Return _resultLin_

To calculate the *linearization* of a *conjunction* type _t_, of the form `$And(` _left_ `,` _right_ `)`:

* Let _leftLin_ be a copy of the *linearization* of _left_ in _C_

* For each _f_ in _leftLin, set the descendent of _f_ to _t_

* Let _rightLin_ be a copy of the *linearization* of _right_ in _C_

* For each _f_ in _rightLin_, set the descendent of _f_ to _t_

* Return the result of *merging* _leftLin_ and _rightLin_

Merging
=======

To calculate the merge of *linearizations* _left_ and _right_:

* Let variable _result_ be an empty linearization

* Loop:

  * If _left_ is empty:

    * Return the concanentation of _result_ and _right_

  * If _right_ is empty:

    * Return the concatenation of _result_ and _left_

  * Let _firstLeft_ be the first element of _left_

  * If _right_ does not contain a facet with the same ancestor as _firstLeft_:

    * Pop _firstLeft_ from the front of _left_

    * Append _firstLeft_ to _result_

    * Continue

  * Let _firstRight_ be the first element of _right_

  * If _left_ does not contain a facet with the same ancestor as _firstRight_:

    * Pop _firstRight_ from the front of _right_

    * Append _firstRight_ to _result_

    * Continue

  * Pop _firstLeft_ from the front of _left_

  * Let _matchRight_ be the first facet in _right_ with the same ancestor as _firstLeft_

  * Remove _matchRight_ from _right_

  * Let _merged_ be the result of merging _firstLeft_ and _matchRight_

  * Append _merged_ to _result_

  * Continue

To merge *facets* _left_ and _right_:

* Assert: _left_ and _right_ have the same descendent

* Assert: _left_ and _right_ have the same ancestor

* Let _d_ be the descendent of _left_

* Let _a_ be the ancestor of _left_

* Let _leftKeys_ be the set of keys of the priority tags of _left_

* Let _rightKeys_ be the set of keys of the priority tags of _right_

* Let _keys_ be the union of _leftKeys_ and _rightKeys_

* Let variable _tags_ be an empty list of priority tags

* For each _k_ in _keys_:

  * let _val_ be the minimum of:

    * the value of any priority tag of _left_ with key _k_

    * the value of any priority tag of _right_ with key _k_

  * Add priority tag _k_ _val_ to _tags_

* Return the *facet* _d_ _a_ _tags_

Fodder
======


If *type* _t_ is a subtype of *type* _s_ in *context* _c_, and _s_ is a *declaration reference* to a *type declaration* with a *declaration body*, then the *linearization* of _t_ in _c_ has a *facet* corresponding to _s_.

If *type* _t_ implements *interface* _i_ in *context* _c_, then the *linearization* of _t_ in _c_ has a *facet* corresponding to _i_.

TODO: need to communicate that if _a_ is a subtype of _b_, then _a_ will precede _b_ in the linearization. And same if interface _i_ extends interface _j_; _i_ will precede _j_.

Issue: it may be that it is more effective to define an inhertiance graph (a DAG) first, rather than starting with the linearization. The main reason to do this is so that things like overload resolution won't treat methods from unrelated types _x_ and _y_ as having a well-defined relative priority order, when they shouldn't.


> Issue:
> 
> This chapter needs to explain how, given a type, an implementation should derive the \emph{linearization} of that type into an ordered list of \emph{facets}.
> Each facet corresponds to some DeclBody, and thus has a set of declarations in it that may bind certain names.
> 
> The linearization of a type should include:
> 
> 
> * A facet for the type itself, which will include the declarations explicitly written inside the body of that type's DeclBody.
> 
> * One facet for each transitive base of the type, including both concrete types it inherits from and `interface`s it conforms to.
> 
> * One facet for each `extension` that is both visible in the context where linearization is being performed \emph{and} applicable to the type.
> 
> 
> Note that base facets are included even for bases that are introduced via an `extension`.
> Similarly, extension facets are included for extensions that might apply to the type through one of its bases.
> 
> The set of facets for a type will always be a subset of those for each of its bases.
> 
> The order of facets is significant, because it affects the relative priority of the bindings in those facets for lookup.
> In the simplest terms, facets earlier in the list will be prioritized over those later in the list.
> Thus, derived types should always appear before their bases.
> In general, facets for extensions should appear after the facet for the type declaration that the extension applies to.
> 
> (It is possible that a simple \emph{sequence} of facets will not actually be sufficient, and a DAG representation might be needed, if forcing a total ordering on facets would risk > unintuitive lookup results)
> 
> There is good precedent in the PL world for this kind of linearization, which is sometimes referred to as the \emph{method resolution order} (MRO).
> A particular solution, known as the \emph{C3 linearization algorithm} is often recommended as the one to use, and it is what the Slang compiler currently implements.
