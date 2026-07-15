#!/usr/bin/env Rscript
# lib_hierarchical_backtest.R
# ----------------------------
# Reusable walk-forward backtest function, generalized from
# walk_forward_sot_backtest.R so the same PIT-safe protocol runs identically
# for every stat family (cards, corners, offsides, SOT) -- one codepath, not
# four copy-pasted scripts that could silently drift apart.
#
# source()'d by run_all_family_backtests.R; not meant to be run directly.

suppressPackageStartupMessages({
  library(lme4)
  library(dplyr)
})

run_family_backtest <- function(df, response_col, family_label, k_shrink = 5, min_train = 20, use_own_elo = FALSE) {
  df <- df[!is.na(df[[response_col]]) & !is.na(df$elo_diff_pre), ]
  if (use_own_elo) df <- df[!is.na(df$elo_pre), ]
  df$match_date <- as.Date(df$match_date)
  df <- df[order(df$match_date, df$match_id), ]
  df$y <- df[[response_col]]
  df$own_elo_pre_100 <- df$elo_pre / 100
  formula_rhs <- if (use_own_elo) "elo_diff_pre_100 + own_elo_pre_100 + data_source + (1 | team_name)"
                 else "elo_diff_pre_100 + data_source + (1 | team_name)"
  model_formula <- as.formula(paste("y ~", formula_rhs))

  wc26_dates <- sort(unique(df$match_date[df$data_source == "espn_boxscore"]))
  results <- list(); row_i <- 1; fit_failures <- 0

  for (d in wc26_dates) {
    d <- as.Date(d, origin = "1970-01-01")
    train <- df[df$match_date < d, ]
    test  <- df[df$match_date == d & df$data_source == "espn_boxscore", ]
    if (nrow(train) < min_train || nrow(test) == 0) next

    global_mean <- mean(train$y, na.rm = TRUE)
    team_stats <- train %>%
      group_by(team_name) %>%
      summarise(n = sum(!is.na(y)), team_mean = mean(y, na.rm = TRUE), .groups = "drop")

    fit <- tryCatch(
      suppressWarnings(glmer(model_formula,
            data = train, family = poisson(link = "log"),
            control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5)))),
      error = function(e) NULL
    )
    if (is.null(fit)) { fit_failures <- fit_failures + 1; next }

    for (i in seq_len(nrow(test))) {
      row <- test[i, ]
      ts <- team_stats[team_stats$team_name == row$team_name, ]
      n <- if (nrow(ts) == 0) 0 else ts$n
      tm <- if (nrow(ts) == 0) global_mean else ts$team_mean
      lambda_baseline <- (n * tm + k_shrink * global_mean) / (n + k_shrink)
      lambda_global <- global_mean

      newdata <- data.frame(elo_diff_pre_100 = row$elo_diff_pre / 100,
                             own_elo_pre_100 = row$elo_pre / 100,
                             data_source = factor("espn_boxscore", levels = levels(train$data_source)),
                             team_name = row$team_name)
      lambda_hier <- tryCatch(as.numeric(predict(fit, newdata = newdata, type = "response", allow.new.levels = TRUE)),
                               error = function(e) NA)
      if (is.na(lambda_hier) || lambda_hier <= 0) next

      actual <- row$y
      thresh <- round(lambda_baseline)
      results[[row_i]] <- data.frame(
        family = family_label, match_id = row$match_id, match_date = as.character(d),
        team_name = row$team_name, opponent_name = row$opponent_name, actual = actual, n_prior = n,
        lambda_baseline = lambda_baseline, lambda_global = lambda_global, lambda_hier = lambda_hier,
        nll_baseline = -dpois(actual, lambda_baseline, log = TRUE),
        nll_global   = -dpois(actual, lambda_global, log = TRUE),
        nll_hier     = -dpois(actual, lambda_hier, log = TRUE),
        threshold = thresh,
        brier_baseline = (1 - ppois(thresh - 1, lambda_baseline) - as.numeric(actual >= thresh))^2,
        brier_hier      = (1 - ppois(thresh - 1, lambda_hier) - as.numeric(actual >= thresh))^2
      )
      row_i <- row_i + 1
    }
  }
  cat(sprintf("[%s] folds skipped on fit failure: %d\n", family_label, fit_failures))
  bind_rows(results)
}

summarize_backtest <- function(res, family_label) {
  match_level <- res %>%
    group_by(match_id) %>%
    summarise(nll_baseline = mean(nll_baseline), nll_hier = mean(nll_hier), .groups = "drop")
  match_level$diff <- match_level$nll_baseline - match_level$nll_hier
  tt <- t.test(match_level$diff)
  set.seed(20260714)
  boot <- replicate(2000, mean(sample(match_level$diff, replace = TRUE)))
  ci90 <- quantile(boot, c(0.05, 0.95))
  data.frame(
    family = family_label, n_team_matches = nrow(res), n_matches = nrow(match_level),
    nll_baseline = mean(res$nll_baseline), nll_hier = mean(res$nll_hier),
    corr_baseline = suppressWarnings(cor(res$actual, res$lambda_baseline)),
    corr_hier = suppressWarnings(cor(res$actual, res$lambda_hier)),
    mean_diff = mean(match_level$diff), t_stat = tt$statistic, p_value = tt$p.value,
    ci90_lo = ci90[1], ci90_hi = ci90[2],
    raw_pass = ci90[1] > 0
  )
}
