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
  * The migration to Apple Silicon **`macos-26`** in October 2026 triggered a sharp recurrence of queue timeouts (176 failures; 44.5% of all runner-starvation events in project history).

---

## 📈 Visualizations

### 1. 24-Hour Diurnal Congestion Curve (UTC)
![Diurnal Curve](./assets/diurnal_curve.svg)

### 2. Historical Timeline & Outages (2024–2026)
![Historical Timeline](./assets/timeline.svg)

### 3. Population Outcome Distribution
![Outcome Distribution](./assets/outcomes_donut.svg)

### 4. Day-of-Week Comparison
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
├── index.html                     # Full interactive HTML report
├── README.md                      # Overview and summary
├── assets/
│   ├── diurnal_curve.svg          # 24-hour UTC activity and failure rate curve
│   ├── timeline.svg               # Monthly executions vs runner starvations
│   ├── outcomes_donut.svg         # Outcome breakdown (41,410 runs)
│   └── day_of_week.svg            # Day-of-week failure rate comparison
└── data/
    ├── summary_metrics.json       # Population-level summary counts
    ├── hourly_breakdown.csv       # Hourly UTC aggregations
    ├── day_of_week_breakdown.csv  # Day-of-week aggregations
    ├── monthly_timeline.csv       # Month-by-month history
    └── failure_classifications.csv# Breakdown of all 14,269 failure causes
```

---

## 🚀 View the Full HTML Report

Open `index.html` in any browser or enable **GitHub Pages** (Settings > Pages > Branch: `main` / `root`) to view the interactive web report.
