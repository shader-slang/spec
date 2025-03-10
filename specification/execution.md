Execution [exec]
=========

A **runtime session** is a context for loading and execution of Slang code.
A *runtime session* exists within the context of a **process** running on some **host** machine.
For some implementations, a *runtime session* may be the same as a *process*, but this is not required.

A *runtime session* has access to one or more distinct **devices** on which work may be performed.
Different *devices* in a *runtime session* may implement different **architectures**, each having its own machine code format(s).
For some implementations, the *host* may also be a *device*, but this is not required.

Issue: We need to define what it means to "execute" statements and to "evaluate" expressions...

When a strand invokes an invocable entity _f_, it executes the body of _f_ (a statement).
As part of executing a statement, a strand may execute other statements, and evaluate expressions.
A strand evaluates an expression to yield a value, and also for any side effects that may occur.

Strands [exec.strand]
-------

A **strand** is a logical runtime entity that executes Slang code.
The state of a strand consists of a stack of *activation records*, representing invocations that the strand has entered but not yet exited.

A strand may be realized in different ways by different devices, runtime systems, and compilation strategies.

Note: The term "strand" was chosen because a term like "thread" is both overloaded and charged.
On a typical CPU *architecture*, a strand might map to a thread, or it might map to a single SIMD lane, depending on how code is compiled.
On a typical GPU *architecture*, a strand might map to a thread, or it might map to a wave, thread block, or other granularity.

Note: An implementation is allowed to "migrate" a strand from one thread to another.

A strand is **launched** for some *invocable* declaration _D_, with an initial stack comprising a single activation record for _D_.

Activation Records [exec.activation]
------------------

An **activation record** represents the state of a single invocation of some *invocable* declaration by some strand.
An *activation record* for *invocable* declaration _D_ by strand _S_ consists of:

* A value for each parameter of _D_

* The location _L_ within the *body* of _D_ that _S_'s execution has reached for that invocation

* A value for each local variable of _D_ that is in scope at _L_

Waves [exec.wave]
-----

A **wave** is a set of one or more *strands* that execute concurrently.
At each point in its execution, a *strand* belongs to one and only one *wave*.

Waves are guaranteed to make forward progress independent of other waves.
Strands that belong to the same wave are not guaranteed to make independent forward progress.

Note: A runtime system can execute the strands of a wave in "lock-step" fashion, if it chooses.

Strands that are *launched* to execute a *kernel* as part of a *dispatch* will only ever be in the same wave as strands that were launched as part of the same *dispatch*.

Every *wave* _W_ has an integer **wave size** _N_ > 0.
Every strand that belongs to _W_ has an integer **lane ID** _i_, with 0 <= _i_ < _N_.
Distinct strands in _W_ have distinct *lane IDs*.

Note: A wave with *wave size* _N_ can have at most _N_ strands that belong to it, but it can also have fewer.
This might occur because a partially-full wave was launched, or because strands in the wave terminated.
If strands in a wave have terminated, it is possible that there will be gaps in the sequence of used lane IDs.

Two strands that are launched for the same kernel for the same node of the same pipeline configuration as part of the same dispatch will belong to waves with the same wave size.

Note: Wave sizes can differ across target platforms, pipeline stages, and even different optimization choices made by a compiler.

Uniformity [exec.uniformity]
----------

A **collective** operation is one that require multiple strands to coordinate.
A *collective* operation is only guaranteed to execute correctly when the required subset of strands all **participate** in the operation together.

### Tangle [exec.uniformity.tangle]

Any strand begins execution of an entry point as part of a **tangle** of strands.
The *tangle* that a strand belongs to can change over the course of its execution.
When a strand executes a collective operation, it *participates* with those strands that are part of the same tangle.

When a strand executes a conditional control-flow operation, it branches to a destination that can depend on a condition value.
When the strands of a tangle execute a conditional control-flow operation, each strand in the tangle becomes part of a new tangle with exactly those strands that branch to the same destination.

A **control-flow region** is a pair of nodes (_E_, _M_) in the control-flow graph of a function, such that either:

* _E_ dominates _M_
* _M_ is unreachable

A node _N_ in the control-flow graph of a function is inside the region (_E_, _M_) if _E_ dominates _N_ and _M_ does not dominate _N_.

A **structured region** is a *control-flow region* that is significant to the Slang language semantics.

For each function body, there is a *structured region* (_Entry_, _Exit_) where _Entry_ is the unique entry block of the function's control-flow graph, and _Exit_ is a unique block dominated by all points where control flow can exit the function body.

Each conditional control-flow operation has a **merge point**,
and defines a structured region (_C_, _M_) where _C_ is the control-flow operation and _M_ is its *merge point*.

A strand **breaks out of** a control-flow region (_E_, _M_) if it enters the region (by branching to _E_) and then subsequently exits the region by branching to some node _N_, distinct from _M_, that is not inside the region.

Note: We define the case where a strand *breaks out of* a region, but not the case where a strand exits a region normally.
The motivation for this choice is that a strand that goes into an infinite loop without exiting a region needs to be treated the same as a strand that exits that region normally.

When the strands in a tangle enter a structured control-flow region (_E_, _M_), all of the strands in the tangle that do not break out of that region form a new region at _M_.

### Dynamic Uniformity [exec.uniformity.dynamic]

Uniformity must be defined relative to some granularity of grouping for strands: e.g., per-strand, per-wave, per-block, etc.

When the strands in a tangle evaluate some expression, we say that the result is dynamically per-_G_ for some granularity of group _G_, if for any two strands in the tangle that are in the same _G_, those strands compute the same value for that expression.

We say that a tangle is executing code dynamically per-_G_ uniform when for every _G_, either all of the strands in that _G_ are in the tangle, or all of them are not in that tangle.

### Static Uniformity [exec.uniformity.static]

A value in a Slang program (such as the result of evaluating an expression) is statically per-_G_, for some granularity of group _G_, if it can be proved, using the rules in this specification, that the value will always be dynamically per-_G_ at runtime.

We say that control-flow is statically per-_G_ uniform at some point in a program if it can be proved, using the rules in this specification, that at runtime any stand at that point would be part of a tangle that is per-_G_ uniform.

TODO: Okay, now we actually need to write just such rules...
