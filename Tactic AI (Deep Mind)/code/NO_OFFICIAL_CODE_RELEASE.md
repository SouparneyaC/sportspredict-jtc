# Official code release: none found

Checked (2026-07-09):
- `github.com/google-deepmind` organization (via GitHub search API, `q=tacticai org:google-deepmind`) — 0 results.
- `github.com/deepmind` (legacy org, now redirects to google-deepmind) — no TacticAI repo.
- General GitHub search for "tacticai" — ~21 results, all third-party/unofficial: student projects, personal reproductions (some explicitly built on public StatsBomb open data to approximate the GNN architecture, e.g. `AmauryLeChaffotec/tacticai-corners`, `mattr-ta95/tactic-ai-recreation`, `srinivasand04/tacticai-lite`), and unrelated apps that happen to share the name. None are official Google DeepMind releases, none are endorsed/linked from DeepMind's own blog post or the Nature Communications paper.
- The Nature Communications paper's own Code Availability statement (see supplementary/paper) does not point to a public repository — the described "Data availability" is that underlying Liverpool FC tracking data is proprietary and not shared; code equivalent is likewise not released.
- The only genuinely official artifact found is the Zenodo notebook (`TacticAI_Nature_Communications_Figure_data_and_code.ipynb`, CC-BY-4.0), saved in `../supplementary/`. That notebook reproduces the paper's **figures and statistical analysis only** — it is not the TacticAI model/training code itself.

**Conclusion: Google DeepMind has not publicly released the TacticAI model code.** Do not spend further time searching for it; if a future official release appears it would most likely surface at `github.com/google-deepmind` or be linked from the DeepMind blog post.
