SP #027 - Tuple Syntax

This proposal repurposes the existing comma operator syntax, and changes the meaning of
`(a, b, ...)` to represent construction of tuples.

Status
------

Author: Yong He

Status: In Experiment.

Implementation: [PR 7230](https://github.com/shader-slang/slang/pull/7230).

Reviewed by: 


Background
-----------

[SP008](008-tuples.md) adds tuple types to the language. Unlike many other modern languages,
Slang still lacks a convenient syntax for constructing tuples. The current way to construct
a new tuple is to call the builtin `makeTuple()` function.

In most languages that support tuples, such as Python, Swift and Rust, tuples are constructed
with a paranthesis, for example: `(1, false, 2.0f)` results in a `Tuple<int, bool, float>`.

Many Slang users comming from these languages would expect the same syntax for constructing
tuples. These users are often surprised by Slang's current syntax of comma operator.
Specifically, `float3 v = (1.0, 2.0, 3.0);` doesn't result in an error, but instead constructs
`v` as a `float3(3.0, 3.0, 3.0)` since the comma expression inside the parenthesis evaluates
to the value of the last sub-expression, as in C/C++.

Proposed Solution
---------

We propose to remove the support for comma operator inside a paranthesis in Slang language
version 2026 due to very limited use of the comma operator. Starting from Slang 2026,
`(a,b,c)` should now mean construction of a tuple, bringing Slang's syntax to be consistent with
other modern languages.

A special case is the meaning of paranthesis with only one element. The meaning of `(expr)` should
be unchanged -- no tuple will be constructed if there is no comma in the paranthesis.

`(a,)` means construction of a 1-element tuple, similar to that in Python.

Additionally, `()` means construction of an empty tuple.

Impact to Existing Codebase
---------

Comma operator is usually used inside a for loop's init and side effect expressions, such as

```
for (i = 0, j = 0; pred; i++, j++) { }
```

Note that change in this proposal only affects the meaning of the comma operator inside a paranthesis.
In this example, since neither the init nor the side-effect expression is wrapped inside a paranthesis,
they will continue to be parsed as a comma expression.

Even when the user wraps these expression in a paranthesis, the semantics of the for loop
should still remain the same:

```
for ((i = 0, j = 0); pred; (i++, j++)) { }
```

This for loop should continue to work, since the only purpose of these expressions is to introduce
side-effect. The change from comma operator to tuple construction only affects the "return" value
of the expression and will not affect the side-effect.

Apart from their use in `for` loops, use of comma operator in other contexts is uncommon. We expect
this change to have very minimum impact to exising codebases. The benefit of the added convenience
for tuples out-weights the potential downsides.

Future Work -- Type Syntax
---------

This proposal only adds the `()` syntax to construct tuple values but not types. Supporting `()` for
defining tuple types may introduce nuances and syntax ambiguities that require more careful design.
For this reason, we leave the type syntax as a future work.