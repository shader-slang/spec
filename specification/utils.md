% utils.tex
%
% This file defines all the utility commands that are needed to prepare the rest of the document.

\setcounter{secnumdepth}{6}


% \DefineVariable : a helper command for defining a getter and setter pair.
%
% Doing `\DefineVariable{Thing}` will allow you to use `\SetThing{...}` to
% set a variable and `\Thing` to access its current value.
%
\makeatletter
\newcommand*\DefineVariable[1]{\@namedef{Set#1}##1{\global\@namedef{#1}{##1}}}
\makeatother
%

\DefineVariable{ChapterLabel}
\DefineVariable{SectionLabel}
\DefineVariable{SubSectionLabel}
\DefineVariable{SubSubSectionLabel}
\DefineVariable{ParagraphLabel}
\DefineVariable{SubParagraphLabel}

\SetChapterLabel{}
\SetSectionLabel{}
\SetSubSectionLabel{}
\SetSubSubSectionLabel{}
\SetParagraphLabel{}
\SetSubParagraphLabel{}

%
\newcommand*{\ChapterPath}{\ChapterLabel}
\newcommand*{\SectionPath}{\ChapterPath.\SectionLabel}
\newcommand*{\SubSectionPath}{\SectionPath.\SubSectionLabel}
\newcommand*{\SubSubSectionPath}{\SubSectionPath.\SubSubSectionLabel}
\newcommand*{\ParagraphPath}{\SubSubSectionPath.\ParagraphLabel}
\newcommand*{\SubParagraphPath}{\ParagraphPath.\SubParagraphLabel}
%
\newcommand*{\HeadingPath}[1]{\texorpdfstring{TEX}{PDF}}
%
\newcommand*{\Chapter}[2]{\SetChapterLabel{#2}\chapter{#1}\label{\ChapterPath}}
\newcommand*{\Section}[2]{\SetSectionLabel{#2}\section{#1}\label{\SectionPath}}
\newcommand*{\SubSection}[2]{\SetSubSectionLabel{#2}\subsection{#1}\label{\SubSectionPath}}
\newcommand*{\SubSubSection}[2]{\SetSubSubSectionLabel{#2}\subsubsection{#1}\label{\SubSubSectionPath}}
\newcommand*{\Paragraph}[2]{\SetParagraphLabel{#2}\paragraph{#1}\label{\ParagraphPath}}
\newcommand*{\SubParagraph}[2]{\SetSubParagraphLabel{#2}\subparagraph{#1}\label{\SubParagraphPath}}
%

\titleformat{\chapter}{\sffamily\huge\bfseries}{\thechapter}{1em}{\sffamily{#1}{\hfill}\mdseries\small{[\ChapterPath]}}

\titleformat{\section}{\sffamily\Large\bfseries}{\thesection}{1em}{\sffamily{#1}{\hfill}\mdseries\small{[\SectionPath]}}

\titleformat{\subsection}{\sffamily\large\bfseries}{\thesubsection}{1em}{\sffamily{#1}{\hfill}\mdseries\small{[\SubSectionPath]}}

\titleformat{\subsubsection}{\sffamily\normalsize\bfseries}{\thesubsubsection}{1em}{\sffamily{#1}{\hfill}\mdseries\small{[\SubSubSectionPath]}}

\titleformat{\paragraph}{\sffamily\normalsize\bfseries}{\theparagraph}{1em}{\sffamily{#1}{\hfill}\mdseries\small{[\ParagraphPath]}}

\titleformat{\subparagraph}{\sffamily\normalsize\bfseries}{\thesubparagraph}{1em}{\sffamily{#1}{\hfill}\mdseries\small{[\SubParagraphPath]}}

%\newcommand*{\Chapter}[2]{\chapter{#1}}
%\newcommand*{\Section}[2]{\section{#1}}
%\newcommand*{\SubSection}[2]{\subsection{#1}}
%\newcommand*{\SubSubSection}[2]{\subsubsection{#1}}
%\newcommand*{\Paragraph}[2]{\paragraph{#1}}
%\newcommand*{\SubParagraph}[2]{\subparagraph{#1}}

\newcommand*{\CalloutStyle}{\sffamily\bfseries}
\newcommand*{\CalloutName}[1]{\text{\CalloutStyle{#1}}}

\newcommand{\DefineCallout}[3]{
    \newtcolorbox{#1}[1][]{breakable,sharp corners, skin=enhancedmiddle jigsaw,parbox=false,
boxrule=0mm,leftrule=1mm,boxsep=0mm,arc=0mm,outer arc=0mm,attach title to upper,
after title={: \\}, coltitle=black,colback=#3,colframe=black, title={#2},
fonttitle=\CalloutStyle,##1}}

\definecolor{DescriptiveCalloutColor}{gray}{0.9}
\definecolor{NormativeCalloutColor}{gray}{0.9}

\DefineCallout{Note}{Note}{DescriptiveCalloutColor}
\DefineCallout{Incomplete}{Incomplete}{DescriptiveCalloutColor}
\DefineCallout{SyntaxCallout}{Syntax}{NormativeCalloutColor}
\DefineCallout{LexicalCallout}{Syntax}{NormativeCalloutColor}
\DefineCallout{Legacy}{Legacy}{NormativeCalloutColor}
\DefineCallout{Rationale}{Rationale}{DescriptiveCalloutColor}
\DefineCallout{Example}{Example}{DescriptiveCalloutColor}
\DefineCallout{Semantics}{Semantics}{NormativeCalloutColor}
\DefineCallout{Checking}{Checking}{NormativeCalloutColor}
\DefineCallout{Description}{Description}{DescriptiveCalloutColor}
\DefineCallout{TODO}{TODO}{DescriptiveCalloutColor}

%
%\definecolor{ListingKeywordColor}{gray}{0.5}
%\definecolor{ListingTypeColor}{gray}{0.5}
%
%\lstdefinelanguage{slang}{
%    classoffset=0,morekeywords={class,func,let,struct},\keywordstyle=\color{ListingKeywordColor},
%    classoffset=1,morekeywords={void,int,float,bool},\keywordstyle=\color{ListingTypeColor},
%    classoffset=0,
%    morecomment=[l]{//},
%    morecomment=[s]{/*}{*/},
%    morestring=[b]",
%}
%
%\lstnew



\definecolor{FREQUENCYCOLOR}{RGB}{0,176,80}
\definecolor{KEYWORDCOLOR}{RGB}{0,32,96}
\definecolor{COMMENTCOLOR}{RGB}{192,0,0}
\definecolor{TYPECOLOR}{RGB}{0,112,192}
\definecolor{KEYWORDARGCOLOR}{RGB}{144,155,170}
\definecolor{PREPROCOLOR}{RGB}{170,64,32}
\definecolor{ATTRCOLOR}{RGB}{0,112,32}

\definecolor{CodeBackgroundColor}{gray}{0.85}

\lstdefinestyle{SlangCodeStyle}{
    basicstyle=\ttfamily\mdseries\upshape,
    classoffset=0,
    morekeywords={once},
    otherkeywords={\#include,\#define,\#undef,\#if,\#ifdef\#ifndef,\#else,\#elif,\#endif,\#error,\#warning,\#line,\#pragma,\#version},
    keywordstyle=\color{PREPROCOLOR}\ttfamily\bfseries\upshape,
    classoffset=1,
    morekeywords={if,else,struct,class,discard,while,for,do,func,let,var,property,break,continue,yield,interface,in,out,inout,ref,take,borrow,module,include,implements,extension,static,return,import,public,internal,private,implementing,this,enum,is,case,typealias,typedef,associatedtype,auto,const,init,get,set,subscript,cbuffer,tbuffer,switch,true,false,default,operator,prefix,postfix,throws,row\_major,column\_major,fwd\_diff,bwd\_diff},
    keywordstyle=\color{KEYWORDCOLOR}\ttfamily\bfseries\upshape,
    classoffset=2,
    morekeywords={@GroupShared},
    keywordstyle=\color{FREQUENCYCOLOR}\ttfamily\mdseries\upshape,
    classoffset=3,
    morekeywords={void,int,float,Int,Float,Unit,bool,Bool,Texture2D,T,S,IFoo,vector,matrix,int3,ConstantBuffer,TextureBuffer,ParameterBlock,String,IFromIntegerLiteral,IFromFloatingPointLiteral,This,RWStructuredBuffer,float4,float4x4,float2,RWTexture2DMS,TextureCubeArray,SamplerState,SamplerComparisonState,StructuredBuffer,IDifferentiable},
    keywordstyle=\color{TYPECOLOR}\ttfamily\mdseries\upshape,
    classoffset=4,
    morekeywords={mutating,Differentiable},
    keywordstyle=\color{ATTRCOLOR}\ttfamily\mdseries\upshape,
    classoffset=0,
    moredelim=[is][\color{KEYWORDARGCOLOR}\ttfamily\mdseries\upshape]{|}{|},
    moredelim=[is][\color{red}\ttfamily\mdseries\upshape]{^}{^},
    morecomment=[l]//,
    commentstyle=\color{COMMENTCOLOR}\ttfamily\mdseries\upshape,
    tabsize=2,
    mathescape=true}

\lstset{
    style=SlangCodeStyle,
    basicstyle=\text\ttfamily\small}

\lstnewenvironment{codeblock}[1][]
    {\lstset{
        style=SlangCodeStyle,
        #1}}
    {}

\newcommand{\InlineCodeStyle}[1]{
    \fboxsep2pt
    \text{\ttfamily\colorbox{CodeBackgroundColor}{#1}}
}

\newcommand{\code}[1]{\InlineCodeStyle{\code{#1}}}

%\newcommand{\code}[1]{\text{\colorbox{CodeBackgroundColor}{\code{#1}}}}
\newcommand{\kw}[1]{\code{#1}}

\newcommand{`{`}{\code{\{}}
\newcommand{`}`}{\code{\}}}

% TODO: should make `\SpecRef` link to the definition point.
\newcommand{\SpecDef}[1]{\text{\emph{#1}}}
\newcommand{\SpecRef}[1]{#1}
\newcommand{\SpecDefine}[1]{\SpecDef{#1}}

\newcommand{\SynDefine}[1]{\label{syntax:#1}\text{\emph{#1} ::=}}
\newcommand{\SynRef}[1]{\hyperref[syntax:#1]{\text{\emph{#1}}}}
\newcommand{|}{\text{ $\vert$ }}
\newcommand{*}{\text{*}}
\newcommand{+}{\text{+}}
\newcommand{?}{\text{?}}

\newcommand{\SynVar}[2][]{\text{\emph{#1:#2}}}


\newlist{SynEnvList}{itemize}{1}
\setlist[SynEnvList]{
  parsep=1ex, partopsep=0pt, itemsep=0pt, topsep=0pt, label={},
  leftmargin=2\leftmargin, listparindent=-\leftmargin,
  itemindent=\listparindent
}
\newenvironment{Syntax} {
    \begin{SyntaxCallout}
    \begin{SynEnvList}
    \item\relax
}{
    \end{SynEnvList}
    \end{SyntaxCallout}
}
\newenvironment{Lexical} {
    \begin{LexicalCallout}
    \begin{SynEnvList}
    \item\relax
}{
    \end{SynEnvList}
    \end{LexicalCallout}
}


\newcommand{\MetaDef}[1]{\textbf{$\mathbb{#1}$}}
\newcommand{\SynComment}[1]{\text{\small{// #1}}}

\newcommand{\MetaVar}[1]{\text{\textbf{$\mathbb{#1}$}}}

\newcommand{\ContextVarA}{\ensuremath{\Gamma_0}}
\newcommand{\ContextVarB}{\ensuremath{\Gamma_1}}
\newcommand{\ContextVarC}{\ensuremath{\Gamma_2}}
\newcommand{\ContextVarD}{\ensuremath{\Gamma_3}}
\newcommand{\ContextVarE}{\ensuremath{\Gamma_4}}
\newcommand{\ContextVarF}{\ensuremath{\Gamma_5}}

\newcommand{\ExprVarE}{\ensuremath{e}}
\newcommand{\ExprVarF}{\ensuremath{f}}

\newcommand{\StmtVarS}{\ensuremath{s}}
\newcommand{\StmtVarT}{\ensuremath{t}}

\newcommand{\TypeVarT}{\ensuremath{T}}
\newcommand{\TypeVarU}{\ensuremath{U}}

\newcommand{\BindingVarX}{\ensuremath{\alpha}}
\newcommand{\BindingVarY}{\ensuremath{\beta}}

\newcommand{\Char}[1]{\code{#1}}

\newcommand{\ResultType}{\text{\textsc{Return}}}
\newcommand{\BreakLabel}{\text{\textsc{Break}}}
\newcommand{\ContinueLabel}{\text{\textsc{Continue}}}

\newcommand{\RequireCap}[1]{\text{\textsc{Require} \textsc{#1}}}


\newcommand{\DerivationRule}[3][]{\ensuremath{\trfrac[#1]{#2}{#3}}}

%
% Utilities for use in `Checking` callouts:
%

\newcommand{\SynthExpr}[4]{\ensuremath{#1 \vdash #2 \Rightarrow #3 \vdash #4}}
\newcommand{\CheckExpr}[4]{\ensuremath{#1 \vdash #2 \Leftarrow #3 \vdash #4}}

\newcommand{\CheckType}[3]{\ensuremath{#1 \vdash \textsc{type}\ #2\ \textsc{ok} \vdash #3}}

\newcommand{\CheckStmt}[3]{\ensuremath{#1 \vdash \textsc{stmt}\ #2\ \textsc{ok} \vdash #3}}
\newcommand{\CheckStmts}[3]{\ensuremath{#1 \vdash \textsc{stmts}\ #2\ \textsc{ok} \vdash #3}}
\newcommand{\CheckDecl}[3]{\ensuremath{#1 \vdash \textsc{decl}\ #2\ \textsc{ok} \vdash #3}}

\newcommand{\CheckCases}[3]{\ensuremath{#1 \vdash \textsc{CheckAlternatives}(#2, #3)}}
\newcommand{\CheckCase}[3]{\ensuremath{#1 \vdash \textsc{CheckAlternative}(#2, #3)}}
\newcommand{\CheckCaseLabel}[3]{\ensuremath{#1 \vdash \textsc{CheckAlternativeLabel}(#2, #3)}}

% Check that the given context contains an entry of the given form.
\newcommand{\ContextContains}[2]{\ensuremath{#1 \vdash #2}}

% Check that lookup up the given symbol in the context yields the given value/type/whatever.
\newcommand{\ContextLookup}[3]{\ensuremath{#1 ( #2 ) = #3}}

% Check that a type conforms to a given interface in the input context.
% Yields an output context (which may include additional constraints).
\newcommand{\CheckConforms}[4]{\ensuremath{#1 \vdash #2\ \textsc{ConformsTo} #3 \vdash #4}}


% Check that an attempt to construct an instance of the given type
% with the given argument list is valid.
\newcommand{\CheckConstruct}[4]{\ensuremath{#1 \vdash \textsc{Construct}(#2, #3) \vdash #4}}

% Check/synthesize a call to an expression with arguments.
\newcommand{\CheckCall}[5]{\ensuremath{#1 \vdash \textsc{Call}(#2, #3) \Leftarrow #4 \vdash #5}}
\newcommand{\SynthCall}[5]{\ensuremath{#1 \vdash \textsc{Call}(#2, #3) \Rightarrow #4 \vdash #5}}

% Check/synthesize lookup of a name
\newcommand{\CheckLookup}[4]{\ensuremath{#1 \vdash \textsc{Lookup}(#2) \Leftarrow #3 \vdash #4}}
\newcommand{\SynthLookup}[3]{\ensuremath{#1 \vdash \textsc{Lookup}(#2) \Rightarrow #3}}
