Overloading [overload]
===========

**Overloading** occurs when a single *name* has multiple meanings in a given context.

Overload Sets [overload.set]
=============

```.semantics
OverloadSet
    => `$OverloadSet(` Candidate* `)`
```

An *overload set* is an *intermediate expression* that represents a set of *candidate* meanings.

Simplification [overload.set.simplify]
--------------

The **simplification** of an *overload set* is a *checked expression*.

The compute the *simplification* of an *overload set* _overloadSet_:

* If _overloadSet_ has exactly one *candidate* _c_:

  * Return the value of _c_

* If _overloadSet_ has no *candidates*:

  * return `$Error`

* Return _overloadSet_

Filtering [lookup.result.filter]
---------

TODO: Need to specify how to filter an overload set down to only those candidates that satisfy some predicate

Candidates [overload.candidate]
==========

A *candidate* represents on possible meaning for a *name* or *expression* in a given context.

```.semantics
Candidate
    => `$Candidate` CheckedExpression Distance* Cost Constraint*

Cost
    => `$NoCost`
    => `$Infinite`
    => /* need a representation for costs */

Constraint
    => /* need a representation for solver constraints */
```

Distances [overload.candidate.distance]
---------

```.semantics
Distance
    => DistanceKey value:Integer

DistanceKey
    => UniqueID
```

Given *candidate* _a_, *candidate* _b_, and *distance key* _k_, _a_ is **closer for** _k_ than _b_ if:

* There exists a *distance* _da_ in _a_ with *key* _k_

* There exists a *distance* _db_ in _b_ with *key* _k_

* The value of _da_ is less than the value of _db_

A *candidate* _a_ is **closer** than _b_ if:

* There exists a _k0_ such that _a_ is *closer for* _k0_ than _b_

* There does not exist any _k1_ such that _b_ is *closer for* _k1_ than _a_

Resolution [overload.resolution]
==========

TODO: Overload resolution should basically just amount to finding a minimal-cost (or highest-priority, equivalently) element in the set of candidates.

Type Conversion [overload.conversion]
===============

> When an *overload set* is implicitly converted to a specific *type*, it is possible to filter candidates to only those that can be converted to that type.

To implicitly convert an *overload set* _overloadSet_ to *type* _toType_:

* Let variable _result_ be an empty overload set

* For each *candidate* _fromExpr_ _distances_ _fromCost_ _fromConstraints_ in _overloadSet_:

  * Let _scope_ be a fresh *solver scope*

  * Copy each of the _fromConstraints_ into _scope_

  * With _scope_:

    * let _toExpr_ _toCost_ be the result of implicitly converting _fromExpr_ to _toType_

    * If _toCost_ is not `$Infinite`:

      * let _cost_ be the merge of _toCost_ and _fromCost_

      * let _constraints_ be the constraints of _scope_

      * let _candidate_ be a fresh *candidate* _toExpr_ _distances_ _cost_ _constraints_

      * Add _candidate_ to _result_

* Return _result_

Overloaded Calls [overload.call]
================

To check a call to an _overloadSet_ on a list of _arguments_:

* Let variable _result_ be an empty overload set

* For each *candidate* _f_ _distances_ _fromCost_ _fromConstraints_ in _overloadSet_:

  * Let _scope_ be a fresh *solver scope*

  * Copy each of the _fromConstraints_ into _scope_

  * With _scope_:

    * Let _candidateCall_ _callCost_ be the result of checking a call to _f_ on _arguments_

    * If _candidateCallCost_ is not `$Infinite`:  

      * let _cost_ be the merge of _callCost_ and _fromCost_

      * let _constraints_ be the constraints of _scope_

      * Add *candidate* _candidateCall_ _distances_ _cost_ _constraints_ to _result_

* Return _result_

Calling a Generic
=================

To check a call to a *generic declaration reference* _genericDeclRef_ on a list of _arguments_:

* Let _declRef_ be the result of *instantiating* _genericDeclRef_

* Return the result of calling _declRef_ on _arguments_

Calling a Function
==================

To check a call to a *fully-specialized declaration reference* _f_ on a list of _arguments_, where _f_ refers to a *function declaration*:

* Match the arguments to the parameters by index and/or name (and build a cost model)

* For each _arg_ and its corresponding _param_:

  * Let _convertedArg_ be the result of implicitly converting _arg_ to the type of _param_

  * // Need to take "direction" into account...

  * // Need to accumulate the cost of each _convertedArg_

* // Construct the checked call expression, with its full cost

Calling a Type
==============

To check a call to a *type* _t_ on a list of _arguments_:

* If there is exactly one element _arg_ in _arguments_:

  * Return the result of *explicitly converting* _arg_ to _t_

* Let _init_ be the result of looking up `$init` in _t_

* Return the result of calling _init_ on _arguments_

