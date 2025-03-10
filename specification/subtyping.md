Subtyping {#subtype}
=========

<div class=issue>

This chapter needs to define what the subtyping rules are, as something distinct from the conversion/coercion rules (which need their own chapter).

At the most basic, we want to have a guarantee that if `T` is a subtype of `S`, then it is safe and meaningful to read an `S` from a memory location that holds a `T`.
Beyond that, we need to decide whether it a subtype (in the formal semantics) must have the same size and stride as the supertype, or it if is allowed to be larger.

The key reason to have the subtyping rules kept distinct from the conversion/coercion rules is that many built-in types (as well as the conceptual/intermediate types that are needed for semantic checking) are covariant type constructors, where the covariance must be defined in terms of true subtyping and not just convertability. E.g., a `borrow` T} can be converted to a `borrow` S} only if `T` is truly a subtype of `S`, and not just convertible to it.

Note that the ``is-a-subtype-of'' relationship between two types is distinct from the ``conforms-to'' relationship between a proper type and an interface type.
The ``conforms-to'' relationship might need to be documented in this chapter as well, just because it shares a lot of structurally similar machinery.

(In fact, it may be best to have a judgement that is parameterized over the type relationship that is being checked: conformance, subtyping, implicit coercion, explicit conversion.)

</div>
