#!/usr/bin/env Rscript
# rbp_linear_regression.R
# --------------------------
# R port of ml/rbp_linear_regression.py. Regresses `rbp` on structural/rule
# features from the master dataset, using OLS with cluster-robust SEs
# (grouped by match, via sandwich::vcovCL) and the same two out-of-sample
# validation schemes (time-ordered walk-forward + GroupKFold-by-match),
# compared against a zero-parameter "predict the training-fold mean RBP"
# baseline. See the .py docstring / STATSBOMB_INTEGRATION_AND_STATS_TESTS
# doc for full methodology rationale, including the two collinearity fixes
# (elo_diff/draw_probability share one missing-indicator; rule_fired_count
# is dropped as an exact linear combination of the 9 rule dummies).
#
# Usage: Rscript ml/rbp_linear_regression.R

suppressPackageStartupMessages({
  library(dplyr)
  library(sandwich)
  library(lmtest)
})

ROOT <- getwd()
MASTER <- file.path(ROOT, "datasets", "master_question_dataset.csv")
OUT <- file.path(ROOT, "ml", "rbp_linear_regression_results_r.json")

RULE_COLS <- c("rule1_fired", "rule5_fired", "rule7_fired", "rule8_fired",
               "rule10_fired", "rule12_fired", "rule13_fired", "rule14_fired", "rule15_fired")

load_usable <- function() {
  df <- read.csv(MASTER, stringsAsFactors = FALSE)
  usable <- df[df$actually_submitted == "True" &
                 !is.na(df$our_estimate) & !is.na(df$crowd_estimate) &
                 !is.na(df$outcome) & !is.na(df$rbp), ]
  usable
}

engineer_features <- function(df) {
  X <- data.frame(row.names = seq_len(nrow(df)))
  X$gap <- df$our_estimate - df$crowd_estimate
  X$abs_gap <- abs(X$gap)
  X$elo_diff <- df$elo_diff
  X$draw_probability <- df$draw_probability
  X$rest_days_diff <- df$rest_days_diff
  X$squad_value_diff_m <- (df$squad_value_a_eur - df$squad_value_b_eur) / 1e6
  X$is_player_prop <- as.integer(df$is_player_prop == "True")
  for (col in RULE_COLS) {
    v <- df[[col]]
    X[[col]] <- as.integer(!is.na(v) & v == "True")
  }

  # elo_diff and draw_probability share one source and are missing on
  # identical rows -- one shared indicator, not two duplicate ones.
  X$elo_context_missing <- as.integer(is.na(X$elo_diff))
  X$elo_diff[is.na(X$elo_diff)] <- median(X$elo_diff, na.rm = TRUE)
  X$draw_probability[is.na(X$draw_probability)] <- median(X$draw_probability, na.rm = TRUE)

  X$squad_value_diff_m_missing <- as.integer(is.na(X$squad_value_diff_m))
  X$squad_value_diff_m[is.na(X$squad_value_diff_m)] <- median(X$squad_value_diff_m, na.rm = TRUE)

  X$rest_days_diff_missing <- as.integer(is.na(X$rest_days_diff))
  if (sum(X$rest_days_diff_missing) == 0) X$rest_days_diff_missing <- NULL
  if (any(is.na(X$rest_days_diff))) X$rest_days_diff[is.na(X$rest_days_diff)] <- median(X$rest_days_diff, na.rm = TRUE)

  y <- as.numeric(df$rbp)
  groups <- df$match
  list(X = X, y = y, groups = groups)
}

r2_mse <- function(preds, actuals) {
  mse <- mean((preds - actuals)^2)
  ss_res <- sum((actuals - preds)^2)
  ss_tot <- sum((actuals - mean(actuals))^2)
  r2 <- if (ss_tot > 0) 1 - ss_res / ss_tot else NA
  list(r2 = r2, mse = mse)
}

walk_forward_validation <- function(df, X, y) {
  dates <- as.Date(df$date)
  match_order <- df %>%
    mutate(.date = dates) %>%
    group_by(match) %>%
    summarise(min_date = min(.date)) %>%
    arrange(min_date) %>%
    pull(match)

  n_matches <- length(match_order)
  burn_in <- n_matches %/% 2

  preds <- c(); actuals <- c(); baseline <- c()
  for (i in (burn_in + 1):n_matches) {
    train_matches <- match_order[1:(i - 1)]
    test_match <- match_order[i]
    train_idx <- df$match %in% train_matches
    test_idx <- df$match == test_match
    if (sum(test_idx) == 0 || sum(train_idx) < 10) next

    fit <- lm(y[train_idx] ~ ., data = X[train_idx, ])
    p <- predict(fit, newdata = X[test_idx, ])
    preds <- c(preds, p)
    actuals <- c(actuals, y[test_idx])
    baseline <- c(baseline, rep(mean(y[train_idx]), sum(test_idx)))
  }
  list(preds = preds, actuals = actuals, baseline = baseline)
}

grouped_kfold_validation <- function(X, y, groups, n_splits = 6) {
  set.seed(42)
  unique_groups <- unique(groups)
  fold_assign <- sample(rep(1:n_splits, length.out = length(unique_groups)))
  group_to_fold <- setNames(fold_assign, unique_groups)
  row_fold <- group_to_fold[groups]

  preds <- c(); actuals <- c(); baseline <- c()
  for (k in 1:n_splits) {
    train_idx <- row_fold != k
    test_idx <- row_fold == k
    fit <- lm(y[train_idx] ~ ., data = X[train_idx, ])
    p <- predict(fit, newdata = X[test_idx, ])
    preds <- c(preds, p)
    actuals <- c(actuals, y[test_idx])
    baseline <- c(baseline, rep(mean(y[train_idx]), sum(test_idx)))
  }
  list(preds = preds, actuals = actuals, baseline = baseline)
}

main <- function() {
  df <- load_usable()
  cat("Usable rows:", nrow(df), " | Unique matches:", length(unique(df$match)), "\n")

  fe <- engineer_features(df)
  X <- fe$X; y <- fe$y; groups <- fe$groups
  cat("Features (", ncol(X), "):", paste(names(X), collapse = ", "), "\n")
  cat(sprintf("RBP: mean=%.3f, std=%.3f, min=%.2f, max=%.2f\n\n", mean(y), sd(y), min(y), max(y)))

  cat(strrep("=", 80), "\n")
  cat("IN-SAMPLE OLS (cluster-robust SEs, grouped by match)\n")
  cat(strrep("=", 80), "\n")
  fit <- lm(y ~ ., data = X)
  vcov_cl <- vcovCL(fit, cluster = groups)
  ct <- coeftest(fit, vcov = vcov_cl)
  print(ct)
  r2 <- summary(fit)$r.squared
  adj_r2 <- summary(fit)$adj.r.squared
  cat(sprintf("\nR-squared: %.4f   Adj. R-squared: %.4f\n", r2, adj_r2))

  cat("\n", strrep("=", 80), "\n")
  cat("OUT-OF-SAMPLE VALIDATION\n")
  cat(strrep("=", 80), "\n")

  wf <- walk_forward_validation(df, X, y)
  m_model <- r2_mse(wf$preds, wf$actuals)
  m_base <- r2_mse(wf$baseline, wf$actuals)
  cat(sprintf("\nWalk-forward (n_test=%d):\n", length(wf$actuals)))
  cat(sprintf("  Model:    R2=%.4f  MSE=%.2f\n", m_model$r2, m_model$mse))
  cat(sprintf("  Baseline: R2=%.4f  MSE=%.2f\n", m_base$r2, m_base$mse))
  cat("  Model beats baseline:", m_model$mse < m_base$mse, "\n")

  gk <- grouped_kfold_validation(X, y, groups)
  g_model <- r2_mse(gk$preds, gk$actuals)
  g_base <- r2_mse(gk$baseline, gk$actuals)
  cat(sprintf("\nGrouped 6-fold CV (n_test=%d):\n", length(gk$actuals)))
  cat(sprintf("  Model:    R2=%.4f  MSE=%.2f\n", g_model$r2, g_model$mse))
  cat(sprintf("  Baseline: R2=%.4f  MSE=%.2f\n", g_base$r2, g_base$mse))
  cat("  Model beats baseline:", g_model$mse < g_base$mse, "\n")

  pvals <- ct[, 4]
  sig <- names(pvals)[pvals < 0.05]
  cat("\nSignificant coefficients (p<0.05, cluster-robust):", paste(sig, collapse = ", "), "\n")

  out <- list(
    n_rows = nrow(df), n_matches = length(unique(df$match)),
    in_sample_r2 = r2, in_sample_adj_r2 = adj_r2,
    significant_at_5pct = sig,
    walk_forward = list(r2_model = m_model$r2, mse_model = m_model$mse,
                        r2_baseline = m_base$r2, mse_baseline = m_base$mse),
    grouped_kfold = list(r2_model = g_model$r2, mse_model = g_model$mse,
                         r2_baseline = g_base$r2, mse_baseline = g_base$mse)
  )
  writeLines(jsonlite::toJSON(out, auto_unbox = TRUE, pretty = TRUE), OUT)
  cat("\nWritten:", OUT, "\n")
}

main()
