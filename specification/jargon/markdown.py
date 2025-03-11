import mistletoe
import re

class DiagnosticSeverity:
    def __init__(self, name, level):
        self.name = name
        self.level = level

Trace = DiagnosticSeverity("trace", 0)
Note = DiagnosticSeverity("note", 1)
Warning = DiagnosticSeverity("warning", 2)
Error = DiagnosticSeverity("error", 3)
Fatal = DiagnosticSeverity("fatal", 4)

diagnosticLevel = Note
fatalLevel = Error

def getDiagnosticLocation(obj):
    if object is None:
        return "unknown"
    if isinstance(obj, str):
        return obj
    if isinstance(obj, Element):
        if hasattr(obj, "range"):
            range = obj.range
            if range is not None:
                obj = range
    if isinstance(obj, SourceRange):
        obj = obj.startLoc
    if isinstance(obj, SourceLoc):
        if obj.file is None:
            return "unknown"
        if obj.line is None:
            return obj.file
        return "{0}({1})".format(obj.file, obj.line)

    return obj.__class__.__name__

def diagnose(node, severity, message, *args, **kwargs):
    if severity.level < diagnosticLevel.level:
        return

    location = getDiagnosticLocation(node)
    message = message.format(*args, **kwargs)
    print("{0}: {1}: {2}".format(severity.name, location, message))

    if severity.level >= fatalLevel.level:
        exit(1)


def applyTransform(node, transform):
    if callable(transform):
        return transform(node)

    for base in node.__class__.mro():
        baseName = base.__name__
        methodName = "visit" + baseName
        if hasattr(transform, methodName):
            method = getattr(transform, methodName)
            return method(node)

def transformTree(node, transform):
    if node is None:
        return

    #print("transforming {0}".format(node))

    possibleNewNodeOrNodes = applyTransform(node, transform)

    if possibleNewNodeOrNodes is None or possibleNewNodeOrNodes == node:
        transformChildren(node, transform)
        return node

    if not isinstance(possibleNewNodeOrNodes, list):
        return transformTree(possibleNewNodeOrNodes, transform)

    transformedNewNodes = [transformTree(newNode, transform) for newNode in possibleNewNodeOrNodes]
    return transformedNewNodes    
    
def transformChildren(node, transform):
    if isinstance(node, TextElement):
        return

    newChildren = []
    for i in range(len(node.children)):
        oldChild = node.children[i]
        newChildOrChildren = transformTree(oldChild, transform)

        if isinstance(newChildOrChildren, list):
            newChildren.extend(newChildOrChildren)
        else:
            newChildren.append(newChildOrChildren)

    node.children = newChildren

class SourceLoc:
    def __init__(self, file=None, line=None, col=None):
        self.file = file
        self.line = line
        self.col = col

class SourceRange:
    def __init__(self, startLoc=None, endLoc=None):
        self.startLoc = startLoc
        self.endLoc = endLoc

class Node:
    def __init__(self, range=None):
        self.range = range

    def dump(self):
        return self.__class__.__name__

class TextElement(Node):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.text = text

    def __repr__(self):
        return self.text.__repr__()

    def getText(self):
        return self.text

    def dump(self):
        return self.text.__repr__()

def _enumerateChildren(obj):
    if isinstance(obj, Node):
        yield obj
        return

    if isinstance(obj, list):
        for item in obj:
            yield from _enumerateChildren(item)
        return

    if isinstance(obj, str):
        yield TextElement(obj)
        return

    raise Exception("Invalid object: {0}".format(obj))

def _collectChildren(obj):
    return [child for child in _enumerateChildren(obj)]

class Element(Node):
    contentSeparator = ""
    template = "<{tag}{attributes}>{content}</{tag}>\n"

    def __init__(self, children=[], **kwargs):
        super().__init__(**kwargs)

        children = _collectChildren(children)

        self.children = children
        self.id = None

    def getText(self):
        return self.contentSeparator.join([child.getText() for child in self.children])

    def dump(self):
        def dumpChild(child):
            if isinstance(child, Node):
                return child.dump()
            return child.__repr__()
        
        childrenDump = ", ".join([dumpChild(child) for child in self.children])

        return "{0}({1})".format(self.__class__.__name__, childrenDump)

class Block(Element):
    tag = "div"

class LeafBlock(Block):
    pass

class ThematicBreak(LeafBlock):
    tag = "hr"

class Heading(LeafBlock):
    def __init__(self, children, level=None, **kwargs):
        super().__init__(children, **kwargs)
        self.level = level

    @property
    def tag(self):
        level = self.level
        if level < 1:
            level = 1
        if level > 6:
            level = 6
        return "h{0}".format(level)

class PreBlock(LeafBlock):
    tag = "pre"

class CodeBlock(LeafBlock):
    def __init__(self, children, language=None, **kwargs):
        super().__init__(children, **kwargs)
        self.language = language

class Paragraph(LeafBlock):
    tag = "p"

class ContainerBlock(Block):
    pass

class List(ContainerBlock):
    tag = "ul"

class OrderedList(List):
    tag = "ol"

class UnorderedList(List):
    tag = "ul"

class ListItem(ContainerBlock):
    tag = "li"

class BlockQuote(ContainerBlock):
    tag = "blockquote"

class InlineElement(Element):
    template = "<{tag}{attributes}>{content}</{tag}>"
    tag = "span"

class CodeSpan(InlineElement):
    tag = "code"

class Link(InlineElement):
    tag = "a"
    def __init__(self, children, target=None, **kwargs):
        super().__init__(children, **kwargs)
        self.target = target

class Strong(InlineElement):
    tag = "strong"
    def __init__(self, children, delimiter=None, **kwargs):
        super().__init__(children, **kwargs)
        self.delimiter = delimiter

class Emphasis(InlineElement):
    tag = "em"
    def __init__(self, children, delimiter=None, **kwargs):
        super().__init__(children, **kwargs)
        self.delimiter = delimiter

class LineBreak(InlineElement):
    tag = "br"
    template = "<{tag}{attributes}>"

class ThematicBreak(InlineElement):
    tag = "hr"
    template = "<{tag}{attributes}>"

class EscapeSequence(InlineElement):
    tag = None
    template = "{content}"

# Custom Elements

class Nav(ContainerBlock):
    tag = "nav"

class Sequence(ContainerBlock):
    tag = None
    template = "{content}"

class Section(Sequence):
    @property
    def heading(self):
        return self.children[0]

    @property
    def title(self):
        return self.heading.children

class Document(Sequence):
    pass

class TitleHeading(Heading):
    classAttribute = "title-heading"
    def __init__(self, content):
        super().__init__(content, level=0)

class Definition(InlineElement):
    tag = "dfn"

class Reference(InlineElement):
    tag = "a"

class Variable(InlineElement):
    tag = "var"

class TableOfContents(ContainerBlock):
    classAttribute = "toc"

class Callout(ContainerBlock):
    classAttribute = "callout"
    pass

class NoteCallout(Callout):
    classAttribute = "note"
    title = "Note"

class GrammarCallout(Callout):
    classAttribute = "grammar"
    title = "Grammar"

class LexicalCallout(GrammarCallout):
    classAttribute = "lexical"
    title = "Lexical"

class SyntaxCallout(GrammarCallout):
    classAttribute = "syntax"
    title = "Syntax"

class SemanticsCallout(GrammarCallout):
    classAttribute = "semantics"
    title = "Semantics"

class IssueCallout(Callout):
    classAttribute = "issue"
    title = "Issue"

class ToDoCallout(Callout):
    classAttribute = "issue"
    title = "TODO"

def getText(node):
    if node is None:
        return ""
    if isinstance(node, list):
        return "".join([getText(child) for child in node])
    return node.getText()

# convert the mistletoe nodes to our custom elements

class Converter:
    def __init__(self):
        pass

    def convertDocument(self, node, children):
        return Document(children)

    def convertSetextHeading(self, node, children):
        return Heading(children, node.level)

    def convertHeading(self, node, children):
        return Heading(children, node.level)

    def convertParagraph(self, node, children):
        return Paragraph(children)

    def convertBlockCode(self, node, children):
        return CodeBlock(children, node.language)

    def convertCodeFence(self, node, children):
        return CodeBlock(children, node.language)

    def convertCodeSpan(self, node, children):
        return CodeSpan(children)

    def convertList(self, node, children):
        return List(children)

    def convertListItem(self, node, children):
        return ListItem(children)

    def convertRawText(self, node):
        return TextElement(node.content)

    def convertEscapeSequence(self, node, children):
        return EscapeSequence(children)

    def convertLink(self, node, children):
        return Link(children, node.target)

    def convertInlineCode(self, node, children):
        return CodeSpan(children)

    def convertStrong(self, node, children):
        return Strong(children, node.delimiter)

    def convertEmphasis(self, node, children):
        return Emphasis(children, node.delimiter)

    def convertQuote(self, node, children):
        return BlockQuote(children)

    def convertLineBreak(self, node):
        return TextElement("\n")

    def convertThematicBreak(self, node):
        return ThematicBreak()




def convertMistletoeNodeToCustomElement(path, inputNode, converter):
    methodName = "convert" + inputNode.__class__.__name__
    method = getattr(converter, methodName)

    outputNode = None
    if inputNode.children is not None:
        outputChildren = [convertMistletoeNodeToCustomElement(path, child, converter) for child in inputNode.children]
        outputNode = method(inputNode, outputChildren)
    else:
        outputNode = method(inputNode)

    if hasattr(inputNode, "line_number"):
        line = inputNode.line_number
        if line is not None:
            loc = SourceLoc(path, line)
            outputNode.range = loc    

    return outputNode

def readMarkdownFile(filepath):
    with open(filepath, "r") as file:
        content = file.read()
        document = mistletoe.Document(content)
        converted = convertMistletoeNodeToCustomElement(filepath, document, Converter())
        return converted


class Renderer:
    def __init__(self):
        pass

    def render(self, node, contentSeparator=""):
        if node is None:
            return ""
        
        if isinstance(node, list):
            return contentSeparator.join([self.render(child, contentSeparator) for child in node])

        for base in node.__class__.mro():
            baseName = base.__name__
            methodName = "render" + baseName
            if hasattr(self, methodName):
                method = getattr(self, methodName)
                return method(node)

        raise Exception("No render method found for node: " + node.__class__.__name__)

    def renderTextElement(self, node):
        # TODO: escape the text
        return node.getText()

    def renderAttributes(self, node):
        attributes = ""

        if node.id is not None:
            attributes += " id=\"{0}\"".format(node.id)

        classAttributeKey = "classAttribute"
        classes = []
        for base in node.__class__.mro():
            if classAttributeKey in base.__dict__:
                classes.append(base.__dict__[classAttributeKey])

        if len(classes) > 0:
            classAttributeValue = " ".join(classes)
            attributes += " class=\"{0}\"".format(classAttributeValue)

        return attributes

#    def renderGrammarCharacterClassCharacterRange(self, node):
#        print("renderGrammarCharacterClassCharacterRange: {0}".format(node))
#        text = self.renderElement(node)
#        print("text: {0}".format(text))
#        return text

    def renderElement(self, node):
        tag = node.tag
        attributes = self.renderAttributes(node)
        content = self.render(node.children, node.contentSeparator)

        # TODO: add an explicit pass to insert these self-anchors
        if node.id is not None:
            content = "<a href=\"#{0}\" class=\"anchor\">{1}</a>".format(node.id, content)

        result = node.template.format(tag=tag, attributes=attributes, content=content)

        if hasattr(node.__class__, "preTemplate"):
            result = node.__class__.preTemplate + result
        if hasattr(node.__class__, "postTemplate"):
            result = result + node.__class__.postTemplate


        return result

    def renderCodeBlock(self, node):
        return "<pre><code class=\"language-{0}\">{1}</code></pre>\n".format(node.language, self.render(node.children))

    def renderCodeSpan(self, node):
        return "<code>{0}</code>".format(self.render(node.children))

    def renderLink(self, node):
        return "<a href=\"{0}\">{1}</a>".format(node.target, self.render(node.children))

class Transform:
    def __init__(self):
        pass

def collectSectionChildren(inputNodeList, outputNodeList, startIndex, inputHeadingLevel, outputHeadingLevel):
    index = startIndex
    while index < len(inputNodeList):
        child = inputNodeList[index]
        if not isinstance(child, Heading):
            outputNodeList.append(child)
            index += 1
            continue

        if child.level < inputHeadingLevel:
            return index
        
        if child.level != inputHeadingLevel:
            diagnose(child, Warning, "heading level jumped from {0} to {1}", inputHeadingLevel, child.level)
            inputHeadingLevel = child.level

        child.level = outputHeadingLevel
        subSectionChildren = [child]
        index = collectSectionChildren(inputNodeList, subSectionChildren, index + 1, inputHeadingLevel + 1, outputHeadingLevel + 1)

        outputNodeList.append(Section(subSectionChildren))
    return index

class CollectSectionsTransform(Transform):
    def __init__(self, baseHeadingLevel):
        self.section = Section([])
        self.baseHeadingLevel = baseHeadingLevel
        super().__init__()

    def visitTopLevelHeading(self, node):
        node.level = self.baseHeadingLevel
        return node

    def visitDocument(self, node):
        if len(node.children) == 0:
            return

        firstChild = node.children[0]
        if isinstance(firstChild, Heading) and firstChild.level == 1:
            firstChild = self.visitTopLevelHeading(firstChild)
            newChildren = [firstChild]
            collectSectionChildren(node.children, newChildren, 1, 1, self.baseHeadingLevel + 1)
            node = Section(newChildren)
        else:
            newChildren = []
            collectSectionChildren(node.children, newChildren, 0, 1, self.baseHeadingLevel)
            node.children = newChildren

        return node

class CollectRootDocumentSectionsTransform(CollectSectionsTransform):
    def __init__(self):
        super().__init__(0)

    def visitTopLevelHeading(self, node):
        return TitleHeading(node.children)

class CollectChapterPathsTransform(Transform):
    def __init__(self, chapterPaths):
        self.chapterPaths = chapterPaths
        super().__init__()

    def visitLink(self, node):
        self.chapterPaths.append(node.target)

def transformChapterDocument(node):
    node = transformTree(node, CollectSectionsTransform(1))
    return node

def readChapterDocument(chapterPath):
    node = readMarkdownFile(chapterPath)
    node = transformChapterDocument(node)
    return node

def matchesFilter(node, filter):
    if isinstance(filter, type):
        return isinstance(node, filter)
    if callable(filter):
        return filter(node)
    raise Exception("Invalid filter: {0}".format(filter))

def enumerateChildren(node, filter):
    for child in node.children:
        if matchesFilter(child, filter):
            yield child

def findChildren(node, filter):
    return [child for child in enumerateChildren(node, filter)]

def findChild(node, filter):
    found = [child for child in findChildren(node, filter)]
    if len(found) == 0:
        return None
    if len(found) > 1:
        diagnose(node, Warning, "found multiple children that match the filter")
    return found[0]

def isTableOfContentsSection(node):
    if not isinstance(node, Section):
        return False
    if not ("contents" in getText(node.heading).lower()):
        return False
    return True

def findTableOfContentsSection(document):
    return findChild(document, isTableOfContentsSection)

def findTableOfContents(document):
    sections = findChildren(document, isTableOfContentsSection)
    if len(sections) == 0:
        diagnose(document, Warning, "no table of contents section found")
        return None
    if len(sections) > 1:
        diagnose(document, Warning, "found multiple table of contents sections")

    section = sections[0]
    diagnose(section, Trace, "found table of contents section")

    section.__class__ = Nav
    
    #for child in section.children:
    #    print("child: {0}".format(child))

    tableOfContentsListList = findChildren(section, List)
    #for child in tableOfContentsListList:
    #    print("list: {0}".format(child))


    if len(tableOfContentsListList) == 0:
        diagnose(section, Warning, "no table of contents list found in table of contents section")
        return None
    if len(tableOfContentsListList) > 1:
        diagnose(section, Warning, "found multiple table of contents lists in table of contents section")
    
    tableOfContentsList = tableOfContentsListList[0]
    tableOfContents = TableOfContents([tableOfContentsList])

    section.children = [tableOfContents if child == tableOfContentsList else child for child in section.children]

    return tableOfContents

def includeChapters(document):
    tableOfContents = findTableOfContents(document)
    if tableOfContents is None:
        return
    
    chapterPaths = []
    transformTree(tableOfContents, CollectChapterPathsTransform(chapterPaths)) 
    
    chapters = []
    for chapterPath in chapterPaths:
        chapterNode = readChapterDocument(chapterPath)
        document.children.append(chapterNode)

def buildTableOfContentsListEntry(section):
    heading = section.heading

    link = Link(heading.children, "#" + heading.id)
    children = [link]

    items = buildTableOfContentsListItems(section)
    if len(items) > 0:
        children.append(UnorderedList(items))

    return ListItem(children)

def buildTableOfContentsListItems(section):
    result = []
    for node in section.children:
        if isinstance(node, Section):
            result.append(buildTableOfContentsListEntry(node))
    return result


class BuildTableOfContentsTransform(Transform):
    def __init__(self, document):
        self.document = document
        super().__init__()

    def visitTableOfContents(self, node):
        tableOfContentsListItems = buildTableOfContentsListItems(self.document)
        tableOfContentsList = UnorderedList(tableOfContentsListItems)
        #print("tableOfContentsList: {0}".format(tableOfContentsList))
        node.children = [ tableOfContentsList ]

class GenerateSectionIDsTransform(Transform):
    def visitSection(self, node):
        if node.heading.id is not None:
            return

        name = "section " + getText(node.heading.children)
        id = name.lower().replace(" ", "-")
        #print("id: {0}".format(id))
        node.heading.id = id

def generateSectionIDs(document):
    transformTree(document, GenerateSectionIDsTransform())


def getPotentialCalloutHeadingText(node):
    if isinstance(node, Heading):
        return getText(node.children)
    if isinstance(node, Paragraph):
        return getText(node.children)
    return None

calloutClasses = [NoteCallout, LexicalCallout, IssueCallout, ToDoCallout]
calloutClassDictionary = {}
for calloutClass in calloutClasses:
    calloutClassDictionary[calloutClass.title.lower()] = calloutClass


def detectCalloutClass(node):
    potentialHeadingText = getPotentialCalloutHeadingText(node)
    if potentialHeadingText is None:
        return None

    match = re.match(r"([a-zA-Z ]*):|$", potentialHeadingText)
    if match is None:
        return None

    calloutKind = match.group(1).lower()
    #print("found potential callout: {0}".format(calloutKind))

    if calloutKind in calloutClassDictionary:
        return calloutClassDictionary[calloutKind]

    return None

class IdentifyCalloutsTransform(Transform):
    def __init__(self):
        super().__init__()
        self._visited = set()

    def visitParagraph(self, node):
        if node in self._visited:
            return
        self._visited.add(node)

        calloutClass = detectCalloutClass(node)
        if calloutClass is None:
            return

        callout = calloutClass(node.children)
        return callout

    def visitBlockQuote(self, node):
        if len(node.children) == 0:
            return

        # print("visitBlockQuote: {0}".format(node))
        calloutClass = detectCalloutClass(node.children[0])
        if calloutClass is None:
            return

        diagnose(node, Trace, "found callout: {0}", calloutClass.title)

        newText = TextElement(calloutClass.title)

        newHeading = Heading([newText], 6)

        newChildren = [newHeading]
        newChildren.extend(node.children[1:])

        callout = calloutClass(newChildren)
        return callout

def identifyCallouts(document):
    transformTree(document, IdentifyCalloutsTransform())

