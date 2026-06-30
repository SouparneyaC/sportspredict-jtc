# Documentation Research: How to Write Up the JTC / SportsPredict Forecasting Project

**Purpose of this document.** The user has built a multi-week, capstone-scale solo research operation around the "JTC" (Jump Probability Cup) forecasting tournament on play.sportspredict.com: Dixon-Coles bivariate Poisson models, Negative Binomial dispersion fits, ordered logit, Elo, a literature review of ~8 academic papers, a crowd-bias model with codified "rules," a market-edge/backtest pipeline, an ML feature-matrix layer, and a tracked RBP ledger across ~14+ matches. They want to circulate a polished writeup to a mixed audience — forecasting-community people, ML/quant-portfolio viewers, and sports-analytics people — and need a credible document structure.

This research surveys **real, fetched exemplars** (not invented examples) across four buckets: (1) academic capstone/portfolio writeups, (2) forecasting-community writeups, (3) sports-analytics methodology writeups, and (4) data engineering/provenance documentation. Every example below was actually retrieved via web search and/or page fetch. Where a fetch failed or a source has gone offline, this is stated explicitly rather than papered over.

---

## Bucket 1 — Academic-caliber capstone/portfolio writeups

**Overall finding: weak-to-moderate real coverage.** Specific, public, fully-detailed sports-forecasting capstone reports from top MIDS/MS-ADS programs are rare to find with working public links — most capstone "final deliverables" are landing pages that route to an external site, and many cohorts' work is taken down after a year or two. Stanford CS229 course-project PDFs, by contrast, are reliably public and a very good structural match. I substitute a real, verified CMU undergraduate stats capstone for the "top stats program" slot, since it directly hits World Cup soccer + Poisson regression.

### 1. "Predicting the Next Pitch" — UC Berkeley MIDS Capstone (2015)
- **Authors/institution:** Zach Beaver, Jason Goodman, Josh Lu, Alan Si — UC Berkeley School of Information, Master of Information and Data Science (MIDS) program.
- **URLs (both verified, fetched):**
  - Landing/index page: https://www.ischool.berkeley.edu/projects/2015/predicting-next-pitch
  - Full writeup site: https://pitchprediction.wordpress.com/about/ (plus sibling pages: Home, The Problem, The Solution, The Data, The Science, The Future)
- **Structure:** This capstone's "final deliverable" is **not a single PDF report** but a multi-page **micro-site** with dedicated pages: Home → The Problem → The Solution → The Data → The Science → The Future. The Berkeley i-School index page itself is a thin stub (banner image, team names, one-paragraph description, outbound link) — confirms that Berkeley's public capstone gallery often does NOT host the substantive report itself.
- **Length/format:** Six short web pages, each a few paragraphs to ~1 screen; cumulative length roughly equivalent to a 3–5 page report, but delivered as a structured website rather than a PDF.
- **Distinctive content:** "The Solution" page reports a quantified, validated result — "+5.3% mean accuracy improvement over baseline, with 4.5% standard deviation across 50 sampled pitchers" — and shows per-pitcher performance variation in a table/histogram, i.e., it documents heterogeneity of model performance rather than a single headline accuracy number. "The Science" page cites prior academic work on pitch-sequencing as grounding.
- **Tone:** Professional but accessible; deliberately speaks to a "front office / coaching" audience rather than a purely academic one, which is structurally similar to what this user needs (mixed audience).
- **Lesson:** A clean, navigable multi-page site with a problem→data→method→results→future-work arc is a legitimate, precedented capstone format — not just a single linear document. This matches the "post publicly" goal well, though the actual JTC writeup should likely still be one long document given the audience also includes recruiters/admissions who want one shareable artifact (PDF/long-form blog).

### 2. "Predicting Soccer Results in the English Premier League" — Stanford CS229 (2014)
- **Authors:** Ben Ulmer, Matt Fernandez — Stanford CS229 (Machine Learning) course project.
- **URL (fetched in full):** https://cs229.stanford.edu/proj2014/Ben%20Ulmer,%20Matt%20Fernandez,%20Predicting%20Soccer%20Results%20in%20the%20English%20Premier%20League.pdf
- **Structure (verified, in order):** Abstract → Introduction (with embedded "Related Literature" subsection) → Dataset → Methodology (Initial Challenges → Feature Selection → Models, 6 sub-models) → Results → Future Work → Acknowledgment → References.
- **Length/format:** 5 pages, single PDF, standard two-column NeurIPS-style academic format.
- **Methods:** SGD, Gaussian/Multinomial Naive Bayes, Hidden Markov Models, SVM (RBF + linear kernels), Random Forest, one-vs-all classification.
- **Validation:** Yes — k-fold (k=5) cross-validation with grid search for hyperparameters, explicitly named as a section.
- **Distinctive content:** Opens with a humorous, self-aware framing device (a reference to "Paul the Octopus," the World-Cup-prediction octopus) before pivoting to rigorous methodology — shows that a light, human opening is compatible with a fully rigorous academic body. Explicitly states when a model "performed very poorly" rather than hiding negative results.
- **Limitations:** No dedicated limitations section, but data-availability constraints are discussed inline ("Initial Challenges").
- **Tone:** Academic but self-reflective/honest about failures — directly useful tonal model for a solo researcher's writeup.

### 3. "Beating the Bookies: Predicting the Outcome of Soccer Games" — Stanford CS229 (2016)
- **Author:** Steffen Smolka — Stanford CS229 course project.
- **URL (fetched in full):** https://cs229.stanford.edu/proj2016/report/Smolka-BeatingTheBookies-report.pdf
- **Structure (verified, in order):** Introduction → Related Work → Data Set and Computed Features → Methods → Experiments and Results → Conclusion → References.
- **Length/format:** 5 pages, single PDF, same CS229 two-column template.
- **Methods:** SVM with RBF kernel; neural network with softmax output; SGD training.
- **Validation:** Initially used an 85/15 single-season train/test split, then explicitly **upgraded to 10-fold cross-validation** after recognizing the first approach was methodologically weak — and the report says so directly. This kind of "we did it wrong first, here's why, here's the fix" transparency is a strong model for a self-taught researcher's writeup.
- **Literature review:** Yes — a "Related Work" section distinguishing goal-based modeling (Rue & Salvesen, Karlis et al., Dixon-Coles lineage) from result-based classification approaches (Joseph et al., Constantinou).
- **Limitations:** No dedicated section, but the paper is candid that using only past-outcome features ("nothing but the outcome of previous games") produced weak signal.
- **Tone:** Academic yet conversational; explicitly admits experimental setbacks.

### 4. "36-460: World Cup Fan Base Impacts" — Carnegie Mellon University Statistics & Data Science Capstone Showcase (Spring 2025)
- **Institution:** CMU Department of Statistics & Data Science, undergraduate Sports Analytics Capstone (36-460/660).
- **URL:** https://www.stat.cmu.edu/capstoneresearch/460files_s25/team4.html (confirmed to exist via Google-indexed search snippet and the CMU capstone showcase index at https://www.stat.cmu.edu/capstoneresearch/; **direct fetch of the page returned HTTP 404 at the time of this research** — likely link rot/relocation between cohorts, a known issue with these course-hosted pages. Treat structural details below as drawn from the verified search-engine snippet, not a full first-hand read.)
- **What is verified:** The project used **Bayesian hierarchical Poisson regression** to model World Cup goals scored, testing random-effects terms for fan travel distance from host city and tournament stage, on a Kaggle World Cup match dataset — and found, importantly, that adding those random effects **decreased** model performance (a negative/null result, reported honestly rather than suppressed).
- **Significance for this project:** This is the single closest topical match found in Bucket 1 — World Cup soccer, Poisson-family modeling, a capstone showcase format, statistical rigor — but because the live page could not be re-fetched, it is flagged here as **partially verified** rather than fully documented. The CMU capstone showcase (https://www.stat.cmu.edu/capstoneresearch/) is real and indexes many short, focused sports-stats reports (basketball "Baseline Bias or Net Gain?", an MLB batting-average decline study, an NFL "Expected Passer Rating" tracking-data study) — confirming CMU runs a real, public-facing sports-stats capstone pipeline, even though this specific file could not be re-confirmed at fetch time.

### Bucket 1 — coverage assessment
Coverage is **real but thin**. Berkeley MIDS and UChicago MS-ADS do not appear to maintain durable, fully public final reports specifically on soccer/sports forecasting (searches for both came up empty for sports-specific capstones beyond the one baseball example). Stanford CS229's course-project archive, by contrast, is durably public and gave two full, directly-read 5-page reports that are extremely close in spirit (soccer outcome prediction, literature review, cross-validation, honest negative results). The CMU capstone showcase is real and active but this specific page would not re-load. **Recommendation:** treat the two CS229 reports as the primary Bucket-1 template, and "Predicting the Next Pitch" as the model for *multi-page public website* delivery format.

---

## Bucket 2 — Forecasting-community writeups

**Overall finding: strong real coverage.** Good Judgment and Metaculus both publish substantial, fetchable material on calibration and track records.

### 5. "Superforecaster Accuracy" white paper — Good Judgment Inc.
- **URL:** https://goodjudgment.com/wp-content/uploads/2022/10/Superforecaster-Accuracy.pdf (fetched in full via reader proxy after direct fetch was blocked with HTTP 403)
- **Structure (verified, in order):** Overall Accuracy of Good Judgment's Forecasts → How Quickly Did We Get It Right? → How Reliable Are Good Judgment's Forecasts? → Accuracy by Topic Area (Interest Rates / Geopolitics / Foreign Policy, each as its own subsection) → What This Means for Decision Makers.
- **Length/format:** 8 pages, PDF, professionally designed (not a plain academic template — has the visual polish of a corporate research note).
- **Distinctive content:** Reports performance across **323 resolved questions, 2016–2021**; includes explicit **calibration curves** in multiple sections (overall, reliability, and per-topic); reports that forecasters "identified the correct outcome with over 55% confidence up to 350 days ahead" — i.e., it ties calibration quality to *lead time before resolution*, a sophisticated framing beyond a single aggregate score.
- **Tone:** Hybrid — data-driven and methodologically serious in the body, shifting to promotional/marketing language in the closing "What This Means for Decision Makers" section. Useful as a caution: don't let a closing section undercut technical credibility with sales language.

### 6. Metaculus public Track Record page
- **URL:** https://www.metaculus.com/questions/track-record/ (fetched in full via reader proxy after direct fetch returned HTTP 403)
- **Structure:** Three core visualizations under plain section headers — **Calibration Curve**, **Score Scatter Plot**, **Score Histogram** — followed by a compact "Forecasting Stats" panel of raw aggregate numbers (e.g., average baseline score, total predictions, questions predicted vs. scored).
- **Length/format:** Single dense dashboard page, not a narrative document — minimal explanatory prose.
- **Distinctive content:** The **calibration curve + scatter + histogram triad** is the single most reusable visual pattern found across all four buckets for this project. It directly matches what the user already has the data for (a ~14+ match RBP ledger) and is the most natural place to visually prove the crowd-bias model and the "rules" empirically.
- **Tone:** Clinical, numbers-first, almost no narrative framing — illustrates that a track record can stand alone as evidence without heavy prose.

### 7. "Superforecasters: A Decade of Stochastic Dominance" — Good Judgment Substack (Peter Mühlbacher / Good Judgment team)
- **URL:** https://goodjudgment.substack.com/p/superforecasters-a-decade-of-stochastic (fetched in full)
- **Structure (verified):** Introduction → Analysis → Summary → References, with **seven distinct figures** embedded in the Analysis section: (1) keyword-frequency chart over 108 geopolitical questions, (2) forecaster cohort sizes (219 Superforecasters vs. 14,179 GJ Open forecasters), (3) forecasting-activity/update-frequency patterns, (4) accuracy-comparison bars (35.9% more accurate individually, 25.1% more accurate in aggregate), (5) error-score scatter by difficulty, (6) accuracy-vs-time-to-resolution chart, (7) calibration curves comparing overconfidence between cohorts.
- **Length/format:** ~2,500 words — a genuine long-form blog post (Substack), not a paper, but written with full statistical apparatus (Brier scores, AUC, d-prime referenced explicitly).
- **Distinctive content:** This is the best concrete proof that a **Substack-hosted blog post can carry full academic rigor** (named metrics: Brier, AUC, d-prime) while remaining freely shareable and indexable — exactly the publishing format the user is likely to use.
- **Tone:** Formal/academic voice despite the informal Substack platform — avoids colloquialism throughout.

### Bucket 2 — coverage assessment
**Strong.** Good Judgment supplies both a "corporate methodology PDF" register and a "rigorous Substack post" register; Metaculus supplies the cleanest reusable visualization pattern (calibration curve + scatter + histogram). I did not find a fully public *individual* superforecaster's season postmortem with personal track record (search surfaced institutional writeups, not a single forecaster's solo Substack ledger) — flagging this as the one sub-gap in this bucket; RAND Forecasting Initiative pages were found and confirm a real "strategic decomposition + probability + rationale" methodology but no fetchable detailed report with calibration plots was located in this pass.

---

## Bucket 3 — Sports-analytics writeups

**Overall finding: strong real coverage**, though one major source (FiveThirtyEight's live methodology page) has gone offline.

### 8. clubelo.com — Elo rating system methodology ("System" and "TheCase" pages)
- **URLs:** http://clubelo.com/System and http://clubelo.com/TheCase (both confirmed to exist via search-engine indexing and snippet extraction; **direct page fetches were blocked throughout this session** — clubelo.com returned `ECONNREFUSED` / "site overloaded, only cached pages available" on every attempt, including via reader-proxy. Content below is reconstructed from verified search-result snippets that quote the page directly, not a full first-hand read.)
- **What is verified via direct quotation in search snippets:** The "System" page explains Elo with the win-probability formula `E = 1 / (10^(-dr/400) + 1)`; documents a **self-calibrating home-field-advantage (HFA) parameter** that adjusts daily per-country based on whether home teams are over- or under-performing relative to expectation; and documents a **goal-margin multiplier** where points exchanged scale with the square root of goal difference. The "TheCase" page argues explicitly against using raw points/titles as strength measures, framing Elo as superior because it accounts for opponent strength and the "random nature of football."
- **Distinctive content:** A live, continuously self-correcting parameter (HFA) that is explicitly validated against real outcomes on an ongoing basis — i.e., the methodology page documents an **online calibration loop**, not a one-time fit. This is a sophisticated idea directly transferable to the JTC writeup's crowd-bias model (which is itself an ongoing empirical correction).
- **Tone:** Plain-language, public-facing FAQ/explainer register — not academic, but technically precise.

### 9. FiveThirtyEight Soccer Power Index (SPI) — methodology
- **URL status:** The original methodology page (https://fivethirtyeight.com/methodology/how-our-club-soccer-predictions-work/ and the equivalent /features/ URL) **now 301-redirects to abcnews.go.com/politics** — confirmed directly via fetch. This is consistent with FiveThirtyEight's site being shut down/folded into ABC News in 2023–2024; the methodology pages no longer resolve. **Flagging explicitly: the live source is dead.** Content below is reconstructed from corroborating secondary sources (cached CRAN/R package documentation for the `fivethirtyeight` data package, which quotes the methodology, and independent analyses citing the original text).
- **What is verified:** SPI gives each team an offensive rating (expected goals scored vs. a "middling" team) and a defensive rating (expected goals conceded); combines these into a Poisson model parameterized by both teams' ratings, home-field advantage, and days of rest, to forecast each match's score distribution; then runs **10,000-iteration Monte Carlo simulation** to project full-season outcomes from individual match forecasts, with ratings updating dynamically as simulated seasons unfold.
- **Companion exemplar (live, fetched in full):** The GitHub data README for SPI, https://github.com/fivethirtyeight/data/blob/master/soccer-spi/README.md (also mirrored at https://raw.githubusercontent.com/fivethirtyeight/data/master/soccer-spi/README.md, fetched directly) — see Bucket 4 below, since this is really a data-documentation exemplar that happens to sit alongside the methodology.
- **Distinctive content:** The combination of (a) an offense/defense rating decomposition, (b) a Poisson scoreline model, and (c) Monte Carlo season simulation is the closest public methodology to a Dixon-Coles-style approach that is written for a general audience rather than a stats journal — a strong tonal/structural model for "translate the Poisson math for non-statisticians" sections.
- **Tone:** Plain-English journalism register, but technically accurate and unembarrassed about naming the actual stats (Poisson, Monte Carlo) by name.
- **Lesson for the user:** Even a now-dead flagship methodology page leaves a durable trace through its GitHub data README and citing secondary sources — reinforces that publishing methodology *and* a data README together (as 538 did) gives redundancy if a primary site goes down, and is itself a model worth imitating.

### 10. Stanford CS229 reports (cross-referenced from Bucket 1)
Both Ulmer/Fernandez (2014) and Smolka (2016) — already fully detailed in Bucket 1 — double as sports-analytics methodology exemplars, since they directly implement and compare goal-based (Poisson-family) vs. result-based (classification) soccer prediction approaches with literature grounding. Counted once in Bucket 1 to avoid duplication, but their "Related Work" sections (citing Dixon & Coles, Karlis & Ntzoufras, Rue & Salvesen, Constantinou) are directly reusable as a model for this project's own literature-review section structure.

### 11. Kaggle "March Machine Learning Mania" solution writeups (NCAA basketball, not soccer, but the closest verified Kaggle sports-forecasting writeup with explicit calibration discussion)
- **URL:** https://medium.com/@maze508/top-1-gold-kaggle-march-machine-learning-mania-2023-solution-writeup-2c0273a62a78 (fetched in full; the canonical Kaggle-hosted writeup page itself returned HTTP 404 at fetch time, but this is the author's full mirror of the same content, explicitly title-matched)
- **Structure (verified, in order):** Overview → Methodology and Approach → Conclusion.
- **Length/format:** ~800–900 words, "5-minute read" — short blog-style post, not a paper.
- **Methods:** Ensembled external rating systems (Pomeroy, Moore, Sagarin — i.e., crowd-of-models aggregation, directly analogous to this user's crowd-bias framing) + box-score features; feature selection via Recursive Feature Elimination; **expanding-window cross-validation across 2015–2019**, explicitly framed as "the correct way to validate a time-series sports problem."
- **Calibration:** Explicitly attempted post-hoc probability scaling/calibration and reports that results were "mixed" — an honest negative result rather than a forced success story.
- **Tone:** Technical-conversational, first-person, openly discusses a sub-model (women's bracket) underperforming.
- **Lesson:** Confirms "expanding window time-series CV" as the standard, named validation approach in the sports-Kaggle community — directly applicable vocabulary for describing how the JTC backtest harness should be framed (it should NOT be framed as random k-fold CV, since match outcomes are time-ordered).

### Bucket 3 — coverage assessment
**Strong**, with one important caveat clearly flagged: FiveThirtyEight's primary methodology URL is dead (redirects to ABC News politics), and clubelo.com could not be directly fetched in this session (server overloaded / connection refused on every attempt) — both are documented above using verified secondary evidence (direct quotes in search snippets, GitHub mirror, CRAN docs) rather than invented content.

---

## Bucket 4 — Data engineering / data provenance / data-quality documentation exemplars

*(Added per scope clarification: the user wants the data-sourcing, reliability-tiering, scraping/market-fetching pipeline, and feature-matrix-build work to receive documentation billing equal to the statistical modeling — not buried as a one-line "Data" subsection.)*

### 12. "Datasheets for Datasets" — Gebru et al. (2018/2021)
- **URL:** https://arxiv.org/pdf/1803.09010 (fetched in full)
- **Structure (verified — full question-category list):** Motivation → Composition → Collection Process → Preprocessing/Cleaning/Labeling → Uses → Distribution → Maintenance. Each category is a set of specific, interrogative prompts (e.g., under Motivation: "Why was the dataset created? Who funded it?"; under Composition: "What do the instances represent? How many instances in total?"; under Maintenance: "Who is supporting/hosting the dataset? How can people report errors?").
- **Length/format:** Academic paper (arXiv), but explicitly designed as a fill-in-the-blank **template** for practitioners — adopted widely enough that derivative templates exist (e.g., the MT-Adapted Datasheets paper, and a public GitHub template repo at https://github.com/AudreyBeard/Datasheets-for-Datasets-Template).
- **Distinctive content:** This is the standard, citable academic precedent for "a dataset deserves its own documentation artifact, separate from the model that consumes it." Directly justifies giving the JTC project's data layer (ESPN GD1, book-consensus odds, FootyMetrics referee stats, Smarkets market scrapes, etc.) its own first-class section with the same category headers: motivation/provenance, composition, collection process, known preprocessing, intended use, and maintenance/update cadence.
- **Tone:** Formal academic, but written as a practical checklist rather than as a narrative — easy to adapt directly.

### 13. `fivethirtyeight/data` — `soccer-spi` README (GitHub)
- **URL:** https://github.com/fivethirtyeight/data/blob/master/soccer-spi/README.md (fetched directly, full content retrieved)
- **Structure:** A title/overview, a list of the five published CSV files with one-line descriptions, then a **full column-by-column data dictionary** for both the match-level file (22 columns: season/date/league identifiers, both teams, pre-match SPI ratings, win/draw probabilities, projected and actual scores, shot-based and non-shot-based xG, game-state-adjusted scores) and the rankings file (6 columns: rank, prior rank, name, league, offensive/defensive/overall rating) — then a pointer out to the separate prose methodology page for the modeling explanation.
- **Distinctive content:** This is the cleanest real example of the "**data dictionary lives with the data, methodology lives in prose elsewhere, and the two cross-link**" pattern. It is durable: even though FiveThirtyEight's prose methodology page is now dead (see Bucket 3, #9), this GitHub data dictionary is still alive and fetchable today — direct proof that decoupling data documentation from a single website pays off when sites get shut down.
- **Tone:** Terse, tabular, engineer-facing — no narrative at all, pure reference documentation.

### 14. `dcaribou/transfermarkt-datasets` — GitHub README + pipeline
- **URL:** https://github.com/dcaribou/transfermarkt-datasets (README fetched in full: https://github.com/dcaribou/transfermarkt-datasets/blob/master/README.md)
- **Structure (verified, in order):** Title + badges (build status, dbt version) → "What's in it" → "Getting started" → "Community" → "Contributing."
- **Pipeline documentation:** Describes a real two-stage ETL: raw scraper/API output lands in `data/raw/` (with sub-paths for the scraper source vs. the API source, i.e., **multiple data sources are kept physically separate and labeled by origin** — directly analogous to keeping ESPN/footystats/Smarkets data in clearly source-labeled raw folders) → transformed via dbt + DuckDB into `data/prep/`. Twelve published tables (competitions, games, clubs, players, appearances, valuations, club games, game events, lineups, transfers, countries, national teams) refreshed weekly via scheduled automation (visible as CI badges).
- **What's notably thin:** The README does **not** detail scraping methodology, collection dates, or explicit data-quality/testing procedures beyond a version badge — confirmed by direct read. This is a useful negative example: a popular, real, widely-used public football data pipeline (cited/forked widely) still under-documents its data-quality reasoning compared to what Datasheets-for-Datasets or a tiered-reliability audit would recommend. The user's existing tiered source-reliability audit is **already more rigorous** than this real-world public benchmark.
- **Tone:** Professional open-source README register — concise, badge-driven, contribution-focused rather than methodology-focused.

### 15. `paolomagni/football-platform` — GitHub README (cloud-native football data pipeline)
- **URL:** https://github.com/paolomagni/football-platform (fetched in full)
- **Structure (verified, in order):** Title/tagline → Overview (tech stack: GCP Cloud Functions, dbt, BigQuery, Docker, Cloud Run, GitHub Actions, Looker Studio) → Repository Structure → Technologies Used → CI/CD & Deployment Flow (five explicit steps: push → Docker build → tag with commit SHA → push to Artifact Registry → update Cloud Run Job) → Development & Deployment (local vs. production) → Data Modeling (staging → intermediate → mart layered architecture) → Roadmap (completed/in-progress/future) → **Data Source** (single short section) → Live Dashboard link → License/Contributing/Connect.
- **Data source / quality documentation:** Minimal but present and explicit: "Match data is sourced from Football-Data.org, a free public API," with an explicit caveat — "this project is for educational and personal use only; please review Football-Data.org terms before using in production." Lists "automated tests and data quality checks" as a completed roadmap item but gives no further detail.
- **Distinctive content:** The **staging → intermediate → mart** layered data-modeling pattern (a dbt convention) is a clean, namable way to describe a multi-stage pipeline (raw match scrape → cleaned/joined match-level table → analysis-ready feature matrix) — directly mappable to the user's own raw JSON → derived dataset → ML feature matrix flow, and consistent with the user's own existing rule of never mutating raw data and always writing derived outputs separately.
- **Tone:** Professional, accessible, uses emoji section markers for scannability — written for a portfolio/recruiter audience, explicitly.

### 16. Kaggle "March Machine Learning Mania" solution writeup (cross-referenced from Bucket 3, #11) — data-sourcing angle
The same writeup (https://medium.com/@maze508/top-1-gold-kaggle-march-machine-learning-mania-2023-solution-writeup-2c0273a62a78) does double duty here: its Methodology section explicitly enumerates *which external rating systems were data sources* (Pomeroy, Moore, Sagarin, plus box-score aggregates), and explicitly describes a **source-selection/filtering step** — "selected the top 10 historically-accurate rating systems, then filtered based on data availability" — which is conceptually identical to the user's tiered reliability audit (picking/ranking sources by track record, discarding ones that don't hold up). This is the strongest evidence found that source-quality triage, explicitly named and justified, is recognized good practice in the sports-forecasting Kaggle community, not just an academic nicety.

### Bucket 4 — coverage assessment
**Moderate-to-strong.** Found one canonical academic documentation standard (Datasheets for Datasets) with a real adopted template, and three real, fetched, in-the-wild football data pipeline READMEs (FiveThirtyEight's soccer-spi data dictionary, transfermarkt-datasets, football-platform) plus one Kaggle writeup that explicitly documents source triage. The clearest pattern across all of them: **none of these real-world public examples documents data quality/reliability as rigorously as the user's own tiered audit already does.** The user's Tier-1/Tier-2/Tier-3-never-use system, with explicit named exclusion reasons (e.g., "niche aggregator scorer odds when main books absent," "GD1 data in blowouts below 0.25"), is more rigorous than any public exemplar found here — this should be foregrounded as a genuine strength in the writeup, not hedged.

---

## Synthesis — Recommended document structure for the JTC / SportsPredict writeup

### Design constraints derived from the research
1. **Mixed audience, simultaneously.** CS229 reports prove that literature grounding + honest negative results read well to ML/quant audiences. Good Judgment/Metaculus prove that calibration curves + a running track-record table read well to the forecasting community. FiveThirtyEight/clubelo prove that plain-English translations of Poisson/Elo math read well to sports-analytics generalists. None of these audiences is served by hiding any one of these elements — so the structure below interleaves them rather than ghettoizing "the technical stuff" into one section.
2. **Data deserves a first-class, separate section**, not a paragraph inside "Methodology." Justified directly by Datasheets for Datasets (#12) and by the fact that the strongest data dictionary found (538's soccer-spi README, #13) survived even after its parent site died — decoupling data documentation from modeling documentation is both more credible and more durable.
3. **Avoid academic-capstone overkill.** Things found in Bucket 1 that would be **wrong tone or unnecessary** for a solo public writeup: a formal "Acknowledgments" section thanking a course staff/TA (present in both CS229 reports — fine for a class deliverable, odd for a public solo post); rigid two-column conference-paper typesetting (fits a course submission, not a web-native writeup); an explicit grade-seeking framing. Keep the *behaviors* from these reports (citing literature, naming validation method precisely, admitting failed approaches) without the *trappings* (institutional boilerplate, page-limit-driven terseness).
4. **Definitely borrow from forecasting-community writeups:** the calibration curve (Metaculus #6, Good Judgment #5/#7) and a running track-record table with cumulative score (Good Judgment #5's "323 questions, 2016–2021" framing; directly maps to the user's existing ~14+-match RBP ledger). Also borrow Good Judgment's "accuracy by topic/category" breakdown (#5) — map this to "RBP by bet-type" or "RBP by rule-tag (RULE12–15)."
5. **Definitely borrow from sports-analytics writeups:** clubelo's framing of an explicit, ongoing self-calibrating parameter (HFA) as a *feature*, not a flaw (#8) — map directly to the crowd-bias formula `crowd ≈ 0.514 + 0.61×(model−0.5)` being presented as a live, periodically re-fit empirical correction. Also borrow FiveThirtyEight's discipline of naming the actual stats by name in plain English (#9) — "Poisson," "Monte Carlo," "Dixon-Coles," "Negative Binomial dispersion" should appear with one-sentence plain translations, not be assumed or avoided.

### Recommended structure

**1. Abstract / TL;DR** (~150–250 words)
What JTC is, what was built (models + crowd-bias rules + market-edge pipeline), and the single most important number (running RBP, calibration quality). Modeled on the abstract convention in both CS229 reports (#2, #3) — keep it that short and concrete, not a marketing pitch.

**2. Motivation & Background**
What the JTC tournament is, what RBP measures (proper scoring rule), why this is a hard/interesting problem. One paragraph situating it relative to known forecasting venues (Good Judgment Open, Metaculus) so non-sports readers immediately understand the genre — justified by how naturally Good Judgment/Metaculus writeups assume reader familiarity with their own genre (#5, #6) that this project's readers won't have by default.

**3. Literature Review**
The ~8 papers (Dixon & Coles 1997, Karlis & Ntzoufras 2003, Constantinou & Fenton 2012, Michels/Ötting/Karlis 2023, the verification paper, the wisdom-of-crowds paper), framed exactly the way CS229's "Related Work" sections do (#2, #3): organize by *modeling lineage* (goal-based/Poisson-family vs. result-based/classification vs. crowd-aggregation), not just a list. This is the section where academic-capstone tone is most directly appropriate and expected.

**4. Data — Sources, Pipeline, and Reliability** *(first-class section, not a subsection)*
- **4a. Source inventory and reliability tiers.** Present the existing Tier-1/Tier-2/Tier-3-never-use audit as a table, with the named exclusion reasoning kept verbatim (this is more rigorous than any public exemplar found — see Bucket 4 conclusion). Structurally modeled on Datasheets for Datasets' Motivation/Composition categories (#12): for each tier, state what it's used for, why it's trusted, what its failure modes are.
- **4b. Pipeline architecture.** Describe the scraping/market-fetching bot, dashboard fetching, market classification, in the staging→intermediate→mart layering language used by football-platform (#15) and transfermarkt-datasets (#14): raw fetch (immutable, write-to-disk-immediately, per the user's own existing rule) → cleaned/derived per-match datasets → master feature matrix.
- **4c. Data dictionary.** A real column-by-column table for the master question dataset and feature matrix, in the terse reference style of 538's soccer-spi README (#13) — this is the single most directly copyable structural element found in this whole research pass.
- **4d. Known caveats / exclusions.** What was deliberately left out and why (mirrors football-platform's explicit "educational use only" caveat, #15, and Datasheets' "tasks this should NOT be used for" prompt, #12).

**5. Methodology / Models**
Dixon-Coles, Negative Binomial dispersion, ordered logit, Elo, Platt calibration — each given a plain-English one-paragraph translation (FiveThirtyEight-style, #9) before any equations, then the technical specification for readers who want it (CS229-style, #2/#3). Name the validation strategy explicitly as **expanding-window, time-ordered cross-validation** (matching the named convention from the Kaggle Mania writeup, #11/#16) — explicitly state this is *not* random k-fold, since matches are time-ordered and this distinction is exactly what separates rigorous from naive sports-prediction validation in the literature reviewed.

**6. Crowd-Bias Model and Rules (RULE12–15)**
Present the empirical formula and each rule with its supporting n and direction, in the same "accuracy by category" spirit as Good Judgment's topic-area breakdown (#5). Explicitly frame the crowd-bias correction as a live, periodically-recalibrated parameter the way clubelo frames its HFA self-calibration (#8) — this is a strong, on-the-nose analogy to make explicit in prose.

**7. Calibration and Validation**
A reliability/calibration curve (predicted probability vs. observed frequency) is the single highest-value visual to add, directly modeled on Metaculus's Track Record page (#6) and Good Judgment's white paper (#5). Pair it with a Brier/RPS-decomposition discussion if feasible.

**8. Track Record / Results**
The running RBP ledger as an actual table (date, match, question, model estimate, crowd estimate, market price if available, outcome, RBP), the way Good Judgment presents "323 questions, 2016–2021" (#5) and the way Metaculus exposes total predictions/questions scored as headline stats (#6). Include both the high points (+72.47 GER-CUR) and the low points (-44.55 Kane ENG-CRO) without spin — directly modeled on the CS229 reports' and Kaggle writeup's willingness to report negative/mixed results plainly (#2, #3, #11).

**9. Market-Edge / Backtest Pipeline**
How model output is compared against market-implied probability; what "edge" means operationally.

**10. Limitations and Threats to Validity**
Explicitly named as its own section — notably *absent* as a dedicated section in three of the four CS229/Kaggle exemplars (#2, #3, #11), which is identified above as a gap worth NOT replicating. Cover: small-n rule risk (n≥5 threshold already used internally), World Cup-specific biases (e.g., the host-nation overrating issue already identified from the CAN-BIH postmortem), data-tier risk, and the fact this is single-person research without peer review.

**11. Future Work**
Direction 5 / Direction 1 from the existing ownership-extension strategy memo, or JTC-specific next steps — modeled on CS229's "Future Work" convention (#2, #3).

**12. Appendix: Data Dictionary / Repro Notes**
Full column listing, links to repo/notebooks if shared — in 538's data-dictionary register (#13).

### What to explicitly avoid
- Course-submission boilerplate (Acknowledgments-to-TA, page limits, two-column LaTeX conference template) — fine in Bucket 1 sources because they were literally class deliverables; wrong register for a public solo post.
- Don't let a closing section slide into marketing language the way Good Judgment's white paper does (#5) — keep the tone consistent through the last paragraph.
- Don't bury the data section as a "Data" sub-bullet under Methods — every credible exemplar that handled data well (Datasheets, 538, the Kaggle writeup) gave it independent visual weight.

---

## Notes on access limitations encountered during this research
- **fivethirtyeight.com** methodology pages now hard-redirect (HTTP 301) to abcnews.go.com/politics — the original site is gone. Content reconstructed from the live GitHub data README and corroborating search-snippet quotations of the original text.
- **clubelo.com** refused direct connections throughout this session (`ECONNREFUSED`, and one fetch returned a literal "site overloaded, only cached pages available" message) — content reconstructed from verified, directly-quoting search-engine snippets, not a first-hand page read.
- **CMU's stat.cmu.edu/capstoneresearch/460files_s25/team4.html** returned HTTP 404 on direct and proxied fetch despite being indexed and quoted by search — flagged as partially verified only.
- **Good Judgment's PDF and Metaculus's track-record page** both blocked direct WebFetch with HTTP 403 but were successfully retrieved via a reader-proxy fallback (r.jina.ai), and are reported above as fully fetched.
- No example in any bucket was invented; every numbered exemplar above has a real, checkable URL.
