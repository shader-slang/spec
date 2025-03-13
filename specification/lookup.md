Lookup [lookup]
======

**Lookup** is an operation that takes a *name* and maps it to zero or more *candidate* meanings, in a particular *static context*.

Two kinds of *lookup* may be performed when checking Slang *expressions*:

* **simple lookup** of a *name* on its own; for example, as part of a *name expression*

* **member lookup** of a *name* inside of a base *expression*; for example, as part of a *member expression*

Names [lookup.name]
=====

TODO: The definition of _Name_ really belongs in another section.

```.semantics
Name
    => ParsedName
    => SpecialName

ParsedName
    => Identifier
    => `operator` InfixOperator
    => `operator` `prefix` PrefixOperator
    => `operator` `postfix` PostfixOperator

SpecialName
    => `$init`
    => `$subscript`
    => `$this`
    => `$This`
    => `$continue`
    => `$break`
```

> Note:
>
> A *parsed name* is a name that can appear in Slang source code.
> *Parsed names* include the ordinary case of simple identifiers, but also allow operators to be named.
>
> A *special name* is a name that cannot appear in Slang soure code.
> *Special names* are used by this specification to allow the mechanisms for lookup and overload resolution to be shared by multiple kinds of declarations.

Lookup in a Context [lookup.context]
===================

To *look up* a *name* _n_ in *context* _c_:

* Let _scope_ be the *current scope* of _c_

* Let _result_ be the result of looking up _n_ in _scope_

* Return _result_

Bindings [lookup.binding]
========

```.semantics
Binding
    => Name `=` value:CheckedExpression
```

To *look up* a *name* _n_ in a *binding* _b_:

* If the name of _b_ is not _n_ return an empty list of *candidates*

* Otherwise, return the value of _b_

Scopes [lookup.scope]
======

```.semantics
Scope
    => EmptyScope
    => Binding
    => LayeredScope
    => TypeScope
    => InstanceScope
    => DeclarationScope
    => FileScope
    => ModuleScope
```

Empty Scopes [lookup.scope.empty]
------------

```.semantics

EmptyScope
    => `$Empty`
```

The result of *looking up* a *name* in an *empty scope* is an empty list of *candidates*.

Layered Scopes [lookup.scope.layer]
--------------

```.semantics
LayeredScope
    => inner:Scope outer:Scope
```

To *look up* a name _n_ in a *layered scope* _s_:

* Let variable _innerCandidates_ be the result of *looking up* _n_ in the inner scope _s_

* Let variable _outerDistances_ be the result of *looking up* _n_ in the outer scope of _s_

* Let _k_ be a fresh *distance key*

* For each _candidate_ in _innerCandidates_:

  * Extend _candidate_ with a *disance* with key *key* and value zero

* For each _candidate_ in _outerCandidates_:

  * Extend _candidate_ with a *distance* with key *key* and value one

* Return the union of _innerCandidates_ and _outerCandidates_

Type Scopes [lookup.scope.type]
-----------

```.semantics
TypeScope
    => `$ThisType` `=` implicitThisType:Type
```

> A *type scope* represents a scope in which an implicit `This` type is available.

To *look up* a *name* _n_ in a *type scope* _s_ with *distances* _ds_:

* Let _thisType_ be the implicit `This` type of _s_

* If _n_ is `$ThisType`, return `$Candidate(` _thisType_ `,` _ds_ `)`

* If _n_ is `$this`, return `$Candidate(` `$Error` `,` _ds_ `)`

* Otherwise, return the result of looking up _n_ in _thisType_ with _ds_

Instance Scopes [lookup.scope.instance]
---------------

```.semantics
InstanceScope
    => `$this` `=` implicitThisParameter:CheckedExpression
```

> An *instance scope* represents a scope in which an implicit `this` expression is available.

To *look up* a *name* _n_ in an *instance scope* _s_:

* Let _thisExpr_ be the implicit `this` parasmeter of _s_

* If _n_ is `$this`, return _thisExpr_

* Otherwise, return the result of looing up _n_ in _thisExpr_ with _ds_

Declaration Scopes [lookup.scope.decl]
------------------

```.semantics
DeclarationScope
    => `$DeclarationScope(` DeclarationReference `)`
```

To *look up* a *name* _n_ in a *declaration scope* _s_:

* Return the result of looking up _n_ in the declaration reference of _s_

File Scope [lookup.scope.file]
----------

```.semantics
FileScope
    => `$FileScope(` SourceUnit `)`
```

To *look up* a *name* _n_ in a *file scope* _s_:

* Let _sourceUnit_ be the source unit of _s_

* Let variable _result_ be an empty set of *candidates*

* For each *import declaration* _importDecl_ in _s_:

  * Let _importedModule_ be the *module* imported by _importDecl_

  * // need to fill out the details here, since visibility matters for this case

* Return _result_

Note: File scopes only handle lookup of declaration from modules `import`ed into a particular source unit; they do not do anything around lookup of declarations inside the module itself.

Module Scope [lookup.scope.module]
------------

```.semantics
ModuleScope
    => `$ModuleScope(` Module `)`
```

To look up a _name_ in a *module scope* _s_:

* Let _m_ be the module of _s_

* Let variable _result_ be an empty set of *candidates*

* For each _sourceUnit_ in _m_

  * Let _suResult_ be the result of looking up _name_ in _sourceUnit_

  * Set _result_ to the union of _result_ and _suResult_

* Return _result_


Note: Lookup at module scope can always just return direct declaration references, since no qualification is needed.


Member Lookup [lookup.member]
=============

Expressions [lookup.member.expr]
-----------

To *look up* the name _n_ in a *checked expression* _e_ that is not a *type*

* Let _t_ be the type of _e_

* Let _typeResult_ be the result of looking up _n_ in _t_

* Let variable _result_ be an empty lookup result

* For each *candidate* _typeCandidate_ in _typeResult_:

  * Let _memberDeclRef_ be the declaration reference of _typeCandidate_

  * Let _distances_ be the distances of _typeCandidate_

  * If the declaration of _memberDeclRef_ is *effectively static*:

    * Add _typeCandidate_ to _result_

  * Otherwise:

    * Let _memberRef_ be the *checked* *member expression* _e_ `.` _member_

    * Add `$Candidate(` _memberRef_ `,` _distances_ `)` to _result_

* If _t_ is a *pointer-like type*:

  * Let _pt_ be the pointee type of _t_

  * Let _derefExpr_ be the result of *dereferencing* _e_

  * Let _derefCandidates_ be the result of looking up _n_ in _derefExpr_

  * Add all candidates from _derefCandidates_ to _result_

* TODO: The swizzle cases go here...

* Return _result_

Declaration References [lookup.member.decl-ref]
----------------------

To *look up* a *name* _n_ in a *fully specialized* *declaration reference* _declRef_ that is not a *type*:

* Let _memberDecls_ be the result of directly looking up _n_ in the declaration of _baseDeclRef_

* Let variable _result_ be an empty set of *candidates*

* For each _memberDecl_ in _memberDecls_:

  * Let _memberDeclRef_ be `$StaticMemberRef(` _baseDeclRef_ `$,` _memberDecl_ `$)`

  * Let _memberCandidate_ be `$Candidate(` _memberDeclRef `$, {} )`

  * Add _memberCandidate_ to _result_

* return _result_

Generics [lookup.member.generic]
--------

To *look up* a *name* _n_ in a *generic declaration reference* _genericRef_:

* Let _declRef_ be the result of *instantiating* _genericRef_

* Return the result of *looking up* _n_ in _declRef_

Type [lookup.member.type]
----

To *look up* a *name* _n_ in a *type* _t_:

* Let _facets_ be the result of *linearizing* _t_

* Let variable _result_ be an empty lookup result

* For each _facet_ in _facets_:

  * Let _facetResult_ be the result of looking up _n_ in _facet_

  * Set _result_ to the union of _result_ and _facetResult_

* Return _result_

Direct Lookup [lookup.direct]
=============

Note: **Direct** lookup refers to the case where there is no attempt to perform recursive or hierarchical walks.

Facets [lookup.direct.facet]
------

To directly look up name _n_ in a *facet* _f_:

* Let *declaration reference* _ancestor_ be the ancestor of _f_

* Let _ancestorResult_ (a list of *declarations*) be the result of directly looking up _n_ in _ancestor_

* Let _distances_ be the *distances* of _f_

* Let variable _result_ be an empty lookup result

* For each *declaration* _ancestorDecl_ in _ancestorResult_:

  * Let _derivedDeclRef_ be `$MemberLookup` _f_ _ancestorDecl_

  * Let _candidate_ be `$Candidate(` _derivedDeclRef_ `,` _distances_ `)`

  * Add _candidate_ to _result_

* Return _result_

Note: Each *facet* in the *linearization* of a type _t_ already stores *distances* to represent the relative priority of nodes in the inheritance graph of _t_. By including those distances in the result of lookup, other parts of the specification that need to consider such prioritization do not need to inspect the inheritance graph itself.

TODO: As described above, a member lookup into the facet (a subtype witness) always gets generated. This really shouldn't be the case, depending on the nature of the facet. A direct facet (representing the type itself) should simply return a static member reference, as should any `extension` facets. A conformance facet should be the ones to look up a conforming member.

Declarations [lookup.direct.decl]
------------

To directly look up name _n_ in a *declaration* _baseDecl_:

* If _baseDecl_ does not have a *declaration body*:

  * Return an empty *lookup result*

* Let _results_ be an empty set of *declarations*

* For each _memberDecl_ in the declaration body of _baseDecl_

  * let _memberName_ be the name of _memberDecl_

  * If _memberName_ is equal to _name_:

    * Add _memberDecl_ to _result_

* Return _result_

