SP #000: Optional constraints
=================

Extending [SP #001], we should allow optional `where` statements that can be statically checked for sections in a function body. This allows users to succinctly express optional behaviour depending on whether an interface is implemented or not.

Status
------

Status: Design Review

Implementation: [PR 7422](https://github.com/shader-slang/slang/pull/7422)

Author: Julius Ikkala

Reviewer: 

Background
----------

Currently, if one wants to have different behaviour depending on if a generic type parameter implements an interface or not, one must write duplicates of the same function or structure to do so:

```slang
void release<T>(T t)
{
    // Behaviour in general
}

void release<T>(T t)
    where T : IThing
{
    // Behaviour if IThing is implemented.
}
```

These functions are likely to have highly similar implementations, except for short portions where either the interface or a fallback approach is used. This problem grows much larger if more than one parameter has an optional constraint; 2^N implementations are needed for N type parameters.

An example situation where this can occur, is with an interface for cleaning up resources:

```slang
interface IDroppable
{
    [mutating]
    void drop();
}
```

Now, if one wants to write a generic data structure (e.g. `HashMap<K, V>`) which would call `drop()` when erasing entries, multiple implementations are needed. For the `HashMap<K, V>` case, four are needed to cover all combinations of `K: IDroppable` and `V: IDroppable`. This leads to large amounts of duplicated code.

Related Work
------------

C++ works around similar issues with the SFINAE mechanism and/or `if constexpr`; however, this kind of approach is not viable in Slang, as generics are checked for validity before specialization.

While Rust does not support a directly similar feature, there are ways to achieve similar behaviour. A similar approach to Slang's current state is available, you can duplicate functions with different trait bounds. Another approach is to implement the trait for every type with an empty default:

```rust
trait MyTrait {
    fn do_thing() { /* no-op */ }
}
impl<T> MyTrait for T {}
```

Then, `MyTrait` can be unconditionally required and the optional functionality just depends on whether there is a more specific implementation of the trait or not.

Proposed Approach
-----------------

A new `where optionally` syntax is introduced:

```slang
void release<T>(T t)
    where optionally T : IThing
{
    t.doThing(); // ERROR, it's possible that T doesn't implement IThing
    if (T is IThing)
    {
        t.doThing(); // LEGAL, it's known here.
    }
}
```

The optional interface can only be used inside blocks that explicitly check for it with `if (T is IInterface)`. Initially, this checking does not accept `if` predicates with more logic than that, even if they would also ensure the interface's presence: `if (T is IInterface && someCondition)` won't allow you to use `IInterface`. This can later be relaxed if deemed useful.

Multiple different type parameter can have optional constraints that can be separately checked; this avoids the 2^N problem mentioned before.

Detailed Explanation
--------------------

An `OptionalConstraintModifier` is added as a modifier to mark constraints as optional.

A new `NoneWitness` is introduced. It can be used to satisfy any optional constraint when the underlying constraint is not fulfilled. `NoneWitness` lowers to a witness table with a known unique sequential ID. We can then compare any witness table's sequential ID to `NoneWitness`'s ID to check if the witness table actually implements the optional constraint.

When filtering lookup results, we filter out results whose breadcrumb trail contains witnesses related to unchecked optional constraints. An optional constraint is considered as "checked" when it's used inside an `IfStmt` whose predicate is exactly `sub is sup`, where `sub = subtypeWitness->getSub()` and `sup = subtypeWitness->getSup()`.

All calls to functions through `NoneWitness` or its corresponding lowered witness table can simply be omitted; assuming no bugs in checking, such uses can only occur in unreachable code.

Alternatives Considered
-----------------------

An alternative would be to approach the problem as in Rust, where the user would simply implement the trait for every type with an empty default implementation, that would then be specialized as needed. In Slang, this would be expressed as:

```slang
public extension<T> T: IDroppable
{
    [mutating]
    void drop() {}
}
```

In current Slang, this issues an error "type 'T' cannot be extended. `extension` can only be used to extend a nominal type." The author is not aware of how much work it would be to allow this kind of usage or whether it would clash with existing Slang functionality.

One drawback of the Rust-style approach is that the language server will then offer `drop()` for every single type if the extension is visible. It is also a more indirect way of expressing optional behaviour, but does not need new syntax to be implemented.

This proposal intentionally left out `as`. While `val as IThing` could conceivably be supported, it would only be useful for language consistency; there is nothing that the `val as IThing` syntax allows that cannot be done with an `if (T is IThing)` block. Furthermore, the `if-is` syntax also allows calling mutating functions of `inout` parameters, which `as` does not.
