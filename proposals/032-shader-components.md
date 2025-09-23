SP #032: Shader Components
=================

We propose to add a construct for authoring "components" in Slang.
These components provide a unit of shader modularity and composition that sits between `struct` types and modules in granularity.
The granularity and behavior of components is designed to solve certain problems that neither `struct`s nor modules have proven able to model.

This is a "mega-feature" and, if the proposal is received favorably, would likely need to be broken down into several smaller steps that can be implemented, tested, and deployed one-by-one.

Status
------

Status: Design Review

Implementation: -

Author: Theresa Foley (`tfoley@nvdia.com`)

Reviewer: -

Background
----------

This feature is primarily concerned with *separation of concerns*, although we may specifically refer to "modularity" and/or "composability" along the way.

### File-Oriented Separation of Concerns

Historically, developers have often used what we might call *file-oriented* separation of concerns in shader codebases.
In a language like HLSL, a `.h` file can be used to express a unit of code code that supports the following:

* The unit can express that it *depends on* other units, by `#include`-ing their `.h` files

* The unit can have zero or more declarations of what we will call "ordinary code": that is, `struct` types, functions, and other declarations that *do not* depend on any global- or `namespace`-scope shader parameters in their definition/implementation

* The unit can introduce (whether explicitly or implicitly) zero or more specialization parameters, such a `#define`s, that can or must be specified at compile time

* The unit can declare zero or more global- or `namespace`-scope shader parameters, such as `cbuffer` declarations, `Texture2D`s, etc.

* The unit can define zero or more functions that may depend on global- or `namespace`-scope shader parameters. These functions can include entry points.

An simplistic example of a feature/unit defined in this style might be:

```hlsl
// MyFeature.hlsl.h
#pragma once

// dependencies:
#include "YourFeature.hlsl.h"
#include "AnotherFeature.hlsl.h"

// ordinary code:
struct Stuff { /* ... */ };
float getValue(Stuff stuff) { /* ... */ }

// shader parameters
ConstantBuffer<Stuff> gStuff;
Texture2D gMyTexture;

// functions that use shader parameters:
Stuff getStuff() { return gStuff; }
```

The file-oriented approach has some important benefits, that developers might not even think about, because the pattern is so ubiquitous:

* Code in the body of a function can freely refer to the shader parameters and other functions in the unit that defines that function, as well as in any other units that it depends on via `#include`. No prefixing is required at use sites. The units that the function makes use of needn't show up in its parameter list, nor at call sites to the function.

* By using constructs like include guards or `#pragma once`, a shader codebase can support a dependency DAG of such file-oriented units.
Each of these file-oriented units will only be textually included once in a given compile.

The file-oriented approach also has some significant drawbacks, some of which are exacerbated by design choices in the Slang language and compiler:

* A developer cannot easily enforce that the code inside a `.h` unit only depends on the dependencies of that unit, as stated via `#include`. Additional code will often be in scope during compilation, so it is possible for maintainers to introduce dependencies that were never intended.

* Similarly, a developer cannot meaningfully enforce the separation between "ordinary" code (that must not depend on global- or `namespace`-scope shader parameter) and the code that is allowed to be parameter-dependent.

* There is no easy way for application-agnostic tooling like Slang to recognize the dependency structure from the `#include`s. While there can be *logical* units of modularity in the programmer's mind, those logical units cannot easily be referred to or manipulated by tools.

* As a consequence of the preceding two items, a tool like the Slang compiler cannot tell which global- or `namespace`-scope shader parameters are potentially relevant to a given entry point.

* Because file-based units of modularity are not modeled in the Slang type system, they cannot be used with some of the most powerful tools that Slang supports, such as generics and `interface`s.

Because the Slang compiler cannot see the dependency structure, and because of our principle that the parameter layout automatically computed by the compiler should not change just because of changes to things like function bodies, the compiler must currently assume that every single global- or `namespace`-scope shader parameter that ended up textually included in a compilation *might* be relevant to an entry point. For some codebases that use file-oriented separation of concerns, this can lead to shaders having hundreds or thousands of unintended parameters in their layouts, leading to performance problems at best, and runtime failures at worst, depending on the application or engine.

### Slang Modules

Slang's module system and `import` construct can be used in a file-oriented decomposition, instead of simply `#include`-ing units consisting of `.h` files.
Using modules allows a developer to better control visibility (e.g., to know that the code in a module only depends on what it `import`s).

Translating the earlier example to use modules, we might have:

```hlsl
// MyFeature.slang

// dependencies:
import YourFeature;
import AnotherFeature;

// ... rest of code unchanged ...
```

Simply using Slang modules, while still declaring shader parameters at global or `namespace` scope, does not resolve the problem of too many shader parameters often being pulled into a compile (via the `import` graph), even if they are not intended to be used by or visible to a given entry point.

In addition, while modules are units that the Slang compiler can see and comprehend, they are not compatible with tools like generics and `interface`s.
For example, it is not possible for a developer to declare that a module conforms to some `interface` and have that be checked.
SImilarly, modules cannot be generic and cannot be used as arguments to generics; instead, Slang has a separate system for "link-time specialization" that overlaps with the capabilities of generics, so that developers need to internalize a model for when to use each approach.

### Type-Based Separation of Concerns

Many Slang features are designed with the intention of supporting a more *type-based* rather than file-oriented model.
In the abstract, one can simply take the parameters and the parameter-dependent code for a feature and transplant it from the global scope into a `struct`.

Applying this logic to the running example, we might get:

```hlsl
// MyFeatureModule.slang

// dependencies:
import YourFeatureModule;
import AnotherFeatureModule;

// ordinary code:
struct Stuff { /* ... */ };
float getValue(Stuff stuff) { /* ... */ }

struct MyFeatureParams
{
    // shader parameters
    ConstantBuffer<Stuff> stuff;
    Texture2D myTexture;

    // functions that use shader parameters:
    Stuff getStuff() { return stuff; }
}
```

Note that here we have added the suffix `Module` to the names of the `.slang` files for modules, and used `Params` as a suffix on the name for the `struct` that represents a given feature.
This naming convention exists primarily to avoid ambiguity in the text of this proposal, and we do not advocate that developers follow this kind of verbose scheme.

When this kind of `struct`-based separation of concerns is used, a module typically does not declare *any* global-scope shader parameters.
Instead, an application will typically declare the parameters that a given entry point needs directly on that entry point, e.g.:

```hlsl
[shader("compute")]
void myComputeShader(
    uniform MyFeatureParams myFeature,
    // ...
    )
{ /* ... */ }
```

Wrapping the shader parameters and the parameter-dependent functions in a `struct` initially seems to solve several problems with the file-oriented approach:

* There is a clear separation between the "ordinary" code and the parameter-dependent code, and attempts to make a function in "ordinary" code, like `getValue()` above, reference a shader parameter like `stuff` (inside `MyFeatureParams`) will result in a compile-time error.

* Because the only uniform shader parameters are those declared directly on an entry point, such as the `myFeature` parameter of `myComputeShader()` above, it is simple for the Slang compiler or other tools to determine a more narrowly-scoped list of the shader parameters that a given entry point might access.

### Problems With Using `struct`s for Separation of Concerns

Type-based separation of concerns using `struct` types can initially look like a panacea for structuring a shader codebase for modularity.
However, the simple examples above have avoided showing the many cases where `struct` types are simply not up to the task.
For example, note that the code shown for the example `MyFeature` module above did not reference the parameters nor the functions of the modules it `import`ed.
Suppose now that the `MyFeature` module needed to access the parameters of the `YourFeature` or `AnotherFeature` modules (or functions that in turn need to access those parameters).

Naively, we might try to solve the problem by modifying the `struct` type for `MyFeature` to have nested fields that use the `struct` types for `YourFeature` and `AnotherFeature`, the two features on which is depends:

```
struct MyFeatureParams
{
    YourFeatureParams yourFeature;
    AnotherFeatureParams anotherFeature;

    // rest of body as before
}
```

This solution allows a method in `MyFeatureParams` to acess members of, e.g., `yourFeature` by using an explicit `yourFeature.` prefix.
The requirement to use a prefix when naming declarations from another feature means that code is more verbose than in the original file-oriented model.

The approach of using nested fields ultimately falls flat once an application needs to deal with dependency graphs that aren't simple tree structures.
Suppose that `YourFeature` itself actually depends on `AnotherFeature`; the resulting declarations if we follow the approach of simply inserting fields looks like:

```
struct YourFeatureParams
{
    AnotherFeatureParams anotherFeature;
    // ...
}
// ...
struct MyFeatureParams 
{
    YourFeatureParams yourFeature;
    AnotherFeatureParams anotherFeature;
    // ...
}
```

Now we have two copies of the parameters for `AnotherFeature` included by-value in `MyFeatureParams`.
If we use an entry point declaration like the one shown earlier:

```hlsl
[shader("compute")]
void myComputeShader(
    uniform MyFeatureParams myFeature,
    // ...
    )
{ /* ... */ }
```

the result is that both `myFeature.anotherFeature` *and* `myFeature.yourFeature.anotherFeature` are distinct ranges of shader parameters corresponding to the same logical feature.
Sometimes such duplication is intentional, but often it isn't what a programmer desires.

Using `struct` fields to encode the transitive dependencies between features does not lead to a satisfying result, and developers who traverse this path often arrive at the solution of using explicit parameters for each and every feature.
After eliminated the nested fields for features, their entry point declarations might look like:

```hlsl
[shader("compute")]
void myComputeShader(
    uniform AnotherFeatureParams anotherFeature,
    uniform YourFeatureParams yourFeature,
    uniform MyFeatureParams myFeature,
    // ...
    )
{ /* ... */ }
```

and functions related to a feature might look like:

```hlsl
```hlsl
// MyFeatureModule.slang

// ...

int calculateSomething(
    MyFeatureParams myFeature,
    YourFeatureParams yourFeature,
    AnotherFeatureParams anotherFeature,
    int x,
    float y)
{
    // ...
}
```

That is, the complete transitive dependency graph of features starts to appear in the signature of every entry point and every function, resulting in a large amount of tedium and frustration for developers.

We set out with the intention of improving on the file-oriented approach to separation of concerns.
While the design we've arrived at addresses the problem of allowing tools like the compiler to easily see the dependencies of a shader entry point, we've paid for that gain by losing most of what made the file-oriented approach such a sweet spot in the design space.

Related Work
------------

### If pointers are pervasive (and treated as if they are free...)

Anybody coming from the CPU programming world might look at what was described above as the failure of `struct` based separation of concerns and wonder why we can't just use pointers.
Pretending for a second that pointers are well supported (and peform well) across all the targets a developer cares about, they could write their per-feature `struct`s like:

```c++
struct YourFeatureParams
{
    AnotherFeatureParams* anotherFeature;
    // ...
}
// ...
struct MyFeatureParams 
{
    YourFeatureParams* yourFeature;
    AnotherFeatureParams* anotherFeature;
    // ...
}
```

and their entry points like:

```hlsl
[shader("compute")]
void myComputeShader(
    uniform MyFeatureParams* myFeature,
    // ...
    )
{ /* ... */ }
```

The reality, however, is that pointers are not well supported across the full range of targets many Slang users care about.
Further, even if/when such support becomes pervasive, it is important to understand that unrestricted use of pointers is not free.

For performance-critical kernels on throughput-oriented devices like GPUs, leaning on a general-purpose memory hierarchy for everything is almost always going to be less efficient than exploiting more specialized paths for communication.
For example, developers on Vulkan and D3D12 may spend a lot of time trying to ensure that the most essential shader parameters get passed as push constants (VK) or root constants (D3D); these mechanisms are semantically not all that different than a `ConstantBuffer<>` resource, but the performance difference makes them worth it.

### Dependency Injection

A secondary concern that arises when a codebase tries to employ a pointer-based solution like that described above is that often a lot of code needs to be written simply to "wire up" all of the pointers from one feature to another.

In dynamic languages (like Python, Ruby, etc.) and somewhat dynamic languages (C#, Java, etc.) many developers make use of *dependency injection* frameworks.
These frameworks often start with the idea that `class` or other type declaration may indicate its dependency on another type (whether a concrete type or an interface) by simply declaraing a field of that type (or constructor parameter, property, etc.).
One or more `class`es (or individual objects) can then be registered with some kind of factory or container.
A factory/container can be prompted to provide an instance of some `class`, at which point it will use reflection APIs provided by the language runtime to find and construct an instance of the appropriate class and, most importantly, to *inject* values into the fields (or parameters, etc.) that represent the dependencies of that `class`.

While dependency injection is almost always a dynamic run-time technique, the underlying ideas that it is based on stem from prior work on component-oriented software.

### Components

Many systems have been proposed and developers for building software out of some notion of *components*.
Motivation for such systems is often to improve modularity and support greater re-use.

The term "component" does not have a single universally agreed-upon definition in the software world.
The characterization here will, somewhat unavoidably, be biased toward what this particular feature proposal is focused on.

For our purposes, software components are defined by a few key properties:

* A component has identity (like an object), and its lifetime is semantically significant (unlike objects in most languages with automatic memory management)

* A component can have zero or more interfaces (whether explicitly-declared or implicitly defined) that it *provides*

* A component can have zero or more interfaces (again, explicit or implicit) that it *requires*

* One or more components can be *composed* by "snapping" them together such that a requirement of one component is wired up to another component that provides the matching interface.

* A component can have its own internal *state*, and can encapsulate that state.

* The state of a component can itself include a composite of other components; the outer component is said to *aggregate* the nested components.

While `class`-based objects are often used to *implement* components, it should be understood that components and objects have different purposes.
The distinction between objects and components is in some ways comparable to that between objects and actors in actor programming models.

In most component systems, the way components are snapped or wired together does not change during their lifetime; this is part of why dependency-injection approaches are applicable to assembling objects that are intended to be used as components.

Note that the term "component" on its own almost always refers to an *instance* (akin to an object), and we must typically refer specifically to a "component type" when we want to refer to a type, class, or other archetype used to instantiate components.

Proposed Approach
-----------------

> Note: The specific keywords introduced in this proposal are not our focus, but we need some concrete syntax to be able to illustrate the feature with examples.
> We encourage reviewers to prioritize giving feedback on the semantics of the feature first, and trust that if the feature is desirable to have then we can take ample time to iterate on the naming choices involved.

### Component Type Declarations

We propose to extend the Slang language to support a new kind of nominal type declaration: a `component` type declaration.

A `component` type declaration has capabilities similar to a `struct` or `class` declaration, and supports things like generic parameters, fields, properties, subscripts, etc.
Here is the running example from the background section changed to use a `component` type declaration to encapsulate a feature:

```hlsl
// MyFeatureModule.slang

// dependencies:
import YourFeatureModule;
import AnotherFeatureModule;

// ordinary code:
struct Stuff { /* ... */ };
float getValue(Stuff stuff) { /* ... */ }

component MyFeature
{
    // shader parameters
    ConstantBuffer<Stuff> stuff;
    Texture2D myTexture;

    // functions that use shader parameters:
    Stuff getStuff() { return stuff; }
}
```

Superficially, this does not appear to be a large change from using a `struct` declaration for type-based modularity.

A `component` type declaration is semantically different from a `struct` in a few key ways:

* A `component` type declaration introduces a reference type (as a `class` does in Slang) rather than  value type (as a `struct` does)

* A `component` type declaration cannot inherit from any other concrete types; it can conform to `interface`s, but no other form of inheritance is allowed

* A `component` type cannot include constructor (`init`) declarations, and there is no way for user code in Slang to create an instance of a component type

* Beyond the examples given in this proposal, a `component` type may only be used as the type of non-`static` local variables declared with `let`, as well as function parameters with the `in` parameter-passing mode (the default). We may be able to relax some of these restrictions, but would prefer to keep things as limited as possible to start with.

* A `component` type declaration can include several new kinds of member declarations, detailed in the following sections; these new kinds of members are not allowed inside of other kinds of type declarations

### Allow Entry Points Inside Components (and Structs)

Many of the logical features or concerns in a shader codebase include entry points. Even if a module primarily exists to expose a data structure for access in a user's own entry points, the module might still need to define compute entry points for operations that build or maintain the data structure.

Because logical features/concerns can include entry points, it is important for any type declaration we intend to use for encapsulating features to support having entry points nested under it.
We propose to extend *all* aggregate type declarations (`struct`s, `class`es, and `component` types) to support having methods be labelled as entry points using `[shader(...)]` attributes.
For example:

```hlsl
struct MyVertexFragmentPipeline
{
    float4x4 mvp;
    Texture2D diffuseTex;
    // ...

    struct AsembledVertex { /* ... */ }
    struct RasterVertex { /* ... */ }
    struct Fragment { /* ... */ }

    [shader("vertex")]
    RasterVertex vertexShader(
        AssembledVertex inVertex,
        out float4 sv_position : SV_Position)
    { /* ... */ }

    [shader("fragment")]
    Fragment fragmentShader(
        RasterVertex inVertex)
    { /* ... */ }
}
```

An entry point declared as a (non-`static`) member of a type will take an implicit `this` parameter of the surrounding type, just as any other method would.
Importantly, the outer `this` parameter will be implicitly treated as if it was declared with `uniform`.
Thus, the example above would be more-or-less equivalent to the following code in current Slang:

```hlsl
struct MyVertexFragmentPipeline
{
    float4x4 mvp;
    Texture2D diffuseTex;
    // ...

    struct AsembledVertex { /* ... */ }
    struct RasterVertex { /* ... */ }
    struct Fragment { /* ... */ }
}

[shader("vertex")]
MyVertexFragmentPipeline.RasterVertex MyVertexFragmentPipeline_vertexShader(
    uniform MyVertexFragmentPipeline _this,
    MyVertexFragmentPipeline.AssembledVertex inVertex,
    out float4 sv_position : SV_Position)
{ /* ... */ }

[shader("fragment")]
MyVertexFragmentPipeline.Fragment MyVertexFragmentPipeline_fragmentShader(
    uniform MyVertexFragmentPipeline _this,
    MyVertexFragmentPipeline.RasterVertex inVertex)
{ /* ... */ }
```

When refactoring code that uses file-oriented separation of concerns and global shader parameter declarations to use types:

* Global shader parameters of a concern become fields in the coresponding type

* Global functions of a concern (including entry points) become methods of the corresponding type

An important property of this translation is that the functions (including entry points) of a type-based concern can still access the shader parameters without any prefix (because of implicit lookup through `this`).
While allowing entry points as type members might seem like a frivolous bit of syntactic sugar, it is actually key to enabling developers to migrate away from shader code architectures that result in widespread pollution of the global namespace.

### Requirement Declarations

In the background section we saw that attempts to encapsulate the concerns/features of a shader codebase using `struct`s often run into resistance once they have to contend with non-trivial dependency relationships between concerns.

We propose that `component` type declarations should support explicit member declarations to declare their requirements.
Here is a small example:

```
component RNG
{
    // parameters ...

    uint rand();
}

component LightEnvSampling
{
    require RNG;

    // ...

    Light pickRandomLight()
    {
        // ...
        let r = rand();
        // ...
    }
}
```

In this example we have two concerns, each implemented as a `component` type declaration.
The `RNG` concern implements random number generation, and has some shader parameters that it uses for this purpose.
The `LightEnvSampling` concern implements stochastic sampling of a lighting environment, and depends on the `RNG` concern's `rand()` function to accomplish this task.

The `require RNG` declaration in the example above explicitly declares that the `FilmSampling` component type depends on the `RNG` component type.
Within the body of methods in `LightEnvSampling`, such as `pickRandomLight()`, all of the (visible) members of the `RNG` component type are in scope and usable.
In the example we see the `pickRandomLight()` method directly calling `rand()` with no prefix.

Using `require` declarations helps address two problems we ran into with other approaches to separation of concerns for shader code:

* Unlike traditional file-oriented approaches, there is an explicit representation of the dependency structure that is visible to the compiler and its type system

* Unlike `struct`-based approaches, the parameters/operations of other concerns can be referenced simply (without any prefixing) by code in concerns that depend on them

In addition, because `component` types are semantically reference types rather than value types, complicated dependency DAGs to not result in duplication.
For example, we can introduce an additional component type that depends on `RNG`:

```
component FilmSampling
{
    require RNG;

    // ...

    float3 pickRandomSamplePos()
    {
        // ...
        let r = rand();
        // ...
    }
}
```

A shader that uses both `LightSampling` and `FilmSampling` doesn't get stuck with the parameters of `RNG` being duplicated into both of those types.
But a reader might be wondering: where *do* the parameters of RNG get placed, for the purposes of things like automatic parameter layout.

#### Additional Features

The above discussion only covered the simplest form of a `require` declaration.
We propose to support a few more forms that increase the flexibility of `require`s.

##### Named Requirements

First, we propose to allow a `require` declaration to include an explicit name that will be used to reference the other component in code.
Changing the `FilmSampling` example above to use an explicitly named requirement, we get code like:

```
component FilmSampling
{
    require rng : RNG;

    // ...

    float3 pickRandomSamplePos()
    {
        // ...
        let r = rng.rand();
        // ...
    }
}
```

Note that inside the body of `pickRandomSamplePos()`, it is no longer possible to implicitly reference the members of `RNG` without a prefix;
instead, the programmer must explicitly reference members through the name (`rng`) that was established by the `require` declaration.

As an additional (small) detail, if a developer wants to declare a requirement and neither bind it to a name *nor* implicitly pull its members into scope, then it can use the name `_` (a single underscore) as a placeholder, e.g.:

```
require _ : RNG;
```

(This detail assumes that we also change the Slang parser to start treating `_` as a true reserved word in the language, which is something we know we will want sooner or later for things like pattern matching)

##### Requiring an Interface Type

We also propose to allow a `require` declaration to name an `interface` type instead of a concrete `component` type.
To revisit our example with random number generation, suppose that instead of a single `RNG` component type, there is an interface for random number generation and a few concrete `component` types that implement it:

```
interface IRNG { uint rand(); }

component MersenneTwister : IRNG
{ /* ... */ }
// ...
```

Rather than `require` one of the concrete implementations, a `component` type like our `FilmSampling` example can instead `require` the interface:

```
component FilmSampling
{
    require IRNG;

    // ...
}
```

Using `require` with an interface type has the same basic semantics as when it is used with a concrete type, with respect to what names are bound or brought into scope (depending on the syntactic form of the `require`).

Allowing a `require` of an `interface` type raises the question of how such a requirement will eventually be wired up to a specific concrete implementation.
The next section will discuss our proposed answer.

### Part Declaration

With `component` type declarations and their `require`ments, a programmer can express simple fine-grained concerns.
Concerns at larger scales, such as entire subsystems, will often need to be composed internally from many smaller-scale units, each providing a part of the functionality of the whole.

We propose to support explicit `part` declarations inside of `component` type declarations, to express the sub-components that are aggregated together, as well as their interconnections.
Here is an example of a hypothetical `Scene` component type that aggregates some of the other component types we have been using for examples:

```
component Scene
{
    part RNG;
    part LightSampling;
    part FilmSampling;
}
```

At its most basic, the declaration above shows that a `Scene` component is composed of three parts: an `RNG` component, a `LightSampling` component, and a `FilmSamplingComponent`.

#### How is this different than just declaring a member variable?

A programmer coming mostly a C++ mindset, or simply a more traditionally object-oriented mindset, might wonder why the declaration of `Scene` above can't just be expressed using ordinary fields, as in:

```
component SceneWithoutParts
{
    RNG rng;
    LightSampling lightSampling;
    FilmSampling filmSampling;
}
```

The key sticking point here is that a `component` type like `RNG` is semantically a *reference* type in Slang, so a field declaration like `RNG rng;` only serves to indicate that `SceneWithoutParts` stores a reference to some RNG but does not, for example, cause the storage for an instance of `RNG` to be included in the layout of the `SceneWithoutParts` type.

For the sake of developers who primarily think in C/C++ terms, a basic mental model to employ would be that a `require Thing;` or a field of type `Thing` maps to a *pointer* to a `Thing`, while a `part` of type `Thing` maps to a *value* of type `Thing`.

#### Wiring: Satisfying Requirements

The simple declaration of a component type like `Scene` above:

```
component Scene
{
    part RNG;
    part LightSampling;
    part FilmSampling;
}
```

hides the fact that along with describing the parts that make up a `Scene`, the `part` declarations also serve to determine how those parts are wired together.

In a simple case, like `Scene` above, the wiring can all be inferred by the Slang compiler.
Each of `LightSampling` and `FilmSampling` have a single `require`ment, for an instance of `RNG`, and there just happens to be exactly one instance of `RNG` there in the body of `Scene`.
Inference can also apply for `require`ments of interface type.

Rather than rely on inference, a developer can specify how wiring should be performed.
For example, to make the wiring in the previous example more explicit, we can give a name to the `part` for `RNG`:

```
component Scene
{
    part rng: RNG;
    part LightSampling(rng);
    part FilmSampling(rng);
}
```

In this case the `RNG` part has been bound to the name `rng`, and that name is being explicitly passed into the `part`s for `LightSampling` and `FilmSampling`.

When `part`s are given explicit names, it also becomes possible to declaring more than one `part` of the same type.
Consider this alternative version of the scene component:

```
component SceneWithMultipleRNGs
{
    part lightRNG: RNG;
    part LightSampling(lightRNG);

    part filmRNG: RNG;
    part FilmSampling(filmRNG);
}
```

Here the `SceneWithMultipleRNGs` component aggregates two distinct `RNG` components, with each one being used to satisfy the `RNG` requirement of one of the other parts.

Rather than build a fully complete graph of components as `part`s, a coarse-grained `component` type can instead declare its own `require`ments, and those can be used to automatically satisfy the requirements of its parts.
For example, a variation of the scene component that encapsulates the two sampling concerns but leaves the RNG as an unsatisfied requirement might be:

```
component SceneThatNeedsExternalRNG
{
    require RNG;

    part LightSampling;
    part FilmSampling;
}
```

Note that when a `part` is declared, the Slang compiler will statically determine how all of its `require`ments will be satisfied.
It will consult the arguments provided to the `part` declaration first, and then look for a sibling `require` or `part` member in the enclosing `component` type declaration.
If this search fails, an error will be diagnosed:

```
component BadScene1
{
    part LightSampling; // ERROR: `RNG` requirement of `LightSampling` was not satsified
}
```

If multiple matching candidates are found, then that is also an error (and a list of candidates should be printed, as for ambiguous overload resolution):

```
component BadScene2
{
    require rng1 : RNG;
    part rng2 : RNG;

    part LightSampling; // ERROR: ambiguity when automatically satisfying `RNG` requirement of `LightSampling`
}
```

### Layout and Parameter Binding

We intend `component` types to be used for composition of shader programs from coarse-grained features, including the shader parameters of those features (which might otherwise be expressed as global-scope shader parameters).
Given this intention, it is vital that we carefully think about the layout of instances of `component` types, especially when used as, e.g., entry-point parameters.

#### Instance vs. Reference Layout

Much like a `class` type, we need to distinguish between the layout for *instances* of a `component` type, vs. the layout for a *reference* to an instance.
As for `class` types, a reference to a `component` type is semantically a pointer, for the purposes of layout.

The instance layout of a `component` type can be computed by a process similar to that is used for `struct` types, in terms of how things like fields are handled.
The key things that need to be decided, then, are how `part` and `require` declarations should influence layout.

#### In-Memory vs. Parameter Layout

We are going to distinguish between two modes for how and where a `component` type might be used: a component that resides "in memory," vs. a component that is being used to define the overall parameter layout of a shader.

This proposal currently only defines support for `component` types as part of defining the parameter signature of a shader program.
There is no support defined here for, say, loading a component from a `RWByteAddressBuffer`.
We will still define the "in memory" case here, as it would be needed for those use cases, so that the distinction will be clear if we later decide to support such cases.

#### Part Declarations

A `part` declaration of type `P` inside of a `component` declaration will be laid out as if it were a field using the instance layout of `P`.

A simple consequence of this choice is that a developer can write a large `component` type to aggregate many other features/concerns as `parts`, and have control over the relative ordering of its contents.

#### Require Declarations

For the "in memory" layout mode:

* A `require` declaration using a concrete component type `R` is laid out as a field of pointer type (a pointer to an instance of `R`)
* A `require` declaration using an `interface` type `I` is laid out as a field of the existential type `any I`

More space-optimized layouts are possible, but we elect not to get to clever in this proposal.

For the "shader parameter" layout mode:

* A `require` declaration is laid out the same as the unit type (`void`); that is, it consumes zero bytes.

In "shader parameter" layout mode, it is the responsibility of the Slang compiler's back-end to synthesize the appropriate value in contexts where it is referenced (this will be covered more in the detailed design).

#### Shader Parameters of Component Type

A top-level shader parameter can be either declared at global/`namespace` scope in a module, or as an explicit/implicit parameter of an entry point.
Slang lays out module scopes and entry-point scopes in a manner similar to a `struct` type, with the parameters taking the place of fields.
We can thus *also* view the layout process for module and entyr-point scopes as similar to computing the instance layout for a `component` type.

For any top-level shader parameter of a `component` type `C`, the surrounding entity (module or entry point) will be treated *as if* that parameter was instead a `require` declaration for `C` (with the same name as the original parameter).
Because we expect to be using the "shader parameter" layout mode for entry points and modules, these pseudo-`require` declarations will consume zero bytes in the parameter layout for the parent entity (entry point or module).

> Open: This is one of the aspects of the design that we expect to require the most iteration and experimentation once a proof-of-concept implementation is available. It is likely that we won't know the exact right semantics to use until we are writing code to interface a renderer with this stuff.
>
> One concrete possibility is that we should by default not allow explicit shader parameters to use `component` types, and instead somehow add support for `part` and `require` declarations at global/`namespace` scope, as well as for entry-point parameters.
> Pushing this burden back on shader authors invites them to carefully think about what kind of layout they want/expect.
>
> Another concrete possibility is to disallow explicit shader parameters of `component` type entirely, and only support the case where a component type is a shader parameter by virtue of being the implicit `this` parameter of an entry point declared inside a `component`.
> Hopefully by restricting support to only the one use case, we will have a better chance of finding a satisfying default policy.

### Slang Compiler API

The Slang compilation API had the interface `slang::IComponentType` for a long time, and this proposal might be the first time that the choice of name for that interface becomes clear.

After compiling a module through the Slang compiler API, the user should be able to look up a `component` type declaration by name and get back an `IComponentType` to represent it.
Just like a module or entry point, these `IComponentType`s represent linkable code, and can be used for composition/linking through the relevant Slang compiler API operations.

#### Dependencies

Internally, the implementation of `IComponentType` stores a list of unresolved dependencies.
This list is used for things like:

* An `IComponentType` representing a module stores references to the modules that it `import`s in its dependency list

* An `IComponentType` representing an entry point stores a reference to the module where the entry point is declared in its dependency list

For an `IComponentType` reprsenting a `component` type declaration, its dependency list should store a reference to the module where the `component` type was declared, along with references to the types that it `require`s.

The discussion of layout for top-level shader parameters of `component` type above introduces the possibility that an entry point or module might conceptually have `require` declarations (at least for the purposes of layout).
These conceptual `require`s should be stored as dependencies of a module or entry point, just as they would be for a `component` type declaration.

#### Composition

Using the Slang compilation API to compose one or more `IComponentType`s corresponding to `component` type declarations will have a semantic effect similar to (but not identical to) what would result if those same `component` types were specified in the same sequence as `part`s of a larger aggregate.
That is, if one has `component` types like:

```
component A { /* ... */ }
component B { /* ... */ }
component C { /* ... */ }
```

And uses the Slang compilation/reflection API to look them up with code like:

```c++
slang::IComponentType* a = module->findComponentTypeByName("A");
slang::IComponentType* b = module->findComponentTypeByName("B");
slang::IComponentType* c = module->findComponentTypeByName("C");
```

then C++ code like the following:

```c++
slang::IComponentType* parts[] = { a, b, c };
slang::IComponentType* composed;
slangSession->createCompositeComponentType(
    parts,
    3,
    &composed);
```

is comparable to the following Slang declaration:

```
component Composed
{
    part A;
    part B;
    part C;
}
```

The primary difference between the two cases is that when using the Slang language to compose one or more `part`s, the compiler will enforce that the programmer must account for the `require`ments of all the parts.
If, say, `A` above had a `require X` in it, then the programmer using Slang would be forced to write something like:

```
component Composed
{
    require X; // unsatisfied requirement from A needs to be made explicit as a requirement of this aggregate
    part A;
    part B;
    part C;
}
```

In contrast, if composing `{a,b,c}` using the C++ `createCompositeComponentType` API, the unresolved `X` requirement of `a` would automatically become an unresolved `X` requirement on `composed`.

The `createCompositeType` API also lacks the more fine-grained controls that `require` and `part` declarations give, where components can be bound to names and those names can be used to make it explicit how dependencies should be wired up.
It is possible that the compilation API could be extended with such support, but we do not include such work in this proposal.

#### Linking

When asked to link an `IComponentType`, the Slang compilation API already has logic to detect the unsatisfied dependencies of the input program and attempt to link them in.
At a high level, for each unsatisfied dependency the API implementation will attempt to find an `IComponentType` that it can link in, and it accumulates a list of these found `IComponentType`s (removing duplicates along the way).
If the search ever fails, the linking process itself fails.
Otherwise, the API implementation does the equivalent of composing the input program with the list of found `IComponentType`s to form a new aggregate.
This process is repeated until either an error is encountered or no unsatisfied dependencies remain.

The above process currently only handles the case where an unsatisfied dependency is a module, and it satisfies such dependencies using the module itself.
This proposal adds two new cases that the above logic should account for:

* If an unresolved dependency is for a concrete `component` type, then that component type should be used to satisfy the depdendency, as if it was specified using a `part` declaration; whatever specific `require`s in the program gave rise to the unsatisfied requirement should then be wired up to that conceptual `part` for the purposes of code generation.

* If an unresolved depdendency is for an `interface` type, then the linker should diagnose an error.

### Summary

We have proposed a new kind of type declaration: `component` types.
These new declarations provide first-class support for describing the dependencies between components (via `require` declarations) and for expressing the construction of a new component by aggregating one or more parts (via `part` declarations).

The design of `component` types is motivated by the desire for a first-class language construct that can be used for separation of concerns that represent logical "features" of a shader codebase.
Our experience has shown that neither modules nor `struct` types are at the right granularity to apply cleanly to such features, so `component` types are designed to provide a granularity that sits between the two.

Detailed Explanation
--------------------

The previous sections went deep into many details of the feature proposal, so our focus in this section is on implementation considerations.

### Parsing

We expect that `component` types can re-use most of the existing parsing logic that is already shared between `struct` and `class` types.
Adding `require` and `part` as keyword-based declarations should also be a simple application of techniques already used throughout the parser.

Following the existing policies of the Slang compiler, we propose that the parser should not attempt to rule out the various invalid cases of nesting (e.g., `init` declarations in a `component` declaration, or `require` declarations in a `struct`, etc.), and instead try to be relatively permissive during parsing and diagnose problems during semantic checking.

### Semantic Checking

One of the most important parts of semantic checking for this feature will be diagnosing all the various cases that we are intentionally not allowing.
We need to diagnose on most attempts to use `component` types, because they are only allowed in very narrow contexts.
Similarly, we will need to include checking logic for all of the new declarations (`component`, `require`, and `part`) to ensure that they are only nested in contexts that are explicitly allowed.

Semantically, `require` and `part` declarations behave a lot like field/variable declarations (insofar as they bind a name to a value that is an instance of some type), and hopefully can find a suitable place in the AST class hierarchy that allows them to leverage some of the code that already handles variable-like declarations.

The lookup rules for `require` and `part` declarations, where unnamed declarations implicitly pull the members into scope should in principle be implementable using the compiler-internal support for "transparent" declarations (already used for things like legacy `cbuffer` declarations and unscoped `enum`s).

The most complicated task that needs to be performed during semantic checking is validation of `part` declarations, to ensure that their requirements are implicitly or explicitly met.
We propose the following sketch of how the task can be approached:

* Inspect the type of the `part` (it must be a `component` type) and collect its `require` members into a list.

* Iterate over any explicit arguments to the `part` and for each check whether it is implicitly coercible to each of the `require`d types. Record any matches in a dictionary from requirement to satisfying argument. Diagnose on any ambiguity (more than one argument matches a given requirement), and on arguments that do not meet any requirements.

* Filter the original list of requirements to just those that did not find a match in the previous step (that is, those without a corresponding entry in the dictionary)

* Inspect the enclosing declaration of the `part` (it must be a `component` type declaration), and iterate over its `require` and `part` declarations (other than the `part` being checked). For each, take its type and match it with the remaining requirements in the same was as was done for arguments. Diagnose any ambiguities. For matches, synthesize a member lookup expression on `this` comparable to what would have been passed for an explicit argument.

* Store the generated dictionary alongside the `part` declaration, akin to how witness tables are stored on conformance declarations.

### Lowering and IR

Two key (and related) challenges that need to be addressed at the IR level are:

* When using the "shader-parameter" layout, a `component` instance does not include any representation of its `require` members, so there is no obvious way to lower references to those members.

* For many targets we cannot (or do not want to) rely on general-purpose pointers when passing around `component`s, so the conceptual pointers that represent a `require` for the "in-memory" layout may need to be specialized/optimized out of existence.

We start by defining two ways of representing a `component` type in the IR:

* For each `component` type declaration, we will generate an IR-level `struct` that corresponds to its instance data in "shader-parameteter" layout

* We introduce a new pointer-like type `ComponentPtr<T>` that conceptually represents a reference to a `component`, where the instance data is of type `T`.

Any places where a `component` type is used as the type of a parameter, local variable, or intermediate expression will use the type `ComponentPtr<T>`.
Any `part` declaration of type `P` will map to IR-level fields using the instance-data type for `P`.

Most code that works with `component`s can then be lowered to use ordinary pointer-based operations on `ComponentPtr<T>`.
For example, fields of a `component` can be accessed with IR code similar to that used for an AST-level `struct`, just with an additional layer of indirection/dereference due to the `ComponentPtr`.
The challenge, then, is in how we handle access to `require` and `part` members.

We note that conceptually we can reconstruct an entire value of a `component` type given a value (or reference to a value) of its "shader-parameter" layout instance data *plus* a list of the values that should be used for its `require`s.
We thus propose an IR instruction with a name like `makeComponent` that semantically performs this operation: it's operands are a value of type `T` (where `T` is the instance data type for some component type), and a sequence of values for the `require`s of that component type (represented as `ComponentPtr`s in the case where they are components), and yields a `ComponentPtr<T>`.

Next, we observe that in cases where a value of type `ComponentPtr<T>` is the result of a `makeComponent` instruction, then access to any of the `require` members of that value can be peephole optmized to just be the corresponding operand from the `makeComponent`.

Similarly, any access to a `part` member of type `P` on a value `v` can itself be translated into a `makeComponent` instruction as follows:

* Emit an instruction to load/reference the shader-parameter layout instance data for that `part`, which is just a field of `T`. Call the result `base`.

* For each `require` of `P`, look up the corresponding argument expression (cached during semantic checking of the AST) and emit it in a context where the implicit `this` parameter is bound to `v`. Call the resulting values `reqArgs`.

* Emit a `makeComponent(base, reqArgs...)`, which will represent the `part` that was accessed.

In order to generate code that no longer relies on pointers at runtime, a specialization pass is then needed, to identify calls where an argument is a `makeComponent` instruction and the corresponding parameter is a `ComponentPtr<T>`.
Such call sites can be specialized by replacing the `makeComponent` argument with the (deduplicated) operands of the `makeComponent`, generating a specialized callee that accepts corresponding parameters in place of the `ComponentPtr<T>`, which then begins its body with a `makeComponent` to reconstruct the original argument value.
Note that deduplication here is vital, and should be applied across all `component`-type parameters of the callee at once, because we want to ensure that even if a given component has been aliased and is accessed via multiple `require` paths, it will translate into a single paraemter in the final generated code.
Ee are able to emulate aliased references to a component, by specializing the aliasing out of existence.

At the top level, the composed and linked `IComponentType`s for a shader program form the starting point for the specialization that unfolds.
When an `IComponentType` representing a `component` type declaration gets linked in, it should lower to an IR global shader parameter using the (shader-parameter layout) instance data for that `component` type, along with a global-scope `makeComponent` instruction that is based on how the composition and linking process satisfied its `require`ments.
For any entry-point parameter that translates to an IR `ComponentPtr<T>` the effective argument for that parameter will then corresponding to a global-scope `makeComponent` instruction, which can be used to bootstrap the specialization process.

Alternatives Considered
-----------------------

Many of the most important features of Slang - things like generics, `interface`s, and `extension`s - were adopted, at least in part, because they were battle-tested ideas that were already implemented in many languages, including some more mainstream modern languages like Rust and Swift.
This proposal is different, because there is not an established precedent for the kind of feature we are proposing.
While we believe this is a good and perhaps even *necessary* feature for the future of Slang, it would be irresponsible to not look for alternatives that come with less risk.

### Do Nothing

The obvious alternative to most feature proposals is to simply not adopt the feature.
In this case, the alternative leaves developers with the two main alternatives we describe in the background section (field-oriented decompositions, and type-based decomposition using `struct`s), when they are trying to achieve good separation of concerns for the features of a shader codebase.

We believe that the status quo is not acceptable, but even if others agree, it may not justify the effort and risk that a feature like this entails.

### Just Lean on Pointers

If the GPU graphics world changed overnight and suddenly all the major platforms supported flexible general-purpose pointers with great performance, it would be more difficult to argue that this feature is strictly *necessary* for developers to achieve good separation of concerns.
Developers could simply adopt the same pointer-based data structures that they might use in a non-performance-critical CPU codebse (whether in C/C++ or in something like Rust, using borrows instead of raw pointers).

To date, the philosophy on the Slang project has been that we are reluctant to make major language features that affect software architecture reliant on new hardware or drivers.
Consider how the `ParameterBlock<T>` feature was carefully intentionally designed so that even if it was motivated by Vulkan descriptor sets and D3D12 descriptor tables, it was still able to be implemented with good efficiency for targets like D3D11 or even OpenGL.

We believe that the constructs in this proposal would be valuable to have in the language, whether or not "good enough" pointer support becomes widely available.

### Improve Some Other Language Feature to Fill the Gap

This is a bit of a catch-all alternative, covering ideas like:

* Find a way to extend `struct` types so that they can avoid their inability to model aliasing (perhaps by supporting mixin inheritance and allowing things like "diamond" inheritance patterns)

* Try to define a subset of `class` types that will be allowed on current GPU targets

* Find a way to extend modules or `namespace`s so that they can avoid introducing global-scope shader parameters that might not be wanted

During the design process that led to this proposal, we have experimented with all of the above ideas (and many more).
What we found is that the resulting feature typically takes the same broad shape, independent of the starting point.
Furthermore, that shape is inconsistent enough with the existing semantics of all of these constructs that it would tend to hurt more than help developer understanding.

### Change Slang to Eliminate Unused Parameters by Default

One could look at the problems that motivate this feature and decide that the *actual* root of the issue is the Slang compiler's stubborn insistence on not eliminating unused shader parameters before performing layout and automatically binding parameters.
The claim that the Slang compiler doesn't have access to the dependency information it needs may ring hollow when the compiler *already* has an IR pass to eliminate unused shader parameters (which must, then, have some form of dependency information to work from), and simply elects to perform layout/binding at an earlier point in compilation.

This alternative would represent a large shift, not only in the Slang compiler, but in the overall philosophy of the Slang project.
One of our overriding goals is to develop tools that are usable and practical for developers in the here and now, but that are also thoughtfully designed for where GPUs and GPU programming are headed.

The relative ordering of layout/binding and elimination of unused shader parameters is an intentional choice, motivated by the desire to improve support for separate compilation and linking of GPU code over time.
Elimination of unused shader parameters requires global knowledge of the entire call graph of a program.
In contrast, a useful separate compilation model requires that layouts can be computed without global information, and are stable, so that they can be part of a binary interface between separately-compiled code.

Future Directions
-----------------

As mentioned in the introduction, this proposal constitutes a "mega-feature."
Despite the apparent scope, we have actually tried our best to restrict ourselves to the "simplest thing that could possibly work" version of the feature.
Many extensions and improvements can be considered on top of this basic framework.
A few examples include:

### Allow `component` types to appear in more places

It is possibly conspicuous that this proposal doesn't mention putting a `component` type in a `ParameterBlock<T>`.

If `component` types prove useful, developers are inevitably going to want to start storing them in data various data structures, or even just as fields of a `struct`.
This proposal hopefully makes it clear that most such uses would amount to a pointer/reference at runtime, and use the "in memory" layout for `component` types.

Bridging the gap between the in-memory and shader-parameter use cases would be an important implementation challenge.

### Inheritance and `virtual`/`override`

Users of Slang consistently want inheritance to be supported for types, and `component` types are in many ways a natural fit for inheritance.
Once Slang has its general infrastructure for inheritance worked out, it would be good to look into how it might apply to `component` types.

Superficially, a `component` type `Derived` that inherits from a `component` type `Base`:

```
component Base { /* ... */ }
component Derived : Base
{ /* ... */ }
```

is semantically similar to having a `part` of type `Base`:

```
component Base { /* ... */ }
component Derived
{
    part Base;
    /* ... */
}
```

The major differences between the two cases arise once `virtual` members start to be considered.

If inheritance is supported, it can be convenient to allow a shorthand syntax for aggregating a `part` that uses a subtype of some component type.
For example, code like this:

```
component Outer
{
    part inner : SomeComponentType
    {
        /* STUFF GOES HERE */
    }
}
```

could be syntactic sugar for something along the lines of:

```
component ANON : SomeComponentType
{
    /* STUFF GOES HERE */
}
component Outer
{
    part inner : ANON;
}
```

### Allow `component` types to provide interfaces via delegation

While `require` declarations represent conceptually represent a kind of input or "socket" on a component (a place where something needs to be plugged in), the conceptual outputs (that would be plugged into the sockets of other components) are most obviously represented by the `interface`s that a component conforms to.

When defining a composite component built from parts, it is possible (and in some cases *required*) for the larget component to expose `require`ments corresponding to a `require`ment of one of its parts, and doing so is fairly lightweight, syntactically.
In contrast, if a composite wants to expose an `interface` that is implemented by one of its `part`s, it would need to declare conformance and manually implement all of that `interface`s requirements by delegating to the given `part`.

If this pattern proves to be a pain point for developers, it might be valuable to provide a `provide` declaration that serves as a kind of dual to `require`.
A declaration like:

```
component Outer
{
    part thatPart : ThatType;
    provide ISomething using thatPart;
}
```

would indicate that the `Outer` component intends to conform to the `ISomething` interface via delegation to `thatPart`.
This declaration would trigger the Slang comiler to synthesize all of the requirements of the interface, and diagnose errors in cases where delegation is not possible (e.g., because of uses of `This` in requirements).

A `provide` declaration along these lines is not really specific to `component`s, and could be useful inside of other kinds of type declaration.

### Allow Slang code to instantiate components

This proposal disallows user code from isantiating components, but there is no strong technical reason to do so.
Instead, that idea is left out from the first version of the feature because developers would need to wrap their head around what components *are* before they can understand more complicated ways of using them.

As this proposal discusses, a local variable declaration using a `component` type is just a reference; neither the declaration itself nor assignment to it brings a component into existence.
However, we have already defined a declaration form that *does* bring a component into existence: a `part` declaration.

Allowing a `part` declaration to occur in any scope where a local variable is allowed would be a modest extension of this proposal.
The IR lowering for such a construct is straightforward, and comparable to a `part` nested in a `component` type.
The primary semantic challenge, for the declaration itself, would be codifying the rules for automatic satisfaction of any `require`ments of the `part`'s type.

One reason for holding off on proposing this detail is that a local `part` declaration like this would clearly expose the fact that components semantically have a well-defined lifetime, and that lifetime cannot be extended just by retaining a reference to them (as can be done for an object of a `class` type).
A local `part` declaration amounts to a stack-allocated instance of the corresponding type, and its lifetime is determined by the scope in which it is declared.
Any code that references such a locally-declared `part` would need to be subject to checks that the reference cannot escape the lifetime of that `part`.

### A clearly-defined semantic model and lattice for objects, components, and values

In the model that this proposal is putting forward, `component`s, objects, and ordinary values (things like numbers, strings, and `struct` types) could potentially be organized into some kind of lattice.
For example, here are some relevant properties:

* Values are not conceptually created or destroyed: they just *are*

* An object does not (semantically) get destroyed; it may simply become inaccessible

* Objects and `component`s both have *identity* while ordinary values do not

* An object can be treated as a value, with that value being the identity of the object

* A component may have a well-defined *lifetime*, and its creation, destruction, and *existence* may all be semantically significant

* A component can only be treated as a value within a scope that is guaranteed to be a subset of its lifetime, and such a value must not be "escaped" from that scope

* An object can be treated as a component, with an idefinite lifetime

Forming (and then *explaining*) a clear semantic model for how these different categories of runtime entities relate is an important step for formalizing what is going on in the language.
Note how the finite-lifetime property of a component has a large overlap with notions of non-copyable or pinned types, as well as things like borrowing.

### Allow functions to use implicit scoping/wiring

The implicit scoping and implicit wiring that come with `require` and `part` are powerful.
Whereas `struct`-based modularity approaches tend to lead to more verbase code and bloated parameter and argument lists focused on plumbing, one of the key benefits for functions nested under a `component` is that they can conveniently reference the members of the current component, its parts, and its dependencies.

It is reasonable to ask if the same benefits could be provided to functions defined *outside* of `component`s.

A superficially-simple extension of the ideas in this proposal would be to allow functions (and other callables) to include `require` clauses (perhaps in the same syntactic position used for `where` clauses).
The body of a function could benefit from implicit scoping to access the requirement, and callers of the function could rely on inference of appropriate arguments at calls sites, instead of explicit arguments.

Such an idea is closely related to the way that `implicit` parameters (and other uses of the `implicit` keyword) work in Scala, and it might be better to instead focus on such a feature as an adoption of ideas from `implicit`s rather than an expansion of `require`.

### Expand the compiler API for composition and linking

When building a composite component using the Slang language features proposed here, a developer has access to two main capabilities that are not exposed via the C++ compiler API for `slang::IComponentType`:

* The developer can include multiple `part`s and/or `require`s of any given type

* The developer can give the `part`s (and `require`s) names, and use those names to make the wiring (the way that the `require`ments of a given `part` are satisfied) explicit

These capabilities were less interesting when the compiler API was mostly being used to compose modules, because modules are effectively singletons.

Entry points have given rise to more nuance in the linker model (and led to API extensions) because unlike with modules it *can* make sense to link in multiple copies of a single entry point (each with different generic arguments), and as a result developers also needed a way to give unique names to the duplicates (in case the mangled names Slang generates are not desired).

If `component` types are adopted, it might be a good time to look for ways to make the composition and linking APIs more full-featured and orthogonal.

One notable gap in the API is that while it technically supports forming complicated hierarchal compositions (akin to nested `struct` types, where the "fields" are the modules and entry points), it does not provide much help in navigating (or reflecting) that structure.
Entry points are referred to by index, not by some kind of path through the hierarchy.
The indexing is required, in practice, because a `slang::IEntryPoint` along is not sufficient to uniquely identify an entry point in a composite program, because there might be multiple instances of any given `IEntryPoint`.
The same basic problems apply in the case of `component` types, but are likely to be come more pronounced.

An additional feature that could be relevant to the linking API that is not *technically* related to `component` types is support for some kind of `union`-like composition.
The current `createCompositeComponentType` operation can be intuitively described as taking a list of types (where modules and entry points are identified with a `struct` of their uniform parameters) and returning a `struct` or tuple.
There are cases where a developer instead wants parameter binding/layout to follow a model more like a `union` (e.g., when it might mix-and-match various entry points, each with their own `uniform` parameters), and it is in many ways a natural extension of the existing functionality.
