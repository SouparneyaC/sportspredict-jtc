# Mexico vs Ecuador — 2026-06-30
**Result: Mexico 2-0 Ecuador | RBP: +154.20 | 11/15 beat crowd**

Round of 32, WC2026 knockout stage.

---

## Files in this folder

| File | What it contains |
|------|-----------------|
| `01_espn_data.json` | ESPN API box scores for all 6 group matches + player stat profiles (Jimenez, Plata, Valencia, Gimenez) |
| `02_smarkets_markets.json` | All Smarkets markets captured from event 45161448 — liquidity status, implied lambdas, RULE8 trigger |
| `03_model_derivations.json` | All scipy computations — brentq lambda fits, Skellam for SOT comparison, thinned Poisson for players, time-window scaling |
| `04_rules_applied.json` | Every named rule evaluated — whether it fired, trigger value, and effect on each question |
| `05_estimates.json` | Final 15 submitted probability estimates with full reasoning and pick tier |
| `06_post_match_results.json` | Actual outcomes, per-question RBP, beat/below crowd breakdown, key lessons |
| `07_instrument_trace.json` | **The key file** — each question traced through all 5 layers: raw source → processing → rule → category → estimate → outcome → RBP |
| `bash_log.txt` | Verbatim bash session log — all API calls, raw outputs, scipy commands run |

---

## Match context

- **Mexico** (43.3% win): Clinical, 3 clean sheets in group stage. Averaged only 1.67 corners and 4.33 SOT — structurally low-volume despite 3 wins.
- **Ecuador** (23.0% win): Bimodal attacking profile — 15 SOT vs Curacao (outlier) vs 1+3 SOT in competitive matches. Finishing crisis broke vs Germany.
- **RULE8 fired hard**: Draw probability = 34.25% (highest of any knockout match). All comparison props shaded toward 0.50.
- **All player markets illiquid**: Unlike FRA-SWE, no bid/offer existed for any anytime goalscorer or player prop on Smarkets. Q1 and Q5 were purely model-based.

---

## Biggest wins

| Q | Topic | Us | Crowd | RBP |
|---|-------|-----|-------|-----|
| 12 | 3+ offsides (NO) | 0.28 | 0.55 | +49.58 |
| 13 | Goal before break (YES) | 0.40 | 0.34 | +19.83 |
| 2 | 2H more goals (NO) | 0.40 | 0.49 | +18.96 |
| 6 | MEX 6+ SOT (NO) | 0.19 | 0.35 | +23.44 |

---

## Biggest losses

| Q | Topic | Us | Crowd | RBP |
|---|-------|-----|-------|-----|
| 10 | 9+ corners (YES) | 0.40 | 0.47 | -11.80 |
| 9 | MEX wins (YES) | 0.43 | 0.48 | -7.22 |
| 1 | Jimenez scores (YES) | 0.27 | 0.31 | -6.32 |

---

## Key lesson from this match

**Q12 (offsides) was the campaign's largest single-question win (+49.58 RBP).**
Ecuador's ESPN box scores showed 0 offsides vs CIV and 1 vs GER — structural low-offside team. The crowd priced generic WC offsides at 55%. Our match-specific ESPN read gave us 28%. Outcome: fewer than 3 offsides. This is the definitive proof that per-match ESPN data beats the crowd's generic priors.
