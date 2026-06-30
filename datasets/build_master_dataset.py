"""
build_master_dataset.py
========================
Builds ONE comprehensive per-question flat (row/column) dataset from every
raw match JSON in data/external_markets/, plus joined pre-match features
from the project's own historical/external data sources.

This script only READS raw data. It never modifies any file under
data/external_markets/, data/processed/, data/external/, data/international_results/,
data/soccer-elo/, or bot/. Output is written to a NEW file:
    datasets/master_question_dataset.csv

Run from anywhere:  python3 datasets/build_master_dataset.py
(paths below are resolved relative to this file, not the cwd)

See datasets/MASTER_DATASET_DICTIONARY.md for the full column-by-column
explanation, and DATASET_AUDIT_2026-06-26.md for the research trail that
produced this design.
"""

import json
import csv
import re
import math
import glob
from pathlib import Path
from bisect import bisect_left
from datetime import date as date_cls

ROOT = Path(__file__).parent.parent
EXT_MARKETS = ROOT / "data" / "external_markets"
OUT_CSV = Path(__file__).parent / "master_question_dataset.csv"

SKIP_PATTERNS = ["smarkets_quotes", "smarkets_raw", "smarkets_parsed",
                  "wc2026_raw", "wc2022_raw", "ledger", "smarkets_markets"]

# ──────────────────────────────────────────────────────────────────────────
# 1. Team code -> canonical full name (matches spelling used in
#    data/international_results/results.csv and data/processed/elo_match_panel.csv)
# ──────────────────────────────────────────────────────────────────────────
CODE_TO_NAME = {
    "ALG": "Algeria", "ARG": "Argentina", "AUS": "Australia", "AUT": "Austria",
    "BEL": "Belgium", "BIH": "Bosnia and Herzegovina", "BRA": "Brazil",
    "CAN": "Canada", "CDR": "DR Congo", "CIV": "Ivory Coast", "COL": "Colombia",
    "CPV": "Cape Verde", "CRO": "Croatia", "CUR": "Curaçao", "CZE": "Czech Republic",
    "ECU": "Ecuador", "EGY": "Egypt", "ENG": "England", "ESP": "Spain",
    "FRA": "France", "GER": "Germany", "GHA": "Ghana", "HAI": "Haiti",
    "IRN": "Iran", "IRQ": "Iraq", "JOR": "Jordan", "JPN": "Japan",
    "KOR": "South Korea", "KSA": "Saudi Arabia", "MAR": "Morocco", "MEX": "Mexico",
    "NED": "Netherlands", "NOR": "Norway", "NZL": "New Zealand", "PAN": "Panama",
    "PAR": "Paraguay", "POR": "Portugal", "QAT": "Qatar", "RSA": "South Africa",
    "SAU": "Saudi Arabia", "SCO": "Scotland", "SEN": "Senegal", "SUI": "Switzerland",
    "SWE": "Sweden", "TUN": "Tunisia", "TUR": "Turkey", "URU": "Uruguay",
    "USA": "United States", "UZB": "Uzbekistan",
}

VENUE_CITY_ALIASES = {
    "Zapopan": "Guadalajara", "Arlington": "Dallas", "Inglewood": "Los Angeles",
    "Santa Clara": "San Francisco Bay Area", "Foxborough": "Boston",
    "East Rutherford": "New York/New Jersey", "New York": "New York/New Jersey",
    "Miami Gardens": "Miami", "Guadalupe": "Monterrey",
}

TRANSFERMARKT_NAME_ALIASES = {
    # left = our canonical name, right = name as it appears in
    # data/external/transfermarkt/extracted/national_teams.csv
    "Turkey": "Turkiye",
    "Bosnia and Herzegovina": "Bosnia-Herzegovina",
    # (Ivory Coast, DR Congo, Curaçao, Haiti, Cape Verde are simply ABSENT
    #  from that 119-row extract -- left unmapped on purpose, see audit doc)
}

# ──────────────────────────────────────────────────────────────────────────
# 2. Load supplementary data sources once
# ──────────────────────────────────────────────────────────────────────────

def load_elo_lookup():
    """frozenset({team_a,team_b}) -> {date_str: {team_name: elo_pre}}."""
    path = ROOT / "data" / "processed" / "elo_match_panel.csv"
    lookup = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row["date"].startswith("2026"):
                continue
            teams = frozenset({row["home_team"], row["away_team"]})
            lookup.setdefault(teams, {})[row["date"]] = {
                row["home_team"]: float(row["elo_home_pre"]),
                row["away_team"]: float(row["elo_away_pre"]),
            }
    return lookup


def lookup_with_date_tolerance(by_teams, team_a, team_b, date_str, tolerance_days=1):
    """The raw match-file date (from filename) is occasionally 1 day off from
    results.csv's date for the same fixture (timezone artifact on several
    US/Canada-hosted matches, e.g. usa_par_2026-06-13.json vs results.csv's
    2026-06-12 row for the same United States-Paraguay game). Try the exact
    date first, then +/- N days, before giving up."""
    by_date = by_teams.get(frozenset({team_a, team_b}))
    if not by_date:
        return None
    if date_str in by_date:
        return by_date[date_str]
    try:
        d0 = date_cls.fromisoformat(date_str)
    except ValueError:
        return None
    for delta in range(1, tolerance_days + 1):
        for cand in (d0.fromordinal(d0.toordinal() + delta), d0.fromordinal(d0.toordinal() - delta)):
            cand_str = cand.isoformat()
            if cand_str in by_date:
                return by_date[cand_str]
    return None


def load_team_match_dates():
    """team_name -> sorted list of date strings (date.fromisoformat-able) the team played, from results.csv."""
    path = ROOT / "data" / "international_results" / "results.csv"
    team_dates = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            d = row["date"]
            for t in (row["home_team"], row["away_team"]):
                team_dates.setdefault(t, []).append(d)
    for t in team_dates:
        team_dates[t].sort()
    return team_dates


def load_venue_lookup():
    """frozenset({team_a,team_b}) -> {date_str: (city, country)} from results.csv
    (covers the full WC2026 schedule, including future-dated fixtures)."""
    path = ROOT / "data" / "international_results" / "results.csv"
    lookup = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row["date"].startswith("2026"):
                continue
            teams = frozenset({row["home_team"], row["away_team"]})
            lookup.setdefault(teams, {})[row["date"]] = (row["city"], row["country"])
    return lookup


def load_altitude_lookup():
    path = ROOT / "data" / "external" / "altitude" / "wc2026_venue_altitude.csv"
    lookup = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            lookup[row["city"]] = float(row["altitude_m"])
    return lookup


def load_squad_lookup():
    """team full name -> dict(squad_size, average_age, total_market_value, fifa_ranking)."""
    path = ROOT / "data" / "external" / "transfermarkt" / "extracted" / "national_teams.csv"
    lookup = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row["name"]
            lookup[name] = {
                "squad_size": row["squad_size"] or None,
                "average_age": row["average_age"] or None,
                "total_market_value_eur": row["total_market_value"] or None,
                "fifa_ranking_2025": row["fifa_ranking"] or None,
            }
    return lookup


def load_ordered_logit_coefs():
    path = ROOT / "data" / "processed" / "ordered_logit_coefs.json"
    return json.loads(path.read_text())


def load_poisson_coefs():
    path = ROOT / "data" / "processed" / "poisson_goals_coefs.json"
    return json.loads(path.read_text())


def rest_days_for(team_dates_index, team, match_date):
    dates = team_dates_index.get(team)
    if not dates:
        return None
    i = bisect_left(dates, match_date)
    if i == 0:
        return None  # first known match for this team, no prior date
    prev = dates[i - 1]
    if prev == match_date:
        if i - 1 == 0:
            return None
        prev = dates[i - 2]
    try:
        d1 = date_cls.fromisoformat(match_date)
        d2 = date_cls.fromisoformat(prev)
        return (d1 - d2).days
    except ValueError:
        return None


# ──────────────────────────────────────────────────────────────────────────
# 3. Raw JSON parsing helpers
# ──────────────────────────────────────────────────────────────────────────

def is_match_file(fname):
    if not fname.endswith(".json"):
        return False
    if any(p in fname for p in SKIP_PATTERNS):
        return False
    return bool(re.search(r"\d{4}-\d{2}-\d{2}", fname))


def extract_date(fname):
    m = re.search(r"(\d{4}-\d{2}-\d{2})", fname)
    return m.group(1) if m else ""


def extract_slug_codes(fname):
    """ger_cur_2026-06-14.json -> ['GER', 'CUR']"""
    parts = fname.replace(".json", "").split("_")
    non_date = [p for p in parts if not re.match(r"\d{4}", p)]
    return [p.upper() for p in non_date[:2]]


def q_num(key):
    m = re.match(r"(Q\d+)", str(key), re.IGNORECASE)
    return m.group(1).upper() if m else str(key)


def to_int_outcome(val):
    if val is None:
        return None
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        v = val.strip().upper()
        if v == "YES":
            return 1
        if v == "NO":
            return 0
    return None


def safe_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


RULE_NAMES = [f"RULE{i}" for i in range(1, 16)]


def extract_rules(d):
    """Look across every key name this project has used for rule-tracking and
    return (rules_fired_list, rule_bool_dict) where rule_bool_dict maps
    'RULE1'..'RULE15' -> True/False/None (None = not mentioned in this file)."""
    rule_bool = {r: None for r in RULE_NAMES}
    fired = []

    for container_key in ("rules_fired", "rules_in_effect", "rules_applied"):
        container = d.get(container_key)
        if isinstance(container, dict):
            for k, v in container.items():
                base = re.match(r"(RULE\d+)", k.upper())
                if not base:
                    continue
                rname = base.group(1)
                if k.upper().endswith("_NOTE"):
                    continue
                if rname in rule_bool:
                    val = bool(v) if isinstance(v, bool) else True
                    rule_bool[rname] = val
                    if val:
                        fired.append(rname)
        elif isinstance(container, list):
            for item in container:
                s = str(item).upper()
                base = re.match(r"(RULE\d+)", s)
                if base and base.group(1) in rule_bool:
                    rule_bool[base.group(1)] = True
                    fired.append(base.group(1))

    # also scan context_note / free text for explicit "RULE7 fires" style mentions
    note = d.get("context_note") or ""
    if isinstance(note, str):
        for m in re.finditer(r"RULE(\d{1,2})", note.upper()):
            rname = f"RULE{m.group(1)}"
            if rname in rule_bool and rule_bool[rname] is None:
                rule_bool[rname] = True
                fired.append(rname)

    return sorted(set(fired)), rule_bool


STOPWORDS = {"will", "be", "a", "an", "the", "or", "to", "in", "of", "at", "have",
             "is", "than", "this", "that", "it", "its", "for", "on", "as", "by",
             "and", "be", "least", "1"}


def text_tokens(*parts):
    """Combine a container key (e.g. 'q5_kane_1plus_sot_2h') and/or a free-text
    question string into one normalized token set: lowercase, split on
    non-alphanumerics, drop stopwords, crude pluralization-strip.

    Needed because question numbering DRIFTS between containers in this project:
    pre-match draft files and the final post-match record do not reliably use the
    same Qn for the same question (verified directly: eng_cro draft
    'q5_kane_1plus_sot_2h' is actually final 'Q7'; cro_pan final_estimates.Q1
    ['fouls'] is actually post_match.outcomes.Q4 ['fouls'], a 4-question rotation).
    Matching on topic words instead of position is the only safe join here."""
    tokens = set()
    for part in parts:
        if not part:
            continue
        part = re.sub(r"^q\d+_?", "", str(part).lower())
        for t in re.split(r"[^a-z0-9]+", part):
            if t and t not in STOPWORDS:
                tokens.add(t.rstrip("s"))
    return tokens


def extract_pre_match_estimates(d, post_match_qs):
    """Per-question recommended/pre-match estimate, keyed to match post_match_qs's
    keys via topic-word matching (see text_tokens), not raw Q-number position,
    because that numbering is not reliably consistent across containers in this
    project (confirmed on multiple files, both era1 and era3 -- see docstring above
    and DATASET_AUDIT_2026-06-26.md)."""
    candidates = []  # (container_key, tokens, value_dict)
    for container_key in ("derived_estimates_for_sportspredict_markets",
                          "final_estimates", "question_analysis"):
        container = d.get(container_key)
        if not isinstance(container, dict):
            continue
        for k, v in container.items():
            if isinstance(v, dict):
                candidates.append((k, text_tokens(k, v.get("question")), v))

    targets = []  # (qn, tokens)
    for qn, pm_data in post_match_qs.items():
        targets.append((qn, text_tokens(pm_data.get("raw_key"), pm_data.get("question_text"))))

    # global greedy matching: highest-scoring (target, candidate) pairs first
    scored = []
    for qn, ttoks in targets:
        if not ttoks:
            continue
        for idx, (ckey, ctoks, v) in enumerate(candidates):
            if not ctoks:
                continue
            overlap = len(ttoks & ctoks)
            union = len(ttoks | ctoks)
            jaccard = overlap / union if union else 0
            if overlap >= 2 and jaccard >= 0.35:
                scored.append((jaccard, qn, idx))
    scored.sort(reverse=True)

    out = {}
    draft_key_to_qn = {}
    used_qn, used_idx = set(), set()
    for jaccard, qn, idx in scored:
        if qn in used_qn or idx in used_idx:
            continue
        used_qn.add(qn)
        used_idx.add(idx)
        ckey, _, v = candidates[idx]
        draft_key_to_qn[q_num(ckey)] = qn
        est = v.get("recommended_estimate")
        if est is None:
            est = v.get("estimate")
        out[qn] = {
            "recommended_estimate": safe_float(est),
            "question_text": v.get("question"),
            "category": v.get("category"),
            "confidence": v.get("confidence"),
            "direction": v.get("direction"),
            "key_drivers": "; ".join(v.get("key_drivers", [])) if isinstance(v.get("key_drivers"), list) else None,
        }
    return out, draft_key_to_qn


def extract_edge_ranks(d, draft_key_to_qn):
    """edge_ranking is written pre-match using the SAME draft numbering as
    final_estimates/question_analysis, which may not equal the post-match Qn
    (see text_tokens docstring) -- translate through draft_key_to_qn rather than
    trusting item['q'] directly."""
    out = {}
    er = d.get("edge_ranking")
    if isinstance(er, list):
        for item in er:
            if isinstance(item, dict) and item.get("q"):
                draft_qn = q_num(item["q"])
                qn = draft_key_to_qn.get(draft_qn, draft_qn)
                out[qn] = item.get("rank")
    return out


def extract_player_profiles(d):
    pp = d.get("player_profiles")
    if isinstance(pp, dict):
        return pp
    return {}


def detect_is_player_prop(question_text, player_profiles):
    if not question_text:
        return False, None
    qtext_lower = question_text.lower()
    for pkey in player_profiles:
        pname = pkey.replace("_", " ").lower()
        if pname and pname in qtext_lower:
            return True, pkey
    return False, None


def extract_post_match(d):
    """Returns (container_key_used, dict of qn -> {our_estimate, crowd_estimate,
    outcome, rbp, note, question_text, actually_submitted}, final_score,
    match_total_rbp, settled_date, beat_crowd_count, match_no_submission_flag)."""
    pm = d.get("post_match_results")
    key_used = "post_match_results"
    if not pm:
        pm = d.get("post_match")
        key_used = "post_match" if pm else None
    if not pm:
        return None, {}, None, None, None, None, False

    final_score = pm.get("final_score")
    match_total_rbp = pm.get("total_rbp") if pm.get("total_rbp") is not None else pm.get("match_rbp_total")
    settled_date = pm.get("settled_date")
    match_no_submission_flag = bool(pm.get("NO_SUBMISSION_FLAG")) or "NO SUBMISSION" in str(
        pm.get("submission_status", "")).upper()

    out = {}
    sub_ests = d.get("final_submission_estimates") or {}

    def add(qn, question_text, our_est, crowd_est, outcome_raw, rbp, note, actually_submitted=True, raw_key=None):
        out[qn] = {
            "question_text": question_text,
            "our_estimate": safe_float(our_est),
            "crowd_estimate": safe_float(crowd_est),
            "outcome": to_int_outcome(outcome_raw),
            "rbp": safe_float(rbp),
            "note": note,
            "actually_submitted": actually_submitted,
            "raw_key": raw_key or qn,
        }

    # Schema A/E/G: dict of question_results / questions
    qr = pm.get("question_results") or pm.get("questions") if isinstance(pm.get("questions"), dict) else pm.get("question_results")
    if isinstance(qr, dict) and qr:
        for k, v in qr.items():
            if not isinstance(v, dict):
                continue
            outcome_raw = v.get("outcome_numeric") if v.get("outcome_numeric") is not None else v.get("outcome")
            add(q_num(k), v.get("question"), v.get("our_estimate"), v.get("crowd_estimate"), outcome_raw, v.get("rbp"), v.get("notes") or v.get("note"), raw_key=k)

    # Schema B: questions is a list (also covers the bih_qat "computed but never
    # submitted" variant, which uses 'our_est_unsubmitted' + 'submitted': null)
    elif isinstance(pm.get("questions"), list) and pm["questions"]:
        for item in pm["questions"]:
            if not isinstance(item, dict):
                continue
            qn = f"Q{item.get('q', '')}"
            our_est = item.get("us")
            actually_submitted = True
            if our_est is None and "our_est_unsubmitted" in item:
                our_est = item.get("our_est_unsubmitted")
                actually_submitted = bool(item.get("submitted"))
            add(qn, item.get("leaderboard_question") or item.get("question"), our_est, item.get("crowd"), item.get("outcome"), item.get("rbp"), item.get("note"), actually_submitted, raw_key=item.get("leaderboard_question") or qn)

    # Schema C/D/era3: results dict or outcomes dict
    elif isinstance(pm.get("results"), dict) or isinstance(pm.get("outcomes"), dict):
        res_dict = pm.get("results") or pm.get("outcomes")
        for k, v in res_dict.items():
            if not isinstance(v, dict):
                continue
            qn = q_num(k)
            our_est = v.get("our_est") if v.get("our_est") is not None else v.get("our_estimate")
            crowd_est = v.get("crowd")
            if our_est is None and k in sub_ests and isinstance(sub_ests[k], dict):
                our_est = sub_ests[k].get("estimate")
                crowd_est = crowd_est or sub_ests[k].get("crowd_pred")
            add(qn, v.get("question"), our_est, crowd_est, v.get("outcome"), v.get("rbp"), v.get("note"), raw_key=k)

    # Calibration-only matches (no real submission): post_match_results.crowd_results
    elif isinstance(pm.get("crowd_results"), dict) and pm["crowd_results"]:
        match_no_submission_flag = True
        for k, v in pm["crowd_results"].items():
            if not isinstance(v, dict):
                continue
            qn = q_num(k)
            add(qn, None, v.get("our_estimate"), v.get("crowd_estimate"), v.get("outcome"), None, v.get("notes") or v.get("note"), actually_submitted=False)

    return key_used, out, final_score, match_total_rbp, settled_date, pm.get("beat_crowd_count"), match_no_submission_flag


def detect_schema_era(d):
    if "model_outputs" in d and ("rules_fired" in d or "rules_applied" in d) and ("final_estimates" in d or "question_analysis" in d):
        return 3
    if "model_outputs" in d or "rules_in_effect" in d or "elo_ratings" in d:
        return 2
    return 1


def extract_venue_group_gameday(d):
    return d.get("venue"), d.get("group"), d.get("game_day"), d.get("tournament")


def parse_city_from_venue_string(venue_str):
    if not venue_str or not isinstance(venue_str, str):
        return None
    parts = [p.strip() for p in venue_str.split(",")]
    if len(parts) >= 2:
        city_part = parts[1]
        city_part = re.sub(r"\s*\([^)]*\)", "", city_part).strip()
        return city_part
    return None


# ──────────────────────────────────────────────────────────────────────────
# 4. Main build
# ──────────────────────────────────────────────────────────────────────────

def main():
    print("Loading supplementary data sources...")
    elo_lookup = load_elo_lookup()
    team_dates_index = load_team_match_dates()
    venue_lookup = load_venue_lookup()
    altitude_lookup = load_altitude_lookup()
    squad_lookup = load_squad_lookup()
    ordered_logit = load_ordered_logit_coefs()
    poisson_coefs = load_poisson_coefs()

    rows = []
    files_processed = 0
    files_skipped = []
    post_match_key_counts = {"post_match_results": 0, "post_match": 0, "none": 0}
    squad_unmatched = set()

    for fpath in sorted(EXT_MARKETS.glob("*.json")):
        fname = fpath.name
        if not is_match_file(fname):
            continue

        with open(fpath, encoding="utf-8") as f:
            try:
                d = json.load(f)
            except json.JSONDecodeError as e:
                files_skipped.append((fname, f"JSON error: {e}"))
                continue

        codes = extract_slug_codes(fname)
        if len(codes) != 2:
            files_skipped.append((fname, f"could not extract 2 team codes from filename (got {codes})"))
            continue
        code_a, code_b = codes
        team_a = CODE_TO_NAME.get(code_a, code_a)
        team_b = CODE_TO_NAME.get(code_b, code_b)
        match_code = f"{code_a}-{code_b}"
        date = extract_date(fname)

        key_used, post_match_qs, final_score, match_total_rbp, settled_date, beat_crowd_count, match_no_submission_flag = extract_post_match(d)
        post_match_key_counts[key_used or "none"] += 1

        if not post_match_qs:
            files_skipped.append((fname, "no post-match question data found (no post_match_results/post_match key, or empty)"))
            continue

        pre_match_ests, draft_key_to_qn = extract_pre_match_estimates(d, post_match_qs)
        edge_ranks = extract_edge_ranks(d, draft_key_to_qn)
        rules_fired_list, rule_bool = extract_rules(d)
        player_profiles = extract_player_profiles(d)
        venue_raw, group, game_day, tournament = extract_venue_group_gameday(d)
        schema_era = detect_schema_era(d)

        no_submission_text = " ".join(str(x) for x in [d.get("submission_note")]).upper()
        no_submission_flag = (match_no_submission_flag or "NO SUBMISSION" in no_submission_text
                               or "our_estimates_calibration" in d)
        is_calibration_only = no_submission_flag

        # ── pre-match feature joins (match-level, computed once per file) ──
        elo_a = elo_b = elo_diff = None
        elo_match = lookup_with_date_tolerance(elo_lookup, team_a, team_b, date)
        if elo_match:
            elo_a = elo_match.get(team_a)
            elo_b = elo_match.get(team_b)
        # prefer the value actually used in the raw file's own model_inputs/elo_ratings if present
        model_inputs = d.get("model_inputs") or d.get("elo_ratings") or {}
        for k, v in model_inputs.items():
            kl = k.lower()
            if kl.startswith(code_a.lower()) and "elo" in kl:
                elo_a = safe_float(v)
            elif kl.startswith(code_b.lower()) and "elo" in kl:
                elo_b = safe_float(v)
        if elo_a is not None and elo_b is not None:
            elo_diff = elo_a - elo_b

        rest_a = rest_days_for(team_dates_index, team_a, date)
        rest_b = rest_days_for(team_dates_index, team_b, date)
        rest_diff = (rest_a - rest_b) if (rest_a is not None and rest_b is not None) else None

        venue_city = parse_city_from_venue_string(venue_raw)
        venue_country = None
        if not venue_city:
            vlookup = lookup_with_date_tolerance(venue_lookup, team_a, team_b, date)
            if vlookup:
                venue_city, venue_country = vlookup
        venue_city_clean = re.sub(r"\s+area$", "", venue_city, flags=re.IGNORECASE) if venue_city else venue_city
        alt_city = VENUE_CITY_ALIASES.get(venue_city_clean, venue_city_clean)
        altitude_m = altitude_lookup.get(alt_city) if alt_city else None

        squad_a = squad_lookup.get(TRANSFERMARKT_NAME_ALIASES.get(team_a, team_a))
        squad_b = squad_lookup.get(TRANSFERMARKT_NAME_ALIASES.get(team_b, team_b))
        if squad_a is None:
            squad_unmatched.add(team_a)
        if squad_b is None:
            squad_unmatched.add(team_b)

        draw_prob = None
        model_outputs = d.get("model_outputs") or {}
        for k, v in model_outputs.items():
            if k.lower() in ("p_draw",):
                draw_prob = safe_float(v)
        if draw_prob is None and elo_diff is not None:
            b_elo, b_home = ordered_logit["b_elo"], ordered_logit["b_home"]
            c1, c2 = ordered_logit["c1"], ordered_logit["c2"]
            eta = b_elo * elo_diff + b_home * 0  # neutral venue assumption
            p_away_or_less = 1 / (1 + math.exp(-(c1 - eta)))
            p_home_or_less = 1 / (1 + math.exp(-(c2 - eta)))
            draw_prob = p_home_or_less - p_away_or_less

        lambda_a = lambda_b = None
        for k, v in model_outputs.items():
            kl = k.lower()
            if kl == f"lambda_{code_a.lower()}":
                lambda_a = safe_float(v)
            elif kl == f"lambda_{code_b.lower()}":
                lambda_b = safe_float(v)
        if lambda_a is None and elo_diff is not None:
            intercept, coef = poisson_coefs["intercept"], poisson_coefs["elo_diff_coef"]
            lambda_a = math.exp(intercept + coef * elo_diff)
            lambda_b = math.exp(intercept + coef * (-elo_diff))

        match_meta = dict(
            file=fname, match=match_code, team_a=team_a, team_b=team_b,
            team_a_code=code_a, team_b_code=code_b, date=date,
            tournament=tournament, group=group, game_day=game_day,
            venue_raw=venue_raw, venue_city=venue_city, venue_country=venue_country,
            altitude_m=altitude_m,
            schema_era=schema_era, post_match_key_used=key_used,
            final_score=final_score, match_total_rbp=safe_float(match_total_rbp),
            settled_date=settled_date,
            match_submitted=not no_submission_flag,
            match_is_calibration_only=is_calibration_only,
            elo_team_a_pre=elo_a, elo_team_b_pre=elo_b, elo_diff=elo_diff,
            rest_days_a=rest_a, rest_days_b=rest_b, rest_days_diff=rest_diff,
            squad_value_a_eur=(squad_a or {}).get("total_market_value_eur"),
            squad_value_b_eur=(squad_b or {}).get("total_market_value_eur"),
            squad_avg_age_a=(squad_a or {}).get("average_age"),
            squad_avg_age_b=(squad_b or {}).get("average_age"),
            fifa_ranking_2025_a=(squad_a or {}).get("fifa_ranking_2025"),
            fifa_ranking_2025_b=(squad_b or {}).get("fifa_ranking_2025"),
            draw_probability=draw_prob,
            poisson_lambda_a=lambda_a, poisson_lambda_b=lambda_b,
            rules_fired_list=";".join(rules_fired_list),
            rule_fired_count=len(rules_fired_list),
            **{f"{r.lower()}_fired": rule_bool[r] for r in RULE_NAMES},
        )

        for qn, pm_data in post_match_qs.items():
            pre = pre_match_ests.get(qn, {})
            question_text = pm_data.get("question_text") or pre.get("question_text")
            our_est = pm_data.get("our_estimate")
            recommended_est = pre.get("recommended_estimate")
            actually_submitted = pm_data.get("actually_submitted", True)
            submission_diff = None
            submission_error_flag = False
            if actually_submitted and our_est is not None and recommended_est is not None:
                submission_diff = round(recommended_est - our_est, 4)
                submission_error_flag = abs(submission_diff) > 0.03

            is_player_prop, player_key = detect_is_player_prop(question_text, player_profiles)
            outcome = pm_data.get("outcome")
            rbp = pm_data.get("rbp") if actually_submitted else None
            beat_crowd = None if rbp is None else (rbp > 0)

            row = dict(match_meta)
            row.update(dict(
                question_num=qn,
                question_text=question_text,
                question_category=pre.get("category"),
                confidence=pre.get("confidence"),
                direction=pre.get("direction"),
                key_drivers=pre.get("key_drivers"),
                edge_rank=edge_ranks.get(qn),
                recommended_estimate=recommended_est,
                our_estimate=our_est,
                submission_diff=submission_diff,
                submission_error_flag=submission_error_flag,
                crowd_estimate=pm_data.get("crowd_estimate"),
                outcome=outcome,
                outcome_known=outcome is not None,
                rbp=rbp,
                beat_crowd=beat_crowd,
                actually_submitted=actually_submitted,
                is_player_prop=is_player_prop,
                player_key=player_key,
                postmortem_note=pm_data.get("note"),
            ))
            rows.append(row)

        files_processed += 1

    if squad_unmatched:
        print(f"\n[INFO] {len(squad_unmatched)} teams have no Transfermarkt squad-value match (left null): {sorted(squad_unmatched)}")

    # sort chronologically, then by match, then by question number
    def sort_key(r):
        qn = int(re.sub(r"[^0-9]", "", r["question_num"]) or "0")
        return (r["date"], r["match"], qn)
    rows.sort(key=sort_key)

    fieldnames = list(rows[0].keys()) if rows else []
    OUT_CSV.parent.mkdir(exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"\n{'=' * 70}")
    print(f"FILES PROCESSED: {files_processed}")
    print(f"FILES SKIPPED:   {len(files_skipped)}")
    for fn, reason in files_skipped:
        print(f"  [SKIP] {fn}: {reason}")
    print(f"\npost_match key usage: {post_match_key_counts}")
    print(f"\nTOTAL ROWS: {len(rows)}")
    print(f"TOTAL COLUMNS: {len(fieldnames)}")
    matches = sorted(set(r["match"] for r in rows))
    print(f"UNIQUE MATCHES: {len(matches)}")
    print(f"Output written to: {OUT_CSV}")


if __name__ == "__main__":
    main()
