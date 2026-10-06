#!/usr/bin/env python3

import itertools
import os
import re
import sys

# globals
g_verbose = False

g_stdlibLinkPrefix = 'https://docs.shader-slang.org/en/latest/external/core-module-reference/'
g_stdlibDir = None

g_slangPrefix = 'https://docs.shader-slang.org/en/latest/external/slang'
g_slangPrefixGhDir = 'https://github.com/shader-slang/slang/tree/master'
g_slangDir = None

g_slangSpecPrefixGhFile = 'https://github.com/shader-slang/spec/blob/main'
g_slangSpecPrefixGhDir = 'https://github.com/shader-slang/spec/tree/main'
g_slangSpecDir = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))

def warning(*args, **kwargs):
    print('Warning:', *args, file=sys.stderr, **kwargs)

def error(*args, **kwargs):
    print('Error:', *args, file=sys.stderr, **kwargs)
    sys.exit(2)

def verbosePrint(s):
    if g_verbose:
        print(s)

def verbosePrintNoNewline(s):
    if g_verbose:
        print(s, end="")

def getDefaultStandardLibraryReferenceDir():
    return os.path.realpath(os.path.join(os.path.dirname(__file__), "../../stdlib-reference"))

def getDefaultSlangDir():
    return os.path.realpath(os.path.join(os.path.dirname(__file__), "../../slang"))

def printHelpAndExit():
    print('''Scans markdown files and checks for broken links

Usage: check-links.py [options] <files>

Options:
-v                     Verbose output
-slang-dir <dir>       Local directory containing a copy of GitHub repository
                       https://github.com/shader-slang/slang
                       Default: ''' + getDefaultSlangDir() + '''
-stdlib-ref-dir <dir>  Local directory containing a copy of GitHub repository
                       https://github.com/shader-slang/stdlib-reference
                       Default: ''' + getDefaultStandardLibraryReferenceDir() + '''
''')
    sys.exit(1)


class AnchorNotFoundError(Exception):
    pass

# match:                  (> )   (```...)
codeFenceMatcher = re.compile(r"^[ >]*(`{3,}|~{3,})(.*)$")

# match:                   `code`, ``co`de``, ...
codeSpanMatcher = re.compile(r"(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)")

# Yields the lines of a markdown file with code removed so that links and
# anchors in code are not picked up. Lines in fenced code blocks are replaced
# by empty lines and inline code spans by spaces, so line numbers are
# preserved. Code spans spanning multiple lines are not handled.
def markdownLinesWithoutCode(file):
    fence = None
    for line in file:
        m = codeFenceMatcher.match(line)
        if fence is None:
            if m:
                fence = m.group(1)
                yield ""
            else:
                yield codeSpanMatcher.sub(" ", line)
        else:
            # closing fence: same character, at least as long, no info string
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and m.group(2).strip() == "":
                fence = None
            yield ""

# match: [link text](url#anchr "optional title")
# URLs may contain balanced parentheses, e.g., https://en.wikipedia.org/wiki/Foo_(bar)
# The title may also be written as 'title' or (title).
linkMatcherMarkDown = re.compile(r"\[(?:[^\]\\]|\\.)*\]\(\s*((?:[^()\s#]|\([^()\s]*\))*)#?((?:[^()\s]|\([^()\s]*\))*)(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)")

# match:                   <a   ...          href="(url...)#(anchr)"    >
linkMatcherHref = re.compile(r'<a\s(?:[^>]*?\s)?href="([^"#]*)#?([^"]*)"[^>]*>')

# NOTE: we don't use this at the moment, since it's not supported by GitHub markdown viewer
# match:                                 # title {#(anchor)}
# anchorMatcherMarkdownSection = re.compile(r"^#.*\{#([^}]+)\}")

# match:                  <a   ...          id="(anchr)"     >
anchorMatcherA = re.compile(r'<a\s(?:[^>]*?\s)?id="([^"]*)"[^>]*>')

# cache: real path of file -> { anchor: [ line numbers ] }
g_anchorCache = {}

# Returns the anchors defined in a markdown file as a dict mapping each
# anchor to the list of line numbers where it is defined. Throws
# FileNotFoundError if the file does not exist.
def collectAnchors(filename):
    key = os.path.realpath(filename)
    if key in g_anchorCache:
        return g_anchorCache[key]

    verbosePrint(f"Collecting anchors: {filename}")

    anchors = {}
    with open(filename) as file:
        lineNo = 0
        for line in markdownLinesWithoutCode(file):
            lineNo = lineNo + 1
            for m in anchorMatcherA.finditer(line):
                verbosePrint(f"  - found anchor {m.group(1)}")
                anchors.setdefault(m.group(1), []).append(lineNo)

    g_anchorCache[key] = anchors
    return anchors

# Reports anchors that are defined more than once, and empty anchors.
# Returns the number of errors.
def checkDuplicateAnchors(srcFile):
    errors = 0

    for anchor, lineNos in collectAnchors(srcFile).items():
        if len(anchor) == 0:
            for lineNo in lineNos:
                errors = errors + 1
                print(f"{srcFile}:{lineNo}: Empty anchor")
            continue

        for lineNo in lineNos[1:]:
            errors = errors + 1
            print(f"{srcFile}:{lineNo}: Anchor '{anchor}' already defined at line {lineNos[0]}")

    return errors

# returns True if uriPath started with externalUriPrefix and the path
# was found
#
# returns False if uriPath did not start with externalUriPrefix
#
# throws FileNotFoundError if uriPath started with externalUriPrefix
# and the path was not found
#
# if checkAnchor is set and uriFragment is non-empty, also checks that the
# mapped markdown file defines the anchor, and throws AnchorNotFoundError
# if it does not. Fragments on non-markdown files (e.g., GitHub line
# anchors '#L123') are not checked.
def maybeCheckExternalLinkWithRemap(uriPath, externalUriPrefix, localDir, mdToHtmlMap, uriFragment="", checkAnchor=False):
    # match whole path components only, e.g., prefix '.../slang' must not
    # match '.../slang-foo'
    externalUriPrefix = externalUriPrefix.rstrip("/")
    if uriPath == externalUriPrefix or uriPath.startswith(externalUriPrefix + "/"):

        # relative path
        relPath = uriPath[len(externalUriPrefix) + 1:]

        mappedPath = os.path.join(localDir, relPath)
        verbosePrint(" mapped path: "+mappedPath)

        if mdToHtmlMap and mappedPath.endswith(".md"):
            raise FileNotFoundError

        if mdToHtmlMap and mappedPath.endswith(".html"):
            mappedPath = mappedPath[:-5] + ".md"

        found = os.path.isdir(mappedPath) or os.path.isfile(mappedPath)

        if not found:
            raise FileNotFoundError

        if checkAnchor and len(uriFragment) > 0:
            if os.path.isdir(mappedPath):
                raise AnchorNotFoundError(f"'{mappedPath}' is a directory")
            if mappedPath.endswith(".md") and uriFragment not in collectAnchors(mappedPath):
                raise AnchorNotFoundError(f"Anchor '{uriFragment}' not found in file '{mappedPath}'")

        return True
    else:
        return False

def checkExternalLink(uriPath, uriFragment):
    if maybeCheckExternalLinkWithRemap(uriPath, g_stdlibLinkPrefix, g_stdlibDir, True):
        pass
    elif maybeCheckExternalLinkWithRemap(uriPath, g_slangPrefix, g_slangDir, True, uriFragment, True):
        pass
    elif maybeCheckExternalLinkWithRemap(uriPath, g_slangPrefixGhDir, g_slangDir, False):
        pass
    elif maybeCheckExternalLinkWithRemap(uriPath, g_slangSpecPrefixGhDir, g_slangSpecDir, False, uriFragment, True):
        pass
    elif maybeCheckExternalLinkWithRemap(uriPath, g_slangSpecPrefixGhFile, g_slangSpecDir, False, uriFragment, True):
        pass
    elif uriPath.startswith("https://en.wikipedia.org/"):
        pass
    elif uriPath.startswith("https://doi.org/"):
        pass
    elif uriPath.startswith("https://github.com/shader-slang/slang/issues/"):
        pass
    elif uriPath.startswith("https://www.ietf.org/"):
        pass
    elif uriPath.startswith("https://docs.vulkan.org/"):
        pass
    elif uriPath.startswith("https://registry.khronos.org/"):
        pass
    elif uriPath.startswith("https://en.cppreference.com/"):
        pass
    else:
        raise FileNotFoundError


def checkMarkDownLinks(srcFile):
    errors = 0

    verbosePrint(f"Collecting links: {srcFile}")

    with open(srcFile) as file1:
        lineNo = 0
        for line in markdownLinesWithoutCode(file1):
            lineNo = lineNo + 1
            for m in itertools.chain(linkMatcherMarkDown.finditer(line), linkMatcherHref.finditer(line)):
                linkDstFile = m.group(1)
                linkDstAnchor = m.group(2)
                verbosePrintNoNewline(f"- {linkDstFile} {linkDstAnchor}:")

                try:
                    if linkDstFile.startswith("https://"):
                        checkExternalLink(linkDstFile, linkDstAnchor)
                        continue

                    if len(linkDstFile) == 0:
                        dstFile = srcFile
                    else:
                        dstFile = os.path.join(os.path.dirname(srcFile), linkDstFile)

                    if os.path.isdir(dstFile):
                        if len(linkDstAnchor) > 0:
                            raise AnchorNotFoundError(f"'{dstFile}' is a directory")
                        verbosePrint("OK")
                        continue

                    if len(linkDstAnchor) > 0:
                        verbosePrint("")
                        if linkDstAnchor not in collectAnchors(dstFile):
                            raise AnchorNotFoundError(f"Anchor '{linkDstAnchor}' not found in file '{dstFile}'")
                    elif not os.path.isfile(dstFile):
                        raise FileNotFoundError

                except FileNotFoundError:
                    errors = errors + 1
                    print(f"{srcFile}:{lineNo}: Link destination file {linkDstFile} not found!")
                    continue

                except AnchorNotFoundError as ex:
                    errors = errors + 1
                    print(f"{srcFile}:{lineNo}: Link destination file {linkDstFile} does not define anchor {linkDstAnchor}")
                    warning(str(ex))
                    continue

                verbosePrint("OK")

    return errors

def main(argv):
    global g_verbose
    global g_slangDir
    global g_stdlibDir

    # parse options
    while len(argv) > 0:
        if argv[0] == '-v':
            g_verbose = True
            argv = argv[1:]
            continue

        if argv[0] == '-slang-dir' and len(argv) >= 2:
            g_slangDir = argv[1]
            argv = argv[2:]
            continue

        if argv[0] == '-stdlib-ref-dir' and len(argv) >= 2:
            g_stdlibDir = argv[1]
            argv = argv[2:]
            continue

        break

    if len(argv) == 0:
        printHelpAndExit()

    if g_stdlibDir is None:
        g_stdlibDir = getDefaultStandardLibraryReferenceDir()

    if g_slangDir is None:
        g_slangDir = getDefaultSlangDir()

    if not os.path.isdir(g_stdlibDir):
        error(f"Slang standard library reference path '{g_stdlibDir}' is not a directory")

    if not os.path.isdir(g_slangDir):
        error(f"Slang repository path '{g_slangDir}' is not a directory")

    errors = 0
    for f in argv:
        errors += checkDuplicateAnchors(f)
        errors += checkMarkDownLinks(f)

    print(f"Encountered {errors} errors")

    sys.exit(1 if errors > 0 else 0)

if __name__ == "__main__":
    main(sys.argv[1:])
