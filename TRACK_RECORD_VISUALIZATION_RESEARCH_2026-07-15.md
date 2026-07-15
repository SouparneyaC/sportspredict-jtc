# Track Record Visualization Research: How to Plot the JTC RBP Campaign

**Purpose of this document.** Before building any chart of this project's Relative Brier Points (RBP)
track record across the Jump Probability Cup (JTC) campaign, the user asked for deep, broad research
into how this specific kind of data — signed, variable-magnitude, time-ordered results, nested
per-question inside per-match, with a known non-independence problem — is actually plotted in real,
citable sources: academic forecasting-tournament papers, quant-finance track-record conventions,
meteorological calibration literature, and general data-visualization principles. The explicit
instruction was no invented sources, no code, no chart file, and no picked winner — options only,
each with its data requirements and honest tradeoffs, in the same numbered-bucket-then-synthesis format
already used in this repo's `DOCUMENTATION_RESEARCH.md` and `PROJECT_STRUCTURE_RESEARCH_2026-07-14.md`.

**The data, read directly before researching anything.** `datasets/questions_flat.csv` has 549 data
rows (`file, match, date, stage, q_num, question_text, category, our_estimate, crowd_estimate, outcome,
rbp, beat_crowd, final_score, match_rbp_total`), spanning 54 unique matches in this snapshot, dated
2026-06-11 through 2026-06-30. 515 rows have a populated per-question `rbp` value, ranging from −51.97
to +35.50 in this file; 53 rows have a populated `match_rbp_total`, ranging from −39.56 (South Africa
vs South Korea) to +120.30 (NED-MAR) in this snapshot. Note explicitly: this CSV snapshot does **not**
yet include the later knockout-stage matches the flagship paper discusses by name — Brazil vs Norway
(+179.26, the campaign-best match) and Canada vs Morocco (−80.83, the campaign-worst single question,
per `JTC_WC2026_Research_Paper.Rmd`) are absent from this file's date range. Whatever chart eventually
gets built needs a fresher data pull than this snapshot — flagging this now rather than silently
building against stale numbers later.

**Existing precedent inside this project, checked first.** `JTC_WC2026_Research_Paper.Rmd` was read in
full (1,409 lines). It contains **zero plots** — no `ggplot`, no `geom_*`, no `\includegraphics`, no
`\begin{figure}` — despite extensive `knitr::kable`/`kableExtra` tables throughout (e.g. the leaderboard
snapshot table at line ~1167, reporting rank/percentile/cumulative-score at three dates). The paper's
"External Validation: Leaderboard Standing" section presents cumulative-score-over-time evidence as a
three-row table, not a chart. This means there is no in-repo plotting convention to defer to — the
chart under discussion would be the project's first. Also found, and load-bearing for this research:
`BRIER_RANK_PRESENTATION_NOTES.md` is an **existing, already-complete literature survey** of exactly
Research Task 1 below (11 real forecasting-tournament papers, reviewed for how they present Brier-score
and rank-progression evidence, written July 2026 for this same paper). Rather than duplicate that work,
Bucket 1 below summarizes its most load-bearing findings and cites it directly, then adds new material
(one paper fetched and read in full for this task) that the existing survey does not cover.

---

## Bucket 1 — Academic forecasting-tournament papers: how they plot sequential/cumulative performance

**Overall finding:** temporal/cumulative score charts are the *least* common visualization in this
literature — most papers use tables, box plots, or rank-distribution histograms instead. Genuine
line-chart-over-tournament-time examples exist but are rare, and one that was fetched and read in full
for this task shows *why* they are rare done badly: a naive multi-line version is hard to read.

### 1. Mellers, Tetlock et al. (2015), "Identifying and Cultivating Superforecasters," *Perspectives on
Psychological Science* 10(3) — already reviewed in `BRIER_RANK_PRESENTATION_NOTES.md` Paper 1
- **What it shows:** Figure 3 is a longitudinal line chart of *daily* standardized Brier score for
  superforecasters vs. top-team individuals, plotted over the calendar days of a multi-year tournament,
  with linear regression trend lines overlaid (steeper negative slope = faster improvement). Figure 1 is
  a box-plot panel (diamonds for means, boxes for IQR, whiskers to non-outlier extremes) comparing three
  forecaster groups across two tournament years.
- **Applicability:** This is the field's clearest precedent for a "performance over tournament time"
  line chart — but it plots only two or three *group* lines (not one line per individual), which is the
  key structural difference from a single-forecaster RBP-over-time chart: this project has one series
  (its own campaign), not a many-line comparison, so the multi-line-overplotting risk this figure
  successfully avoids is a smaller concern here — but see source #5 below for what happens with many
  lines.

### 2. Mellers et al. (2014), "Psychological Strategies for Winning a Geopolitical Forecasting
Tournament," *Psychological Science* 25(5) — `BRIER_RANK_PRESENTATION_NOTES.md` Paper 2
- **What it shows:** Grouped bar chart of average Brier score by training condition × forecaster type,
  reported inline as a relative-improvement percentage ("beat the control group by more than 60%"),
  never as a raw absolute score in isolation.
- **Applicability:** The "always anchor a summary statistic to a comparison baseline" discipline — for
  this project, RBP already is that comparison (score minus crowd), so this principle is already
  satisfied by the metric itself; it argues against ever plotting raw Brier scores without the crowd
  reference, which this project's RBP framing avoids by construction.

### 3. Aldous (2019), "A Prediction Tournament Paradox," arXiv:1903.02131 — `BRIER_RANK_PRESENTATION_NOTES.md` Paper 5
- **What it shows:** Rank-distribution histograms (not temporal charts) demonstrating that in a
  100-question tournament with 300 contestants, the eventual winner is most likely to be around the
  100th-most-accurate contestant, not the 1st — short tournaments have large rank variance.
- **Applicability:** A direct methodological caveat for any chart that implies "the trend is going up,
  therefore skill." With ~54–90 matches and ~550–730 questions, this project's sample is meaningfully
  larger than Aldous's 100-question worked example, but the paper's core lesson — a rising cumulative
  line early in a small sample is not yet strong evidence of skill over luck — is directly relevant to
  how confidently any early-tournament chart should be captioned.

### 4. Atanasov, Witkowski, Ungar & Mellers (2020), "Superforecasting Reality Check," *Judgment and
Decision Making*, PMC7333631 — `BRIER_RANK_PRESENTATION_NOTES.md` Paper 9
- **What it shows:** Defines Net Brier Points exactly as this project's RBP: for each question, on each
  day, individual Brier score minus the mean of all active participants' Brier scores that day,
  accumulated across questions. Figure 2 is a histogram of "confirmed superforecasters per percentage
  bin" — a rank-distribution chart, not a temporal one.
- **Applicability:** Establishes that RBP is a published, peer-reviewed operationalization (not an
  invented metric), and that even the paper defining the closest published analogue to RBP chose a
  **histogram of the final distribution**, not a running-total line chart, as its primary visual —
  worth weighing against the instinct to always plot a cumulative line.

### 5. MacKay (2025), "Who Has the Best Probabilities? Luck versus Skill in Prediction Tournaments,"
arXiv:2509.08744 — **fetched and read in full for this task (13 pages); not in
`BRIER_RANK_PRESENTATION_NOTES.md`**
- **What it shows:** This is the single most structurally similar real paper found in this entire
  research pass: an informal, real, multi-year World Cup prediction tournament run by the University of
  York mathematics department, scored with the Brier score, exactly this project's genre. Figure 2 (page
  11) is titled "The evolution of forecaster average Brier scores over the matches of the 2010 FIFA
  World Cup finals": x-axis is **match number** (1 through 64, i.e. every match of the tournament, not
  calendar date), y-axis is **running/cumulative average Brier score per forecaster** (range roughly
  −0.7 to −0.2 in the figure, since MacKay's scores are negatively oriented), and each line is one
  forecaster's whole-tournament running average — roughly 15–20 overlapping lines in different colors
  and line styles (solid, dashed, dotted) on one axis. The paper's own reading of this figure: "most
  scores and differences stabilize [over the 64 matches], although some players are clearly inclined to
  gamble." The paper also derives, analytically, *how many questions it takes for skill to dominate
  luck*: with per-forecaster probabilities typically differing by about 0.1, it takes roughly 100
  questions before a one-standard-deviation separation between two forecasters' mean scores emerges
  (~16% chance the worse forecaster still wins by luck), and roughly 400 questions before that shrinks
  to a two-standard-deviation, 95%-confidence separation. The paper's own empirical read of the 2010
  World Cup tournament: the top 15–20 forecasters (of the real field) were separated by less than 0.1 in
  score and "could be ranked confidently only within… about 3–5 places either way."
- **Applicability — the most directly load-bearing finding in this entire research pass.** Two things
  transfer directly: (1) the chart type — running/cumulative average score vs. match number, one line
  per entity, is exactly the structural precedent for a cumulative-RBP-vs-match-number chart for this
  project's single campaign; (2) the sample-size math is a direct, quantitative answer to "how much
  should a chart's story be trusted at n≈54–90 matches" — MacKay's own worked tournament needed
  something like 100 questions (this project has ~550–730 question-level rows, well past that threshold,
  though only ~54–90 match-level observations, which is below it) before treating rank as more than
  noise. This is a genuine, citable, quantitative caveat to put in any chart's caption, not a vague
  "small sample" disclaimer. It's also a **cautionary visual precedent**: Figure 2's own ~15–20
  overlapping colored/dashed lines are hard to read as drawn — this is a real, published example of
  exactly the "too many series on one axis" anti-pattern that Bucket 4 (Cleveland, Tufte) below warns
  against, useful precisely because it shows what NOT to imitate even though the underlying axis choice
  (match number, running average) is sound. This project's chart has only one entity (its own campaign),
  so the specific overplotting failure doesn't recur here — but it is a reason not to add a second or
  third comparison line (e.g. "vs. the JTC crowd's own running average") without deliberately choosing
  a design that avoids Figure 2's clutter (see Bucket 4 sources on small multiples and Bucket 3's
  candidate designs).

### 6. Satopää et al. (2025), "ForecastBench," ICLR 2025 / arXiv:2409.19839 — `BRIER_RANK_PRESENTATION_NOTES.md` Paper 6
- **What it shows:** The most formally structured modern Brier-score leaderboard table (Model | N |
  Brier | 95% CI | p-value vs. top | % more accurate than #1), with human superforecasters and general
  public as reference rows. Figure 1 is a scatterplot of Brier score vs. an external metric with a trend
  line — not a temporal chart.
- **Applicability:** Reinforces that a table-plus-CI, not a chart, remains the modern standard for the
  primary "did it work" evidence in this literature; supports treating any RBP-over-time chart as a
  *secondary/supporting* visual, with the ledger table as primary, consistent with how
  `JTC_WC2026_Research_Paper.Rmd` already does it.

### Bucket 1 coverage assessment
**Strong**, built substantially on this repo's own prior work (`BRIER_RANK_PRESENTATION_NOTES.md`,
July 2026) plus one new paper (MacKay 2025) fetched and read in full for this task, which turned out to
be the single best structural and quantitative match found anywhere in this research pass. No paper
reviewed in either document was invented; every DOI/arXiv ID is real and was independently verified via
search and, for MacKay 2025, direct PDF fetch and page-by-page read.

---

## Bucket 2 — Quantitative finance: cumulative track-record and drawdown conventions

**Overall finding:** this is structurally the closest analogue to the RBP problem (signed, variable-
magnitude, sequential results), and this project has already deeply studied one canonical source
(Stefan Jansen's *Machine Learning for Trading*, local clone at `external_repos/machine-learning-for-
trading/`) — which turned out to contain real, in-repo plotting code directly relevant to this task,
found and read during this research pass.

### 7. `case_studies/utils/strategy_analysis.py` — this project's own local clone of the ML4T repo,
**read directly, not summarized secondhand**
- **What it contains:** `plot_sharpe_waterfall()` (lines 522–718) is a bar chart of a strategy's Sharpe
  ratio through successive pipeline stages (signal → allocation → costs → risk overlay), color-coded by
  sign of the stage-over-stage delta: the first bar is neutral blue (`#2196F3`), each subsequent bar is
  green (`#4CAF50`) if it improved over the previous stage or red (`#F44336`) if it degraded, with a
  dashed zero-reference line (`ax.axhline(0, ...)`), delta annotations between bars, and bootstrap-CI
  error bars drawn only when the CI actually brackets the point estimate (a real, in-code discipline
  against showing a stale/misleading CI). `plot_concentration_curve()` and `plot_cost_decay()` in the
  same file use `ax.fill_between(..., alpha=0.1, ...)` to shade the area under a line — a lightweight,
  low-data-ink way of showing magnitude without adding a second geometric element.
- **A concrete, checkable example of "principled, not a magic number."** The y-axis padding in
  `plot_sharpe_waterfall` is computed as `pad = max(span * 0.18, 0.15)` where `span` is the actual
  data's min-to-max range — i.e. the padding is a function of the observed data, not a fixed pixel or
  axis-limit constant, so it never clips a real value and never leaves excessive dead space regardless
  of the input's scale. This is a genuine in-repo example of what "not a magic number" means in
  practice: a parameter derived from the data being plotted, with a stated floor, rather than a bare
  constant chosen by eyeballing one instance of the chart.
- **A concrete, honest counter-finding.** This same file's sign-coding uses red/green hex codes
  (`#F44336` / `#4CAF50`) — precisely the color pair Bucket 4's colorblind-safety sources (below) flag
  as the single worst-case choice for red-green color vision deficiency, which affects roughly 8% of
  men. This project has already studied and could structurally imitate this exact chart type (a
  waterfall/sign-coded bar chart) for a per-match RBP chart — but should not copy its color choice
  without modification; a colorblind-safe diverging pair (Bucket 4) is a direct, low-cost substitute for
  the same visual structure.
- **Applicability:** The waterfall/sign-coded-bar-with-zero-line pattern is a strong structural
  candidate for a per-match RBP bar chart (each bar = one match's `match_rbp_total`, colored by sign,
  ordered by date, zero-reference line). The data-derived-padding convention is directly reusable
  guidance for any axis-limit decision in a future RBP chart.

### 8. pyfolio (Quantopian), `pyfolio/plotting.py` — verified via GitHub source and API documentation
(https://github.com/quantopian/pyfolio/blob/master/pyfolio/plotting.py,
https://pyfolio.ml4trading.io/api-reference.html; not independently re-fetched line-by-line in this
pass, corroborated via search results quoting the module's own function names/docstrings)
- **What it shows:** The canonical open-source "tearsheet" convention for a trading strategy's track
  record: a cumulative-returns line chart (with an optional log-scale variant specifically added for
  strategies whose performance ranges are wide enough that a linear scale compresses the early history),
  paired with a **separate** `plot_drawdown_underwater()` panel directly below it — an "underwater"
  chart plotting current drawdown-from-peak vs. date, filled from zero down to the current value, so
  loss episodes read as shaded valleys rather than requiring the viewer to mentally subtract a running
  peak from a noisy line. Rolling-Sharpe and rolling-beta panels are separate small charts in the same
  tearsheet, not overlaid on the cumulative-return chart itself.
- **Applicability:** The cumulative-return-chart-plus-separate-underwater-panel pattern is a directly
  transferable two-panel design for RBP: a cumulative-RBP-over-time line on top, a "drawdown from
  running peak RBP" panel underneath — this decomposition avoids cramming both "how much have I made"
  and "how bad did my worst losing streak get" onto one axis, which a single line chart cannot show
  cleanly (a peak-to-trough drawdown is only legible against its own zero baseline, not against the
  cumulative line's own scale). Log-scale is not obviously transferable, since RBP (unlike returns) is
  signed and can cross zero, where log scales are undefined — noted as a real disanalogy, not silently
  papered over.

### 9. This project's own `writeups/docs/DOCUMENTATION_STANDARDS.md` §5, "CLV as the grading standard"
— already read in full as part of this project's existing research, not re-fetched
- **What it shows:** Professional sports-betting discipline: "grade every bet, every time — selective
  tracking introduces selection bias and breaks the metric," with Closing Line Value graded relative to
  the sharpest available market close, exactly analogous to RBP graded relative to the JTC crowd.
- **Applicability — a visualization-specific implication not stated in the original document.** This
  discipline has a direct plotting consequence: whatever chart gets built must plot **every** scored
  question or match in the ledger, not a curated subset (e.g., not "just the highlight wins"), or the
  chart itself becomes a selection-biased instrument in exactly the way the grading discipline was
  designed to prevent. This also argues for showing the full, unfiltered distribution (Bucket 3's
  reliability-diagram material and Bucket 5's clustering-aware options) rather than only headline
  numbers.

### 10. Retail trading-journal convention (TradesViz, general trading-journal literature) — verified via
search, multiple corroborating sources on waterfall charts and P&L calendars for variable-stake trade
sequences; not a single canonical academic source, flagged as commercial/practitioner-tier evidence
- **What it shows:** Two real, named, widely-used chart types for exactly the "variable-magnitude,
  signed, sequential result" problem: a **trade-sequence waterfall chart** (each bar = one trade's
  effect on cumulative P&L, colored by sign) and a **P&L calendar** (a calendar grid, each cell shaded
  by that day's signed P&L magnitude) for revealing day-of-week or clustering patterns.
- **Applicability:** The waterfall chart corroborates source #7's `plot_sharpe_waterfall` pattern
  independently, from a completely different (retail-trading, not academic-quant) tradition — two
  unrelated fields converging on the same chart type for this data shape is itself evidence it's a
  sound default, not an idiosyncratic choice. The P&L calendar is a real precedent for a match-level
  heatmap-by-date, though it is a weaker fit here since this project's per-match cadence is irregular
  and tournament-structured (group stage → knockout), not daily/weekly like a trading calendar — flagged
  as an interesting but lower-priority option for that reason.

### Bucket 2 coverage assessment
**Strong**, and unusually direct: this bucket produced a real, already-in-repo, already-studied piece of
plotting code (source #7) rather than only external references, which is the strongest possible kind of
precedent for "not inventing anything" — it is verifiable by reading the file directly, which was done.

---

## Bucket 3 — Calibration and reliability diagrams (a different, complementary plot)

**Overall finding:** this is a well-established, rigorously citable literature, already partially
represented in this project's own `references.bib` (Murphy 1973, Dimitriadis/Gneiting/Jordan 2021), and
it answers a **different question** than a cumulative-RBP-over-time chart — calibration asks "when I say
60%, does it happen 60% of the time?", pooled across all questions regardless of when they occurred;
cumulative RBP asks "did the scored total go up or down, and when?" Both are legitimate, complementary,
and should not be conflated into one chart.

### 11. Murphy (1973), "A New Vector Partition of the Probability Score," *Journal of Applied
Meteorology* 12(4) — already cited in `references.bib`; construction verified via search of secondary
sources quoting the original (direct AMS journal fetch not attempted, paywalled)
- **What it shows:** The classic three-term decomposition of the (negatively oriented) Brier score into
  uncertainty (unavoidable, determined by the base rate of the event), resolution (how much the
  forecast's bins differ from the overall base rate — more bins can increase this), and reliability (how
  close each bin's forecast probability is to that bin's observed frequency). The reliability diagram
  plots observed frequency (y-axis) against forecast probability (x-axis) for each bin, with the 45°
  diagonal as the ideal-reliability reference; the diagram becomes an "attributes diagram" when a
  no-skill line (drawn halfway between the climatology line and the diagonal) and a no-resolution
  (horizontal, climatology-frequency) line are added, and the sample count per bin is typically shown as
  an inset histogram to convey sharpness alongside reliability.
- **Applicability:** This is the standard, decades-old visual for testing calibration specifically — a
  genuinely different plot from a time-ordered RBP chart. This project's own prior work (per the task
  brief) already found that calibration, not raw accuracy, is what the proper scoring rule actually
  rewards — this diagram is the standard way to show that finding visually, using `our_estimate` binned
  against realized `outcome`, independent of match date or RBP.

### 12. Dimitriadis, Gneiting & Jordan (2021), "Stable Reliability Diagrams for Probabilistic
Classifiers," *PNAS* 118(8) — already cited in `references.bib`; fetched via PMC7923594 and read
- **What it shows:** A direct, modern fix for exactly the "magic numbers" problem the user is worried
  about, applied to reliability diagrams specifically: the traditional approach requires choosing a
  number of bins (e.g. 9, 10, or 11 equal-width bins), and the paper demonstrates this choice alone
  "yield[s] drastically distinct reliability diagrams" from the same data — i.e., the standard method's
  bin count is a literal magic number with a materially different visual result depending on the
  arbitrary choice. Their CORP method (Consistent, Optimally binned, Reproducible, via the Pool-Adjacent-
  Violators/isotonic-regression algorithm) replaces manual binning with an automatically-determined
  monotone step function fit to the data, plus two distinct uncertainty bands: **consistency bands**
  (drawn around the diagonal, showing the spread expected under perfect calibration) and **confidence
  bands** (drawn around the fitted curve itself, a classical interval on the estimate).
- **Applicability:** This is the single most directly relevant source in this entire research pass for
  the user's explicit "no magic numbers" instruction, because it is a peer-reviewed, PNAS-published
  demonstration that an arbitrary bin-count choice (exactly the kind of unjustified numeric parameter
  the user is worried about) materially changes a chart's story — and it proposes a principled,
  parameter-free alternative. If this project ever builds a calibration/reliability diagram (a
  complementary chart to the RBP-over-time chart discussed in the synthesis below), CORP-style isotonic
  binning is the citable, principled alternative to picking an arbitrary bin width by eye.

### 13. Bröcker & Smith (2007), "Increasing the Reliability of Reliability Diagrams," *Weather and
Forecasting* 22(3) — verified via search (AMS journals listing); not independently re-fetched in full,
flagged as search-corroborated
- **What it shows:** An earlier, resampling-based method for adding consistency bars/bands to a
  traditional binned reliability diagram, addressing the same instability problem CORP later solved more
  formally.
- **Applicability:** Establishes that "a reliability diagram needs an uncertainty band to be trustworthy"
  is not a novel idea invented for this project but a two-decade-old, named concern in the meteorological
  verification literature — reinforces that a reliability diagram without any uncertainty band (a bare
  scatter of points on a diagonal) would itself be under-specified by this literature's own standards.

### Bucket 3 coverage assessment
**Strong.** Both core citations were already present in this project's own `references.bib` before this
research began — this bucket mainly deepened what those citations actually show visually (their figures
and specific method names), rather than discovering new sources from scratch.

---

## Bucket 4 — General visualization principles: avoiding "AI-sloppy," unjustified chart design

### 14. Tufte (1983), *The Visual Display of Quantitative Information* — data-ink ratio / chartjunk;
verified via multiple corroborating secondary sources (the concept is extremely widely and consistently
described; direct access to the out-of-print original book was not attempted in this pass)
- **What it shows:** Defines "data-ink" as the non-erasable, non-redundant ink that actually represents
  data values, the data-ink ratio as data-ink divided by total ink used, and "chartjunk" as any ink that
  conveys no new information (decorative borders, unnecessary gridlines, redundant labels, 3D bevel
  effects on 2D data). The prescriptive rule: maximize the data-ink ratio by erasing non-data-ink first,
  then erasing redundant data-ink.
- **Applicability:** Directly actionable for an RBP chart: no 3D bar effects, no drop shadows, no
  redundant "RBP: +X" label repeated both as a bar height and a printed number and a legend entry, no
  background gridlines heavier than needed to read a value approximately. This is the most direct,
  concrete antidote to what the user called "AI sloppy design."

### 15. Cleveland & McGill (1984), "Graphical Perception: Theory, Experimentation, and Application to
the Development of Graphical Methods," *JASA* 79(387) — verified via multiple sources including a
publicly hosted course PDF (faculty.washington.edu/aragon/classes/hcde511/s12/readings/cleveland84.pdf);
not independently re-fetched in full in this pass, but the core ranking is consistently and precisely
reported across every source found
- **What it shows:** An empirically validated ranking of "elementary perceptual tasks" by how accurately
  humans judge them from a graphic, from best to worst: **position along a common scale** (e.g. a dot's
  height on a shared y-axis) and **position along identical, non-aligned scales** rank highest; **length**
  (e.g. bar height, when bars share a common baseline) ranks second; **angle/slope** third; **area**
  fourth; **volume, curvature, and shading/color saturation** rank worst.
- **Applicability — this is the concrete, citable basis for choosing bar/line encodings over pie/area/
  bubble encodings for RBP data.** A per-match RBP value is a single signed magnitude best shown as
  **position/length on a common numeric scale** (a bar from a shared zero baseline, or a point's height
  on a shared y-axis) — both top-ranked tasks per this research. This directly rules out a bubble chart
  (area judgments, ranked near the bottom) or a pie/donut framing of "win rate" (angle judgments, ranked
  third) as inferior encodings for the *magnitude* of RBP specifically, even though a win/loss binary
  count could reasonably use a simpler chart.

### 16. Cleveland (1993), *Visualizing Data* — Trellis displays / small multiples; and Tufte (1990),
*Envisioning Information* — small multiples chapter; both verified via multiple corroborating sources
(Wikipedia's "Small multiple" article, Pew Research's own explainer of their small-multiples convention,
InfoVis:Wiki); primary texts not independently re-fetched, but the concept and its authorship attribution
are consistent and well-corroborated across sources
- **What it shows:** A small-multiples (a.k.a. trellis, lattice, panel, or facet) display repeats the
  same chart form across an array of panels sharing identical axes/scales, varying only one dimension
  (e.g. one panel per category, per time period, per group) — enabling direct visual comparison without
  requiring the viewer to mentally overlay differently-scaled charts. Cleveland's own Trellis graphics
  (implemented later as `lattice`/`ggplot2::facet_wrap` in R) is the software realization of this
  principle specifically for statistical/panel data.
- **Applicability:** This is the most directly relevant principle for the non-independence finding in
  Bucket 5 below — faceting per match (small multiples, one tiny panel per match, each showing that
  match's ~15 question-level RBP values) is a citable, principled way to show question-level detail
  *without* implying question-level statistical independence the way one long unbroken per-question
  scatter across the whole campaign would.

### 17. Okabe & Ito (2008), "Color Universal Design" — verified via multiple corroborating sources
quoting the exact eight hex values; the original CUD organization page was not independently re-fetched
in this pass, but the palette and its values are extremely widely and consistently reproduced
- **What it shows:** An eight-color palette designed to remain distinguishable under the most common
  forms of color vision deficiency: black `#000000`, orange `#E69F00`, sky blue `#56B4E9`, bluish green
  `#009E73`, yellow `#F0E442`, blue `#0072B2`, vermillion `#D55E00`, reddish purple `#CC79A7`.
- **Applicability:** A direct, named, checkable alternative to the red/green sign-coding this project's
  own studied ML4T-derived code already uses (Bucket 2, source #7). Blue (`#0072B2`) for "beat crowd" /
  vermillion (`#D55E00`) for "lost to crowd" is a same-structure, colorblind-safe substitute for the
  green/red pair, using two colors already in this named, citable palette.

### 18. ColorBrewer diverging palettes — verified via multiple corroborating sources describing the
tool's own colorblind-safety flags (colorbrewer2.org itself was not independently re-fetched in this
pass; its safety classifications are consistently reported across every corroborating source found)
- **What it shows:** Of ColorBrewer's diverging palettes, six are explicitly flagged colorblind-safe:
  `PuOr` (purple–orange), `BrBG` (brown–blue-green), `PiYG`, `PRGn`, `RdBu`, and one more in that family;
  `RdGy`, `RdYlGn`, and `Spectral` are explicitly **not** colorblind-safe (the latter two both route
  through green, the exact hue confusable with red under the most common color vision deficiency).
- **Applicability:** For a diverging (win-vs-loss, or positive-vs-negative RBP) color scale rather than
  two discrete categorical colors, `PuOr` or `RdBu` are the principled, named, citable choices — `PuOr`
  in particular converges structurally with Okabe-Ito's orange/blue pair (source #17), so orange-vs-blue
  is a color choice independently supported by two different named, citable, colorblind-safety-vetted
  systems, not an arbitrary substitute for red/green.

### 19. viridis — perceptually uniform sequential colormap; verified via CRAN package documentation and
multiple corroborating sources
- **What it shows:** A sequential (not diverging) colormap running dark purple → blue → green → bright
  yellow, engineered so that perceived brightness changes linearly with the underlying data value (unlike
  the default "jet"/rainbow colormap, which has perceptual discontinuities), and verified colorblind-safe
  and safe when printed in grayscale.
- **Applicability:** Lower priority for this project's core RBP data, since RBP is inherently signed/
  diverging (needs a diverging, not sequential, palette) — but directly applicable if a *magnitude-only*
  auxiliary encoding is needed (e.g. shading match-level "stakes" or sample-size/confidence by intensity
  in a small-multiples panel), where a sequential, perceptually uniform scale would be the principled
  choice over an arbitrary custom gradient.

### Bucket 4 coverage assessment
**Strong**, with every named framework/author real and independently corroborated across at least two to
three sources each, consistent with this project's own established practice (per
`DOCUMENTATION_RESEARCH.md`, `PROJECT_STRUCTURE_RESEARCH_2026-07-14.md`) of disclosing when a primary
text itself wasn't directly re-fetched and content was instead corroborated via multiple independent
secondary sources.

---

## Bucket 5 — Visualizing clustered/non-independent panel data (the question-in-match problem)

**Overall finding:** this project's own prior statistical work already discovered the underlying
problem empirically; the visualization literature has a well-established, directly named answer.

### 20. This project's own `STATSBOMB_INTEGRATION_AND_STATS_TESTS_2026-07-08.md` §6 — already read in
full as part of this task, not re-derived
- **What it found:** A Welch's t-test on "does deviating from the crowd predict RBP?" gives the
  **opposite sign** depending on whether it's run naively at the question level (n=771 in that session's
  dataset, treating each question as independent) versus correctly at the match level (n=71, aggregating
  each match to one row first, the truly independent unit since ~15 questions per match share context).
  The match-level, correct-unit version is the one that agrees with an independent regression's finding.
- **Applicability — the visualization-specific consequence.** If a statistical test gives the wrong-sign
  answer when run at the wrong unit of analysis, a **chart** built at the wrong unit of analysis carries
  exactly the same risk: a bare per-question scatter plot across the whole campaign (549 points) would
  visually imply 549 independent draws in the same way the naive t-test statistically assumed 549
  independent observations — and a viewer could just as easily eyeball a misleading trend from it. This
  is the specific reason the candidate designs in the synthesis below either aggregate to the match level
  before plotting, or explicitly facet by match rather than pooling all questions onto one shared axis.

### 21. Diggle, Heagerty, Liang & Zeger, *Analysis of Longitudinal Data* (2nd ed., Oxford University
Press, 2002) — the standard reference text for repeated-measures/clustered visualization; verified via
search, not independently re-fetched (a textbook, not an open-access paper)
- **What it shows:** The standard first visual for repeated/clustered measurements grouped by subject is
  the "spaghetti plot" — one line per subject/cluster, outcome on the y-axis, time (or an ordered index)
  on the x-axis — explicitly recommended as a first diagnostic specifically *because* it keeps each
  cluster's internal structure visible rather than pooling all observations onto one undifferentiated
  scatter.
- **Applicability:** Directly names the "per-match line/group" pattern as a recognized solution, not an
  ad hoc invention — a match's ~15 questions plotted as their own small connected sequence (one segment
  per match) rather than merged indiscriminately into one long question-level timeline is exactly this
  convention, applied to this project's own match-clustered RBP data.

### 22. Swihart, Caffo, James, Strand, Schwartz & Punjabi (2010), "Lasagna Plots: A Saucy Alternative to
Spaghetti Plots," *Epidemiology* 21(5), PubMed 20699681 — verified via PubMed listing; abstract-level
content, not independently re-fetched in full
- **What it shows:** A named, real, peer-reviewed alternative to the spaghetti plot for the exact failure
  mode source #21 doesn't solve: when there are many clusters (many lines), a spaghetti plot over-plots
  and becomes unreadable — precisely the failure visible in MacKay's own Figure 2 (Bucket 1, source #5).
  The lasagna-plot fix reorganizes the same data into a heatmap-like grid (one row per subject/cluster,
  color intensity encoding the outcome value, time along the x-axis), trading line-shape legibility for
  scalability to many clusters.
- **Applicability:** Not the first choice for this project (its per-match cluster count, ~54–90, is
  large enough that a full spaghetti-per-match chart would already be crowded, but small enough that
  Bucket 4's small-multiples/faceting approach — many small separate panels rather than one dense
  heatmap — is likely more legible for a human audience than a lasagna-style heatmap, which reads more
  cleanly at hundreds-to-thousands of rows). Flagged as a real, named, available option if the campaign
  eventually grows to many more matches and a small-multiples grid becomes too large to scan.

### Bucket 5 coverage assessment
**Strong on the diagnosis (this project's own prior statistical work), moderate on breadth of external
sources** — the core citation (Diggle et al.) is a standard, real textbook rather than an open-access
paper, so its content here is summarized from its well-established, widely-taught reputation rather than
a direct fetch; this is disclosed rather than presented as a first-hand read.

---

## Bucket 6 — Real-world forecasting-tournament dashboards and track-record visualizations

### 23. Metaculus public Track Record page — https://www.metaculus.com/questions/track-record/ — already
partially documented in this project's own `DOCUMENTATION_RESEARCH.md` (source #6, fetched via a
reader-proxy fallback after a direct HTTP 403); **re-attempted in this pass via the same reader-proxy
route, with a materially weaker result**
- **What was recovered this time:** The page's summary statistics panel ("36.13 average baseline score,"
  "4,050,568 total predictions," "18,659 questions predicted," "11,963 questions scored") came through
  cleanly. The three chart sections — Calibration Curve, Score Scatter Plot, Score Histogram — were
  confirmed to exist as page sections by heading text, but the reader-proxy fetch did **not** return
  enough of the page's rendered chart markup to describe axis definitions, binning, or point-encoding in
  first-hand detail this time (the earlier `DOCUMENTATION_RESEARCH.md` pass reported the same three-chart
  structure with similarly limited technical detail — the specific axis/binning mechanics of Metaculus's
  own charts have not been independently verified in either research pass, and this is disclosed rather
  than inferred). **Access limitation, disclosed honestly rather than papered over.**
- **Applicability:** The three-chart-type combination itself (calibration curve + a per-question score
  scatter + a score-distribution histogram) is confirmed as real and is the most reusable *structural*
  pattern found among real public forecasting dashboards — a calibration curve for the Bucket 3 question,
  a scatter/histogram for the distribution-of-results question — even though the fine encoding details
  of Metaculus's specific implementation remain unverified.

### 24. MacKay's own York World Cup tournament writeup (Bucket 1, source #5) — doubles as a real-world
example, not just an academic citation
- **What it shows:** A genuine, small-scale, real forecasting-tournament dashboard equivalent — one
  academic's own multi-year, informally-run World Cup prediction pool, complete with a "we switched from
  Brier score to log score after 2014" methodological revision documented in the same paper.
- **Applicability:** Evidence that even a small, informal, single-department tournament (comparable in
  spirit to a solo campaign like this project's) produces a citable, published track-record chart — this
  project's own eventual chart has real precedent even at a modest, non-institutional scale.

### 25. Good Judgment Open / Good Judgment Inc. public materials — https://www.gjopen.com/,
https://goodjudgment.com/resources/the-superforecasters-track-record/ — **search-level access only in
this pass; direct fetch of a chart-bearing page was not successful**
- **What was found:** Confirmation that Good Judgment publishes track-record materials and an
  "Analytics" page referencing calibration information, and the previously-verified Good Judgment
  white-paper content already documented in this project's own `DOCUMENTATION_RESEARCH.md` (source #5:
  calibration curves reported across 323 resolved questions 2016–2021, with lead-time-before-resolution
  as an added dimension). No new chart-level detail beyond what that existing document already recorded
  was obtained in this pass. **Flagged as a non-outcome rather than silently omitted.**

### 26. FiveThirtyEight forecast-tracking visualizations — cross-referenced from this project's own
`DOCUMENTATION_RESEARCH.md` (source #9), not re-attempted in this pass
- **What is already known and documented:** The live methodology/tracking pages are dead (301-redirect
  to ABC News politics as of the prior research pass); the GitHub `soccer-spi` data README survives and
  is a data-dictionary exemplar, not a chart exemplar. Not re-investigated here since the prior finding
  already fully disclosed the access failure and there was no new angle to pursue for chart-specific
  content.

### Bucket 6 coverage assessment
**Moderate**, and this is stated plainly rather than dressed up: the two most promising real-world
dashboard precedents (Metaculus, Good Judgment) both resisted a full first-hand technical read in this
pass, for the same reasons already encountered in this project's own prior research (bot-blocking,
HTTP 403s). What is solidly confirmed is the *category* of chart each uses (calibration curve, score
scatter, score histogram for Metaculus; calibration curve plus lead-time framing for Good Judgment) —
useful for Bucket 3's calibration-diagram case, less useful for the cumulative-RBP-over-time question
this document is centrally about, where Bucket 1's MacKay (2025) paper and Bucket 2's quant-finance
sources are the strongest evidence found.

---

## Synthesis — Candidate chart designs (options, not a recommendation)

Every design below is stated with its required data aggregation, which design choices are principled
(with the specific source backing each choice), and honest tradeoffs. None is picked as a winner, per
the brief.

### Candidate A — Cumulative RBP-over-match-number line chart with an underwater drawdown panel
**What it is:** Two stacked panels sharing an x-axis of match number (ordered chronologically, not
calendar date — see the design-choice note below). Top panel: a single line of cumulative RBP
(running sum of `match_rbp_total`), with markers at each match. Bottom panel: an "underwater" chart —
current value minus running peak-to-date — shaded from zero down to the current drawdown, so losing
streaks read as visually distinct valleys.
- **Data aggregation required:** One row per match (`match_rbp_total`, already present in
  `questions_flat.csv`), cumulatively summed in match order; a running maximum computed from the same
  series for the drawdown panel. No question-level data needed.
- **Principled choices, with sourcing:**
  - *Match number, not calendar date, as the x-axis* — directly follows MacKay (2025) Figure 2's own
    choice (Bucket 1, source #5) and avoids visually compressing the group stage (many matches in a
    short calendar window) against the more sparsely-spaced knockout rounds, which a calendar-date axis
    would do.
  - *Match-level, not question-level, unit* — directly required by this project's own non-independence
    finding (Bucket 5, source #20); plotting at the question level here would repeat the exact mistake
    the naive t-test made.
  - *Two stacked panels rather than one overlaid chart* — follows the pyfolio tearsheet convention
    (Bucket 2, source #8) of separating cumulative performance from drawdown rather than cramming both
    onto one axis.
  - *Zero-reference line, minimal chartjunk* — Tufte's data-ink principle (Bucket 4, source #14).
- **Honest tradeoffs:** A single cumulative line, by construction, cannot show the magnitude-variance
  finding this project has already documented (large crowd-deviations are a higher-variance bet, per
  `STATSBOMB_INTEGRATION_AND_STATS_TESTS_2026-07-08.md` §6) — a smooth-looking upward line can hide the
  fact that a small number of very large single-match results (e.g. the −80.83 and +179.26 matches cited
  in the flagship paper) are doing most of the work, which Candidate B below shows directly and this one
  does not. Also inherits MacKay's own explicit caveat: at ~54–90 matches, this project is close to but
  arguably still below the ~100-match threshold his own paper derives for one-standard-deviation
  confidence in a rank/trend claim (Bucket 1, source #5) — any caption should say so rather than imply
  the upward trend is already statistically settled.

### Candidate B — Per-match RBP waterfall/sign-coded bar chart, ordered by date
**What it is:** One bar per match (`match_rbp_total`), ordered chronologically along the x-axis, height
equal to that match's RBP, colored by sign, with a dashed zero-reference line, optionally annotated at
named notable events already documented in this project (e.g. the campaign's largest single-match
positive and negative results).
- **Data aggregation required:** One row per match — identical aggregation to Candidate A's top panel,
  but plotted as discrete bars instead of a cumulative running line.
- **Principled choices, with sourcing:**
  - *Bar height (position/length along a common baseline), not bubble area or color intensity alone,
    for encoding RBP magnitude* — directly follows Cleveland & McGill's ranking of perceptual tasks
    (Bucket 4, source #15): length-from-a-common-baseline is the second-most-accurately-judged encoding,
    well above area or angle.
  - *Structural precedent, not invented* — this is the same chart shape as this project's own already-
    studied `plot_sharpe_waterfall()` (Bucket 2, source #7) and the independently-converging retail-
    trading waterfall-chart convention (Bucket 2, source #10) — two unrelated fields landing on the same
    design for the same data shape.
  - *Colorblind-safe diverging sign-coding* — Okabe-Ito blue/vermillion or ColorBrewer's `PuOr`
    (Bucket 4, sources #17–18), explicitly chosen over the red/green pair this project's own studied
    reference code actually uses, and explicitly justified by naming which color-vision-deficiency
    literature the substitution addresses.
  - *Annotate, don't caption-dump* — Tufte's data-ink principle argues for sparse, targeted annotation
    of only the named notable matches already documented elsewhere in this project (the flagship paper's
    own campaign-best/worst call-outs), rather than labeling every bar.
- **Honest tradeoffs:** With ~54–90 bars, this chart is denser than Candidate A's smooth line and will
  need either a wide aspect ratio or a rotated/scrollable x-axis to stay legible — a real space
  constraint, not a magic-number one, since the number of bars is fixed by the number of matches played,
  not a chosen bin width. It also does not show a running cumulative total directly (a viewer has to
  mentally sum the bars, or this chart needs to be paired with Candidate A rather than replace it) — this
  is the direct tradeoff Candidate A's cumulative line and this chart's discrete-event framing represent:
  cumulative-total legibility vs. per-event-magnitude legibility, and the literature reviewed here (both
  MacKay's line chart and this project's own waterfall precedent) suggests these are genuinely two
  different, complementary charts rather than one chart doing both jobs.

### Candidate C — Reliability/calibration diagram (a different chart, answering a different question)
**What it is:** `our_estimate` binned (via CORP/isotonic regression, not an arbitrarily chosen bin
count) against realized `outcome`, plotted as observed frequency vs. forecast probability with a 45°
diagonal reference and consistency/confidence bands, independent of match date or RBP.
- **Data aggregation required:** All 515+ question-level rows with a populated `our_estimate` and
  resolved `outcome` — this is the one candidate that legitimately needs the question level, not the
  match level, since calibration is a property of the probability-to-outcome mapping pooled across many
  independent probability judgments, not a property of any one match's total.
- **Principled choices, with sourcing:**
  - *CORP/isotonic-regression binning instead of a manually chosen bin count* — directly answers the
    user's "no magic numbers" brief, backed by Dimitriadis, Gneiting & Jordan's own PNAS demonstration
    that manual bin-count choice materially changes the diagram's story (Bucket 3, source #12).
  - *Consistency and confidence bands, not a bare point-and-diagonal plot* — backed by both the CORP
    paper and Bröcker & Smith (2007) (Bucket 3, sources #12–13), which together establish that an
    unbanded reliability diagram is under-specified by this literature's own two-decade standard.
  - *A genuinely different question from Candidates A/B* — this chart cannot show "did the campaign
    trend up or down," and A/B cannot show "am I well-calibrated" — both are real, complementary,
    literature-backed charts for different claims this project has already made (per the task brief's
    own framing and this project's prior calibration-focused work).
- **Honest tradeoffs:** Does not use the match-level clustering structure at all (Bucket 5's non-
  independence finding is specifically about RBP contributions within a match sharing context, which is
  a different concern from calibration of a probability judgment against its binary outcome — though a
  match-clustered standard-error correction on the bands themselves would be the fully rigorous version,
  not attempted by the sources reviewed here for this exact metric). Also the smallest-payoff candidate
  for the specific ask in this task (a "track record across all matches priced so far" chart) since it
  doesn't show the campaign's trajectory at all — included because the task brief explicitly asked for
  this to be researched as a distinct, complementary option, not because it substitutes for A or B.

### Candidate D — Small-multiples grid, one facet per match, each showing its ~15 question-level RBP values
**What it is:** A grid of small panels (Cleveland's Trellis/Tufte's small-multiples pattern), one panel
per match, sharing identical x/y scales, each panel showing that match's individual question-level RBP
values as points or a mini bar chart, so within-match variability and between-match totals are both
visible without pooling all 549 question-rows onto one undifferentiated axis.
- **Data aggregation required:** No aggregation — the full question-level dataset, but explicitly grouped
  by `match` rather than flattened, which is the entire point of this candidate.
- **Principled choices, with sourcing:**
  - *Faceting by match instead of a pooled per-question scatter* — the direct visualization-literature
    answer (Bucket 5, sources #21–22) to this project's own documented statistical finding that
    question-level RBP values are not independent within a match (Bucket 5, source #20) — this design
    is the one candidate here explicitly built to avoid implying false independence, which a flat
    per-question scatter plot would otherwise do just as the naive t-test did numerically.
  - *Shared, identical axes across all panels* — a defining requirement of small multiples per both
    Tufte and Cleveland (Bucket 4, source #16), so that panel-to-panel comparison is honest (a match with
    a taller bar in its panel really did score higher, not just get drawn at a different scale).
- **Honest tradeoffs:** At ~54–90 matches this is a genuinely large grid — even at a small per-panel
  size, this is the candidate most likely to require either a scrollable/paginated layout or a much
  larger canvas than the other three, and is the one design here explicitly flagged in Bucket 5 (source
  #22, the lasagna-plot paper) as the point at which a heatmap-style alternative starts to out-perform a
  literal small-multiples grid for legibility. It also does not, by itself, show a single cumulative
  headline number the way Candidate A does — it is the richest candidate for auditing individual matches
  but the weakest for a single "at a glance, is the campaign net positive" answer, which is the opposite
  tradeoff profile from Candidate A.

None of these four candidates is mutually exclusive with the others — A and B in particular are the same
underlying match-level data shown two ways (cumulative vs. discrete), and C and D both answer questions
A/B cannot. Per the brief, no candidate is selected here; this is left as an open decision for whichever
follow-up conversation actually builds the chart.

---

## What to avoid (synthesized across all six buckets)

- **Don't plot at the question level without either aggregating to the match level first or faceting by
  match** — this project's own statistical work already showed the wrong-unit-of-analysis mistake flips
  a real result's sign (Bucket 5, source #20); a chart built the same wrong way carries the same risk.
- **Don't pick a reliability-diagram bin count by eye** — Dimitriadis, Gneiting & Jordan's own PNAS paper
  demonstrates that this exact kind of arbitrary choice changes the diagram's conclusion (Bucket 3,
  source #12); use isotonic/CORP-style binning or explicitly justify a fixed bin count against it.
- **Don't reuse red/green sign-coding without checking colorblind-safety** — this project's own already-
  studied reference code does exactly this (Bucket 2, source #7), and the same visual structure is
  available with a colorblind-safe substitute already named and hex-coded in two independent, real
  systems (Bucket 4, sources #17–18).
- **Don't cherry-pick which matches/questions appear in the chart** — the CLV "grade every bet, every
  time" discipline this project has already adopted elsewhere (Bucket 2, source #9) applies exactly the
  same way to a chart: a chart of only the highlight results would be a selection-biased instrument, not
  an honest track record.
- **Don't imply statistical confidence in a trend that the sample size doesn't yet support** — MacKay's
  own analytical derivation (Bucket 1, source #5) gives a concrete, citable answer for how many questions
  are needed before luck is confidently distinguishable from skill; a chart caption claiming more
  certainty than that threshold supports would overstate the evidence.
- **Don't add chartjunk (3D effects, redundant labels, unnecessary gridlines, decorative bevels)** —
  Tufte's data-ink principle (Bucket 4, source #14) is the most literal, direct antidote to what the user
  called "AI sloppy design," and is easy to violate by accident with default settings in most plotting
  libraries.

---

## Notes on access limitations encountered during this research

- **Metaculus's Track Record page** (Bucket 6, source #23) again resisted a full first-hand technical
  read of its charts' axis/binning mechanics via the same reader-proxy fallback that partially worked in
  this project's earlier `DOCUMENTATION_RESEARCH.md` pass — the page's summary-statistics panel came
  through cleanly both times, but neither pass obtained enough rendered chart markup to describe the
  calibration curve's binning method or the scatter plot's point-encoding with full confidence. This is
  disclosed rather than inferred or invented.
- **Good Judgment Open / Good Judgment Inc.'s chart-bearing pages** (Bucket 6, source #25) were not
  successfully fetched at the chart level in this pass; only search-level confirmation that such
  materials exist was obtained. The previously-verified Good Judgment white-paper content already in
  `DOCUMENTATION_RESEARCH.md` remains the strongest first-hand evidence this project has for that
  organization's calibration-reporting conventions.
- **Murphy (1973)** (Bucket 3, source #11) is paywalled at its original AMS journal location; this
  document's description of the reliability/attributes diagram is built from multiple independent,
  consistent secondary sources describing the construction directly, not from a first-hand read of the
  original 1973 text.
- **Tufte's original books** (*The Visual Display of Quantitative Information*, 1983; *Envisioning
  Information*, 1990) and **Cleveland's original books/paper** (*The Elements of Graphing Data*, 1985;
  *Visualizing Data*, 1993; Cleveland & McGill 1984) were not independently re-fetched in full in this
  pass (several are out-of-print books, not open-access documents); their content here is drawn from
  multiple mutually-corroborating secondary sources that consistently and specifically describe the same
  named concepts, rankings, and terminology, which is the same standard of care this project's own prior
  research documents (`DOCUMENTATION_RESEARCH.md`, `PROJECT_STRUCTURE_RESEARCH_2026-07-14.md`) already
  apply when a primary source resists direct fetch.
- **Okabe & Ito's original Color Universal Design materials** and **ColorBrewer's own site** were
  likewise not independently re-fetched; their specific hex values and colorblind-safety classifications
  were cross-checked across multiple independent secondary sources rather than taken from a single
  quote, since a wrong hex code would be a concrete, checkable error rather than a matter of
  interpretation.
- No source in any bucket above was invented; every named paper, book, or tool has a real, checkable
  citation or URL, and every access limitation is disclosed at the point where it was encountered rather
  than smoothed over.
