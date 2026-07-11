#!/usr/bin/env Rscript
# build_unified_team_match_panel.R
# -----------------------------------
# R port of build_unified_team_match_panel.py. Pools the WC2026 ESPN
# team-match panel with the WC2018+2022 StatsBomb team-match panel into one
# tagged table, and reports the same cross-source measurement-heterogeneity
# check (see the .py docstring / STATSBOMB_INTEGRATION_AND_STATS_TESTS doc
# for the caveat this check exists to surface).
#
# Reads (read-only): data/processed/espn_match_panel.csv,
#                     data/processed/statsbomb_team_match_panel.csv
# Writes: data/processed/unified_team_match_panel_r.csv
#
# Usage: Rscript datasets/build_unified_team_match_panel.R

suppressPackageStartupMessages(library(dplyr))

ROOT <- getwd()
ESPN_PANEL <- file.path(ROOT, "data", "processed", "espn_match_panel.csv")
SB_PANEL <- file.path(ROOT, "data", "processed", "statsbomb_team_match_panel.csv")
OUT <- file.path(ROOT, "data", "processed", "unified_team_match_panel_r.csv")

# Reuses the same canonical map as datasets/build_master_dataset.py (kept as
# a literal copy here since sourcing the Python file isn't possible from R;
# keep in sync if that file's CODE_TO_NAME ever changes).
CODE_TO_NAME <- c(
  ALG = "Algeria", ARG = "Argentina", AUS = "Australia", AUT = "Austria",
  BEL = "Belgium", BIH = "Bosnia and Herzegovina", BRA = "Brazil",
  CAN = "Canada", CDR = "DR Congo", CIV = "Ivory Coast", COL = "Colombia",
  CPV = "Cape Verde", CRO = "Croatia", CUR = "Curaçao", CZE = "Czech Republic",
  ECU = "Ecuador", EGY = "Egypt", ENG = "England", ESP = "Spain",
  FRA = "France", GER = "Germany", GHA = "Ghana", HAI = "Haiti",
  IRN = "Iran", IRQ = "Iraq", JOR = "Jordan", JPN = "Japan",
  KOR = "South Korea", KSA = "Saudi Arabia", MAR = "Morocco", MEX = "Mexico",
  NED = "Netherlands", NOR = "Norway", NZL = "New Zealand", PAN = "Panama",
  PAR = "Paraguay", POR = "Portugal", QAT = "Qatar", RSA = "South Africa",
  SAU = "Saudi Arabia", SCO = "Scotland", SEN = "Senegal", SUI = "Switzerland",
  SWE = "Sweden", TUN = "Tunisia", TUR = "Turkey", URU = "Uruguay",
  USA = "United States", UZB = "Uzbekistan"
)
NAME_TO_CODE <- setNames(names(CODE_TO_NAME), CODE_TO_NAME)

load_espn_rows <- function() {
  r <- read.csv(ESPN_PANEL, stringsAsFactors = FALSE)
  slug_a <- sapply(strsplit(r$match_slug, "-"), `[`, 1)
  slug_b <- sapply(strsplit(r$match_slug, "-"), `[`, 2)
  opp_code <- ifelse(slug_a == r$team_code, slug_b, slug_a)
  result <- ifelse(r$goals > r$opponent_goals, "W", ifelse(r$goals == r$opponent_goals, "D", "L"))

  data.frame(
    season_year = 2026, data_source = "espn_boxscore",
    match_id = r$event_id, match_date = r$date, competition_stage = NA,
    team_code = r$team_code, team_name = unname(CODE_TO_NAME[r$team_code]),
    opponent_code = opp_code, opponent_name = unname(CODE_TO_NAME[opp_code]),
    is_home = r$home_away == "home",
    goals = r$goals, opponent_goals = r$opponent_goals, result = result,
    total_shots = r$total_shots, shots_on_target = r$shots_on_target,
    blocked_shots = r$blocked_shots, xg_total = NA,
    fouls_committed = r$fouls, fouls_won = NA,
    yellow_cards = r$yellow_cards, red_cards = r$red_cards,
    corners = r$corners, offsides = r$offsides,
    passes = r$passes, passes_completed = NA, pass_pct = r$pass_pct * 100,
    clearances = r$clearances, interceptions = r$interceptions,
    possession_pct = r$possession_pct, saves = r$saves,
    effective_tackles = r$effective_tackles,
    venue = r$venue, venue_city = r$venue_city, referee_name = NA,
    stringsAsFactors = FALSE
  )
}

load_statsbomb_rows <- function() {
  r <- read.csv(SB_PANEL, stringsAsFactors = FALSE)
  data.frame(
    season_year = as.integer(r$season_name), data_source = "statsbomb_event_data",
    match_id = r$match_id, match_date = r$match_date, competition_stage = r$competition_stage,
    team_code = unname(NAME_TO_CODE[r$team_name]), team_name = r$team_name,
    opponent_code = unname(NAME_TO_CODE[r$opponent_name]), opponent_name = r$opponent_name,
    is_home = as.logical(r$is_home),
    goals = r$goals, opponent_goals = r$opponent_goals, result = r$result,
    total_shots = r$total_shots, shots_on_target = r$shots_on_target,
    blocked_shots = r$blocked_shots, xg_total = r$xg_total,
    fouls_committed = r$fouls_committed, fouls_won = r$fouls_won,
    yellow_cards = r$yellow_cards, red_cards = r$red_cards,
    corners = r$corners, offsides = r$offsides,
    passes = r$passes, passes_completed = r$passes_completed, pass_pct = r$pass_pct,
    clearances = r$clearances, interceptions = r$interceptions,
    possession_pct = NA, saves = NA, effective_tackles = NA,
    venue = r$stadium_name, venue_city = NA, referee_name = r$referee_name,
    stringsAsFactors = FALSE
  )
}

cross_source_plausibility_check <- function(df) {
  teams_espn <- unique(df$team_name[df$data_source == "espn_boxscore"])
  teams_sb <- unique(df$team_name[df$data_source == "statsbomb_event_data"])
  teams_both <- sort(intersect(teams_espn, teams_sb))

  cat("\n", length(teams_both), "teams appear under both sources (cross-tournament):\n")
  cat(sprintf("%-15s %-10s %3s %7s %6s %6s %8s\n", "Team", "src", "n", "fouls", "SOT", "cards", "corners"))
  ratios <- list(fouls = c(), sot = c(), cards = c(), corners = c())
  for (team in teams_both) {
    for (src in c("espn_boxscore", "statsbomb_event_data")) {
      tr <- df[df$team_name == team & df$data_source == src, ]
      n <- nrow(tr)
      fouls <- mean(tr$fouls_committed); sot <- mean(tr$shots_on_target)
      cards <- mean(tr$yellow_cards + tr$red_cards); corners <- mean(tr$corners)
      tag <- if (src == "espn_boxscore") "ESPN/26" else "SB/18+22"
      cat(sprintf("%-15s %-10s %3d %7.2f %6.2f %6.2f %8.2f\n", team, tag, n, fouls, sot, cards, corners))
    }
    e <- df[df$team_name == team & df$data_source == "espn_boxscore", ]
    s <- df[df$team_name == team & df$data_source == "statsbomb_event_data", ]
    ratios$fouls <- c(ratios$fouls, mean(e$fouls_committed) / mean(s$fouls_committed))
    ratios$sot <- c(ratios$sot, mean(e$shots_on_target) / mean(s$shots_on_target))
    ratios$cards <- c(ratios$cards, mean(e$yellow_cards + e$red_cards) / mean(s$yellow_cards + s$red_cards))
    ratios$corners <- c(ratios$corners, mean(e$corners) / mean(s$corners))
  }
  cat("\nMean ESPN/StatsBomb ratio across", length(teams_both), "teams:\n")
  for (stat in names(ratios)) cat(sprintf("  %-10s %.3f\n", stat, mean(ratios[[stat]])))
}

build <- function() {
  df <- bind_rows(load_espn_rows(), load_statsbomb_rows())
  dir.create(dirname(OUT), recursive = TRUE, showWarnings = FALSE)
  write.csv(df, OUT, row.names = FALSE, na = "")

  cat("Unified panel written:", OUT, "\n")
  cat("Total rows:", nrow(df), "\n")
  for (y in sort(unique(df$season_year))) {
    cat(sprintf("  %d: %d team-match rows\n", y, sum(df$season_year == y)))
  }
  cross_source_plausibility_check(df)
}

build()
