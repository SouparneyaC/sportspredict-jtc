#!/usr/bin/env Rscript
# walk_forward_cards_referee_backtest.R
# ----------------------------------------
# Tests the refined cards model pre-registered in
# PREREGISTRATION_cards_referee_fouls_stage.md: adds referee identity (as a
# second random intercept), each team's own PIT-safe shrunk foul rate, and
# a knockout-stage fixed effect to the model that originally failed
# (elo_diff + data_source + team only). Same walk-forward protocol as every
# other backtest this session -- refit at every fold using only strictly-
# prior data.

suppressPackageStartupMessages({library(lme4); library(dplyr)})
ROOT <- "/Users/aki/Desktop/sportspredict_research"
df <- read.csv(file.path(ROOT, "data", "processed", "unified_team_match_panel_with_referee.csv"), stringsAsFactors = FALSE)
df$cards <- df$yellow_cards + df$red_cards
df$data_source <- factor(df$data_source)
df$elo_diff_pre_100 <- df$elo_diff_pre / 100
df$own_elo_pre_100 <- df$elo_pre / 100
df$match_date <- as.Date(df$match_date)
df <- df[!is.na(df$cards) & !is.na(df$elo_diff_pre) & df$referee_name_full != "", ]
df <- df[order(df$match_date, df$match_id), ]
df$referee_name_full <- factor(df$referee_name_full)

wc26_dates <- sort(unique(df$match_date[df$data_source == "espn_boxscore"]))
k_shrink <- 5
results <- list(); row_i <- 1; fit_failures <- 0

for (d in wc26_dates) {
  d <- as.Date(d, origin = "1970-01-01")
  train <- df[df$match_date < d, ]
  test  <- df[df$match_date == d & df$data_source == "espn_boxscore", ]
  if (nrow(train) < 25 || nrow(test) == 0) next

  # PIT-safe shrunk own-foul-rate, same k=5 logic as the production baseline
  global_foul_mean <- mean(train$fouls_committed, na.rm = TRUE)
  foul_stats <- train %>% group_by(team_name) %>%
    summarise(n = sum(!is.na(fouls_committed)), team_mean = mean(fouls_committed, na.rm = TRUE), .groups = "drop")
  train$own_foul_rate_shrunk <- sapply(train$team_name, function(tm) {
    fs <- foul_stats[foul_stats$team_name == tm, ]
    if (nrow(fs) == 0) return(global_foul_mean)
    (fs$n * fs$team_mean + k_shrink * global_foul_mean) / (fs$n + k_shrink)
  })

  # cards baseline (k=5 shrinkage on cards itself, the original production method)
  global_card_mean <- mean(train$cards, na.rm = TRUE)
  card_stats <- train %>% group_by(team_name) %>%
    summarise(n = sum(!is.na(cards)), team_mean = mean(cards, na.rm = TRUE), .groups = "drop")

  fit <- tryCatch(
    suppressWarnings(glmer(cards ~ elo_diff_pre_100 + own_elo_pre_100 + data_source + is_knockout +
                              own_foul_rate_shrunk + (1 | team_name) + (1 | referee_name_full),
          data = train, family = poisson(link = "log"),
          control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 3e5)))),
    error = function(e) NULL
  )
  if (is.null(fit)) { fit_failures <- fit_failures + 1; next }

  for (i in seq_len(nrow(test))) {
    row <- test[i, ]
    cs <- card_stats[card_stats$team_name == row$team_name, ]
    n <- if (nrow(cs) == 0) 0 else cs$n
    tm <- if (nrow(cs) == 0) global_card_mean else cs$team_mean
    lambda_baseline <- (n * tm + k_shrink * global_card_mean) / (n + k_shrink)

    fs <- foul_stats[foul_stats$team_name == row$team_name, ]
    own_foul_rate_shrunk <- if (nrow(fs) == 0) global_foul_mean else (fs$n * fs$team_mean + k_shrink * global_foul_mean) / (fs$n + k_shrink)

    ref_known <- row$referee_name_full %in% levels(train$referee_name_full)
    newdata <- data.frame(elo_diff_pre_100 = row$elo_diff_pre / 100, own_elo_pre_100 = row$elo_pre / 100,
                           data_source = factor("espn_boxscore", levels = levels(train$data_source)),
                           is_knockout = row$is_knockout, own_foul_rate_shrunk = own_foul_rate_shrunk,
                           team_name = row$team_name,
                           referee_name_full = factor(row$referee_name_full, levels = levels(train$referee_name_full)))
    lambda_hier <- tryCatch(as.numeric(predict(fit, newdata = newdata, type = "response", allow.new.levels = TRUE)),
                             error = function(e) NA)
    if (is.na(lambda_hier) || lambda_hier <= 0) next

    actual <- row$cards
    results[[row_i]] <- data.frame(
      match_id = row$match_id, match_date = as.character(d), team_name = row$team_name,
      referee_known_from_history = ref_known, is_knockout = row$is_knockout, actual = actual,
      lambda_baseline = lambda_baseline, lambda_hier = lambda_hier,
      nll_baseline = -dpois(actual, lambda_baseline, log = TRUE),
      nll_hier = -dpois(actual, lambda_hier, log = TRUE)
    )
    row_i <- row_i + 1
  }
}
cat(sprintf("Folds skipped on fit failure: %d\n", fit_failures))
res <- bind_rows(results)
write.csv(res, file.path(ROOT, "topics", "cards", "cards_referee_backtest_results.csv"), row.names = FALSE)

cat(sprintf("\nn=%d team-match predictions\n", nrow(res)))
cat(sprintf("Mean NLL -- baseline: %.4f   refined (referee+fouls+stage): %.4f\n",
            mean(res$nll_baseline), mean(res$nll_hier)))

match_level <- res %>% group_by(match_id) %>%
  summarise(nll_baseline = mean(nll_baseline), nll_hier = mean(nll_hier), .groups = "drop")
match_level$diff <- match_level$nll_baseline - match_level$nll_hier
tt <- t.test(match_level$diff)
set.seed(20260714)
boot <- replicate(2000, mean(sample(match_level$diff, replace = TRUE)))
ci90 <- quantile(boot, c(0.05, 0.95))
cat(sprintf("Match-level (n=%d): mean diff=%+.4f  t=%.3f  p=%.4f  bootstrap 90%% band=[%+.4f, %+.4f]\n",
            nrow(match_level), mean(match_level$diff), tt$statistic, tt$p.value, ci90[1], ci90[2]))
cat(if (ci90[1] > 0) "PASS\n" else "FAIL (not distinguishable from baseline)\n")

cat(sprintf("\nReferee coverage: %d/%d test rows had a referee seen before (vs new/unseen)\n",
            sum(res$referee_known_from_history), nrow(res)))
