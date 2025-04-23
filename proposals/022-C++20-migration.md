# SP #022: Upgrading Slang Codebase to C++20

This proposal outlines a plan to upgrade the Slang codebase from C++17 to C++20, enabling the use of modern C++ features.

## Status

Status: Design Review

Implementation: Not yet implemented

Author: Ellie Hermaszewska

Reviewer: TBD

## Background

The Slang codebase currently uses C++17. C++20 introduces several valuable features that could improve code quality, and developer quality of life. There have been requests from people contributing to the Slang codebase to make this upgrade.

## Related Work

Some large, related C++ codebases have or are migrating to C++20:

- The current Unreal Engine coding standards specify C++20
- Godot is making such a transition (some useful discussion and motivation here: https://github.com/godotengine/godot/pull/100749)

However other similar projects such as LLVM and DXC are still on C++17.

## Proposed Approach

The implementation will merely bump the language standard the slang targets are built with, and fix any breakages in a backwards compatible way. This proposal does not aim to introduce any usage of specific C++20 features, the intention is that these will organically be used as time progresses.

Documentation will need to be updated also.

## Risks

# Risks

## Technical Risks

- **Compiler compatibility gaps** across platforms and environments, this hasn't proven to be an issue with any other language versions or features, c++20 support should be standardized and mature by now
- **Build system failures** on specific platforms, this will be picked up by CI before any merge
- **Third-party dependency incompatibilities** all third party dependencies are compatible with C++20
  - Unordered Dense
  - Spirv headers
  - Spirv tools
  - Vulkan headers

## Customer Impact

Only those compiling from source will be affected, additionally only those who are both compiling from source, and are on a very old compiler. Binary distributions will not be affected.

For the unlikely possibility that there is a consumer with an unupgradeable old compiler who doesn't use the binary distribution, they can make their use case known with very little friction and we can roll back the change until they sort themselves out.

The COM interfaces in the slang headers will not immediately change to use any C++20 features.

Specifically checked with Omniverse, their lowest compiler version is gcc11 which is within the C++20 support versions.

## Compiler Support Matrix

These are the minimum compiler versions we will support.

| Compiler | Minimum Version       | Release Date |
| -------- | --------------------- | ------------ |
| MSVC     | 19.29 (VS 2019 16.10) | May 2021     |
| GCC      | 10.0                  | May 2020     |
| Clang    | 13.0                  | Oct 2021     |

## Detailed Explanation

### Compiler Requirements

Our CI already tests with C++20-compatible compilers:

- GCC 13.0
- Clang 15
- MSVC 19.26

This means we already don't test with older C++17-only compilers.

### Implementation

The implementation will focus on updating build configurations to specify C++20, with minimal code changes initially. We'll gradually adopt C++20 features where they provide clear benefits.

### Documentation Updates

We'll update documentation to reflect new compiler requirements and provide guidance for downstream users.

## Alternatives Considered

1. **Stay on C++17**:

   - Pros: No disruption to users with older compilers
   - Cons: Miss out on language improvements and modern features

2. **Skip to C++23**:

   - Pros: More features, longer before next upgrade needed
   - Cons: Limited compiler support, higher migration risk

3. **Partial adoption via feature test macros**:
   - Pros: Gradual transition, backward compatibility
   - Cons: Complex code with conditional compilation, harder maintenance
