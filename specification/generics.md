Generics [section.generic]
========

> Issue:
>
> This chapter needs to define the key semantic-checking operations that relate to generics, including:
> 
> 
> * Inference of \emph{implied constraints} on a generic declaration, based on the signature of that declaration.
> 
> * Validation and canonicalization of constraints on generic declarations.
> 
> * Validation of explicit specialization of a generic (e.g., `G<A,B>`), which includes validating that the constraints on the generic are satisfied by the parameters.
> 
> * Inference of generic arguments in contexts where a generic function is called on value arguments (without first specializing it).
