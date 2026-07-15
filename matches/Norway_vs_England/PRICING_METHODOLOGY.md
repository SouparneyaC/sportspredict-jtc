# Norway vs England — Pricing Methodology (QF, 2026-07-11)

**Match:** NOR vs ENG, WC2026 Quarterfinal. `match_id: 8fd166b3-1b8b-4834-a761-ba7caf26ed93`
**Window:** opens 2026-07-11T21:00 UTC, closes 2026-07-12T01:00 UTC.
**Venue:** Hard Rock Stadium, Miami Gardens FL. Neutral (neither team is USA/MX/CA).
**Referee:** Clément Turpin (France) — confirmed via web search, corroborated against our own ESPN data on his 2 other WC2026 matches (England-Croatia, Colombia-Ghana).

## 1. What changed after yesterday

Spain vs Belgium (2026-07-10) was priced model-only, no market data, by deliberate instruction.
The postmortem found the single worst miss of that match (Belgium 3+ SOT, priced 0.85, actual 2
SOT) had already been flagged by Smarkets pre-match — a 27pp gap, documented in that session's
own methodology doc — but the market fetch happened *after* estimates were locked, under a
"reference only" rule, so the flag was never actionable.

This session restores standard **RULE1** practice: Smarkets fetched first (see
`02_smarkets_quotes_raw.json`, pulled before any model computation), and every model-vs-market
gap over roughly 15-20 percentage points is treated as a mandatory stop-and-recheck rather than
a footnote. Six such gaps came up this session; the full log with what was checked and how each
was resolved is in `03_model_derivations.json` under `market_gap_log`.

## 2. Point-in-time Elo

Neither Norway nor England was in the existing 10-team R16 Elo replay, so a new script
(`nor_eng_qf_point_in_time_elo_replay.py`) replays both teams' full group+R32+R16 paths from
`data/processed/unified_team_match_panel.csv` (verified real scores — `results.csv` is still
NA-filled for all WC2026 games, the same staleness bug documented for Spain-Belgium).
Result: **Norway 2040.58, England 2138.54** (diff +97.97, a moderate favorite — not the
216-point blowout gap Spain had over Belgium).

## 3. The three biggest corrections this session

1. **Bellingham 2+ SOT** — 2026 empirical rate (0.60, driven by his last 2 games) vs market
   (0.28) was a 32pp gap, the largest of the session. His full major-tournament history (2022 WC,
   n=5) shows a ceiling of 1 SOT — never 2+. Historical record and market agreed against the
   recent streak; priced at **0.32**, sharply below the naive empirical read.
2. **3+ total goals / BTTS** — the Poisson model's total-goals lambda (2.254) ran well below
   both teams' actual 2026 scoring environments (England 3.2, Norway 4.2 goals/game) and below
   the market-implied lambda (2.999). Both questions were blended heavily toward market +
   empirical logs rather than the raw model output. Norway in particular has scored **and**
   conceded in literally every one of its 5 games this tournament (5/5 BTTS).
3. **Norway 4+ corners / 24+ total shots** — neither has an exact-match Smarkets line (closest
   lines are 4.5 and 25.5). Rather than mark these NA per last session's convention, an implied
   lambda was back-solved from the near-miss market line via `brentq` and re-evaluated at the
   actual threshold — a genuine methodological upgrade this session, since it uses available
   market signal instead of discarding it for a technicality.

## 4. SYMMETRIC_REGIME_COVERAGE check (explicit, both directions)

Spain-Belgium's POSTMORTEM.md flagged that the opponent-quality shading applied to Spain's own
SOT prop was never run for Belgium's. This match has the same paired-prop shape (England 6+
corners / Norway 4+ corners), so the check was run explicitly for both sides this time — see
`03_model_derivations.json`. Conclusion: no additional asymmetric shading needed, because this
matchup (+97.97 Elo, a 45/29/26 win/draw/loss split) isn't a blowout-level mismatch the way
Spain-Belgium was. That's a substantive finding from running the check, not a skipped check.

## 5. Summary table

| # | Question | Estimate | Market | Gap | Resolution |
|---|---|---|---|---|---|
| 1 | Haaland scores | 0.48 | 0.4368 | 4.3pp | Small lean above market, validated precedent from Brazil-Norway |
| 2 | Kane 2+ SOT | 0.50 | 0.4855 | 1.5pp | Market already blends form + history correctly |
| 3 | Bellingham 2+ SOT | 0.32 | 0.2813 | 3.9pp (post-correction) | Sharp correction from 0.60 empirical, see §3 |
| 4 | 3+ total goals | 0.54 | 0.5765 | 3.7pp (post-correction) | Corrected from model's 0.39, see §3 |
| 5 | Tied at HT | 0.43 | 0.4220 | 0.8pp | Model/market already agreed |
| 6 | BTTS | 0.58 | 0.6062 | 2.6pp (post-correction) | Corrected from model's 0.45, see §3 |
| 7 | England 6+ corners | 0.51 | 0.5069 | 0.3pp | Exact-match line, model/market agreed |
| 8 | Norway 4+ corners | 0.63 | 0.6010 (calibrated) | 2.9pp | Near-miss line calibration, see §3 |
| 9 | Sub scores/assists | 0.53 | NA | — | New corpus base rate (0.55, n=60) |
| 10 | Penalty OR red | 0.38 | 0.3836 | 0.4pp | Excellent model/market agreement |
| 11 | Card in each half | 0.48 | NA | — | New corpus base rate (0.4833, n=60) + Turpin n=2 |
| 12 | 24+ total shots | 0.68 | 0.6460 (calibrated) | 3.4pp | Near-miss line calibration, see §3 |
| 13 | 2H > 1H goals | 0.44 | 0.4652 | 2.5pp | Sim corrected for uniform-time artifact, see §3 |
| 14 | England more corners AND shots | 0.55 | NA | — | Compound, Skellam-based joint estimate |
| 15 | England win (regulation) | 0.48 | 0.4975 | 1.75pp | Model/market already agreed |

No question in the final table has a residual gap over 5pp against its market or corpus
cross-check — every gap that started larger than that was explicitly resolved, not left as an
unexplained discrepancy.
