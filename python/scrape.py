#!/usr/bin/env python3
"""
Wrapper for google-maps-scraper.

Usage:
  python scrape.py                              # uses config.json
  python scrape.py config.json                  # explicit config
  python scrape.py --campaign babitha_employers_kwc
  python scrape.py --campaign blue_collar_kwc --batch 3
  python scrape.py --list-campaigns             # show all campaigns
"""

import argparse
import csv
import os
import re
import subprocess
import sys
import tempfile
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from campaigns import CAMPAIGNS

KEEP_COLS = ["title", "category", "address", "website", "phone", "emails"]

_default_bin = "../google-maps-scraper.exe" if sys.platform == "win32" else "../google-maps-scraper"
BINARY = os.environ.get("SCRAPER_BINARY", _default_bin)


# ── helpers ──────────────────────────────────────────────────────────────────

def run_scraper(query, output_csv, grid=None):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as qf:
        qf.write(query + "\n")
        query_file = qf.name

    cmd = [BINARY, "-input", query_file, "-results", str(output_csv), "-email"]

    if grid:
        bbox = f"{grid['min_lat']},{grid['min_lon']},{grid['max_lat']},{grid['max_lon']}"
        cmd += ["-grid-bbox", bbox, "-grid-cell", str(grid["cell"])]

    print(f"    → {query!r}")
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            print(f"      {line.rstrip()}")
        proc.wait()
        return proc.returncode == 0
    except Exception as e:
        print(f"    ERROR: {e}", file=sys.stderr)
        return False
    finally:
        if os.path.exists(query_file):
            os.unlink(query_file)


def read_csv_slim(path):
    rows = []
    try:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rows.append({col: row.get(col, "") for col in KEEP_COLS})
    except Exception:
        pass
    return rows


def dedup(rows):
    seen_phones, seen_ta = set(), set()
    out = []
    for row in rows:
        phone = re.sub(r"\D", "", row.get("phone", ""))
        ta = (row.get("title", "").lower().strip(), row.get("address", "").lower().strip())
        if phone and phone in seen_phones:
            continue
        if ta in seen_ta:
            continue
        if phone:
            seen_phones.add(phone)
        seen_ta.add(ta)
        out.append(row)
    return out


def apply_filters(rows, require_email=False, require_phone=False,
                  require_website=False, no_website=False):
    if require_email:
        rows = [r for r in rows if r.get("emails", "").strip()]
    if require_phone:
        rows = [r for r in rows if r.get("phone", "").strip()]
    if require_website:
        rows = [r for r in rows if r.get("website", "").strip()]
    if no_website:
        rows = [r for r in rows if not r.get("website", "").strip()]
    return rows


def write_csv(rows, path):
    if not rows:
        print("No results to write.")
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=KEEP_COLS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {len(rows)} rows → {path}")


def print_stats(rows):
    print(f"  Total:        {len(rows)}")
    print(f"  With email:   {sum(1 for r in rows if r.get('emails','').strip())}")
    print(f"  With phone:   {sum(1 for r in rows if r.get('phone','').strip())}")
    print(f"  With website: {sum(1 for r in rows if r.get('website','').strip())}")
    print(f"  No website:   {sum(1 for r in rows if not r.get('website','').strip())}")


# ── campaign mode ─────────────────────────────────────────────────────────────

def run_campaign(campaign_id, batch_num=None, output_dir=Path("results"),
                 require_email=False, require_phone=False,
                 require_website=False, no_website=False):

    c = CAMPAIGNS.get(campaign_id)
    if not c:
        print(f"Unknown campaign: {campaign_id}")
        print("Available:", ", ".join(CAMPAIGNS.keys()))
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    grid = {**c["bbox"], "cell": c["cell"]}

    batches = c["batches"]
    if batch_num is not None:
        if batch_num < 1 or batch_num > len(batches):
            print(f"Batch {batch_num} out of range. Campaign has {len(batches)} batches.")
            sys.exit(1)
        batches_to_run = [(batch_num - 1, batches[batch_num - 1])]
    else:
        batches_to_run = list(enumerate(batches))

    print(f"\nCampaign: {c['label']}")
    print(f"Batches:  {len(batches_to_run)} of {len(c['batches'])}")
    print(f"Grid:     {grid}")
    print()

    all_rows = []

    for idx, batch in batches_to_run:
        print(f"── Batch {idx+1}/{len(c['batches'])} ──")
        for query in batch:
            slug = re.sub(r"[^\w]+", "_", query.lower())[:50]
            tmp_csv = output_dir / f"batch{idx+1:02d}_{slug}.csv"
            ok = run_scraper(query, tmp_csv, grid=grid)
            if ok and tmp_csv.exists():
                rows = read_csv_slim(tmp_csv)
                print(f"      Got {len(rows)} results")
                all_rows.extend(rows)

    print(f"\nTotal before dedup: {len(all_rows)}")
    deduped = dedup(all_rows)
    print(f"After dedup:        {len(deduped)}")
    filtered = apply_filters(deduped, require_email, require_phone, require_website, no_website)
    print(f"After filters:      {len(filtered)}")

    suffix = f"_batch{batch_num}" if batch_num else ""
    out_path = output_dir / f"{campaign_id}{suffix}_master.csv"
    write_csv(filtered, out_path)
    print_stats(filtered)


# ── config mode ───────────────────────────────────────────────────────────────

def run_config(cfg_path):
    with open(cfg_path) as f:
        config = json.load(f)

    output_dir = Path(config.get("output_dir", "results"))
    output_dir.mkdir(parents=True, exist_ok=True)
    filters = config.get("filters", {})
    all_rows = []

    for i, query in enumerate(config["queries"]):
        slug = re.sub(r"[^\w]+", "_", query.lower())[:50]
        out_csv = output_dir / f"raw_{i:02d}_{slug}.csv"
        ok = run_scraper(query, out_csv)
        if ok and out_csv.exists():
            rows = read_csv_slim(out_csv)
            print(f"  Got {len(rows)} results")
            all_rows.extend(rows)

    print(f"\nTotal before dedup: {len(all_rows)}")
    deduped = dedup(all_rows)
    filtered = apply_filters(deduped, **filters)
    write_csv(filtered, output_dir / "master.csv")
    print_stats(filtered)


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Google Maps Scraper wrapper")
    parser.add_argument("config", nargs="?", default="config.json", help="Config JSON file")
    parser.add_argument("--campaign", "-c", help="Campaign ID to run")
    parser.add_argument("--batch", "-b", type=int, help="Run single batch number (1-based)")
    parser.add_argument("--list-campaigns", "-l", action="store_true", help="List all campaigns")
    parser.add_argument("--output-dir", "-o", default="results", help="Output directory")
    parser.add_argument("--require-email", action="store_true")
    parser.add_argument("--require-phone", action="store_true")
    parser.add_argument("--require-website", action="store_true")
    parser.add_argument("--no-website", action="store_true", help="Only businesses with no website")

    args = parser.parse_args()

    if args.list_campaigns:
        print("\nAvailable campaigns:\n")
        for k, v in CAMPAIGNS.items():
            print(f"  {k}")
            print(f"    {v['label']}")
            print(f"    {len(v['batches'])} batches · goal: {v['goal']}\n")
        return

    if args.campaign:
        run_campaign(
            args.campaign,
            batch_num=args.batch,
            output_dir=Path(args.output_dir),
            require_email=args.require_email,
            require_phone=args.require_phone,
            require_website=args.require_website,
            no_website=args.no_website,
        )
    else:
        run_config(args.config)


if __name__ == "__main__":
    main()
