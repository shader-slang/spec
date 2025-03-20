import jinja2 as jinja
import lark
import re
import markdown as md

rootSourceFilePath = "./index.md"

# spec nodes

class PreBlock(md.Block):
    tag = "pre"
    classAttribute = "lexical grammar"

class MetaNode(md.InlineElement):
    classAttribute = "meta"
    pass

class MetaVariable(md.Variable):
    classAttribute = "meta"
    pass

class MetaValue(MetaNode):
    pass

class MetaTypeNode(MetaValue):
    pass

class MetaTerminal(md.InlineElement):
    classAttribute = "meta terminal"

class GrammarNode(md.InlineElement):
    classAttribute = "grammar"

class GrammarOp(GrammarNode):
    pass

class GrammarOrExpr(GrammarNode):
    contentSeparator = " | "

class GrammarDiffExpr(GrammarNode):
    contentSeparator = " - "

class GrammarCharacterClass(GrammarNode):
    classAttribute = "character-class"
    preTemplate = "["
    postTemplate = "]"

class GrammarCharacterClassRange(GrammarNode):
    pass

class GrammarCharacterClassCharacter(GrammarCharacterClassRange):
    classAttribute = "character"
    pass

class GrammarCharacterClassCharacterRange(GrammarCharacterClassRange):
    classAttribute = "character-range"
    contentSeparator = "-"
    pass

class GrammarZeroOrMore(GrammarNode):
    postTemplate = "*"

class GrammarOneOrMore(GrammarNode):
    postTemplate = "+"

class GrammarOptional(GrammarNode):
    postTemplate = "?"

class GrammarProduction(md.Block):
    classAttribute = "grammar production"
    contentSeparator = "\n"

class GrammarVariableIntroducer(GrammarNode):
    classAttribute = "introducer"
    contentSeparator = ":"

class GrammarAlternative(GrammarNode):
    classAttribute = "alternative"
    contentSeparator = " "
    preTemplate = "⇒ "

class GrammarAlternativeList(md.Sequence):
    contentSeparator = "\n"

class GrammarSequence(GrammarNode):
    classAttribute = "sequence"
    contentSeparator = " "

class GrammarBlockComment(GrammarNode):
    classAttribute = "block-comment"

class GrammarParenthesizedExpression(GrammarNode):
    preTemplate = "("
    postTemplate = ")"

def createMetaNode(node):
    text = md.getText(node)
    if len(text) == 1 or text[0].islower():
        return MetaVariable(node.children)
    return MetaValue(node.children)

def maybeCreateMetaNode(node):
    if node.delimiter == "_":
        return createMetaNode(node)
    return node.children

class IdentifySpecNodesTransform(md.Transform):
    def __init__(self):
        super().__init__()

    def visitStrong(self, node):
        node = maybeCreateMetaNode(node)
        return md.Definition(node)

    def visitEmphasis(self, node):
        node = maybeCreateMetaNode(node)
        return md.Reference(node)

    def visitCodeSpan(self, node):
        text = md.getText(node)
        match = re.match(r"^\$(.*)$", text)
        if not match:
            return
        
        newText = match[1]
        return MetaTerminal(newText)


grammarRulesParser = lark.Lark(r"""

start: NEWLINE* production*

production: nonterminal allow_newline alternatives NEWLINE*

?alternatives: new_style_alternatives | old_style_alternatives

?new_style_alternatives: alternative+

?old_style_alternatives: old_style_definer allow_newline old_style_alternatives_list (allow_newline ";")?

old_style_alternatives_list: "|"? old_style_alternative old_style_alterantives_list_next*

?old_style_alterantives_list_next: allow_newline "|" old_style_alternative

?old_style_definer: ":" | ":=" | "=" |

old_style_alternative: sequence_expression

alternative: "=>" allow_newline sequence_expression allow_newline

!allow_newline: NEWLINE?

?or_expression: sequence_expression ("|" sequence_expression)*

?sequence_expression: sub_expression+

?sub_expression: postfix_expression ("-" postfix_expression)?

?postfix_expression: simple_expression | star_expression | plus_expression | question_expression

?simple_expression: term

star_expression: postfix_expression "*" allow_newline

plus_expression: postfix_expression "+" allow_newline

question_expression: postfix_expression "?" allow_newline

?term: nonterminal | variable_introducer | terminal | parenthesized_expression | character_class | block_comment

parenthesized_expression: "(" or_expression ")"

character_class: "[" character_class_content "]"

character_class_content: character_class_range+

?character_class_range: character_class_character | character_class_character_range

character_class_character: /[^\\\]]/

character_class_character_range: character_class_character "-" character_class_character

variable_introducer: variable ":" nonterminal

nonterminal: /[A-Z][a-zA-Z0-9_]*/ NEWLINE?

variable: /[a-z][a-zA-Z0-9_]*/ NEWLINE?

terminal: BACKQUOTED_TERMINAL NEWLINE? | SINGLE_QUOTED_TERMINAL NEWLINE? | DOUBLE_QUOTED_TERMINAL NEWLINE?

BACKQUOTED_TERMINAL: /`[^`]+`/

SINGLE_QUOTED_TERMINAL: /'[^\']+'/

DOUBLE_QUOTED_TERMINAL: /"[^\"]*"/

LINE_COMMENT: /\/\/[^\n]*/

block_comment: /\/\*[\s\S]*?\*\//

NEWLINE: /\n/ | /\r/ | /\r\n/

%ignore /[ \t]+/ | LINE_COMMENT

""", start='start')

class GrammarTransformer(lark.Transformer):

    def start(self, node):
        #print("start: {0}".format(node))
        return node

    def production(self, node):
        #print("production: {0}".format(node))
        definition = md.Definition([node[0]])
        alternatives = GrammarAlternativeList(node[2])
        return GrammarProduction([definition, alternatives])

    def new_style_alternatives(self, node):
        #print("new_style_alternatives: {0}".format(node))
        return node

    def old_style_alternatives(self, node):
        #print("old_style_alternatives: {0}".format(node))
        return node[2]

    def old_style_alternatives_list(self, node):
        #print("old_style_alternatives_list: {0}".format(node))
        return node

    def old_style_alterantives_list_next(self, node):
        #print("old_style_alterantives_list_next: {0}".format(node))
        return node[1]

    def old_style_alternative(self, node):
        #print("old_style_alternative: {0}".format(node))
        return GrammarAlternative([node[0]])

    def alternative(self, node):
        #print("alternative: {0}".format(node))
        return GrammarAlternative([node[1]])

    def or_expression(self, node):
        #print("or_expression: {0}".format(node))
        return GrammarOrExpr(node)

    def sub_expression(self, node):
        #print("sub_expression: {0}".format(node))
        return GrammarDiffExpr([node[0], node[1]])

    def star_expression(self, node):
        #print("star_expression: {0}".format(node))
        return GrammarZeroOrMore(node[0])

    def plus_expression(self, node):
        #print("plus_expression: {0}".format(node))
        return GrammarOneOrMore(node[0])

    def question_expression(self, node):
        #print("question_expression: {0}".format(node))
        return GrammarOptional(node[0])

    def sequence_expression(self, node):
        #print("sequence_expression: {0}".format(node))
        return GrammarSequence(node)

    def variable_introducer(self, node):
        #print("variable_introducer: {0}".format(node))
        return GrammarVariableIntroducer([node[0], node[1]])

    def variable(self, node):
        #print("variable: {0}".format(node))
        return MetaValue(md.TextElement(node[0].value))

    def nonterminal(self, node):
        #print("nonterminal: {0}".format(node))
        return MetaTypeNode(md.TextElement(node[0].value))
    
    def terminal(self, node):
        #print("terminal: {0}".format(node))
        rawText = node[0].value
        text = rawText[1:-1]
        return md.CodeSpan(md.TextElement(text))

    def character_class(self, node):
        #print("character_class: {0}".format(node))
        return GrammarCharacterClass(node)

    def character_class_content(self, node):
        #print("character_class_content: {0}".format(node))
        return node

    def character_class_range(self, node):
        #print("character_class_range: {0}".format(node))
        return GrammarCharacterClassRange(node)

    def character_class_character(self, node):
        #print("character_class_character: {0}".format(node))
        return GrammarCharacterClassCharacter(md.TextElement(node[0].value))

    def character_class_character_range(self, node):
        #print("character_class_character_range: {0}".format(node))
        return GrammarCharacterClassCharacterRange(node)

    def block_comment(self, node):
        #print("block_comment: {0}".format(node))
        return GrammarBlockComment(md.TextElement(node[0].value))

    def parenthesized_expression(self, node):
        #print("parenthesized_expression: {0}".format(node))
        return GrammarParenthesizedExpression(node)

class ProcessGrammarRulesTransform(md.Transform):
    def visitGrammarCallout(self, node):
        codeBlock = md.findChild(node, md.CodeBlock)
        if codeBlock is None:
            return

        rawCode = md.getText(codeBlock)
        #print("rawCode: {0}".format(rawCode))
        try:
            parsed = grammarRulesParser.parse(rawCode)
        except Exception as e:
            md.diagnose(codeBlock, md.Error, "{0}", e)
            return

        converted = GrammarTransformer().transform(parsed)
        converted = PreBlock(converted)

        #print("converted: {0}".format(converted.dump()))

        node.children = [converted if child == codeBlock else child for child in node.children]

def processGrammarRules(node):
    md.transformTree(node, ProcessGrammarRulesTransform())

class IdentitySectionIDsTransform(md.Transform):
    def visitSection(self, node):
        heading = node.heading

        if len(heading.children) == 0:
            return
        lastChild = heading.children[-1]

        if not isinstance(lastChild, md.TextElement):
            return
        text = md.getText(lastChild)

        match = re.match(r"^((.*[^ ]+)?)[ ]+\[(.*)\]$", text)
        if not match:
            return

        remainingText = match.group(1).strip()
        lastChild.text = remainingText
        if remainingText == "":
            heading.children = heading.children[:-1]

        node.heading.id = "sec." + match.group(3)
        return node

class IdentityOldStyleCalloutsTransform(md.Transform):
    def visitCodeBlock(self, node):
        if not node.language:
            return
        
        language = node.language
        #print("language: {0}".format(language))

        if language == ".lexical":
            node.language = None
            return md.LexicalCallout(node)

        if language == ".syntax":
            node.language = None
            return md.SyntaxCallout(node)

        if language == ".semantics":
            node.language = None
            return md.SemanticsCallout(node)

        if language == ".issue":
            node.language = None
            return md.IssueCallout(node)

class CombineSpecialSpansTransform(md.Transform):

    def _isSpecialSpan(self, node):
        if isinstance(node, md.Reference):
            node = node.children[0]
        if isinstance(node, md.Definition):
            node = node.children[0]

        if isinstance(node, md.CodeSpan): return True
        if isinstance(node, MetaVariable): return True
        return False

    def _createCombinedSpecialSpan(self, spans):
        if len(spans) == 1:
            return spans[0]

        if any(isinstance(span, md.CodeSpan) for span in spans):
            newChildren = []
            for span in spans:
                if isinstance(span, md.CodeSpan):
                    newChildren.extend(span.children)
                else:
                    newChildren.append(span)
            return md.CodeSpan(newChildren)

        # raise Exception("Unknown special span: {0}".format(spans))
        return None

    def __init__(self):
        super().__init__()
        self._newChildren = []
        self._specialSpans = []
        self._whitespaceSpans = []

    def _flushSpecialSpans(self):
        if len(self._specialSpans) > 0:
            newSpan = self._createCombinedSpecialSpan(self._specialSpans)
            if newSpan is not None:
                self._newChildren.append(newSpan)
            else:
                self._newChildren.extend(self._specialSpans)
            self._specialSpans = []

    def _flushWhitespaceSpans(self):
        if len(self._specialSpans) > 0:
            self._specialSpans.extend(self._whitespaceSpans)
        else:
            self._newChildren.extend(self._whitespaceSpans)
        self._whitespaceSpans = []

    def visitParagraph(self, node):
        self._newChildren = []
        self._specialSpans = []
        self._whitespaceSpans = []
        for child in node.children:
            if md.getText(child).isspace():
                self._whitespaceSpans.append(child)
                continue

            if not self._isSpecialSpan(child):
                self._flushSpecialSpans()
                self._flushWhitespaceSpans()
                self._newChildren.append(child)
                continue

            self._flushWhitespaceSpans()
            self._specialSpans.append(child)

        self._flushSpecialSpans()
        self._flushWhitespaceSpans()

        node.children = self._newChildren
        return node

# NFA for lexical grammar
class LexicalGrammar():
    class Expr():
        pass

    class Nothing(Expr):
        pass

    class Terminal(Expr):
        def __init__(self, name):
            super().__init__()
            self.name = name

    class Range(Expr):
        def __init__(self, lo, hi):
            super().__init__()
            self.lo = lo
            self.hi = hi

    class Diff(Expr):
        def __init__(self, left, right):
            super().__init__()
            self.left = left
            self.right = right

    class Or(Expr):
        def __init__(self, alternatives):
            super().__init__()
            self.alternatives = alternatives

    class Seq(Expr):
        def __init__(self, exprs):
            super().__init__()
            self.exprs = exprs

    class OneOrMore(Expr):
        def __init__(self, inner):
            super().__init__()
            self.inner = inner

    def Optional(self, inner):
        return self.Or([inner, self.Nothing()])

    def ZeroOrMore(self, inner):
        return self.Optional(self.OneOrMore(inner))

    class Nonterminal(Expr):
        def __init__(self, name):
            self.name = name
            self.definition = None

        def setDefinition(self, definition):
            if self.definition is not None:
                raise Exception("duplicate definition for nonterminal")
            self.definition = definition

    def __init__(self):
        self.nonterminals = {}
        pass
    
    def getNonterminal(self, name):
        if name in self.nonterminals:
            return self.nonterminals[name]
        
        nonterminal = self.Nonterminal(name)
        self.nonterminals[name] = nonterminal
        return nonterminal

class CollectLexicalGrammarProductionsTransform(md.Transform):
    def __init__(self, lexicalGrammar):
        self.lexicalGrammar = lexicalGrammar

    def translateCodeSpan(self, node):
        name = md.getText(node)
        return self.lexicalGrammar.Terminal(name)

    def translateMetaTypeNode(self, node):
        name = md.getText(node)
        return self.lexicalGrammar.getNonterminal(name)

    def translateGrammarOptional(self, node):
        inner = self.translateExpr(node.children[0])
        return self.lexicalGrammar.Optional(inner)

    def translateGrammarOneOrMore(self, node):
        inner = self.translateExpr(node.children[0])
        return self.lexicalGrammar.OneOrMore(inner)

    def translateGrammarZeroOrMore(self, node):
        inner = self.translateExpr(node.children[0])
        return self.lexicalGrammar.ZeroOrMore(inner)

    def translateGrammarParenthesizedExpression(self, node):
        inner = self.translateExpr(node.children[0])
        return inner

    def translateGrammarSequence(self, node):
        translatedAlternatives = [self.translateExpr(a) for a in node.children]
        if len(translatedAlternatives) == 0:
            return self.lexicalGramar.Nothing()
        if len(translatedAlternatives) == 1:
            return translatedAlternatives[0]        
        return self.lexicalGrammar.Seq(translatedAlternatives)

    def translateGrammarOrExpr(self, node):
        return self.translateAlternatives(node.children)

    def translateGrammarAlternative(self, node):
        return self.translateExpr(node.children[0])

    def translateGrammarCharacterClass(self, node):
        return self.translateAlternatives(node.children)

    def translateGrammarCharacterClassCharacterRange(self, node):
        left = self.translateExpr(node.children[0])
        right = self.translateExpr(node.children[1])
        return self.lexicalGrammar.Range(left, right)

    def translateGrammarDiffExpr(self, node):
        left = self.translateExpr(node.children[0])
        right = self.translateExpr(node.children[1])
        return self.lexicalGrammar.Diff(left, right)

    def translateGrammarCharacterClassCharacter(self, node):
        text = md.getText(node)
        return self.lexicalGrammar.Terminal(text)

    def translateGrammarAlternativeList(self, node):
        return self.translateAlternatives(node.children)

    def translateExpr(self, node):
        className = node.__class__.__name__
        methodName = "translate" + className
        method = getattr(self, methodName)
        return method(node)

    def translateAlternatives(self, alternatives):
        translatedAlternatives = [self.translateExpr(a) for a in alternatives]
        if len(translatedAlternatives) == 0:
            return self.lexicalGramar.Nothing()
        if len(translatedAlternatives) == 1:
            return translatedAlternatives[0]        
        return self.lexicalGrammar.Or(translatedAlternatives)

    def visitGrammarProduction(self, node):

        nonterminalBeingDefined = node.children[0]
        nonterminalName = md.getText(nonterminalBeingDefined)
        nonterminal = self.lexicalGrammar.getNonterminal(nonterminalName);

        definition = self.translateExpr(node.children[1])

        nonterminal.setDefinition(definition)

        print("found: ", nonterminalName)

class CollectLexicalGrammarTransform(md.Transform):
    def __init__(self):
        self.lexicalGrammar = LexicalGrammar()

    def visitLexicalCallout(self, node):
        md.transformTree(node,
            CollectLexicalGrammarProductionsTransform(self.lexicalGrammar))

def collectLexicalGrammar(node):
    transform = CollectLexicalGrammarTransform()
    md.transformTree(node, transform)

    lg = transform.lexicalGrammar

    for nt in lg.nonterminals.values():
        if nt.definition is None:
            print("nonterminal {0} does not have a definition".format(nt.name))

    # TODO: tag important nonterminals where the terminals that
    # are their alternatives should be treated as distinct
    # lexemes, because the abstract syntax will refer to them
    # as such:
    #
    # Operator, Punctuation


    # TODO: confirm that the lexical grammar can be represented
    # as an NFA (basically: it can't have rules that contain themselves)

    # TODO: actually translate to a proper NFA, then to a DFA,
    # so that we can generate a reference lexer

    return lg

def transformRootDocument(node):
    node = md.transformTree(node, md.CollectRootDocumentSectionsTransform())
    md.includeChapters(node)
    node = md.transformTree(node, IdentifySpecNodesTransform())

    md.transformTree(node, IdentitySectionIDsTransform())

    md.identifyCallouts(node)

    md.transformTree(node, IdentityOldStyleCalloutsTransform())

    md.transformTree(node, CombineSpecialSpansTransform())

    processGrammarRules(node)

    # TODO:
    # assign IDs to definitions
    # link references to their definitions
    # introduce self-link anchors for nodes with IDs
    # merge consecutive paragraphs that should span a code block, algorithm, etc.
    # section numbering
    # convert all grammar blocks to new syntax (and then clean up grammar for grammars...)

    lexicalGramar = collectLexicalGrammar(node)

    md.generateSectionIDs(node)
    node = md.transformTree(node, md.BuildTableOfContentsTransform(node))
    return node



def parseRootSourceFile(filepath):
    rootNode = md.readMarkdownFile(filepath)
    document = transformRootDocument(rootNode)
    return document

rootDocument = parseRootSourceFile(rootSourceFilePath)

renderer = md.Renderer()
titleHTML = renderer.render(rootDocument.title)
contentHTML = renderer.render(rootDocument)

jinjaEnv = jinja.Environment(loader=jinja.FileSystemLoader("."))
template = jinjaEnv.get_template("templates/index.html")

outputHTML = template.render(title=titleHTML, content=contentHTML)

with open("index.html", "w", encoding="utf-8") as file:
    file.write(outputHTML)
