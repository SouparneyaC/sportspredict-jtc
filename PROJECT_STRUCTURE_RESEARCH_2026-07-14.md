# Project Structure Research: Making This Repo Traceable by Unit-of-Work, for Both Human Reviewers and AI Agents

**Purpose of this document.** This repo (~855 project files: root-level research memos, `bot/`, `data/`+`datasets/`, `matches/*/` per-match pricing pipelines, `ml/`+`model/`, `papers/`, `writeups/`) is organized "by layer" — all scripts under `ml/`/`model/`, all data under `data/`, all match folders under `matches/`. `REPO_MAP.md` already gives a flat, directory-by-directory table of contents, but it doesn't solve a different problem: tracing one *unit of work* (e.g. "the cards question type," a specific match, a specific model) end-to-end — script, data, reasoning, results — without hunting across 5+ unrelated top-level directories. This is true for the primary researcher working the repo daily, for a senior reviewer doing a periodic audit, and for Claude Code picking up a session cold.

This document surveys **real, fetched or verifiably-searched sources** (not invented) across six buckets — Anthropic's own agentic-coding guidance, DS/ML project-structure standards, reproducible-research repo guidance, the package-by-feature-vs-layer debate, index/manifest/cross-linking patterns that don't require physical reorg, and real-world large-repo examples — then closes with a synthesis of concrete options for this specific repo. It does not pick a winner or implement anything; per the brief, that's a follow-up conversation. Structure mirrors `DOCUMENTATION_RESEARCH.md` (numbered buckets of sources → synthesis → what to avoid).

I grounded the synthesis in this repo's actual current structure by reading `REPO_MAP.md` §4 (`matches/`), §5 (`ml/`+`model/`), and §7 (`writeups/`) in full before writing the recommendations below — not a generic description of "a typical ML repo."

---

## Bucket 1 — Anthropic's own published guidance on structuring repos/context for agentic coding

**Overall finding: strong, current, and directly on-point.** Anthropic has published exactly the kind of guidance the user asked for, including a page specifically about large codebases/monorepos.

### 1. "Best practices for Claude Code" — Anthropic docs
- **URL:** https://code.claude.com/docs/en/best-practices (fetched in full)
- **Core principle:** Nearly every practice reduces to one constraint — "Claude's context window fills up fast, and performance degrades as it fills." CLAUDE.md should contain only what Claude *can't* infer from the code itself (bash commands it can't guess, non-default code-style rules, architectural decisions specific to the project) and explicitly should **not** contain "file-by-file descriptions of the codebase" — that's what directory structure and grep are for. Also: "folder hierarchies, naming conventions... provide important signals," and subagents should be used for investigation precisely so exploratory file reads don't pollute the main context.
- **Applicability:** Directly validates why `REPO_MAP.md` (a giant narrative index) is a stopgap rather than a scalable solution for AI-agent legibility — Anthropic's own guidance is that per-file narrative description is exactly what CLAUDE.md/README content should avoid, in favor of structure the agent can navigate itself. Also validates the existing repo convention (per `ML_EXPERIMENTS_NOTEBOOK.md`, `REPO_MAP.md`) of writing things down explicitly rather than relying on Claude re-deriving context each session — but Anthropic's framing suggests that content belongs in structural/on-demand form (skills, per-directory files), not one ever-growing root document.

### 2. "Set up Claude Code in a monorepo or large codebase" — Anthropic docs
- **URL:** https://code.claude.com/docs/en/large-codebases (fetched in full)
- **Core principle:** For large single-tree or multi-package codebases, Anthropic recommends **layering CLAUDE.md files by directory** (root file for repo-wide rules, one per subsystem/package for local conventions — "Claude loads repository-wide rules plus only the conventions for the code you're working in"), **per-directory skills** (`.claude/skills/<name>/SKILL.md` scoped to a subtree, loaded on demand, "API-specific tooling doesn't consume context during frontend work"), and **path-scoped rules** (`.claude/rules/` with `paths:` globs) for conventions that apply to "the same rule across many scattered paths" — which is exactly this repo's shape (cards-question logic is scattered across `ml/backtests/`, `data/processed/`, and `matches/*/04_rules_applied.json`, not confined to one directory). It explicitly frames `claudeMdExcludes` and skill-scoping as *alternatives to physically moving files* when a codebase's natural layout doesn't match a task's boundaries.
- **Applicability:** This is the single most directly transferable source found. A `.claude/skills/cards-question-pricing/SKILL.md` (or a `paths:`-scoped rule matching `**/*cards*`) is a concrete, Anthropic-native mechanism to give the agent "everything about cards" without moving a single file — a real, load-bearing candidate for solving the agent-legibility half of the problem discussed in the synthesis below.

### 3. "Effective context engineering for AI agents" — Anthropic Engineering blog
- **URL:** https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents (fetched in full)
- **Core principle:** Favor "just-in-time" context retrieval over pre-loading everything: agents should keep "lightweight identifiers (file paths, stored queries, web links, etc.)" and dynamically load data at runtime, mirroring how humans use "file systems, inboxes, and bookmarks" rather than memorizing everything. Explicitly: "folder hierarchies, naming conventions, and timestamps all provide important signals" — a file named `test_utils.py` inside `tests/` communicates something different than the same name inside `src/core_logic/`. This enables "progressive disclosure" — incremental discovery through exploration rather than a single giant context dump.
- **Applicability:** This is the theoretical backbone for why a *lightweight index/manifest* (a small file of pointers — "here's where the cards script/data/docs live") is agent-native in a way a narrative essay is not: it's exactly the "lightweight identifier" pattern Anthropic recommends, and it composes with grep/glob rather than requiring the agent to have read everything already.

### 4. "Building Effective Agents" — Anthropic Engineering blog
- **URL:** https://www.anthropic.com/engineering/building-effective-agents (verified via search; not directly re-fetched, content corroborated across multiple independent secondary summaries including anthropic-cookbook and agentpatterns.ai)
- **Core principle:** Three principles for agent-facing systems: simplicity, transparency ("explicitly showing the agent's planning steps"), and a carefully documented agent-computer interface (ACI) — treating tool/interface documentation with the same rigor as a human-computer interface. "Success in the LLM space isn't about building the most sophisticated system. It's about building the right system for your needs."
- **Applicability:** Argues against over-engineering the fix — e.g., building a bespoke graph database or custom retrieval tool for this repo would violate "simplicity" when a well-labeled markdown index plus grep already satisfies the requirement.

### 5. "How we built our multi-agent research system" — Anthropic Engineering blog
- **URL:** https://www.anthropic.com/engineering/multi-agent-research-system (content verified via Simon Willison's detailed write-up, https://simonwillison.net/2025/Jun/14/multi-agent-research-system/, which quotes the original extensively)
- **Core principle:** Sub-agents need an explicit objective, output format, tool guidance, and clear task boundaries; the team found rewriting *tool descriptions* (not the prompt) produced a 40% reduction in task-completion time for downstream agents. Also: because a sub-agent's own context can be truncated, load-bearing state (a plan, a decision) must be persisted outside the conversation, not just held in-context.
- **Applicability:** Reinforces that whatever index/manifest layer gets built should read like a tool description — objective, scope, boundaries stated plainly — rather than prose narrative, and that it must persist as a real file (not just something explained once in a chat) since context truncates.

---

## Bucket 2 — Data science / ML project structure standards

**Overall finding: consistent convergence on a 3-tier data pipeline (raw → interim/intermediate → processed) plus an explicit, versioned pipeline-definition artifact separate from the data itself.**

### 6. Cookiecutter Data Science
- **URL:** https://cookiecutter-data-science.drivendata.org/ (fetched in full)
- **Core principle:** `data/raw` = "the original, immutable data dump"; `data/interim` = "intermediate data that has been transformed"; `data/processed` = "the final, canonical data sets for modeling"; `data/external` = "data from third party sources." States the philosophy in general terms — "a logical, flexible, and reasonably standardized project structure... making it much easier for somebody who has never seen a particular project to figure out where they would find the various moving parts" — comparable to a Rails app's standard skeleton. Notebooks use an ordered-numeric-prefix + author-initials + short description naming convention (`1.0-jqp-initial-data-exploration`) for the same reason numbered pipeline files help here.
- **Applicability:** This project's `data/raw` (immutable per-fetch dumps, per the "never mutate raw data" rule already enforced in `matches/*/espn_*_raw.json`) → curated per-match JSON → `ml/feature_matrix.csv`/`datasets/` flow is already structurally isomorphic to this convention, just without the folder names matching. Confirms the *existing* data layering is sound; the gap is topic-level cross-linking, not the raw/processed separation itself.

### 7. DVC (Data Version Control) — project structure
- **URL:** https://doc.dvc.org/user-guide/project-structure (redirect-verified; content corroborated via search results quoting the same official structure)
- **Core principle:** A `dvc.yaml` explicitly declares pipeline **stages** (inputs, outputs, parameters, metrics) as a versioned, git-tracked artifact separate from the data itself; `.dvc` placeholder files track large data/model artifacts without committing their bytes to git. The pipeline definition is the traceable, greppable "what depends on what" layer, decoupled from the large binary data it points to.
- **Applicability:** DVC's actual innovation for this project's problem isn't the folder layout (already similar to Cookiecutter's) — it's the idea of **a small, versioned, git-native manifest file that declares stage → inputs/outputs**, which is a lighter-weight cousin of the Bazel BUILD-file idea (Bucket 5) and could be mimicked with plain markdown/YAML without adopting the DVC tool itself.

### 8. Kedro — opinionated pipeline structure
- **URL:** verified via https://docs.kedro.org/ and corroborating summaries (docs.kedro.org/en/stable/create/minimal_kedro_project/, kedro.org blog)
- **Core principle:** Enforces numbered data layers (`01_raw`, `02_intermediate`, `03_primary`, ... `06_models`) and a **Data Catalog** (`conf/base/catalog.yml`) that "formalizes how data is accessed, versioned, and managed across a project, preventing file paths and storage logic from being scattered throughout the codebase." Pipelines are explicit DAGs of pure functions, registered centrally in `pipeline_registry.py`.
- **Applicability:** The Data Catalog concept — one central file mapping a logical dataset name to its physical path and format — is close to what a "topic index" for this project could do for data specifically (e.g., a single table mapping `cards_data → data/processed/statsbomb_team_match_panel.csv`, `sot_data → ...`), again without requiring the Kedro framework itself.

### 9. Google Cloud MLOps reference architecture
- **URL:** https://docs.cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning (existence and content verified via search; not independently re-fetched in full — flagged as search-corroborated rather than directly read)
- **Core principle:** Recommends recording, for every pipeline execution, enough metadata to answer "what data, what code, what parameters, what results, and who approved it" for lineage/reproducibility/audit — i.e., traceability is treated as a first-class pipeline output, not an afterthought.
- **Applicability:** This is essentially what `matches/*/04_rules_applied.json` and `06_post_match_results.json` already do per-match (tier, applied rules, resulting estimate, reasoning note, settlement) — confirms the per-match pipeline is already well-instrumented; the missing piece is the same discipline applied *across matches, grouped by question-type* rather than only within one match folder.

---

## Bucket 3 — Reproducible-research repo guidance

**Overall finding: strong, directly fetched, and the clearest formal articulation of "why data/methods/output must stay separated" — which cuts directly against a naive "just move everything cards-related into one folder" reorg.**

### 10. The Turing Way — Guide for Reproducible Research
- **URL:** https://book.the-turing-way.org/reproducible-research/reproducible-research/ (fetched; this landing page is a navigation hub, thin on specifics — flagged honestly, details came from the linked Research Compendia page below)
- **Core principle:** Reproducibility means "data and code being available to fully rerun the analysis" — a repo-structure problem as much as a code-quality problem.
- **Applicability:** Sets up the more specific guidance in source #11.

### 11. The Turing Way — Research Compendia
- **URL:** https://book.the-turing-way.org/reproducible-research/compendia/ (fetched in full)
- **Core principle:** Three explicit principles for a "research compendium": (1) "files should be organized in a conventional folder structure," (2) **"data, methods, and output should be clearly separated,"** (3) "the computational environment should be specified." Also gives a three-way file classification — **read-only** (raw data/metadata, never modified), **human-generated** (code, papers, docs authored by the researcher), **project-generated** (cleaned data, figures, computed outputs) — and recommends naming files/folders so "it is easy for others to understand what they contain" without opening them.
- **Applicability:** This is the strongest counter-argument in all six buckets to a literal "put the cards script, cards data, and cards docs in one physical folder" reorg — Turing Way's own guidance is that data, methods, and output stay in separate top-level areas *by kind*, which is what this repo already does (`data/`, `ml/`+`model/`, `matches/*/06_post_match_results.json`). The read-only/human-generated/project-generated distinction also maps cleanly onto this repo's own "never mutate raw fetch data" convention already in force. The implication: cross-cutting traceability should be solved with a *linking* mechanism layered on top of the kind-based separation, not by physically merging kinds together.

### 12. The Turing Way — Advanced Structure for Data Analysis
- **URL:** https://book.the-turing-way.org/project-design/pd-overview/project-repo/project-repo-advanced/ (fetched in full)
- **Core principle:** A fuller example tree — `analysis/`, `build/`, `data/`, `docs/`, `project-management/`, `res/`, `src/`, `test/`, `lib/`, `example/` — with the stated rule: "general structure should separate input (data), methods (scripts) and output (results, figures, manuscript)."
- **Applicability:** Same conclusion as #11, from an independent page: kind-based (layer) separation is the recommended default even in reproducibility-focused guidance, not feature/topic-based separation.

### 13. NeurIPS Paper Checklist (reproducibility)
- **URL:** https://blog.neurips.cc/2021/03/26/introducing-the-neurips-2021-paper-checklist/ ; https://neurips.cc/Conferences/2022/PaperInformation/PaperChecklist (existence/mechanics verified via search, not independently fetched in full)
- **Core principle:** For every reproducibility claim, authors answer yes/no/n-a and **cite the specific section of the paper that supports the answer** — i.e., every methodological claim must be individually traceable to a specific location, not just generally "documented somewhere in the repo."
- **Applicability:** A useful discipline to borrow at the index/manifest level (Bucket 5): a topic-index entry for "cards" shouldn't just say "documented in the notebook" — it should cite the exact section/line/file, the same way the checklist forces per-claim citations rather than blanket assertions.

### 14. Datasheets for Datasets / Model Cards — repo-layout implications
- **URL:** https://arxiv.org/pdf/1803.09010 (already known to this project per `DOCUMENTATION_RESEARCH.md` #12 — not re-summarized for content here; layout implication only) plus corroborating search on "DAG/System Cards" patterns
- **Core principle (layout-specific, not content-specific):** Search corroboration surfaced a "DAG/System Cards" pattern where a datasheet lives as its own artifact and its URI is used as a **node anchor in a pipeline DAG that ties model and dataset artifacts together** — i.e., the documentation artifact doesn't move into the pipeline's physical location; the pipeline graph *points at* the documentation artifact by reference.
- **Applicability:** Directly analogous to what an index/manifest approach would do for this repo: a "cards question-type" entry doesn't relocate `walk_forward_cards_referee_backtest.R`, it points at it — consistent with Turing Way's separation principle and Anthropic's "lightweight identifier" framing (source #3) converging on the same answer from three different fields.

---

## Bucket 4 — "Package by feature" vs "package by layer"

**Overall finding: a real, well-documented software-architecture debate, directly mappable onto this repo's problem, but with an important caveat about when feature-based packaging backfires (heavily-shared code/data).**

### 15. "Package by feature, not layer" — javapractices.com
- **URL:** http://www.javapractices.com/topic/TopicAction.do?Id=205 (site's TLS certificate is expired as of this research pass — WebFetch failed with "certificate has expired"; content below is drawn from corroborating search-result summaries that directly quote/paraphrase the page, consistent with how this project's own `DOCUMENTATION_RESEARCH.md` handled unreachable sources — flagged rather than papered over)
- **Core principle:** Package-by-layer groups by technical role (all controllers together, all services together) — low cohesion within a package, since unrelated features sit side by side; package-by-feature groups everything one feature needs into one directory, giving high cohesion, high modularity, and low cross-package coupling, and lets more classes be package-private instead of forced-public.
- **Applicability:** Names exactly this repo's current shape: `ml/` (all scripts, any feature), `data/` (all data, any feature), `matches/` (grouped by match, which is one axis of "feature" — but not by question-type, which is the axis the user actually needs for "the cards question").

### 16-17. Corroborating treatments — Sahibinden Technology (Medium) and Chathuranga T.'s WordPress writeup
- **URLs:** https://medium.com/sahibinden-technology/package-by-layer-vs-package-by-feature-7e89cde2ae3a ; https://chathurangat.wordpress.com/2017/09/12/software-architecture-package-by-features-or-package-by-layers/ (both verified via search; not independently re-fetched)
- **Core principle:** Package-by-layer "supports the Single Responsibility Principle" at the layer level but produces low cohesion and forces broad public visibility; package-by-feature produces high cohesion but only pays off when a feature's dependencies are genuinely self-contained. Neither source claims one approach is universally correct — both frame it as a tradeoff conditioned on how much code/data a "feature" actually shares with its neighbors.
- **Applicability — the caveat that matters most for this repo:** package-by-feature works best when a feature's data and code are *not* heavily shared with other features. This repo's actual data (`data/processed/statsbomb_team_match_panel.csv`, `elo_current_ratings.csv`, the unified 456-row panel) is used by essentially every question-type backtest simultaneously — SOT, corners, cards, and offsides backtests in `ml/backtests/` all read the same underlying panels via `lib_hierarchical_backtest.R`. A literal package-by-feature move (physically relocating "the cards data" into a cards-only folder) would either require duplicating shared panels per topic (violating the project's own no-duplicate-raw-data discipline and Turing Way's read-only/immutable-raw principle, source #11) or leave the data behind anyway — meaning the *data* layer in this repo is closer to genuinely layer-shaped by nature, while the *reasoning/decision* layer (preregistrations, rules, postmortems) is closer to genuinely feature-shaped. This asymmetry is a first-class input to the synthesis below.

---

## Bucket 5 — Index/manifest/cross-linking patterns that avoid full physical reorg

**Overall finding: strong coverage, several directly citable mechanisms, and one already partially implemented inside this very repo (`writeups/`).**

### 18. Bazel — explicit per-target dependency declarations
- **URLs:** https://bazel.build/basics/dependencies ; https://bazel.build/concepts/dependencies (content verified via search, consistent across both pages)
- **Core principle:** "Every rule must explicitly declare all of its actual direct dependencies to the build system, and no more" — Bazel fails the build if a target references something it hasn't declared. Google's multiyear effort to retrofit fully explicit dependencies across its monorepo was expensive but "builds are now much faster... engineers can remove dependencies they don't need without worrying about breaking targets."
- **Applicability:** The core lesson transfers even without adopting Bazel: an explicit, checked, per-unit-of-work "declared dependency list" (script(s) + data file(s) + doc(s) for "cards") is more valuable *because it's machine-checkable*, not just narrated. `writeups/README.md`'s own 100-link verification script (source #24 below) is already this idea in miniature.

### 19. Architecture Decision Records / MADR
- **URLs:** https://adr.github.io/ ; https://adr.github.io/madr/ (verified via search, corroborated by this project's own existing `writeups/decisions/000X-*.md` files, which already use the Status/Context/Decision/Consequences MADR shape per `REPO_MAP.md` §7)
- **Core principle:** One immutable, numbered file per architecturally-significant decision; once accepted, changes happen only via a new ADR that supersedes and cross-links the old one — never a silent edit.
- **Applicability:** Already adopted in this repo for three pricing-methodology decisions (market-priority-over-model, shadow-deploy-before-live, never-blindly-drop-a-question). The open question is whether question-type-specific decisions (e.g. "cards stays market-anchored, not model-driven, for this tournament" — the actual conclusion of `PREREGISTRATION_cards_referee_fouls_stage.md` per `REPO_MAP.md` §5) deserve the same ADR treatment, which would make them independently discoverable (`writeups/decisions/000X-cards-...md`) rather than living only inside a 37-file backtest campaign folder.

### 20. CALM (Architecture-as-Code) — ADR-to-architecture linking
- **URL:** https://calm.finos.org/tutorials/intermediate/10-adr-linking/ (fetched in full)
- **Core principle:** Links ADRs into an architecture description via a flat `adrs` array of relative paths/URLs — but explicitly **only at the whole-architecture level, not per-component**. There is no built-in mechanism to say "this specific service/file is governed by this specific ADR."
- **Applicability — useful as a negative finding:** even a purpose-built architecture-as-code standard doesn't solve fine-grained (per-file) ADR-to-code linking out of the box; this repo would have to build that granularity itself (e.g., a one-line "Decisions: ADR-0002" pointer at the top of each affected script or a table row in a topic index) rather than expecting an off-the-shelf tool to provide it.

### 21. e-ADR / "fitness functions for decisions as code"
- **URL:** https://github.com/adr/e-adr (verified via search)
- **Core principle:** Embeds ADR references directly in source via annotations (e.g. `@ADR(1)` pointing to `docs/adr/0001-*.md`); a related pattern ("fitness functions") writes an automated test that asserts a codebase still complies with a given decision, making the ADR's consequence checkable rather than just narrated.
- **Applicability:** A lightweight version — a one-line comment or header field in each backtest script naming which ADR/rule/preregistration governs it — would be cheap to add and would make `grep -r "ADR-0002"` or `grep -r "RULE_FOULS"` across the repo immediately surface every governed file, script, and doc, which is close to what the user needs for "trace everything about X."

### 22. Zettelkasten / bidirectional linking (Obsidian, Roam)
- **URL:** verified via multiple search results (e.g. https://e-student.org/zettelkasten-method/, Obsidian community discussion at https://forum.obsidian.md/t/zettelkasten-linking-for-surprising-connections/33214); not a single canonical fetched source, but the concept is well-established and consistently described across sources
- **Core principle:** Atomic notes carry unique identifiers and are connected via bidirectional links, forming an index/graph layer *on top of* wherever the notes physically live — one community description frames this as "physically separat[ing] structures while functionally connect[ing] them through bidirectional links."
- **Applicability:** The clearest conceptual precedent for "don't move the files, add a linking layer." The practical risk (also visible in the Obsidian/Roam tooling ecosystem) is that true bidirectional linking usually depends on specialized tooling (a vault, a graph index) that a plain-markdown-and-grep workflow doesn't have — so the actionable version for this repo is a *simulated* one-directional-but-consistent link convention (topic index → file, plus a corresponding one-line backlink comment in the file itself), not a full Zettelkasten app.

### 23. AGENTS.md — open standard for agent-facing repo context
- **URL:** https://agents.md/ (fetched in full); adoption/scale details corroborated via https://www.infoq.com/news/2025/08/agents-md/ and https://www.agentpatterns.ai/standards/agents-md/
- **Core principle:** A predictable, nestable per-directory file (`AGENTS.md`, functionally identical in mechanism to nested `CLAUDE.md`, source #2) — "agents automatically read the nearest file in the directory tree, so the closest one takes precedence and every subproject can ship tailored instructions." Donated to the Linux Foundation's Agentic AI Foundation in December 2025; reportedly adopted by 60,000+ open-source projects by that point.
- **Applicability:** Confirms nested, per-directory context files are now an industry-standard (not just Anthropic-specific) pattern for exactly this problem — giving weight to Option 4 in the synthesis below.

### 24. This repo's own `writeups/` directory — an internal, already-working precedent
- **Location:** `writeups/` (per `REPO_MAP.md` §7, read in full during this research pass)
- **Core principle:** Already implements several of the patterns surveyed above, in miniature, for exactly one match (France vs Spain): MADR-style ADRs (`decisions/0001-*.md` through `0003-*.md`) cross-linking to the rules they formalize, a README-as-index with a "Standing Decisions" table, Keep-a-Changelog conventions, and — most relevant here — a **verified-link discipline**: "every path reference in this section was individually verified to resolve (a 100-link check via a Python script comparing percent-encoded/decoded paths against `os.path.exists`)." This is a real, already-built instance of Bazel's "explicit and checked, not just narrated" principle (source #18), built independently before this research pass.
- **Applicability:** This is the strongest "real-world example" in the entire research pass, because it's not external — it's proof the approach already works inside this specific repo, for one match. The open question for the synthesis is whether/how to extend this pattern from "one match" to "one question-type across all matches," which is a different traceability axis (cross-cutting rather than per-match).

---

## Bucket 6 — Real-world examples

### 25. OpenAI's own repository — 88 nested AGENTS.md files
- **Source:** cited within the AGENTS.md adoption coverage (source #23 above, via agentpatterns.ai's summary)
- **Principle demonstrated:** A large, real, heavily-agent-assisted codebase choosing distributed per-directory context files over a single monolithic index or a physical reorg.
- **Applicability:** Directly comparable in spirit to what this repo would do if it added per-directory `CLAUDE.md`/skills (source #2) instead of trying to move `ml/backtests/*cards*` files into a new `cards/` directory.

### 26. Google's Bazel-based monorepo dependency-explicitness effort
- **Source:** source #18 above (bazel.build docs), corroborated by https://earthly.dev/blog/monorepo-with-bazel/ (existence/content verified via search, not independently fetched)
- **Principle demonstrated:** A real, large-scale, multiyear precedent for retrofitting explicit dependency declarations onto a pre-existing large codebase *without* a physical reorganization — the fix was declarative metadata, not file moves.
- **Applicability:** The closest real large-scale precedent for "add a manifest/declaration layer instead of moving files," at a scale far beyond this project but directly analogous in mechanism.

### 27. This repo's `writeups/` directory (cross-referenced from source #24)
Counted once in Bucket 5 to avoid duplication, but doubles as the single most directly applicable real-world example found, since it's real, already-built, already-verified, and already inside this exact repo.

---

## Synthesis — Candidate approaches for this repo

Four constraints emerged repeatedly across all six buckets and should anchor whichever option gets chosen later:

1. **Turing Way's own reproducibility guidance argues against a literal by-feature physical merge of data+code+docs** (source #11), because this repo's data panels are genuinely shared across question-types (the same `statsbomb_team_match_panel.csv` feeds SOT, corners, cards, and offsides backtests via one shared library, `lib_hierarchical_backtest.R`) — a literal reorg would force either duplication (violating the project's own immutable-raw-data rule) or leave data behind anyway, undermining the reorg's own goal.
2. **Anthropic's own guidance (sources #1–#3, #23) converges on nested, per-directory, on-demand context files (CLAUDE.md/AGENTS.md/skills) as the standard fix for exactly this shape of problem** — and this mechanism is now an industry-wide convention (60,000+ repos per source #23), not an Anthropic-only idiosyncrasy.
3. **This repo already has a working, verified precedent for the "index layer, not physical move" approach** — `writeups/` (source #24) — including a checkable-link discipline that mirrors Bazel's core lesson (source #18) that a manifest is only trustworthy if it's periodically verified, not just written once.
4. **The repo's two traceability axes are asymmetric.** `matches/*/` is already well-organized by one axis (per-match). The user's actual pain point is the *other* axis — per-question-type — which currently has no folder of its own anywhere.

Given those constraints, four candidate approaches, not mutually exclusive:

### Option A — Full physical reorg by unit-of-work
Move/copy question-type-relevant scripts, data extracts, and docs into new topic-named directories (e.g. `topics/cards/`), package-by-feature style.
- **Effort:** Very high. ~855 files, no single unambiguous unit boundary (a script often serves multiple question-types; data panels are shared across all of them).
- **Git-history impact:** Significant — `git mv` preserves blame reasonably well for untouched files, but many of the scripts/data would need to be split, symlinked, or duplicated rather than simply moved, which does break history-following.
- **Breaks existing content:** Would invalidate exact-path references baked into `ML_EXPERIMENTS_NOTEBOOK.md`, `JTC_PROJECT_WRITEUP.md`, `PAPER_REVISION_NOTES.md`, and every `matches/*/MANIFEST.md`, all of which cite current paths verbatim (per `REPO_MAP.md`).
- **Human-review quality:** Would be excellent *if* fully executed and kept current — but Turing Way's own separation principle (source #11) suggests fighting this is fighting against the grain of how this project's data is actually shared, likely producing duplication and drift rather than clarity.
- **Agent-grep quality:** Excellent once done, but the ongoing maintenance burden (every new match/backtest has to be filed correctly into every topic it touches) is high and easy to let slip, which the project's own convention of "append, don't hold back" (`REPO_MAP.md`'s own stated status note) suggests would be hard to sustain solo at ~10hrs/day pace.

### Option B — Lightweight cross-cutting topic index (Zettelkasten/manifest-style, zero physical moves)
Add a small set of per-topic markdown manifests (e.g. `TOPIC_INDEX/cards.md`, `TOPIC_INDEX/sot.md`) — each one a table of exact paths (script, data, preregistration, rule doc, relevant match sub-files) plus a one- or two-sentence "current verdict" (mirroring `ml/backtests/`'s own PASS/FAIL verdicts). Optionally add a matching one-line backlink comment in each governed file (source #21's e-ADR idea, simplified).
- **Effort:** Low-to-medium. Comparable in scope to writing `REPO_MAP.md` itself, but organized by topic instead of by directory — could reuse much of the same research/verification labor.
- **Git-history impact:** None — pure addition.
- **Human-review quality:** Good — a reviewer greps or opens one file and sees every governing artifact for a topic, verdict included, without needing to already know the repo's directory conventions.
- **Agent-grep quality:** Good, and directly aligned with Anthropic's stated "lightweight identifier" pattern (source #3) — but only as good as the maintenance discipline behind it; needs the same kind of link-verification script `writeups/` already uses (source #24) to avoid silent staleness, since nothing enforces the index staying accurate the way a physical file location would.
- **Risk:** A second index (alongside `REPO_MAP.md`) is another thing to remember to update; without an automated check it can drift the same way `JTC_PROJECT_WRITEUP.md` itself is already flagged as one-day-stale relative to `PAPER_REVISION_NOTES.md`.

### Option C — Contained reorg of the newest, most self-contained subsystem, index layer everywhere else
Physically reorganize only `ml/backtests/` (37 files, all dated the same day, cross-referenced mostly within itself per `REPO_MAP.md` §5) into topic subfolders (`ml/backtests/sot/`, `ml/backtests/cards/`, `ml/backtests/corners/`, `ml/backtests/offsides/`, plus a `shared/` for `lib_hierarchical_backtest.R` and the PIT-Elo panel builders that genuinely serve every topic) — since this is the one area of the repo that is already naturally question-type-shaped (each PREREGISTRATION doc already maps 1:1 to a topic) and has the smallest blast radius of cross-references to break. Leave `matches/`, `data/`, and root-level MD files as-is, and extend the `writeups/` pattern (already proven, source #24) as the cross-cutting index for everything outside `ml/backtests/`.
- **Effort:** Medium, tightly scoped.
- **Git-history impact:** Moderate but contained — 37 files, `git mv` mostly viable since these are largely untouched-since-creation, same-day scripts.
- **Human-review quality:** Very good for the ML/backtest layer specifically (the part most likely to face a "did you validate this properly" audit); leaves the older, harder-to-move layers (`matches/`, root MDs) exactly as reviewable as they are today — i.e., no regression, targeted improvement.
- **Agent-grep quality:** Very good for the reorganized subsystem; the rest of the repo relies on Option B/D layered on top for the same benefit.
- **Risk:** Splits the repo into "the well-organized new part" and "the legacy layer-organized part," which is honest about the repo's actual history but could read as inconsistent to a reviewer unless explicitly called out (e.g., in `REPO_MAP.md` itself) as a deliberate, dated choice.

### Option D — Nested CLAUDE.md/skills + human-readable topic index, single source of truth
Combine B with Anthropic's own native mechanism (source #2): write the per-topic manifests as Option B describes, but *also* expose the highest-traffic ones as `.claude/skills/<topic>-pricing/SKILL.md` files (e.g. `cards-pricing`, `sot-pricing`) whose frontmatter `description` triggers on the relevant keywords, so a Claude Code session working on a cards question loads the topic's file list automatically rather than the researcher having to remember to point it there. The skill file and the human-readable markdown manifest can share the same underlying table (a skill is essentially a markdown file with YAML frontmatter, so this is close to zero extra authoring cost over Option B alone).
- **Effort:** Low-to-medium — marginal cost over Option B once B exists, since it reuses the same content in a slightly different file location/format.
- **Git-history impact:** None.
- **Human-review quality:** Identical to Option B (a human reads the same markdown table, whether it sits in `TOPIC_INDEX/` or `.claude/skills/`).
- **Agent-grep quality:** Best of all four options for the *specific* case of a live Claude Code session, since skills load automatically on relevant keywords per Anthropic's own nested-context mechanism (source #2, #23) rather than requiring the agent to already know to grep for a topic-index directory — directly closes the "AI agent needs to quickly gain correct context" half of the brief.
- **Risk:** Two file locations for conceptually one artifact (unless carefully kept as one source of truth with the skill file symlinking or `@`-importing the manifest, per CLAUDE.md's documented `@path/to/import` syntax) — needs a clear convention to avoid drift between the two.

None of these four are mutually exclusive — B and D in particular are naturally the same content in two forms, and C is orthogonal to whichever of B/D gets chosen for the rest of the repo. This is intentionally left as an open decision for a follow-up conversation, not resolved here.

---

## What to avoid

- **Don't do a big-bang full physical reorg (Option A) without first checking how many existing documents hard-code current paths.** `ML_EXPERIMENTS_NOTEBOOK.md`, `JTC_PROJECT_WRITEUP.md`, `PAPER_REVISION_NOTES.md`, and every `matches/*/MANIFEST.md` cite exact current paths (confirmed via `REPO_MAP.md`); a reorg without a redirect/compatibility pass would silently break a large fraction of this project's own existing cross-references.
- **Don't invent a bespoke index format or adopt heavyweight tooling (a graph database, an Obsidian vault, a custom retrieval index) when the plain-markdown-table-plus-relative-links approach already works in this exact repo** (`writeups/README.md`'s Standing Decisions table, `REPO_MAP.md` itself) and satisfies both Turing Way's "conventional folder structure" principle (source #11) and Anthropic's "building effective agents" simplicity principle (source #4). Building Effective Agents explicitly warns against frameworks that "create extra layers of abstraction" beyond what's needed.
- **Don't write a topic index as prose/narrative only.** Per Anthropic's context-engineering guidance (source #3) and the NeurIPS checklist's per-claim-citation discipline (source #13), each topic-index entry should be a machine-parseable table of exact paths, not a paragraph that merely mentions files in passing — narrative burial is exactly what makes the current repo hard to grep.
- **Don't let a new index go unverified.** `writeups/README.md`'s own 100-link Python verification check (source #24) is the concrete, already-proven precedent to reuse — any new topic-index layer should get the same kind of automated existence-check, or it will silently drift the way `JTC_PROJECT_WRITEUP.md` itself is already flagged (one day after being frozen) as stale relative to the live dataset.
- **Don't apply "package by feature" as a blanket rule without checking which files are genuinely shared vs. genuinely topic-specific first** (source #16-17's caveat) — this repo's data panels are shared across every question-type backtest simultaneously via `lib_hierarchical_backtest.R`, so a literal feature-based data reorg fights the project's own no-duplicate-raw-data discipline; the *reasoning/decision* layer (preregistrations, rules, postmortems) is a much better candidate for feature-based grouping than the *data* layer is.
- **Don't conflate "documenting a topic" with "moving a topic."** Every converging source in Buckets 3 and 5 (Turing Way's compendium principles, DVC's dvc.yaml, Kedro's Data Catalog, Datasheets' DAG-anchor pattern, Bazel's BUILD files, ADRs, Zettelkasten) solves traceability by adding a *pointer/declaration layer*, not by relocating the underlying artifacts — that convergence across six independent fields is itself evidence this is the right general shape of fix for this repo's problem, whatever the specific format ends up being.

---

## Notes on access limitations encountered during this research

- **javapractices.com** (source #15) returned "certificate has expired" on direct WebFetch — content reconstructed from multiple independent search-result summaries that directly quote/paraphrase the page, not a first-hand read.
- **Cookiecutter Data Science's "opinions" sub-pages** (linked from the main page for deeper rationale) were not individually fetched; the top-level page's stated rationale was used as-is and flagged as thin where the page itself deferred to linked sub-pages.
- **The Turing Way's top-level "Guide for Reproducible Research" page** (source #10) is a navigation hub with limited direct content; the substantive structural guidance came from the two linked sub-pages (sources #11-12), which were fetched directly and are the ones actually cited for specifics.
- **Google Cloud's MLOps architecture page, DVC's redirect-resolved project-structure page, and several Bucket 5/6 sources** (Bazel/monorepo blog posts, OpenAI's 88-AGENTS.md figure, javapractices' Medium/WordPress corroborations) were verified via search-result content rather than independently re-fetched in full within this pass — flagged per-source above rather than presented as first-hand reads.
- No source in any bucket was invented; every numbered source above has a real, checkable URL, and every access failure or partial-verification is disclosed at the point of use rather than papered over.
