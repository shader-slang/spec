Storage [storage]
=======

Concrete Storage Locations [storage.concrete]
--------------------------

A **concrete storage location** with layout *L* for storable type _T_ comprises a set of contiguous *memory locations*, in a single *address space*, where a value of type _T_ with layout *L* can be stored.

### Reference Types [storage.concrete.type]

A **reference type** is written _m_ `ref` _T_ where _m_ is a *memory access mode* and _T_ is a storable type.

<div class="issue">
How do we get layout involved here?
</div>

#### Type Conversion [storage.concrete.type.conversion]

An expression of reference type `modify` `ref` _T_ can be implicitly coerced to type `read` `ref` _S_ if _T_ is subtype of _S_.

An expression of reference type `modify` `ref` _T_ can be implicitly coerced to type `write` `ref` _S_ if _S_ is subtype of _T_.

An expression of reference type `read` `ref` _T_ can be implicitly coerced to type _T_.

Abstract Storage Locations [storage.abstract.location]
--------------------------

An **abstract storage location** is a logical place where a value of some proper type _T_ can reside.

A *concrete storage location* is also an *abstract storage location*.

Example: A local variable declaration like `var x : Int;` defines an *abstract storage location*, and a reference to `x` will have the *abstract storage reference type* `read modify Int`.

Abstract Storage Access [storage.abstract.access]
-----------------------

An **abstract storage access** is an operation performed by a *strand* on an *abstract storage location*.
Each *abstract storage access* has an *abstract storage access mode*.

Access Mode [storage.abstract.access.mode]
------------

An **abstract storage access mode** is either `get`, `set`, or a *memory access mode*.

Abstract Storage References [storage.abstract.reference.type]
---------------------------

An **abstract storage reference type** is written _m_ _T_ where _T_ is a proper type and _m_ is a set of one or more *abstract storage access modes*.

<div class="issue">
Some of the access types imply others, and it is inconvenient to have to write all explicitly in those cases.
For example:

* If you have `read` access, you can also perform a `get` (if the stored type is copyable).
* If you have `modify` access, you can also perform a `write`.
* If you hae `modify` or `write` access, you can also perform a `set` (if the stored type is copyable).

(Having `modify` access doesn't let you perform a `read` or `get`, because it implies the possibility of write-back which could in principle conflict with other accesses)

</div>

### Type Conversion [storage.abstract.reference.type.conversion]

An expression with *reference type* `read` `ref` _T_ can be implicitly coerced to an *abstract storage reference type* `read` _T_.

An expression with *reference type* `write` `ref` _T_ can be implicitly coerced to an *abstract storage reference type* `write` _T_.

An expression with *reference type* `modify` `ref` _T_ can be implicitly coerced to an *abstract storage reference type* `read write modify` _T_.

An expression with *abstract storage reference type* _a_ _T_ can be implicitly coerced to *abstract storage reference type* _b_ _T_ if _b_ is a subset of _a_.

An expression with an abstract storage type _m_ _T_ can be implicitly coerced to an abstract storage type _m_ _S_ if all of the following are true:

* _S_ is a subtype of _T_ unless _m_ does not contain any of `write`, `modify`, and `set`
* _T_ is a subtype of _S_ unless _m_ does not contain any of `read`, `modify`, and `get`

Containment [storage.location.contain]
-----------

An abstract storage location may contain other abstract storage locations.

Two *abstract storage locations* overlap if they are the same location, or one transitively contains the other.

An abstract storage location of an array type _T_`[`_N_`]` contains _N_ storage locations of type _T_, one for each element of the array.

An abstract storage location of a `struct` type _S_ contains a distinct storage location for each of the *fields* of _S_.


### Conflicts [storage.access.conflict]

An *abstract storage access* performed by a strand begins at some point _b_ in the execution of that strand, and ends at some point _e_ in the execution of that strand.
The interval of an *abstract storage access* is the half-open interval [_b_, _e_).

The intervals [|a0|, |a1|) and [|b0|, |b1|) overlap if either:

* |a0| happens-before |b0| and |b0| happens-before |a1|
* |b0| happens-before |a0| and |a0| happens-before |b1|

Two *abstract storage accesses* _A_ and _B_ overlap if all of the following:

* The *abstract storage location* of _A_ overlaps the *abstract storage location* of _B_
* The interval of _A_ overlaps the interval of _B_

Two distinct *abstract storage accesses* _A_ and _B_ conflict if all of the following:

* _A_ and _B_ overlap
* At least one of the accesses is a `write`, `modify`, or `set`

Expressions That Reference Storage [storage.expr]
----------------------------------

<div class="issue">
This text really belongs in the relevant sections about type-checking each of these expression forms.
</div>

Rather than evaluating to a value, of an expression may evaluate to an abstract storage location, along with restrictions on the kinds of access allowed to that location.
An expression that evaluates to an abstract storage location does not constitute an abstract storage access to that location.

Examples of expressions that evaluate to an abstract storage location include:

* An identifier expression that names some variable _v_

* A member-access expression _x_._m_ where _x_ is an abstract storage location of some struct type _S_ and _m_ is a field of _S_

* A member-access expression _x_._p_ where _p_ is a property

* A subscript exrpession _x_`[`_i_`]` that resolves to an invocation of a `subscript` declaration

Examples of expressions that perform an abstract storage access include:

* An assignment _dst_ `=` _src_ performs a write to _dst_. It also performs a read from _src_ if _src_ is an abstract storage location.

* A call `f(... a ... )` where argument `a` is an abstract storage location performs an abstract storage access based on the direction of the corresponding parameter:

  * An `in` parameter performs a read access that begins and ends before the strand enters the body of `f`

  * An `out` parameter begins a write access before the call begins, and ends it after the call returns. The abstract storage location `a` must have been uninitialized before the call, and will be initialized after the call.

  * An `inout` parameter begins a modify access before the call that ends after the call returns. The abstract storage location `a` must have been initialized before the call.

  * TODO: `ref` etc.
