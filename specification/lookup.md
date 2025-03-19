Lookup [lookup]
======

**Lookup** is an operation that takes a *name* and maps it to zero or more *candidate* meanings that the *name* has in a particular entity.
Lookup may be performed in a *static context*, or in a particular *expression* or *declaration*.

> Note:
>
> *Lookup* is performed in a *static context* when a *name* is used by itself as an *expression*.
>
> *Lookup* is performed in an *expression* as part of checking a *member expression*.

Names [lookup.name]
=====

TODO: The definition of _Name_ really belongs in another section.

```.semantics
Name
    => ParsedName
    => SpecialName

ParsedName
    => Identifier
    => `operator` InfixOperator ` `
    => `operator` `prefix` PrefixOperator ` `
    => `operator` `postfix` PostfixOperator ` `

SpecialName
    => `$init`
    => `$subscript`
    => `$this`
    => `$This`
```

TODO: The formatting of the above grammar block is wrong; fixes are required to the script that extracts and formats the grammars.

> Note:
>
> A *parsed name* is a name that can appear in Slang source code.
> *Parsed names* include the ordinary case of simple identifiers, but also allow operators to be named.
>
> A *special name* is a name that cannot appear in Slang soure code.
> *Special names* are used by this specification to allow the mechanisms for lookup and overload resolution to be shared by multiple kinds of declarations.

Lookup Predicates [lookup.predicate]
=================

A **lookup predicate** is a *predicate* on *declarations*.

Lookup Transform [lookup.transform]
================

A **lookup transform** is a compile-time operation that takes a *declaration reference* as input and returns a *declaration reference* as output.

Lookup Queries [lookup.query]
==============

A **lookup query** is an object that consists of:

* the *name* being looked up

* an optional *lookup predicate* to be used to filter *candidates*

* a mutable list of *candidates* that have been collected

* a mutable stack of *distances* to apply to candidate values

* a mutable stack of *lookup transforms* to apply to candidate values

To add a *declaration* _d_ to a *lookup query* _q_:

* if _d_ satisfies the *lookup predicate* of _q_

  * let variable _declRef_, a *declaration reference*, be a *direct declaration reference* to _d_

  * for each *lookup transform* _f_ of _q_ in top-down order:

    * set _declRef_ to the result of applying _f_ to _declRef_

  * let _d_ be the distances of _q_

  * let _candidate_ be a *candidate* with _declRef_ and _d_

  * append _candidate_ to the candidtes of _q_

Algorithm [lookup.algo]
=========

To *look up* a *name* _n_ in some entity _e_ with optional *lookup predicate* _p_:

* if _p_ is absent:

  * set _p_ to a *lookup predicate* that is true for *declarations* that *should be included in default lookup results*

* let _q_ be a fresh *lookup query* with name _n_ and predicate _p_

* with _q_:

  * *collect lookup candidates* from _e_

* let _candidates_ be the candidates of _q_

* if _candidates_ contains a *candidate* _best_ such that _best_ *shadows* all of the other *candidates* in _candidates_

  * return the expression of _best_

* if _candidates_ is empty:

  * fail with an error

* if _candidates_ has a single entry _c_:

  * return the expression of _c_

* otherwise:

  * return an *overload set* with _candidates_

**Collecting lookup candidates** from an entity is an operation performed in context of some *lookup query*.

A *declaration* _d_ **should be included in default lookup results** if all of the following are true:

* _d_ is not an *attribute declaration*

* _d_ is not a *system-value declaration*

* // ...

Shadowing [lookup.shadow]
=========

A *candidate* _a_ **shadows** a *candidate* _b_ if:

* _a_ is *closer* than _b_

* the expression of _a_ is not *overloadable*

A *checked expression* _e_ is **overloadable** if:

* _e_ is a *declaration reference* to some declaration _d_

* _d_ is one of:

  * a *function declaration*

  * a *constructor declaration*

  * a *subscript declaration*



Lookup in a Context [lookup.context]
===================

To *collect lookup candidates* from a *context* _c_:

* let _scope_ be the *current scope* of _c_

* *collect lookup candidates* from _scope_

Bindings [lookup.binding]
========

```.semantics
Binding
    => Name `=` Declaration
```

> A *binding* associates a *name* with a single meaning (a *declaration*) that it denotes.

> Note:
>
> Many formal type systems have bindings that associate a name with a type, but the representation of *bindings* here assocaites a *name* with a *checked expression* (which has a type).

To *collect lookup candidates* from a *binding* _b_:

* let _queryName_ be the name of the current *lookup query*

* if the name of _b_ is equal to _queryName_:

  * let _v_ be the value of _b_

  * add _v_ to the current *lookup query*

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

To *collect lookup candidates* from an *empty scope*, do nothing.

Layered Scopes [lookup.scope.layer]
--------------

```.semantics
LayeredScope
    => inner:Scope outer:Scope
```

To *collect lookup candidates* from a *layered scope* _s_:

* let _k_ be a fresh *distance key*

* with a *distance* with key _k_ and value zero:

  * *collect lookup candidates* from the inner scope of _s_

* with a *distance* with key _k_ and value one:

  * *collect lookup candidates* from the outer scope of _s_

> Note:
>
> The intention of the algorithm here is that every *candidate* found through the inner *scope* should be considered closer than ever *candidate* find through the outer *scope*.

Type Scopes [lookup.scope.type]
-----------

```.semantics
TypeScope
    => `$ThisType` `=` implicitThisType:Declaration
```

> A *type scope* represents a scope in which an implicit `This` type is available.

To *collect lookup candidates* a *type scope* _s_:

* if _n_ is `$ThisType`:

  * let _thisType_ be the implicit `This` type of _s_

  * add _thisType_ to _q_ to the current *lookup query*

* if _n_ is `$this`:

  * add `$thisInStaticContext`  to the current *lookup query*

* *collect lookup candidates* from _thisType_

Instance Scopes [lookup.scope.instance]
---------------

```.semantics
InstanceScope
    => `$this` `=` implicitThisParameter:Declaration
```

> An *instance scope* represents a scope in which an implicit `this` expression is available.

To *collect lookup candidates* from an *instance scope* _s_:

* if _n_ is `$this`:

  * let _thisParam_ be the implicit `this` parameter of _s_

  * add _thisParam_ to _q_

* *collect lookup candidates* from _thisExpr_

Declaration Scopes [lookup.scope.decl]
------------------

```.semantics
DeclarationScope
    => `$DeclarationScope(` DeclarationReference `)`
```

To *collect lookup candidates* from a *declaration scope* _s_:

* let _declRef_ be the declaration reference of _s_

* *collect lookup candidates* from _declRef_

File Scope [lookup.scope.file]
----------

```.semantics
FileScope
    => `$FileScope(` SourceUnit `)`
```

To *collect lookup candidates* from a *file scope* _s_:

* let _sourceUnit_ be the source unit of _s_

* for each *import declaration* _importDecl_ in _sourceUnit_:

  * let _importedModule_ be the *module* imported by _importDecl_

  * // need to fill out the details here, since visibility matters for this case

Note: File scopes only handle lookup of declaration from modules `import`ed into a particular source unit; they do not do anything around lookup of declarations inside the module itself.

Module Scope [lookup.scope.module]
------------

```.semantics
ModuleScope
    => `$ModuleScope(` Module `)`
```

To *collect lookup candidates* from a *module scope* _s_:

* let _m_ be the module of _s_

* for each _sourceUnit_ in _m_

  * *collect lookup candidates* from _sourceUnit_

Note: Lookup at module scope can always just return direct declaration references, since no qualification is needed.


Member Lookup [lookup.member]
=============

Expressions [lookup.member.expr]
-----------

To *collect lookup candidates* from a *checked expression* _e_, where _e_ is not a *type*:

* let _T_ be the type of _e_

* with a *lookup transform* that *tries to bind* a *declaration reference* to _e_:

  * *collect lookup candidates* from _T_

* if _T_ is a *pointer-like type*:

  * let _derefExpr_ be the result of *dereferencing* _e_

  * *collect lookup candidates* from _derefExpr_ for _q_

* // swizzle cases go here

To **try to bind** a *declaration reference* _memberDeclRef_ to a *checked expression* _e_:

* if the *declaration* of _memberDeclRef_ is *effectively static*:

  * return _memberDeclRef_

* otherwise:

  * return the *checked* *member expression* _e_ `.` _member_

TODO: The definition of *effectively static* needs to go somewhere.

Declaration References [lookup.member.decl-ref]
----------------------

To *collect lookup candidates* from a *fully-specialized* *declaration reference* _baseDeclRef_, where _baseDeclRef_ is not a *type*:

* with a *lookup transform* that *statically binds* a *declaration* to _baseDeclRef_

  * *collect direct lookup candidates* from the decalration of _baseDeclRef_

To **statically bind** a *declaration* _memberDecl_ to a *declaration reference* _baseDeclRef_:

* return a *checked* *static member reference* _baseDeclRef_ `::` _memberDecl_

TODO: This case is being slippery, since a *declaration reference* is itself an *expression*, so some rule needs to explain when this case applies vs. when the instance-member-lookup case applies.

Generics [lookup.member.generic]
--------

To *collect lookup candidates* from a *generic declaration reference* _genericRef_:

* let _declRef_ be the result of *instantiating* _genericRef_

* *collect lookup candidates* from _declRef_

Type [lookup.member.type]
----

To *collect lookup candidates* from a *type* _t_:

* let _facets_ be the result of *linearizing* _t_

* for each _facet_ in _facets_:

  * *collect lookup candidates* from _facet_

Direct Lookup [lookup.direct]
=============

Note: **Direct** lookup refers to the case where there is no attempt to perform recursive or hierarchical walks.

Facets [lookup.direct.facet]
------

To *collect direct lookup candidates* from a *facet* _f_:

* let *declaration reference* _ancestorDeclRef_ be the ancestor of _f_

* let _ancestorDecl_ be the *declaration* of _ancestorDeclRef_

* let _distances_ be the *distances* of _f_

* with _distances_ pushed on the current *lookup query*

  * with a *lookup transform* that transforms a *declaration* _d_ into `$DynamicLookup(` _f_ `,` _d_ `)`
  
    * *collect direct lookup candidates* from _ancestorDecl_

Note: Each *facet* in the *linearization* of a type _t_ already stores *distances* to represent the relative priority of nodes in the inheritance graph of _t_. By including those distances in the result of lookup, other parts of the specification that need to consider such prioritization do not need to inspect the inheritance graph itself.

TODO: As described above, a member lookup into the facet (a subtype witness) always gets generated. This really shouldn't be the case, depending on the nature of the facet. A direct facet (representing the type itself) should simply return a static member reference, as should any `extension` facets. A conformance facet should be the ones to look up a conforming member.

Declarations [lookup.direct.decl]
------------

To *collect direct lookup candidates* from a *declaration* _baseDecl_:

* if _baseDecl_ has a *declaration body* _body_:

  * for each _memberDecl_ in _body_:

    * add _memberDecl_ to the current *lookup query*
