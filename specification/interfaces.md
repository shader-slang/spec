# Interfaces {#SECTION.interface}

<div class=issue>
This chapter needs to document the rules for what it means for a type to \emph{conform} to an interface, and how the compiler should check for conformance.


The biggest challenge in specifying the rules for conformance is that the Slang compiler does not require an \emph{exact} match between the requirement in an `interface` and the concrete declaration that satisfies it:


* A field can satisfy a `property` requirement.
* A non-\code{throws} function can satisfy a \code{throws} requirement
* A non-`[mutating]` function can satisfy a `[mutating]` requirement
* A function with default arguments can satisfy a requirement without those arguments
* A generic function may satisfy a non-generic requirement
* A generic declaration with fewer constraints may satisfy a generic requirement with more constraints


In the limit, we can say that a type satisfies a requirement if a \emph{synthesized} declaration that exactly matches the requirement signature would type-check successfully.
The body of a synthesized `get` accessor for a property \code{p} would consist of something like \code{return this.p;}.
Similarly, the body of a synthesized `func` for a function \code{f} would consist of something like \code{return this.f(a0, a1, ...);} where the values \code{a0}, etc., are the declared parameters of the synthesized function.

The main place where the above approach runs into wrinkles is around synthesis for generic requirements, where subtle semantic choices need to be made.

Ideally, checking of conformances is something that can be done after checking of all explicit function bodies (statements/expressions) in a module.
Other checking rules can \emph{assume} that a type conforms to an interface if it is declared to, knowing that the error will be caught later if it doesn't.

The important case where conformances can't be checked late is if we support inference (not just synthesis) of declarations to satisfy requirements.
Basically, if we want to support inference of `associatedtype`s, then only way to infer that type is by looking for the declarations that satisfy other requirements.

(Conveniently, checking of requirements also doesn't require looking at function bodies: only signatures)

This chapter is probably also the right place to define the rules for canonicalization of interface conjunctions.

</div>