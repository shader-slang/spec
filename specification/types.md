# Types and Values {#section.type}
================

<div class=issue>


* An integer value
* A floating-point value
* A string value
* A code point value
* A Boolean value

A composite value is one of:

* A tuple value
* An array-like value
* A structure value
* An `enum` value

</div>


A <dfn>type</dfn> is a set of <dfn>values</dfn>;
the values in that set are <dfn>instances</dfn> of the type.

Note: A given [=value=] might be an [=instance=] of zero or more [=types=]. We avoid saying that a value *has* some type, except in cases where there is an "obviously right" type for such a value.

```.semantics
Value :=
  ImplicitlyTypedValue
  | UntypedValue

TypedValue :=
  ImplicitlyTypedValue
  | ExplicitlyTypedValue

ExplicitlyTypedValue := UntypedValue `:` Type

ImplicitlyTypedValue := /* TODO */

UntypedValue := /* TODO */
```

## Level {#value.level}

Every [=value=] has a positive integer <dfn export>level</dfn>.

Note: Typical values that a Slang program calculates and works with have [=level=] zero.

## Types of Types {#type.type}

A [=type=] is itself a [=value=].

The level of a [=type=] is one greater than the maximum of zero and the maximum level of the instances of that type.

Note: It is impossible for a type to be an instance of itself.

A [=type=] whose instances are all [=values=] with [=level=] zero is a <dfn export>proper type</dfn>.

Note: Most of what a programmer thinks of as types are [=proper types=]. The [=level=] of a [=proper type=] will always be one.

A [=type=] whose instances are [=types=] with [=level=] one is a <dfn export>kind</dfn>.

The [=kind=] `Type` is the [=kind=] of all [=proper types=].

A [=type=] whose instances are [=types=] with [=level=] two is a <dfn export>sort</dfn>.

The [=sort=] `Kind` is the [=sort=] of all [=kinds=].

## Scalars {#type.scalar}

All scalar values have [=level=] zero.

### Unit ### {#type.unit}

The <dfn export>unit type</dfn>, named <a lt="unit type">`Unit`</a>, has a single instance: the <dfn export>unit value</dfn>.
The name `void` is an alias for the unit type.

### Booleans ### {#type.bool}

The type `Bool` has two instances: `true` and `false`.

### Numeric Scalars ### {#type.scalar.numeric}

#### Integers #### {#type.scalar.numeric.int}

The <dfn>integer types</dfn> are:

<table>
<tr><th>Type</th><th>Kind</th></tr>

<tr><td>`Int8`</td>  <td>8-bit signed integer type</td></tr>
<tr><td>`Int16`</td><td>16-bit signed integer type</td></tr>
<tr><td>`Int32`</td><td>32-bit signed integer type</td></tr>
<tr><td><dfn lt="Int64" export>`Int64`</dfn></td><td>64-bit signed integer type</td></tr>

<tr><td>`UInt8`</td>  <td>8-bit unsigned integer type</td></tr>
<tr><td>`UInt16`</td><td>16-bit unsigned integer type</td></tr>
<tr><td>`UInt32`</td><td>32-bit unsigned integer type</td></tr>
<tr><td>`UInt64`</td><td>64-bit unsigned integer type</td></tr>

</table>

An [=integer type=] is either signed or unsigned.
An integer type has a bit width.

Signed integer types use two's complement representation.
Arithmetic operations on values of integer type (both signed and unsigned) wrap on overflow/underflow.

The name `Int` is an alias for the type `Int32`.
The name `UInt` is an alias for the type `UInt32`.

#### Floating-Point Numbers #### {#type.scalar.numeric.float}

The <dfn>floating-point types</dfn> are:

<table>
<tr><th>Type</th><th>Kind</th><th>IEEE 754 Format</tr>

<tr><td>`Float16`</td><td>16-bit floating-point type</td><td>`binary16`</td></tr>
<tr><td>`Float32`</td><td>32-bit floating-point type</td><td>`binary16`</td></tr>
<tr><td>`Float64`</td><td>64-bit floating-point type</td><td>`binary16`</td></tr>
</table>

All [=floating-point types=] are signed.
A floating-point type has a bit width.

A [=floating-point type=] has a corresponding IEEE 754 format.
The instances of a floating-point type are all the values of its IEEE 754 format.

The name `Float` is an alias for the `Float32` type.

### Text ### {#type.text}

#### Unicode Scalar Values #### {#type.text.unicode-scalar-value}

Issue: Need to write this section.

#### Characters #### {#type.text.char}

Issue: Need to write this section.

#### Strings #### {#type.text.string}

Issue: Need to write this section.

## Finite Sequences {#type.sequence.finite}

The <dfn>element count</dfn> of a finite sequence is the number of elements in it.

The <dfn>element type</dfn> of a homogeneous sequence is the type of elements in it.

The [=level=] of a sequence is the level of its [=element type=].

```.semantics
Sequence := `{` (Value `,`)* `}`
```

## Array Types {#type.array}

```.semantics
ArrayType := elementType:Type `[` elementCount:Int `]`
```

An <dfn>array</dfn> is a finite homogenous sequence.
An <dfn>array type</dfn> |T|`[`|N|`]` is the type of |N|-element [=arrays=] with elements of type |T|.

The [=element count=] of an [=array type=] must be a non-negative `Int`.


## Vectors {#type.vector}

```.semantics
VectorType := `Vector` `<` elementType:Type `,` elementCount:Int `>`
```

A <dfn>vector</dfn> is a finite homogenous sequence.
The [=element type=] of a vector must be a scalar numeric type.

A <dfn>vector type</dfn> `Vector<`|T|`,`|N|`>` is the type of [=vectors=] with |N| elements of type |T|.

The [=element count=] of a [=vector type=] must be a non-negative `Int`.

## Matrices {#type.matrix}

A <dfn>matrix</dfn> is a finite homogenous sequence.
The [=element type=] of a [=matrix=] must be a [=vector type=].

The <dfn>rows</dfn> of a matrix are its elements.
The <dfn>row type</dfn> of a matrix is its [=element type=].
The <dfn export>row count</dfn> of a matrix is its [=element count=].

The <dfn>scalar type</dfn> of a matrix is the [=element type=] of its [=element type=].

The <dfn>column count</dfn> of a matrix is the [=element count=] of its [=row type=].
The <dfn export>column type</dfn> of a matrix with [=scalar type=] |T| and [=column count=] |C| is `Vec<`T`,`|C|`>`

A <dfn export>matrix type</dfn> `Matrix<`|T|`,`|R|`,`|C|`>` is the type of matrices with |R| [=rows=] of type `Vector<`|C|`,`|T|`>`.

## The `Never` Type {#type.never}

```.semantics
NeverType := `Never`
```

The type `Never` has no instances.

## Declaration References {#decl.ref}

A <dfn export>declaration reference</dfn> is a [=value=] that refers to some [=declaration=].

```.semantics
DeclarationReference :=
  DirectDeclarationReference
  | MemberDeclarationReference
  | SpecializedDeclarationReference
```

### Direct Declaration References ### {#decl.ref.direct}

A [=declaration=] serves as a <dfn export>direct declaration reference</dfn> to itself.

```.semantics
DirectDeclarationReference := Declaration
```

### Member Declaration Reference ### {#decl.ref.member}

```.semantics
MemberDeclarationReference := base:DeclarationReference `::` member:Declaration
```

A <dfn export>member declaration reference</dfn> refers to some *member* [=declaration=] of a base [=declaration reference=].
A [=member declaration reference=] must satisfy the following constraints:

* The *base* must refer to a declaration with members (TODO: make this precise)
* The *member* must be a direct member declaration of the *base*

### Specialized Declaration Reference ### {#decl.ref.specialize}

```.semantics
SpecializedDeclarationReference := base:Value `<` (arguments:Value `,`)* `>`
```

A <dfn export>specialized declaration reference</dfn> refers to a specialization of some generic declaration.
A [=specialized declaration reference=] must satisfy the following constraints:

* The *base* must refer to a generic declaration
* The *base* must not be a [=specialized declaration reference=]
* The number of *arguments* must match the number of parameters of *base*
* Each of the *arguments* must be an instance of the type of the corresponding parameter of *base*

### Fully-Specialized Declaration References ### {#decl.ref.specialized.fully}

A [=declaration reference=] |r| is <dfn export>unspecialized</dfn> if |r| refers to a generic declaration and |r| is not a [=specialized declaration reference=].

A [=declaration reference=] |r| is <dfn export>fully specialized</dfn> if all of:

* |r| is [=unspecialized=]
* if |r| has a base [=declaration reference=], then its base is [=fully specialized=]

<div class="issue">
We need to do some work to define what a fully-qualified declaration reference is, since some parts of the semantics want it.

A direct declaration reference is fully qualified if it is to a module, a parameter (generic or value), or a local declaration.

A member declaration reference is fully qualified if its base is.
A specialization is fully qualified if its base is.
</div>

## Nominal Types {#type.nominal}

A <dfn export>nominal type</dfn> is a fully-specialized declaration reference to a [=type declaration=].

`struct` Types {#type.struct}
---------------

A <dfn export>struct type</dfn> is a fully-specialized declaration reference to a `struct` declaration.

A [=struct type=] is a [=proper type=].

`class` Types {#type.class}
-------------

A <dfn export>class type</dfn> is a fully-specialized declaration reference to a `class` declaration.

An instance of a [=class type=] is an <dfn export>object</dfn>.

A [=class type=] is a [=proper type=].

`enum` Types {#type.enum}
------------

An <dfn export>enum type</dfn> is a fully-specialized declaration reference to an `enum` declaration.

An [=enum type=] is a [=proper type=].

Type Aliases {#type.alias}
------------

A <dfn export>type alias</dfn> is a fully-specialized declaration reference to an `typealias` declaration.

A [=type alias=] is a [=proper type=].

Associated Types {#type.assoc}
----------------

An <dfn export>associated type</dfn> is a fully-specialized declaration reference to an `associatedtype` declaration.

An [=associated type=] is a [=proper type=].

Interfaces {#type.interface}
----------

An <dfn export>interface</dfn> is a value that is either:

* a fully-specialized declaration reference to an `interface` declaration

* a conjunction of interfaces

The [=instances=] of an interface are the [=proper types=] that conform to it.

An [=interface=] has level two.

The [=sort=] `Interface` is the [=sort=] of all [=interfaces=].

`any` Types {#type.any}
-----------

```.semantics
ExistentialAnyType := `any` Interface
```

An <dfn export>any type</dfn> takes the form `any` |I|, where |I| is an [=interface=].

The [=level=] of an [=any type=] is one.

An instance of `any` |I| is an <dfn export>existential value</dfn>.

* a [=type=] |T|

* a witness that |T| conforms to |I|

* a [=value=] of type |T|

The [=level=] of an existential value is zero.

Functions {#type.function}
---------

A <dfn export>function</dfn> is a value that can be called.

A function is called with zero or more values as <dfn export>arguments</dfn>.
The [=arguments=] to a function call must match the function's <dfn export>parameters</dfn>

If a call to a function returns normally, it returns a value of the function's <dfn export>result type</dfn>.

A call to a function may have additional <dfn export>effects</dfn>.

A <dfn export>function type</dfn> takes the form:

```.semantics
FunctionType := `(` (Parameter `,`)* `)` Effect* `->` resultType:Type

Parameter := (Name `:`)? Type
```

`(` |parameters| `)` |effects| `->` |resultType|

where:

* |parameters| is a comma-separated sequence of zero or more [=parameters=]
* |effects| is zero or more [=effects=]
* |resultType| is a [=type=]

Each of the |parameters| of a function type may either be a [=type=] or of the form *name*`:`*type*.

A fully-specialized declaration reference to a function declaration is a [=function=].

The level of a function is the maximum of the levels of its parameter types and result types.

Generics {#type.generic}
--------

A <dfn export>generic</dfn> is a value that can be specialized.

A generic is specialized with one or more values as [=arguments=].
The [=arguments=] to a specialization must match the generic's [=parameters=].

A <dfn export>dependent function type</dfn> takes the form:

```.semantics
DependentFunctionType := `<` (Parameter `,`)* `>` `->` resultType:Type
```

`<` |parameters| `>` `->` |resultType|

where:

* |parameters| is a comma-separated sequence of zero or more parameters
* |resultType| is a type

The |parameters| of a generic type may either be a type or of the form *name*`:`*type*.

The result type of a generic type may refer to the parameters.

An unspecialized declaration reference to a generic declaration is a [=generic=].

The level of a generic is the maximum of the level of its result type and one greater than the maximul of the levels of its parameter types.

Witnesses {#type.witness}
---------

A <dfn export>proposition</dfn> is a phrase that logically may be either true or false.

[=Propositions=] are [=types=].
A <dfn export>witness</dfn> is an instance of a [=proposition=].
The existance of a [=witness=] of some [=proposition=] |P| demonstrates the truth of |P|.

The notation "a [=witness=] that |P|", where |P| is a proposition, is equivalent to "an [=instance=] of |P|".

The notation |T| `extends` |S| denotes a [=proposition=] that the [=type=] |T| is a subtype of the [=type=] |S|.

The notation |T| `implements` |I| denotes a [=proposition=] that the [=type=] |T| conforms to the [=interface=] |I|.

```.semantics
Proposition := /* TODO */

SubtypeProposition := subtype:Type `extends` supertype:Type

ImplementationProposition := Type `implements` Interface
```

<div class="issue">
A witness that *t* `implements` *i* is a witness table.

Given:
* an interface *i*
* a requirement of *i*, represented as a direct member declaration of *r*
* a type *t*
* a witness table *w*, of type *t* `implements` *i*

then looking up the witness value for *r* should basically amount to a (static) member reference into *w*.

This would all be easier if Slang followed the approach of something like Haskell, where the `This` parameter is basically explicit.

Basically this amounts to saying that *t* `implements` *i* acts as a declaration reference to *i*, and that a declaration reference to an `interface` is not "fully specialized" (in the sense that members can be looked up) without that added parameter.

(*t* `implements` *i*)::*r*

So... I need to do that.
</div>


Module Values {#value.module}
-------------

A [=module=] is a [=value=].
