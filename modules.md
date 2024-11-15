Modules {#module}
=======

A <dfn>module</dfn> is a unit of encapsulation for declarations.

Primary Source Unit {#module.source.primary}
-------------------

One or more source units may be compiled together to form a module.
Compilation of a module begins with a single source unit that is the <dfn>primary source unit</dfn> of the module.
An implementation *should* use the primary source unit as a means to identify a module when resolving references from one module to another.

A primary source unit may start with a \code{module} declaration, which specifies the name of the module.

\begin{Syntax}
\SynDefine{ModuleDeclaration}
    \code{module} \SynRef{Identifier} \code{;}
\end{Syntax}

If a primary source unit does not start with a \code{module} declaration, the module comprises only a single source unit, and the name of the module must be determined by some implementation-specified method.
A primary source unit without a \code{module} declaration must not contain any \code{include} declarations.

Note: An implementation might derive a default module name from a file name/path, command-line arguments, build configuration files, etc.

Note: A module might be defined in a single source unit, but have code spread across multiple files.
For example, \code{#include} directives might be used so that the content of a single source unit comes from multiple files.

A \code{module} declaration must always be the first declaration in its source unit.
A \code{module} declaration must not appear in any source unit that is not a primary source unit.

Seconary Source Units {#module.source.secondary}
---------------------

Any source units in a module other than the primary source unit are <dfn>secondary source units</dfn>.

### Include Declarations ### {#module.include}

Secondary source units are included into a module via **`include`** declarations.

\begin{Syntax}
    \SynDefine{IncludeDeclaration} \\
        \code{include} \SynRef{PathSpecifier} \code{;}

    \SynDefine{PathSpecifier} \\
        \SynRef{PathElement} ( \code{.} \SynRef{PathElement} )\SynStar

    \SynDefine{PathElement} \\
        \SynRef{Identifier}
        | \SynRef{StringLiteral}
\end{Syntax}

An implementation must use the name (identifier or string) given in an include declaration to identify a source unit via implementation-specified means.
It is an error if the name given in a source unit matching the given name cannot be identified.

<div class=note>
Include declarations should not be confused with preprocessor \code{#include} directives.

Each source unit in a module is preprocessed independently, and the preprocessor state at the point where an \code{include} declaration appears does not have any impact on how the source unit identified by that include declaration will be preprocessed.
</div>

A module comprises the transitive closure of source units referred to via \code{include} declarations.
An implementation must use an implementation-specified means to determine if multiple \code{include} declarations refer to the same source unit or not.

Note: Circular, and even self-referential, \code{include} declarations are allowed.

### Implementing Declarations ### {#module.implementing}

Secondary source units must start with an \code{implementing} declaration, naming the module that the secondary source unit is part of.

\begin{Syntax}
\SynDefine{ImplementingDeclaration}
    \code{implementing} \SynRef{PathSpecifier} \code{;}
\end{Syntax}

Note: It is an error if the name on an \code{implementing} declaration in a secondary source unit does not match the name on the \code{module} declaration of the corresponding primary source unit.

\begin{Rationale}
\code{implementing} declarations ensure that given a source unit, a tool can always identify the module that the source unit is part of (which can in turn be used to identify all of the source units in the module via its \code{include} declarations).
\end{Rationale}

An \code{implementing} declaration must always be the first declaration in its source unit.
An \code{implementing} declaration must not appear in any source unit that is not a secondary source unit.


Import Declarations {#module.import}
-------------------

Modules may depend on one another via \code{import} declarations.

\begin{Syntax}
  \SynDefine{ImportDeclaration} \\
    \code{import} \SynRef{PathSpecifier} \code{;}
\end{Syntax}

An \code{import} declaration names a module, and makes the public declarations in the named module visible to the current source unit.

Note: An \code{import} declaration only applies to the scope of the current source unit, and does \emph{not} import the chosen module so that it is visible to other source units of the current module.

Implementations must use an implementation-specified method to resolve the name given in an \code{import} declaration to a module.
Implementations may resolve an \code{import} declaration to a previously compiled module.
Implementations may resolve an \code{import} declaration to a source unit, and then attempt to compile a module using that source unit as its primary source unit.
If an implementation fails to resolve the name given in an \code{import} declaration, it must diagnose an error.
If an implementation diagnoses erros when compiling a soure unit named via an \code{import} declaration fails, it must diagnose an error.

<div class=note>
The current Slang implementation searches for a module by translating the specified module name into a file path by:

* Replacing any dot (\Char{.}) separators in a compound name with path separators (e.g., \Char{/})
* Replacing any underscores (\Char{_}) in the name with hyphens (\Char{-})
* Appending the extension \code{.slang}

The implementation then looks for a file matching this path on any of its configured search paths.
If such a file is found it is loaded as a module comprising a single source unit.
</div>




























