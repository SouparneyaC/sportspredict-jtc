#!/usr/bin/env Rscript
# Tests the own-Elo-level refinement pre-registered in
# PREREGISTRATION_elo_level_refinement.md against the original model, on
# both SOT and corners (the two families that passed originally). Checks
# both promotion criteria: (1) still beats baseline, (2) top-tercile
# underprediction bias shrinks.

suppressPackageStartupMessages(library(dplyr))
ROOT <- "/Users/aki/Desktop/sportspredict_research"
source(file.path(ROOT, "ml", "backtests", "lib_hierarchical_backtest.R"))

df <- read.csv(file.path(ROOT, "data", "processed", "unified_team_match_panel_with_pit_elo.csv"), stringsAsFactors = FALSE)
df$data_source <- factor(df$data_source)
df$elo_diff_pre_100 <- df$elo_diff_pre / 100

tercile_bias_check <- function(res, label) {
  res <- res[order(res$lambda_hier), ]
  n <- nrow(res)
  top <- res[(2 * n %/% 3 + 1):n, ]
  resid_top <- top$actual - top$lambda_hier
  tt <- t.test(resid_top)
  cat(sprintf("  [%s] top-tercile mean residual: %+.3f (t=%.3f, p=%.4f)\n",
              label, mean(resid_top), tt$statistic, tt$p.value))
}

for (fam in list(c("sot", "shots_on_target"), c("corners", "corners"))) {
  label <- fam[1]; col <- fam[2]
  cat(sprintf("\n=== %s: ORIGINAL model ===\n", label))
  res_orig <- run_family_backtest(df, col, label, use_own_elo = FALSE)
  print(summarize_backtest(res_orig, label)[, c("mean_diff", "p_value")])
  tercile_bias_check(res_orig, "original")

  cat(sprintf("\n=== %s: REFINED model (own Elo added) ===\n", label))
  res_new <- run_family_backtest(df, col, label, use_own_elo = TRUE)
  print(summarize_backtest(res_new, label)[, c("mean_diff", "p_value")])
  tercile_bias_check(res_new, "refined")

  write.csv(res_new, file.path(ROOT, "ml", "backtests", sprintf("%s_backtest_results_ownelo.csv", label)), row.names = FALSE)
}
