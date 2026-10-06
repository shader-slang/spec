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
    global g_verbose

    if g_verbose:
        print(s)

def verbosePrintNoNewline(s):
    global g_verbose

    if g_verbose:
        print(s, end="")

def getDefaultStandardLibraryReferenceDir():
    return os.path.realpath(os.path.join(os.path.dirname(__file__), "../../stdlib-reference"))

def getDefaultSlangDir():
    return os.path.realpath(os.path.join(os.path.dirname(__file__), "../../slang"))

def printHelpAndExit():
    print('''Scans markdown files and checks for broken links

Usage: check-markdown-relative-links.py [options] <files>

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


def scanForAnchor(file, anchorMatchers, filename, anchor):
    for line in file:
        for am in anchorMatchers:
            for m in am.finditer(line):
                verbosePrint(f"  - found anchor {m.group(1)}")
                if anchor == m.group(1):
                    return

    raise NameError(f"Anchor '{anchor}' not found in file '{filename}'")

# returns True if uriPath started with externalUriPrefix and the path
# was found
#
# returns False if uriPath did not start with externalUriPrefix
#
# throws FileNotFoundError if uriPath started with externalUriPrefix
# and the path was not found
def maybeCheckExternalLinkWithRemap(uriPath, externalUriPrefix, localDir, mdToHtmlMap):
    if uriPath.startswith(externalUriPrefix):

        # relative path
        relPath = uriPath[len(externalUriPrefix):]
        if relPath.startswith("/"):
            relPath = relPath[1:]

        mappedPath = os.path.join(localDir, relPath)
        verbosePrint("uri path: " + uriPath + "   mapped path: "+mappedPath)

        if mdToHtmlMap and mappedPath.endswith(".md"):
            raise FileNotFoundError

        if mdToHtmlMap and mappedPath.endswith(".html"):
            mappedPath = mappedPath[:-5] + ".md"

        found = os.path.isdir(mappedPath) or os.path.isfile(mappedPath)

        if not found:
            raise FileNotFoundError

        return True
    else:
        return False

def checkExternalLink(uriPath, uriFragment):
    global g_stdlibDir
    global g_stdlibLinkPrefix
    global g_slangPrefix
    global g_slangPrefixGhDir
    global g_slangDir
    global g_slangSpecPrefixGhDir
    global g_slangSpecPrefixGhFile
    global g_slangSpecDir

    if maybeCheckExternalLinkWithRemap(uriPath, g_stdlibLinkPrefix, g_stdlibDir, True):
        pass
    elif maybeCheckExternalLinkWithRemap(uriPath, g_slangPrefix, g_slangDir, True):
        pass
    elif maybeCheckExternalLinkWithRemap(uriPath, g_slangPrefixGhDir, g_slangDir, False):
        pass
    elif maybeCheckExternalLinkWithRemap(uriPath, g_slangSpecPrefixGhDir, g_slangSpecDir, False):
        pass
    elif maybeCheckExternalLinkWithRemap(uriPath, g_slangSpecPrefixGhFile, g_slangSpecDir, False):
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

    # match:                            [link text........] ((url...)(anchr))
    linkMatcherMarkDown = re.compile(r"\[(?:[^\]\\]|\\.)*\]\(([^)#]*)#?([^)]*)\)")

    # match:                       <a      href="(url...)(anchr)"     >
    linkMatcherHref = re.compile(r'<a [^>]*href="([^"#]*)([^"]*)"[^>]*>')

    # NOTE: we don't use this at the moment, since it's not supported by GitHub markdown viewer
    # match:                                     # title {#(anchor)}
    # anchorMatcherMarkdownSection = re.compile(r"^#.*\{#([^}]+)\}")

    # match:                      <a      id="(anchr)"     >
    anchorMatcherA = re.compile(r'<a [^>]*id="([^"]*)"[^>]*>')

    verbosePrint(f"Collecting links: {srcFile}")

    with open(srcFile) as file1:
        lineNo = 0
        for line in file1:
            lineNo = lineNo + 1
            for m in itertools.chain(linkMatcherMarkDown.finditer(line), linkMatcherHref.finditer(line)):
                linkDstFile = m.group(1)
                linkDstAnchor = m.group(2)
                verbosePrintNoNewline(f"- {linkDstFile} {linkDstAnchor}:")

                try:
                    if linkDstFile.startswith("https://"):
                        verbosePrintNoNewline("external")
                        checkExternalLink(linkDstFile, linkDstAnchor)
                        continue

                    if len(linkDstFile) == 0:
                        dstFile = srcFile
                    else:
                        dstFile = os.path.join(os.path.dirname(srcFile), linkDstFile)

                    with open(dstFile) as file2:
                        if len(linkDstAnchor) > 0:
                            verbosePrint("")
                            scanForAnchor(file2, [ anchorMatcherA ], dstFile, linkDstAnchor)

                except FileNotFoundError:
                    errors = errors + 1
                    print(f"{srcFile}:{lineNo}: Link destination file {linkDstFile} not found!")
                    continue

                except NameError as ex:
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

    # version check -- this script was developed with Python 3.12
    if sys.version_info < (3, 12):
        warning(f"Python version {sys.version_info.major}.{sys.version_info.minor} is not at least 3.12!")

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
            g_stdLibDir = argv[1]
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
        errors += checkMarkDownLinks(f)

    print(f"Encountered {errors} errors")

if __name__ == "__main__":
    main(sys.argv[1:])
