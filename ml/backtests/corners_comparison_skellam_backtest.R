#!/usr/bin/env Rscript
# corners_comparison_skellam_backtest.R
# ----------------------------------------
# Pre-registered in PREREGISTRATION_corners_comparison.md. Tests the
# DIFFERENCE/comparison composition of the already-passing per-team corners
# hierarchical Poisson GLMM -- "does team A have more corners than team B" --
# the shape of ENG-ARG SF Q9 ("Will Argentina have more corner kicks than
# England?"). This is distinct from both:
#   (a) the per-team backtest (PASSED, topics/corners/corners_backtest_results.csv)
#       which scores each team's own predicted count against its own actual count.
#   (b) the SUM/combined-threshold composition (FAILED,
#       topics/corners/combined_corners_backtest_results.csv) which convolves
#       the two teams' predictions into Poisson(lambda_A + lambda_B).
#
# Method: same walk-forward, PIT-safe, refit-every-fold protocol as
# lib_hierarchical_backtest.R's run_family_backtest(), generalized to score
# BOTH teams jointly per match via the Skellam distribution (difference of
# two independent Poissons), rather than one team at a time.
#
# EXPLICIT LIMITATION (stated in the preregistration, not discovered here):
# the Skellam construction assumes independence between the two teams'
# within-match corner counts. This is the same assumption that broke the SUM
# composition (positive within-match correlation). It is tested empirically
# below, not asserted away -- see PREREGISTRATION_corners_comparison.md for
# the analytic reasoning on why the DIFFERENCE composition's sensitivity to
# that correlation runs the opposite direction from the SUM composition's.
#
# Usage: Rscript corners_comparison_skellam_backtest.R

suppressPackageStartupMessages({
  library(lme4)
  library(dplyr)
})

ROOT <- "/Users/aki/Desktop/sportspredict_research"
PANEL <- file.path(ROOT, "data", "processed", "unified_team_match_panel_with_pit_elo.csv")

# ---- Skellam P(X_A > X_B) for independent Poisson(lambda_A), Poisson(lambda_B) ----
# Hand-rolled (no 'skellam' package available in this environment): exact closed
# form via P(X_A > X_B) = sum_k P(X_B = k) * P(X_A > k), truncated at k = 0..N.
# At corners-scale lambdas (~1-10), truncation error at N=60 is on the order of
# 1e-15 -- effectively exact.
skellam_p_gt <- function(lambda_a, lambda_b, N = 60) {
  if (is.na(lambda_a) || is.na(lambda_b) || lambda_a <= 0 || lambda_b <= 0) return(NA_real_)
  ks <- 0:N
  pb <- dpois(ks, lambda_b)
  p_a_gt_k <- 1 - ppois(ks, lambda_a)   # P(X_A > k)
  sum(pb * p_a_gt_k)
}

brier <- function(p, outcome) (p - outcome)^2
logloss <- function(p, outcome) {
  p <- pmin(pmax(p, 1e-9), 1 - 1e-9)
  -(outcome * log(p) + (1 - outcome) * log(1 - p))
}

# ---- Load panel, same filtering/ordering discipline as lib_hierarchical_backtest.R ----
df <- read.csv(PANEL, stringsAsFactors = FALSE)
df$data_source <- factor(df$data_source)
df$elo_diff_pre_100 <- df$elo_diff_pre / 100
df <- df[!is.na(df$corners) & !is.na(df$elo_diff_pre), ]
df$match_date <- as.Date(df$match_date)
df <- df[order(df$match_date, df$match_id), ]
df$y <- df$corners

k_shrink <- 5
min_train <- 20
model_formula <- as.formula("y ~ elo_diff_pre_100 + data_source + (1 | team_name)")

wc26_dates <- sort(unique(df$match_date[df$data_source == "espn_boxscore"]))

results <- list(); row_i <- 1; fit_failures <- 0; skipped_unpaired <- 0

for (d in wc26_dates) {
  d <- as.Date(d, origin = "1970-01-01")
  train <- df[df$match_date < d, ]
  test  <- df[df$match_date == d & df$data_source == "espn_boxscore", ]
  if (nrow(train) < min_train || nrow(test) == 0) next

  # only matches with exactly two team-rows present can be scored as a comparison
  match_counts <- table(test$match_id)
  paired_ids <- names(match_counts[match_counts == 2])
  if (length(paired_ids) == 0) { skipped_unpaired <- skipped_unpaired + length(unique(test$match_id)); next }
  skipped_unpaired <- skipped_unpaired + (length(unique(test$match_id)) - length(paired_ids))

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

  lambda_baseline_for <- function(team_name) {
    ts <- team_stats[team_stats$team_name == team_name, ]
    n <- if (nrow(ts) == 0) 0 else ts$n
    tm <- if (nrow(ts) == 0) global_mean else ts$team_mean
    (n * tm + k_shrink * global_mean) / (n + k_shrink)
  }
  lambda_hier_for <- function(team_name, elo_diff) {
    newdata <- data.frame(elo_diff_pre_100 = elo_diff / 100,
                           data_source = factor("espn_boxscore", levels = levels(train$data_source)),
                           team_name = team_name)
    tryCatch(as.numeric(predict(fit, newdata = newdata, type = "response", allow.new.levels = TRUE)),
              error = function(e) NA_real_)
  }

  for (mid in paired_ids) {
    rows <- test[test$match_id == mid, ]
    rowA <- rows[1, ]; rowB <- rows[2, ]

    lam_A_hier <- lambda_hier_for(rowA$team_name, rowA$elo_diff_pre)
    lam_B_hier <- lambda_hier_for(rowB$team_name, rowB$elo_diff_pre)
    lam_A_base <- lambda_baseline_for(rowA$team_name)
    lam_B_base <- lambda_baseline_for(rowB$team_name)

    if (any(is.na(c(lam_A_hier, lam_B_hier))) || any(c(lam_A_hier, lam_B_hier) <= 0)) next

    p_hier <- skellam_p_gt(lam_A_hier, lam_B_hier)
    p_base <- skellam_p_gt(lam_A_base, lam_B_base)
    p_5050 <- 0.5

    actual_A <- rowA$y; actual_B <- rowB$y
    outcome <- as.numeric(actual_A > actual_B)

    results[[row_i]] <- data.frame(
      match_id = mid, match_date = as.character(d),
      team_A = rowA$team_name, team_B = rowB$team_name,
      actual_A = actual_A, actual_B = actual_B, outcome_A_gt_B = outcome,
      lambda_A_hier = lam_A_hier, lambda_B_hier = lam_B_hier,
      lambda_A_baseline = lam_A_base, lambda_B_baseline = lam_B_base,
      p_hier = p_hier, p_baseline = p_base, p_5050 = p_5050,
      brier_hier = brier(p_hier, outcome), brier_baseline = brier(p_base, outcome), brier_5050 = brier(p_5050, outcome),
      logloss_hier = logloss(p_hier, outcome), logloss_baseline = logloss(p_base, outcome), logloss_5050 = logloss(p_5050, outcome)
    )
    row_i <- row_i + 1
  }
}

cat(sprintf("[corners_comparison] folds skipped on fit failure: %d\n", fit_failures))
cat(sprintf("[corners_comparison] test matches skipped (not exactly 2 team-rows): %d\n", skipped_unpaired))

res <- bind_rows(results)
n <- nrow(res)
cat(sprintf("[corners_comparison] n = %d scored matches\n", n))

out_csv <- file.path(ROOT, "ml", "backtests", "corners_comparison_backtest_results.csv")
write.csv(res, out_csv, row.names = FALSE)
cat(sprintf("Wrote %s\n", out_csv))

# ---- Summary stats: paired t-test + bootstrap 90% CI vs each baseline, both metrics ----
summarize_vs <- function(res, metric_hier, metric_other, label) {
  diff <- res[[metric_other]] - res[[metric_hier]]
  tt <- t.test(diff)
  set.seed(20260715)
  boot <- replicate(2000, mean(sample(diff, replace = TRUE)))
  ci90 <- quantile(boot, c(0.05, 0.95))
  data.frame(
    comparison = label, metric = sub("_hier$", "", metric_hier),
    n = length(diff), mean_diff = mean(diff), t_stat = tt$statistic, p_value = tt$p.value,
    ci90_lo = ci90[1], ci90_hi = ci90[2], raw_pass = ci90[1] > 0
  )
}

summary_rows <- bind_rows(
  summarize_vs(res, "brier_hier", "brier_baseline", "hier_vs_baseline"),
  summarize_vs(res, "logloss_hier", "logloss_baseline", "hier_vs_baseline"),
  summarize_vs(res, "brier_hier", "brier_5050", "hier_vs_5050"),
  summarize_vs(res, "logloss_hier", "logloss_5050", "hier_vs_5050")
)

cat("\n=== corners comparison (Skellam) backtest summary ===\n")
cat(sprintf("n scored matches: %d\n", n))
cat(sprintf("mean Brier   -- hier: %.4f  baseline: %.4f  5050: %.4f\n",
            mean(res$brier_hier), mean(res$brier_baseline), mean(res$brier_5050)))
cat(sprintf("mean LogLoss -- hier: %.4f  baseline: %.4f  5050: %.4f\n",
            mean(res$logloss_hier), mean(res$logloss_baseline), mean(res$logloss_5050)))
print(summary_rows[, c("comparison", "metric", "n", "mean_diff", "t_stat", "p_value", "ci90_lo", "ci90_hi", "raw_pass")])

summary_csv <- file.path(ROOT, "ml", "backtests", "corners_comparison_backtest_summary.csv")
write.csv(summary_rows, summary_csv, row.names = FALSE)
cat(sprintf("\nWrote %s\n", summary_csv))

# ---- Live application: refit on ALL data strictly before 2026-07-15, predict tonight's SF ----
cat("\n=== Live application (shadow-deployment only): England vs Argentina SF, 2026-07-15 ===\n")

live_train <- df[df$match_date < as.Date("2026-07-15"), ]
live_fit <- suppressWarnings(glmer(model_formula,
      data = live_train, family = poisson(link = "log"),
      control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))))

# PIT elo entering the SF = elo_post from each team's last completed match
# (2026-07-11 QF), cross-checked against data/processed/wc2026_pit_elo_panel.csv:
# England elo_post = 2172.2772, Argentina elo_post = 2253.3138.
eng_elo <- 2172.2772
arg_elo <- 2253.3138
eng_diff <- eng_elo - arg_elo   # -81.0366
arg_diff <- arg_elo - eng_elo   # +81.0366

predict_live <- function(team, elo_diff) {
  newdata <- data.frame(elo_diff_pre_100 = elo_diff / 100,
                         data_source = factor("espn_boxscore", levels = levels(live_train$data_source)),
                         team_name = team)
  as.numeric(predict(live_fit, newdata = newdata, type = "response", allow.new.levels = TRUE))
}

lam_eng <- predict_live("England", eng_diff)
lam_arg <- predict_live("Argentina", arg_diff)
p_arg_gt_eng <- skellam_p_gt(lam_arg, lam_eng)
p_eng_gt_arg <- skellam_p_gt(lam_eng, lam_arg)

cat(sprintf("England corners lambda: %.3f\nArgentina corners lambda: %.3f\n", lam_eng, lam_arg))
cat(sprintf("P(Argentina corners > England corners) [Q9 shape] = %.4f\n", p_arg_gt_eng))
cat(sprintf("P(England corners > Argentina corners)             = %.4f\n", p_eng_gt_arg))
cat(sprintf("P(tie)                                             = %.4f\n", 1 - p_arg_gt_eng - p_eng_gt_arg))

live_out <- data.frame(
  question = "Q9_argentina_more_corners_than_england",
  team_A = "Argentina", team_B = "England",
  lambda_A = lam_arg, lambda_B = lam_eng,
  p_A_gt_B = p_arg_gt_eng, p_B_gt_A = p_eng_gt_arg, p_tie = 1 - p_arg_gt_eng - p_eng_gt_arg,
  n_train_rows = nrow(live_train), fit_train_cutoff = "2026-07-15 (strictly before)"
)
live_csv <- file.path(ROOT, "matches", "England Vs Argentina (Jul.15.26)", "12_corners_comparison_live_prediction.csv")
write.csv(live_out, live_csv, row.names = FALSE)
cat(sprintf("\nWrote %s\n", live_csv))
