# Decisions log

Judgment calls and their justification, in chronological order.
## Day 1 — T-100 acquisition is manual, not scripted

`transtats.bts.gov` requires JavaScript to submit its field-selection form,
and the bulk PREZIP endpoint is not reachable from an automated environment.
Confirmed by direct testing (empty response fetching PREZIP zip URLs; the
Socrata API at data.bts.gov only exposes nationwide monthly aggregates, not
route-level microdata). Decision: download year-by-year manually per
`docs/DOWNLOAD_INSTRUCTIONS.md`, and script everything downstream of the raw
CSVs (concatenation, checksum/provenance logging, DuckDB load, validation).
This matches the plan's own note that BTS T-100 "requires year-by-year
downloads via manual checkbox interface or scripted form POST — no simple
file URL exists."

## Day 1 — CLASS code filter deferred to real data

`src/ingest/load_t100.py` leaves `SCHEDULED_PASSENGER_CLASS_CODES` empty by
design. The plan is explicit: do not guess which CLASS codes mean scheduled
passenger service. The script prints the CLASS value distribution from the
actual downloaded files; codes must be cross-checked against the live BTS
CLASS code lookup before the filter is set. Pending real data.
