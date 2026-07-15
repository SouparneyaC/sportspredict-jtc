#!/usr/bin/env Rscript
# run_all_family_backtests.R
# ----------------------------
# Driver: runs the pre-registered (PREREGISTRATION_cards_corners_offsides_and_combined.md)
# walk-forward backtest for cards, corners, offsides (SOT already banked from
# the earlier run) using lib_hierarchical_backtest.R, then applies a
# Benjamini-Hochberg FDR correction across ALL four family p-values (the
# quant-finance-style multiple-testing safeguard pre-registered before this
# ran). Writes per-family result CSVs + a summary table.

suppressPackageStartupMessages(library(dplyr))
ROOT <- "/Users/aki/Desktop/sportspredict_research"
source(file.path(ROOT, "ml", "backtests", "lib_hierarchical_backtest.R"))

PANEL <- file.path(ROOT, "data", "processed", "unified_team_match_panel_with_pit_elo.csv")
df <- read.csv(PANEL, stringsAsFactors = FALSE)
df$data_source <- factor(df$data_source)
df$elo_diff_pre_100 <- df$elo_diff_pre / 100

df$cards <- df$yellow_cards + df$red_cards

families <- list(
  cards    = "cards",
  corners  = "corners",
  offsides = "offsides",
  sot      = "shots_on_target"
)

# Per-family results now live in topics/<slug>/ (moved out of ml/backtests/
# during the topic-based reorg); this script stays here as shared cross-family
# infra (it fits/writes all four families plus the joint FDR summary below).
OUTPUT_DIR <- list(
  sot      = file.path(ROOT, "topics", "shots-on-target"),
  cards    = file.path(ROOT, "topics", "cards"),
  corners  = file.path(ROOT, "topics", "corners"),
  offsides = file.path(ROOT, "topics", "offsides")
)

all_summaries <- list()
for (label in names(families)) {
  col <- families[[label]]
  cat(sprintf("\n=== Running %s ===\n", label))
  res <- run_family_backtest(df, col, label)
  out_dir <- if (!is.null(OUTPUT_DIR[[label]])) OUTPUT_DIR[[label]] else file.path(ROOT, "ml", "backtests")
  write.csv(res, file.path(out_dir, sprintf("%s_backtest_results.csv", label)), row.names = FALSE)
  summ <- summarize_backtest(res, label)
  all_summaries[[label]] <- summ
  print(summ)
}

summary_df <- bind_rows(all_summaries)
summary_df$p_adj_BH <- p.adjust(summary_df$p_value, method = "BH")
summary_df$fdr_pass <- summary_df$raw_pass & (summary_df$p_adj_BH < 0.10)

cat("\n\n=== FINAL SUMMARY: all 4 families, raw + FDR-adjusted ===\n")
print(summary_df[, c("family", "n_team_matches", "n_matches", "nll_baseline", "nll_hier",
                      "corr_baseline", "corr_hier", "mean_diff", "p_value", "p_adj_BH", "raw_pass", "fdr_pass")])

write.csv(summary_df, file.path(ROOT, "ml", "backtests", "all_families_summary.csv"), row.names = FALSE)
cat(sprintf("\nWrote %s\n", file.path(ROOT, "ml", "backtests", "all_families_summary.csv")))
