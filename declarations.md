Declarations {#decl}
============

A \SpecDefine{declaration} is a unit of syntax that typically affects what names are visibile in a scope, and how those names are interpreted.
In the abstract syntax, a source unit comprises a sequence of declarations.

\begin{Syntax}
    \SynDefine{SourceUnit} \\
        ( \SynRef{ModuleDeclaration} \SynOr \SynRef{ImplementingDeclaration} ) \SynOpt \\
        \SynRef{IncludeDeclaration} \SynStar \\
        \SynRef{ImportDeclaration} \SynStar \\
        ( \SynRef{Declaration} ) \SynStar
\end{Syntax}

A declaration may be preceded by zero or more modifiers.

\begin{Syntax}
    \SynDefine{Declaration} \\
        \SynRef{Modifier} \SynRef{Declaration} \\
    \SynOr \SynRef{VariableDeclaration} \\
    \SynOr \SynRef{FunctionDeclaration} \\
    \SynOr \SynRef{TypeDeclaration} \\
\end{Syntax}

A \SpecDefine{binding} is an association of an identifier with a specific entity, such as a declaration.
A \SpecDefine{scope} is a set of bindings.

\begin{Note}
A scope may include more than one binding for the same identifier.
\end{Note}

An \SpecDefine{environment} is either the unique \SpecDefine{empty environment}, or it comprises a scope that is the \SpecDefine{local scope} of that environment, and a \SpecDefine{parent environment}.

For each production in the abtract syntax, there is a \SpecDefine{input environment} in effect at the start of that production, and an \SpecDefine{output environment} in effect after that production.
Each production determines the input environment used by its sub-terms.
When the description of a production does not say otherwise:

\begin{itemize}
\item The input environment of a production's first sub-term is the input environment of that production.
\item The input environment of each sub-term other than the first is the output environment of the preceding sub-term.
\item The output environment of the entire production is the output environment of its last sub-term.
\end{itemize}

The output environment of a token is its input environment.
The output environment of an empty production is its input environment.

When we say that a declaration \SpecDefine{introduces} a binding, we mean that its output environment is the output environment of its last sub-term extended with that binding.

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

A \SpecDef{type declaration} introduces a binding to a type.

\begin{Syntax}
    \SynDefine{TypeDeclaration} \\
        \SynRef{AggregateTypeDeclaration} \\
        \SynOr \SynRef{EnumDeclaration} \\
        \SynOr \SynRef{TypeAliasDeclaration} \\
\end{Syntax}

### Aggregate Types ### {#decl.agg}

\begin{Syntax}
    \SynDefine{AggregateTypeDeclaration} \\
        (\code{struct} \SynOr \code{class} \SynOr \code{interface}) \SynRef{Identifier} \\
        \SynRef{GenericParametersClause}\SynOpt \\
        \SynRef{BasesClause}\SynOpt
        \SynRef{GenericWhereClause}\SynOpt \\
        \SynRef{DeclarationBodyClause} \code{;}\SynOpt\\

    \SynDefine{DeclarationBodyClause} \\
        \lstinline|{| Declaration\SynStar \lstinline|}| 
\end{Syntax}

An \SpecDef{aggregate type declaration} is either a \SpecDef{\kw{struct} declaration}, a \SpecDef{\kw{class} declaration}, or an \SpecDef{\kw{interface} declaration}.

The declarations in the body clause of an aggregate type declaration are referred the \SpecDef{members} of that declaration.

\SubSubSection{Instance and Static Members}{static}

Members of an aggregate type may me marked with a \kw{static} modifier, in which case they are \SpecDef{static members} of the type.
Members not marked with \kw{static} are \SpecDef{instance members} of the type.

Static members are referenced through the type itself.
Instance members are referened through values that are instances of the type.

\SubSubSection{Fields}{field}

Variable declarations that are instance members of an aggregate type declaration are also referred to as the \SpecDef{fields} of the aggregate type declaration.

\SubSubSection{Methods}{method}

Function declarations that are instance members of an aggregate type declaration are also referred to as \SpecDef{methods}.

By default, the implicit \kw{this} parameter of a method acts has a direction of \kw{in}.
A method of a \kw{struct} type declaration may be modified with the \code{[mutating]} attribute, in which case the implicit \kw{this} parameter has a direction of \kw{inout}.

### Bases ### {#decl.agg.bases}

\begin{Syntax}
    \SynDefine{BasesClause} \\
        \code{:} \SynRef{Base} (\code{,} \SynRef{Base})\SynStar

    \SynDefine{Base} \\
        \SynRef{TypeExpression}
\end{Syntax}

An aggregate type declaration has zero or more \SpecDef{bases}.
If an aggregate type declaration has no bases clause, then it has zero bases;
otherwise, the bases of the aggregate type declaration are the types identified by each \SynRef{Base} in that clause.

The list of bases of a \kw{struct} declaration must consist of:

\begin{itemize}
\item at most one \kw{struct} type
\item zero or more interface types
\end{itemize}


The list of bases of a \kw{class} declaration must consist of:

\begin{itemize}
\item at most one \kw{class} type
\item zero or more interface types
\end{itemize}

The list of bases of an \kw{interface} declaration must consist of:

\begin{itemize}
\item zero or more interface types
\end{itemize}

\begin{Legacy}

### Syntax Details ### {#decl.agg.syntax}

The body clause of an aggregate type declaration may end with a semicolon (\code{;}).
The body clause of an aggregate type declaration \emph{must} end with a semicolon if there are any tokens between the closing \lstinline|}| token and the next line break that follows it.

\begin{Note}
Put more simply: a closing \code{;} is not required on an aggregate type declaration \emph{so long} as there is nothing but trivia after it on the same line.
\end{Note}

\end{Legacy}

\begin{Legacy}
### Legacy: Aggregate Type Specifiers ### {#decl.agg.type-specifier}

An aggregate type declaration may be used as a type specififer in declarations using traditional syntax.

When an aggregate type declaration is used as a type specififer, the closing \lstinline|}| of its body must be followed by another token on the same line.

\end{Legacy}

### `enum` Declarations ### {#decl.enum}

\begin{Syntax}
    \SynDefine{EnumDeclaration} \\
        \code{enum} \SynRef{Identifier} \\
        \SynRef{GenericParametersClause}\SynOpt \\
        \SynRef{BasesClause}\SynOpt
        \SynRef{GenericWhereClause}\SynOpt \\
        \SynRef{EnumBody} \code{;}\SynOpt\\

    \SynDefine{EnumBody} \\
        \SynRef{TraditionalEnumBody} \\
        \SynOr \SynRef{DeclarationBody}
\end{Syntax}

An \SpecDef{\kw{enum} declaration} introduces a binding for a type whose instances value into one or more cases.

An \kw{enum} declaration that has a declaration body is a \SpecDef{modern \kw{enum} declaration}.
A \kw{enum} declaration that has a traditional \kw{enum} body is a \SpecDef{traditional \kw{enum} declaration}.

An \kw{enum} declaration may have a bases clause, in which case the list of bases must consist of:

\begin{itemize}
\item at most one proper type; if present, this determines an \SpecDef{underlying type} for the \kw{enum} declaration.
\item zero or more interface types
\end{itemize}

A traditional \kw{enum} declaration always has an underlying type.
If an underlying type is not specified in the bases list of a traditional \kw{enum} declaration, then the underlying type of that declaration is \code{Int}.
The underlying type of a traditional \kw{enum} declaration must be a built-in integer type.

A modern \kw{enum} declaration must not specify an underlying type.

\SubSubSection{Cases}{case}

\begin{Syntax}
    \SynDefine{CaseDeclaration} \\
        \code{case} \SynRef{Identifier} \SynRef{InitialValueClause}\SynOpt
        
    \SynDefine{TraditionalEnumBody} \\
        \lstinline|{| (TraditionalCaseDeclaration \code{,})\SynStar \lstinline|}| \\

    \SynDefine{TraditionalCaseDeclaration} \\
        \SynRef{Identifier} \SynRef{InitialValueClause}\SynOpt
\end{Syntax}

The possible values of an \kw{enum} type are determined by the \SpecDef{case declarations} in its body.
An \kw{enum} type has one case for each case declaration in its body.

The case declarations in a modern \kw{enum} declaration are declared using the \kw{case} keyword.
The case declarations in a traditional \kw{enum} body are \SpecDef{traditional case declarations}.

Each case of a traditional \kw{enum} declaration has an \SpecDef{underlying value}, that is a value of the underlying type of that \kw{enum} declaration.
When a traditional case declaration includes an initial-value expression, its underlying value is the result of evaluating that expression, with the underlying type of the \kw{enum} declaration as the expected type.
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

A \SpecDef{type alias declaration} introduces a binding that resolves to some other type.

\begin{Syntax}
    \SynDefine{TypeAliasDeclaration} \\
        \SynRef{ModernTypeAliasDeclaration}
        \SynOr \SynRef{TraditionalTypeAliasDeclaration}

    \SynDefine{ModernTypeAliasDeclaration} \\
        \code{typealias} \SynRef{Identifier} \\
        \SynRef{GenericParametersClause}\SynOpt \\
        \SynRef{GenericWhereClause}\SynOpt \\
        \code{=} \SynRef{TypeExpr} \code{;}
\end{Syntax}

\begin{Checking}
    \DerivationRule{
        \begin{trgather}
        \CheckType{\ContextVarA}{type}{\ContextVarB} \\
        \end{trgather}	
    }{
        \CheckDecl{\ContextVarA}{\code{typealias} name = type\code{;}}{\ContextVarB,\code{type} name = type}
    }

\end{Checking}
    

\begin{Legacy}

\SubSubSection{Traditional Syntax}{legacy}

A type alias may also be declared using a \SpecDef{traditional type alias declaration}.

\begin{Syntax}
    \SynDefine{TraditionalTypeAliasDeclaration} \\
        \code{typedef} \SynRef{TypeSpecifier} \SynRef{Declarator} \code{;}
\end{Syntax}

\end{Legacy}

### Associated Types ### {#decl.type.associated}

An \SpecDef{associated type declaration} introduces a type requirement to an \kw{interface} declaration.

\begin{Syntax}
    \SynDefine{AssociatedTypeDeclaration} \\
        \code{associatedtype} \SynRef{Identifier} \\
        \SynRef{GenericParametersClause}\SynOpt \\
        \SynRef{BasesClause}\SynOpt \\
        \SynRef{GenericWhereClause}\SynOpt \code{;}
\end{Syntax}

An associated type declaration may only appear as a member declaration of an \kw{interface} declaration.

%An associated type declaration introduces a type into the signature of an interface, without specifying the exact concrete type to use.
%An associated type is an interface requirement, and different implementations of an interface may provide different types that satisfy the same associated type interface requirement:

Variables {#decl.var}
---------

\begin{Syntax}
    \SynDefine{VariableDeclaration} \\
        (\code{let} \SynOr \code{var}) \SynRef{Identifier}
            \SynRef{TypeAscriptionClause}\SynOpt
            \SynRef{InitialValueClause}\SynOpt \code{;}
    
    \SynDefine{TypeAscriptionClause}
        \code{:} \SynRef{TypeExpression}
    
    \SynDefine{InitialValueClause}
        \code{=} \SynRef{Expression}
\end{Syntax}

A \SpecDef{variable} is a storage location that can hold a value.
Every variable has a type, and it can only hold values of that type.
Every variable is either immutable or mutable.

A \SpecDef{variable declaration} introduces a binding for the given \SynRef{Identifier}, to a variable.
A variable declaration using the \kw{let} keyword binds an immutable variable.
A variable declaration using the \kw{var} keyword binds a mutable variable.

Every variable declaration has a type, and the variable it binds is of the same type.

A variable declaration must have either a \SynRef{TypeAscriptionClause} or an \SynRef{InitialValueClause}; a variable declaration may have both.

If a variable declaration has a type ascription, then let \MetaVar{T} be the type that results from evaluating the type expression of that type ascription in the input environment of the declaration.

If a variable declaration has a \SynRef{TypeAscriptionClause} and no \SynRef{InitialValueClause}, then the type of that variable declaration is \MetaVar{T}.

If a variable declaration has both a \SynRef{TypeAscriptionClause} and an \SynRef{InitialValueClause}, then let \MetaVar(E) be the value that results from evaluating the expression of the initial value clause against the expected type \MetaVar{T} in the input environment of the declaration.
The type of the variable declaration is the type of \MetaVar{E}, and its initial value is \MetaVar{E}.

If a variable declaration has an \SynRef{InitialValueClause} but no \SynRef{TypeAscriptionClause}, then let \MetaVar(E) be the value that results from evaluating the expression of the initial value clause in the input environment of the declaration.
The type of the variable declaration is the type of \MetaVar{E}, and its initial value is \MetaVar{E}.

\begin{Legacy}

### Traditional Variable Declarations ### {#decl.var.traditional}

Variable declaration may also be declared using legacy syntax, which is similar to C:

    \begin{Syntax}
        \SynDefine{VariableDeclaration} \\
            \SynRef{LegacyVariableDeclaration} \\

        \SynDefine{LegacyVariableDeclaration} \\
            \SynRef{TypeSpecifier} \SynRef{InitDeclarator} \SynStar \code{;} \\

        \SynDefine{InitDeclarator} \\
            \SynRef{Declarator} \SynRef{InitialValueClause} \SynOpt
    \end{Syntax}

A legacy variable declaration introduces a binding for each \SynRef{InitDeclarator}.
Let \MetaVar{S} be the type that results from evaluating the \SynRef{TypeSpecifier} in the input environment.
The type \MetaVar{T} corresponding to each declarator is determined by evaluating the declarator in the input environment, against input type \MetaVar{S}.

\begin{Note}
Slang does not support the equivalent of the \kw{auto} type specifier in C++.
Variables declared using \kw{let} and \kw{var} can be used to fill a similar role.
\end{Note}

The variables introduced by a legacy variable declaration are immutable if the declaration has a \kw{const} modifier; otherwise it is mutable.

\end{Legacy}

### Variables at Global Scope ### {#decl.var.global}

A variable declaration at global scope may be either a global constant, a static global variable, or a global shader parameter.

Variables declared at global scope may be either a global constant, a static global variables, or a global shader parameters.

\SubSubSection{Global Constants}{const}

A variable declared at global scope and marked with \kw{static} and \kw{const} is a \SpecDefine{global constant}.

A global constant must have an initial-value clause, and the initial-value expression must be a compile-time constant expression.

\begin{Incomplete}
Need a sectin to define what a "compile-time constant expression" is.
\end{Incomplete}

\SubSubSection{Static Global Variables}{global.static}

A variable declared at global scope and marked with \kw{static} but not with \kw{const} is a \SpecDefine{static global variable}.

A static global variable provides storage for each invocation executing an entry point.
Writes to a static global variable from one invocation do not affect the value seen by other invocations.

\begin{Note}
The semantics of static global variable are similar to a "thread-local" variable in other programming models.
\end{Note}

A static global variable may include an initial-value expression; if an initial-value expression is included it is guaranteed to be evaluated and assigned to the variable before any other expression that references the variable is evaluated.
If a thread attempts to read from a static global variable during the evaluation of the initial-value expression for that variable, a runtime error is raised.

There is no guarantee that the initial-value expression for a static global variable is evaluated before entry point execution begins, or even that the initial-value expression is evaluated at all (in cases where the variable might not be referenced at runtime).

\begin{Note}
The above rules mean that an implementation may perform dead code elimination on static global variables, and may choose between eager and lazy initialization of those variables at its discretion.
\end{Note}

\SubSubSection{Global Shader Parameters}{global.param}

A variable declared at global scope and not marked with \kw{static} is a \SpecDef{global shader parameter}.

Global shader parameters are used to pass arguments from application code into invocations of an entry point.
The mechanisms for parameter passing are specific to each target platform.

A global shader parameter may include an initial-value expression, but such an expression does not affect the semantics of the compiled program.

\begin{Note}
An implementation may choose to provide ways to query the initial-value expression of a global shader parameter, or to evaluate it to a value.
Host applications may use such capabilities to establish a default value for global shader parameters.
\end{Note}

### Variables at Function Scope ### {#decl.var.func}

Variables declared at \emph{function scope} (in the body of a function, initializer, subscript acessor, etc.) may be either a function-scope constant, function-scope static variable, or a local variable.

\SubSubSection{Function-Scope Constants}{const}

A variable declared at function scope and marked with both \kw{static} and \kw{const} is a \SpecDef{function-scope constant}.
Semantically, a function-scope constant behaves like a global constant except that its name is only bound in the local scope.

\SubSubSection{Function-Scope Static Variables}{static}

A variable declared at function scope and marked with \kw{static} (but not \kw{const}) is a \SpecDef{function-scope static variable}.
Semantically, a function-scope static variable behaves like a global static variable except that its name is only visible in the local scope.

The initial-value expression for a function-scope static variable may refer to non-static variables in the body of the function.
In these cases initialization of the variable is guaranteed not to occur until at least the first time the function body is evaluated for a given invocation.

\SubSubSection{Local Variables}{local}

A variable declared at function scope and not marked with \kw{static} (even if marked with \kw{const}) is a \SpecDef{local variable}.
A local variable has unique storage for each activation of a function.

\begin{Note}
When a function is called recursively, each call produces a distinct activation with its own copies of local variables.
\end{Note}

Functions {#decl.func}
---------

A \SpecDef{function declaration} introduces a binding to a function.

\begin{Syntax}
    \SynDefine{FunctionDeclaration} \\
        \code{func} \SynRef{Identifier} \\
            \SynRef{GenericParametersClause}\SynOpt \\
            \SynRef{ParametersClause} \\
            \SynRef{GenericWhereClause}\SynOpt \\
            \SynRef{ResultTypeClause}\SynOpt \\
            \SynRef{FunctionBodyClause} \\
\end{Syntax}

### Parameters ### {#decl.param}

The parameters of a function declaration are determined by the \SpecDef{parameter declarations} in its parameters clause.

\begin{Syntax}
    \SynDefine{ParametersClause} \\
        \code{(} (\SynRef{ParameterDeclaration} \code{,}) \SynStar \code{)}

    \SynDefine{ParameterDeclaration} \\
        \SynRef{Identifier} \code{:} \SynRef{Direction}\SynOpt \SynRef{TypeExpression} \SynRef{DefaultValueClause}\SynOpt

    \SynDefine{DefaultValueClause} \\
        \code{=} \SynRef{Expression}
\end{Syntax}

A parameter declaration must include a type expression; the type of the parameter is the result of evaluating that type expression.

A parameter declaration may include a default-value clause; it it does, the default value for that parameter is the result of evaluating the expression in that clause with an expected type that is the type of the parameter.

\SubSubSection{Directions}{dir}

Every parameter has a \SpecDef{direction}, which determines how an argument provided at a call site is connected to that parameter.

\begin{Syntax}
    \SynDefine{Direction} \\
        \code{in} \\
        \SynOr \code{out} \\
        \SynOr \code{take} \\
        \SynOr \code{borrow} \\
        \SynOr \code{inout} \SynOr \code{in out} \\
        \SynOr \code{ref} \\
\end{Syntax}

If a parameter declaration includes a \SynRef{Direction}, then that determines the direction of the parameter; otherwise the direction of the parameter is \kw{in}.

\Paragraph{\code{in}}{in}

The \kw{in} direction indicates typical pass-by-value (copy-in) semantics.
The parameter in the callee binds to a copy of the argument value passed by the caller.

\Paragraph{\code{out}}{out}

The \kw{out} direction indicates copy-out semantics.
The parameter in the callee binds to a fresh storage location that is uninitialized on entry.
When the callee returns, the value in that location is moved to the storage location referenced by the argument.

\Paragraph{\code{take}}{take}

The \kw{take} direction indicates move-in semantics.
The argument provided by the caller is moved into the parameter of the callee, ending the lifetime of the argument.

\Paragraph{\code{borrow}}{borrow}

The \kw{borrow} direction indicates immutable borrow semantics.

If the parameter has a noncopyable type, then the parameter in the callee binds to the storage location referenced by the argument.

If the parameter has a copyable type, then the parameter in the callee may, at the discretion of the implementation, bind to either the storage location referenced by the argument, or a copy of the argument value.

\Paragraph{\code{inout}}{inout}

The \kw{inout} direction indicates exclusive mutable borrow semantics.
The syntax \kw{in out} is equivalent to \kw{inout}

If the parameter has a noncopyable type, then the parameter in the callee binds to the storage location referenced by the argument.

If the parameter has a copyable type, then the parameter in the callee may, at the discretion of the implementation, bind to either:

\begin{itemize}
\item the storage location referenced by the argument
\item a fresh storage location, in which case that location is initialized with a copy of the argument value on entry, and the value at that location is written to the argument on return from the function.
\end{itemize}

\Paragraph{\code{ref}}{ref}

The \kw{ref} direction indicates pass-by-reference semantics.
The parameter in the callee binds to the storage location referenced by the argument.

### Result Type ### {#decl.func.result}

\begin{Syntax}
    \SynDefine{ResultTypeClause} \\
        \code{->} \SynRef{TypeExpression}
\end{Syntax}

Every function has a \SpecDef{result type}, which is the type of value that results from calling that function.
If a function declaration has a result type clause, then the result type of the function is the type that results from evaluating the type expression in that clause.
If a function declaration does not have a result type clause, then the result type of the function is \code{Unit}.

### Body ### {#decl.func.body}

\begin{Syntax}
    \SynDefine{FunctionBodyClause} \\
        \SynRef{BlockStatement} \\
        \SynOr \code{;}
\end{Syntax}

A function declaration may have a \SpecDef{body}.
A function declaration with a body is a \SpecDef{function definition}.

If the function body clause is a block statement, then that statement is the body of the function declaration.
If the function body clause is \code{;}, then that function declaration has no body.

\begin{Legacy}

### Traditional Function Declarations ### {#decl.func.traditional}

A \SpecDef{traditional function declaration} is a function declaration that uses traditional C-like syntax.

\begin{Syntax}
    \SynDefine{TraditionalFunctionDeclaration} \\
        \SynRef{TypeSpecifier} \SynRef{Declarator} \\
        \SynRef{GenericParametersClause}\SynOpt \\
        \SynRef{TraditionalParametersClause}
        \SynRef{GenericWhereClause}\SynOpt \\
        \SynRef{FunctionBodyClause} \\

    \SynDefine{TraditionalParametersClause} \\
        \code{(} (\SynRef{TraditionalParameterDeclaration} \code{,}) \SynStar \code{)}

    \SynDefine{TraditionalParameterDeclaration} \\
        \SynRef{Direction} \SynRef{TypeSpecifier} \SynRef{Declarator} \SynRef{DefaultValueClause}\SynOpt \\
\end{Syntax}

\end{Legacy}

### Entry Points ### {#decl.func.entry}

An \SpecDef{entry point} declaration is a function declaration that can be used as the starting point of execution for a thread.

Constructors {#decl.init}
------------

A \SpecDef{constructor declaration} introduces logic for initializing an instance of the enclosing type declaration.
A constructor declaration is implicitly static.

\begin{Syntax}
    \SynDefine{ConstructorDeclaration} \\
        \code{init} \\
        \SynRef{GenericParametersClause}\SynOpt \\
        \SynRef{ParametersClause} \\
        \SynRef{FunctionBodyClause} \\
\end{Syntax}

A constructor declaratin has an implicit \kw{this} parameter, with a direction of \kw{out}.

%An initializer has access to an implicit `this` variable that is the instance being initialized; an initializer must not be marked `static`.
%The `this` variable of an initializer is always mutable; an initializer need not, and must not, be marked `[mutating]`.

%> Note: Slang currently does not enforce that a type with an initializer can only be initialized using its initializers.
%> It is possible for user code to declare a variable of type `MyVector` above, and explicitly write to the `x` and `y` fields to initialize it.
%> A future version of the language may close up this loophole.

\begin{Note}
Slang does not provide any equivalent to C++ \emph{destructors}, which run automatically when an instance goes out of scope.
\end{Note}

Properties {#decl.prop}
----------

A \SpecDef{property declaration} introduces a binding that can have its behavior for read and write operations customized.

\begin{Syntax}
    \SynDefine{PropertyDeclaration} \\
        \code{property} \\
        \SynRef{Identifier}
        \SynRef{GenericParametersClause}\SynOpt \\
        \SynRef{TypeAscriptionClause} \\
        \SynRef{GenericWhereClause} \\
        \SynRef{PropertyBody} \\

    \SynDefine{PropertyBody} \\
        \lstinline|{| \SynRef(AccessorDecl)\SynStar \lstinline|}|
\end{Syntax}

### Accessors ### {#decl.accessor}

\begin{Syntax}
    \SynDefine{AccessorDecl} \\
        \SynRef{GetAccessorDecl} \\
        \SynRef{SetAccessorDecl} \\

    \SynDefine{GetAccessorDecl} \\
        \code{get} \SynRef{FunctionBodyClause}

    \SynDefine{SetAccessorDecl} \\
        \code{set} \SynRef{ParametersClause}\SynOpt \SynRef{FunctionBodyClause}
\end{Syntax}



Subscripts {#decl.subscript}
----------

A \SpecDef{subscript declaration} introduces a way for the enclosing type to be used as the base expression of a subscript expression.

\begin{Syntax}
    \SynDefine{SubscriptDeclaration} \\
        \code{subscript} \\
        \SynRef{GenericParametersClause}\SynOpt \\
        \SynRef{ParametersClause} \\
        \SynRef{ResultTypeClause} \\
        \SynRef{GenericWhereClause} \\
        \SynRef{PropertyBody} \\
\end{Syntax}

\begin{Note}
Unlike a function declaration, a subscript declaration cannot elide the result type clause.
\end{Note}

Extensions {#decl.extension}
----------

An extension declaration is introduced with the \kw{extension} keyword:

```
extension MyVector
{
    float getLength() { return sqrt(x*x + y*y); }
    static int getDimensionality() { return 2; }
}
```

An extension declaration adds behavior to an existing type.
In the example above, the \code{MyVector} type is extended with an instance method `getLength()`, and a static method `getDimensionality()`.

An extension declaration names the type being extended after the `extension` keyword.
The body of an extension declaration may include type declarations, functions, initializers, and subscripts.

\begin{Note}
The body of an extension may *not* include variable declarations.
An extension cannot introduce members that would change the in-memory layout of the type being extended.
\end{Note}

The members of an extension are accessed through the type that is being extended.
For example, for the above extension of \code{MyVector}, the introduced methods are accessed as follows:

```
MyVector v = ...;

float f = v.getLength();
int n = MyVector.getDimensionality();
```

An extension declaration need not be placed in the same module as the type being extended; it is possible to extend a type from third-party or standard-library code.
The members of an extension are only visible inside of modules that \kw{import} the module declaring the extension;
extension members are \emph{not} automatically visible wherever the type being extended is visible.

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

In order to avoid problems with conflicting conformances, when a module \Char{M} introduces a conformance of type \Char{T} to interface \Char{I}, one of the following should be true:
\begin{enumerate}
    \item{the type \Char{T} is declared in module \Char{M}, or}
    \item{the type \Char{I} is declared in module \Char{M}}
\end{enumerate}

Any conformance that does not follow these rules (that is, where both \Char{T} and \Char{I} are imported into module \Char{M}) is called a \SpecDef{retroactive} conformance, and there is no way to guarantee that another module \Char{N} will not introduce the same conformance.
The runtime behavior of programs that include overlapping retroactive conformances is currently undefined.

Currently, extension declarations can only apply to structure types; extensions cannot apply to enumeration types or interfaces.

Generics {#decl.generic}
--------

Many kinds of declarations can be made \SpecDef{generic}: structure types, interfaces, extensions, functions, initializers, and subscripts.

A generic declaration introduces a \SpecDef{generic parameter list} enclosed in angle brackets \Char{<>}:

```
T myFunction<T>(T left, T right, bool condition)
{
    return condition ? left : right;
}
```

### Generic Parameters ### {#decl.generic.param}

A generic parameter list can include one or more parameters separated by commas.
The allowed forms for generic parameters are:
\begin{enumerate}
    \item{A single identifier like \Char{T} is used to declare a \SpecDef{generic type parameter} with no constraints.}
    \item{A clause like \code{T : IFoo} is used to introduce a generic type parameter \Char{T} where the parameter is \SpecDef{constrained} so that it must conform to the \code{IFoo} interface.}
    \item{A clause like \code{let N : int} is used to introduce a generic value parameter \Char{N}, which takes on values of type \code{int}.}
\end{enumerate}

\begin{Note}
The syntax for generic value parameters is provisional and subject to possible change in the future.
\end{Note}

Generic parameters may declare a default value with \Char{=}:

```
T anotherFunction<T = float, let N : int = 4>(vector<T,N> v);
```

For generic type parameters, the default value is a type to use if no argument is specified.
For generic value parameters, the default value is a value of the same type to use if no argument is specified.

### Explicit Specialization ### {#decl.generic.specialize.explicit}

A generic is \SpecDef{specialized} by applying it to \SpecDef{generic arguments} listed inside angle brackets \Char{<>}:

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

If a generic function/type/etc. is used where a non-generic function/type/etc. is expected, the compiler attempts \SpecDef{implicit specialization}.
Implicit specialization infers generic arguments from the context at the use site, as well as any default values specified for generic parameters.

For example, if a programmer writes:

```
int i = anotherFunction( int3(99) );
```

The compiler will infer the generic arguments `<int, 3>` from the way that \code{anotherFunction} was applied to a value of type \code{int3}.

\begin{Note}
Inference for generic arguments currently only takes the types of value arguments into account.
The expected result type does not currently affect inference.
\end{Note}

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

\begin{Note}
Currently there is no user-exposed syntax for writing a generic extension.
\end{Note}

\begin{Legacy}

Constant Buffers and Texture Buffers {#decl.buffer}
------------------------------------

A \SpecDef{traditional buffer declaration} is a shorthand for declaring a global-scope shader parameter.

\begin{Syntax}
    \SynDefine{TraditionalBufferDeclaration} \\
        (\code{cbuffer} \SynOr \code{tbuffer}) \SynRef{Identifier} \SynRef{DeclarationBody} \code{;}\SynOpt
\end{Syntax}

Given a traditional buffer declaration, an implementation shall behave as if the declaration were desugared into:

\begin{itemize}
\item A \kw{struct} declaration with some unique name \MetaVar{S}, and with the declaration body of the buffer declaration.
\item A global shader parameter declaration with some unique name \MetaVar{P}, where the type of the parameter is \code{ConstantBuffer<S>} in the case of a \kw{cbuffer} declaration, or \code{TextureBuffer<S>} in the case of a \kw{tbuffer} declaration.
\end{itemize}

For each member declared in \MetaVar{S}, a traditional buffer declaration introduces a binding that refers to that member accessed through \MetaVar{P}.

\end{Legacy}