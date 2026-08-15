# Project Scope Statement

**Project title:** Route-Level Demand Forecasting for Transpacific Capacity Planning — Korean Air

**Version:** 2.0 · **Duration:** 14 calendar days · **Effort assumption:** ~4 hrs/day (~50 hrs total)

**Change from v1.0:** Fare prediction and revenue estimation removed from scope. The project now forecasts demand and converts it into a capacity recommendation measured in seats. All fare-data dependencies (SerpApi, Travelpayouts, published yield) are eliminated.

---

## 1. Business context

A widebody aircraft assigned to ICN–LAX is committed for roughly 24 hours per rotation. Network planners decide months in advance how many frequencies to operate on each route, and that decision is expensive in both directions.

Deploy too many seats and the aircraft flies partly empty — the cost is incurred whether or not the seat is sold. Deploy too few and demand is turned away to a competitor on the same city pair, which costs both the immediate passenger and, on business routes, the traveller's future loyalty.

Planners work to a **target load factor**: a utilisation level that balances the two errors. The operational question is not "how many people will fly?" but "given expected demand, is our current schedule carrying the right number of seats?"

**Problem statement.** Korean Air does not publish route-level demand data. Public sources exist but are split across US and Korean regulators, arrive with a six-month lag, and are reported in two languages under different conventions. This project assembles them into a route-level monthly demand forecast, converts that forecast into a frequency recommendation against a load-factor target, and measures the value of doing so in seats correctly deployed rather than model accuracy.

---

## 2. The decision this project supports

> **For each route and each future month: how many flights should be scheduled?**

The recommendation chain is deliberately short, so every step is auditable:

1. Forecast passengers for route *r*, month *m* → **P̂**
2. Divide by the target load factor **L\*** → seats required, **S_req = P̂ / L\***
3. Compare to seats currently scheduled, **S_sched**
4. Convert the gap to frequencies using average seats per departure on that route
5. Recommend an increase, a decrease, or no change

**L\* must be derived, not invented.** Compute it from Korean Air's own achieved network passenger load factor over the recovery period, or from the route's own historical achieved level. Document the derivation and the value. A target picked because it sounded plausible is the kind of assumption that unravels under a single interview question.

---

## 3. Decision metric and success outcome

### 3.1 Why not forecast accuracy

WAPE measures whether the model is right. It does not measure whether being right was worth anything. A model can improve WAPE by 20% on routes whose capacity was already correct, and change no decision at all. The metric below counts only errors that would have moved a schedule.

### 3.2 Primary decision metric — Capacity Misallocation Rate (CMR)

For each route-month, seats are misallocated in one of two directions:

**Surplus seats** — capacity deployed beyond what demand needed:

    surplus = max(0, S_sched − P_actual / L*)

**Shortfall seats** — capacity below what demand needed, indicating turned-away passengers:

    shortfall = max(0, P_actual / L* − S_sched)

**Capacity Misallocation Rate:**

    CMR = Σ (surplus + shortfall) / Σ S_sched

expressed as a percentage of deployed seats. Lower is better. It is directionally symmetric, denominated in seats, and computable entirely from T-100 — no price data, no assumed cost per seat, no invented dollar figure.

### 3.3 Success outcome — a backtested counterfactual

The headline result is **not** "the model achieved X% error." It is:

> Over a 24-month rolling backtest across five routes, a schedule driven by the model's forecasts would have produced a Capacity Misallocation Rate of **A%**, versus **B%** under the seasonal-naive baseline — a relative reduction of **C%**, equivalent to **N seat-months** placed where demand actually was.

This is a counterfactual, so it must be constructed honestly:

- Forecasts come only from data available at the time of each forecast — the rolling-origin backtest already enforces this
- The baseline is the seasonal-naive schedule, not the schedule Korean Air actually flew. **You cannot claim to beat Korean Air.** They hold booking data, corporate contracts, and connecting-traffic information you do not. State this explicitly.
- The claim is about a decision rule, not about the airline's competence

### 3.4 Acceptance thresholds

| Gate | Threshold | Status |
|---|---|---|
| Statistical | ≥15% WAPE improvement over seasonal naive, rolling-origin backtest | Mandatory |
| Decision | ≥20% relative reduction in CMR versus the baseline schedule rule | Mandatory |
| Coverage | Model beats baseline on at least 4 of 5 routes | Mandatory |
| Communication | A non-analyst reads the README and understands what was built, what it found, and what it can't do | Mandatory |

If the statistical gate passes but the decision gate fails, that is a genuine and reportable finding: accuracy improved in months where capacity was already correct. Report it rather than hiding it — "my model got better without mattering, and here's why" demonstrates more judgment than a passing number.

---

## 4. Objectives

| # | Objective | Measure |
|---|---|---|
| O1 | Forecast monthly revenue passengers per route, 3 months ahead | ≥15% WAPE improvement over seasonal naive |
| O2 | Quantify competitive capacity effects on Korean Air demand | Competitor-seat features carry non-trivial SHAP contribution, with economically sensible direction |
| O3 | Convert forecasts into frequency recommendations | Recommendation issued per route-month in flights and seats |
| O4 | Demonstrate decision value | ≥20% CMR reduction versus baseline |
| O5 | Communicate to a non-technical audience | 5-slide deck plus plain-language README |

O1, O3, O4, O5 are mandatory. O2 is cut first if the schedule slips.

---

## 5. Scope boundaries

### In scope

**Carrier:** Korean Air (KE).

**Competitors** (features only, not forecast targets): Asiana (OZ), Delta (DL), United (UA), American (AA), Air Premia (YP) where present.

**Routes — modelled (5):** ICN–LAX, ICN–JFK, ICN–SFO, ICN–SEA, ICN–ATL.

**Route — qualitative case study only (1):** ICN–YYZ. Absent from US DOT data. Retained as a narrative device and as a demonstration of data-coverage boundaries.

**Time window:** 2015-01 through latest available T-100 release, with the disruption period excluded from training (see §7).

**Target:** monthly revenue passengers per carrier × route, **modelled in logs** (see §7).

**Output:** frequency recommendation per route-month, against a derived load-factor target.

### Out of scope — with reasons

| Excluded | Why |
|---|---|
| Ticket price prediction | No accessible fare data source. Amadeus self-service closed July 2026; Kiwi closed to new developers; Travelpayouts requires affiliate qualification. Scraped market fares would not represent the carrier's realised fares in any case. |
| Revenue or profit estimation | Follows from the above. Any dollar figure would rest on an assumed cost per seat, which is the weakest possible link in a recommendation chain. |
| Price elasticity | Requires both price data and an instrument. Neither is available. |
| **Time-of-day scheduling** | T-100 is monthly and contains no departure times or day-of-week. The data cannot support timetable decisions — only frequency and capacity. **This distinction must be stated in the deck**; conflating the two is the most likely place an aviation-literate interviewer catches the project out. |
| Fleet assignment / aircraft type optimisation | Requires fleet availability and maintenance constraints not in scope |
| Cathay Pacific | Publishes network-level traffic only; cannot support route-level decisions |
| Cargo | Different business, different drivers |
| Korean domestic routes | LCC-dominated competitive structure; dilutes the narrative |
| Real-time deployment | Portfolio artifact, not a system |
| Any claim to outperform Korean Air's actual planning | They hold booking, corporate-contract, and connecting-traffic data not available here. The comparison is against a naive rule only. |

---

## 6. Data sources

| Source | What it provides | Granularity | Cost | Key risk |
|---|---|---|---|---|
| **US DOT BTS T-100 International Segment (28IS)**<br>[Download tables](https://www.transtats.bts.gov/Tables.asp?DB_ID=111) · [DB overview](https://www.transtats.bts.gov/DatabaseInfo.asp?QO_VQ=EEE) · [28IS description](https://www.bts.dot.gov/topics/airlines-and-airports/data-bank-28is-t-100-and-t-100f-international-segment-data-us-and) | Passengers, seats, departures, load factor, aircraft type, for foreign carriers serving the US | Carrier × route × month × aircraft type | Free | Six-month confidentiality lag; forecast "as-of" date is data-end, not today |
| **MOLIT air statistics via data.go.kr**<br>[By airline](https://www.data.go.kr/data/15049013/fileData.do) · [By airport](https://www.data.go.kr/data/15092537/fileData.do) | Supplied seats, flights, passengers, cargo by airline (KAL named) | Airline × month | Free | Korean-language field names; 12-month export cap — loop by calendar year |
| **Korea Airports Corporation**<br>[Intl route stats](https://www.airport.co.kr/www/cms/frFlightStatsCon/internationalLineStats.do?MENU_ID=1250) | International route-level and airline-level statistics | Route × month | Free | **Does not cover Incheon** — IIAC reports separately |
| **Incheon International Airport Corporation**<br>[Air traffic statistics (EN)](https://www.airport.kr/co/en/cpr/statisticOfLocalAirport.do) | ICN traffic statistics | Route/airline × month | Free | Separate portal and format |
| **EIA jet fuel spot price**<br>[EIA monthly](https://www.eia.gov/dnav/pet/hist/eer_epjk_pf4_rgc_dpgM.htm) · [FRED `MJFUELUSGULF`](https://fred.stlouisfed.org/data/MJFUELUSGULF) | Cost driver influencing capacity decisions | Monthly | Free | Spot ≠ airline's booked fuel cost; directional signal only |
| **FRED**<br>[fred.stlouisfed.org](https://fred.stlouisfed.org) — search "Korea / U.S. Foreign Exchange Rate" | KRW–USD exchange rate | Daily | Free | Aggregate to monthly mean |
| **Holiday calendars** — Korean lunar (Seollal, Chuseok), US federal | Demand-shifting calendar events | Daily | Free (`holidays`, `korean-lunar-calendar`) | Lunar holidays drift across Gregorian months — genuine feature-engineering work |

**Primary source of truth:** BTS T-100. Korean sources are for cross-validation only — pull 2022–2026, not full history. A discrepancy found and explained is a finding worth a slide.

**Provenance requirement.** BTS accepts amended filings and exports always reflect the latest filed version, with no revision flag. Record the resolved URL, download date, and file checksum for every extract in `data/SOURCES.md`.

---

## 7. Modelling decisions fixed in advance

Recording these in scope prevents them from becoming mid-project improvisation.

**Three regimes, one excluded:**

| Regime | Window | Use |
|---|---|---|
| Pre-pandemic | 2015-01 → 2020-02 | Train |
| Disruption | 2020-03 → ~2022-06 | Excluded from training; retained for plots |
| Recovery | ~2022-07 → data end | Train |

The recovery boundary is provisional. **Verify it against the data**: plot ICN–LAX monthly passengers and select the month where the series rejoins a stable trend. Choosing the cutoff from the data, and saying so, is stronger than citing a policy date.

**Model log(passengers), not passengers.** Pre- and post-disruption levels differ substantially. On the raw scale a regime term must absorb a large additive shift that differs by route; on the log scale it becomes a clean intercept and seasonality becomes multiplicative — which is how airline demand behaves.

**Demand is censored by capacity.** T-100 reports passengers *carried*, not passengers who *wanted* to fly. When a route runs near capacity, observed passengers are truncated at the seat count and true demand was higher. Flag route-months with load factor above roughly 90% as censored, and note in the limitations memo that CMR shortfall figures are therefore conservative — real turned-away demand exceeds what the data can show. This is a genuine subtlety and few portfolio projects surface it.

**The Asiana acquisition falls inside the modelling window.** After the merger, OZ is no longer an independent competitor on ICN–US routes, so competitor and concentration features measure something that stopped existing. Handle it by either combining KE+OZ from the merger onward or adding a merger indicator. Locate the break by plotting combined KE+OZ seats and finding the level shift, then confirm the date. Clean fallback if it proves messy: define competitors as US carriers only.

---

## 8. Deliverables

| ID | Deliverable | Acceptance criteria |
|---|---|---|
| D1 | GitHub repository | Reproducible from clean clone. README written for a non-technical reader. |
| D2 | Data pipeline | Scripted ingest → Parquet → DuckDB. Schema and provenance documented. |
| D3 | Demand forecast model + backtest report | Rolling-origin, time-ordered splits only. Per-route error table. Baseline comparison. |
| D4 | **Capacity decision layer** | CMR computed for model and baseline across the backtest. Per-route frequency recommendations with uncertainty bands. |
| D5 | Decision tool | Streamlit app: select route and horizon → forecast, interval, seats required, recommended frequency change. Static notebook acceptable as fallback. |
| D6 | Executive deck (5 slides) | Business question / data / method / **CMR result in seats** / next step. No architecture diagrams. |
| D7 | Limitations & roadmap memo (1 page) | Covers the six-month lag, capacity censoring, the excluded disruption regime, the absence of fare data, the Asiana structural break, and the monthly-granularity limit on scheduling claims. |

D7 is a primary deliverable, not an appendix. Most portfolio projects arrive with clean handed-over data and no account of what was unavailable. This one hit three dead data sources and documented the workaround — that is the differentiating asset.

---

## 9. Assumptions

1. T-100 international covers KE continuously from 2015 with no undocumented gaps.
2. A defensible target load factor can be derived from Korean Air's published network figures.
3. Korean-language portals are navigable via browser translation; field names mapped once into a documented dictionary.
4. ~4 focused hours per day including weekends.
5. Data volume fits comfortably on a local machine.

---

## 10. Constraints

- **Hard 14-day deadline.** Schedule fixed; scope absorbs variance.
- **No paid data.** Free sources only.
- **Six-month T-100 lag is immovable.** The forecast is anchored to the data-end date and labelled as such.
- **Monthly granularity caps the decision.** Frequency and capacity only — never departure times.

---

## 11. Risks

| Risk | Likelihood | Impact | Response |
|---|---|---|---|
| CMR improves less than 20% despite good WAPE | Medium | Medium | Report it as a finding: accuracy improved where capacity was already correct. Analyse which routes drive the gap. This is a legitimate result, not a failure. |
| Load-factor target proves hard to justify | Medium | Medium | Run CMR at three target levels as a sensitivity band rather than a single figure |
| Capacity censoring distorts high-load routes | High | Medium | Flag censored route-months; state that shortfall estimates are conservative |
| Asiana merger contaminates competitor features | High | Medium | Fall back to US-carriers-only competitor definition |
| A route has too few observations post-cleaning | Medium | Medium | Drop it. Four well-modelled routes beat five with one forced. |
| Streamlit app consumes the final days | Medium | High | Timeboxed to 6 hours. Static notebook is acceptable. Communication outranks the app. |
| Scope creep back toward revenue | Medium | High | Explicitly out of scope. If tempted, write it into D7 as future work. |

---

## 12. Schedule

### Phase 1 — Foundation (Days 1–3)

| Day | Work | Done when |
|---|---|---|
| 1 | Initialise repo, environment, DuckDB. Download T-100 international by year. | KE monthly passengers by route queryable, 2015 → present |
| 2 | Pull Korean sources (2022–2026, looped by calendar year). Cross-validate against T-100. | Discrepancy between sources quantified and explained |
| 3 | Pull fuel, FX, holiday calendars. Derive and document the target load factor L\*. | `SOURCES.md` complete with checksums; L\* derivation written up |

**Gate:** if clean route-level demand data does not exist by end of Day 3, cut to 3 routes and proceed.

### Phase 2 — Analysis (Days 4–5)

| Day | Work | Done when |
|---|---|---|
| 4 | EDA: seasonality by route, regime break, competitor capacity, load-factor distribution. Identify censored route-months. Locate the Asiana structural break. | Five charts that would survive an executive audience; recovery cutoff chosen from the data |
| 5 | Feature engineering: lags, rolling stats, competitor seats, route HHI, lunar holiday flags, fuel, FX. Log transform applied. | Modelling table built; leakage audit written down |

### Phase 3 — Modelling (Days 6–8)

| Day | Work | Done when |
|---|---|---|
| 6 | Baselines and rolling-origin backtest harness. | Baseline WAPE **and baseline CMR** recorded per route |
| 7 | Global LightGBM across carrier × route, time-ordered CV. | Model beats baseline, or the reason it doesn't is understood |
| 8 | Tuning, quantile outputs for intervals, SHAP. | Intervals produced; feature attributions economically sensible |

### Phase 4 — Decision (Days 9–10)

| Day | Work | Done when |
|---|---|---|
| 9 | Build the CMR counterfactual. Compute for model and baseline across the backtest. Sensitivity across three L\* values. | The headline sentence exists with real numbers in it |
| 10 | Segmented error analysis: which routes, seasons, and regimes fail, and what that implies for when a planner should override the model. | Failure modes named per route |

### Phase 5 — Communication (Days 11–13)

| Day | Work | Done when |
|---|---|---|
| 11 | Streamlit decision tool. **Timeboxed — 6 hours, hard stop.** | App runs locally, or fallback notebook finalised |
| 12 | Executive deck (D6). | 5 slides, no jargon, result stated in seats |
| 13 | README (D1) and limitations memo (D7). | A non-analyst can follow the README end to end |

### Day 14 — Buffer and rehearsal

Reproducibility check from a clean clone. Rehearse the 90-second verbal version. This day exists because Days 1–13 will slip somewhere; if they don't, use it to strengthen D7.

**Cut order under pressure:** O2 (competitor attribution) → D5 (app) → depth of Day 10. Never D6 or D7.

---

## 13. Definition of done

A reader who has never seen the project can, in under ten minutes:

1. State the decision it supports — how many flights to schedule on a route next month
2. See that the model beats a stated baseline on a time-honest backtest
3. Read a specific recommendation in flights and seats, with an uncertainty band
4. Understand the value in seats correctly deployed, not in model error
5. Find a clear account of what the data could not support

Model accuracy alone does not meet this bar. Neither does a decision claim without a backtest behind it.

---

## 14. Phase 2 (not committed)

Recorded so the 14-day scope reads as a deliberate first increment:

- Fare and revenue modelling, if a data source becomes accessible
- Weekly or daily granularity via a schedule data source, enabling actual timetable decisions
- Explicit censored-demand modelling (Tobit or a spill-adjusted target) rather than flagging
- Cathay Pacific as a comparative case on HKG–US routes visible in T-100
- Hierarchical reconciliation from route forecasts to network totals
