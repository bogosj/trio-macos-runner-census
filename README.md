# macOS Runner Starvation in GitHub Actions: `nightscout/Trio` CI Census

An empirical study and population census analyzing **41,410 GitHub Actions workflow runs** across all **2,437 public forks** of [`nightscout/Trio`](https://github.com/nightscout/Trio) from September 2024 to late October 2026.

This project investigates the availability, queue contention, and time-of-day failure patterns of GitHub's cloud-hosted macOS runner fleet (`macos-14`, `macos-15`, and `macos-26`).

---

## 📊 Key Findings

* **Full Population:** 2,437 repositories indexed; 41,410 total workflow runs evaluated.
* **Confirmed Runner Starvations:** **395 runs** failed or timed out due to macOS host unavailability (`runner_id: 0`, unacquired runner annotations, or capacity exhaustion notices).
* **Diurnal Congestion Peak (14:00 – 17:00 UTC / 10:00 AM – 1:00 PM EDT):**
  * Failure rate of manual builds peaks at **5.2% – 6.2%** during global developer business hours overlap.
  * Over 63% of all manual runner-lack failures occur in the 14:00 – 20:00 UTC window.
* **Safe Window (22:00 – 11:00 UTC):**
  * Late US evening through European morning sees failure rates plummet to **< 1%** (0.3% at 03:00 and 23:00 UTC).
* **The Sunday Inoculation:**
  * Sunday hosts **73.5% of all executions (30,448 runs)** due to automated weekly crons.
  * However, Sunday experiences the lowest failure rate across the entire week (**0.25%**) because `build_trio.yml` executes pre-flight checks on `ubuntu-latest` and cancels early before ever requesting a macOS runner.
* **Longitudinal Inflection (October 2026):**
  * Global capacity strain on GitHub's shared Apple Silicon **`macos-26`** (arm64) runner fleet in October 2026 caused a sharp surge in queue timeouts (176 failures; 44.5% of all runner-starvation events in project history).
* **Recent 4-Week Crisis vs. Prior 4-Week Baseline:**
  * Comparing the **Recent 4-Week Window (Oct 1 – Oct 28)** against the **Prior 4-Week Baseline (Sep 3 – Sep 30)** reveals an acute **+551.9% surge in runner starvation failures** (jumping from 27 to 176).
  * Manual build failure rate jumped **8.0x** (from 0.92% to 7.39%).
  * During peak hours (14:00 – 16:00 UTC), failure rates exploded from ~1% to **18.4% – 21.9%** (over 1 in 5 builds failing).

---

## 🔍 Comparative Window Analysis (Recent 4 Weeks vs. Prior 4 Weeks)

### Identification of the 4-Week Optimal Window

To identify the optimal comparison window, we evaluated candidate spans of 4, 5, and 6 weeks against the weekly progression of failures:

* **Why 4 Weeks (28 Days) is the Optimal Boundary:** Throughout September 2026 (Weeks 8–5), runner failure rates remained at a stable background baseline of 0.5%–1.3% (averaging 0.92%). Starting October 1 (Week 4), failure rates climbed progressively, culminating in a critical surge in **Weeks 2 and 1 (15.63% and 12.78%)**.
* Isolating **October 1 to October 28 (Recent 4 Weeks)** against **September 3 to September 30 (Prior 4 Weeks)** captures the exact phase transition from stability to crisis. Expanding the window to 5 or 6 weeks blends quiescent September weeks into the recent period, diluting the measured escalation from +552% down to +394%.

### Weekly Failure Progression (Last 8 Weeks)

| Week | Date Range | Total Runs | Manual Dispatches | Runner Starvations | Failure Rate (%) | Operational Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **W-08** | 2026-09-03 to 2026-09-09 | 1,755 | 361 | 4 | 1.11% | Baseline |
| **W-07** | 2026-09-10 to 2026-09-16 | 2,204 | 1,188 | 16 | 1.35% | Baseline |
| **W-06** | 2026-09-17 to 2026-09-23 | 2,262 | 1,014 | 5 | 0.49% | Baseline |
| **W-05** | 2026-09-24 to 2026-09-30 | 1,736 | 384 | 2 | 0.52% | Baseline |
| **W-04** | 2026-10-01 to 2026-10-07 | 1,960 | 545 | 7 | 1.28% | Baseline |
| **W-03** | 2026-10-08 to 2026-10-14 | 1,836 | 753 | 17 | 2.26% | Elevated |
| **W-02** | 2026-10-15 to 2026-10-21 | 662 | 499 | **78** | **15.63%** | Critical Surge |
| **W-01** | 2026-10-22 to 2026-10-28 | 865 | 571 | **74** | **12.78%** | Critical Surge |

### Peak Hour Escalation (14:00 – 17:00 UTC)

| Hour (UTC) | Prior 4W Rate | Recent 4W Rate | Shift / Escalation |
| :--- | :--- | :--- | :--- |
| **14:00** | 0.0% | **18.4%** | From 0 failures to 1 in 5.4 builds failing |
| **15:00** | 1.3% | **21.9%** | **16.8x surge (1 in 4.5 builds fail)** |
| **16:00** | 0.0% | **20.0%** | From 0 failures to 1 in 5 builds failing |
| **17:00** | 1.8% | **12.3%** | 6.8x surge |

---

## 📈 Visualizations

### 1. 24-Hour Diurnal Congestion Curve (UTC)
![Diurnal Curve](./assets/diurnal_curve.svg)

### 2. Recent 4 Weeks vs. Prior 4 Weeks Hourly Comparison
![Hourly Comparison Recent vs Prior](./assets/recent_vs_prior_4w_hourly.svg)

### 3. 8-Week Progression of Runner Starvation
![Weekly Progression](./assets/weekly_progression_8w.svg)

### 4. Historical Timeline & Outages (2024–2026)
![Historical Timeline](./assets/timeline.svg)

### 5. Population Outcome Distribution
![Outcome Distribution](./assets/outcomes_donut.svg)

### 6. Day-of-Week Comparison
![Day of Week Comparison](./assets/day_of_week.svg)

---

## 🔬 Research Methodology & Collection Architecture

Conducting a complete census across thousands of repositories requires balancing deep inspection against GitHub API rate limits and secondary abuse protections.

```
Total Fork Population:                     2,437 repositories (100% indexed)
Total Build Trio Workflow Runs:           41,410 executions
Total Failures / Cancellations Inspected:  14,269 runs (100% deep-inspected)
Total Confirmed macOS Runner Starvations:    395 runs
Overall Build Success Rate:                 65.5% (27,117 successful builds)
```

### 1. Two-Stage Research Pipeline

* **Stage 1 (Pilot Validation):** An initial sample of 400 public forks (2,740 workflow runs) was evaluated to test endpoints, map data structures, and establish deterministic diagnostic heuristics for runner allocation failures (identifying unassigned `runner_id: 0` metadata and check-run annotations).
* **Stage 2 (Complete Population Census):** Scaled across all 25 pages of public forks of `nightscout/Trio` (2,437 forks total), cataloging all 41,410 runs and deep-inspecting every non-successful execution.

### 2. Collection Tooling & Persistent Storage

* **Standard Library Tooling:** Built using zero-external-dependency Python (`urllib.request`, `concurrent.futures`, `threading`, `sqlite3`, `queue`) leveraging the GitHub REST API v3 authenticated via GitHub CLI token (`gh auth token`).
* **Transactional Crash Resilience:** All data was persisted in a local SQLite database (`census_trio.db`) with Write-Ahead Logging (`PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`). Every inspected run was committed immediately, enabling atomic checkpoints and seamless crash recovery.
* **Smart Priority Queue:** When inspecting failures, runs were prioritized by event type: manual user builds (`workflow_dispatch`) and runs with queuing delays (`queue_duration_mins > 0`) were inspected first, surfacing critical capacity drops before batch scheduled skips.

### 3. Throttling, Pacing & Rate Limit Management

GitHub enforces a strict primary ceiling of **5,000 authenticated requests per rolling hour**, alongside secondary rate limits that penalize burst traffic or excessive concurrent connections. To operate continuously without risk of 403 or 429 lockouts, we used a two-tier throttling architecture:

| Collector Phase | Concurrency | Pacing / Delay | Sustained Throughput | % of Hourly Quota | Operational Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Phase 1: 12-Hour Smear Daemon** (`census_collector.py`) | 1 Worker (Single-Threaded) | 4.2s sleep ± 0.4s randomized jitter | ~830 – 850 req / hr | ~16.8% | Gentle overnight execution: indexed all 2,437 forks, captured all 41,410 runs, and inspected the initial 5,910 failures. Random jitter prevented periodic signature triggers. |
| **Phase 2: Accelerated Collector** (`fast_census_collector.py`) | 8 Workers (Thread Pool) | Token-Bucket Limiter (0.95s min aggregate delay) | ~3,600 – 3,780 req / hr | ~75.0% | High-throughput accelerated inspection of the remaining 8,358 failures across 2 rolling rate windows, staying well below the 5,000/hr cap. |

* **The Dynamic Rate Guardian:** Monitored `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers on every response. If the remaining quota dipped below 80 calls in any rolling hour, all worker threads paused automatically until `X-RateLimit-Reset + 5.0s`. Exponential backoff was integrated to handle transient 403/429 responses.
* **Total API Volume:** Executed over **16,700 API calls** across the study with zero rate limit bans, 403 lockouts, or dropped connections.

### 4. Diagnostic Criteria for Runner Starvation

A workflow run was classified as a **macOS Runner Starvation** if and only if:
1. A job targeted a macOS runner label (`macos-26`, `macos-15`, `macos-14`, `xcode-27`) and completed with conclusion `cancelled`, `failure`, or `timed_out`; AND
2. `runner_id == 0` or `runner_name == ""` with an empty step execution array (`steps: []`), indicating no virtual machine host was ever assigned; OR
3. Check-run annotations explicitly contained either:
   * `"The job was not acquired by Runner of type hosted even after multiple attempts"`
   * `"Due to capacity constraints, jobs targeting macOS arm64 runners may experience longer queue times."`
4. Or the job failed at step `Set up job` due to host provisioning dropouts.

*Early-Exit Filtering for No-Op Scheduled Skips:* If job `Cancel run when there is nothing to build` had conclusion `cancelled` and the subsequent `Build` job was `skipped`, the run was classified as a normal scheduled skip (not a failure).

---

## 🔒 Privacy & PII Redaction

In accordance with privacy standards:
* **All personal identifiers have been completely stripped:** zero personal usernames, GitHub accounts, personal fork URLs, or email addresses appear in this repository.
* All data is provided in aggregated form by temporal bucket (hour, day, month) and failure classification.

---

## 📁 Repository Structure

```
├── index.html                                  # Full interactive HTML report
├── README.md                                   # Overview, findings, and methodology
├── assets/
│   ├── diurnal_curve.svg                       # 24-hour UTC activity and failure rate curve
│   ├── recent_vs_prior_4w_hourly.svg           # Peak congestion escalation comparison
│   ├── weekly_progression_8w.svg               # 8-week failure progression & boundary
│   ├── timeline.svg                            # Monthly executions vs runner starvations
│   ├── outcomes_donut.svg                      # Outcome breakdown (41,410 runs)
│   └── day_of_week.svg                         # Day-of-week failure rate comparison
├── data/
│   ├── summary_metrics.json                    # Population-level summary counts
│   ├── window_comparison_4w.json               # Recent 4W vs Prior 4W metrics & deltas
│   ├── weekly_progression_8w.csv               # Week-by-week failure counts & rates
│   ├── hourly_comparison_recent_vs_prior.csv   # Hourly comparison data
│   ├── hourly_breakdown.csv                    # Full 24-hour UTC aggregations
│   ├── day_of_week_breakdown.csv               # Day-of-week aggregations
│   ├── monthly_timeline.csv                    # Month-by-month history
│   └── failure_classifications.csv             # Breakdown of all 14,269 failure causes
└── scripts/
    ├── build_report_and_data.py                # Pipeline generator for full census data
    └── generate_window_comparison.py           # Window comparison analysis generator
```

---

## 🚀 View the Full HTML Report

Open `index.html` in any browser or enable **GitHub Pages** (Settings > Pages > Branch: `main` / `root`) to view the interactive web report.
