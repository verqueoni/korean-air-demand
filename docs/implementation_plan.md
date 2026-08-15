# Implementation Plan — 14 Days

**Companion to:** `project_scope_statement.md` (v2.0)
**Project:** Route-Level Demand Forecasting for Transpacific Capacity Planning — Korean Air

Work through this in order. Each day has a **Done when** test — do not start the next day until it passes. If a day overruns, consult the cut order in §Contingency rather than compressing the final days.

---

## Before Day 1

### Repository structure

```
korean-air-demand/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── raw/              # never edited, never committed
│   ├── interim/
│   ├── processed/
│   ├── SOURCES.md        # provenance log
│   └── warehouse.duckdb
├── src/
│   ├── ingest/
│   ├── features/
│   ├── models/
│   └── decision/
├── notebooks/
├── outputs/
│   ├── figures/
│   └── tables/
├── app/
└── docs/
    ├── DECISIONS.md      # judgment calls and their justification
    └── LIMITATIONS.md    # becomes deliverable D7
```

### `.gitignore` — set this before the first commit

```
data/raw/
data/interim/
*.duckdb
.env
__pycache__/
.ipynb_checkpoints/
venv/
```

Raw data does not go in git. The ingest scripts plus `SOURCES.md` are what make it reproducible.

### Environment

```bash
python -m venv venv && source venv/bin/activate
pip install pandas pyarrow duckdb lightgbm scikit-learn \
            matplotlib plotly streamlit shap \
            holidays korean-lunar-calendar openpyxl
pip freeze > requirements.txt
```

### Daily discipline

- Commit at the end of every day, even if incomplete
- Every judgment call goes in `docs/DECISIONS.md` with one line of justification — you will not remember why in three weeks, and an interviewer will ask
- Every raw download gets an entry in `data/SOURCES.md`: URL, download date, file checksum, row count

---

## PHASE 1 — FOUNDATION (Days 1–3)

### Day 1 — Repository and T-100

- [ ] Create the folder structure and `.gitignore`; `git init`; first commit
- [ ] Set up the virtual environment and install packages
- [ ] Go to [TranStats Tables](https://www.transtats.bts.gov/Tables.asp?DB_ID=111)
- [ ] Select the **T-100 International Segment (All Carriers)** table
- [ ] Choose fields: `YEAR`, `MONTH`, `UNIQUE_CARRIER`, `CARRIER`, `CARRIER_NAME`, `ORIGIN`, `DEST`, `PASSENGERS`, `SEATS`, `DEPARTURES_PERFORMED`, `DEPARTURES_SCHEDULED`, `AIRCRAFT_TYPE`, `CLASS`, `DISTANCE`, `CARRIER_GROUP`
- [ ] Download year by year, 2015 → latest. Save as `data/raw/t100_intl_YYYY.csv`
- [ ] **Check the `CLASS` code lookup on the BTS site before filtering** — do not guess which codes mean scheduled passenger service. Record the codes you keep in `DECISIONS.md`.
- [ ] Write `src/ingest/load_t100.py`: read all yearly files, concatenate, filter to scheduled passenger service, load into DuckDB as table `t100_raw`
- [ ] Record download date, URL, and row count per file in `SOURCES.md`

**Done when** this query returns a continuous monthly series:

```sql
SELECT YEAR, MONTH, SUM(PASSENGERS) AS pax, SUM(SEATS) AS seats
FROM t100_raw
WHERE UNIQUE_CARRIER = 'KE' AND ORIGIN = 'ICN' AND DEST = 'LAX'
GROUP BY 1,2 ORDER BY 1,2;
```

- [ ] Run `SELECT MAX(YEAR*100+MONTH) FROM t100_raw` and **write the result into `DECISIONS.md` as the project's as-of date.** Every forecast is anchored to it.

**Watch for:** duplicate rows from multiple aircraft types on the same route-month — this is expected and correct; aggregate, don't deduplicate.

---

### Day 2 — Korean sources and cross-validation

- [ ] Download from [data.go.kr — by airline](https://www.data.go.kr/data/15049013/fileData.do), looping by calendar year, **2022 → 2026 only** (cross-validation, not modelling)
- [ ] Download from [KAC international route stats](https://www.airport.co.kr/www/cms/frFlightStatsCon/internationalLineStats.do?MENU_ID=1250)
- [ ] Download from [IIAC statistics](https://www.airport.kr/co/en/cpr/statisticOfLocalAirport.do) — **required separately, KAC does not cover Incheon**
- [ ] Build a field-name dictionary (Korean → English) in `docs/DECISIONS.md`; map once, reuse
- [ ] Load into DuckDB as `molit_airline`, `kac_routes`, `iiac_routes`
- [ ] Write `notebooks/01_cross_validation.ipynb`: compare KE monthly international passengers, T-100 versus Korean sources, over the overlapping window
- [ ] Quantify the discrepancy as a percentage and explain the cause (scope differences — T-100 covers only US-touching flights; Korean sources cover the full network)

**Done when** you can state in one sentence why the two sources differ and by how much. That sentence goes in the deck.

**Watch for:** Korean files often use CP949/EUC-KR encoding, not UTF-8. If you see mojibake, specify the encoding on read.

---

### Day 3 — Covariates and the load factor target

- [ ] Download [EIA jet fuel monthly](https://www.eia.gov/dnav/pet/hist/eer_epjk_pf4_rgc_dpgM.htm) or [FRED `MJFUELUSGULF`](https://fred.stlouisfed.org/data/MJFUELUSGULF), 2014 → present
- [ ] Download KRW–USD from [FRED](https://fred.stlouisfed.org), 2014 → present; aggregate daily to monthly mean
- [ ] Generate holiday flags: US federal via `holidays`; Seollal and Chuseok via `korean-lunar-calendar`. **Encode as a fraction of the month, not a binary** — a lunar holiday can straddle two Gregorian months
- [ ] **Derive the target load factor L\*.** Compute Korean Air's achieved passenger load factor on the in-scope routes over the recovery period from T-100 (`SUM(PASSENGERS)/SUM(SEATS)`). Cross-check against KE's published network load factor.
- [ ] Write the derivation into `DECISIONS.md` with the actual number and the window used
- [ ] Pick three values around it (e.g. L\*−3pp, L\*, L\*+3pp) for the Day 9 sensitivity band

**Done when** `SOURCES.md` is complete with checksums, and `DECISIONS.md` contains a justified L\* with its derivation.

> ### GATE — end of Day 3
> If clean route-level demand data does not exist for all five routes, **cut to three routes and continue.** Do not spend Day 4 on data acquisition.

---

## PHASE 2 — ANALYSIS (Days 4–5)

### Day 4 — EDA and three structural questions

- [ ] Plot monthly passengers by route, 2015 → present, all five on one figure
- [ ] **Question 1 — where does the recovery regime start?** Plot ICN–LAX and identify the month where the series rejoins a stable trend. Record the chosen cutoff and reasoning in `DECISIONS.md`. Do not default to a policy date.
- [ ] **Question 2 — which route-months are censored?** Flag every route-month with load factor above ~90%. Count them. These are months where observed passengers understate true demand.
- [ ] **Question 3 — where does the Asiana merger break the competitor features?** Plot combined KE+OZ seats on ICN–LAX by month; find the level shift or schedule rationalisation. Record the date and your chosen handling (combine KE+OZ from that point, or add a merger indicator, or fall back to US-carriers-only competitors).
- [ ] Plot seasonality: month-of-year profile per route, recovery period only
- [ ] Plot competitor capacity trends: DL, UA, AA, OZ seats per route-month
- [ ] Plot the load factor distribution — this motivates the whole capacity argument

**Done when** you have five figures saved to `outputs/figures/` that would survive being shown to an executive, and three answered questions in `DECISIONS.md`.

---

### Day 5 — Feature engineering

- [ ] Build the modelling table at carrier × route × month grain
- [ ] Apply the log transform to the target: `y = log(passengers)`
- [ ] Calendar features: month, quarter, holiday-fraction flags
- [ ] Lag features: `y` at t−1, t−2, t−3, t−12
- [ ] Rolling features: 3- and 12-month means and standard deviations, **all shifted so no current-month information leaks**
- [ ] Competitor features: total competitor seats on the city pair, route-level HHI, count of carriers
- [ ] Route attributes: distance, aircraft type mix
- [ ] Macro: fuel price, KRW–USD, both lagged
- [ ] Regime indicator for the recovery period
- [ ] Merger indicator, per the Day 4 decision

- [ ] **Leakage audit — write it down in the notebook.** For each feature, state what date it would have been knowable. Anything requiring same-month information is removed. Seats and departures are a judgment call: schedules are published months ahead, so scheduled capacity is legitimately knowable — but justify it explicitly.

**Done when** the modelling table is saved to `data/processed/` and the leakage audit is written out feature by feature.

---

## PHASE 3 — MODELLING (Days 6–8)

### Day 6 — Baselines and the backtest harness

- [ ] Implement seasonal naive: forecast = same month, previous year
- [ ] Implement route-month mean as a second baseline
- [ ] Build the rolling-origin backtest: expanding window, 3-month forecast horizon, minimum 24 months training, step forward one month at a time
- [ ] Compute and record **baseline WAPE per route**
- [ ] Compute and record **baseline CMR per route** using the Day 3 L\* — you need this now, not on Day 9

**Done when** a table of baseline WAPE and baseline CMR per route is saved to `outputs/tables/`. Everything downstream is measured against it.

**Watch for:** the most common fatal error in this project type is random k-fold cross-validation. Splits must be strictly time-ordered.

---

### Day 7 — Global model

- [ ] Fit a single LightGBM across all carrier × route series, with route and carrier as categorical features
- [ ] Use the same rolling-origin harness — no separate evaluation path
- [ ] Compare WAPE against baseline, per route
- [ ] If the global model loses to seasonal naive, investigate before tuning: usual causes are leakage-driven overfitting, insufficient training window, or the regime break not being handled

**Done when** the model beats baseline on at least four of five routes, or you can explain in writing why it doesn't.

---

### Day 8 — Intervals and attribution

- [ ] Refit with quantile objectives at 0.1, 0.5, 0.9 to produce prediction intervals
- [ ] Check interval calibration: roughly 80% of actuals should fall inside the P10–P90 band. If coverage is far off, the intervals are decorative
- [ ] Compute SHAP values; review the top features
- [ ] **Sanity-check direction economically.** More competitor seats should not increase Korean Air demand. If it does, you likely have a capacity-correlation artifact rather than a competitive effect — investigate and document
- [ ] Light hyperparameter tuning, time-ordered only

**Done when** intervals are calibrated and feature attributions are economically sensible or explained.

---

## PHASE 4 — DECISION (Days 9–10)

### Day 9 — The CMR counterfactual

This is the day that produces your headline result.

- [ ] For each backtest month, convert the forecast to required seats: `S_req = P̂ / L*`
- [ ] Compute surplus: `max(0, S_sched − P_actual / L*)`
- [ ] Compute shortfall: `max(0, P_actual / L* − S_sched)`
- [ ] Compute `CMR = Σ(surplus + shortfall) / Σ S_sched`, for both the model and the baseline
- [ ] Repeat at all three L\* values — report as a sensitivity band, not a point estimate
- [ ] Convert the seat difference into monthly frequencies using average seats per departure per route
- [ ] Flag which portion of the shortfall falls in censored route-months, and note that these figures are conservative

- [ ] **Write the headline sentence with real numbers in it:**

> Over the backtest, a model-driven schedule would have produced a Capacity Misallocation Rate of ___%, versus ___% under the seasonal-naive baseline — a relative reduction of ___%, equivalent to ___ seat-months placed where demand actually was.

- [ ] State explicitly in the notebook that the comparison is against a naive rule, **not** against Korean Air's actual schedule

**Done when** that sentence is complete and reproducible from a script.

**If CMR improves by less than 20%:** report it. Analyse which routes drive the gap. "Accuracy improved in months where capacity was already correct" is a legitimate and interesting finding, and the scope permits it.

---

### Day 10 — Segmented error analysis

- [ ] Break error down by route, by season, by regime, and by censored versus uncensored
- [ ] Identify the worst-performing segments and diagnose why
- [ ] Translate this into override guidance: in which situations should a planner not trust the model?
- [ ] Save the error table to `outputs/tables/`

**Done when** you can name the model's failure modes per route without looking them up.

---

## PHASE 5 — COMMUNICATION (Days 11–13)

### Day 11 — Decision tool · TIMEBOXED, 6 HOURS, HARD STOP

- [ ] Streamlit app: select route and horizon → show forecast with interval, seats required, seats scheduled, recommended frequency change
- [ ] Include the L\* sensitivity toggle
- [ ] **At the 6-hour mark, stop regardless of state.** A static notebook is an acceptable substitute for this deliverable. The deck and README are not substitutable.

---

### Day 12 — Executive deck (5 slides)

1. The decision — how many flights to schedule on a route next month, and why it's expensive to get wrong
2. Data — what exists, what doesn't, the six-month lag
3. Approach — one slide, no architecture diagram
4. **Result — the CMR sentence, in seats**
5. Limitations and next step

- [ ] No model architecture. No jargon. If a slide needs a technical term, cut the slide
- [ ] **Include the explicit note that this is capacity and frequency planning, not departure-time scheduling** — the data is monthly and cannot support timetable claims

---

### Day 13 — README and limitations memo

- [ ] `README.md` for a non-technical reader: problem → approach → result → limitations → how to reproduce
- [ ] `docs/LIMITATIONS.md` (deliverable D7), covering all six:
  - Six-month T-100 confidentiality lag and the as-of date
  - Capacity censoring — passengers carried ≠ demand, shortfall figures conservative
  - Disruption regime excluded from training, and the cutoff choice
  - No fare data available; three sources tried and why each failed
  - Asiana merger structural break and its handling
  - Monthly granularity caps the decision at frequency, not timetable

- [ ] For each limitation, state what would be needed to resolve it

**Done when** a non-analyst can read the README end to end and explain what you built.

---

## DAY 14 — BUFFER AND REHEARSAL

- [ ] Clone the repo to a fresh directory and run the full pipeline. Fix whatever breaks
- [ ] Verify every figure and table in the deck regenerates from a script
- [ ] Rehearse the 90-second verbal version aloud, without notes:
  > *The decision, the data problem, the result in seats, the main limitation.*
- [ ] Prepare answers to the four predictable questions:
  - What would you do differently?
  - Where could this be wrong?
  - Why not just use the airline's own data?
  - How do you know the model is actually useful rather than just accurate?

This day exists because Days 1–13 will slip somewhere. If they don't, spend it strengthening `LIMITATIONS.md`.

---

## Contingency

**Cut order under time pressure:**

1. Competitor SHAP attribution (objective O2)
2. Streamlit app (D5) → static notebook
3. Depth of Day 10 segmented analysis
4. Fifth route

**Never cut:** the deck (D6), the README, the limitations memo (D7), or the CMR counterfactual (D4). A model nobody understands scores nothing in an admissions interview.

**If you fall two days behind:** drop to three routes and re-run from Day 6. The pipeline is route-agnostic, so this costs hours rather than days.
