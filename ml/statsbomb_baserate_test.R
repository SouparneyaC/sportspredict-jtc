#!/usr/bin/env Rscript
# statsbomb_baserate_test.R
# ---------------------------
# R port of ml/statsbomb_baserate_test.py. Same methodology: shrink Portugal's
# and Croatia's historical StatsBomb rates toward the tournament-wide mean
# (empirical Bayes pooling), price the real Portugal vs Croatia WC2026 match
# with Poisson thresholds, and compare against what we actually submitted.
#
# Usage: Rscript ml/statsbomb_baserate_test.R

suppressPackageStartupMessages({
  library(jsonlite)
})

ROOT <- getwd()
TEAM_PANEL <- file.path(ROOT, "data", "processed", "statsbomb_team_match_panel.csv")
PLAYER_PANEL <- file.path(ROOT, "data", "processed", "statsbomb_player_match_panel.csv")
SB_EVENTS <- file.path(ROOT, "data", "external", "statsbomb", "open-data", "data", "events")
SB_MATCHES <- file.path(ROOT, "data", "external", "statsbomb", "open-data", "data", "matches")
MATCH_DIR <- file.path(ROOT, "matches", "Portugal_vs_Croatia")
OUT <- file.path(ROOT, "ml", "statsbomb_baserate_results_r.json")

poisson_ge <- function(threshold, lam) 1 - ppois(threshold - 1, lam)

shrink <- function(team_mean, n, global_mean, k = 5) (n * team_mean + k * global_mean) / (n + k)

`%||%` <- function(a, b) if (is.null(a) || length(a) == 0) b else a

load_team_rates <- function() {
  rows <- read.csv(TEAM_PANEL, stringsAsFactors = FALSE)
  stats <- c("shots_on_target", "total_shots", "corners", "fouls_committed", "goals")
  global_mean <- sapply(stats, function(s) mean(rows[[s]]))
  global_mean["cards"] <- mean(rows$yellow_cards + rows$red_cards)

  team_rates <- function(team_name) {
    tr <- rows[rows$team_name == team_name, ]
    n <- nrow(tr)
    out <- list(n_matches = n)
    for (s in stats) out[[s]] <- shrink(mean(tr[[s]]), n, global_mean[[s]])
    out$cards <- shrink(mean(tr$yellow_cards + tr$red_cards), n, global_mean[["cards"]])
    out
  }

  list(por = team_rates("Portugal"), cro = team_rates("Croatia"), global_mean = global_mean)
}

load_player_rate <- function(full_name, mode = "goals", n_pseudo = 3, weak_prior = 0.15) {
  rows <- read.csv(PLAYER_PANEL, stringsAsFactors = FALSE)
  rows <- rows[rows$player_name == full_name, ]
  n <- nrow(rows)
  if (n == 0) return(list(rate = NA, n = 0))
  per_match <- switch(mode,
    "goals" = rows$goals,
    "score_or_assist" = as.numeric(rows$goals > 0 | rows$assists > 0),
    "sot_2plus" = as.numeric(rows$shots_on_target >= 2),
    "sot_1plus" = as.numeric(rows$shots_on_target >= 1)
  )
  m <- mean(per_match)
  list(rate = (n * m + n_pseudo * weak_prior) / (n + n_pseudo), n = n)
}

scan_raw_events_for_derived_stats <- function() {
  match_ids <- c(
    sapply(fromJSON(file.path(SB_MATCHES, "43", "3.json"), simplifyDataFrame = FALSE), function(m) m$match_id),
    sapply(fromJSON(file.path(SB_MATCHES, "43", "106.json"), simplifyDataFrame = FALSE), function(m) m$match_id)
  )
  n <- length(match_ids)
  header_goal_matches <- 0; ht_tied_matches <- 0; pen_or_red_matches <- 0

  for (mid in match_ids) {
    events <- fromJSON(file.path(SB_EVENTS, paste0(mid, ".json")), simplifyDataFrame = FALSE)
    events <- Filter(function(e) (e$period %||% 1) != 5, events)

    has_header_goal <- FALSE; pen_awarded <- FALSE; red_shown <- FALSE
    ht_goals <- list()
    teams_seen <- character(0)

    for (e in events) {
      etype <- e$type$name
      team_id <- if (!is.null(e$team)) as.character(e$team$id) else NA
      if (!is.na(team_id)) teams_seen <- union(teams_seen, team_id)

      if (etype == "Shot") {
        shot <- e$shot
        outcome <- shot$outcome$name
        if (identical(shot$type$name, "Penalty")) pen_awarded <- TRUE
        if (outcome == "Goal") {
          if (e$period == 1) ht_goals[[team_id]] <- (ht_goals[[team_id]] %||% 0) + 1
          if (identical(shot$body_part$name, "Head")) has_header_goal <- TRUE
        }
      } else if (etype == "Own Goal For" && e$period == 1) {
        ht_goals[[team_id]] <- (ht_goals[[team_id]] %||% 0) + 1
      } else if (etype == "Foul Committed") {
        fc <- e$foul_committed
        if (isTRUE(fc$penalty)) pen_awarded <- TRUE
        card <- fc$card$name
        if (!is.null(card) && card %in% c("Red Card", "Second Yellow")) red_shown <- TRUE
      } else if (etype == "Bad Behaviour") {
        card <- e$bad_behaviour$card$name
        if (!is.null(card) && card %in% c("Red Card", "Second Yellow")) red_shown <- TRUE
      }
    }

    if (has_header_goal) header_goal_matches <- header_goal_matches + 1
    if (pen_awarded || red_shown) pen_or_red_matches <- pen_or_red_matches + 1
    for (t in teams_seen) if (is.null(ht_goals[[t]])) ht_goals[[t]] <- 0
    if (length(unique(unlist(ht_goals))) == 1) ht_tied_matches <- ht_tied_matches + 1
  }

  list(n_matches = n, p_header_goal = header_goal_matches / n,
       p_ht_tied = ht_tied_matches / n, p_pen_or_red = pen_or_red_matches / n)
}

main <- function() {
  rates <- load_team_rates()
  por <- rates$por; cro <- rates$cro
  cat("Portugal (n=", por$n_matches, "):\n"); str(por)
  cat("Croatia  (n=", cro$n_matches, "):\n"); str(cro)

  cat("\nScanning raw events for header goals / HT-tied / penalty-or-red...\n")
  derived <- scan_raw_events_for_derived_stats()
  str(derived)

  ronaldo <- load_player_rate("Cristiano Ronaldo dos Santos Aveiro", "goals", 3, 0.35)
  bruno <- load_player_rate("Bruno Miguel Borges Fernandes", "sot_2plus", 3, 0.25)
  modric <- load_player_rate("Luka Modrić", "score_or_assist", 3, 0.30)
  bsilva <- load_player_rate("Bernardo Mota Veiga de Carvalho e Silva", "sot_1plus", 3, 0.40)

  cat(sprintf("\nRonaldo goal rate (n=%d): %.3f\n", ronaldo$n, ronaldo$rate))
  cat(sprintf("Bruno 2+ SOT rate (n=%d): %.3f\n", bruno$n, bruno$rate))
  cat(sprintf("Modric score-or-assist rate (n=%d): %.3f\n", modric$n, modric$rate))
  cat(sprintf("Bernardo Silva 1+ SOT rate (n=%d): %.3f\n", bsilva$n, bsilva$rate))

  lam_total_goals <- por$goals + cro$goals
  p_le_2_goals <- ppois(2, lam_total_goals)
  p_both_card <- (1 - exp(-por$cards)) * (1 - exp(-cro$cards))

  model_estimates <- c(
    "Will Cristiano Ronaldo (Portugal) score a goal?" = ronaldo$rate,
    "Will the match have 2 or fewer total goals?" = p_le_2_goals,
    "Will Bruno Fernandes (Portugal) have 2 or more shots on target?" = bruno$rate,
    "Will Luka Modrić (Croatia) score or assist a goal?" = modric$rate,
    "Will Croatia have 4 or more shots on target?" = poisson_ge(4, cro$shots_on_target),
    "Will there be 4 or more total cards shown?" = poisson_ge(4, por$cards + cro$cards),
    "Will both teams receive at least one card?" = p_both_card,
    "Will Portugal have 6 or more corner kicks?" = poisson_ge(6, por$corners),
    "Will the match be tied at halftime?" = derived$p_ht_tied,
    "Will Portugal have 6 or more shots on target?" = poisson_ge(6, por$shots_on_target),
    "Will Bernardo Silva (Portugal) have 1 or more shots on target?" = bsilva$rate,
    "Will a header goal be scored?" = derived$p_header_goal,
    "Will there be 20 or more total shots?" = poisson_ge(20, por$total_shots + cro$total_shots),
    "Will a penalty kick be awarded OR a red card be shown?" = derived$p_pen_or_red
  )

  actual <- fromJSON(file.path(MATCH_DIR, "06_post_match_results.json"), simplifyDataFrame = FALSE)
  qres <- actual$question_results
  outcome_map <- setNames(qres, sapply(qres, function(q) q$text))

  S <- 101.3
  cat(sprintf("\n%-62s %6s %6s %6s %8s %8s %10s\n", "Question", "Model", "Ours", "Crowd", "Outcome", "OurRBP", "ModelRBP*"))
  total_our <- 0; total_model <- 0; n_better <- 0; n_rows <- 0
  for (qtext in names(model_estimates)) {
    if (is.null(outcome_map[[qtext]])) next
    a <- outcome_map[[qtext]]
    outcome <- ifelse(a$outcome == "YES", 1, 0)
    model_p <- model_estimates[[qtext]]
    our_brier <- (a$our_estimate - outcome)^2
    crowd_brier <- (a$crowd_estimate - outcome)^2
    model_brier <- (model_p - outcome)^2
    model_rbp <- (crowd_brier - model_brier) * S
    total_our <- total_our + a$rbp
    total_model <- total_model + model_rbp
    n_rows <- n_rows + 1
    if (model_rbp > a$rbp) n_better <- n_better + 1
    cat(sprintf("%-62s %6.2f %6.2f %6.2f %8s %8.2f %10.2f\n",
                substr(qtext, 1, 60), model_p, a$our_estimate, a$crowd_estimate, a$outcome, a$rbp, model_rbp))
  }
  cat(sprintf("\nOn these %d questions: our RBP=%.2f, model-implied RBP=%.2f, model beats us on %d/%d\n",
              n_rows, total_our, total_model, n_better, n_rows))

  write(toJSON(list(portugal_rates = por, croatia_rates = cro, derived = derived,
                     total_our_rbp = total_our, total_model_rbp = total_model),
               auto_unbox = TRUE, pretty = TRUE), OUT)
  cat("\nWritten:", OUT, "\n")
}

main()
