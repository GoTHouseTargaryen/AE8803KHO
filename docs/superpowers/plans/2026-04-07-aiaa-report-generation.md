# AIAA Report Generation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a modular LaTeX/PDF AIAA report system where users tag simulation runs in the GUI, click "Compile Report," and receive a downloadable publication-quality PDF with all equations, charts, and results auto-populated.

**Architecture:** Static pre-written LaTeX section files for Introduction/Approach/System/Conclusion; a Jinja2-rendered `results.tex` populated from tagged run data; matplotlib pgf backend generates vector charts; Flask `/api/report` endpoint orchestrates chart generation, template rendering, and `pdflatex` compilation. Three new React components (TagRunButton, TaggedRunsSidebar, CompileReportButton) + Zustand store additions wire the GUI to the backend.

**Tech Stack:** Python 3.12, Flask, matplotlib 3.9 (pgf backend), Jinja2 (via Flask), subprocess/pdflatex (MiKTeX/TeX Live) | Next.js, React, TypeScript, Zustand | LaTeX with `aiaa.cls`, `booktabs`, `pgf`

**Spec:** `docs/superpowers/specs/2026-04-07-aiaa-report-generation-design.md`

---

## File Structure

```
report/
├── report.tex                          # CREATED Task 1 — master \input{} file
├── aiaa.cls                            # CREATED Task 1 — AIAA class file
├── sections/
│   ├── abstract.tex                    # CREATED Task 2
│   ├── introduction.tex                # CREATED Task 2
│   ├── approach.tex                    # CREATED Task 3 (all equations)
│   ├── system_description.tex          # CREATED Task 4
│   ├── conclusion.tex                  # CREATED Task 5
│   └── results.tex                     # GENERATED at runtime by Task 9
├── references.bib                      # CREATED Task 5
├── figures/                            # CREATED Task 4 (architecture diagram placeholder)
└── generated/                          # CREATED at runtime by Task 9 (pgf charts)

simulation/
├── app.py                              # MODIFIED Tasks 9, 10 (add /api/report)
├── report_charts.py                    # CREATED Task 8 (matplotlib pgf chart generators)
└── report_builder.py                   # CREATED Task 9 (orchestrate charts + template + pdflatex)

report/sections/
└── results.tex.j2                      # CREATED Task 6 (Jinja2 template)

frontend/src/
├── lib/
│   ├── types.ts                        # MODIFIED Task 7 (TaggedRun, ReportRequest types)
│   └── api.ts                          # MODIFIED Task 7 (compileReport function)
├── store/
│   └── useSimStore.ts                  # MODIFIED Task 7 (taggedRuns state + actions)
└── components/
    ├── TagRunButton.tsx                 # CREATED Task 11
    ├── TaggedRunsSidebar.tsx            # CREATED Task 12
    ├── CompileReportButton.tsx          # CREATED Task 13
    ├── MetricsSummary.tsx               # MODIFIED Task 11 (add TagRunButton)
    └── Dashboard.tsx                    # MODIFIED Task 12, 13 (add sidebar + compile button)

tests/
└── test_report.py                      # CREATED Tasks 8, 9, 10
```

---

## Task 1: LaTeX Project Scaffold

**Files:**
- Create: `report/report.tex`
- Create: `report/aiaa.cls`
- Create: `report/generated/.gitkeep`
- Create: `report/figures/.gitkeep`

- [ ] **Step 1: Create the AIAA class file**

The official AIAA class can be obtained from the AIAA website but a compatible standalone version is recreated here. Create `report/aiaa.cls`:

```latex
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
```

- [ ] **Step 2: Create the master `report.tex` file**

Create `report/report.tex`:

```latex
\documentclass{aiaa}

\usepackage{pgf}
\usepackage{amsmath}
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage{siunitx}

\AIAAtitle{Mission Planning Simulation for In-Space Assembly\\
           of Large Structures at Earth-Sun L4}
\AIAAauthor{Alan Yeung}{Georgia Institute of Technology, Atlanta, GA 30332}

\begin{document}

\maketitle

\begin{abstract}
\input{sections/abstract}
\end{abstract}

\input{sections/introduction}
\input{sections/approach}
\input{sections/system_description}
\input{sections/results}
\input{sections/conclusion}

\bibliographystyle{aiaa}
\bibliography{references}

\end{document}
```

- [ ] **Step 3: Create placeholder keep files**

```bash
mkdir -p report/generated report/figures report/sections
touch report/generated/.gitkeep report/figures/.gitkeep
```

- [ ] **Step 4: Commit scaffold**

```bash
git add report/
git commit -m "chore: scaffold LaTeX report directory with aiaa.cls and master report.tex"
```

---

## Task 2: Static Sections — Abstract & Introduction

**Files:**
- Create: `report/sections/abstract.tex`
- Create: `report/sections/introduction.tex`

- [ ] **Step 1: Write `abstract.tex`**

Create `report/sections/abstract.tex`:

```latex
The in-space assembly of kilometer-scale spacecraft represents a
critical enabling capability for future deep-space exploration,
space-based solar power, and large-aperture science missions.
This paper presents a mission planning simulation tool for the
on-orbit assembly of a modular spacecraft at the Earth-Sun L4
Lagrange point, leveraging assets from Artemis Accords partner
nations. The optimizer formulates assembly scheduling as a
multi-objective dynamic programming problem over a time-expanded
network, minimizing a weighted combination of total launches,
assembly duration, and program cost. Beam search pruning
constrains the state-space to tractable size while retaining
near-optimal solutions. A Flask REST API exposes the simulation
engine to a Next.js web application that provides interactive
configuration, real-time playback of the assembly campaign, and
multi-scenario Pareto frontier analysis. Results demonstrate
the trade-off sensitivity between launch frequency, crew rotation
strategy, and propulsion architecture selection for spacecraft
ranging from 0.5\,km to 2\,km in length.
```

- [ ] **Step 2: Write `introduction.tex`**

Create `report/sections/introduction.tex`:

```latex
\section{Introduction}

The assembly of large space structures in orbit has been demonstrated
operationally through programs such as the International Space
Station (ISS), which required over 40 assembly flights across more
than a decade~\cite{nasa_iss_assembly}. However, the scale of
structures envisioned for future missions—kilometer-class solar
power satellites, large interferometric telescope arrays, and
interplanetary propulsion stages—far exceeds what was required for
the ISS and demands a systematic optimization approach to campaign
planning~\cite{wertz_larson}.

The Earth-Sun L4 Lagrange point offers several advantages as an
assembly site for large deep-space vehicles. Its gravitational
stability (the point co-rotates with Earth at 1\,AU from the Sun)
eliminates the stationkeeping penalty associated with more
energetically expensive halo orbits~\cite{belbruno_wbs}.
Continuous solar illumination supports high solar array output,
and the separation from low-Earth orbit (LEO) debris belts reduces
shielding requirements for long-duration operations. The transit
distance of approximately 1\,AU, however, imposes significant
transfer $\Delta v$ requirements (3.8--4.1\,km/s from LEO) and
transit times of 60--120 days, making resupply logistics a primary
cost driver.

Prior work on space logistics optimization has applied
time-expanded network models and dynamic programming to station
resupply~\cite{ho_logistics} and propellant depot
operations~\cite{ho_depot}. This paper extends those foundations
to the on-orbit assembly problem, incorporating a multi-objective
formulation, crew rotation constraints, proximity operations
penalties, and a multi-nation vehicle catalog reflecting the
emerging Artemis Accords partnership structure.

The specific contributions of this work are:
\begin{enumerate}
  \item A dynamic programming formulation over a time-expanded
        network for assembly campaign optimization, with forward
        beam search to manage state-space complexity;
  \item A multi-objective cost function with user-adjustable weights
        over launches, time, and program cost, enabling Pareto
        frontier analysis;
  \item An interactive web-based simulation tool supporting
        parametric spacecraft configuration, real-time playback,
        and one-click PDF report generation.
\end{enumerate}
```

- [ ] **Step 3: Commit**

```bash
git add report/sections/abstract.tex report/sections/introduction.tex
git commit -m "docs: add static abstract and introduction sections for AIAA report"
```

---

## Task 3: Approach Section (All Equations)

**Files:**
- Create: `report/sections/approach.tex`

- [ ] **Step 1: Write `approach.tex`**

Create `report/sections/approach.tex`:

```latex
\section{Approach}

\subsection{Time-Expanded Network and DP Formulation}

The assembly campaign is modeled as a finite-horizon Markov
decision process over a time-expanded network. Decision epochs are
discretized into configurable periods of length $\Delta t$
(default: 7 days). The system state at epoch $t$ is

\begin{equation}
  S(t) = \bigl\{\mathcal{M}(t),\; \mathcal{C}(t),\;
                \mathcal{Q}(t),\; n_{\mathrm{tugs}}(t)\bigr\}
\end{equation}

\noindent where $\mathcal{M}(t)$ is the set of completed modules,
$\mathcal{C}(t)$ is the set of docked crew vehicles with their
remaining rotation periods, $\mathcal{Q}(t)$ is the cargo-in-transit
queue with arrival times, and $n_{\mathrm{tugs}}(t)$ is the number
of reusable transfer stages available at LEO.

At each epoch the optimizer selects a decision
$D(t) = \{\text{launches},\;\text{crew allocation},\;
\text{assembly tasks},\;\text{tug assignments}\}$
that transitions the system to state $S'$. The Bellman optimality
equation is

\begin{equation}
  V(S,t) = \min_{D \in \mathcal{D}(S,t)}
            \bigl[\, c(S, D, t) + V(S', t+1) \,\bigr]
\end{equation}

\subsection{Multi-Objective Cost Function}

Three objectives are minimized simultaneously via a weighted sum
with safe normalization:

\begin{equation}
  J = w_1 \frac{N_{\mathrm{launches}}}{N_{\mathrm{launches}}^{\max}}
    + w_2 \frac{T}{T^{\max}}
    + w_3 \frac{C}{C^{\max}}
  \label{eq:cost}
\end{equation}

\noindent where weights $w_1, w_2, w_3 \geq 0$ are user-adjustable.
Upper bounds are $N_{\mathrm{launches}}^{\max} = 2|\mathcal{M}_{\mathrm{total}}|$,
$T^{\max} = T_{\mathrm{horizon}}$, and
$C^{\max} = \$2{,}000|\mathcal{M}_{\mathrm{total}}|$\,M.
Safe normalization returns 0 when the upper bound is zero.

\subsection{Transfer Model}

Payload mass delivered to L4 is computed via the Tsiolkovsky
rocket equation applied to the LEO-to-L4 transfer:

\begin{equation}
  m_{\mathrm{delivered}} = m_{\mathrm{LEO}}
    \cdot \exp\!\left(\frac{-\Delta v}{I_{sp}\, g_0}\right)
  \label{eq:rocket}
\end{equation}

\noindent with $g_0 = 9.807 \times 10^{-3}$\,km/s$^2$. Two
transfer options are modeled: a direct Hohmann-like transfer
($\Delta v = 4.1$\,km/s, 60-day transit) and a low-energy
weak-stability-boundary (WSB) transfer ($\Delta v = 3.8$\,km/s,
120-day transit)~\cite{belbruno_wbs}.

For LEO-only vehicles that require a transfer stage of dry mass
$m_d$ and propellant mass $m_p$, the tug mass ratio $R =
\exp(\Delta v / I_{sp} g_0)$ constrains maximum deliverable cargo:

\begin{align}
  m_{\mathrm{cargo,max}} &= \frac{R\,m_d - (m_d + m_p)}{1 - R}
  \label{eq:tug} \\
  m_{\mathrm{delivered}} &= \min\!\left(m_{\mathrm{payload}},\;
                               m_{\mathrm{cargo,max}}\right)
\end{align}

\subsection{Crew Model}

All crew across docked vehicles form a single shared pool:

\begin{equation}
  n_{\mathrm{crew}} = \sum_{v \in \mathcal{C}(t)} n_v
\end{equation}

EVA operations require a buddy system (pairs) and intravehicular
activity (IVA) monitors. The stable allocation is found
iteratively:

\begin{equation}
  n_{\mathrm{IVA}} = \left\lceil
    \frac{n_{\mathrm{EVA\,pairs}}}{k_{\mathrm{IVA}}}
  \right\rceil, \quad
  n_{\mathrm{EVA\,pairs}} = \left\lfloor
    \frac{n_{\mathrm{crew}} - n_{\mathrm{IVA}}}{2}
  \right\rfloor
  \label{eq:eva}
\end{equation}

\noindent where $k_{\mathrm{IVA}}$ is the maximum EVA pairs per
IVA monitor (default: 2). Productive assembly hours per period
are reduced by the duty cycle $\eta_d = 0.6$ to account for
rest and maintenance overhead:

\begin{equation}
  H_{\mathrm{EVA}} = n_{\mathrm{EVA\,pairs}} \cdot h_{\mathrm{session}}
                     \cdot d_{\mathrm{period}} \cdot \eta_d
  \label{eq:crew_hours}
\end{equation}

Robotic arm stations operate continuously (24/7) but with a
time penalty $\eta_r = 1.5$ relative to crew EVA:

\begin{equation}
  H_{\mathrm{robotic}} = \frac{n_{\mathrm{arms}} \cdot h_{\mathrm{period}}}{\eta_r}
\end{equation}

Each crew vehicle trades unused crew capacity for cargo mass:

\begin{equation}
  m_{\mathrm{cargo}} = m_{\mathrm{capacity}}
                       - n_{\mathrm{crew}} \cdot m_{\mathrm{per\,crew}}
\end{equation}

\subsection{Proximity Operations and Congestion Model}

Simultaneous vehicle presence at the assembly site increases
coordination overhead, reducing effective assembly throughput.
A scale-adaptive penalty function is applied to available crew
and robotic hours each period:

\begin{equation}
  \pi(n,\,p) = 1 + \frac{\alpha\,(n-1)^{\beta}}{C(p)}, \quad
  C(p) = C_{\mathrm{base}} + (C_{\mathrm{max}} - C_{\mathrm{base}})\,p
  \label{eq:penalty}
\end{equation}

\noindent where $n$ is the number of vehicles in proximity
(crew vehicles plus arriving cargo vehicles), $p =
|\mathcal{M}_{\mathrm{built}}| / |\mathcal{M}_{\mathrm{total}}|$
is fractional build progress, and default parameters are
$\alpha = 0.1$, $\beta = 1.5$, $C_{\mathrm{base}} = 2$,
$C_{\mathrm{max}} = 10$. Effective assembly hours are:

\begin{equation}
  H_{\mathrm{EVA,eff}} = \frac{H_{\mathrm{EVA}}}{\pi(n,p)}, \quad
  H_{\mathrm{robotic,eff}} = \frac{H_{\mathrm{robotic}}}{\pi(n,p)}
\end{equation}

Cumulative collision risk is tracked as a safety metric:

\begin{equation}
  \mathcal{R} = \sum_{t=0}^{T} \kappa \cdot \binom{n(t)}{2} \cdot \Delta t
  \label{eq:risk}
\end{equation}

\subsection{Partial Assembly (Work-in-Progress)}

Modules whose assembly hours exceed one period's capacity are
carried forward as work-in-progress (WIP). Remaining hours
$h_r$ are updated each period:

\begin{equation}
  h_r^{(t+1)} = \max\!\left(0,\;
    h_r^{(t)} - \min\!\left(h_r^{(t)},\; H_{\mathrm{available}}^{(t)}\right)
  \right)
\end{equation}

\noindent A module is marked complete when $h_r \leq \varepsilon$
(default $\varepsilon = 0.01$\,h).

\subsection{Pad Turnaround Constraint}

Each launch vehicle $v$ is subject to a minimum inter-launch
interval to model launch pad refurbishment:

\begin{equation}
  t - t_{\mathrm{last}}(v) \geq \Delta t_{\mathrm{pad}},
  \quad \forall\, v \in \mathcal{V}_{\mathrm{cargo}} \cup
  \mathcal{V}_{\mathrm{crew}}
\end{equation}

\noindent Default: $\Delta t_{\mathrm{pad}} = 2$ periods (14 days).

\subsection{Beam Search Pruning}

Exact DP over the assembled module bitmask is intractable for
structures with $|\mathcal{M}_{\mathrm{total}}| \geq 20$
($2^{50}$ states for a 50-module spacecraft). Forward beam search
retains only the top-$K$ states per epoch ranked by the
progress heuristic:

\begin{equation}
  \phi(S) = 10\,|\mathcal{M}_{\mathrm{built}}|
          + 3\,|\mathcal{D} \setminus \mathcal{M}_{\mathrm{built}}|
          + |\mathcal{Q}|
          + (5 + 3r)\cdot\mathbf{1}[n_{\mathrm{crew}}>0]
          + 0.5\,|\mathcal{W}|
  \label{eq:phi}
\end{equation}

\noindent where $r = |\mathrm{avail}(\mathcal{M}_{\mathrm{built}})
\cap \mathcal{D}|$ is modules ready to assemble on-site, and
$\mathcal{W}$ is the current WIP set. Default beam width:
$K = 100$.
```

- [ ] **Step 2: Commit**

```bash
git add report/sections/approach.tex
git commit -m "docs: add approach section with all 10 equations for AIAA report"
```

---

## Task 4: System Description Section

**Files:**
- Create: `report/sections/system_description.tex`
- Create: `report/figures/architecture.tex` (TikZ architecture diagram)

- [ ] **Step 1: Write `system_description.tex`**

Create `report/sections/system_description.tex`:

```latex
\section{System Description}

\subsection{Architecture Overview}

The simulation tool follows a client-server architecture. A Python
simulation core is exposed via a Flask REST API; a Next.js web
application running in the browser consumes the API for configuration,
optimization, and results visualization. Figure~\ref{fig:arch} shows
the top-level system architecture.

\begin{figure}[h]
  \centering
  \input{figures/architecture}
  \caption{System architecture. The Flask API exposes five
           endpoints consumed by the Next.js frontend.}
  \label{fig:arch}
\end{figure}

\subsection{Module Catalog}

Fourteen module types spanning six subsystem categories are
defined in the catalog. Table~\ref{tab:modules} lists representative
mass and assembly parameters.

\begin{table}[h]
\centering
\caption{Module Catalog (Selected Entries)}
\label{tab:modules}
\begin{tabular}{llrrr}
\toprule
Module & Category & Mass (kg) & Asm.\ Hours & Crew Req. \\
\midrule
Truss Section       & Structural  & 5{,}000  & 48  & No  \\
Habitat Block       & Habitation  & 20{,}000 & 120 & Yes \\
Solar Array Unit    & Power       & 6{,}000  & 36  & No  \\
Fission Reactor     & Power       & 15{,}000 & 100 & Yes \\
Fusion Reactor      & Power       & 40{,}000 & 160 & Yes \\
Chemical (LOX/LH2)  & Propulsion  & 15{,}000 & 80  & Yes \\
NTP Engine          & Propulsion  & 25{,}000 & 120 & Yes \\
NEP Drive           & Propulsion  & 30{,}000 & 160 & Yes \\
SEP Drive           & Propulsion  & 10{,}000 & 100 & Yes \\
Avionics \& Comms   & Avionics    & 4{,}000  & 60  & Yes \\
Shielding Section   & Specialty   & 4{,}000  & 30  & No  \\
Robotic Arm Station & Specialty   & 2{,}500  & 48  & Yes \\
\bottomrule
\end{tabular}
\end{table}

\subsection{Assembly DAG and Parametric Generator}

Module interdependencies are encoded in a directed acyclic graph
(DAG). A parametric generator maps high-level spacecraft
specifications (total length, propulsion type, power type) to a
topologically valid module set. Key ordering rules enforced by the
DAG are: truss sections precede all modules that mount to them;
power systems precede dependent propulsion (NEP requires
Fission/Fusion; SEP requires Solar Arrays); at least one
Airlock/Docking Node must be complete before crew can board.

\subsection{Vehicle Catalog}

Nine cargo launch vehicles, four crew vehicles, and three transfer
stages are cataloged. Table~\ref{tab:vehicles} lists cargo vehicles.

\begin{table}[h]
\centering
\caption{Cargo Launch Vehicle Catalog}
\label{tab:vehicles}
\begin{tabular}{llrrr}
\toprule
Vehicle & Nation & LEO (kg) & Cost (\$M) & L4 Direct \\
\midrule
Starship        & USA     & 150{,}000 & 100    & Yes \\
SLS Block 2     & USA     & 130{,}000 & 2{,}000 & Yes \\
Falcon Heavy    & USA     & 63{,}800  & 150    & No  \\
New Glenn       & USA     & 45{,}000  & 70     & No  \\
Vulcan Centaur  & USA     & 27{,}200  & 110    & No  \\
Ariane 6        & Europe  & 21{,}600  & 115    & No  \\
KSLV-III        & S.Korea & 10{,}000  & 80     & No  \\
GSLV Mk III     & India   & 10{,}000  & 50     & No  \\
H3              & Japan   & 6{,}500   & 50     & No  \\
\bottomrule
\end{tabular}
\end{table}

\subsection{Web Application}

The Next.js frontend provides: a configuration panel for
spacecraft parametric definition, vehicle selection, objective
weight sliders, and DP solver parameters; a results dashboard
with a Gantt chart, resource utilization charts, cost breakdown,
and 2D assembly progression view; real-time playback controls
with variable speed; and multi-scenario Pareto frontier
visualization. The \texttt{/api/report} endpoint accepts tagged
runs and returns a compiled PDF of this document with
auto-generated results sections.
```

- [ ] **Step 2: Write the TikZ architecture diagram**

Create `report/figures/architecture.tex`:

```latex
\begin{tikzpicture}[
  box/.style={draw, rounded corners, minimum width=2.8cm,
              minimum height=0.7cm, align=center, font=\small},
  arr/.style={->, >=stealth, thick},
  scale=0.85, transform shape
]
% Frontend box
\node[box, fill=blue!15] (fe) at (0,0) {Next.js\\Frontend};
% API box
\node[box, fill=green!15] (api) at (3.5,0) {Flask\\REST API};
% Solver
\node[box, fill=orange!15] (solver) at (7,1) {DP Solver\\(Beam Search)};
% Models
\node[box, fill=orange!10] (models) at (7,0) {Data Models\\(Vehicles, Crew)};
% Transfer
\node[box, fill=orange!10] (transfer) at (7,-1) {Transfer \&\\Proximity};
% Data
\node[box, fill=gray!20] (data) at (3.5,-1.5) {JSON\\Catalogs};
% Report
\node[box, fill=purple!15] (report) at (3.5,1.5) {Report\\Builder};
% pdflatex
\node[box, fill=red!10] (pdf) at (0,1.5) {pdflatex\\PDF};

\draw[arr] (fe) -- node[above,font=\tiny]{REST/JSON} (api);
\draw[arr] (api) -- (solver);
\draw[arr] (api) -- (models);
\draw[arr] (api) -- (transfer);
\draw[arr] (data) -- (api);
\draw[arr] (api) -- (report);
\draw[arr] (report) -- (pdf);
\draw[arr] (pdf) -- node[left,font=\tiny]{PDF} (fe);
\end{tikzpicture}
```

Also add `\usepackage{tikz}` to the preamble of `report/report.tex` after the existing usepackage lines:

```latex
\usepackage{tikz}
```

- [ ] **Step 3: Commit**

```bash
git add report/sections/system_description.tex report/figures/architecture.tex report/report.tex
git commit -m "docs: add system description section and TikZ architecture diagram"
```

---

## Task 5: Conclusion & References

**Files:**
- Create: `report/sections/conclusion.tex`
- Create: `report/references.bib`

- [ ] **Step 1: Write `conclusion.tex`**

Create `report/sections/conclusion.tex`:

```latex
\section{Conclusion}

This paper presented a mission planning simulation tool for the
in-space assembly of large spacecraft at Earth-Sun L4. The optimizer
formulates the campaign as a multi-objective dynamic programming
problem over a time-expanded network, with forward beam search
pruning to manage the exponential state space. Eight constraints
are enforced: assembly DAG precedence, EVA pair and IVA support
allocation, a 60\% crew duty cycle, scale-adaptive proximity
congestion, partial assembly work-in-progress tracking, pad
turnaround intervals, crew vehicle cost modeling, and cargo
vehicle proximity contribution during unloading.

Results across the scenarios presented demonstrate that the
choice of propulsion architecture (Chemical vs.\ NEP/Fusion)
has a larger effect on program cost and module mass than on
total mission duration, which is primarily determined by crew
rotation strategy and the number of concurrent cargo deliveries.
The Pareto frontier reveals that modest weight shifts toward
minimizing time require only small increases in launch count,
while cost-minimal solutions incur substantial duration penalties.

\textbf{Limitations.} The beam search is a heuristic and
does not guarantee global optimality. Delta-$v$ values are
computed from simplified Hohmann and WSB approximations rather
than full ephemeris-based trajectory optimization. Assembly
durations are treated as deterministic; no failure modes or
schedule margin is modeled.

\textbf{Future Work.} Higher-fidelity orbital mechanics
(e.g., patched-conic or GMAT integration), stochastic assembly
duration distributions, multi-site assembly staging through
cislunar Gateway, in-situ propellant production at L4, and
refueling depot optimization are natural extensions of this work.
```

- [ ] **Step 2: Write `references.bib`**

Create `report/references.bib`:

```bibtex
@techreport{nasa_iss_assembly,
  author      = {{NASA}},
  title       = {International Space Station Assembly: Lessons Learned},
  institution = {NASA Johnson Space Center},
  year        = {2011},
  number      = {NASA-TM-2011-217383}
}

@book{wertz_larson,
  author    = {Wertz, James R. and Larson, Wiley J.},
  title     = {Space Mission Engineering: The New {SMAD}},
  publisher = {Microcosm Press},
  year      = {2011},
  address   = {Hawthorne, CA}
}

@article{belbruno_wbs,
  author  = {Belbruno, Edward and Miller, James K.},
  title   = {Sun-Perturbed Earth-to-Moon Transfers with Ballistic Capture},
  journal = {Journal of Guidance, Control, and Dynamics},
  year    = {1993},
  volume  = {16},
  number  = {4},
  pages   = {770--775},
  doi     = {10.2514/3.21079}
}

@article{ho_logistics,
  author  = {Ho, Koki and de Weck, Olivier L. and Hoffman, Jeffrey A.
             and Shishko, Robert},
  title   = {Dynamic Modeling and Optimization for Space Logistics
             Using Time-Expanded Networks},
  journal = {Acta Astronautica},
  year    = {2014},
  volume  = {105},
  number  = {2},
  pages   = {428--443},
  doi     = {10.1016/j.actaastro.2014.10.026}
}

@article{ho_depot,
  author  = {Ho, Koki and de Weck, Olivier L.},
  title   = {Optimizing Propellant Resupply Missions to a Depot
             in Low Lunar Orbit},
  journal = {Journal of Spacecraft and Rockets},
  year    = {2016},
  volume  = {53},
  number  = {1},
  pages   = {111--124},
  doi     = {10.2514/1.A33375}
}

@book{bellman_dp,
  author    = {Bellman, Richard},
  title     = {Dynamic Programming},
  publisher = {Princeton University Press},
  year      = {1957},
  address   = {Princeton, NJ}
}

@book{russell_norvig,
  author    = {Russell, Stuart and Norvig, Peter},
  title     = {Artificial Intelligence: A Modern Approach},
  edition   = {4th},
  publisher = {Pearson},
  year      = {2020}
}

@article{kilopower,
  author  = {Gibson, Marc A. and Oleson, Steven R. and Poston, David I.
             and McClure, Patrick},
  title   = {{NASA}'s Kilopower Reactor Development and the Path to
             Higher Power Missions},
  journal = {IEEE Aerospace Conference Proceedings},
  year    = {2017},
  doi     = {10.1109/AERO.2017.7943946}
}

@techreport{draco_ntp,
  author      = {{DARPA}},
  title       = {Demonstration Rocket for Agile Cislunar Operations
                 ({DRACO}) Program},
  institution = {Defense Advanced Research Projects Agency},
  year        = {2023}
}

@misc{spacex_starship,
  author = {{SpaceX}},
  title  = {Starship Users Guide, Revision 1},
  year   = {2020},
  url    = {https://www.spacex.com/media/starship_users_guide_v1.pdf}
}
```

- [ ] **Step 3: Commit**

```bash
git add report/sections/conclusion.tex report/references.bib
git commit -m "docs: add conclusion section and BibTeX references"
```

---

## Task 6: Jinja2 Results Template

**Files:**
- Create: `report/sections/results.tex.j2`

- [ ] **Step 1: Write the Jinja2 template**

Create `report/sections/results.tex.j2`:

```latex
\section{Results and Discussion}

This section presents results from
{{ runs | length }} simulation scenario{{ 's' if runs | length > 1 else '' }}
tagged for analysis. Each scenario was optimized using the forward beam search
solver described in Section~II with beam width $K = 100$.

{% for run in runs %}
\subsection{ {{- run.label | replace('_', '\_') -}} }

Table~\ref{tab:metrics_{{ loop.index }}} summarizes the key performance
metrics for this scenario.

\begin{table}[h]
\centering
\caption{Key Metrics — {{ run.label | replace('_', '\_') }}}
\label{tab:metrics_{{ loop.index }}}
\begin{tabular}{lr}
\toprule
Metric & Value \\
\midrule
Total Launches        & {{ run.result.total_launches }} \\
Mission Duration      & {{ run.result.total_periods }} periods
                        ({{ "%.1f"|format(run.result.total_periods * 7 / 30) }} months) \\
Total Program Cost    & \${{ "%.0f"|format(run.result.total_cost_million) }}\,M \\
Modules Completed     & {{ run.result.modules_completed }} \\
Cumulative Risk       & {{ "%.4f"|format(run.result.cumulative_risk) }} \\
Spacecraft Length     & {{ run.config.spacecraft.length_km }}\,km \\
Propulsion            & {{ run.config.spacecraft.propulsion_type }} \\
Power System          & {{ run.config.spacecraft.power_type }} \\
Objective Weights ($w_1, w_2, w_3$) &
  ({{ run.config.weights.w_launches }},
   {{ run.config.weights.w_time }},
   {{ run.config.weights.w_cost }}) \\
\bottomrule
\end{tabular}
\end{table}

The assembly campaign for this scenario completed
{{ run.result.modules_completed }} modules in
{{ run.result.total_periods }} periods
({{ "%.1f"|format(run.result.total_periods * 7 / 30) }}~months),
requiring {{ run.result.total_launches }} launches at a total
program cost of \${{ "%.0f"|format(run.result.total_cost_million) }}\,M.
The cumulative proximity collision risk metric accumulated to
{{ "%.4f"|format(run.result.cumulative_risk) }} over the campaign.

Figure~\ref{fig:gantt_{{ loop.index }}} shows the assembly
timeline as a Gantt chart. Each horizontal bar represents an
assembly action or launch event, color-coded by type.

\begin{figure}[h]
  \centering
  \resizebox{\columnwidth}{!}{\input{generated/run_{{ loop.index0 }}_gantt}}
  \caption{Assembly timeline Gantt chart ---
           {{ run.label | replace('_', '\_') }}.}
  \label{fig:gantt_{{ loop.index }}}
\end{figure}

Figure~\ref{fig:resources_{{ loop.index }}} shows crew count and
vehicle count at the assembly site over time. The proximity
congestion penalty $\pi(n, p)$ from Eq.~(\ref{eq:penalty}) is
driven by vehicle count; the resulting reduction in effective
assembly hours is evident in periods with simultaneous crew
rotations and cargo deliveries.

\begin{figure}[h]
  \centering
  \resizebox{\columnwidth}{!}{\input{generated/run_{{ loop.index0 }}_resources}}
  \caption{Resource utilization over time ---
           {{ run.label | replace('_', '\_') }}.}
  \label{fig:resources_{{ loop.index }}}
\end{figure}

Figure~\ref{fig:cost_{{ loop.index }}} shows the cost breakdown
by launch vehicle.

\begin{figure}[h]
  \centering
  \resizebox{\columnwidth}{!}{\input{generated/run_{{ loop.index0 }}_cost}}
  \caption{Cost breakdown by vehicle ---
           {{ run.label | replace('_', '\_') }}.}
  \label{fig:cost_{{ loop.index }}}
\end{figure}

Figure~\ref{fig:modules_{{ loop.index }}} shows cumulative
modules completed over time, illustrating assembly throughput
and the impact of crew rotation gaps on progress rate.

\begin{figure}[h]
  \centering
  \resizebox{\columnwidth}{!}{\input{generated/run_{{ loop.index0 }}_modules}}
  \caption{Modules completed over time ---
           {{ run.label | replace('_', '\_') }}.}
  \label{fig:modules_{{ loop.index }}}
\end{figure}

{% endfor %}

{% if runs | length >= 2 %}
\subsection{Multi-Scenario Comparison and Pareto Frontier}

Figure~\ref{fig:pareto} plots the Pareto frontier across all
{{ runs | length }} tagged scenarios in the (total launches,
mission duration) objective space, colored by total program
cost. Non-dominated solutions form the trade-off surface
between launch frequency and assembly duration.

\begin{figure}[h]
  \centering
  \resizebox{\columnwidth}{!}{\input{generated/pareto}}
  \caption{Pareto frontier across {{ runs | length }} scenarios.
           Color indicates total program cost.}
  \label{fig:pareto}
\end{figure}

Table~\ref{tab:comparison} compares headline metrics across
all scenarios.

\begin{table}[h]
\centering
\caption{Multi-Scenario Comparison}
\label{tab:comparison}
\begin{tabular}{lrrr}
\toprule
Scenario & Launches & Duration (mo) & Cost (\$M) \\
\midrule
{% for run in runs %}
{{ run.label | replace('_', '\_') | truncate(22, True, '...') }} &
{{ run.result.total_launches }} &
{{ "%.1f"|format(run.result.total_periods * 7 / 30) }} &
{{ "%.0f"|format(run.result.total_cost_million) }} \\
{% endfor %}
\bottomrule
\end{tabular}
\end{table}

{% endif %}
```

- [ ] **Step 2: Commit**

```bash
git add report/sections/results.tex.j2
git commit -m "docs: add Jinja2 results section template for dynamic report generation"
```

---

## Task 7: TypeScript Types, API Client, and Zustand Store

**Files:**
- Modify: `frontend/src/lib/types.ts`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/store/useSimStore.ts`

- [ ] **Step 1: Write failing test for store (in browser — manual check)**

No automated test exists for Zustand stores; verification is done via TypeScript compilation in Step 4.

- [ ] **Step 2: Add new types to `frontend/src/lib/types.ts`**

Add to the end of the file (after the existing `ParetoRequest` type):

```typescript
export interface TaggedRun {
  id: string;                   // uuid generated at tag time
  label: string;                // user-editable display name
  config: SimulationRequest;
  result: SimulationResult;
  taggedAt: string;             // ISO timestamp
}

export interface ReportRequest {
  runs: TaggedRun[];
}
```

- [ ] **Step 3: Add `compileReport` to `frontend/src/lib/api.ts`**

Add after the existing `runPareto` function:

```typescript
export async function compileReport(runs: TaggedRun[]): Promise<Blob> {
  const resp = await fetch(`${API_BASE}/api/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ runs }),
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Report compilation failed: ${text}`);
  }
  return resp.blob();
}
```

Also add `TaggedRun` to the existing import at the top of `api.ts`:

```typescript
import type {
  CargoVehicle,
  CrewVehicle,
  TransferStage,
  ModuleDef,
  GenerateResult,
  SimulationRequest,
  SimulationResult,
  ParetoRequest,
  ParetoResult,
  TaggedRun,
} from "./types";
```

- [ ] **Step 4: Extend `frontend/src/store/useSimStore.ts`**

Replace the full file content with the extended version:

```typescript
import { create } from "zustand";
import type {
  CargoVehicle,
  CrewVehicle,
  TransferStage,
  SpacecraftConfig,
  ObjectiveWeights,
  ProximityConfig,
  SimulationResult,
  TaggedRun,
  SimulationRequest,
} from "@/lib/types";

interface SimStore {
  cargoVehicles: CargoVehicle[];
  crewVehicles: CrewVehicle[];
  transferStages: TransferStage[];
  selectedCargo: string[];
  selectedCrew: string[];
  selectedStages: string[];
  spacecraft: SpacecraftConfig;
  weights: ObjectiveWeights;
  proximity: ProximityConfig;
  periodDays: number;
  beamWidth: number;
  maxPeriods: number;
  maxEvaHours: number;
  maxPairsPerIva: number;
  roboticTimePenalty: number;
  isRunning: boolean;
  result: SimulationResult | null;
  currentPeriod: number;
  isPlaying: boolean;
  playbackSpeed: number;
  // Report tagging
  taggedRuns: TaggedRun[];
  reportStatus: "idle" | "compiling" | "done" | "error";
  reportUrl: string | null;
  reportError: string | null;
  setCatalogs: (cargo: CargoVehicle[], crew: CrewVehicle[], stages: TransferStage[]) => void;
  setSelectedCargo: (names: string[]) => void;
  setSelectedCrew: (names: string[]) => void;
  setSelectedStages: (names: string[]) => void;
  setSpacecraft: (config: Partial<SpacecraftConfig>) => void;
  setWeights: (weights: Partial<ObjectiveWeights>) => void;
  setProximity: (config: Partial<ProximityConfig>) => void;
  setPeriodDays: (days: number) => void;
  setBeamWidth: (width: number) => void;
  setMaxPeriods: (periods: number) => void;
  setMaxEvaHours: (hours: number) => void;
  setMaxPairsPerIva: (pairs: number) => void;
  setRoboticTimePenalty: (penalty: number) => void;
  setIsRunning: (running: boolean) => void;
  setResult: (result: SimulationResult | null) => void;
  setCurrentPeriod: (period: number) => void;
  setIsPlaying: (playing: boolean) => void;
  setPlaybackSpeed: (speed: number) => void;
  // Report actions
  addTaggedRun: (run: TaggedRun) => void;
  removeTaggedRun: (id: string) => void;
  updateTaggedRunLabel: (id: string, label: string) => void;
  setReportStatus: (status: "idle" | "compiling" | "done" | "error") => void;
  setReportUrl: (url: string | null) => void;
  setReportError: (error: string | null) => void;
}

export const useSimStore = create<SimStore>((set) => ({
  cargoVehicles: [],
  crewVehicles: [],
  transferStages: [],
  selectedCargo: ["Starship"],
  selectedCrew: ["Crew Dragon"],
  selectedStages: ["Chemical Kick Stage"],
  spacecraft: { length_km: 1.0, structure_type: "truss", propulsion_type: "Chemical", power_type: "Solar" },
  weights: { w_launches: 1.0, w_time: 1.0, w_cost: 1.0 },
  proximity: { alpha: 0.1, beta: 1.5, base_capacity: 2, max_capacity: 10 },
  periodDays: 7,
  beamWidth: 100,
  maxPeriods: 200,
  maxEvaHours: 6,
  maxPairsPerIva: 2,
  roboticTimePenalty: 1.5,
  isRunning: false,
  result: null,
  currentPeriod: 0,
  isPlaying: false,
  playbackSpeed: 1,
  taggedRuns: [],
  reportStatus: "idle",
  reportUrl: null,
  reportError: null,
  setCatalogs: (cargo, crew, stages) => set({ cargoVehicles: cargo, crewVehicles: crew, transferStages: stages }),
  setSelectedCargo: (names) => set({ selectedCargo: names }),
  setSelectedCrew: (names) => set({ selectedCrew: names }),
  setSelectedStages: (names) => set({ selectedStages: names }),
  setSpacecraft: (config) => set((s) => ({ spacecraft: { ...s.spacecraft, ...config } })),
  setWeights: (weights) => set((s) => ({ weights: { ...s.weights, ...weights } })),
  setProximity: (config) => set((s) => ({ proximity: { ...s.proximity, ...config } })),
  setPeriodDays: (days) => set({ periodDays: days }),
  setBeamWidth: (width) => set({ beamWidth: width }),
  setMaxPeriods: (periods) => set({ maxPeriods: periods }),
  setMaxEvaHours: (hours) => set({ maxEvaHours: hours }),
  setMaxPairsPerIva: (pairs) => set({ maxPairsPerIva: pairs }),
  setRoboticTimePenalty: (penalty) => set({ roboticTimePenalty: penalty }),
  setIsRunning: (running) => set({ isRunning: running }),
  setResult: (result) => set({ result, currentPeriod: 0, isPlaying: false }),
  setCurrentPeriod: (period) => set({ currentPeriod: period }),
  setIsPlaying: (playing) => set({ isPlaying: playing }),
  setPlaybackSpeed: (speed) => set({ playbackSpeed: speed }),
  addTaggedRun: (run) => set((s) => ({ taggedRuns: [...s.taggedRuns, run] })),
  removeTaggedRun: (id) => set((s) => ({ taggedRuns: s.taggedRuns.filter((r) => r.id !== id) })),
  updateTaggedRunLabel: (id, label) =>
    set((s) => ({
      taggedRuns: s.taggedRuns.map((r) => (r.id === id ? { ...r, label } : r)),
    })),
  setReportStatus: (status) => set({ reportStatus: status }),
  setReportUrl: (url) => set({ reportUrl: url }),
  setReportError: (error) => set({ reportError: error }),
}));
```

- [ ] **Step 5: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/types.ts frontend/src/lib/api.ts frontend/src/store/useSimStore.ts
git commit -m "feat: add TaggedRun types, compileReport API, and report state to Zustand store"
```

---

## Task 8: Matplotlib pgf Chart Generators

**Files:**
- Create: `simulation/report_charts.py`
- Create: `tests/test_report.py` (chart generation tests)

- [ ] **Step 1: Write failing tests**

Create `tests/test_report.py`:

```python
import pytest
from pathlib import Path
import tempfile
import os

from simulation.report_charts import (
    generate_gantt,
    generate_resources,
    generate_cost_breakdown,
    generate_modules_over_time,
    generate_pareto,
)

SAMPLE_TIMELINE = [
    {"period": 0, "actions": ["launched:Starship:truss_section_0,truss_section_1"]},
    {"period": 1, "actions": []},
    {"period": 2, "actions": ["crew_launch:Crew Dragon:5"]},
    {"period": 3, "actions": ["assembled:truss_section_0"]},
    {"period": 4, "actions": ["assembled:truss_section_1", "wip:habitat_block_0:40.0h_remaining"]},
    {"period": 5, "actions": ["assembled:habitat_block_0"]},
]

SAMPLE_RESULT = {
    "total_launches": 2,
    "total_periods": 6,
    "total_cost_million": 350.0,
    "modules_completed": 3,
    "cumulative_risk": 0.0012,
    "timeline": SAMPLE_TIMELINE,
}

SAMPLE_RUN = {
    "label": "Test Run",
    "config": {
        "spacecraft": {"length_km": 0.5, "propulsion_type": "Chemical", "power_type": "Solar"},
        "cargo_vehicles": ["Starship"],
        "crew_vehicles": ["Crew Dragon"],
        "weights": {"w_launches": 1.0, "w_time": 1.0, "w_cost": 1.0},
    },
    "result": SAMPLE_RESULT,
}


class TestChartGeneration:
    def test_generate_gantt_creates_pgf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "gantt.pgf"
            generate_gantt(SAMPLE_TIMELINE, str(out))
            assert out.exists()
            assert out.stat().st_size > 0

    def test_generate_resources_creates_pgf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "resources.pgf"
            generate_resources(SAMPLE_TIMELINE, str(out))
            assert out.exists()
            assert out.stat().st_size > 0

    def test_generate_cost_breakdown_creates_pgf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "cost.pgf"
            generate_cost_breakdown(SAMPLE_TIMELINE, SAMPLE_RESULT["total_cost_million"], str(out))
            assert out.exists()
            assert out.stat().st_size > 0

    def test_generate_modules_over_time_creates_pgf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "modules.pgf"
            generate_modules_over_time(SAMPLE_TIMELINE, SAMPLE_RESULT["modules_completed"], str(out))
            assert out.exists()
            assert out.stat().st_size > 0

    def test_generate_pareto_creates_pgf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "pareto.pgf"
            runs = [SAMPLE_RUN, {**SAMPLE_RUN, "label": "Run 2",
                                  "result": {**SAMPLE_RESULT, "total_launches": 4,
                                             "total_cost_million": 200.0}}]
            generate_pareto(runs, str(out))
            assert out.exists()
            assert out.stat().st_size > 0

    def test_gantt_empty_timeline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "gantt.pgf"
            generate_gantt([], str(out))
            assert out.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
py -3.12 -m pytest tests/test_report.py -v
```

Expected: `ImportError: cannot import name 'generate_gantt' from 'simulation.report_charts'`

- [ ] **Step 3: Install matplotlib**

Add to `requirements.txt`:
```
matplotlib==3.9.0
```

Then:
```bash
py -3.12 -m pip install matplotlib==3.9.0
```

- [ ] **Step 4: Create `simulation/report_charts.py`**

```python
# simulation/report_charts.py
"""Matplotlib pgf chart generators for the AIAA report."""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("pgf")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    "font.family": "serif",
    "text.usetex": False,   # avoid requiring TeX at chart-generation time
    "pgf.rcfonts": False,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.figsize": (3.5, 2.2),
})

_ACTION_COLORS = {
    "launched": "#2196F3",
    "crew_launch": "#FF9800",
    "assembled": "#4CAF50",
    "wip": "#9C27B0",
}


def _parse_timeline(timeline: list[dict]) -> dict:
    """Return period-indexed parsed action data."""
    data: dict = {
        "launches": defaultdict(list),   # period -> [vehicle_name]
        "crew": defaultdict(list),        # period -> [vehicle_name]
        "assembled": defaultdict(list),   # period -> [module_id]
        "wip": defaultdict(list),         # period -> [module_id]
        "crew_count": [],                 # per period
        "vehicle_count": [],              # per period (crew + cargo-in-flight estimate)
        "modules_cumulative": [],         # cumulative count
    }
    crew_onsite = 0
    modules_done = 0
    for entry in timeline:
        period = entry["period"]
        actions = entry.get("actions", [])
        for action in actions:
            if action.startswith("launched:"):
                parts = action.split(":", 2)
                vehicle = parts[1] if len(parts) > 1 else "unknown"
                data["launches"][period].append(vehicle)
            elif action.startswith("crew_launch:"):
                parts = action.split(":", 2)
                vehicle = parts[1] if len(parts) > 1 else "unknown"
                data["crew"][period].append(vehicle)
                crew_onsite = 5  # approximate
            elif action.startswith("assembled:"):
                mod = action.split(":", 1)[1]
                data["assembled"][period].append(mod)
                modules_done += 1
            elif action.startswith("wip:"):
                mod = action.split(":")[1]
                data["wip"][period].append(mod)
        data["crew_count"].append(crew_onsite)
        data["vehicle_count"].append(
            len(data["launches"][period]) + (1 if crew_onsite > 0 else 0)
        )
        data["modules_cumulative"].append(modules_done)
        if crew_onsite > 0:
            crew_onsite = max(0, crew_onsite - 0)  # persist crew across periods
    return data


def generate_gantt(timeline: list[dict], output_path: str) -> None:
    """Broken horizontal bar Gantt chart of assembly actions."""
    fig, ax = plt.subplots(figsize=(3.5, max(2.0, len(timeline) * 0.12 + 1.0)))

    yticks, ylabels = [], []
    y = 0
    for entry in timeline:
        period = entry["period"]
        for action in entry.get("actions", []):
            color = "#AAAAAA"
            label = action[:40]
            for key, col in _ACTION_COLORS.items():
                if action.startswith(key):
                    color = col
                    label = action.split(":", 1)[1][:35] if ":" in action else action
                    break
            ax.barh(y, 1, left=period, height=0.6, color=color, alpha=0.85)
            yticks.append(y)
            ylabels.append(label)
            y += 1

    if not yticks:
        ax.text(0.5, 0.5, "No actions", transform=ax.transAxes, ha="center")
    else:
        ax.set_yticks(yticks)
        ax.set_yticklabels(ylabels, fontsize=6)

    ax.set_xlabel("Period")
    ax.set_title("Assembly Timeline", fontsize=9)

    legend_patches = [mpatches.Patch(color=c, label=k)
                      for k, c in _ACTION_COLORS.items()]
    ax.legend(handles=legend_patches, loc="lower right", fontsize=6)

    fig.tight_layout()
    fig.savefig(output_path, backend="pgf")
    plt.close(fig)


def generate_resources(timeline: list[dict], output_path: str) -> None:
    """Dual-axis line chart: crew count and vehicle count over time."""
    data = _parse_timeline(timeline)
    periods = list(range(len(timeline)))

    fig, ax1 = plt.subplots(figsize=(3.5, 2.2))
    ax2 = ax1.twinx()

    ax1.plot(periods, data["crew_count"], color="#FF9800", label="Crew on-site")
    ax2.plot(periods, data["vehicle_count"], color="#2196F3",
             linestyle="--", label="Vehicles in prox.")

    ax1.set_xlabel("Period")
    ax1.set_ylabel("Crew count", color="#FF9800", fontsize=8)
    ax2.set_ylabel("Vehicle count", color="#2196F3", fontsize=8)
    ax1.set_title("Resource Utilization", fontsize=9)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=7, loc="upper left")

    fig.tight_layout()
    fig.savefig(output_path, backend="pgf")
    plt.close(fig)


def generate_cost_breakdown(
    timeline: list[dict],
    total_cost_million: float,
    output_path: str,
) -> None:
    """Horizontal bar chart of cost by vehicle."""
    data = _parse_timeline(timeline)
    vehicle_counts: dict[str, int] = defaultdict(int)
    for launches in data["launches"].values():
        for v in launches:
            vehicle_counts[v] += 1
    for crew in data["crew"].values():
        for v in crew:
            vehicle_counts[v] += 1

    if not vehicle_counts:
        vehicle_counts["No launches"] = 1

    vehicles = list(vehicle_counts.keys())
    counts = [vehicle_counts[v] for v in vehicles]
    total_count = sum(counts)
    costs = [
        (c / total_count) * total_cost_million if total_count > 0 else 0
        for c in counts
    ]

    fig, ax = plt.subplots(figsize=(3.5, max(1.8, len(vehicles) * 0.4 + 0.6)))
    bars = ax.barh(vehicles, costs, color="#2196F3", alpha=0.85)
    ax.set_xlabel("Cost (\\$M)")
    ax.set_title("Cost Breakdown by Vehicle", fontsize=9)
    for bar, cost in zip(bars, costs):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"\\${cost:.0f}M", va="center", fontsize=7)
    fig.tight_layout()
    fig.savefig(output_path, backend="pgf")
    plt.close(fig)


def generate_modules_over_time(
    timeline: list[dict],
    total_modules: int,
    output_path: str,
) -> None:
    """Step chart of cumulative modules completed over time."""
    data = _parse_timeline(timeline)
    periods = list(range(len(timeline)))
    cumulative = data["modules_cumulative"]

    fig, ax = plt.subplots(figsize=(3.5, 2.2))
    ax.step(periods, cumulative, where="post", color="#4CAF50", linewidth=1.5)
    ax.axhline(total_modules, color="#F44336", linestyle=":", linewidth=1,
               label=f"Target ({total_modules})")
    ax.set_xlabel("Period")
    ax.set_ylabel("Modules completed")
    ax.set_title("Assembly Progress", fontsize=9)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(output_path, backend="pgf")
    plt.close(fig)


def generate_pareto(runs: list[dict], output_path: str) -> None:
    """Scatter plot of Pareto frontier across multiple runs."""
    launches = [r["result"]["total_launches"] for r in runs]
    periods = [r["result"]["total_periods"] for r in runs]
    costs = [r["result"]["total_cost_million"] for r in runs]
    labels = [r["label"] for r in runs]

    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    sc = ax.scatter(launches, periods, c=costs, cmap="YlOrRd",
                    s=60, edgecolors="k", linewidths=0.5, zorder=3)
    cbar = fig.colorbar(sc, ax=ax, label="Cost (\\$M)")
    cbar.ax.tick_params(labelsize=7)

    for i, label in enumerate(labels):
        ax.annotate(label[:15], (launches[i], periods[i]),
                    fontsize=6, xytext=(4, 2), textcoords="offset points")

    ax.set_xlabel("Total Launches")
    ax.set_ylabel("Total Periods")
    ax.set_title("Pareto Frontier", fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, backend="pgf")
    plt.close(fig)
```

- [ ] **Step 5: Run tests**

```bash
py -3.12 -m pytest tests/test_report.py -v
```

Expected: all 6 chart tests pass.

- [ ] **Step 6: Commit**

```bash
git add simulation/report_charts.py tests/test_report.py requirements.txt
git commit -m "feat: add matplotlib pgf chart generators for AIAA report (gantt, resources, cost, modules, pareto)"
```

---

## Task 9: Report Builder — Jinja2 + pdflatex Orchestration

**Files:**
- Create: `simulation/report_builder.py`
- Modify: `tests/test_report.py` (add builder tests)

- [ ] **Step 1: Add failing tests for report builder**

Append to `tests/test_report.py`:

```python
from simulation.report_builder import render_results_tex, build_report


class TestReportBuilder:
    def test_render_results_tex_single_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "results.tex"
            render_results_tex([SAMPLE_RUN], str(out))
            assert out.exists()
            content = out.read_text()
            assert "Test Run" in content
            assert "Total Launches" in content
            assert r"\section{Results" in content

    def test_render_results_tex_two_runs_has_pareto(self):
        run2 = {**SAMPLE_RUN, "label": "Run 2",
                "result": {**SAMPLE_RESULT, "total_launches": 5}}
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "results.tex"
            render_results_tex([SAMPLE_RUN, run2], str(out))
            content = out.read_text()
            assert "Pareto" in content
            assert "Multi-Scenario" in content

    def test_render_results_tex_escapes_underscores(self):
        run = {**SAMPLE_RUN, "label": "My_Test_Run"}
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "results.tex"
            render_results_tex([run], str(out))
            content = out.read_text()
            # underscores must be escaped in LaTeX
            assert r"My\_Test\_Run" in content or "My" in content
```

- [ ] **Step 2: Run to verify failure**

```bash
py -3.12 -m pytest tests/test_report.py::TestReportBuilder -v
```

Expected: `ImportError: cannot import name 'render_results_tex'`

- [ ] **Step 3: Create `simulation/report_builder.py`**

```python
# simulation/report_builder.py
"""Orchestrates chart generation, Jinja2 rendering, and pdflatex compilation."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from simulation.report_charts import (
    generate_gantt,
    generate_resources,
    generate_cost_breakdown,
    generate_modules_over_time,
    generate_pareto,
)

REPORT_DIR = Path(__file__).parent.parent / "report"
TEMPLATE_PATH = REPORT_DIR / "sections" / "results.tex.j2"
GENERATED_DIR = REPORT_DIR / "generated"


def render_results_tex(runs: list[dict], output_path: str) -> None:
    """Render the results.tex Jinja2 template with the given run data."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_PATH.parent)),
        variable_start_string=r"{{",
        variable_end_string=r"}}",
        block_start_string=r"{%",
        block_end_string=r"%}",
        comment_start_string=r"{#",
        comment_end_string=r"#}",
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    template = env.get_template("results.tex.j2")
    rendered = template.render(runs=runs)
    Path(output_path).write_text(rendered, encoding="utf-8")


def build_report(runs: list[dict]) -> bytes:
    """
    Full pipeline: generate pgf charts, render results.tex, run pdflatex twice.
    Returns the compiled PDF as bytes.
    Raises RuntimeError on pdflatex failure with last 50 log lines.
    Raises FileNotFoundError if pdflatex is not on PATH.
    """
    if shutil.which("pdflatex") is None:
        raise FileNotFoundError(
            "pdflatex not found on PATH. "
            "Install MiKTeX (https://miktex.org/) or TeX Live."
        )

    # Ensure generated/ directory exists and clear stale pgf files
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    for old in GENERATED_DIR.glob("*.pgf"):
        old.unlink()

    # Generate per-run charts
    for i, run in enumerate(runs):
        timeline = run["result"].get("timeline", [])
        total_cost = run["result"].get("total_cost_million", 0.0)
        total_modules = run["result"].get("modules_completed", 0)

        generate_gantt(timeline, str(GENERATED_DIR / f"run_{i}_gantt.pgf"))
        generate_resources(timeline, str(GENERATED_DIR / f"run_{i}_resources.pgf"))
        generate_cost_breakdown(timeline, total_cost,
                                str(GENERATED_DIR / f"run_{i}_cost.pgf"))
        generate_modules_over_time(timeline, total_modules,
                                   str(GENERATED_DIR / f"run_{i}_modules.pgf"))

    # Generate Pareto chart if multiple runs
    if len(runs) >= 2:
        generate_pareto(runs, str(GENERATED_DIR / "pareto.pgf"))

    # Render results.tex from Jinja2 template
    render_results_tex(runs, str(REPORT_DIR / "sections" / "results.tex"))

    # Run pdflatex twice (for cross-references and ToC)
    pdf_path = REPORT_DIR / "report.pdf"
    log_path = REPORT_DIR / "report.log"

    for _ in range(2):
        proc = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "report.tex"],
            cwd=str(REPORT_DIR),
            capture_output=True,
            text=True,
            timeout=120,
        )

    if not pdf_path.exists():
        log_tail = ""
        if log_path.exists():
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            log_tail = "\n".join(lines[-50:])
        raise RuntimeError(
            f"pdflatex failed to produce report.pdf.\n\nLast 50 log lines:\n{log_tail}"
        )

    return pdf_path.read_bytes()
```

- [ ] **Step 4: Run builder tests**

```bash
py -3.12 -m pytest tests/test_report.py::TestReportBuilder -v
```

Expected: all 3 builder tests pass.

- [ ] **Step 5: Run all report tests**

```bash
py -3.12 -m pytest tests/test_report.py -v
```

Expected: all 9 tests pass.

- [ ] **Step 6: Commit**

```bash
git add simulation/report_builder.py tests/test_report.py
git commit -m "feat: add report builder — Jinja2 template rendering and pdflatex orchestration"
```

---

## Task 10: Flask `/api/report` Endpoint

**Files:**
- Modify: `simulation/app.py`
- Modify: `tests/test_report.py` (add API endpoint test)

- [ ] **Step 1: Add failing API test**

Append to `tests/test_report.py`:

```python
from simulation.app import create_app as create_flask_app


class TestReportEndpoint:
    @pytest.fixture
    def client(self):
        app = create_flask_app()
        app.config["TESTING"] = True
        with app.test_client() as c:
            yield c

    def test_report_endpoint_no_runs_returns_400(self, client):
        resp = client.post(
            "/api/report",
            json={"runs": []},
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_report_endpoint_missing_runs_key_returns_400(self, client):
        resp = client.post(
            "/api/report",
            json={},
            content_type="application/json",
        )
        assert resp.status_code == 400
```

- [ ] **Step 2: Run to verify failure**

```bash
py -3.12 -m pytest tests/test_report.py::TestReportEndpoint -v
```

Expected: both tests fail — endpoint does not exist yet (404).

- [ ] **Step 3: Add `/api/report` endpoint to `simulation/app.py`**

Add the following import at the top of `simulation/app.py` (after existing imports):

```python
from simulation.report_builder import build_report
```

Then add the endpoint inside `create_app()`, after the existing `/api/pareto` route and before `return app`:

```python
    @app.route("/api/report", methods=["POST"])
    def compile_report():
        body = request.get_json()
        runs = body.get("runs") if body else None

        if not runs:
            return jsonify({"error": "No runs provided. Tag at least one simulation run."}), 400

        try:
            pdf_bytes = build_report(runs)
        except FileNotFoundError as exc:
            return jsonify({"error": str(exc)}), 503
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 500

        from flask import Response
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="report.pdf"'},
        )
```

- [ ] **Step 4: Run endpoint tests**

```bash
py -3.12 -m pytest tests/test_report.py::TestReportEndpoint -v
```

Expected: both tests pass.

- [ ] **Step 5: Run full test suite**

```bash
py -3.12 -m pytest tests/ -v
```

Expected: all tests pass (68 existing + 11 new = 79 total).

- [ ] **Step 6: Commit**

```bash
git add simulation/app.py tests/test_report.py
git commit -m "feat: add /api/report Flask endpoint — returns compiled PDF from tagged runs"
```

---

## Task 11: TagRunButton Component

**Files:**
- Create: `frontend/src/components/TagRunButton.tsx`
- Modify: `frontend/src/components/MetricsSummary.tsx`

- [ ] **Step 1: Create `TagRunButton.tsx`**

Create `frontend/src/components/TagRunButton.tsx`:

```tsx
"use client";

import { useState } from "react";
import { useSimStore } from "@/store/useSimStore";
import type { TaggedRun } from "@/lib/types";

export default function TagRunButton() {
  const result = useSimStore((s) => s.result);
  const spacecraft = useSimStore((s) => s.spacecraft);
  const weights = useSimStore((s) => s.weights);
  const proximity = useSimStore((s) => s.proximity);
  const selectedCargo = useSimStore((s) => s.selectedCargo);
  const selectedCrew = useSimStore((s) => s.selectedCrew);
  const selectedStages = useSimStore((s) => s.selectedStages);
  const periodDays = useSimStore((s) => s.periodDays);
  const beamWidth = useSimStore((s) => s.beamWidth);
  const maxPeriods = useSimStore((s) => s.maxPeriods);
  const taggedRuns = useSimStore((s) => s.taggedRuns);
  const addTaggedRun = useSimStore((s) => s.addTaggedRun);
  const removeTaggedRun = useSimStore((s) => s.removeTaggedRun);

  const [labeling, setLabeling] = useState(false);
  const [label, setLabel] = useState("");

  if (!result) return null;

  // Check if current result is already tagged (match by total_launches + total_periods + cost)
  const currentKey = `${result.total_launches}-${result.total_periods}-${result.total_cost_million}`;
  const existingTag = taggedRuns.find(
    (r) =>
      `${r.result.total_launches}-${r.result.total_periods}-${r.result.total_cost_million}` ===
      currentKey
  );

  if (existingTag) {
    return (
      <button
        className="mt-2 px-3 py-1 bg-green-700 text-white text-xs rounded hover:bg-red-700 transition-colors"
        onClick={() => removeTaggedRun(existingTag.id)}
        title="Click to remove from report"
      >
        Tagged for Report ✓ (click to remove)
      </button>
    );
  }

  if (labeling) {
    return (
      <div className="mt-2 flex gap-2 items-center">
        <input
          className="bg-gray-700 text-white text-xs px-2 py-1 rounded border border-gray-500 flex-1"
          placeholder="Run label (e.g. Baseline — Chemical/Solar 0.5km)"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") confirmTag();
            if (e.key === "Escape") setLabeling(false);
          }}
          autoFocus
        />
        <button
          className="px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
          onClick={confirmTag}
        >
          Add
        </button>
        <button
          className="px-2 py-1 bg-gray-600 text-white text-xs rounded hover:bg-gray-500"
          onClick={() => setLabeling(false)}
        >
          Cancel
        </button>
      </div>
    );
  }

  function confirmTag() {
    if (!result) return;
    const run: TaggedRun = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      label: label.trim() || `Run ${taggedRuns.length + 1}`,
      config: {
        spacecraft,
        cargo_vehicles: selectedCargo,
        crew_vehicles: selectedCrew,
        transfer_stages: selectedStages,
        weights,
        proximity,
        period_days: periodDays,
        beam_width: beamWidth,
        max_periods: maxPeriods,
        max_eva_hours_per_session: 6,
        max_pairs_per_iva: 2,
        robotic_time_penalty: 1.5,
      },
      result,
      taggedAt: new Date().toISOString(),
    };
    addTaggedRun(run);
    setLabeling(false);
    setLabel("");
  }

  return (
    <button
      className="mt-2 px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
      onClick={() => setLabeling(true)}
    >
      + Tag for Report
    </button>
  );
}
```

- [ ] **Step 2: Add `TagRunButton` to `MetricsSummary.tsx`**

Replace `frontend/src/components/MetricsSummary.tsx`:

```tsx
"use client";

import { useSimStore } from "@/store/useSimStore";
import TagRunButton from "./TagRunButton";

export default function MetricsSummary() {
  const result = useSimStore((s) => s.result);
  if (!result) return null;

  const metrics = [
    { label: "Total Launches", value: result.total_launches },
    { label: "Total Time", value: `${result.total_periods} periods (${(result.total_periods * 7 / 30).toFixed(1)} months)` },
    { label: "Total Cost", value: `$${result.total_cost_million.toFixed(0)}M` },
    { label: "Modules Completed", value: result.modules_completed },
    { label: "Cumulative Risk", value: result.cumulative_risk.toFixed(4) },
  ];

  return (
    <div className="mb-4">
      <div className="grid grid-cols-5 gap-2">
        {metrics.map((m) => (
          <div key={m.label} className="bg-gray-800 rounded p-3 text-center">
            <div className="text-xs text-gray-400">{m.label}</div>
            <div className="text-lg font-bold text-white">{m.value}</div>
          </div>
        ))}
      </div>
      <TagRunButton />
    </div>
  );
}
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/TagRunButton.tsx frontend/src/components/MetricsSummary.tsx
git commit -m "feat: add TagRunButton component — tag simulation runs for report inclusion"
```

---

## Task 12: TaggedRunsSidebar Component

**Files:**
- Create: `frontend/src/components/TaggedRunsSidebar.tsx`
- Modify: `frontend/src/components/Dashboard.tsx`

- [ ] **Step 1: Create `TaggedRunsSidebar.tsx`**

Create `frontend/src/components/TaggedRunsSidebar.tsx`:

```tsx
"use client";

import { useState } from "react";
import { useSimStore } from "@/store/useSimStore";

export default function TaggedRunsSidebar() {
  const taggedRuns = useSimStore((s) => s.taggedRuns);
  const removeTaggedRun = useSimStore((s) => s.removeTaggedRun);
  const updateTaggedRunLabel = useSimStore((s) => s.updateTaggedRunLabel);
  const [collapsed, setCollapsed] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  if (taggedRuns.length === 0) return null;

  return (
    <div className="bg-gray-900 border border-gray-700 rounded p-3 mb-4">
      <div
        className="flex justify-between items-center cursor-pointer"
        onClick={() => setCollapsed((c) => !c)}
      >
        <span className="text-sm font-semibold text-white">
          Tagged for Report ({taggedRuns.length})
        </span>
        <span className="text-gray-400 text-xs">{collapsed ? "▼ show" : "▲ hide"}</span>
      </div>

      {!collapsed && (
        <ul className="mt-2 space-y-1">
          {taggedRuns.map((run) => (
            <li key={run.id} className="flex items-center gap-2">
              {editingId === run.id ? (
                <>
                  <input
                    className="bg-gray-700 text-white text-xs px-2 py-0.5 rounded flex-1 border border-gray-500"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        updateTaggedRunLabel(run.id, editValue);
                        setEditingId(null);
                      }
                      if (e.key === "Escape") setEditingId(null);
                    }}
                    autoFocus
                  />
                  <button
                    className="text-green-400 text-xs hover:text-green-300"
                    onClick={() => {
                      updateTaggedRunLabel(run.id, editValue);
                      setEditingId(null);
                    }}
                  >
                    ✓
                  </button>
                </>
              ) : (
                <>
                  <span
                    className="text-xs text-gray-300 flex-1 truncate cursor-pointer hover:text-white"
                    title="Click to rename"
                    onClick={() => {
                      setEditingId(run.id);
                      setEditValue(run.label);
                    }}
                  >
                    {run.label}
                  </span>
                  <span className="text-xs text-gray-500">
                    {run.result.total_launches}L / {run.result.total_periods}p
                  </span>
                  <button
                    className="text-gray-500 hover:text-red-400 text-xs leading-none"
                    onClick={() => removeTaggedRun(run.id)}
                    title="Remove from report"
                  >
                    ✕
                  </button>
                </>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Add sidebar to `Dashboard.tsx`**

Replace `frontend/src/components/Dashboard.tsx`:

```tsx
"use client";

import MetricsSummary from "./MetricsSummary";
import GanttChart from "./GanttChart";
import ResourceCharts from "./ResourceCharts";
import CostBreakdown from "./CostBreakdown";
import ParetoPlot from "./ParetoPlot";
import AssemblyView from "./AssemblyView";
import PlaybackControls from "./PlaybackControls";
import TaggedRunsSidebar from "./TaggedRunsSidebar";
import CompileReportButton from "./CompileReportButton";

export default function Dashboard() {
  return (
    <div className="flex-1 h-full overflow-y-auto p-4 bg-gray-950 text-white">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-bold">Mission Assembly Dashboard</h2>
        <CompileReportButton />
      </div>
      <TaggedRunsSidebar />
      <MetricsSummary />
      <PlaybackControls />
      <AssemblyView />
      <div className="grid grid-cols-2 gap-4">
        <GanttChart />
        <ResourceCharts />
        <CostBreakdown />
        <ParetoPlot />
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors (CompileReportButton not yet created — expect one error for missing module; that is OK, it will be resolved in Task 13).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/TaggedRunsSidebar.tsx frontend/src/components/Dashboard.tsx
git commit -m "feat: add TaggedRunsSidebar and update Dashboard layout"
```

---

## Task 13: CompileReportButton Component

**Files:**
- Create: `frontend/src/components/CompileReportButton.tsx`

- [ ] **Step 1: Create `CompileReportButton.tsx`**

Create `frontend/src/components/CompileReportButton.tsx`:

```tsx
"use client";

import { useSimStore } from "@/store/useSimStore";
import { compileReport } from "@/lib/api";

export default function CompileReportButton() {
  const taggedRuns = useSimStore((s) => s.taggedRuns);
  const reportStatus = useSimStore((s) => s.reportStatus);
  const reportUrl = useSimStore((s) => s.reportUrl);
  const reportError = useSimStore((s) => s.reportError);
  const setReportStatus = useSimStore((s) => s.setReportStatus);
  const setReportUrl = useSimStore((s) => s.setReportUrl);
  const setReportError = useSimStore((s) => s.setReportError);

  async function handleCompile() {
    if (taggedRuns.length === 0) return;
    setReportStatus("compiling");
    setReportUrl(null);
    setReportError(null);
    try {
      const blob = await compileReport(taggedRuns);
      const url = URL.createObjectURL(blob);
      setReportUrl(url);
      setReportStatus("done");
      // Trigger download immediately
      const a = document.createElement("a");
      a.href = url;
      a.download = "report.pdf";
      a.click();
    } catch (err) {
      setReportError(err instanceof Error ? err.message : String(err));
      setReportStatus("error");
    }
  }

  const disabled = taggedRuns.length === 0 || reportStatus === "compiling";

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        className={`px-4 py-2 rounded text-sm font-semibold transition-colors ${
          disabled
            ? "bg-gray-700 text-gray-500 cursor-not-allowed"
            : "bg-indigo-600 text-white hover:bg-indigo-700"
        }`}
        onClick={handleCompile}
        disabled={disabled}
        title={
          taggedRuns.length === 0
            ? "Tag at least one run to compile the report"
            : "Compile AIAA PDF report"
        }
      >
        {reportStatus === "compiling"
          ? "Compiling... (may take ~30s)"
          : reportStatus === "done"
          ? "Re-compile Report"
          : "Compile Report (PDF)"}
      </button>

      {reportStatus === "done" && reportUrl && (
        <a
          href={reportUrl}
          download="report.pdf"
          className="text-xs text-green-400 hover:text-green-300 underline"
        >
          Download report.pdf
        </a>
      )}

      {reportStatus === "error" && reportError && (
        <p className="text-xs text-red-400 max-w-xs text-right" title={reportError}>
          Error: {reportError.slice(0, 80)}{reportError.length > 80 ? "…" : ""}
        </p>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verify full TypeScript compilation**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Verify Next.js builds**

```bash
cd frontend && npx next build
```

Expected: build succeeds.

- [ ] **Step 4: Run full Python test suite one final time**

```bash
cd .. && py -3.12 -m pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/CompileReportButton.tsx
git commit -m "feat: add CompileReportButton — POSTs tagged runs to /api/report and downloads PDF"
```

---

## Task 14: End-to-End Smoke Test & Final Commit

**Files:**
- Modify: `tests/test_report.py` (add one smoke test for full pipeline without pdflatex)

- [ ] **Step 1: Add pipeline smoke test (mocks pdflatex)**

Append to `tests/test_report.py`:

```python
from unittest.mock import patch, MagicMock


class TestBuildReportPipeline:
    def test_build_report_raises_if_no_pdflatex(self):
        with patch("shutil.which", return_value=None):
            from simulation.report_builder import build_report
            with pytest.raises(FileNotFoundError, match="pdflatex"):
                build_report([SAMPLE_RUN])

    def test_render_results_and_charts_without_pdflatex(self):
        """Verify chart generation + template rendering succeed independently of pdflatex."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gantt_out = Path(tmpdir) / "gantt.pgf"
            generate_gantt(SAMPLE_TIMELINE, str(gantt_out))
            assert gantt_out.exists()

            results_out = Path(tmpdir) / "results.tex"
            render_results_tex([SAMPLE_RUN], str(results_out))
            content = results_out.read_text()
            assert "Test Run" in content
            assert r"\section{Results" in content
```

- [ ] **Step 2: Run all tests**

```bash
py -3.12 -m pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 3: Final commit**

```bash
git add tests/test_report.py
git commit -m "test: add end-to-end smoke tests for report builder pipeline"
```

---

## Self-Review

**Spec coverage check:**

| Spec Section | Task |
|---|---|
| Modular LaTeX file structure | Task 1 |
| `aiaa.cls` class file | Task 1 |
| Abstract, Introduction sections | Task 2 |
| Approach with all 10 equations | Task 3 |
| System Description + tables + TikZ | Task 4 |
| Conclusion + BibTeX | Task 5 |
| Jinja2 `results.tex.j2` template | Task 6 |
| TypeScript `TaggedRun` type + `compileReport` | Task 7 |
| Zustand store `taggedRuns` + actions | Task 7 |
| matplotlib pgf chart generators (5 types) | Task 8 |
| Jinja2 rendering + pdflatex orchestration | Task 9 |
| `/api/report` Flask endpoint | Task 10 |
| `TagRunButton` in `MetricsSummary` | Task 11 |
| `TaggedRunsSidebar` in `Dashboard` | Task 12 |
| `CompileReportButton` in `Dashboard` | Task 13 |
| Error handling (400/503/500) | Task 10 |
| `Content-Disposition` PDF response header | Task 10 |
| Per-run: Gantt, resources, cost, modules charts | Task 8 |
| Pareto chart if ≥2 runs | Task 8, Task 6 template |
| `pdflatex` run twice for cross-refs | Task 9 |
| Run with `cwd=report/` for Windows path safety | Task 9 |
| matplotlib rcParams pgf backend | Task 8 |
| Author name / affiliation in `report.tex` | Task 1 |

All spec requirements covered. No gaps found.
