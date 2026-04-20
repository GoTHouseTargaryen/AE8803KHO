% aiaa.cls — AIAA Conference Paper Class (single-column, compatible)
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{aiaa}[2024/01/01 AIAA Conference Paper]

\LoadClass[10pt]{article}

\RequirePackage[letterpaper,
  top=1in, bottom=1in,
  left=1in, right=1in]{geometry}
\RequirePackage{lmodern}
\RequirePackage{times}
\RequirePackage{mathptmx}
\RequirePackage{amsmath,amssymb}
\RequirePackage{booktabs}
\RequirePackage{array}
\RequirePackage{graphicx}
\RequirePackage{pgf}
\RequirePackage[font=small,labelfont=bf,labelsep=period,
                justification=justified,
                singlelinecheck=false]{caption}
\RequirePackage[hidelinks]{hyperref}
\RequirePackage{cite}
\RequirePackage{setspace}
\RequirePackage{titlesec}
\RequirePackage{abstract}
\RequirePackage{microtype}
\RequirePackage{ragged2e}

% Full justification with improved spacing (microtype handles protrusion)
\tolerance=1200
\emergencystretch=2em
\hyphenpenalty=50
\hbadness=10000
\vbadness=10000

% Section formatting (AIAA style: bold, centered, Roman numeral)
\titleformat{\section}[block]
  {\normalfont\normalsize\bfseries\centering}
  {\Roman{section}.}{0.5em}{\MakeUppercase}
\titleformat{\subsection}[block]
  {\normalfont\normalsize\bfseries}
  {\Alph{subsection}.}{0.5em}{}
\titleformat{\subsubsection}[runin]
  {\normalfont\normalsize\itshape}
  {\arabic{subsubsection}.}{0.5em}{}[.]

% Abstract formatting
\renewenvironment{abstract}{%
  \begin{center}\textbf{Abstract}\end{center}%
  \small
}{}

% Title block commands
\newcommand{\AIAAtitle}[1]{\title{\large\bfseries #1}}
\newcommand{\AIAAauthor}[2]{\author{#1\\{\small\itshape #2}}}

% AIAA-style figure captions: "Fig. 1  Caption." (bolded label, period)
\renewcommand{\figurename}{Fig.}
\captionsetup[figure]{labelformat=simple,labelsep=space,justification=centering,singlelinecheck=true}
\captionsetup[table]{position=top,labelsep=space,labelformat=simple,justification=centering,singlelinecheck=true}

% Loose float placement so figures do not dump to the end
\renewcommand{\topfraction}{0.9}
\renewcommand{\bottomfraction}{0.8}
\renewcommand{\textfraction}{0.1}
\renewcommand{\floatpagefraction}{0.75}
\setcounter{topnumber}{3}
\setcounter{bottomnumber}{2}
\setcounter{totalnumber}{5}

% Booktabs rule adjustments for AIAA tables
\setlength{\heavyrulewidth}{0.08em}
\setlength{\lightrulewidth}{0.05em}
\setlength{\cmidrulewidth}{0.05em}
