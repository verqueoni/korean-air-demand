"""
Day 1 -- validation checks against docs/implementation_plan.md's "Done when".

Usage:
    python src/ingest/validate_day1.py
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "warehouse.duckdb"

ROUTES = [
    ("KE", "ICN", "LAX"),
    ("KE", "ICN", "JFK"),
    ("KE", "ICN", "SFO"),
    ("KE", "ICN", "SEA"),
    ("KE", "ICN", "ATL"),
]


def main() -> None:
    con = duckdb.connect(str(DB_PATH), read_only=True)

    print("=== KE ICN-LAX monthly series (spot check from the plan) ===")
    print(con.execute("""
        SELECT YEAR, MONTH, SUM(PASSENGERS) AS pax, SUM(SEATS) AS seats
        FROM t100_raw
        WHERE UNIQUE_CARRIER = 'KE' AND ORIGIN = 'ICN' AND DEST = 'LAX'
        GROUP BY 1,2 ORDER BY 1,2
    """).df().to_string())

    print("\n=== Route coverage check, all 5 modelled routes ===")
    for carrier, origin, dest in ROUTES:
        n_months = con.execute("""
            SELECT COUNT(DISTINCT YEAR*100+MONTH)
            FROM t100_raw
            WHERE UNIQUE_CARRIER = ? AND ORIGIN = ? AND DEST = ?
        """, [carrier, origin, dest]).fetchone()[0]
        print(f"{carrier} {origin}-{dest}: {n_months} distinct months of data")

    as_of = con.execute("SELECT MAX(YEAR*100+MONTH) FROM t100_raw").fetchone()[0]
    print(f"\n=== As-of date (MAX(YEAR*100+MONTH)) ===\n{as_of}")
    print("Write this into docs/DECISIONS.md as the project's as-of date.")

    con.close()


if __name__ == "__main__":
    main()
