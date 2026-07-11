#!/usr/bin/env Rscript
# explore_statsbomb_data.R
# ---------------------------
# Interactive exploration of the StatsBomb WC2018+2022 data in R, at three
# levels: the flattened team-match panel, the flattened player-match panel,
# and a peek at the raw event-level JSON underneath both of them.
#
# Run interactively (source line-by-line in RStudio/console) or all at once:
#   Rscript datasets/explore_statsbomb_data.R

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(jsonlite)
})

ROOT <- getwd()  # run from the project root

# ── 1. Team-match panel ─────────────────────────────────────────────────────
# One row per team per match: 256 rows (128 matches x 2 teams), WC2018+2022.
team_panel <- read.csv(file.path(ROOT, "data", "processed", "statsbomb_team_match_panel.csv"))

str(team_panel)
summary(team_panel[, c("goals", "total_shots", "shots_on_target", "fouls_committed", "yellow_cards", "corners")])

# Portugal's 9 historical WC appearances
team_panel %>%
  filter(team_name == "Portugal") %>%
  select(season_name, competition_stage, opponent_name, result, goals, opponent_goals,
         shots_on_target, fouls_committed, yellow_cards, corners) %>%
  print()

# Average stats per team, sorted by goals/match -- a quick league-table-style view
team_averages <- team_panel %>%
  group_by(team_name) %>%
  summarise(matches = n(), goals_per_match = mean(goals), sot_per_match = mean(shots_on_target),
            cards_per_match = mean(yellow_cards + red_cards), .groups = "drop") %>%
  arrange(desc(goals_per_match))

print(head(team_averages, 15))

# ── 2. Player-match panel ───────────────────────────────────────────────────
# One row per player per match: 6,130 rows.
player_panel <- read.csv(file.path(ROOT, "data", "processed", "statsbomb_player_match_panel.csv"))

str(player_panel)

# Ronaldo's match log
player_panel %>%
  filter(player_name == "Cristiano Ronaldo dos Santos Aveiro") %>%
  select(match_date, opponent_name, minutes_played, shots, shots_on_target, goals, xg_total) %>%
  arrange(match_date) %>%
  print()

# Top goal scorers across both tournaments
top_scorers <- player_panel %>%
  group_by(player_name) %>%
  summarise(matches = n(), goals = sum(goals), xg_total = sum(xg_total), .groups = "drop") %>%
  arrange(desc(goals)) %>%
  head(10)

print(top_scorers)

# ── 3. Visualize ─────────────────────────────────────────────────────────────
# Goals-per-match distribution across all 256 team-match rows
p1 <- ggplot(team_panel, aes(x = goals)) +
  geom_bar(fill = "#2c7fb8") +
  labs(title = "Goals scored per team per match (WC2018+2022)", x = "Goals", y = "Count") +
  theme_minimal()
ggsave(file.path(ROOT, "data", "processed", "statsbomb_goals_distribution.png"), p1, width = 6, height = 4)

# Shots vs. shots-on-target, colored by xG -- do more shots reliably mean more SOT?
p2 <- ggplot(team_panel, aes(x = total_shots, y = shots_on_target, color = xg_total)) +
  geom_point(size = 2, alpha = 0.7) +
  scale_color_viridis_c() +
  labs(title = "Shots vs. Shots on Target (colored by team xG)", x = "Total shots", y = "Shots on target", color = "xG") +
  theme_minimal()
ggsave(file.path(ROOT, "data", "processed", "statsbomb_shots_vs_sot.png"), p2, width = 6, height = 4)

cat("\nSaved plots:\n")
cat(" -", file.path(ROOT, "data", "processed", "statsbomb_goals_distribution.png"), "\n")
cat(" -", file.path(ROOT, "data", "processed", "statsbomb_shots_vs_sot.png"), "\n")

# ── 4. What the raw data looks like before flattening ───────────────────────
# jsonlite::fromJSON with simplifyDataFrame=FALSE preserves the nested
# dict-per-event structure exactly (each event is a named list, same shape
# as the original JSON) -- this is what build_statsbomb_panel.R parses.
sample_events <- fromJSON(
  file.path(ROOT, "data", "external", "statsbomb", "open-data", "data", "events", "3857276.json"),
  simplifyDataFrame = FALSE
)
cat("\nSample match has", length(sample_events), "raw events. Event #100 (a shot):\n")
str(sample_events[[100]], max.level = 2)
