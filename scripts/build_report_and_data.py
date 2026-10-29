import sqlite3
import json
import csv
import os
import matplotlib.pyplot as plt
import numpy as np

REPO_DIR = '/home/bogosj/assistant/trio-macos-runner-census'
DATA_DIR = f'{REPO_DIR}/data'
ASSETS_DIR = f'{REPO_DIR}/assets'
DB_PATH = '/home/bogosj/.gemini/antigravity-cli/brain/9fbfc48c-71e4-42b4-8fd1-9a2d2e61d208/census_trio.db'

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ---------------------------------------------------------------------------
# 1. EXPORT ANONYMIZED CSVs & JSON
# ---------------------------------------------------------------------------

# Global counts
cur.execute('SELECT COUNT(*) FROM forks')
total_forks = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM workflow_runs')
total_runs = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM workflow_runs WHERE conclusion = "success"')
success_runs = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM workflow_runs WHERE is_runner_lack = 1')
runner_lack_runs = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM workflow_runs WHERE job_inspected = 1')
inspected_runs = cur.fetchone()[0]

summary = {
    'total_forks_indexed': total_forks,
    'total_workflow_runs': total_runs,
    'total_successful_runs': success_runs,
    'success_rate_pct': round(success_runs / total_runs * 100, 2),
    'total_failures_inspected': inspected_runs,
    'total_macos_runner_starvations': runner_lack_runs,
    'runner_starvation_rate_pct': round(runner_lack_runs / total_runs * 100, 2),
    'date_range': {'start': '2024-09-01', 'end': '2026-10-29'}
}

with open(f'{DATA_DIR}/summary_metrics.json', 'w') as f:
    json.dump(summary, f, indent=2)

# Hourly data
cur.execute('''
SELECT 
    CAST(strftime('%H', created_at) AS INTEGER) as hour_utc,
    COUNT(*) as total_runs,
    SUM(CASE WHEN event = 'workflow_dispatch' THEN 1 ELSE 0 END) as dispatch_runs,
    SUM(CASE WHEN event = 'schedule' THEN 1 ELSE 0 END) as schedule_runs,
    SUM(CASE WHEN is_runner_lack = 1 THEN 1 ELSE 0 END) as runner_lack_total,
    SUM(CASE WHEN is_runner_lack = 1 AND event = 'workflow_dispatch' THEN 1 ELSE 0 END) as runner_lack_dispatch
FROM workflow_runs
WHERE created_at IS NOT NULL
GROUP BY hour_utc
ORDER BY hour_utc
''')
hourly_rows = cur.fetchall()

with open(f'{DATA_DIR}/hourly_breakdown.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['hour_utc', 'total_runs', 'dispatch_runs', 'schedule_runs', 'runner_lack_total', 'runner_lack_dispatch', 'manual_failure_rate_pct'])
    for r in hourly_rows:
        pct = round((r[5] / r[2] * 100) if r[2] else 0, 2)
        writer.writerow([r[0], r[1], r[2], r[3], r[4], r[5], pct])

# Day of week data
dow_map = {0: 'Sunday', 1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday'}
cur.execute('''
SELECT 
    CAST(strftime('%w', created_at) AS INTEGER) as dow,
    COUNT(*) as total_runs,
    SUM(CASE WHEN event = 'workflow_dispatch' THEN 1 ELSE 0 END) as dispatch_runs,
    SUM(CASE WHEN event = 'schedule' THEN 1 ELSE 0 END) as schedule_runs,
    SUM(CASE WHEN is_runner_lack = 1 THEN 1 ELSE 0 END) as runner_lack_total,
    SUM(CASE WHEN is_runner_lack = 1 AND event = 'workflow_dispatch' THEN 1 ELSE 0 END) as runner_lack_dispatch
FROM workflow_runs
WHERE created_at IS NOT NULL
GROUP BY dow
ORDER BY (dow + 6) % 7
''')
dow_rows = cur.fetchall()

with open(f'{DATA_DIR}/day_of_week_breakdown.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['day_of_week', 'total_runs', 'dispatch_runs', 'schedule_runs', 'runner_lack_total', 'runner_lack_dispatch', 'manual_failure_rate_pct'])
    for r in dow_rows:
        pct = round((r[5] / r[2] * 100) if r[2] else 0, 2)
        writer.writerow([dow_map[r[0]], r[1], r[2], r[3], r[4], r[5], pct])

# Monthly timeline data
cur.execute('''
SELECT 
    strftime('%Y-%m', created_at) as ym,
    COUNT(*) as total_runs,
    SUM(CASE WHEN event = 'workflow_dispatch' THEN 1 ELSE 0 END) as dispatch_runs,
    SUM(CASE WHEN event = 'schedule' THEN 1 ELSE 0 END) as schedule_runs,
    SUM(CASE WHEN is_runner_lack = 1 THEN 1 ELSE 0 END) as runner_lack_total,
    SUM(CASE WHEN is_runner_lack = 1 AND event = 'workflow_dispatch' THEN 1 ELSE 0 END) as runner_lack_dispatch
FROM workflow_runs
WHERE created_at IS NOT NULL
GROUP BY ym
ORDER BY ym
''')
monthly_rows = cur.fetchall()

with open(f'{DATA_DIR}/monthly_timeline.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['year_month', 'total_runs', 'dispatch_runs', 'schedule_runs', 'runner_lack_total', 'runner_lack_dispatch', 'runner_lack_pct_of_all'])
    for r in monthly_rows:
        pct = round((r[4] / r[1] * 100) if r[1] else 0, 2)
        writer.writerow([r[0], r[1], r[2], r[3], r[4], r[5], pct])

# Failure classifications
cur.execute('''
SELECT 
    job_failure_type,
    COUNT(*) as count
FROM workflow_runs
WHERE job_inspected = 1
GROUP BY job_failure_type
ORDER BY count DESC
''')
failure_rows = cur.fetchall()

with open(f'{DATA_DIR}/failure_classifications.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['failure_category', 'count', 'pct_of_failures', 'pct_of_total_runs'])
    for r in failure_rows:
        pct_fail = round(r[1] / inspected_runs * 100, 2)
        pct_tot = round(r[1] / total_runs * 100, 2)
        writer.writerow([r[0], r[1], pct_fail, pct_tot])

conn.close()
print("Data exports completed.")

# ---------------------------------------------------------------------------
# 2. GENERATE VECTOR SVGs
# ---------------------------------------------------------------------------
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

# SVG 1: Diurnal 24-Hour UTC Curve
hours = [r[0] for r in hourly_rows]
dispatch_runs_h = [r[2] for r in hourly_rows]
schedule_runs_h = [r[3] for r in hourly_rows]
lack_dispatch_h = [r[5] for r in hourly_rows]
lack_dispatch_pct = [(ld / d * 100) if d > 0 else 0 for ld, d in zip(lack_dispatch_h, dispatch_runs_h)]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True, gridspec_kw={'height_ratios': [1, 1.2]})

ax1.bar(np.array(hours) - 0.2, dispatch_runs_h, width=0.4, label='Manual (workflow_dispatch)', color='#0284c7', alpha=0.9)
ax1.bar(np.array(hours) + 0.2, schedule_runs_h, width=0.4, label='Scheduled Cron (Sundays)', color='#93c5fd', alpha=0.9)
ax1.set_ylabel('Workflow Runs', fontsize=10, fontweight='bold', color='#1e293b')
ax1.set_title('Figure 1: Diurnal Activity & macOS Runner Starvation Rate (24h UTC Profile)', fontsize=12, fontweight='bold', pad=10, color='#0f172a')
ax1.legend(loc='upper right', frameon=True, fontsize=9)
ax1.grid(True, linestyle='--', alpha=0.5)

ax2.bar(hours, lack_dispatch_pct, color='#ef4444', alpha=0.85, width=0.55, label='macOS Runner Starvation Rate (%)')
ax2.plot(hours, lack_dispatch_pct, color='#b91c1c', marker='o', linewidth=2, markersize=5)

ax2.axvspan(13.5, 17.5, color='#fee2e2', alpha=0.4, label='Acute Peak Window (14:00 - 17:00 UTC)')
ax2.axvspan(-0.5, 11.5, color='#dcfce7', alpha=0.35, label='Safe Window (22:00 - 11:00 UTC)')
ax2.axvspan(21.5, 23.5, color='#dcfce7', alpha=0.35)

ax2.set_xlabel('Hour of the Day (UTC)', fontsize=10, fontweight='bold', color='#1e293b')
ax2.set_ylabel('Failure Rate (% of Manual Runs)', fontsize=10, fontweight='bold', color='#b91c1c')
ax2.set_xticks(range(24))
ax2.set_xticklabels([f'{h:02d}:00' for h in range(24)], rotation=45, ha='right', fontsize=9)
ax2.set_ylim(0, max(lack_dispatch_pct) * 1.3)
ax2.legend(loc='upper left', frameon=True, fontsize=9)
ax2.grid(True, linestyle='--', alpha=0.5)

for h, pct in zip(hours, lack_dispatch_pct):
    if pct >= 3.5:
        ax2.annotate(f'{pct:.1f}%', (h, pct), textcoords="offset points", xytext=(0, 5),
                     ha='center', fontsize=8, fontweight='bold', color='#b91c1c')

plt.tight_layout()
svg1_path = f'{ASSETS_DIR}/diurnal_curve.svg'
plt.savefig(svg1_path, format='svg')
plt.close()
print(f"Generated {svg1_path}")

# SVG 2: Longitudinal Timeline
yms = [r[0] for r in monthly_rows]
m_total = [r[1] for r in monthly_rows]
m_lack = [r[4] for r in monthly_rows]
x = np.arange(len(yms))

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True, gridspec_kw={'height_ratios': [1, 1.1]})

ax1.bar(x, m_total, color='#10b981', alpha=0.85, width=0.6, label='Total Monthly Executions')
ax1.set_ylabel('Total Executions', fontsize=10, fontweight='bold', color='#1e293b')
ax1.set_title('Figure 2: Historical Timeline of Build Executions vs. macOS Runner Starvations', fontsize=12, fontweight='bold', pad=10, color='#0f172a')
ax1.legend(loc='upper left', frameon=True, fontsize=9)
ax1.grid(True, linestyle='--', alpha=0.5)

ax2.bar(x, m_lack, color='#f97316', alpha=0.85, width=0.55, label='macOS Runner Starvations')
ax2.plot(x, m_lack, color='#c2410c', marker='s', linewidth=2, markersize=5)
ax2.set_ylabel('Starvations Count', fontsize=10, fontweight='bold', color='#c2410c')
ax2.set_xlabel('Month', fontsize=10, fontweight='bold', color='#1e293b')
ax2.set_xticks(x)
ax2.set_xticklabels(yms, rotation=45, ha='right', fontsize=9)
ax2.legend(loc='upper right', frameon=True, fontsize=9)
ax2.grid(True, linestyle='--', alpha=0.5)

if '2025-10' in yms:
    idx_2025_10 = yms.index('2025-10')
    ax2.annotate('Oct 1, 2025\nGitHub Actions Outage', 
                 xy=(idx_2025_10, m_lack[idx_2025_10]), 
                 xytext=(idx_2025_10 - 2.2, m_lack[idx_2025_10] + 15),
                 arrowprops=dict(facecolor='#475569', shrink=0.05, width=1, headwidth=5),
                 fontsize=8, fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", fc="#fef2f2", ec="#f87171"))

if '2026-10' in yms:
    idx_2026_10 = yms.index('2026-10')
    ax2.annotate('Oct 2026: macos-26\nApple Silicon Pool Strain', 
                 xy=(idx_2026_10, m_lack[idx_2026_10]), 
                 xytext=(idx_2026_10 - 3.2, m_lack[idx_2026_10] - 8),
                 arrowprops=dict(facecolor='#475569', shrink=0.05, width=1, headwidth=5),
                 fontsize=8, fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", fc="#fef2f2", ec="#f87171"))

plt.tight_layout()
svg2_path = f'{ASSETS_DIR}/timeline.svg'
plt.savefig(svg2_path, format='svg')
plt.close()
print(f"Generated {svg2_path}")

# SVG 3: Outcome Donut Chart
labels = [
    'Success (65.5%)',
    'Fastlane / Compilation (10.0%)',
    'Scheduled No-Op Skip (6.8%)',
    'Secrets / Auth (4.8%)',
    'Other Steps (4.2%)',
    'TestFlight Upload (2.2%)',
    'Ubuntu Access / PAT (1.6%)',
    'Certificates / Nuke (1.1%)',
    'macOS Runner Lack (1.0%)',
    'Other / Cancel (2.8%)'
]
sizes = [27117, 4154, 2817, 1987, 1745, 914, 653, 458, 395, 1170]
colors = ['#10b981', '#3b82f6', '#94a3b8', '#8b5cf6', '#06b6d4', '#f59e0b', '#ec4899', '#6366f1', '#ef4444', '#cbd5e1']

fig, ax = plt.subplots(figsize=(8, 6.5))
wedges, texts = ax.pie(sizes, colors=colors, startangle=140, wedgeprops=dict(width=0.4, edgecolor='w'))
ax.legend(wedges, labels, title="Outcome Breakdown (41,410 Runs)", loc="center left", bbox_to_anchor=(0.95, 0.5), fontsize=9)
ax.set_title('Figure 3: Population Outcome Distribution across All 2,437 Forks', fontsize=12, fontweight='bold', pad=12, color='#0f172a')
plt.tight_layout()
svg3_path = f'{ASSETS_DIR}/outcomes_donut.svg'
plt.savefig(svg3_path, format='svg')
plt.close()
print(f"Generated {svg3_path}")

# SVG 4: Day of Week Bar Chart
days = [dow_map[r[0]] for r in dow_rows]
dow_rates = [round((r[5] / r[2] * 100) if r[2] else 0, 2) for r in dow_rows]

fig, ax = plt.subplots(figsize=(9, 4.5))
bars = ax.bar(days, dow_rates, color=['#ef4444' if d in ['Tuesday', 'Wednesday'] else '#3b82f6' for d in days], width=0.55, alpha=0.85)
ax.set_ylabel('Manual Build Failure Rate (%)', fontsize=10, fontweight='bold', color='#1e293b')
ax.set_title('Figure 4: macOS Runner Starvation Rate by Day of Week', fontsize=12, fontweight='bold', pad=10, color='#0f172a')
ax.grid(True, linestyle='--', alpha=0.5)
ax.set_ylim(0, max(dow_rates) * 1.3)

for bar, rate in zip(bars, dow_rates):
    ax.annotate(f'{rate:.1f}%', (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                textcoords="offset points", xytext=(0, 4), ha='center', fontsize=9, fontweight='bold', color='#1e293b')

plt.tight_layout()
svg4_path = f'{ASSETS_DIR}/day_of_week.svg'
plt.savefig(svg4_path, format='svg')
plt.close()
print(f"Generated {svg4_path}")
