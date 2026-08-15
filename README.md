# Korean Air Route-Level Demand Forecasting

Route-level demand forecasting and capacity-planning decision tool for
Korean Air, built as a portfolio project (MMA admissions). Forecasts monthly
passengers per route from BTS T-100 and Korean government sources, converts
the forecast into a frequency/capacity recommendation against a derived load
factor target, and measures the value in seats correctly deployed (Capacity
Misallocation Rate) rather than model accuracy alone.

See `docs/project_scope_statement.md` for the full scope and decision
framing, and `docs/implementation_plan.md` for the day-by-day build plan.

## Status

Phase 1 (Days 1-3), in progress.

- [x] Day 1 — repo scaffolding, environment, ingest pipeline written
- [ ] Day 1 — T-100 raw data acquisition: **manual step required**, see
      `docs/DOWNLOAD_INSTRUCTIONS.md`
- [ ] Day 2 — Korean sources + cross-validation
- [ ] Day 3 — covariates + load factor target (L*)

## Reproduce

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 1. Download T-100 International Segment data manually -- see
#    docs/DOWNLOAD_INSTRUCTIONS.md -- and place yearly CSVs in data/raw/
python src/ingest/load_t100.py
python src/ingest/validate_day1.py
```
