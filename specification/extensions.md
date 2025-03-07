# Type Linearization {#linearization}

<div class=issue>

This chapter needs to explain how, given a type, an implementation should derive the \emph{linearization} of that type into an ordered list of \emph{facets}.
Each facet corresponds to some DeclBody, and thus has a set of declarations in it that may bind certain names.

The linearization of a type should include:


* A facet for the type itself, which will include the declarations explicitly written inside the body of that type's DeclBody.

* One facet for each transitive base of the type, including both concrete types it inherits from and `interface`s it conforms to.

* One facet for each `extension` that is both visible in the context where linearization is being performed \emph{and} applicable to the type.


Note that base facets are included even for bases that are introduced via an `extension`.
Similarly, extension facets are included for extensions that might apply to the type through one of its bases.

The set of facets for a type will always be a subset of those for each of its bases.

The order of facets is significant, because it affects the relative priority of the bindings in those facets for lookup.
In the simplest terms, facets earlier in the list will be prioritized over those later in the list.
Thus, derived types should always appear before their bases.
In general, facets for extensions should appear after the facet for the type declaration that the extension applies to.

(It is possible that a simple \emph{sequence} of facets will not actually be sufficient, and a DAG representation might be needed, if forcing a total ordering on facets would risk unintuitive lookup results)

There is good precedent in the PL world for this kind of linearization, which is sometimes referred to as the \emph{method resolution order} (MRO).
A particular solution, known as the \emph{C3 linearization algorithm} is often recommended as the one to use, and it is what the Slang compiler currently implements.
</div>