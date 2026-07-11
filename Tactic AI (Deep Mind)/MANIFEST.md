# MANIFEST — TacticAI (Google DeepMind) research acquisition

Compiled 2026-07-09 by agent1 (pure acquisition pass — no analysis performed; see a separate analysis pass for interpretation).

All content below was obtained from publicly accessible, non-paywalled, non-pirated sources. No login walls or mirror/pirate sites were used. The main journal article turned out to be legitimately open access (Nature Communications is a fully open-access journal; the PDF downloaded directly, no paywall bypass involved).

---

## papers/

| File | Source URL | Description |
|---|---|---|
| `tacticai_nature_communications_2024.pdf` | https://www.nature.com/articles/s41467-024-45965-x.pdf (article page: https://www.nature.com/articles/s41467-024-45965-x) | **Primary source.** The peer-reviewed journal article: Wang, Z., Veličković, P., et al. "TacticAI: an AI assistant for football tactics." *Nature Communications* 15, 1906 (2024). Published March 19, 2024. Open access (Nature Communications is fully OA; no paywall encountered). Covers the full method (geometric deep learning / graph neural network over corner-kick player graphs), predictive tasks (receiver prediction, shot prediction), generative tactic-adjustment component, and the qualitative evaluation with Liverpool FC experts (90% preference result). |
| `tacticai_arxiv_2310.10553.pdf` | https://arxiv.org/pdf/2310.10553 (abstract page: https://arxiv.org/abs/2310.10553) | The arXiv preprint version (v2, submitted 16–17 Oct 2023), predating the final published/typeset Nature Communications version. Kept alongside the published version since preprint and camera-ready text/figures can differ slightly. Authors: Zhe Wang, Petar Veličković, Daniel Hennes, Nenad Tomašev, Laurel Prince, Michael Kaisers, Yoram Bachrach, Romuald Elie, Li Kevin Wenliang, Federico Piccinini, William Spearman, Ian Graham, Jerome Connor, Yi Yang, Adrià Recasens, Mina Khan, Nathalie Beauguerlange, Pablo Sprechmann, Pol Moreno, Nicolas Heess, Michael Bowling, Demis Hassabis, Karl Tuyls. |
| `tacticai_supplementary_information.pdf` | https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-024-45965-x/MediaObjects/41467_2024_45965_MOESM1_ESM.pdf (linked from the Nature Communications article page) | Official Supplementary Information PDF (17 pages) accompanying the Nature Communications article — additional technical/methodological detail and a "Supplementary Discussion" section contrasting TacticAI against prior art. |
| `related_precursor_and_followup_work/gameplan_arxiv_2011.09192.pdf` | https://arxiv.org/pdf/2011.09192 | **Precursor work (not TacticAI itself).** "Game Plan: What AI can do for Football, and What Football can do for AI" — the first paper in the multi-year DeepMind × Liverpool FC research collaboration (referenced in DeepMind's own TacticAI blog post as the starting point of the partnership, incl. penalty-kick game-theoretic analysis). Included for context on the collaboration's history, not as TacticAI follow-up. |
| `related_precursor_and_followup_work/graph_imputer_scientific_reports_2022.pdf` | https://www.nature.com/articles/s41598-022-12547-0.pdf | **Precursor work (not TacticAI itself).** "Multiagent off-screen behavior prediction in football" (the "Graph Imputer" paper), *Scientific Reports* (2022), open access. Second paper in the DeepMind × Liverpool FC collaboration, predicting off-camera player movement from broadcast video; explicitly cited in DeepMind's TacticAI blog post as the direct predecessor to TacticAI. |
| `related_precursor_and_followup_work/setpiece_graph_rl_arxiv_2606.06353.pdf` | https://arxiv.org/pdf/2606.06353 (HTML: https://arxiv.org/html/2606.06353v1) | **Academic follow-up work that cites/builds on TacticAI.** "Maximising the Set-Piece Return: Optimising Football Corner Tactics with Graph Reinforcement Learning" (Groom, Groom, Belo, Rice, Anderson, Darvariu, Wang — Univ. of Birmingham / Nottingham Forest FC / Oxford Robotics Institute), posted June 2026. References TacticAI as the state-of-the-art baseline for automated corner-kick tactic generation and proposes a graph-RL policy that goes beyond imitating historical setups; evaluated on 3,000+ Premier League corners. This is the only substantive TacticAI-citing follow-up paper found in a quick search — not an exhaustive literature review. |

## supplementary/

| File | Source URL | Description |
|---|---|---|
| `TacticAI_Nature_Communications_Figure_data_and_code.ipynb` | https://zenodo.org/records/10557063 (direct file: https://zenodo.org/records/10557063/files/TacticAI_Nature_Communications_Figure_data_and_code.ipynb?download=1) | Official Zenodo deposit (Zenodo record 10557063, uploaded by Zhe Wang, Jan 23 2024, license CC-BY-4.0) titled "TacticAI - Data & Code of Figures and Statistical Analysis." A Jupyter notebook containing the data and code used to generate the paper's figures and statistical analyses — **not** the TacticAI model/training code itself, just the figure-reproduction notebook. |

## blog_and_media/

| File | Source URL | Description |
|---|---|---|
| `deepmind_blog_tacticai.md` | https://deepmind.google/blog/tacticai-ai-assistant-for-football-tactics/ | Full text (captured via fetch, March 19, 2024 post by Zhe Wang and Petar Veličković) of Google DeepMind's official announcement blog post. Covers the research collaboration history (Game Plan → Graph Imputer → TacticAI), the three tactical questions TacticAI addresses (prediction / analysis / optimization), the geometric-deep-learning / pitch-symmetry approach, the retrieval + generative-optimization capabilities, evaluation results, and the full author list. |
| `media_coverage_notes.md` | Multiple (see file) | Short factual notes (headline, byline, outlet, date, URL, 2–4 sentence summary — no full article text reproduced) for 5 media pieces: MIT Technology Review (Mar 19 2024), SportsPro (Mar 21 2024), The Register (Mar 20 2024), and two 2026 pieces (TechMyMoney, The Next Web) covering DeepMind's newer announcement that Brazilian club Palmeiras (with the CBF) is the first team to build on an extended, open-play version of TacticAI — this is a notable recent development but is a DeepMind product claim, not a peer-reviewed result. |

## code/

| File | Description |
|---|---|
| `NO_OFFICIAL_CODE_RELEASE.md` | Documents the search performed (GitHub API search of `google-deepmind` org and general "tacticai" search, ~21 hits, all unofficial third-party reproductions/unrelated projects) and concludes: **Google DeepMind has not publicly released the TacticAI model/training code.** The only official code-adjacent artifact is the Zenodo figures notebook (see `supplementary/`), which does not include the actual GNN model implementation. |

---

## Data availability — explicitly checked, not publicly released

The underlying training data — Liverpool FC's proprietary corner-kick spatio-temporal player-tracking data (7,176 corner kicks referenced in the paper) — is **not publicly available**. The paper's own data availability statement restricts access to this data (proprietary club data, subject to Liverpool FC / data-provider agreements). No portion of the raw tracking dataset was found released on Zenodo, GitHub, or elsewhere. **Do not spend further time searching for this dataset** — it does not appear to exist in public form. (Note: several unofficial third-party GitHub reproductions instead substitute publicly available StatsBomb open event/tracking data as a stand-in, since the real Liverpool FC dataset is unavailable — those are not the original dataset, just approximations by outside developers.)

## What was NOT obtained / not applicable

- **Paywalled full text requiring bypass**: none encountered — Nature Communications is open access, so no login-wall circumvention was needed at any point.
- **Official TacticAI code repository**: does not exist publicly (see `code/NO_OFFICIAL_CODE_RELEASE.md`).
- **Raw Liverpool FC tracking dataset**: proprietary, not released (see above).
- Exhaustive citation/follow-up literature review was explicitly out of scope per task instructions ("don't go deep down this rabbit hole") — only one clear, substantive follow-up paper was captured.
