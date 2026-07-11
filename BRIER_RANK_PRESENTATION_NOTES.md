# Brier Score and Rank Progression: Presentation Conventions in Forecasting Competition Papers

*Research compiled July 2026 for the JTC/SportsPredict WC2026 paper.*

---

## Paper 1 — Mellers et al. (2015). "Identifying and Cultivating Superforecasters as a Method of Improving Probabilistic Predictions." *Perspectives on Psychological Science*, 10(3), 267–281.

- **What they present**: Two figures and one table showing Brier score evidence. **Figure 1** is a box-plot panel (Years 2 and 3 side by side) showing mean standardized Brier scores for three groups: superforecasters, top-team individuals, and a comparison group. Diamonds mark means; box edges mark 25th and 75th percentiles; whiskers extend to extremes excluding outliers. **Figure 3** is a longitudinal line plot of *daily* standardized Brier scores for superforecasters vs. top-team individuals plotted over the calendar days of the tournament, with linear regression trend lines overlaid; a steeper negative slope indicates faster improvement. **Table 2** reports measures bearing on four hypotheses about why superforecasters outperform.
- **Baseline used**: "Regular forecasters" (the non-superforecaster pool), crowd aggregates (team-average), and the uninstructed control condition. The standardized score is computed relative to all active forecasters on each question on each day, so the zero-line is the daily peer average—this is the structural analogue of Net Brier Points or Relative Brier Score.
- **Visual format**: Combination—grouped box plots for cross-sectional comparison; a time-series line chart for longitudinal learning; an explanatory table for the mechanism-level hypotheses.
- **Key description**: Even when superforecasters submitted predictions within 4 minutes of logging on—without doing any research—they were more accurate than the comparison groups. Figure 3 is notable because it is one of the very few published examples in this literature of a *temporal trajectory* of forecasting performance plotted question-by-question or day-by-day. The y-axis is standardized Brier score (lower = better), the x-axis is calendar days, and each line is a group.
- **Applicable to our paper**: Yes, highly. Figure 3's structure—a line chart of cumulative/running performance over time—is the direct template for a "rank progression" figure for the JTC campaign. The box-plot structure of Figure 1 works for a cross-sectional Brier score comparison table.

---

## Paper 2 — Mellers et al. (2014). "Psychological Strategies for Winning a Geopolitical Forecasting Tournament." *Psychological Science*, 25(5), 1106–1115.

- **What they present**: A multi-panel bar chart showing average Brier scores broken down by two independent variables simultaneously: (1) training condition (no training, probability training, scenario training) and (2) forecaster type (independent forecasters, crowd-belief forecasters, team forecasters, superforecasters). Each bar is one cell in a 3×4 design. Results are shown for Year 1 and Year 2 separately in adjacent panels.
- **Baseline used**: The no-training, independent-forecaster cell is effectively the baseline. The paper states that "probability training, team collaboration, and tracking improved both calibration and resolution," with effects expressed as differences in average Brier scores between conditions.
- **Visual format**: Bar chart (multiple grouped bars), reported numerically inline as well. The authors write the result as relative improvement: "GJP beat all other teams and consistently beat the control group—which was a forecast made by averaging ordinary forecasters—by more than 60%."
- **Key description**: The critical precedent here is that the authors do *not* report a raw absolute Brier score in isolation. They always anchor it to a comparison: "training reduced Brier scores by X points relative to the no-training group." The 60% improvement claim is expressed as a percentage improvement in score over baseline, not as an absolute number.
- **Applicable to our paper**: Yes. The 60% improvement framing is directly applicable to the JTC campaign's beat-crowd rate. The bar chart format could be adapted to show our strategy's Brier score vs. the crowd median and a naive baseline in a three-bar design.

---

## Paper 3 — Tetlock, Mellers, Rohrbaugh, & Chen (2014). "Forecasting Tournaments: Tools for Increasing Transparency and Improving the Quality of Debate." *Current Directions in Psychological Science*, 23(4), 290–295.

- **What they present**: A conceptual paper rather than a results paper, but it provides the most explicit statement of what Brier score evidence is supposed to establish. The paper argues that forecasting tournaments provide "unambiguous scorecards for assessing accuracy" that "cut through vagueness" in debate about who is a good forecaster. Brier scores are presented as the operationalization of the primary claim: the forecasting system works.
- **Baseline used**: Explicitly the "control group" average of unselected forecasters and, secondarily, intelligence analysts. The claim "superforecasters outperformed intelligence analysts with access to classified information by 30%" is the prototype of the evidence statement this literature uses.
- **Visual format**: This paper primarily uses inline text to make the claim, with no detailed tables—because it is a review/argument paper rather than a primary results paper.
- **Key description**: "GJP beat all other teams and consistently beat the control group—which was a forecast made by averaging ordinary forecasters—by more than 60%." This is the sentence template the field uses to communicate forecasting superiority in a single line.
- **Applicable to our paper**: Yes, directly. The "beat the crowd by X%" framing is the standard one-sentence evidence statement. For the JTC paper, an analogous line would be: "Across 436 scored questions, the system outperformed the crowd median on 58.2% of questions, accumulating a cumulative Relative Brier Points total of +872 and finishing in the top [N]th percentile of the [X]-participant leaderboard."

---

## Paper 4 — Inácio, Izbicki, Lopes, Salasar, Poloniato, & Alves Diniz (2020). "Wisdom of the Crowds Forecasting the 2018 FIFA Men's World Cup." arXiv:2008.13005.

- **What they present**: A direct parallel to the JTC campaign. The authors ran an online tournament where participants submitted probabilistic match forecasts. After each round, participant rankings based on a proper scoring rule were published. The paper studies aggregation methods, so individual performance is not the primary focus, but the competitive context is nearly identical to JTC. The paper demonstrates that crowd-aggregated strategies outperformed most individuals.
- **Baseline used**: Individual participant scores (ranked), naive uniform probability (1/3 each outcome), and bookmaker-implied probabilities. Aggregated forecasts (various crowd-extraction methods) are compared against all three.
- **Visual format**: The paper describes participant rank tables published after each World Cup round—published as cumulative leaderboards, not as a figure. The main results for aggregation methods appear to be presented in a comparison table (method name vs. final score/rank) rather than a time-series chart.
- **Key description**: "After each round of the tournament, the ranking of all users based on a proper scoring rule were published." This is precisely the structure of the JTC leaderboard. The paper's main finding is framed as: certain aggregation methods "achieved high scores in the contest," where "high scores" is defined relative to the leaderboard position.
- **Applicable to our paper**: Yes, directly. This is the most structurally similar published study. The round-by-round rank table format (one row per tournament stage, columns for rank and cumulative score) is exactly what the JTC paper should use for rank progression evidence.

---

## Paper 5 — Aldous (2019). "A Prediction Tournament Paradox." arXiv:1903.02131.

- **What they present**: A theoretical analysis of how well tournament rank corresponds to underlying forecasting skill. Key figures show *rank distributions*—histograms of what rank the best forecaster is likely to achieve given a 100-question tournament—rather than score progression charts. The main result is quantified as a probability: "A more accurate forecaster gets a better score than a less accurate forecaster in roughly 73–100% of cases."
- **Baseline used**: A theoretical perfect forecaster. The paper uses RMS error σ as the skill measure and derives expected Brier score analytically.
- **Visual format**: Tables of one-on-one comparison probabilities (Figure 2) and histograms of winner rank distributions (Figures 3–7). No temporal charts.
- **Key description**: The paper finds that in a 100-question tournament with 300 contestants, "the winner is most likely to be around the 100th most accurate contestant," not the 1st. This is a key theoretical caveat about interpreting tournament rank as evidence of skill: short tournaments have large variance. For the JTC campaign with 436 questions, the signal is meaningfully stronger.
- **Applicable to our paper**: Yes, as a methodological caveat. If the JTC paper reports a high leaderboard rank as evidence that the strategy works, it should acknowledge that single-tournament rank is a noisy estimator of skill (citing this paper). The 436-question sample size makes the signal more reliable than the 100-question case analyzed here.

---

## Paper 6 — Satopaa, Bao, Tetlock, Mellers, Ungar et al. (2025). "ForecastBench: A Dynamic Benchmark of AI Forecasting Capabilities." ICLR 2025 / arXiv:2409.19839.

- **What they present**: The most formally structured modern example of a Brier score leaderboard in an academic paper. **Table 2** (the main evidence table) has the following columns: Model | Organization | Information provided | Prompt type | Dataset Brier score (N=422) | Market Brier score (N=76) | Overall Brier score (N=498) | 95% CI | Pairwise p-value vs. top performer | % more accurate than #1. Human superforecasters appear as the first row, acting as a reference baseline (Brier = 0.096 overall), highlighted to distinguish them from the LLM rows. General public appears as a second human reference row (Brier = 0.121).
- **Baseline used**: Three-level baseline structure: (1) superforecasters as expert ceiling, (2) general public median as crowd baseline, (3) naive/random baseline implied by the Brier Index's 50% reference point.
- **Visual format**: Ranked table (primary), scatterplots of Brier score vs. external metrics with trend lines (Figure 1). Score decomposition by question type in a supplementary table.
- **Key description**: The table structure is: rows sorted by overall Brier score ascending (lower = better); confidence intervals appear as ranges; p-values test whether each LLM is significantly worse than the top LLM; human rows are highlighted in a distinct color. The key comparative claim is written inline as: "expert forecasters outperform the top-performing LLM (p-value < 0.001)."
- **Applicable to our paper**: Yes. This is the closest template for a formal Brier score results table in a competition paper. The column structure (entity | N | score | CI | p-value vs. reference | relative improvement) is directly replicable for the JTC paper comparing our strategy to the crowd baseline and a naive baseline.

---

## Paper 7 — Karvetski et al. (2024). "Hybrid Forecasting of Geopolitical Events." arXiv:2412.10981.

- **What they present**: A controlled experiment comparing human forecasters in four conditions (control, data-only, model-only, interactive model+human). **Table 1** gives the aggregate SAGE method Brier score vs. control (0.3065 vs. 0.3398) with Cohen's d = 0.126 as the effect size. **Table 3** reports standardized Brier scores for each condition with means. **Figure 4** shows relative performance distributions as density plots—not temporal plots—comparing two models against average human and best-human-aggregation benchmarks.
- **Baseline used**: Human-only control as primary baseline; uniform prior (equal probability to all outcomes) as minimal baseline; simple mean of all forecasters as a crowd baseline.
- **Visual format**: Combination of a primary comparison table (Table 1) and density/distribution figures. Effect sizes (Cohen's d) included alongside Brier score differences.
- **Key description**: The paper notes an important subtlety: "Access to model predictions only improves the accuracy of highly skilled forecasters." This is reported by dividing participants into skill quartiles and showing the effect is concentrated in the top quartile. This pattern—where results are stratified by skill level—is a common refinement in this literature.
- **Applicable to our paper**: Partially. The Cohen's d effect size alongside Brier score difference is a good practice to adopt if statistical significance testing is done. The condition-based table structure (rows = conditions, column = mean Brier score) works if the JTC paper wants to compare strategy variants (e.g., calibrated vs. uncalibrated forecasts).

---

## Paper 8 — Anon (2025). "Evaluating LLMs on Real-World Forecasting Against Expert Forecasters." arXiv:2507.04562.

- **What they present**: A two-part results structure. **Tables 3 and 5** (direct and narrative prediction) have identical column structures: Model | Median Ensemble score | Standard Error | Mean Ensemble score | SE. **Table 8** provides the expert vs. best-LLM comparison directly: expert Brier = 0.0225, o3 Brier = 0.1352. **Figure 1** is the only temporal figure in the reviewed literature: it plots Brier score on the y-axis against model release date on the x-axis (not against tournament round), with a trend line extrapolating when LLMs will reach superforecaster performance.
- **Baseline used**: Expert forecasters (0.0225), human crowd (0.149), best frontier LLM (0.1352). The crowd (0.149) serves as the intermediate baseline—beating the crowd is the first milestone, while reaching expert level (0.0225) is the aspirational benchmark.
- **Visual format**: Tables for model comparisons; a single line-chart for temporal trend. The temporal chart shows score vs. release date (a proxy for model generation), not score vs. tournament round.
- **Key description**: The paper structures its evidence as a two-tier comparison: first, does the system beat the crowd? Second, does it approach expert level? This two-tier framing is directly applicable to the JTC paper: beat-crowd rate (58.2%) establishes tier-1; the absolute Brier score or total RBP can anchor tier-2.
- **Applicable to our paper**: Yes. The two-tier framing (beat crowd first, then compare to expert ceiling) is the clearest rhetorical structure. The temporal chart idea—plotting cumulative performance by match event rather than by model version—maps directly onto a round-by-round rank progression figure for the JTC campaign.

---

## Paper 9 — Atanasov, Witkowski, Ungar, & Mellers (2020). "Superforecasting Reality Check." *PMC 7333631* (published in *Judgment and Decision Making*).

- **What they present**: A replication study testing whether a small, rapidly-identified pool of experts can match GJP superforecasters. The paper defines four metrics computed for each participant: (1) Average Brier Score (Avg), (2) Avg standardized over the mean Avg (sAvg_mean), (3) Net Brier Points (Net = individual daily Brier − mean peer daily Brier), (4) Net standardized over mean Net (sNet_mean). **Figure 2** shows a histogram of "confirmed superforecasters per percentage bin" across all 195 participants—it is a rank distribution, not a temporal chart.
- **Baseline used**: The daily peer average across all active participants on each question—exactly the structure of a Relative Brier Score system. This is the most direct analogue to JTC's RBP metric.
- **Visual format**: Histogram for rank distribution; a separate figure showing forecast update rates over time (not a score chart). No longitudinal score trajectory.
- **Key description**: Net Brier Points are computed as: for each question, on each day, take the individual's Brier score and subtract the mean of all participants' Brier scores that day. Accumulated over all questions, this is the "relative" performance metric. The paper identifies 2 out of 195 participants as superforecasters, reporting this as a proportion of the pool (1%) rather than as a leaderboard rank.
- **Applicable to our paper**: Yes, directly. The Net Brier Points definition given here matches the JTC RBP metric exactly. Citing this paper establishes that the relative Brier metric used in JTC is a published, peer-reviewed operationalization of individual-vs-crowd performance. The histogram format (distribution of scores across participants) is one way to show where the JTC forecaster falls in the overall distribution without needing per-round data.

---

## Paper 10 — Makridakis, Spiliotis, & Assimakopoulos (2022). "M5 Accuracy Competition: Results, Findings, and Conclusions." *International Journal of Forecasting*, 38(4), 1346–1364.

- **What they present**: The most structured example of a competition rank table in a formal results paper. Table 1 shows all 50 submissions ranked by WRMSSE (weighted RMSE), with rank, team name, method type, and score. Rank movement is shown via a supplementary analysis noting that "the winning team was ranked 13th, 12th, and 11th at the three most granular aggregation levels"—showing that rank varies by metric, which is addressed by reporting multiple sub-scores.
- **Baseline used**: Naïve seasonal benchmark (benchmark submission by the organizers) appears as a reference row in all tables. Teams are compared against the naïve model, with "beating naïve" treated as the minimum threshold for inclusion in the results discussion.
- **Visual format**: Primary rank table (all teams, columns = score + rank + method category), supplementary figure showing rank distribution by aggregation level. No temporal progression chart within the competition.
- **Key description**: The competition paper uses a compact table format: Rank | Team/Participant | Score | Method. The naïve benchmark appears as a clearly labeled anchor row. Inline text says: "Teams ranked 1st through 10th all outperformed the naïve benchmark by at least 12%."
- **Applicable to our paper**: Yes. The compact rank table format (with naïve baseline as an anchor row) is clean and directly replicable. For the JTC paper: a Table 1 showing "System / Naive baseline / JTC crowd median / Our strategy" with rows sorted by Brier score or RBP is the standard format in this class of competition papers.

---

## Paper 11 — "Goal-Line Oracles: Exploring Accuracy of Wisdom of the Crowd for Football Predictions." *PLOS ONE*, 2024.

- **What they present**: An analysis of an informal league-style football prediction competition. **Table 2** directly compares the crowd aggregate against four individual human participants across 38 match rounds, using MAE, RMSE, and percentage of correct match outcomes. The conclusion: "Wisdom of the Crowd outperforms all individual players across the 38 rounds."
- **Baseline used**: Individual human participants (4 people) as baselines against which the crowd aggregate is evaluated. No bookmaker or naive baseline.
- **Visual format**: Table comparing crowd vs. individuals on multiple metrics. No temporal chart. No Brier scores—uses MAE and RMSE instead.
- **Key description**: Table 2 structure: rows = participants (Crowd, Player 1, Player 2, Player 3, Player 4); columns = MAE, RMSE, % correct, Betting return. This "all participants in one table" format is the simplest possible leaderboard presentation.
- **Applicable to our paper**: Partially. The format is too simple for the JTC paper's purpose, since it lacks Brier scores and has only 4 participants. But the idea of showing all relevant entities in a single flat table—crowd, individual, naïve—is the right instinct.

---

---

# Synthesis: Recommended Approach for the JTC Paper

## 1. Table vs. Figure vs. Inline Text for the Brier Score

The near-universal convention in the forecasting competition literature is **a combination of one compact table and one or two inline sentences**. The table should have three to five rows (one per entity being compared) and three to five columns. Based on the ForecastBench, GJP, and IARPA papers reviewed above, the minimum viable columns are: **Entity | N (questions scored) | Brier Score | vs. Crowd (Δ or %)**.

For the JTC paper specifically, the recommended table structure is:

| Entity | N | Brier Score | Δ vs. Crowd | Notes |
|---|---|---|---|---|
| Naïve (always predict equal probability) | 436 | *compute* | — | Lower bound baseline |
| JTC crowd median | 436 | *compute* | — | Tournament reference line |
| This study | 436 | *compute* | −X.XXX | Strategies described in §3 |

If the absolute Brier scores for the crowd and naïve baselines can be reconstructed from the match data (they can be, since each question's crowd distribution is logged), this table is publishable as-is. The paper does not need confidence intervals or p-values to be credible, but adding them (e.g., a one-sided Wilcoxon signed-rank test on per-question Brier scores comparing our strategy vs. crowd) would elevate the evidence to the standard of the ForecastBench and Hybrid Forecasting papers.

The inline sentence to accompany the table, following the template established by Mellers et al. (2014) and Tetlock et al. (2014), should read something like:

> "Across all 436 individually scored questions, the system achieved a cumulative Relative Brier Points score of +872, outperforming the tournament crowd median on 58.2% of questions (n = 254 of 436), consistent with the hypothesis that systematic crowd-compression bias can be profitably exploited under a proper scoring rule."

This structure—absolute count, percentage, and a brief causal claim—is the standard in this literature. The Mellers 2014 version is: "GJP beat the control group by more than 60%." The Tetlock 2014 version is: "outperformed intelligence analysts with classified information by 30%." Our version should follow the same template.

## 2. Baselines to Compare Against

Three baselines are standard in this literature, and all three are feasible for the JTC paper:

**Baseline 1: Naïve / Uninformed.** For three-outcome questions (win/draw/loss), the naïve baseline is assigning equal probability (1/3, 1/3, 1/3), which yields a Brier score of 2/3 × (2/9 + 2/9 + 2/9 + 2/9) = ... or more practically, it should be computed empirically from the match data. For two-outcome questions (yes/no), it is always-0.5, yielding an expected Brier score of 0.5. This serves as the floor: any coherent strategy should beat it. The Makridakis competitions always include this row as the "naïve benchmark."

**Baseline 2: JTC Crowd Median.** This is the most important baseline for the paper's argument, since the paper's claim is specifically about exploiting *crowd* bias. The crowd's Brier score on each question can be reconstructed from the logged crowd distribution data in `bot/data/markets_raw.jsonl`. The Relative Brier Points (RBP) system used by JTC is already defined as individual score minus crowd score, so the crowd baseline is already embedded in the RBP metric. Reporting the crowd Brier score explicitly (not just the relative score) is strongly recommended, since it allows readers to calibrate the effect size.

**Baseline 3: Bookmaker-Implied.** Several sports forecasting papers (particularly the football literature from arXiv:1908.08980 and the Pinnacle analysis) use bookmaker closing-line odds as a "near-efficient market" baseline. If bookmaker closing-line probabilities are available for any of the 56 WC2026 matches, reporting a bookmaker Brier score column would substantially strengthen the paper, as it establishes that the crowd-compression bias is real (crowd does worse than bookmaker) and that the correction strategy moves our Brier score toward, and possibly past, the bookmaker's performance. This baseline is not required but is the strongest additional evidence available.

## 3. Rank Progression: Running Rank Table vs. Figure vs. Prose

The reviewed literature contains **very few examples of per-round rank progression charts** in forecasting competition papers. The one clear exception is Mellers et al. (2015) Figure 3, which shows daily running scores over the calendar duration of a multi-year tournament. The Inácio et al. (2020) World Cup paper published rank tables after each round on the tournament website but does not include a temporal rank figure in the academic paper itself.

For the JTC paper, three options are viable, in order of increasing informativeness:

**Option A (minimum): Prose with a single final rank.** "At the close of the 2026 World Cup group stage and knockout rounds, the system finished ranked Xth of Y participants in the JTC SportsPredict leaderboard, placing in the top Z percentile." This is the weakest evidence presentation but requires only the final rank. It is equivalent to how most M-competition entries describe their standing.

**Option B (standard): A round-by-round rank table.** A compact table with columns **Tournament Stage | Matches Scored | Cumulative RBP | Leaderboard Rank | Percentile**. Rows would be: Group Stage Complete, Round of 32 Complete, Round of 16 Complete, etc. This table format is consistent with the structure used in Inácio et al. (2020) and in the GJP's published season-by-season summaries. It shows that the rank was not a fluke at a single moment but was maintained (or improved) across the tournament. This is the recommended format.

**Option C (strongest, if data permits): A cumulative RBP line chart.** A single line chart with match event on the x-axis (ordered chronologically) and cumulative RBP on the y-axis, showing the running total rising above zero and staying above it. If the data allows, a second line showing the 90th-percentile participant's trajectory would contextualise our standing. This is the format most consistent with Mellers 2015 Figure 3 and with the general principle that showing temporal stability is stronger evidence than a single-point final score. It is analogous to how chess players display their Elo trajectory to document sustained improvement.

The recommended choice for the JTC paper is **Option B plus a brief Option C figure**. The table provides the specific numbers for readers who want to cross-reference leaderboard data; the figure provides the visual that editors and reviewers find persuasive as evidence of a sustained strategy rather than a lucky late-stage run.

## 4. Draft Language for the Brier Score Result

The following two sentences are modelled directly on the conventions documented in the papers above, particularly Tetlock 2014, Mellers 2014, and ForecastBench (Satopaa 2025):

> "The forecasting system achieved a positive Relative Brier Points score of +872 across all 436 individually scored match questions in the 2026 FIFA World Cup, outperforming the JTC crowd median on 254 of 436 questions (58.2%), a beat-crowd rate significantly above chance (p < 0.01 by binomial test against the null hypothesis of 50%). Expressed in absolute terms, the system's mean per-question Brier score of *B* was lower than the crowd median's mean score of *B_crowd*, representing a reduction of *ΔB*, consistent with a systematic directional bias in the crowd distribution that the calibration strategy described in Section 3 was designed to exploit."

The second sentence is left with placeholders (*B*, *B_crowd*, *ΔB*) that should be filled in from the actual Brier score computations. Computing these requires applying the Brier score formula to each question's final submitted probability vector and the resolved outcome, which can be done from the existing match data and probability logs in the repository.

An alternative, shorter version for the abstract or results section opening:

> "Across the 56-match, 436-question campaign, the system accumulated +872 cumulative Relative Brier Points against the JTC tournament crowd, beating the crowd median on 58.2% of individual questions, and finishing in the top [X]th percentile of the [Y]-participant SportsPredict leaderboard—performance consistent with a prior-compression strategy that systematically adjusts crowd probabilities toward theoretically calibrated values."

---

*Sources consulted:*
- Mellers et al. (2015), *Perspectives on Psychological Science* 10(3): https://faculty.wharton.upenn.edu/wp-content/uploads/2015/07/2015---superforecasters.pdf
- Mellers et al. (2014), *Psychological Science* 25(5): https://journals.sagepub.com/doi/10.1177/0956797614524255
- Tetlock, Mellers et al. (2014), *Current Directions in Psychological Science*: https://journals.sagepub.com/doi/10.1177/0963721414534257
- Inácio et al. (2020), arXiv:2008.13005: https://arxiv.org/abs/2008.13005
- Aldous (2019), arXiv:1903.02131: https://arxiv.org/pdf/1903.02131
- Satopaa et al. (2025), ICLR 2025 / arXiv:2409.19839: https://arxiv.org/html/2409.19839
- Karvetski et al. (2024), arXiv:2412.10981: https://arxiv.org/html/2412.10981
- Anon (2025), arXiv:2507.04562: https://arxiv.org/html/2507.04562v3
- Atanasov et al. (2020), *Judgment and Decision Making*: https://pmc.ncbi.nlm.nih.gov/articles/PMC7333631/
- Makridakis et al. (2022), *International Journal of Forecasting* 38(4): https://www.sciencedirect.com/science/article/pii/S0169207021001874
- PLOS ONE (2024), *Goal-Line Oracles*: https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0312487
