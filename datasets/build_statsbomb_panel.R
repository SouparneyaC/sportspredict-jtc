#!/usr/bin/env Rscript
# build_statsbomb_panel.R
# -------------------------
# R port of build_statsbomb_panel.py. Same methodology, same source data,
# read-only against data/external/statsbomb/open-data/. Writes to a
# distinctly-suffixed pair of files so it never clobbers the canonical
# Python-built panels:
#   data/processed/statsbomb_team_match_panel_r.csv
#   data/processed/statsbomb_player_match_panel_r.csv
#
# See build_statsbomb_panel.py's docstring for the full methodology
# rationale (SOT definition, cards-from-lineups, corners-from-pass-type,
# minutes-played interval logic, period-5 exclusion). This file mirrors that
# logic exactly so results should match row-for-row.
#
# Usage: Rscript datasets/build_statsbomb_panel.R

suppressPackageStartupMessages({
  library(jsonlite)
  library(dplyr)
})

ROOT <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(), value = TRUE))), ".."))
if (length(ROOT) == 0 || !dir.exists(file.path(ROOT, "data"))) ROOT <- getwd()

SB_DATA <- file.path(ROOT, "data", "external", "statsbomb", "open-data", "data")
OUT_TEAM <- file.path(ROOT, "data", "processed", "statsbomb_team_match_panel_r.csv")
OUT_PLAYER <- file.path(ROOT, "data", "processed", "statsbomb_player_match_panel_r.csv")

TOURNAMENTS <- list(
  list(comp_id = 43, season_id = 3, label = "FIFA World Cup 2018"),
  list(comp_id = 43, season_id = 106, label = "FIFA World Cup 2022")
)

SOT_OUTCOMES <- c("Goal", "Saved", "Saved To Post")
CARD_RED_TYPES <- c("Red Card", "Second Yellow")

parse_clock <- function(s) {
  parts <- as.numeric(strsplit(s, ":")[[1]])
  parts[1] + parts[2] / 60
}

`%||%` <- function(a, b) if (is.null(a)) b else a

load_matches <- function() {
  out <- list()
  for (t in TOURNAMENTS) {
    path <- file.path(SB_DATA, "matches", as.character(t$comp_id), paste0(t$season_id, ".json"))
    ms <- fromJSON(path, simplifyDataFrame = FALSE)
    for (m in ms) out[[as.character(m$match_id)]] <- list(m = m, label = t$label)
  }
  out
}

aggregate_match <- function(match_id) {
  events <- fromJSON(file.path(SB_DATA, "events", paste0(match_id, ".json")), simplifyDataFrame = FALSE)
  lineups <- fromJSON(file.path(SB_DATA, "lineups", paste0(match_id, ".json")), simplifyDataFrame = FALSE)

  events <- Filter(function(e) (e$period %||% 1) != 5, events)
  match_end_min <- max(sapply(events, function(e) e$minute + e$second / 60))

  team_stats <- new.env()
  player_stats <- new.env()
  get_ts <- function(tid) {
    key <- as.character(tid)
    if (is.null(team_stats[[key]])) team_stats[[key]] <- list()
    team_stats[[key]]
  }
  bump <- function(env, key, field, amount = 1) {
    cur <- env[[key]]
    if (is.null(cur)) cur <- list()
    cur[[field]] <- (cur[[field]] %||% 0) + amount
    env[[key]] <- cur
  }

  for (e in events) {
    team <- e$team
    if (is.null(team)) next
    tid <- as.character(team$id)
    etype <- e$type$name
    player <- e$player
    pid <- if (!is.null(player)) as.character(player$id) else NULL

    if (etype == "Shot") {
      shot <- e$shot
      outcome <- shot$outcome$name
      xg <- shot$statsbomb_xg %||% 0
      is_sot <- outcome %in% SOT_OUTCOMES
      bump(team_stats, tid, "total_shots")
      bump(team_stats, tid, "xg_total", xg)
      if (is_sot) bump(team_stats, tid, "shots_on_target")
      if (outcome == "Blocked") bump(team_stats, tid, "blocked_shots")
      if (!is.null(pid)) {
        bump(player_stats, pid, "shots")
        bump(player_stats, pid, "xg_total", xg)
        if (is_sot) bump(player_stats, pid, "shots_on_target")
        if (outcome == "Goal") bump(player_stats, pid, "goals")
      }
    } else if (etype == "Foul Committed") {
      bump(team_stats, tid, "fouls_committed")
      if (!is.null(pid)) bump(player_stats, pid, "fouls_committed")
    } else if (etype == "Foul Won") {
      bump(team_stats, tid, "fouls_won")
      if (!is.null(pid)) bump(player_stats, pid, "fouls_won")
    } else if (etype == "Offside") {
      bump(team_stats, tid, "offsides")
    } else if (etype == "Clearance") {
      bump(team_stats, tid, "clearances")
    } else if (etype == "Interception") {
      bump(team_stats, tid, "interceptions")
    } else if (etype == "Pass") {
      p <- e$pass
      bump(team_stats, tid, "passes")
      if (is.null(p$outcome)) bump(team_stats, tid, "passes_completed")
      if (!is.null(p$type) && identical(p$type$name, "Corner")) bump(team_stats, tid, "corners")
      if (!is.null(pid)) {
        if (isTRUE(p$goal_assist)) bump(player_stats, pid, "assists")
        if (isTRUE(p$shot_assist)) bump(player_stats, pid, "key_passes")
      }
    }
  }

  player_rows <- list()
  for (team_entry in lineups) {
    tid <- as.character(team_entry$team_id)
    tname <- team_entry$team_name
    for (p in team_entry$lineup) {
      cards <- p$cards
      yellow <- if (length(cards) > 0) sum(sapply(cards, function(c) c$card_type == "Yellow Card")) else 0
      red <- if (length(cards) > 0) sum(sapply(cards, function(c) c$card_type %in% CARD_RED_TYPES)) else 0
      bump(team_stats, tid, "yellow_cards", yellow)
      bump(team_stats, tid, "red_cards", red)

      positions <- p$positions
      minutes <- 0
      is_starter <- FALSE
      if (length(positions) > 0) {
        for (iv in positions) {
          start <- parse_clock(iv$from)
          end <- if (!is.null(iv$to)) parse_clock(iv$to) else match_end_min
          minutes <- minutes + max(0, end - start)
          if (identical(iv$start_reason, "Starting XI")) is_starter <- TRUE
        }
        primary_pos <- positions[[1]]$position
        all_pos <- paste(sort(unique(sapply(positions, function(iv) iv$position))), collapse = ";")
      } else {
        primary_pos <- NA
        all_pos <- ""
      }

      ps <- player_stats[[as.character(p$player_id)]]
      if (is.null(ps)) ps <- list()

      player_rows[[length(player_rows) + 1]] <- data.frame(
        player_id = p$player_id, player_name = p$player_name,
        team_id = as.integer(tid), team_name = tname,
        jersey_number = p$jersey_number,
        position_primary = primary_pos, positions_played = all_pos,
        is_starter = is_starter, minutes_played = round(minutes, 1),
        shots = ps$shots %||% 0, shots_on_target = ps$shots_on_target %||% 0,
        goals = ps$goals %||% 0, assists = ps$assists %||% 0,
        key_passes = ps$key_passes %||% 0,
        fouls_committed = ps$fouls_committed %||% 0, fouls_won = ps$fouls_won %||% 0,
        yellow_cards = yellow, red_cards = red,
        xg_total = round(ps$xg_total %||% 0, 4),
        stringsAsFactors = FALSE
      )
    }
  }

  list(team_stats = team_stats, player_rows = bind_rows(player_rows))
}

build <- function() {
  matches <- load_matches()
  team_rows <- list()
  all_player_rows <- list()

  for (mid in names(matches)) {
    m <- matches[[mid]]$m
    label <- matches[[mid]]$label
    home <- m$home_team; away <- m$away_team
    home_id <- home$home_team_id; away_id <- away$away_team_id
    home_name <- home$home_team_name; away_name <- away$away_team_name
    home_score <- m$home_score; away_score <- m$away_score

    agg <- aggregate_match(mid)
    ts <- agg$team_stats

    meta <- list(
      match_id = mid, competition_name = label, season_name = m$season$season_name,
      competition_stage = m$competition_stage$name, match_date = m$match_date,
      kick_off = m$kick_off,
      referee_name = if (!is.null(m$referee)) m$referee$name else NA,
      stadium_name = if (!is.null(m$stadium)) m$stadium$name else NA
    )

    sides <- list(
      list(tid = home_id, opp_id = away_id, tname = home_name, opp_name = away_name,
           is_home = TRUE, tscore = home_score, opp_score = away_score),
      list(tid = away_id, opp_id = home_id, tname = away_name, opp_name = home_name,
           is_home = FALSE, tscore = away_score, opp_score = home_score)
    )

    for (s in sides) {
      st <- ts[[as.character(s$tid)]]
      if (is.null(st)) st <- list()
      result <- if (s$tscore > s$opp_score) "W" else if (s$tscore == s$opp_score) "D" else "L"
      passes <- st$passes %||% 0
      row <- c(meta, list(
        team_id = s$tid, team_name = s$tname, opponent_id = s$opp_id, opponent_name = s$opp_name,
        is_home = s$is_home, goals = s$tscore, opponent_goals = s$opp_score, result = result,
        total_shots = st$total_shots %||% 0, shots_on_target = st$shots_on_target %||% 0,
        blocked_shots = st$blocked_shots %||% 0, xg_total = round(st$xg_total %||% 0, 4),
        fouls_committed = st$fouls_committed %||% 0, fouls_won = st$fouls_won %||% 0,
        yellow_cards = st$yellow_cards %||% 0, red_cards = st$red_cards %||% 0,
        corners = st$corners %||% 0, offsides = st$offsides %||% 0,
        passes = passes, passes_completed = st$passes_completed %||% 0,
        pass_pct = if (passes > 0) round(100 * (st$passes_completed %||% 0) / passes, 1) else NA,
        clearances = st$clearances %||% 0, interceptions = st$interceptions %||% 0
      ))
      team_rows[[length(team_rows) + 1]] <- as.data.frame(row, stringsAsFactors = FALSE)
    }

    if (nrow(agg$player_rows) > 0) {
      prow <- agg$player_rows
      prow$opponent_name <- ifelse(prow$team_id == home_id, away_name, home_name)
      for (col in names(meta)) prow[[col]] <- meta[[col]]
      all_player_rows[[length(all_player_rows) + 1]] <- prow
    }
  }

  team_df <- bind_rows(team_rows)
  player_df <- bind_rows(all_player_rows)

  dir.create(dirname(OUT_TEAM), recursive = TRUE, showWarnings = FALSE)
  write.csv(team_df, OUT_TEAM, row.names = FALSE, na = "")
  write.csv(player_df, OUT_PLAYER, row.names = FALSE, na = "")

  cat("Matches processed:", length(matches), "\n")
  cat("Team-match rows:  ", nrow(team_df), " ->", OUT_TEAM, "\n")
  cat("Player-match rows:", nrow(player_df), " ->", OUT_PLAYER, "\n\n")

  total_goals <- sum(as.numeric(team_df$goals))
  total_shots <- sum(as.numeric(team_df$total_shots))
  total_sot <- sum(as.numeric(team_df$shots_on_target))
  n_matches <- length(matches)
  cat("Sanity check (per match, both teams combined):\n")
  cat(sprintf("  goals/match:  %.3f\n", total_goals / n_matches))
  cat(sprintf("  shots/match:  %.3f\n", total_shots / n_matches))
  cat(sprintf("  SOT/match:    %.3f\n", total_sot / n_matches))
  for (label in c("FIFA World Cup 2018", "FIFA World Cup 2022")) {
    rows <- team_df[team_df$competition_name == label, ]
    nm <- nrow(rows) / 2
    g <- sum(as.numeric(rows$goals))
    cat(sprintf("  %s: %d matches, %d total goals (%.3f/match)\n", label, nm, g, g / nm))
  }
}

build()
