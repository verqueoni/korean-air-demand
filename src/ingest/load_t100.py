"""
Day 1 -- Ingest BTS T-100 International Segment data into DuckDB.

Usage:
    python src/ingest/load_t100.py

Expects one CSV per year at data/raw/t100_intl_YYYY.csv, downloaded manually
from https://www.transtats.bts.gov/Tables.asp?DB_ID=111 (T-100 International
Segment, All Carriers) per docs/DOWNLOAD_INSTRUCTIONS.md.
"""
import hashlib
import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "warehouse.duckdb"
SOURCES_LOG = ROOT / "data" / "SOURCES.md"

EXPECTED_COLUMNS = [
    "YEAR", "MONTH", "UNIQUE_CARRIER", "CARRIER", "CARRIER_NAME",
    "ORIGIN", "DEST", "PASSENGERS", "SEATS", "DEPARTURES_PERFORMED",
    "DEPARTURES_SCHEDULED", "AIRCRAFT_TYPE", "CLASS", "DISTANCE",
    "CARRIER_GROUP",
]

# TODO (Day 1 gate -- must resolve before trusting downstream numbers):
# Confirm the CLASS code(s) that mean "scheduled passenger service" against
# the live BTS CLASS code lookup at transtats.bts.gov before relying on this
# filter. Do not guess. Run this script first to see the CLASS value counts
# printed below, cross-check each code against the BTS glossary, then set
# SCHEDULED_PASSENGER_CLASS_CODES accordingly and record the decision (with
# the codes kept and why) in docs/DECISIONS.md.
SCHEDULED_PASSENGER_CLASS_CODES: list[str] = []  # <-- fill in after verifying

ROUTES_OF_INTEREST = [
    ("KE", "ICN", "LAX"),
    ("KE", "ICN", "JFK"),
    ("KE", "ICN", "SFO"),
    ("KE", "ICN", "SEA"),
    ("KE", "ICN", "ATL"),
]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_year_file(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, encoding="utf-8", low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="cp949", low_memory=False)
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def main() -> None:
    files = sorted(RAW_DIR.glob("t100_intl_*.csv"))
    if not files:
        print(f"No files found in {RAW_DIR}.")
        print("Expected one file per year named t100_intl_YYYY.csv --")
        print("see docs/DOWNLOAD_INSTRUCTIONS.md.")
        sys.exit(1)

    frames = []
    log_lines = []
    for f in files:
        df = load_year_file(f)
        missing = set(EXPECTED_COLUMNS) - set(df.columns)
        if missing:
            print(f"WARNING: {f.name} missing expected columns: {sorted(missing)}")
        frames.append(df)
        checksum = sha256_of(f)
        log_lines.append(
            f"- `{f.name}` -- rows: {len(df)}, sha256: `{checksum}`"
        )
        print(f"{f.name}: {len(df):,} rows, sha256 {checksum[:16]}...")

    t100_raw_all = pd.concat(frames, ignore_index=True)
    print(f"\nCombined: {len(t100_raw_all):,} rows across {len(files)} files")

    if "CLASS" in t100_raw_all.columns:
        print("\nCLASS value counts (verify against the BTS CLASS code lookup "
              "before trusting SCHEDULED_PASSENGER_CLASS_CODES above):")
        print(t100_raw_all["CLASS"].value_counts())

    if SCHEDULED_PASSENGER_CLASS_CODES:
        filtered = t100_raw_all[t100_raw_all["CLASS"].isin(SCHEDULED_PASSENGER_CLASS_CODES)]
        print(f"\nAfter CLASS filter {SCHEDULED_PASSENGER_CLASS_CODES}: "
              f"{len(filtered):,} rows ({len(t100_raw_all) - len(filtered):,} dropped)")
    else:
        filtered = t100_raw_all
        print("\nSCHEDULED_PASSENGER_CLASS_CODES is empty -- loading UNFILTERED. "
              "Fill it in per the TODO above and re-run before treating this as final.")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE OR REPLACE TABLE t100_raw AS SELECT * FROM filtered")
    con.close()
    print(f"\nLoaded into {DB_PATH} as table t100_raw")

    with open(SOURCES_LOG, "a") as f:
        f.write("\n## T-100 International Segment (auto-logged by load_t100.py)\n\n")
        f.write("Source: https://www.transtats.bts.gov/Tables.asp?DB_ID=111 "
                "(T-100 International Segment, All Carriers)\n\n")
        f.write("Download date: <<FILL IN -- date you downloaded each file>>\n\n")
        for line in log_lines:
            f.write(line + "\n")
    print(f"Provenance skeleton appended to {SOURCES_LOG} -- fill in download date.")

    print("\nRun src/ingest/validate_day1.py next to check route coverage "
          "and the as-of date.")


if __name__ == "__main__":
    main()
