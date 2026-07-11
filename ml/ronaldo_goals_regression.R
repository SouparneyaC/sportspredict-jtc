#!/usr/bin/env Rscript
# ronaldo_goals_regression.R
# -----------------------------
# R port of ml/ronaldo_goals_regression.py. Small-sample (n=9) linear
# regression demo: Ronaldo's per-match goals on shots_on_target, xg_total,
# minutes_played, using his 9 WC2018+2022 appearances in
# statsbomb_player_match_panel.csv. See the .py docstring for why n=9 is
# deliberately below the project's usual trust threshold (RULE5: n>=10) --
# this is a methodology demonstration of small-sample overfitting, not a
# usable model. Out-of-sample check is leave-one-out cross-validation (the
# correct analogue of walk-forward/GroupKFold at this sample size).
#
# Usage: Rscript ml/ronaldo_goals_regression.R

suppressPackageStartupMessages({
  library(jsonlite)
  library(sandwich)
  library(lmtest)
})

ROOT <- getwd()
PLAYER_PANEL <- file.path(ROOT, "data", "processed", "statsbomb_player_match_panel.csv")
OUT <- file.path(ROOT, "ml", "ronaldo_goals_regression_results_r.json")

PLAYER_NAME <- "Cristiano Ronaldo dos Santos Aveiro"
FEATURES <- c("shots_on_target", "xg_total", "minutes_played")

df <- read.csv(PLAYER_PANEL, stringsAsFactors = FALSE)
df <- df[df$player_name == PLAYER_NAME, ]
df <- df[order(df$match_date), ]

cat("Rows (matches):", nrow(df), "\n")
print(df[, c("match_date", "opponent_name", "minutes_played", "shots", "shots_on_target", "xg_total", "goals")],
      row.names = FALSE)

X <- df[, FEATURES]
y <- df$goals
cat(sprintf("\nGoals: mean=%.3f, total=%.0f across %d matches\n", mean(y), sum(y), length(y)))

cat("\n", strrep("=", 70), "\n")
cat("IN-SAMPLE OLS (n=", nrow(df), ", HC3 robust SEs) -- ILLUSTRATIVE ONLY, n<<10\n")
cat(strrep("=", 70), "\n")
fit <- lm(goals ~ shots_on_target + xg_total + minutes_played, data = df)
ct <- coeftest(fit, vcov = vcovHC(fit, type = "HC3"))
print(ct)
cat(sprintf("\nR-squared: %.4f   Adj. R-squared: %.4f\n", summary(fit)$r.squared, summary(fit)$adj.r.squared))
# NOTE: statsmodels' cov_type="HC3" also recomputes the overall F-test as a
# robust Wald test, which differs from R's classical (homoskedastic) F-test
# reported by summary(fit) -- that's why the Python run's F p-value (0.677)
# and a plain R F-test p-value (0.381) won't match; both are "correct" for
# what they are, they're just different test statistics. Individual
# coefficient p-values above (HC3) are the ones that should agree.

cat("\n", strrep("=", 70), "\n")
cat("OUT-OF-SAMPLE: LEAVE-ONE-OUT CROSS-VALIDATION\n")
cat(strrep("=", 70), "\n")

n <- nrow(df)
preds <- numeric(n); baseline <- numeric(n)
for (i in 1:n) {
  train <- df[-i, ]
  m <- lm(goals ~ shots_on_target + xg_total + minutes_played, data = train)
  preds[i] <- predict(m, newdata = df[i, ])
  baseline[i] <- mean(train$goals)
}

cat(sprintf("\n%-28s %7s %11s %14s\n", "Match", "Actual", "Model pred", "Baseline pred"))
for (i in 1:n) {
  cat(sprintf("%s vs %-15s %7.0f %11.2f %14.2f\n", df$match_date[i], df$opponent_name[i], y[i], preds[i], baseline[i]))
}

mse_model <- mean((preds - y)^2)
mse_base <- mean((baseline - y)^2)
mae_model <- mean(abs(preds - y))
mae_base <- mean(abs(baseline - y))

cat(sprintf("\nLOOCV MSE  -- model: %.3f  baseline (predict train-mean): %.3f\n", mse_model, mse_base))
cat(sprintf("LOOCV MAE  -- model: %.3f  baseline: %.3f\n", mae_model, mae_base))
cat("Model beats baseline (MSE):", mse_model < mse_base, "\n")

out <- list(
  n_matches = n, features = FEATURES,
  in_sample_r2 = summary(fit)$r.squared, in_sample_adj_r2 = summary(fit)$adj.r.squared,
  loocv = list(mse_model = mse_model, mse_baseline = mse_base, mae_model = mae_model, mae_baseline = mae_base),
  caveat = "n=9 is far below any sample size this project trusts (RULE5 bar is n>=10). Treat as methodology demonstration, not a usable model."
)
writeLines(toJSON(out, auto_unbox = TRUE, pretty = TRUE), OUT)
cat("\nWritten:", OUT, "\n")
