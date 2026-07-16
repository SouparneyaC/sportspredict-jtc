# Q5, Q7, Q8, Q10 — timing and compound-event walk-forward backtest summary

Full detail / scripts: [`topics/cards/card_timing_panel.py`](<../../topics/cards/card_timing_panel.py>) +
[`topics/cards/card_timing_panel.csv`](<../../topics/cards/card_timing_panel.csv>) (new panel, per-team
card timing — built this session, extends the existing count-only
[`referee_card_panel.csv`](<../../topics/cards/referee_card_panel.csv>)).
Backtest script: [`ml/backtests/timing_compound_events_backtest.py`](<../../ml/backtests/timing_compound_events_backtest.py>).
Results: [`ml/backtests/timing_compound_events_backtest_results.csv`](<../../ml/backtests/timing_compound_events_backtest_results.csv>)
(per-match, per-question walk-forward predictions) and
[`ml/backtests/timing_compound_events_backtest_summary.csv`](<../../ml/backtests/timing_compound_events_backtest_summary.csv>)
(the 4-row rollup).

## What this tests

Four questions with no existing dedicated panel or backtest:

- **Q5** "Will at least one goal be scored in each half?" (regulation, 90' + stoppage)
- **Q7** "Will a goal be scored during first- or second-half stoppage time?" (regulation)
- **Q8** "Will both teams receive at least one card?" (regulation)
- **Q10** "Will a card be shown before the first goal of the match? (resolves No if neither a card nor a
  goal occurs)" (regulation)

## Methodology: empirical base rates, not a fitted model

Matches this project's already-established judgment for both families, not a new attempt at a GLMM:
cards failed a hierarchical Poisson GLMM **twice**, including a targeted refit adding referee/fouls/
knockout-stage covariates (`topics/cards/README.md`); rare-event timing is separately documented as
"priced from empirical base rates, not a fitted model" due to window-definition fragility
(`topics/rare-event-timing/README.md`, `BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md`). Fitting a
third model on an even thinner per-question slice of the same data would be overfitting a family that
has already told us twice it doesn't support one.

Walk-forward discipline mirrors `ml/backtests/lib_hierarchical_backtest.R`'s `run_family_backtest()`:
matches sorted by date; for every test date `d`, the predicted rate uses only matches with
`date < d` (never same-day-or-later); a 5-match warm-up (`MIN_TRAIN=5`) is required before a match enters
scoring, dropping the first 6 matches (June 11-13, 2026) for lack of prior data. n=94 of 100 matches
scored per question after warm-up.

**New panel:** `card_timing_panel.py` parses `data/processed/espn_raw_events/*.json` — confirmed by
direct comparison to be a strict superset of every ESPN dump findable under `matches/*/` (65 unique
event_ids there, all already present in the 101-file `espn_raw_events` corpus under different naming
conventions), so no matches were gained by also parsing `matches/*/`. 100 matches have a Final/Full-Time/
AET/Pens status and usable `keyEvents`; the one non-final file (a pre-match France-Spain stub) is
correctly dropped. Cards are scoped to regulation periods (1-2) only, matching every question's own
wording — extra-time/shootout cards are parsed but excluded.

**Goal timing was re-extracted from the same source**, not pulled verbatim from
`ml/backtests/rare_event_panel.csv`, for three concrete reasons documented in the backtest script's own
header: (1) that panel's goal list has no period filter, so extra-time goals leak into regulation-scoped
questions; (2) its minute field truncates ESPN's `displayValue` to the leading digit group, which loses
exactly the "+N" stoppage tag Q7 needs; (3) its `GOAL_TYPES` text-matching set has two real gaps found
while building this script — "Goal - Free Kick" never matches ESPN's actual "Goal - Free-kick" string, and
"Goal - Volley" isn't in the set at all — undercounting goals by ~10 corpus-wide. This is flagged as an
independent finding on the existing panel, not fixed in that file (out of this session's scope). A direct
cross-check (printed by the backtest script) shows 12/100 matches differ from the legacy panel's goal
count, consistent with exactly these two effects.

## Judgment calls, stated plainly

**Q7 stoppage-time definition:** a goal counts as stoppage-time if ESPN's own `clock.displayValue` carries
a "+" offset (e.g. `45'+3'`, `90'+1'`) for that event. This is used *instead of* a numeric minute
threshold because `clock.value` (raw seconds) was found, by direct inspection, to be **pinned to the exact
period-boundary value** (2700.0s / 5400.0s) for 473 of 502 stoppage-tagged events across every event type
checked (goals, cards, subs, delays alike) — the seconds field carries no usable stoppage information at
all in this data source. ESPN's own "+N" tag is the only reliable signal, so this rule inherits ESPN's own
judgment about exactly when regulation "ends" and stoppage "begins" each half, not an invented cutoff.

**Q10 resolution for the two cases the question text doesn't spell out:** the question only explicitly
rules "neither occurs" -> No. This backtest applies the standard single-sided-race convention: a card with
no goal ever scored resolves **Yes** (a card was shown, and no goal ever arrived to precede it); a goal
with no card ever shown resolves **No**. Verified directly that no same-instant ties occurred anywhere in
the 100-match corpus (card and first goal never land on the identical period+minute+stoppage-offset), so
no tie-break rule was actually needed in practice.

## Walk-forward results (n=94 per question, empirical rate vs. naive flat-0.5)

| Question | Brier (walk-forward) | Brier (naive 0.5) | Improvement | Verdict |
|---|---|---|---|---|
| Q5 goal-in-each-half | 0.2505 | 0.2500 | -0.0005 | No real edge over 50/50 — empirical rate (~58%) barely beats coin-flip on Brier |
| Q7 stoppage-time goal | 0.2380 | 0.2500 | +0.0120 | Modest, consistent improvement |
| Q8 both-teams-carded | 0.2571 | 0.2500 | -0.0071 | No real edge — empirical rate (~55%) is *worse* than flat 0.5 on this metric |
| Q10 card-before-first-goal | 0.2336 | 0.2500 | +0.0164 | Largest improvement of the four, still modest |

**Sample-size honesty:** none of these four Brier deltas are being claimed as statistically validated —
this is a single point-estimate comparison over n=94, not a bootstrapped/t-tested pass bar in the style of
the SOT/corners GLMM backtests. Q5 and Q8 show the empirical base rate providing essentially no advantage
over a naive 50/50 guess at this sample size (Q8's rate is *directionally worse* on Brier despite being a
non-trivial 55% base rate — a reminder that "the base rate is informative" and "the base rate beats naive
0.5 on Brier at n=94" are different claims, and only the first one holds here). Q7 and Q10 show a real but
modest edge. This is consistent with the project's standing judgment on both families: base rates are the
right tool (not a fitted model), but the win over "just guess 50/50" is real for some window-definition
questions and genuinely marginal for others — reported honestly rather than rounded up.

## Tonight's live number (all 100 matches strictly before 2026-07-15)

| Question | n | Live base rate |
|---|---|---|
| Q5 — goal in each half | 100 | **0.580** |
| Q7 — stoppage-time goal | 100 | **0.360** |
| Q8 — both teams carded | 100 | **0.550** |
| Q10 — card before first goal | 100 | **0.350** |

These are simple empirical rates over the full corpus (all matches played 2026-06-11 through 2026-07-14,
every one of them strictly before tonight's 2026-07-15 kickoff — no lookahead). Per this project's C.5
shadow-deployment rule, these are the base-rate inputs for pricing, not a claim of validated predictive
skill on this specific live match (the walk-forward table above is the honest read on how much that base
rate actually helps vs. a naive guess). Q8's ~55% both-carded rate should be read alongside `topics/cards/
README.md`'s standing conclusion that cards is a market/crowd-anchored family this tournament, not a
model-driven one — this number is context, not a strong signal.
