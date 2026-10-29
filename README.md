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
