Preprocessor [prepro]
============

As the last phase of lexical processing the token sequence of a *source unit* is preprocessed to produce a new token stream.

The preprocessor supported by Slang is derived from the C/C++ preprocessor with a few changes and extensions.

Issue: We either need to pick a normative reference here for some existing preprocessor (and thus bind ourselves to eventually supporting the semantics of that normative reference), or we need to take the time to fully document what the semantics of our current preprocessor are.

Slang programs may use the following preprocessor directives, with the same semantics as their C/C++ equivalent:


* `#include`
* `#define`
* `#undef`
* `#if`, `#ifdef`, `#ifndef`
* `#else`, `#elif`
* `#endif`
* `#error`
* `#warning`
* `#line`
* `#pragma`


An implementation may use any implementation-specified means to resolve paths provided to `#include` directives.

An implementation that supports `#pragma  once` may use any implementation-specified means to determine if two *source units* are identical.

Changes [prepro.changes]
-------

The input to the Slang preprocessor is a token sequence produced by the rules in Chapter 2, and does not use the definition of "preprocessor tokens" as they are used by the C/C++ preprocessor.

Note: The key place where this distinction matters is in macros that perform token pasting.
The input to the Slang preprocessor has to be a valid sequence of tokens *before* any token pasting occurs.

When tokens are pasted with the `##` operator, the resulting concatenated text is decomposed into one or more new tokens.
It is an error if the concatenated text does not form a valid sequence of tokens.

Note: The C/C++ preprocessor always yields a single token from any token pasting, whether or not that token is valid.

Extensions [prepro.extensions]
----------

Issue: At the very least we need to document support for the GLSL `#version` directive, if we intend to keep it.

