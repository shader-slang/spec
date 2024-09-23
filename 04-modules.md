Modules
=======

A _module_ is a unit of encapsulation for declarations.

Primary Source Unit
-------------------

One or more source units may be compiled together to form a module.
Compilation of a module begins with a single source unit that is the _primary_ source unit of the module.
An implementation *should* use the primary source unit as a means to identify a module when resolving references from one module to another.

A primary source unit may start with a **`module`** declaration, which specifies the name of the module.

> **Syntax**:
>
> _ModuleDeclaration_ : `module` _Identifier_ `;`

If a primary source unit does not start with a **`module`** declaration, the module comprises only a single source unit, and the name of the module must be determined by some implementation-specified method.
A primary source unit without a **`module`** declaration must not contain any **`include`** declarations.

> **Note**: An implementation might derive a default module name from a file name/path, command-line arguments, build configuration files, etc.

> **Note**: A module might be defined in a single source unit, but have code spread across multiple files.
> For example, `#include` directives might be used so that the content of a single source unit comes from multiple files.

A **`module`** declaration must always be the first declaration in its source unit.
A **`module`** declaration must not appear in any source unit that is not a primary source unit.

Seconary Source Units
--------------------

Any source units in a module other than the primary source unit are _secondary_ source units.

### Include Declarations

Secondary source units are included into a module via **`include`** declarations.

> **Syntax**:
>
> _IncludeDeclaration_ :
>     `include` _Identifier_ `;`
>   | `include` _StringLiteral_ `;`

An implementation must use the name (identifier or string) given in an include declaration to identify a source unit via implementation-specified means.
It is an error if the name given in a source unit matching the given name cannot be identified.

> **Note**: Include declarations should not be confused with preprocessor `#include` directives.
>
> Each source unit in a module is preprocessed independently, and the preprocessor state at the point where an **`include`** declaration appears does not have any impact on how the source unit identified by that include declaration will be preprocessed.

A module comprises the transitive closure of source units referred to via **`include`** declarations.
An implementation must use an implementation-specified means to determine if multiple **`include`** declarations refer to the same source unit or not.

> **Note**: Circular, and even self-referential, **`include`** declarations are allowed.

### Implementing Declarations

Secondary source units must start with an **`implementing`** declaration, naming the module that the secondary source unit is part of.

> **Syntax**:
>
> _ImplementingDeclaration_ :
>     `implementing` _Identifier_ `;`


> **Note**: It is an error if the name on an **`implementing`** declaration in a secondary source unit does not match the name on the **`module`** declaration of the corresponding primary source unit.

> **Rationale**: `implementing` declarations ensure that given a source unit, a tool can always identify the module that the source unit is part of (which can in turn be used to identify all of the source units in the module via its `include` declarations).

An **`implementing`** declaration must always be the first declaration in its source unit.
An **`implementing`** declaration must not appear in any source unit that is not a secondary source unit.


Import Declarations
-------------------

Modules may depend on one another via **`import`** declarations.

> **Syntax**:
>
> _ImportDeclaration_ :
>     `import` _Identifier_ (`.` _Identifier_)* `;`
>   | `import` _StringLiteral_ `;`

An **`import`** declaration names a module, and makes the public declarations in the named module visible to the current source unit.

> Note: an **`import`** declaration only applies to the scope of the current source unit, and does *not* import the chosen module so that it is visible to other source units of the current module.

Implementations must use an implementation-specified method to resolve the name given in an **`import`** declaration to a module.
Implementations may resolve an **`import`** declaration to a previously compiled module.
Implementations may resolve an **`import`** declaration to a source unit, and then attempt to compile a module using that source unit as its primary source unit.
If an implementation fails to resolve the name given in an **`import`** declaration, it must diagnose an error.
If an implementation diagnoses erros when compiling a soure unit named via an **`import`** declaration fails, it must diagnose an error.

> **Note**: The current Slang implementation searches for a module by translating the specified module name into a file path by:
>
> * Replacing any dot (`.`) separators in a compound name with path separators (e.g., `/`)
>
> * Replacing any underscores (`_`) in the name with hyphens (`-`)
>
> * Appending the extension `.slang`
>
> The implementation then looks for a file matching this path on any of its configured search paths.
> If such a file is found it is loaded as a module comprising a single source unit.


























