Type Conversions {#conv}
================

<div class=issue>
Broadly this chapter needs to do two things:


* Define the semantic rules for implicit type coercion and explicit type conversion.
* Specify the implicit coercions that are defined for the basic Slang types, and their costs.


The latter part (the builtin implicit coercions and their costs) can be a simple table, once the rules are properly defined.

From a big-picture perspective, the implicit type coercion rules when coercing something of type `From` to type `To` are something like:


* If `From` and `To` are identical types, then coercion succeeds, with no cost.
* If `From` is a subtype of `To`, then coercion succeeds, with a cost that relates to how "far" apart the types are in an inheritance hierarchy.
* If neither of the above applies, look up `init` declarations on type `To`, filtered to those that are marked as suitable for implicit coercion, and then perfom overload resolution to pick the best overload. The cost is the cost that was marked on the chosen `init` declaration.


The overload resolution rules rely on checking implicit type coercions, and the implicit type coercion rules can end up checking an overloaded `init` call.
The specification must explain how to avoid the apparant possibility of infinite recursion.
The simplest way to avoid such problems is to specif that the overload resolution for the `init` call above uses a modified form where only subtyping, and not implicit coercion, is allowed for arguments.

Explicit type conversion follows the same overall flow as the implicit case, except it does not filter the candidates down to only those marked as usable for implicit coercion.
</div>