#!/usr/bin/env Rscript
# apply_to_fra_esp.R
# --------------------
# Application step from PREREGISTRATION_cards_corners_offsides_and_combined.md:
# fit the FDR-surviving models (SOT per-team, offsides per-team+combined,
# corners per-team) ONE more time on ALL currently-available strictly-prior
# data (everything through the QFs -- the legitimate PIT-safe training set
# for a match happening after the QFs), then predict for France and Spain in
# today's SF. Cards excluded (failed). Combined SOT/corners excluded (failed).
#
# Usage: Rscript apply_to_fra_esp.R

suppressPackageStartupMessages(library(dplyr))
ROOT <- "/Users/aki/Desktop/sportspredict_research"
source(file.path(ROOT, "ml", "backtests", "lib_hierarchical_backtest.R"))

df <- read.csv(file.path(ROOT, "data", "processed", "unified_team_match_panel_with_pit_elo.csv"), stringsAsFactors = FALSE)
df$data_source <- factor(df$data_source)
df$elo_diff_pre_100 <- df$elo_diff_pre / 100
df$cards <- df$yellow_cards + df$red_cards

# France/Spain's PIT elo_diff entering the SF, from the systematic replay
# (data/processed/wc2026_pit_elo_panel.csv, cross-checked in memory: France
# 2238.47, Spain 2261.31).
fra_elo <- 2238.47; esp_elo <- 2261.31
fra_diff <- fra_elo - esp_elo   # -22.84
esp_diff <- esp_elo - fra_elo   # +22.84

fit_and_predict <- function(response_col, team, elo_diff) {
  d <- df[!is.na(df[[response_col]]) & !is.na(df$elo_diff_pre), ]
  d$y <- d[[response_col]]
  fit <- suppressWarnings(glmer(y ~ elo_diff_pre_100 + data_source + (1 | team_name),
              data = d, family = poisson(link = "log"),
              control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))))
  newdata <- data.frame(elo_diff_pre_100 = elo_diff / 100,
                         data_source = factor("espn_boxscore", levels = levels(d$data_source)),
                         team_name = team)
  as.numeric(predict(fit, newdata = newdata, type = "response", allow.new.levels = TRUE))
}

cat("Fitting final models on all 456 rows (100 WC2026 + 356 -> wait 256 StatsBomb), predicting France vs Spain SF...\n\n")

lam_sot_fra <- fit_and_predict("shots_on_target", "France", fra_diff)
lam_sot_esp <- fit_and_predict("shots_on_target", "Spain", esp_diff)
lam_off_fra <- fit_and_predict("offsides", "France", fra_diff)
lam_off_esp <- fit_and_predict("offsides", "Spain", esp_diff)
lam_cor_fra <- fit_and_predict("corners", "France", fra_diff)
lam_cor_esp <- fit_and_predict("corners", "Spain", esp_diff)

cat(sprintf("France SOT lambda: %.3f   Spain SOT lambda: %.3f\n", lam_sot_fra, lam_sot_esp))
cat(sprintf("France offsides lambda: %.3f   Spain offsides lambda: %.3f\n", lam_off_fra, lam_off_esp))
cat(sprintf("France corners lambda: %.3f   Spain corners lambda: %.3f\n", lam_cor_fra, lam_cor_esp))

p_spain_sot5 <- 1 - ppois(4, lam_sot_esp)
p_france_sot4 <- 1 - ppois(3, lam_sot_fra)
lam_off_combined <- lam_off_fra + lam_off_esp
p_offsides4 <- 1 - ppois(3, lam_off_combined)

cat("\n=== JTC QUESTIONS: ML PREDICTION ===\n")
cat(sprintf("Q1 (4+ combined offsides): lambda_combined=%.3f -> P = %.4f\n", lam_off_combined, p_offsides4))
cat(sprintf("Q12 (Spain 5+ SOT): lambda=%.3f -> P = %.4f\n", lam_sot_esp, p_spain_sot5))
cat(sprintf("Q15 (France 4+ SOT): lambda=%.3f -> P = %.4f\n", lam_sot_fra, p_france_sot4))

out <- data.frame(
  question = c("Q1_offsides_4plus", "Q12_spain_sot_5plus", "Q15_france_sot_4plus"),
  ml_lambda = c(lam_off_combined, lam_sot_esp, lam_sot_fra),
  ml_probability = c(p_offsides4, p_spain_sot5, p_france_sot4)
)
write.csv(out, file.path(ROOT, "matches", "France Vs Spain (Jul.14.26)", "12_ml_predictions.csv"), row.names = FALSE)
cat(sprintf("\nWrote %s\n", file.path(ROOT, "matches", "France Vs Spain (Jul.14.26)", "12_ml_predictions.csv")))
