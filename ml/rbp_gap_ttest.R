#!/usr/bin/env Rscript
# rbp_gap_ttest.R
# ------------------
# R port of ml/rbp_gap_ttest.py. Welch's t-test on whether |our_estimate -
# crowd_estimate| (median split) associates with a different mean RBP, run
# both naively at the question level (771 rows, NOT independent -- ~15
# questions share one match's context) and correctly at the match level
# (71 rows, the truly independent unit). See the .py docstring / the
# STATSBOMB_INTEGRATION_AND_STATS_TESTS doc for why the two versions are
# expected to disagree in direction, and why the match-level one is the one
# to trust.
#
# Usage: Rscript ml/rbp_gap_ttest.R

suppressPackageStartupMessages({
  library(dplyr)
  library(car)  # for leveneTest
  library(jsonlite)
})

ROOT <- getwd()
MASTER <- file.path(ROOT, "datasets", "master_question_dataset.csv")
OUT <- file.path(ROOT, "ml", "rbp_gap_ttest_results_r.json")

load_usable <- function() {
  df <- read.csv(MASTER, stringsAsFactors = FALSE)
  usable <- df[df$actually_submitted == "True" &
                 !is.na(df$our_estimate) & !is.na(df$crowd_estimate) &
                 !is.na(df$outcome) & !is.na(df$rbp), ]
  usable$abs_gap <- abs(usable$our_estimate - usable$crowd_estimate)
  usable
}

cohens_d <- function(a, b) {
  n1 <- length(a); n2 <- length(b)
  pooled_sd <- sqrt(((n1 - 1) * var(a) + (n2 - 1) * var(b)) / (n1 + n2 - 2))
  (mean(a) - mean(b)) / pooled_sd
}

run_ttest <- function(df, label) {
  median_gap <- median(df$abs_gap)
  low <- df$rbp[df$abs_gap <= median_gap]
  high <- df$rbp[df$abs_gap > median_gap]

  tt <- t.test(high, low, var.equal = FALSE)  # Welch's by default in R
  group <- factor(c(rep("high", length(high)), rep("low", length(low))))
  values <- c(high, low)
  lev <- leveneTest(values, group)
  d <- cohens_d(high, low)

  cat("\n", strrep("=", 70), "\n", label, "\n", strrep("=", 70), "\n", sep = "")
  cat(sprintf("Median |gap| split at: %.4f\n", median_gap))
  cat(sprintf("LOW  group (abs_gap <= median): n=%d, mean RBP=%.3f, sd=%.3f\n", length(low), mean(low), sd(low)))
  cat(sprintf("HIGH group (abs_gap >  median): n=%d, mean RBP=%.3f, sd=%.3f\n", length(high), mean(high), sd(high)))
  cat(sprintf("Mean difference (HIGH - LOW): %.3f  (95%% CI: [%.3f, %.3f])\n",
              mean(high) - mean(low), tt$conf.int[1], tt$conf.int[2]))
  cat(sprintf("Welch's t-test: t=%.3f, df=%.2f, p=%.4f\n", tt$statistic, tt$parameter, tt$p.value))
  cat(sprintf("Levene's test for equal variance: stat=%.3f, p=%.4f\n", lev$`F value`[1], lev$`Pr(>F)`[1]))
  cat(sprintf("Cohen's d: %.3f\n", d))

  list(n_low = length(low), n_high = length(high),
       mean_low = mean(low), mean_high = mean(high),
       mean_diff = mean(high) - mean(low),
       ci_95 = c(tt$conf.int[1], tt$conf.int[2]),
       t_stat = unname(tt$statistic), p_value = tt$p.value,
       levene_stat = lev$`F value`[1], levene_p = lev$`Pr(>F)`[1],
       cohens_d = d, median_split = median_gap)
}

main <- function() {
  df <- load_usable()
  cat("Usable rows:", nrow(df), " | Unique matches:", length(unique(df$match)), "\n")

  question_level <- run_ttest(df, "QUESTION-LEVEL (n=771, rows are NOT fully independent -- see caveat)")

  match_level_df <- df %>%
    group_by(match) %>%
    summarise(abs_gap = mean(abs_gap), rbp = mean(rbp))

  match_result <- run_ttest(as.data.frame(match_level_df),
                             sprintf("MATCH-LEVEL ROBUSTNESS CHECK (n=%d, correctly independent unit)", nrow(match_level_df)))

  writeLines(toJSON(list(question_level = question_level, match_level = match_result),
                     auto_unbox = TRUE, pretty = TRUE), OUT)
  cat("\nWritten:", OUT, "\n")
}

main()
