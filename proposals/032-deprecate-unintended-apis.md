SP #032: Deprecate Public APIs That Shouldn't Exist
===================================================

We propose to deprecate a large number of functions, enumerants, etc. from the Slang public API, and command-line options for `slangc`, in cases where any of the following is true:

* the features were never intended for public use

* the features represent design choices we regret

Status
------

Status: Implementation In-Progress

Implementation: -

Author: Theresa Foley (@tangent-vector)

Reviewer: -

Background
----------

This proposal touches on two main categories of features of the Slang compiler codebase:

### Features That Were Never Intended for Public Use

Slang's build process involves some "boostrapping" steps, including needing to invoke the Slang compiler on the source code for the builtin modules, so that the compiled binary for the core module can be embedded into the Slang compiler itself.
Unfortunately, at the time that the bootstrapping process was implemented, the hooks that were required to implement it got declared in the public `slang.h` header, thus enabling others to use those hooks, even if they were never intended to be part of the supported API of the compiler. The same applies to several command-line options for `slangc` (which also surface as enumerants in `slang.h`) that are only intended to be used during the bootstrapping process.

In addition to the bootstrapping case, there are several parts of the API in `slang.h` or options for `slangc` that only exist to support the `slang-test` tool and the approach we use for testing Slang.
An important example is the support for "pass-through" compilation, where `slangc` doesn't actually try to compile a file and instead hands it off to a downstream compiler more-or-less untouched; the cost of supporting this functionality has risen greatly over time, and it only exists to support some of our earliest test cases.

### Features That We Regret

Some things got put into the `slang.h` API that were over-designed from the start, and never saw enough uptake among developers to justify the cost of supporting all the bells and whistles.
Examples include:

* `ISlangCastable` and `ISlangClonable`

* `ISlangFileSystemExt`

* `ISlangWriter`

* The ability for users to override the "prelude" code for particular target languages and/or downstream compilers

Proposed Approach
-----------------

At a high level, we propose to immediately mark the relevant features as deprecated, and to subsequently remove them in a future release.

Given that these features were never intended to be supported, it is reasonable to have a shorter rather than longer period before the features get removed. It is out of scope for a proposal like this to dictate the timeline, but we will note that the need to avoid breaking these features (in the name of compatibility) routinely gets in the way of efforts to clean up and refactor code in the Slang implementation.

Detailed Explanation
--------------------

The established method for deprecation differs based on the kind of feature/symbol involved, and we propose to follow the precedent:

* For functions (including member functions), `struct`s, `enum`s, and `typedef`s in `slang.h`, mark them `[[deprecated]]`

* For individual enumerants, add a comment indicating that they are deprecated

* For COM interfaces:

    * if no other interfaces in the public API inherit from them, mark them ``[[deprecated]]`

    * Otherwise, mark all of their methods as `[[deprecated]]` and add a commend indicating that the entire interface is deprecated

* In cases where an interface method should be *renamed* (with no signature change) as opposed to just deprecated:

    * Change the name of the `virtual` method

    * Introduce a `[[deprecated]]` inline method with the old name that delegates to the `virtual` one

* If a symbol can be moved into `slang-deprecated.h` without breaking other declarations in `slang.h`, it should be moved there

The features we propose to deprecate are:

* interface `ISlangCastable`

* interface `ISlangClonable`

* `struct SlangTerminatedChars`

* type `SlangPathTypeIntegral`

* `enum SlangPathType`

* type `FileSystemContentsCallBack`

* `enum OSPathKind`

* `enum PathKind`

* interface `ISlangFileSystemExt`

* interface `ISlangMutableFileSystem`

* type `SlangWriterChannelIntegral`

* `enum SlangWriterChannel`

* type `SlangWriterModeIntegral`

* `enum SlangWriterMode`

* interface `ISlangWriter`

* interface `ISlangProfiler`

* type `SlangDiagnosticCallback`

* method `slang::IGlobalSession::addBuiltins`

* method `slang::IGlobalSession::setDownstreamCompilerPrelude`

* method `slang::IGlobalSession::getDownstreamCompilerPrelude`

* method `slang::IGlobalSession::setLanguagePrelude`

* method `slang::IGlobalSession::getLanguagePrelude`

* method `slang::IGlobalSession::checkPassThroughSupport`

* method `slang::IGlobalSession::compileCoreModule`

* method `slang::IGlobalSession::loadCoreModule`

* method `slang::IGlobalSession::saveCoreModule`

* method `slang::IGlobalSession::saveCoreModule`

* method `slang::IGlobalSession::getCompilerElapsedTime`

* method `slang::IGlobalSession::compileBuiltinModule`

* method `slang::IGlobalSession::loadBuiltinModule`

* method `slang::IGlobalSession::saveBuiltinModule`

* `enum slang::BuiltinModuleName`

* `enum SlangArchiveType`

* type `CompileCoreModuleFlags`

* `struct CompileCoreModuleFlag`

* method `slang::ISession::createCompileRequest`

* method `slang::ISession::loadModuleFromIRBlob` should be renamed to `loadModuleFromBinaryBlob`

* method `slang::IComponentType::getResultAsFileSystem`

* method `slang::IComponentType::getEntryPointHostCallable`

* function `slang_createGlobalSessionWithoutCoreModule`

* function `slang_getEmbeddedCoreModule`

* option `-emit-ir` should be deprecated

* option `-report-downstream-time` should be marked as internal

* option `-report-perf-benchmark` should be marked as internal

* option `-report-checkpoint-intermediates` should be marked as internal

* option `-source-embed-style` should be deprecated

* option `-source-embed-name` should be deprecated

* option `-source-embed-language` should be deprecated

* option `-unscoped-enum` should be marked as undesirable (and subject to future deprecation/removal)

* option `-preserve-params` should be marked as undesirable (and subject to future deprecation/removal)

* option `-reflection-json` should be marked as undesirable (and subject to future deprecation/removal)

* option `-msvc-style-bitfield-packing` should be marked as undesirable (and subject to future deprecation/removal)

* option `-fspv-reflect` should be marked as undesirable (and subject to future deprecation/removal)

* option `-enable-effect-annotations` should be marked as undesirable (and subject to future deprecation/removal)

* option `-pass-through` should be deprecated

* option `-serial-ir` should be deprecated (it no longer does anything anyway)

* option `-verify-debug-serial-ir` should be deprecated

* option `-file-system` should be deprecated

* option `-no-mangle` should be deprecated

* option `-no-hlsl-binding` should be deprecated

* option `-no-hlsl-pack-constant-buffer-elements` should be deprecated

* option `-archive-type` should be deprecated

* option `-compile-core-module` should be deprecated

* option `-ir-compression` should be deprecated (it does nothing)

* option `-load-core-module` should be deprecated

* option `-save-core-module` should be deprecated

Alternatives Considered
-----------------------

### Maintain Some or All of This Functionality Long-Term

We could decide that some of these APIs are actually worth supporting in the long run, in order to not break users who already rely on them.
Realistically, the easiest way to find out about such users is by deprecating the functionality and seeing if anybody speaks up.

### Remove These Features Immediately, Rather Than Deprecate

Because all of these are parts of the API that we never *wanted* users to rely on, and some of it is stuff that we never *intended* to support, it may be reasonable to just decide by fiat that removal, as opposed to deprecation, is a reasonable course of action.
