import sqlite3
import csv
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

REPO_DIR = '/home/bogosj/assistant/trio-macos-runner-census'
DATA_DIR = f'{REPO_DIR}/data'
ASSETS_DIR = f'{REPO_DIR}/assets'
DB_PATH = '/home/bogosj/.gemini/antigravity-cli/brain/9fbfc48c-71e4-42b4-8fd1-9a2d2e61d208/census_trio.db'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

end_date = datetime(2026, 10, 28)

# ---------------------------------------------------------------------------
# 1. 8-WEEK PROGRESSION DATA
# ---------------------------------------------------------------------------
weekly_data = []
for i in range(8, 0, -1):
    w_end = end_date - timedelta(days=(i-1)*7)
    w_start = w_end - timedelta(days=6)
    
    cur.execute('''
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN event='workflow_dispatch' THEN 1 ELSE 0 END) as dispatch,
        SUM(CASE WHEN is_runner_lack=1 THEN 1 ELSE 0 END) as lack_total,
        SUM(CASE WHEN is_runner_lack=1 AND event='workflow_dispatch' THEN 1 ELSE 0 END) as lack_disp
    FROM workflow_runs
    WHERE DATE(created_at) BETWEEN ? AND ?
    ''', (w_start.strftime('%Y-%m-%d'), w_end.strftime('%Y-%m-%d')))
    r = cur.fetchone()
    pct = round((r[3]/r[1]*100) if r[1] else 0, 2)
    status = 'Baseline' if pct < 2.0 else ('Elevated' if pct < 5.0 else 'Critical Surge')
    
    weekly_data.append({
        'week_index': f'W-{i:02d}',
        'start_date': w_start.strftime('%Y-%m-%d'),
        'end_date': w_end.strftime('%Y-%m-%d'),
        'total_runs': r[0],
        'dispatch_runs': r[1],
        'lack_total': r[2],
        'lack_dispatch': r[3],
        'dispatch_failure_rate_pct': pct,
        'status': status
    })

with open(f'{DATA_DIR}/weekly_progression_8w.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(weekly_data[0].keys()))
    writer.writeheader()
    writer.writerows(weekly_data)

# ---------------------------------------------------------------------------
# 2. 4-WEEK WINDOW COMPARISON
# ---------------------------------------------------------------------------
# Recent 4 weeks: 2026-10-01 to 2026-10-28
# Prior 4 weeks: 2026-09-03 to 2026-09-30

cur.execute('''
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN event='workflow_dispatch' THEN 1 ELSE 0 END) as dispatch,
    SUM(CASE WHEN is_runner_lack=1 THEN 1 ELSE 0 END) as lack_total,
    SUM(CASE WHEN is_runner_lack=1 AND event='workflow_dispatch' THEN 1 ELSE 0 END) as lack_disp
FROM workflow_runs
WHERE DATE(created_at) BETWEEN '2026-10-01' AND '2026-10-28'
''')
r_res = cur.fetchone()

cur.execute('''
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN event='workflow_dispatch' THEN 1 ELSE 0 END) as dispatch,
    SUM(CASE WHEN is_runner_lack=1 THEN 1 ELSE 0 END) as lack_total,
    SUM(CASE WHEN is_runner_lack=1 AND event='workflow_dispatch' THEN 1 ELSE 0 END) as lack_disp
FROM workflow_runs
WHERE DATE(created_at) BETWEEN '2026-09-03' AND '2026-09-30'
''')
p_res = cur.fetchone()

comparison = {
    'window_length_weeks': 4,
    'window_length_days': 28,
    'recent_window': {'start': '2026-10-01', 'end': '2026-10-28'},
    'prior_window': {'start': '2026-09-03', 'end': '2026-09-30'},
    'recent_metrics': {
        'total_runs': r_res[0],
        'dispatch_runs': r_res[1],
        'runner_lack_total': r_res[2],
        'runner_lack_dispatch': r_res[3],
        'overall_failure_rate_pct': round(r_res[2]/r_res[0]*100, 2),
        'dispatch_failure_rate_pct': round(r_res[3]/r_res[1]*100, 2)
    },
    'prior_metrics': {
        'total_runs': p_res[0],
        'dispatch_runs': p_res[1],
        'runner_lack_total': p_res[2],
        'runner_lack_dispatch': p_res[3],
        'overall_failure_rate_pct': round(p_res[2]/p_res[0]*100, 2),
        'dispatch_failure_rate_pct': round(p_res[3]/p_res[1]*100, 2)
    },
    'deltas': {
        'failure_count_growth_pct': round((r_res[2] - p_res[2]) / p_res[2] * 100, 1),
        'failure_rate_multiplier': round((r_res[3]/r_res[1]) / (p_res[3]/p_res[1]), 2)
    }
}

with open(f'{DATA_DIR}/window_comparison_4w.json', 'w') as f:
    json.dump(comparison, f, indent=2)

# ---------------------------------------------------------------------------
# 3. HOURLY COMPARISON DATA
# ---------------------------------------------------------------------------
cur.execute('''
SELECT 
    CAST(strftime('%H', created_at) AS INTEGER) as hr,
    SUM(CASE WHEN DATE(created_at) BETWEEN '2026-09-03' AND '2026-09-30' AND event='workflow_dispatch' THEN 1 ELSE 0 END) as p_disp,
    SUM(CASE WHEN DATE(created_at) BETWEEN '2026-09-03' AND '2026-09-30' AND is_runner_lack=1 AND event='workflow_dispatch' THEN 1 ELSE 0 END) as p_lack,
    SUM(CASE WHEN DATE(created_at) BETWEEN '2026-10-01' AND '2026-10-28' AND event='workflow_dispatch' THEN 1 ELSE 0 END) as r_disp,
    SUM(CASE WHEN DATE(created_at) BETWEEN '2026-10-01' AND '2026-10-28' AND is_runner_lack=1 AND event='workflow_dispatch' THEN 1 ELSE 0 END) as r_lack
FROM workflow_runs
GROUP BY hr
ORDER BY hr
''')
hourly_comp_rows = cur.fetchall()

with open(f'{DATA_DIR}/hourly_comparison_recent_vs_prior.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['hour_utc', 'prior_dispatch_runs', 'prior_lack_runs', 'prior_failure_rate_pct', 'recent_dispatch_runs', 'recent_lack_runs', 'recent_failure_rate_pct'])
    for r in hourly_comp_rows:
        p_pct = round((r[2]/r[1]*100) if r[1] else 0, 2)
        r_pct = round((r[4]/r[3]*100) if r[3] else 0, 2)
        writer.writerow([r[0], r[1], r[2], p_pct, r[3], r[4], r_pct])

conn.close()
print("Exported CSVs and JSON.")

# ---------------------------------------------------------------------------
# 4. GENERATE SVGs
# ---------------------------------------------------------------------------
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

# SVG 5: Weekly Progression (8 Weeks)
labels = [f"{w['week_index']}\n({w['start_date'][5:]})" for w in weekly_data]
rates = [w['dispatch_failure_rate_pct'] for w in weekly_data]
counts = [w['lack_dispatch'] for w in weekly_data]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True, gridspec_kw={'height_ratios': [1, 1.2]})

colors = ['#10b981' if r < 2.0 else ('#f59e0b' if r < 5.0 else '#ef4444') for r in rates]

ax1.bar(labels, counts, color=colors, width=0.55, alpha=0.9)
ax1.set_ylabel('Runner Starvation Count', fontsize=10, fontweight='bold', color='#1e293b')
ax1.set_title('Figure 5: 8-Week Progression of macOS Runner Starvation (Sep 3 – Oct 28, 2026)', fontsize=12, fontweight='bold', pad=10, color='#0f172a')
ax1.grid(True, linestyle='--', alpha=0.5)

for i, (c, r) in enumerate(zip(counts, rates)):
    ax1.annotate(f"{c} failures", (i, c), textcoords="offset points", xytext=(0, 4), ha='center', fontsize=9, fontweight='bold')

ax2.plot(labels, rates, color='#b91c1c', marker='o', linewidth=2.5, markersize=6)
ax2.bar(labels, rates, color=colors, width=0.55, alpha=0.35)
ax2.axhline(2.0, color='#10b981', linestyle='--', linewidth=1.2, label='Baseline Threshold (< 2%)')
ax2.axhline(5.0, color='#ef4444', linestyle='--', linewidth=1.2, label='Critical Surge Threshold (> 5%)')

ax2.set_ylabel('Manual Build Failure Rate (%)', fontsize=10, fontweight='bold', color='#b91c1c')
ax2.set_xlabel('Week Window', fontsize=10, fontweight='bold', color='#1e293b')
ax2.legend(loc='upper left', frameon=True, fontsize=9)
ax2.grid(True, linestyle='--', alpha=0.5)
ax2.set_ylim(0, max(rates) * 1.25)

for i, r in enumerate(rates):
    ax2.annotate(f"{r:.1f}%", (i, r), textcoords="offset points", xytext=(0, 5), ha='center', fontsize=9, fontweight='bold', color='#b91c1c')

# Annotate the inflection boundary
ax2.axvline(3.5, color='#64748b', linestyle=':', linewidth=2)
ax2.annotate('4-Week Boundary (Oct 1)\nPrior Baseline vs Recent Crisis', xy=(3.5, 10), xytext=(2.2, 12),
             arrowprops=dict(facecolor='#475569', shrink=0.05, width=1, headwidth=5),
             fontsize=8.5, fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", fc="#f8fafc", ec="#94a3b8"))

plt.tight_layout()
svg5_path = f'{ASSETS_DIR}/weekly_progression_8w.svg'
plt.savefig(svg5_path, format='svg')
plt.close()
print(f"Generated {svg5_path}")

# SVG 6: Hourly Comparison (Recent 4 Weeks vs Prior 4 Weeks)
hrs = [r[0] for r in hourly_comp_rows]
p_rates = [round((r[2]/r[1]*100) if r[1] else 0, 2) for r in hourly_comp_rows]
r_rates = [round((r[4]/r[3]*100) if r[3] else 0, 2) for r in hourly_comp_rows]

fig, ax = plt.subplots(figsize=(11, 5.5))
w = 0.38
x = np.arange(len(hrs))

ax.bar(x - w/2, p_rates, width=w, label='Prior 4 Weeks (Sep 3 – Sep 30): Baseline Avg 0.92%', color='#94a3b8', alpha=0.85)
ax.bar(x + w/2, r_rates, width=w, label='Recent 4 Weeks (Oct 1 – Oct 28): Crisis Avg 7.39%', color='#ef4444', alpha=0.9)

ax.set_ylabel('Failure Rate (% of Manual Runs)', fontsize=10, fontweight='bold', color='#1e293b')
ax.set_xlabel('Hour of the Day (UTC)', fontsize=10, fontweight='bold', color='#1e293b')
ax.set_title('Figure 6: Hourly Failure Rate Comparison — Recent 4 Weeks vs. Prior 4 Weeks Baseline', fontsize=12, fontweight='bold', pad=10, color='#0f172a')
ax.set_xticks(x)
ax.set_xticklabels([f'{h:02d}:00' for h in hrs], rotation=45, ha='right', fontsize=9)
ax.axvspan(13.5, 16.5, color='#fee2e2', alpha=0.45, label='Peak Congestion (14:00 - 16:00 UTC): 18.4% - 21.9%')
ax.legend(loc='upper left', frameon=True, fontsize=9)
ax.grid(True, linestyle='--', alpha=0.5)
ax.set_ylim(0, max(r_rates) * 1.25)

for i, (pr, rr) in enumerate(zip(p_rates, r_rates)):
    if rr >= 10.0:
        ax.annotate(f"{rr:.1f}%", (i + w/2, rr), textcoords="offset points", xytext=(0, 4), ha='center', fontsize=8, fontweight='bold', color='#b91c1c')

plt.tight_layout()
svg6_path = f'{ASSETS_DIR}/recent_vs_prior_4w_hourly.svg'
plt.savefig(svg6_path, format='svg')
plt.close()
print(f"Generated {svg6_path}")
