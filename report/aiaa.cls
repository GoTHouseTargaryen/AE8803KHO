% aiaa.cls — AIAA Conference Paper Class (compatible version)
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{aiaa}[2024/01/01 AIAA Conference Paper]

\LoadClass[10pt,twocolumn]{article}

\RequirePackage[letterpaper,
  top=1in, bottom=1in,
  left=1in, right=1in,
  columnsep=0.375in]{geometry}
\RequirePackage{times}
\RequirePackage{mathptmx}
\RequirePackage{amsmath,amssymb}
\RequirePackage{booktabs}
\RequirePackage{graphicx}
\RequirePackage{pgf}
\RequirePackage{caption}
\RequirePackage[hidelinks]{hyperref}
\RequirePackage{cite}
\RequirePackage{setspace}
\RequirePackage{titlesec}
\RequirePackage{abstract}

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

\captionsetup{font=small,labelfont=bf}
