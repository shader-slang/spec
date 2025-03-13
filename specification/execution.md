Execution [exec]
=========

> Note:
>
> This chapter concerns itself with the context in which Slang code is executed at runtime.
>
> The details of the dynamic semantics of particular statement or expression forms is left to the sections that document those pieces of syntax.

Runtime Sessions [exec.runtime]
================

A **runtime session** is a context for loading and execution of Slang code.

A *runtime session* exists within the context of a **process** running on some **host** machine.

> Note:
> 
> For some implementations, a *runtime session* may be the same as a *process*, but this is not required.

A *runtime session* has access to one or more distinct **devices** on which work may be performed.
Different *devices* in a *runtime session* may implement different **architectures**, each having its own machine code format(s).
For some implementations, the *host* may also be a *device*, but this is not required.

The state of a *runtime session* consists of:

* The contents of *memory*, accross all *address spaces* and *devices*

* The running *strands*, *dispatches*, and *commands* on each *device*, and the state of each

* The state of systems and resources external to the *runtime session*, but accessible to it through calls to services of the *host* machine.

Strands [exec.strand]
=======

A **strand** is a logical runtime entity that executes Slang code.
The state of a strand consists of a stack of *invocation records*, representing *invocations* that the strand has entered but not yet exited.

A strand may be realized in different ways by different devices, runtime systems, and compilation strategies.

Note: The term "strand" was chosen because a term like "thread" is both overloaded and charged.
On a typical CPU *architecture*, a strand might map to a thread, or it might map to a single SIMD lane, depending on how code is compiled.
On a typical GPU *architecture*, a strand might map to a thread, or it might map to a wave, thread block, or other granularity.

Note: An implementation is allowed to "migrate" a strand from one thread to another.

A strand is **launched** for some *invocable* declaration _D_, with an initial stack comprising a single *invocation record* for _D_.

Completion Status [exec.completion]
=================

A **completion status** represents the result of *execution* or *evaluation* and can be either a **normal** completion status, or an **abnormal** completion status:

```.semantics

CompletionStatus
  => NormalCompletionStatus
  => AbnormalCompletionStatus

NormalCompletionStatus
  => `NORMAL(` Value `)`

AbnormalCompletionStatus
  => `RETURN(` Value `)`
  => `CONTINUE`
  => `BREAK`
  => `DISCARD`
```

TODO: Cover all possible completion statuses

Execution of Statements [exec.stmt]
=======================

**Execution** is the process by which a *strand* performs the computations indicated by a compiled Slang *statement*.
*Execution* is always performed in the context of some *strand*.
The state of that *strand*, as well as the *runtime session* the *strand* belongs to, can affect the results of *excutiion*.

*Execution* of a statement either completes with some *completion status*, or fails to terminate.

*Execution* of a *statement* does not yield any *value*, but may change the state of a *runtime session* by performing *side effects*, including *memory operations*.

Issue: The notion of a *side effect* needs to be specified properly somewhere.

Note: *Execution* of a *statement* will often entail *execution* of sub-*statements* and *evaluation* of sub-*expressions*.

Evaluation of Expressions [exec.eval]
=========================

**Evaluation** is the process by which a *strand* attempts to calculate a *value* for a compiled Slang *expression*.
*Execution* is always performed in the context of some *strand*.
The state of that *strand*, as well as the *runtime session* the *strand* belongs to, can affect the results of *excutiion*.

*Evaluation* of an expression either completes with some *completion status*, or fails to terminate.

An expression **evaluates to** a *value* _v_, if *evaluation* of that *expression* completes with a *completion status* of _NORMAL(v)_.

*Evaluating* an *expression* may also have some number of *side effects*.

Note: *Evaluation* of an *expression* will often entail *evaluation* of its sub-*expressions*.

Invocation [exec.invocation]
==========

An **invocation** occurs when a *strand* *evaluates* a *call* to a *function* or other *invocable* entity, with zero or more *arguments*.

Invocation Records [exec.invocation.record]
------------------

An **invocation record** represents the state of a single *invocation* being *evaluated* by some *strand*.
The state of an *invocation record* for *invocable* declaration _d_ by strand _s_ consists of:

* A *value* for each *parameter* of _d_

* The location _L_ within the *body* of _d_ that _s_'s execution has reached for that *invocation*

* A *value* for each *local variable* of _d_ that is in scope at _L_

Evaluation of Invocations [exec.invocation.eval]
-------------------------

To *evaluate* an *invocation* of an *invocable* entity _f_ with *arguments* _a0, a1, ..._, in the context of *strand* _s_:

* Create an *invocation record* _r_ for _f_

* For each *parameter* _pi_ of _f_:

  * Set the corresponding *value* in _r_ to the corresponding *argument* _ai_

* Push _r_ onto the stack of *invocation records* for _s_

* Let _result_ be the result of *executing* the *body* of _f_

* Pop _r_ from the the stack of *invocation records* for _s_

* Switch on _result_:

  * _RETURN(v)_: *evaluation* completes with _NORMAL(v)_

  * _NORMAL(v)_: *evaluation* completes with _NORMAL(UNIT())_

  * Otherwise: *evaluation* completes with _result_

Waves [exec.wave]
=====

A **wave** is a set of one or more *strands* that execute concurrently.
At each point in its execution, a *strand* belongs to one and only one *wave*.

Waves are guaranteed to make forward progress independent of other waves.
Strands that belong to the same wave are not guaranteed to make independent forward progress.

Note: A runtime system can execute the strands of a wave in "lock-step" fashion, if it chooses.

Strands that are *launched* to execute a *kernel* as part of a *dispatch* will only ever be in the same wave as strands that were launched as part of the same *dispatch*.

Every *wave* has a positive integer **wave size**.
Each strand that belongs to a *wave* with *wave size* _N_ has a distinct integer **lane ID** in [0, _N_).

Note: A wave with *wave size* _N_ can have at most _N_ strands that belong to it, but it can also have fewer.
This might occur because a partially-full wave was launched, or because strands in the wave terminated.
If strands in a wave have terminated, it is possible that there will be gaps in the sequence of used lane IDs.

Two strands that are launched for the same kernel for the same node of the same pipeline configuration as part of the same dispatch will belong to waves with the same wave size.

Note: Wave sizes can differ across target platforms, pipeline stages, and even different optimization choices made by a compiler.

Uniformity [exec.uniformity]
==========

Collective Operations [exec.uniformity.collective]
---------------------

A **collective** operation is one that require multiple strands to coordinate.
A *collective* operation is only guaranteed to execute correctly when the required subset of strands all **participate** in the operation together.

Tangles [exec.uniformity.tangle]
-------

A **tangle** is a collection of *strands* that are conceptually executing together.
Every *strand* belongs to one and only one *tangle* at any point in its execution.
The *tangle* that a *strand* belongs to can change over the course of its execution.
When a *strand* performs a *collective* operation, it *participates* with those strands that are part of the same tangle.

Control-Flow Graphs [exec.cfg]
-------------------

TODO: These definitions need to live somewhere else.

A **control-flow graph** (or *CFG*) consists of:

* a set of *basic blocks*, including

* a unique *entry block*, and

* the *control-flow edges* between those blocks

### Dominance [exec.cfg.dom]

A *basic block* _x_ dominates another *basic block* _y_ in the same *CFG* if every path of *control-flow edges* from the *entry block* of the *CFG* to _y_ passes through _x_.

Note: By these rules, _x_ *dominates* _y_ if _y_ is unreachable, because every oen of the (zero) paths from the *entry block* to _y_ passes through _x_.

Control-Flow Regions [exec.uniformity.region]
--------------------

A **control-flow region** is a pair of *basic blocks* (_entry_, _exit_) in a *control-flow graph* such that _entry_ *dominates* _exit_.

A node _n_ in a *control-flow graph* is **inside** the region (_entry_, _exit_) if:

* _entry_ dominates _n_, and
* _exit_ does not dominate _n_.

### Breaking Out Of a Region [exec.uniformity.region.break]

A strand **breaks out of** a *control-flow region* (_entry_, _merge_) if it enters the region (by branching to _entry_) and then subsequently exits the region by branching to some node _n_, distinct from _m_, that is not inside the region.

### Structured Regions [exec.uniformity.region.structured]

A **structured region** is a *control-flow region* that is significant to the Slang language semantics.

For each function body, there is a *structured region* (_entry_, _unreachable_) where _entry_ is the unique entry block of the function's control-flow graph, and _unreachable_ is a unique unreachable block.

Each conditional control-flow operation has a **merge point**,
and defines a structured region (_c_, _m_) where _c_ is the control-flow operation and _m_ is its *merge point*.

TODO: We need rules to define the CFG that arises for each of our syntactic forms (both statements and expressions).

Divergence [exec.uniformity.divergence]
----------

When a *strand* _s_ that is part of a tangle _t_ *executes* a *conditional control-flow operation* and branches to a destination *block* _d_, then _s_ becomes part of a new *tangle* comprising exactly the subset of *strands* of _t_ that branch to _d_.

Reconvergence [exec.uniformity.reconvergence]
-------------

When a *strand* _s_ that is part of a tangle _t_ enters a *structured control-flow region* (_entry_, _merge_) and then exits that region by branching to _merge_, it becomes part of a new *tangle* comprising exactly the subset of *strands* of _t_ that entered that region and did not *break out of* that region.

Note: These rules carefully say that a strand re-converges with the strands in the same tangle that don't break out of the region, rather than the strands that exit the region normally. The reason for this choice is that a strand that goes into an infinite loop without exiting a region will be treated the same as a strand that exits that region normally.

Dynamic Uniformity [exec.uniformity.dynamic]
------------------

A **granularity** of group of *strands* is one of:

* _Strand_: a single *strand*
* _Wave_: *strands* in the same *wave*
* _Block_: *strands* in the same compute *block*
* _Dispatch_: *strands* in the same GPU *dispatch*
* _Constant_: all *strands*

### Dynamically Uniform Values [exec.uniformity.dynamic.value]

When a *strand* _s_ in a *tangle* _t_ *evaluates* some *expression* _e_, the result is **dynamically per-_g_**, for some *granularity* _g_, if _e_ evaluates to the same *value* for every *strand* in _t_ that is in the same _g_ as _s_.

### Dynamically Uniform Control Flow [exec.uniformity.dynamic.control]

When a *strand* _s_ in a *tangle* _t_ *executes* some *statement*, then control-flow for _s_ is **dynamically per-_g_ uniform**, for some *granularity* _g_,  if every *strand* in the same _g_ as _s_ is also in _t_.

Rates [exec.rate]
=====

A **rate** takes the form _@g_ where _g_ is a *granularity*.
A *rate* of _@g_ may also be referred to as per-_g_.

TODO: Writing the rules for computing static rates will be an important exercise...

Rates of Values [exec.rate.value]
---------------

An *expression* is **statically per-_g_** if it can be proved, using the rules in this specification, that the value will always be **dynamically per-_g_** at runtime.

Rates of Control-Flow [exec.rate.control]
---------------------

At some point in a Slang program, control-flow is **statically per-_g_ uniform** if it can be proved, using the rules in this specification, that at runtime any *strand* at that point would be part of a *tangle* that is **dynamically per-_g_ uniform**.
