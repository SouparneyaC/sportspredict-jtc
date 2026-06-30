"""
build_feature_matrix.py
=======================
Reads all per-match JSON files in data/external_markets/ that have settled
post_match_results, extracts a flat row per question, handles all schema
versions present in the dataset.

SCHEMAS ENCOUNTERED (documented for future reference):
  Schema A - newer files (bel_irn onwards): post_match_results.question_results
             is a dict keyed Q1_...; values have our_estimate, crowd_estimate,
             outcome (int 0/1), rbp.
  Schema B - older files (bel_egy, ger_cur etc.): post_match_results.questions
             is a list; items have q (int), us, crowd, outcome (int), rbp.
  Schema C - tur_par, usa_aus: post_match_results.results dict; items have
             our_est, crowd, outcome (str YES/NO), rbp. No separate estimates needed.
  Schema D - mex_kor: post_match_results.results dict; items have outcome (str),
             rbp but NO our_est/crowd. Must join with final_submission_estimates.
  Schema E - nzl_egy: post_match_results.question_results dict; items have
             our_estimate, crowd_estimate, outcome (str YES/NO), outcome_numeric (int).
  Schema F - uru_cpv: no JTC submission; crowd_results only. Excluded.

Output: ml/feature_matrix.csv
"""

import json
import os
import csv
import re
from pathlib import Path

BASE = Path(__file__).parent.parent / "data" / "external_markets"
OUT  = Path(__file__).parent / "feature_matrix.csv"

SKIP_PATTERNS = ["smarkets_quotes", "smarkets_raw", "smarkets_parsed",
                 "wc2026_raw", "wc2022_raw", "ledger", "smarkets_markets"]
NO_SUBMISSION = {"uru_cpv"}  # match slugs with no JTC submission

def is_match_file(fname):
    if not fname.endswith(".json"): return False
    for p in SKIP_PATTERNS:
        if p in fname: return False
    return bool(re.search(r'\d{4}-\d{2}-\d{2}', fname))

def extract_date(fname):
    m = re.search(r'(\d{4}-\d{2}-\d{2})', fname)
    return m.group(1) if m else ""

def extract_slug(fname):
    """ger_cur_2026-06-14.json -> 'ger_cur'"""
    parts = fname.replace(".json","").split("_")
    non_date = [p for p in parts if not re.match(r'\d{4}', p)]
    return "_".join(non_date[:2])

def extract_match_code(slug):
    """ger_cur -> GER-CUR"""
    return "-".join(p.upper() for p in slug.split("_")[:2])

def to_int_outcome(val):
    """Convert YES/NO/0/1 to int, return None on failure."""
    if val is None: return None
    if isinstance(val, (int, float)): return int(val)
    if isinstance(val, str):
        v = val.strip().upper()
        if v == "YES": return 1
        if v == "NO":  return 0
    return None

def q_num(key):
    m = re.match(r'(Q\d+)', str(key), re.IGNORECASE)
    return m.group(1).upper() if m else str(key)

# ──────────────────────────────────────────
rows = []
schema_log = {}   # fname -> schema letter used
files_processed = 0
files_skipped = 0

for fpath in sorted(BASE.glob("*.json")):
    fname = fpath.name
    if not is_match_file(fname): continue

    slug = extract_slug(fname)
    date = extract_date(fname)
    match_code = extract_match_code(slug)

    if slug in NO_SUBMISSION:
        print(f"  [SKIP no-sub] {fname}")
        continue

    with open(fpath, encoding="utf-8") as f:
        try:
            d = json.load(f)
        except json.JSONDecodeError as e:
            print(f"  [ERR json] {fname}: {e}")
            files_skipped += 1
            continue

    pm = d.get("post_match_results")
    if not pm:
        print(f"  [SKIP no-pm] {fname}")
        files_skipped += 1
        continue

    sub_ests = d.get("final_submission_estimates") or {}
    # has_sub_estimate: 1 if final_submission_estimates has ≥1 filled estimate
    has_sub_estimate = int(any(
        isinstance(v, dict) and v.get("estimate") is not None
        for v in sub_ests.values()
    ))

    extracted = []   # list of dicts to add to rows

    # ── Schema A / E: post_match_results.question_results is a dict ──────────
    qr_dict = pm.get("question_results")
    if isinstance(qr_dict, dict) and qr_dict:
        schema = "A/E"
        for k, v in qr_dict.items():
            if not isinstance(v, dict): continue
            outcome_raw = v.get("outcome_numeric") if v.get("outcome_numeric") is not None \
                          else v.get("outcome")
            extracted.append({
                "question_num":   q_num(k),
                "question_key":   v.get("question") or k,
                "our_estimate":   v.get("our_estimate"),
                "crowd_estimate": v.get("crowd_estimate"),
                "outcome":        to_int_outcome(outcome_raw),
                "rbp":            v.get("rbp"),
            })

    # ── Schema G: post_match_results.questions is a DICT (e.g. NZL-EGY) ──────
    elif isinstance(pm.get("questions"), dict) and pm["questions"]:
        schema = "G"
        for k, v in pm["questions"].items():
            if not isinstance(v, dict): continue
            outcome_raw = v.get("outcome_numeric") if v.get("outcome_numeric") is not None \
                          else v.get("outcome")
            extracted.append({
                "question_num":   q_num(k),
                "question_key":   v.get("question") or k,
                "our_estimate":   v.get("our_estimate"),
                "crowd_estimate": v.get("crowd_estimate"),
                "outcome":        to_int_outcome(outcome_raw),
                "rbp":            v.get("rbp"),
            })

    # ── Schema B: post_match_results.questions is a list ─────────────────────
    elif isinstance(pm.get("questions"), list) and pm["questions"]:
        schema = "B"
        for item in pm["questions"]:
            if not isinstance(item, dict): continue
            extracted.append({
                "question_num":   f"Q{item.get('q','')}",
                "question_key":   item.get("leaderboard_question") or item.get("question") or f"Q{item.get('q','')}",
                "our_estimate":   item.get("us"),
                "crowd_estimate": item.get("crowd"),
                "outcome":        to_int_outcome(item.get("outcome")),
                "rbp":            item.get("rbp"),
            })

    # ── Schema C/D: post_match_results.results is a dict ─────────────────────
    elif isinstance(pm.get("results"), dict) and pm["results"]:
        schema = "C/D"
        res_dict = pm["results"]
        for k, v in res_dict.items():
            if not isinstance(v, dict): continue
            our_est   = v.get("our_est")    # Schema C has it inline
            crowd_est = v.get("crowd")
            # Schema D fallback: join with final_submission_estimates
            if our_est is None and k in sub_ests:
                sub = sub_ests[k]
                if isinstance(sub, dict):
                    our_est   = sub.get("estimate")
                    crowd_est = crowd_est or sub.get("crowd_pred")
            extracted.append({
                "question_num":   q_num(k),
                "question_key":   v.get("question") or k,
                "our_estimate":   our_est,
                "crowd_estimate": crowd_est,
                "outcome":        to_int_outcome(v.get("outcome")),
                "rbp":            v.get("rbp"),
            })

    else:
        print(f"  [SKIP no-q-data] {fname}  pm_keys={list(pm.keys())}")
        files_skipped += 1
        continue

    schema_log[fname] = schema
    file_rows = 0
    for item in extracted:
        our_est   = item["our_estimate"]
        crowd_est = item["crowd_estimate"]
        outcome   = item["outcome"]
        rbp       = item["rbp"]

        if our_est is None or crowd_est is None or outcome is None:
            print(f"  [WARN null] {fname} {item['question_num']}: "
                  f"our={our_est} crowd={crowd_est} outcome={outcome}")
            continue

        beat = 1 if (rbp is not None and rbp > 0) else 0
        rows.append({
            "match":             match_code,
            "date":              date,
            "question_num":      item["question_num"],
            "question_key":      item["question_key"],
            "our_estimate":      float(our_est),
            "crowd_estimate":    float(crowd_est),
            "outcome":           outcome,
            "rbp":               float(rbp) if rbp is not None else "",
            "beat_crowd":        beat,
            "has_sub_estimate":  has_sub_estimate,
            "schema":            schema,
        })
        file_rows += 1

    files_processed += 1
    print(f"  [OK schema={schema}] {fname}: {file_rows} questions")

# Sort chronologically
def sort_key(r):
    qn = int(re.sub(r'[^0-9]', '', r['question_num']) or '0')
    return (r['date'], r['match'], qn)

rows.sort(key=sort_key)

# Write output
OUT.parent.mkdir(exist_ok=True)
fieldnames = ["match","date","question_num","question_key",
              "our_estimate","crowd_estimate","outcome","rbp","beat_crowd",
              "has_sub_estimate","schema"]

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

# ──────────────────────────────────────────────────────────────────────────────
print(f"\n{'='*64}")
print(f"FILES PROCESSED:  {files_processed}")
print(f"FILES SKIPPED:    {files_skipped}")
print(f"TOTAL ROWS:       {len(rows)}")

submitted = [r for r in rows if r['rbp'] != '']
print(f"\nROWS WITH RBP (usable for diagnostic): {len(submitted)}")

outcomes_yes = sum(1 for r in submitted if r['outcome'] == 1)
outcomes_no  = sum(1 for r in submitted if r['outcome'] == 0)
print(f"  YES outcomes: {outcomes_yes} ({100*outcomes_yes/len(submitted):.1f}%)")
print(f"  NO  outcomes: {outcomes_no}  ({100*outcomes_no/len(submitted):.1f}%)")

beat = sum(1 for r in submitted if r['beat_crowd'] == 1)
print(f"\nBEAT CROWD: {beat}/{len(submitted)} = {100*beat/len(submitted):.1f}%")

import statistics
rbps = [float(r['rbp']) for r in submitted if r['rbp'] != '']
print(f"Mean RBP/question: {statistics.mean(rbps):+.3f}")
print(f"Std  RBP/question: {statistics.stdev(rbps):.3f}")
print(f"Total RBP (sum):   {sum(rbps):+.2f}")

print(f"\nMATCHES COVERED:")
matches = {}
for r in submitted:
    if r['match'] not in matches:
        matches[r['match']] = {'date': r['date'], 'n': 0, 'rbp': 0.0}
    matches[r['match']]['n'] += 1
    matches[r['match']]['rbp'] += float(r['rbp']) if r['rbp'] != '' else 0
for m, v in sorted(matches.items(), key=lambda x: x[1]['date']):
    print(f"  {v['date']} {m:10s} {v['n']:2d} questions  RBP={v['rbp']:+.2f}")

print(f"\nOutput written to: {OUT}")
