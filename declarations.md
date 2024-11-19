Declarations {#decl}
============

A <dfn>declaration</dfn> is a unit of syntax that typically affects what names are visibile in a scope, and how those names are interpreted.
In the abstract syntax, a [=source unit=] comprises a sequence of declarations.

```.syntax
SourceUnit
    ( ModuleDeclaration | ImplementingDeclaration ) ?
    IncludeDeclaration*
    ImportDeclaration*
    ( Declaration )*
```

A declaration may be preceded by zero or more modifiers.

```.syntax
Declaration
    Modifier Declaration
    | VariableDeclaration
    | FunctionDeclaration
    | TypeDeclaration
```

A <dfn>binding</dfn> is an association of an identifier with a specific entity, such as a declaration.
A <dfn>scope</dfn> is a set of bindings.

Note: A scope may include more than one binding for the same identifier.

An <dfn>environment</dfn> is either the unique <dfn>empty environment</dfn>, or it comprises a scope that is the <dfn>local scope</dfn> of that environment, and a <dfn>parent environment</dfn>.

For each production in the abtract syntax, there is a <dfn>input environment</dfn> in effect at the start of that production, and an <dfn>output environment</dfn> in effect after that production.
Each production determines the input environment used by its sub-terms.
When the description of a production does not say otherwise:


* The input environment of a production's first sub-term is the input environment of that production.
* The input environment of each sub-term other than the first is the output environment of the preceding sub-term.
* The output environment of the entire production is the output environment of its last sub-term.


The output environment of a token is its input environment.
The output environment of an empty production is its input environment.

When we say that a declaration <dfn>introduces</dfn> a binding, we mean that its output environment is the output environment of its last sub-term extended with that binding.

Shared Concepts {#decl.shared}
---------------

### Bodies ### {#decl.body}
### Bases ### {#decl.base}
### Parameters ### {#decl.param}
### Accessors ### {#decl.accessor}

Generics {#decl.generic}
--------

Type Declarations {#decl.type}
-----------------

A <dfn>type declaration</dfn> introduces a binding to a type.

```.syntax
TypeDeclaration
    AggregateTypeDeclaration
    | EnumDeclaration
    | TypeAliasDeclaration
```

### Aggregate Types ### {#decl.agg}

```.syntax
    AggregateTypeDeclaration
        (`struct` | `class` | `interface`) Identifier
        GenericParametersClause?
        BasesClause?
        GenericWhereClause?
        DeclarationBodyClause `;`?

    DeclarationBodyClause
        `{` Declaration* `}` 
```

An <dfn>aggregate type declaration</dfn> is either a <dfn>`struct` declaration</dfn>, a <dfn>`class` declaration</dfn>, or an <dfn>`interface` declaration</dfn>.

The declarations in the body clause of an aggregate type declaration are referred the <dfn>direct members</dfn> of that declaration.

#### Instance and Static Members #### {#static}

Members of an aggregate type may me marked with a `static` modifier, in which case they are <dfn>static members</dfn> of the type.
Members not marked with `static` are <dfn>instance members</dfn> of the type.

Static members are referenced through the type itself.
Instance members are referened through values that are instances of the type.

#### Fields #### {#field}

Variable declarations that are instance members of an aggregate type declaration are also referred to as the <dfn>fields</dfn> of the aggregate type declaration.

#### Methods #### {#method}

Function declarations that are instance members of an aggregate type declaration are also referred to as <dfn>methods</dfn>.

By default, the implicit `this` parameter of a method acts has a direction of `in`.
A method of a `struct` type declaration may be modified with the `[mutating]` attribute, in which case the implicit `this` parameter has a direction of `inout`.

### Bases ### {#decl.agg.bases}

```.syntax
    BasesClause
        `:`Base (`,`Base)*

    Base
        TypeExpression
```

An aggregate type declaration has zero or more <dfn>bases</dfn>.
If an aggregate type declaration has no bases clause, then it has zero bases;
otherwise, the bases of the aggregate type declaration are the types identified by eachBase in that clause.

The list of bases of a `struct` declaration must consist of:


* at most one `struct` type
* zero or more interface types



The list of bases of a `class` declaration must consist of:


* at most one `class` type
* zero or more interface types


The list of bases of an [=interface declaration=] must consist of:


* zero or more interface types


#### Traditional Syntax #### {#decl.agg.syntax}

##### Trailing Semicolon #####

For compatibility, the body clause of an aggregate type declaration may end with a semicolon (`;`).
The body clause of an aggregate type declaration must end with a semicolon if there are any tokens between the closing `}` token and the next line break that follows it.

Note: Put more simply: a closing `;` is not required on an aggregate type declaration so long as there is nothing but trivia after it on the same line.

##### Aggregate Type Specifiers ##### {#decl.agg.type-specifier}

An aggregate type declaration may be used as a type specififer in declarations using traditional syntax.

When an aggregate type declaration is used as a type specififer, the closing `}` of its body must be followed by another token on the same line.

### `enum` Declarations ### {#decl.enum}

```.syntax
    EnumDeclaration
        `enum` Identifier
        GenericParametersClause?
        BasesClause?
        GenericWhereClause?
        EnumBody `;`?

    EnumBody
        TraditionalEnumBody
        | DeclarationBody
```

An <dfn>`enum` declaration</dfn> introduces a binding for a type whose instances value into one or more cases.

An [=enum declaration=] that has a declaration body is a <dfn>modern `enum` declaration</dfn>.
A [=enum declaration=] that has a traditional `enum` body is a <dfn>traditional `enum` declaration</dfn>.

An [=enum declaration=] may have a bases clause, in which case the list of bases must consist of:


* at most one proper type; if present, this determines an <dfn>underlying type</dfn> for the `enum` declaration.
* zero or more interface types


A traditional [=enum declaration=] always has an underlying type.
If an underlying type is not specified in the bases list of a traditional `enum` declaration, then the underlying type of that declaration is `Int`.
The underlying type of a traditional [=enum declaration=] must be a built-in integer type.

A modern [=enum declaration=] must not specify an underlying type.

#### Cases #### {#case}

```.syntax
    CaseDeclaration :
        `case` Identifier InitialValueClause?
        
    TraditionalEnumBody :
        `{` (TraditionalCaseDeclaration `,`)* `}`

    TraditionalCaseDeclaration :
        Identifier InitialValueClause?
```

The possible values of an `enum` type are determined by the <dfn>case declarations</dfn> in its body.
An `enum` type has one case for each case declaration in its body.

The case declarations in a modern [=enum declaration=] are declared using the `case` keyword.
The case declarations in a traditional `enum` body are <dfn>traditional case declarations</dfn>.

Each case of a traditional [=enum declaration=] has an <dfn>underlying value</dfn>, that is a value of the underlying type of that `enum` declaration.
When a traditional case declaration includes an initial-value expression, its underlying value is the result of evaluating that expression, with the underlying type of the [=enum declaration=] as the expected type.
The underlying value of a traditional case declaration must be an compile-time-constant integer value.
If a traditional case declaration does not have an initial-value expression, then its underlying value is one greater than the underlying value of the preceding case declaration, or zero if there is no preceding case declaration.

Case declarations are implicitly static.

<!-->
%
%### Conversions ### {#decl.enum.conv}
%
%A value of an enumeration type can be implicitly converted to a value of its tag %type:
%
%```hlsl
%int r = Color.Red;
%```
%
%Values of the tag type can be explicitly converted to the enumeration type:
%
%```hlsl
%Color red = Color(r);
%```
</-->

### Type Aliases ### {#decl.type.alias}

A <dfn>type alias declaration</dfn> introduces a binding that resolves to some other type.

```.syntax
TypeAliasDeclaration :
    ModernTypeAliasDeclaration
    | TraditionalTypeAliasDeclaration

ModernTypeAliasDeclaration :
    `typealias` Identifier
    GenericParametersClause?
    GenericWhereClause?
    `=` TypeExpression `;`
```

```.checking
GIVEN identifier n, type t, context c
GIVEN t checks in c
THEN `typealias` n = t `;` checks in c
```
    

#### Traditional Syntax #### {#decl.type.alias.syntax.traditional}

A type alias may also be declared using a <dfn>traditional type alias declaration</dfn>.

```.syntax
TraditionalTypeAliasDeclaration :
    `typedef` TypeSpecifier Declarator `;`
```

### Associated Types ### {#decl.type.associated}

An <dfn>associated type declaration</dfn> introduces a type requirement to an [=interface declaration=].

```.syntax
    AssociatedTypeDeclaration
        `associatedtype` Identifier
        GenericParametersClause?
        BasesClause?
        GenericWhereClause? `;`
```

An associated type declaration may only appear as a member declaration of an [=interface declaration=].

An associated type is an interface requirement, and different implementations of an interface may provide different types that satisfy the same associated type interface requirement.

Variables {#decl.var}
---------

```.syntax
VariableDeclaration :
    (`let` | `var`) Identifier
        TypeAscriptionClause?
        InitialValueClause? `;`

TypeAscriptionClause :
    `:` TypeExpression

InitialValueClause :
    `=` Expression
```

A <dfn>variable</dfn> is a storage location that can hold a value.
Every variable has a type, and it can only hold values of that type.
Every variable is either immutable or mutable.

A <dfn>variable declaration</dfn> introduces a binding for the given Identifier, to a variable.
A variable declaration using the `let` keyword binds an immutable variable.
A variable declaration using the `var` keyword binds a mutable variable.

Every variable declaration has a type, and the variable it binds is of the same type.

A variable declaration must have either a TypeAscriptionClause or an InitialValueClause; a variable declaration may have both.

If a variable declaration has a type ascription, then let |T| be the type that results from evaluating the type expression of that type ascription in the input environment of the declaration.

If a variable declaration has a TypeAscriptionClause and no InitialValueClause, then the type of that variable declaration is |T|.

If a variable declaration has both a TypeAscriptionClause and an InitialValueClause, then let |E| be the value that results from evaluating the expression of the initial value clause against the expected type |T| in the input environment of the declaration.
The type of the variable declaration is the type of |E|, and its initial value is |E|.

If a variable declaration has an InitialValueClause but no TypeAscriptionClause, then let |E| be the value that results from evaluating the expression of the initial value clause in the input environment of the declaration.
The type of the variable declaration is the type of |E|, and its initial value is |E|.

### Traditional Variable Declarations ### {#decl.var.traditional}

Variable declaration may also be declared using traditional syntax, which is similar to C:

```.syntax
VariableDeclaration :
    LegacyVariableDeclaration

LegacyVariableDeclaration :
    TypeSpecifier InitDeclarator * `;`

InitDeclarator :
    Declarator InitialValueClause ?
```

A legacy variable declaration introduces a binding for each InitDeclarator.
Let |S| be the type that results from evaluating the TypeSpecifier in the input environment.
The type |T| corresponding to each declarator is determined by evaluating the declarator in the input environment, against input type |S|.

Note: Slang does not support the equivalent of the `auto` type specifier in C++.
Variables declared using `let` and `var` can be used to fill a similar role.

The variables introduced by a legacy variable declaration are immutable if the declaration has a `const` modifier; otherwise it is mutable.

### Variables at Global Scope ### {#decl.var.global}

A variable declaration at global scope may be either a global constant, a static global variable, or a global shader parameter.

Variables declared at global scope may be either a global constant, a static global variables, or a global shader parameters.

#### Global Constants #### {#const}

A variable declared at global scope and marked with `static` and `const` is a <dfn>global constant</dfn>.

A global constant must have an initial-value clause, and the initial-value expression must be a compile-time constant expression.

Issue: Need a section to define what a "compile-time constant expression" is.

#### Static Global Variables #### {#global.static}

A variable declared at global scope and marked with `static` but not with `const` is a <dfn>static global variable</dfn>.

A static global variable provides storage for each invocation executing an entry point.
Writes to a static global variable from one invocation do not affect the value seen by other invocations.

Note: The semantics of static global variable are similar to a "thread-local" variable in other programming models.

A static global variable may include an initial-value expression; if an initial-value expression is included it is guaranteed to be evaluated and assigned to the variable before any other expression that references the variable is evaluated.
If a thread attempts to read from a static global variable during the evaluation of the initial-value expression for that variable, a runtime error is raised.

There is no guarantee that the initial-value expression for a static global variable is evaluated before entry point execution begins, or even that the initial-value expression is evaluated at all (in cases where the variable might not be referenced at runtime).

Note: The above rules mean that an implementation may perform dead code elimination on static global variables, and may choose between eager and lazy initialization of those variables at its discretion.

#### Global Shader Parameters #### {#global.param}

A variable declared at global scope and not marked with `static` is a <dfn>global shader parameter</dfn>.

Global shader parameters are used to pass arguments from application code into invocations of an entry point.
The mechanisms for parameter passing are specific to each target platform.

A global shader parameter may include an initial-value expression, but such an expression does not affect the semantics of the compiled program.

Note: An implementation may choose to provide ways to query the initial-value expression of a global shader parameter, or to evaluate it to a value.
Host applications may use such capabilities to establish a default value for global shader parameters.

### Variables at Function Scope ### {#decl.var.func}

Variables declared at <dfn>function scope</dfn> (in the body of a function, initializer, subscript acessor, etc.) may be either a function-scope constant, function-scope static variable, or a local variable.

#### Function-Scope Constants #### {#const}

A variable declared at function scope and marked with both `static` and `const` is a <dfn>function-scope constant</dfn>.
Semantically, a function-scope constant behaves like a global constant except that its name is only bound in the local scope.

#### Function-Scope Static Variables #### {#static}

A variable declared at function scope and marked with `static` (but not `const`) is a <dfn>function-scope static variable</dfn>.
Semantically, a function-scope static variable behaves like a global static variable except that its name is only visible in the local scope.

The initial-value expression for a function-scope static variable may refer to non-static variables in the body of the function.
In these cases initialization of the variable is guaranteed not to occur until at least the first time the function body is evaluated for a given invocation.

#### Local Variables #### {#local}

A variable declared at function scope and not marked with `static` (even if marked with `const`) is a <dfn>local variable</dfn>.
A local variable has unique storage for each activation of a function.

Note: When a function is called recursively, each call produces a distinct activation with its own copies of local variables.

Functions {#decl.func}
---------

A <dfn>function declaration</dfn> introduces a binding to a function.

```.syntax
FunctionDeclaration :
    `func` Identifier
    GenericParametersClause?
    ParametersClause
    GenericWhereClause?
    ResultTypeClause?
    FunctionBodyClause
```

### Parameters ### {#decl.param}

The parameters of a function declaration are determined by the <dfn>parameter declarations</dfn> in its parameters clause.

```.syntax
    ParametersClause
        `(` (ParameterDeclaration `,`)* `)`

    ParameterDeclaration
        Identifier `:` Direction? TypeExpression DefaultValueClause?

    DefaultValueClause
        `=` Expression
```

A parameter declaration must include a type expression; the type of the parameter is the result of evaluating that type expression.

A parameter declaration may include a default-value clause; it it does, the default value for that parameter is the result of evaluating the expression in that clause with an expected type that is the type of the parameter.

#### Directions #### {#dir}

Every parameter has a <dfn>direction</dfn>, which determines how an argument provided at a call site is connected to that parameter.

```.syntax
    Direction
        `in`
        | `out`
        | `take`
        | `borrow`
        | `inout` | `in` `out`
        | `ref`
```

If a parameter declaration includes a Direction, then that determines the direction of the parameter; otherwise the direction of the parameter is `in`.

##### `in` ##### {#dir.in}

The `in` direction indicates typical pass-by-value (copy-in) semantics.
The parameter in the callee binds to a copy of the argument value passed by the caller.

##### `out` ##### {#out}

The `out` direction indicates copy-out semantics.
The parameter in the callee binds to a fresh storage location that is uninitialized on entry.
When the callee returns, the value in that location is moved to the storage location referenced by the argument.

##### `take` ##### {#take}

The `take` direction indicates move-in semantics.
The argument provided by the caller is moved into the parameter of the callee, ending the lifetime of the argument.

##### `borrow` ##### {#borrow}

The `borrow` direction indicates immutable borrow semantics.

If the parameter has a noncopyable type, then the parameter in the callee binds to the storage location referenced by the argument.

If the parameter has a copyable type, then the parameter in the callee may, at the discretion of the implementation, bind to either the storage location referenced by the argument, or a copy of the argument value.

##### `inout` ##### {#inout}

The `inout` direction indicates exclusive mutable borrow semantics.
The syntax `in` out} is equivalent to `inout`

If the parameter has a noncopyable type, then the parameter in the callee binds to the storage location referenced by the argument.

If the parameter has a copyable type, then the parameter in the callee may, at the discretion of the implementation, bind to either:


* the storage location referenced by the argument
* a fresh storage location, in which case that location is initialized with a copy of the argument value on entry, and the value at that location is written to the argument on return from the function.


##### `ref` ##### {#ref}

The `ref` direction indicates pass-by-reference semantics.
The parameter in the callee binds to the storage location referenced by the argument.

### Result Type ### {#decl.func.result}

```.syntax
ResultTypeClause :
    `->` TypeExpression
```

Every function has a <dfn>result type</dfn>, which is the type of value that results from calling that function.
If a function declaration has a result type clause, then the result type of the function is the type that results from evaluating the type expression in that clause.
If a function declaration does not have a result type clause, then the result type of the function is `void`.

### Body ### {#decl.func.body}

```.syntax
FunctionBodyClause :
    BlockStatement
    | `;`
```

A function declaration may have a <dfn>body</dfn>.
A function declaration with a body is a <dfn>function definition</dfn>.

If the function body clause is a block statement, then that statement is the body of the function declaration.
If the function body clause is `;`, then that function declaration has no body.

### Traditional Function Declarations ### {#decl.func.traditional}

A <dfn>traditional function declaration</dfn> is a function declaration that uses traditional C-like syntax.

```.syntax
TraditionalFunctionDeclaration :
    TypeSpecifier Declarator
    GenericParametersClause?
    TraditionalParametersClause
    GenericWhereClause?
    FunctionBodyClause

TraditionalParametersClause :
    `(` (TraditionalParameterDeclaration `,`) * `)`

TraditionalParameterDeclaration :
    Direction TypeSpecifier Declarator DefaultValueClause?
```

### Entry Points ### {#decl.func.entry}

An <dfn>entry point declaration</dfn> is a function declaration that can be used as the starting point of execution for a thread.

Constructors {#decl.init}
------------

A <dfn>constructor declaration</dfn> introduces logic for initializing an instance of the enclosing type declaration.
A constructor declaration is implicitly static.

```.syntax
ConstructorDeclaration :
    `init`
    GenericParametersClause?
    ParametersClause
    FunctionBodyClause
```

A constructor declaratin has an implicit `this` parameter, with a direction of `out`.

Note: Slang does not provide any equivalent to C++ destructors, which run automatically when an instance goes out of scope.

Properties {#decl.prop}
----------

A <dfn>property declaration</dfn> introduces a binding that can have its behavior for read and write operations customized.

```.syntax
    PropertyDeclaration :
        `property`
        Identifier
        GenericParametersClause?
        TypeAscriptionClause
        GenericWhereClause
        PropertyBody

    PropertyBody
        `{` AccessorDecl* `}`
```

### Accessors ### {#decl.accessor}

```.syntax
    AccessorDecl
        GetAccessorDecl
        SetAccessorDecl

    GetAccessorDecl
        `get` FunctionBodyClause

    SetAccessorDecl
        `set` ParametersClause? FunctionBodyClause
```



Subscripts {#decl.subscript}
----------

A <dfn>subscript declaration</dfn> introduces a way for the enclosing type to be used as the base expression of a subscript expression.

```.syntax
SubscriptDeclaration :
    `subscript`
    GenericParametersClause?
    ParametersClause
    ResultTypeClause
    GenericWhereClause
    PropertyBody
```

Note: Unlike a function declaration, a subscript declaration cannot elide the result type clause.

Extensions {#decl.extension}
----------

An extension declaration is introduced with the `extension` keyword:

```
extension MyVector
{
    float getLength() { return sqrt(x*x + y*y); }
    static int getDimensionality() { return 2; }
}
```

An extension declaration adds behavior to an existing type.
In the example above, the `MyVector` type is extended with an instance method `getLength()`, and a static method `getDimensionality()`.

An extension declaration names the type being extended after the `extension` keyword.
The body of an extension declaration may include type declarations, functions, initializers, and subscripts.

Note: The body of an extension must *not* include variable declarations.
An extension cannot introduce members that would change the in-memory layout of the type being extended.

The members of an extension are accessed through the type that is being extended.
For example, for the above extension of `MyVector`, the introduced methods are accessed as follows:

```
MyVector v = ...;

float f = v.getLength();
int n = MyVector.getDimensionality();
```

An extension declaration need not be placed in the same module as the type being extended; it is possible to extend a type from third-party or standard-library code.
The members of an extension are only visible inside of modules that `import` the module declaring the extension;
extension members are not automatically visible wherever the type being extended is visible.

An extension declaration may include an inheritance clause:

```
extension MyVector : IPrintable
{
    ...
}
```

The inheritance clause of an extension declaration may only include interfaces.
When an extension declaration lists an interface in its inheritance clause, it asserts that the extension introduces a new conformance, such that the type being extended now conforms to the given interface.
The extension must ensure that the type being extended satisfies all the requirements of the interface.
Interface requirements may be satisfied by the members of the extension, members of the original type, or members introduced through other extensions visible at the point where the conformance was declared.

It is an error for overlapping conformances (that is, of the same type to the same interface) to be visible at the same point.
This includes cases where two extensions declare the same conformance, as well as those where the original type and an extension both declare the same conformance.
The conflicting conformances may come from the same module or difference modules.

<div algorithm>
In order to avoid problems with conflicting conformances, when a module |M| introduces a conformance of type |T| to interface |I|, one of the following should be true:

* The type |T| is declared in module |M|
* The interface |I| is declared in module |M|

Any conformance that does not follow these rules (that is, where both |T| and |I| are imported into module |M|) is called a <dfn>retroactive conformance</dfn>, and there is no way to guarantee that another module |N| will not introduce the same conformance.
The runtime behavior of programs that include overlapping retroactive conformances is currently undefined.
</div>

Currently, extension declarations can only apply to structure types.

Generics {#decl.generic}
--------

Many kinds of declarations can be made <dfn>generic</dfn>: structure types, interfaces, extensions, functions, initializers, and subscripts.

A generic declaration introduces a <dfn>generic parameter list</dfn> enclosed in angle brackets `<>`:

```
T myFunction<T>(T left, T right, bool condition)
{
    return condition ? left : right;
}
```

### Generic Parameters ### {#decl.generic.param}

A generic parameter list can include one or more parameters separated by commas.
The allowed forms for generic parameters are:

* A single identifier like `T` is used to declare a <dfn>generic type parameter</dfn> with no constraints.
* A clause like `T : IFoo` is used to introduce a generic type parameter `T` where the parameter is <dfn>constrained</dfn> so that it must conform to the `IFoo` interface.
* A clause like `let N : int` is used to introduce a generic value parameter `N`, which takes on values of type `int`.

Note: The syntax for generic value parameters is provisional and subject to possible change in the future.

Generic parameters may declare a default value with `=`:

```
T anotherFunction<T = float, let N : int = 4>(vector<T,N> v);
```

For generic type parameters, the default value is a type to use if no argument is specified.
For generic value parameters, the default value is a value of the same type to use if no argument is specified.

### Explicit Specialization ### {#decl.generic.specialize.explicit}

A generic is <dfn>specialized</dfn> by applying it to <dfn>generic arguments</dfn> listed inside angle brackets `<>`:

```
anotherFunction<int, 3>
```

Specialization produces a reference to the declaration with all generic parameters bound to concrete arguments.

When specializing a generic, generic type parameters must be matched with type arguments that conform to the constraints on the parameter, if any.
Generic value parameters must be matched with value arguments of the appropriate type, and that are specialization-time constants.

An explicitly specialized function, type, etc. may be used wherever a non-generic function, type, etc. is expected:

```
int i = anotherFunction<int,3>( int3(99) );
```

### Implicit Specialization ### {#decl.generic.specialize.implicit}

If a generic function/type/etc. is used where a non-generic function/type/etc. is expected, the compiler attempts <dfn>implicit specialization</dfn>.
Implicit specialization infers generic arguments from the context at the use site, as well as any default values specified for generic parameters.

For example, if a programmer writes:

```
int i = anotherFunction( int3(99) );
```

The compiler will infer the generic arguments `<int, 3>` from the way that `anotherFunction` was applied to a value of type `int3`.

Note: Inference for generic arguments currently only takes the types of value arguments into account.
The expected result type does not currently affect inference.

### Syntax Details ### {#decl.generic.syntax}

The following examples show how generic declarations of different kinds are written:

```
T genericFunction<T>(T value);
funct genericFunction<T>(value: T) -> T;

__init<T>(T value);

__subscript<T>(T value) -> X { ... }

struct GenericType<T>
{
    T field;
}

interface IGenericInterface<T> : IBase<T>
{
}
```

Note: Currently there is no user-exposed syntax for writing a generic extension.

Traditional Buffer Declarations {#decl.buffer}
-------------------------------

A <dfn>traditional buffer declaration</dfn> is a shorthand for declaring a global-scope shader parameter.

```.syntax
TraditionalBufferDeclaration :
    (`cbuffer` | `tbuffer`) Identifier DeclarationBody `;`?
```

Given a traditional buffer declaration, an implementation shall behave as if the declaration were desugared into:


* A `struct` declaration with some unique name |S|, and with the declaration body of the buffer declaration.
* A global shader parameter declaration with some unique name |P|, where the type of the parameter is `ConstantBuffer<S>` in the case of a `cbuffer` declaration, or `TextureBuffer<S>` in the case of a `tbuffer` declaration.


For each member declared in |S|, a traditional buffer declaration introduces a binding that refers to that member accessed through |P|.
