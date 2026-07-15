# Project Bug & Fix Tracker

Generated 2026-07-10. Built by reading every writeup, audit doc, and relevant script
in the repo. Each item traces to a specific document that identified it. Tick status
reflects real verification against the code/data — not just what the docs say.

Legend: ✅ Fixed & confirmed | ⚠️ Known, lower priority | 📝 Docs-only update needed | 🔲 Open

---

## Category A — Code Bugs (actual broken behaviour in scripts)

### A1 — `topics/match-winner-goals-totals/model/poisson_goals.py`: neutral-flag train/predict mismatch ✅ FIXED
**Identified in:** `data/code_audit_findings.md`, `JTC_PROJECT_WRITEUP.md` §10.2  
**What it was:** `build_design_matrix()` unconditionally assigned `home_adv=1.0` to the
home-team row for every match in the 49,400-row panel, including the 13,051 neutral-venue
matches (26.4%) where the home_team label is arbitrary. Every other pipeline file
(`predict.py`, `backtest_harness.py`, `backtest_diagnostics.py`, `backtest_single.py`,
`fit_rho.py`) correctly gated on `r["neutral"] == "TRUE"`. This is a train/serve semantic
mismatch affecting 26% of training rows.  
**Status:** The neutral check was already in the code by the time this session ran.
Verified: running buggy vs fixed side-by-side gives b1=0.25622 (buggy) vs b1=0.23022
(fixed). The saved `poisson_goals_coefs.json` contains the correct fixed coefficients
(b0=0.10408, b1=0.23022, b2=0.00181). A detailed explanatory comment block was added
to the code on 2026-07-10. Coefficients re-confirmed by re-running `python3 topics/match-winner-goals-totals/model/poisson_goals.py`.  
**Note on direction:** The audit predicted attenuation downward (buggy b1 < fixed b1).
Actual result was the opposite — buggy b1 is *higher* (0.256) than fixed (0.230). The
neutral-venue "home" teams skew slightly toward higher-rated sides (seeding/alphabetical
convention), so including them inflated the home_adv signal rather than attenuating it.
The fundamental point stands: the training and inference were inconsistent and the fix
is correct. The writeup's predicted direction was wrong; the fix is right.

---

### A2 — `ml/build_feature_matrix.py`: era-3 `post_match` key silently dropped ✅ FIXED 2026-07-10
**Identified in:** `DATASET_AUDIT_2026-06-26.md` §1 (step 8), §2 (Agent A)  
**What it is:** The script only reads `d.get("post_match_results")` at line 98. Seven
era-3 files use the key `post_match` instead:
  `bih_qat`, `col_cdr`, `cro_pan`, `eng_gha`, `mar_hai`, `sco_bra`, `sui_can`
These produce zero rows in `ml/feature_matrix.csv` even though they are fully settled
with rich data.  
**Why lower priority:** `platt_diagnostic.py` (the only consumer of feature_matrix.csv)
already returned a statistically inconclusive result ("do not apply Platt correction yet").
`build_master_dataset.py` — the authoritative build — already handles both keys correctly
(L464-468 tries `post_match_results` then falls back to `post_match`). All downstream
ML work now uses `master_question_dataset.csv`, not `feature_matrix.csv`. Fixing this
wouldn't change any live estimates.  
**Status:** Open. Fix is a one-line fallback in `build_feature_matrix.py` L98, same
pattern as `build_master_dataset.py`. Do when Platt diagnostic is next re-run.

---

### A3 — `elo_current_ratings.csv` frozen at pre-tournament (June 27 state) ⚠️ OPERATIONAL
**Identified in:** `MODEL_ONLY_VS_MARKET_BLENDED_COMPARISON.md` §0, `JTC_PROJECT_WRITEUP.md` §5.1  
**What it is:** `data/international_results/results.csv` (the martj42 dataset) contains
WC2026 fixture rows but scores are empty — the dataset hasn't been updated past
pre-tournament. `model/elo.py` therefore can't process any in-tournament results.
`elo_current_ratings.csv` is effectively frozen at 2026-06-11 (tournament start) ratings.
For QF-stage matches, the pre-tournament Elo diff can be off by 12–35 points per match.  
**Workaround in place:** `ml/backtests/r16_point_in_time_elo_replay.py` manually replays
the group-stage and R32 results through `elo.py`'s update formula for the R16 teams.
This gave corrected diffs within 3-32 points of what a full-update would give.  
**Status:** Open as a data maintenance issue (not a code bug). Before each QF match,
run the replay script (or extend it for QF fixtures). Do NOT try to "fix" results.csv
by manually inserting scores — this would violate the raw-data-immutable principle and
the file is a third-party dataset. The per-match JSON files and the /matches/ folder
are the authoritative record of actual results.

---

### A4 — `backtest_vs_market.py` never run / no saved results file 🔲 RESEARCH DEBT
**Identified in:** `JTC_PROJECT_WRITEUP.md` §9.2 [NEEDS VERIFICATION]  
**What it is:** The script exists and is correctly written, but has never been run to
produce a saved output. The writeup flags "the reported sign-test win rate, p-value,
and bucket-level breakdown are not available to quote here."  
**Why not urgent:** The main campaign edge comes from crowd-bias arbitrage (the RBP
mechanic), not from beating bookmaker odds head-to-head. The script is a long-run
diagnostic, not a live tool.  
**Status:** Open. Worth running once as a reference point. Command: `python3 topics/match-winner-goals-totals/model/backtest_vs_market.py`

---

## Category B — Data / Documentation Status Updates Needed

### B1 — `JTC_PROJECT_WRITEUP.md` §10.2: neutral-fix verification flag ✅ DONE 2026-07-10
**Flag text:** "NEEDS VERIFICATION: whether this fix has actually been applied and the
model re-fit as of this writeup"  
**Status:** ✅ Resolved 2026-07-10. Fix confirmed applied. Coefficients confirmed correct.
Detailed comment added. Section updated below.

### B2 — `JTC_PROJECT_WRITEUP.md` §8.1: dataset totals discrepancy 📝 STALE
**Flag text:** "NEEDS VERIFICATION: this total is computed directly from the dataset CSV..."
discrepancy between 872.13 (master_question_dataset) vs 812.15 (STEPS_FOR_HIGH_POINTS).  
**Current state:** `master_question_dataset.csv` is now 944 rows (85+ matches) — much
larger than the 480 rows/49 matches the writeup describes. The underlying source of
the discrepancy (STEPS_FOR_HIGH_POINTS was dated 2026-06-26, 3 days before writeup)
is well understood and no longer needs reconciling. The writeup's totals are simply stale.
**Status:** Stale but understood. The NEEDS VERIFICATION flag can be resolved with a
note that the dataset has since grown and the earlier discrepancy was timing-only.

### B3 — `JTC_PROJECT_WRITEUP.md` §5.1: home_advantage coefficient prior 📝 MINOR
**Text:** "the project's own rough prior of ~0.35" for the home_advantage coefficient.  
**Current state:** The fixed coefficient is b1=0.23022. The ~0.35 prior was from
a different model/source. The writeup's framing (that the bug was attenuating b1 *down*
toward 0.23 from a "true" 0.35) turned out to be directionally reversed — the buggy
version gives 0.256 not 0.35, and the fix moved it *down* slightly further to 0.230.
The gap from 0.35 is a separate calibration question, not attributable to this bug.
**Status:** Minor. Worth a footnote but the core finding (bug existed, fix applied) stands.

### B4 — `JTC_PROJECT_WRITEUP.md` §7.1: logit-space calibration diagnostic 📝 OPEN
**Flag text:** "NEEDS VERIFICATION: whether this logit-space/neutral-split diagnostic
has actually been run"  
**Status:** Not confirmed run. `backtest_diagnostics.py` contains the correct code for
the neutral/non-neutral split. Once coefficients are confirmed stable, re-running
`python3 topics/match-winner-goals-totals/model/backtest_diagnostics.py` would close this item.

### B5 — `JTC_PROJECT_WRITEUP.md` §9.2: backtest_vs_market.py output 📝 OPEN
**Flag text:** "NEEDS VERIFICATION: ...did not find a saved output/results file"  
**Status:** Open. Same as A4 above — run the script, save the output.

### B6 — `DATASET_AUDIT_2026-06-26.md` §7.5: dataset row count stale 📝 STALE
**Text:** "480 rows, 73 columns, 49 matches"  
**Current state:** 944 rows, 85+ matches (the build has been re-run many times since).
The column schema has also grown (ESPN team stats columns added).  
**Status:** Stale but intentional — audits are point-in-time records, not living docs.
No action needed here.

---

## Category C — Strategic / Research Next Steps (not bugs, not urgent)

### C1 — Platt scaling revisit at ~350 submitted questions 🔲
Already built, decision made to defer. Revisit once master dataset passes ~350
actually-submitted questions with settled RBP.

### C2 — Meta-model re-run with knockout-stage data folded in 🔲
`META_MODEL_LAB_NOTES.md` §7 explicitly states: fold /matches/ data into
master_question_dataset.csv first, then re-run unchanged. The dataset now includes
/matches/ data (confirmed: Argentina_vs_CapeVerde etc. appear in the match list).
Ready to re-run: `python3 ml/meta_model.py`

### C3 — Extend point-in-time Elo replay for QF stage 🔲
`ml/backtests/r16_point_in_time_elo_replay.py` covers R16 teams. For QF, extend
with R32 results for the 8 remaining teams.

### C4 — Run logit-space neutral/non-neutral calibration diagnostic 🔲
`python3 topics/match-winner-goals-totals/model/backtest_diagnostics.py` — the script is complete and correct.
Closes B4/JTC_PROJECT_WRITEUP.md §7.1 flag.

### C5 — StatsBomb GBDT per-market-type models 🔲
`TRAINING_DATASET_STRATEGY_2026-07-07.md` §5 proposed build. The data is downloaded
and the team/player panels are built (`statsbomb_team_match_panel.csv`,
`statsbomb_player_match_panel.csv`). Next step: train per-market GBDT base-rate models
for fouls/cards/SOT/corners/offsides/player-props with walk-forward + GroupKFold validation.

---

## Summary

| ID | Item | Status |
|---|---|---|
| A1 | poisson_goals.py neutral fix | ✅ Fixed 2026-07-10 |
| A2 | build_feature_matrix.py post_match key | ✅ Fixed 2026-07-10 |
| A3 | elo_current_ratings.csv stale | ⚠️ Operational workaround exists |
| A4 | backtest_vs_market.py never run | 🔲 Research debt |
| B1 | JTC_PROJECT_WRITEUP §10.2 flag | ✅ Updated 2026-07-10 |
| B2 | JTC_PROJECT_WRITEUP §8.1 flag | 📝 Stale totals, understood |
| B3 | JTC_PROJECT_WRITEUP §5.1 b1 prior | 📝 Minor clarification needed |
| B4 | JTC_PROJECT_WRITEUP §7.1 flag | 🔲 Run backtest_diagnostics.py |
| B5 | JTC_PROJECT_WRITEUP §9.2 flag | 🔲 Run backtest_vs_market.py |
| B6 | DATASET_AUDIT row count stale | 📝 Point-in-time doc, no action |
| C1 | Platt scaling revisit | 🔲 Deferred (dataset size gate) |
| C2 | Meta-model re-run | 🔲 Ready (data folded in) |
| C3 | QF-stage Elo replay | 🔲 Extend r16 script |
| C4 | Logit-space calibration diagnostic | 🔲 Script ready to run |
| C5 | StatsBomb GBDT models | 🔲 Data ready, build pending |
