# SP #026: Upgrading to C++ Modules

This proposal outlines a plan to modernize the Slang codebase by adopting C++20 modules, improving build times and code organization.

## Status

Status: Design Review

Implementation: Not yet implemented

Author: Ellie Hermaszewska

Reviewer: TBD

## Background

Following our recent upgrade to C++20 (SP #022), we now have the opportunity to leverage one of its most significant features: modules. The Slang codebase currently uses traditional header/source file organization with `#include` directives, which leads to several issues:

- **Slow compilation times**: Each translation unit must process all included headers
- **Header dependency complexity**: Changes to widely-included headers trigger larger rebuilds
- **Include guards maintenance**: Potential for build errors with complex includes

C++20 modules address these issues by providing cleaner dependency management and faster compilation through better interface boundaries.

## Proposed Approach

We propose a focused approach to implementing C++20 modules in the Slang codebase:

### Phase 1: Infrastructure Setup (1-2 weeks)

1. **Build system updates**:

   - Add module support to CMake configuration
   - Create module mapping files
   - Set up module caching

2. **Create initial module structure**:

   - Define core module organization (see "Module Organization" below)
   - Set up module interface files

3. **Proof of concept**:
   - Convert a small, self-contained component (e.g., `slang-core`) to modules
   - Measure build time impact and fix any issues

### Phase 2: Core Library Conversion (2-3 weeks)

1. **Convert foundation libraries**:

   - `slang-core` module (containers, IO, etc.)
   - `slang-compiler-core` module (diagnostics, artifacts, etc.)

2. **Update build pipeline**:
   - Ensure CI/CD pipeline supports module builds across all compilers (GCC, Clang, MSVC)

### Phase 3: Full Codebase Conversion (3-4 weeks)

1. **Convert remaining components**:

   - `slang` module (compiler, type system, etc.)
   - Tool-specific modules

2. **Optimize module dependencies**:
   - Refine module boundaries
   - Minimize dependencies between modules

### Module Organization

We propose organizing the codebase into the following primary modules:

```
slang.core                   // Core utilities, containers, IO
slang.compiler_core          // Compiler infrastructure
slang.language               // Language processing (AST, parsing)
slang.ir                     // Intermediate representation
slang.codegen                // Code generation
slang.reflection             // Reflection system
slang.tools                  // Development tools
```

Each module will have submodules as needed. For example:

```
slang.core.containers        // Container classes
slang.core.io                // I/O utilities
slang.core.memory            // Memory management
```

## Detailed Explanation

### Module Interface Files

Each module will have a primary interface file that exports the module's public API. For example:

```cpp
// slang.core.cppm
export module slang.core;

// Re-export submodules
export import slang.core.containers;
export import slang.core.io;
export import slang.core.memory;

// Module-level declarations
export namespace slang {
    // Core declarations visible to importers
}
```

Submodule interface files will focus on specific functionality:

```cpp
// slang.core.containers.cppm
export module slang.core.containers;

// Implementation details
import <memory>;

// Public API
export namespace slang {
    template<typename T>
    class List { /* ... */ };

    template<typename K, typename V>
    using Dictionary = ankerl::unordered_dense::map<K, V>;
}
```

### Implementation Files

Implementation files will import the modules they depend on:

```cpp
// list.cpp
module slang.core.containers;

namespace slang {
    // Implementation of List methods
}
```

### Public API Preservation

**We will maintain all public-facing headers** for backward compatibility with external code. These headers will:

1. Include the necessary module imports
2. Forward declarations to the module implementations
3. Ensure no breaking changes to the public API

Example:

```cpp
// slang.h (public header)
#pragma once

// Legacy header that forwards to module implementation
#ifdef __cpp_modules
import slang.core;
#else
#include "slang-core.h"
#endif

// Public API remains unchanged
```

### Migration Strategy

For each component:

1. Create module interface file(s)
2. Convert internal headers to export declarations
3. Update implementation files to use module imports
4. Test and validate across all supported compilers (GCC, Clang, MSVC)

### External Library Integration

Third-party libraries without module support will be handled through:

1. **Header imports**: Using C++20's ability to import traditional headers

   ```cpp
   import <ankerl/unordered_dense.hpp>;  // Import third-party header
   ```

2. **Wrapper modules**: Creating thin wrapper modules around external libraries when beneficial

## Risks

### Technical Risks

- **Cross-compiler compatibility**: Ensuring consistent module behavior across GCC, Clang, and MSVC
- **Build system complexity**: Module dependencies require more sophisticated build ordering
- **Performance impact**: Initial builds may be slower until module caching is optimized

### Mitigation Strategies

- Test module implementations on all target compilers simultaneously
- Create detailed build documentation for module-aware builds
- Implement incremental conversion to identify and address issues early
- Establish module interface guidelines to prevent dependency cycles

## Alternatives Considered

1. **Wait for more mature module support**:

   - Pros: Less risk, more standardized implementations
   - Cons: Delays benefits, increases technical debt

2. **Partial module adoption**:

   - Pros: Lower risk, focused benefits
   - Cons: Complexity of mixed module/non-module code, incomplete benefits

3. **Module-like organization without C++20 modules**:
   - Pros: Works with older compilers, similar organizational benefits
   - Cons: Misses compilation speed benefits, doesn't solve include problems
