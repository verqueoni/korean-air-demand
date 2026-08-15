# Day 1 — manual T-100 download instructions

Why manual: `transtats.bts.gov` requires JavaScript to submit the field-selection
form, and its bulk PREZIP endpoint isn't reachable from an automated sandbox.
This is a known BTS limitation, not specific to this project — the standard
workaround is the manual/scripted-POST download documented here.

## Steps

1. Go to https://www.transtats.bts.gov/Tables.asp?DB_ID=111
2. Select the **T-100 International Segment (All Carriers)** table (Data Bank 28IS).
3. On the field-selection screen, check exactly these fields:
   - `YEAR`
   - `MONTH`
   - `UNIQUE_CARRIER`
   - `CARRIER`
   - `CARRIER_NAME`
   - `ORIGIN`
   - `DEST`
   - `PASSENGERS`
   - `SEATS`
   - `DEPARTURES_PERFORMED`
   - `DEPARTURES_SCHEDULED`
   - `AIRCRAFT_TYPE`
   - `CLASS`
   - `DISTANCE`
   - `CARRIER_GROUP`
4. Filter by year and download **one file per year, 2015 → latest available**
   (the site enforces a per-download row cap, so year-by-year is required —
   not just a convenience).
5. Rename each download to `t100_intl_YYYY.csv` (e.g. `t100_intl_2015.csv`)
   and drop it into `data/raw/`.
6. Before you start filtering by `CLASS`, check the CLASS code lookup on the
   BTS site (linked from the field-selection page) and note which code(s)
   mean "scheduled passenger service" — do not guess. `load_t100.py` will
   print the CLASS value distribution in your actual download so you can
   cross-check it against the lookup.

## After downloading

From the repo root:

```bash
python src/ingest/load_t100.py       # concatenates, prints CLASS values, loads DuckDB
# -> inspect the CLASS value counts, fill in SCHEDULED_PASSENGER_CLASS_CODES
#    in src/ingest/load_t100.py, re-run
python src/ingest/validate_day1.py   # route coverage + as-of date
```

`load_t100.py` appends a provenance skeleton (filename, row count, sha256) to
`data/SOURCES.md` automatically — you only need to fill in the download date
next to each entry.

## Done when

- The KE ICN–LAX monthly query returns a continuous series with no unexplained gaps.
- All five modelled routes (ICN–LAX, ICN–JFK, ICN–SFO, ICN–SEA, ICN–ATL) show
  up in the coverage check.
- `data/SOURCES.md` has one entry per year with checksum, row count, and download date.
- The as-of date (`MAX(YEAR*100+MONTH)`) is written into `docs/DECISIONS.md`.
