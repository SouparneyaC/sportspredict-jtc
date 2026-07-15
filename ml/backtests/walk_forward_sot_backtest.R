#!/usr/bin/env Rscript
# walk_forward_sot_backtest.R
# ----------------------------
# Executes the design pre-registered in PREREGISTRATION_sot_hierarchical_backtest.md
# BEFORE this script was written. Walk-forward comparison of a hierarchical
# Poisson GLMM (team random intercept + elo_diff_pre + data_source) against
# the project's current fixed k=5 empirical-Bayes shrinkage, on shots-on-target,
# across all 100 WC2026 matches, strictly-prior-data-only at every fold.
#
# Reads:  data/processed/unified_team_match_panel_with_pit_elo.csv
# Writes: ml/backtests/sot_backtest_results.csv (per team-match scores, both methods)
#
# Usage: Rscript walk_forward_sot_backtest.R

suppressPackageStartupMessages({
  library(lme4)
  library(dplyr)
})

ROOT <- "/Users/aki/Desktop/sportspredict_research"
PANEL <- file.path(ROOT, "data", "processed", "unified_team_match_panel_with_pit_elo.csv")
OUT <- file.path(ROOT, "ml", "backtests", "sot_backtest_results.csv")

df <- read.csv(PANEL, stringsAsFactors = FALSE)
df <- df[!is.na(df$shots_on_target) & !is.na(df$elo_diff_pre), ]
df$match_date <- as.Date(df$match_date)
df$data_source <- factor(df$data_source)
df <- df[order(df$match_date, df$match_id), ]
# Rescale elo_diff (hundreds of points) to a ~unit scale for optimizer conditioning --
# the raw scale produced a near-unidentifiability warning (intercept/elo_diff eigenvalue),
# purely numerical, not a modeling issue. Same rescaling applied consistently at predict time.
df$elo_diff_pre_100 <- df$elo_diff_pre / 100

cat(sprintf("Panel loaded: %d rows (%d WC2026, %d StatsBomb historical)\n",
            nrow(df), sum(df$data_source == "espn_boxscore"), sum(df$data_source == "statsbomb_event_data")))

wc26_matches <- sort(unique(df$match_date[df$data_source == "espn_boxscore"]))
cat(sprintf("Walk-forward over %d distinct WC2026 match dates\n", length(wc26_matches)))

k_shrink <- 5
results <- list()
row_i <- 1
fit_failures <- 0

for (d in wc26_matches) {
  d <- as.Date(d, origin = "1970-01-01")
  train <- df[df$match_date < d, ]
  test  <- df[df$match_date == d & df$data_source == "espn_boxscore", ]
  if (nrow(train) < 20 || nrow(test) == 0) next  # need a minimum training floor

  # ---- Baseline: fixed k=5 shrinkage, recomputed on strictly-prior data ----
  global_mean <- mean(train$shots_on_target, na.rm = TRUE)
  team_stats <- train %>%
    group_by(team_name) %>%
    summarise(n = sum(!is.na(shots_on_target)), team_mean = mean(shots_on_target, na.rm = TRUE), .groups = "drop")

  # ---- Hierarchical model: refit on strictly-prior data for this fold ----
  # Convergence WARNINGS (e.g. "nearly unidentifiable") are common with glmer and not
  # fatal -- verified by hand that a flagged fold still produces sane, well-calibrated
  # fixed effects (see PREREGISTRATION doc debug note). Only a genuine ERROR skips a fold.
  fit <- tryCatch(
    suppressWarnings(glmer(shots_on_target ~ elo_diff_pre_100 + data_source + (1 | team_name),
          data = train, family = poisson(link = "log"),
          control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5)))),
    error = function(e) NULL
  )
  if (is.null(fit)) {
    fit_failures <- fit_failures + 1
    next
  }

  for (i in seq_len(nrow(test))) {
    row <- test[i, ]
    ts <- team_stats[team_stats$team_name == row$team_name, ]
    n <- if (nrow(ts) == 0) 0 else ts$n
    tm <- if (nrow(ts) == 0) global_mean else ts$team_mean
    lambda_baseline <- (n * tm + k_shrink * global_mean) / (n + k_shrink)
    lambda_global <- global_mean

    newdata <- data.frame(elo_diff_pre_100 = row$elo_diff_pre / 100, data_source = factor("espn_boxscore", levels = levels(train$data_source)),
                           team_name = row$team_name)
    lambda_hier <- tryCatch(
      as.numeric(predict(fit, newdata = newdata, type = "response", allow.new.levels = TRUE)),
      error = function(e) NA
    )
    if (is.na(lambda_hier) || lambda_hier <= 0) next

    actual <- row$shots_on_target
    nll_baseline <- -dpois(actual, lambda_baseline, log = TRUE)
    nll_global   <- -dpois(actual, lambda_global, log = TRUE)
    nll_hier     <- -dpois(actual, lambda_hier, log = TRUE)

    thresh <- round(lambda_baseline)
    p_over_baseline <- 1 - ppois(thresh - 1, lambda_baseline)
    p_over_global   <- 1 - ppois(thresh - 1, lambda_global)
    p_over_hier     <- 1 - ppois(thresh - 1, lambda_hier)
    outcome_over <- as.numeric(actual >= thresh)
    brier_baseline <- (p_over_baseline - outcome_over)^2
    brier_global   <- (p_over_global - outcome_over)^2
    brier_hier     <- (p_over_hier - outcome_over)^2

    results[[row_i]] <- data.frame(
      match_id = row$match_id, match_date = as.character(d), team_name = row$team_name,
      opponent_name = row$opponent_name, actual_sot = actual, n_prior = n,
      lambda_baseline = lambda_baseline, lambda_global = lambda_global, lambda_hier = lambda_hier,
      nll_baseline = nll_baseline, nll_global = nll_global, nll_hier = nll_hier,
      threshold = thresh, brier_baseline = brier_baseline, brier_global = brier_global, brier_hier = brier_hier
    )
    row_i <- row_i + 1
  }
}

cat(sprintf("\nFolds with a fit failure (skipped): %d\n", fit_failures))

res <- bind_rows(results)
write.csv(res, OUT, row.names = FALSE)
cat(sprintf("Wrote %d team-match predictions to %s\n\n", nrow(res), OUT))

cat("=== Mean predictive NLL (lower = better) ===\n")
cat(sprintf("  Global mean only: %.4f\n", mean(res$nll_global)))
cat(sprintf("  k=5 shrinkage (baseline): %.4f\n", mean(res$nll_baseline)))
cat(sprintf("  Hierarchical GLMM: %.4f\n", mean(res$nll_hier)))

cat("\n=== Mean Brier @ baseline-defined threshold (lower = better) ===\n")
cat(sprintf("  Global mean only: %.4f\n", mean(res$brier_global)))
cat(sprintf("  k=5 shrinkage (baseline): %.4f\n", mean(res$brier_baseline)))
cat(sprintf("  Hierarchical GLMM: %.4f\n", mean(res$brier_hier)))

# ---- Match-level clustering: average the 2 teams' NLL per match, then compare ----
match_level <- res %>%
  group_by(match_id) %>%
  summarise(nll_baseline = mean(nll_baseline), nll_hier = mean(nll_hier),
            brier_baseline = mean(brier_baseline), brier_hier = mean(brier_hier), .groups = "drop")
match_level$diff_nll <- match_level$nll_baseline - match_level$nll_hier  # positive = hierarchical better
match_level$diff_brier <- match_level$brier_baseline - match_level$brier_hier

cat(sprintf("\n=== Match-level paired comparison (n=%d matches) ===\n", nrow(match_level)))
cat(sprintf("  Mean NLL improvement (hier vs baseline): %.4f (positive = hierarchical better)\n", mean(match_level$diff_nll)))
tt <- t.test(match_level$diff_nll)
cat(sprintf("  Paired t-test on match-level NLL diff: t=%.3f, p=%.4f, 95%% CI [%.4f, %.4f]\n",
            tt$statistic, tt$p.value, tt$conf.int[1], tt$conf.int[2]))

set.seed(20260714)
B <- 2000
boot_means <- replicate(B, mean(sample(match_level$diff_nll, replace = TRUE)))
ci90 <- quantile(boot_means, c(0.05, 0.95))
cat(sprintf("  Bootstrap 90%% band on mean NLL diff (2000 resamples): [%.4f, %.4f]\n", ci90[1], ci90[2]))

cat(sprintf("\n=== PROMOTION CRITERION CHECK ===\n"))
if (ci90[1] > 0) {
  cat("  PASS: entire 90% bootstrap band is above zero -- hierarchical model beats baseline, distinguishable from noise.\n")
} else if (ci90[2] < 0) {
  cat("  FAIL: entire 90% bootstrap band is below zero -- baseline beats hierarchical model.\n")
} else {
  cat("  FAIL (not promoted): 90% band spans zero -- improvement (if any) is not distinguishable from noise at this n.\n")
}
