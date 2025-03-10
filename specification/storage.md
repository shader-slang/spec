Storage [storage]
=======

Concrete Storage Locations [storage.concrete]
--------------------------

A <dfn>concrete storage location</dfn> with layout *L* for storable type |T| comprises a set of contiguous [=memory locations=], in a single [=address space=], where a value of type |T| with layout *L* can be stored.

### Reference Types [storage.concrete.type]

A <dfn>reference type</dfn> is written |m| `ref` |T| where |m| is a [=memory access mode=] and |T| is a storable type.

<div class="issue">
How do we get layout involved here?
</div>

#### Type Conversion [storage.concrete.type.conversion]

An expression of reference type `modify` `ref` |T| can be implicitly coerced to type `read` `ref` |S| if |T| is subtype of |S|.

An expression of reference type `modify` `ref` |T| can be implicitly coerced to type `write` `ref` |S| if |S| is subtype of |T|.

An expression of reference type `read` `ref` |T| can be implicitly coerced to type |T|.

Abstract Storage Locations [storage.abstract.location]
--------------------------

An <dfn>abstract storage location</dfn> is a logical place where a value of some proper type |T| can reside.

A [=concrete storage location=] is also an [=abstract storage location=].

Example: A local variable declaration like `var x : Int;` defines an [=abstract storage location=], and a reference to `x` will have the [=abstract storage reference type=] `read modify Int`.

Abstract Storage Access [storage.abstract.access]
-----------------------

An <dfn>abstract storage access</dfn> is an operation performed by a [=strand=] on an [=abstract storage location=].
Each [=abstract storage access=] has an [=abstract storage access mode=].

Access Mode [storage.abstract.access.mode]
------------

An <dfn>abstract storage access mode</dfn> is either `get`, `set`, or a [=memory access mode=].

Abstract Storage References [storage.abstract.reference.type]
---------------------------

An <dfn>abstract storage reference type</dfn> is written |m| |T| where |T| is a proper type and |m| is a set of one or more [=abstract storage access modes=].

<div class="issue">
Some of the access types imply others, and it is inconvenient to have to write all explicitly in those cases.
For example:

* If you have `read` access, you can also perform a `get` (if the stored type is copyable).
* If you have `modify` access, you can also perform a `write`.
* If you hae `modify` or `write` access, you can also perform a `set` (if the stored type is copyable).

(Having `modify` access doesn't let you perform a `read` or `get`, because it implies the possibility of write-back which could in principle conflict with other accesses)

</div>

### Type Conversion [storage.abstract.reference.type.conversion]

An expression with [=reference type=] `read` `ref` |T| can be implicitly coerced to an [=abstract storage reference type=] `read` |T|.

An expression with [=reference type=] `write` `ref` |T| can be implicitly coerced to an [=abstract storage reference type=] `write` |T|.

An expression with [=reference type=] `modify` `ref` |T| can be implicitly coerced to an [=abstract storage reference type=] `read write modify` |T|.

An expression with [=abstract storage reference type=] |a| |T| can be implicitly coerced to [=abstract storage reference type=] |b| |T| if |b| is a subset of |a|.

An expression with an abstract storage type |m| |T| can be implicitly coerced to an abstract storage type |m| |S| if all of the following are true:

* |S| is a subtype of |T| unless |m| does not contain any of `write`, `modify`, and `set`
* |T| is a subtype of |S| unless |m| does not contain any of `read`, `modify`, and `get`

Containment [storage.location.contain]
-----------

An abstract storage location may contain other abstract storage locations.

Two [=abstract storage locations=] overlap if they are the same location, or one transitively contains the other.

An abstract storage location of an array type |T|`[`|N|`]` contains |N| storage locations of type |T|, one for each element of the array.

An abstract storage location of a `struct` type |S| contains a distinct storage location for each of the [=fields=] of |S|.


### Conflicts [storage.access.conflict]

An [=abstract storage access=] performed by a strand begins at some point |b| in the execution of that strand, and ends at some point |e| in the execution of that strand.
The interval of an [=abstract storage access=] is the half-open interval [|b|, |e|).

The intervals [|a0|, |a1|) and [|b0|, |b1|) overlap if either:

* |a0| happens-before |b0| and |b0| happens-before |a1|
* |b0| happens-before |a0| and |a0| happens-before |b1|

Two [=abstract storage accesses=] |A| and |B| overlap if all of the following:

* The [=abstract storage location=] of |A| overlaps the [=abstract storage location=] of |B|
* The interval of |A| overlaps the interval of |B|

Two distinct [=abstract storage accesses=] |A| and |B| conflict if all of the following:

* |A| and |B| overlap
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

* A member-access expression |x|.|m| where |x| is an abstract storage location of some struct type |S| and |m| is a field of |S|

* A member-access expression |x|.|p| where |p| is a property

* A subscript exrpession |x|`[`|i|`]` that resolves to an invocation of a `subscript` declaration

Examples of expressions that perform an abstract storage access include:

* An assignment |dst| `=` |src| performs a write to |dst|. It also performs a read from |src| if |src| is an abstract storage location.

* A call `f(... a ... )` where argument `a` is an abstract storage location performs an abstract storage access based on the direction of the corresponding parameter:

  * An `in` parameter performs a read access that begins and ends before the strand enters the body of `f`

  * An `out` parameter begins a write access before the call begins, and ends it after the call returns. The abstract storage location `a` must have been uninitialized before the call, and will be initialized after the call.

  * An `inout` parameter begins a modify access before the call that ends after the call returns. The abstract storage location `a` must have been initialized before the call.

  * TODO: `ref` etc.
