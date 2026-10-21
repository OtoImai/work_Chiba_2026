import matplotlib as mpl
mpl.use('Agg')
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import os

## ======== command-line args ========

parser = argparse.ArgumentParser(
    description='Compute and plot the evaporative moisture-source contribution '
                'map for one LAGRANTO experiment directory.'
)
parser.add_argument('exp_name')
args = parser.parse_args()

## ======== dirs & files ========
exp_name = args.exp_name

base_dir = '/raid/users/imai/work_Chiba_2026'
work_dir = os.path.join(base_dir, 'Work', exp_name)
itra_dir = os.path.join(work_dir, '04_post', 'splited')

ofig_dir = os.path.join(base_dir, 'figure', exp_name)

ocoverage_file = os.path.join(ofig_dir, 'moisture_source_coverage_v2.csv')
ofile_scatter  = os.path.join(ofig_dir, 'initial_q_vs_dtot.png')

## ======== load coverage results, then re-read initial Q for each file ========

cov_df = pd.read_csv(ocoverage_file)
print(f"{len(cov_df)} trajectories in coverage file.")

initial_q_ratio = []

for idx, row in cov_df.iterrows():
    if idx % 500 == 0:
        print(f"{idx}/{len(cov_df)} processed", flush=True)

    fpath = os.path.join(itra_dir, row['file'])
    try:
        df = pd.read_csv(fpath)
    except Exception:
        initial_q_ratio.append(np.nan)
        continue

    df = df.sort_values('time').reset_index(drop=True)
    initial_Q = df.iloc[0]['Q']    # earliest available time (e.g. t=-120h)
    arrival_Q = df.iloc[-1]['Q']   # t=0

    ratio = (initial_Q / arrival_Q) if arrival_Q > 0 else np.nan
    initial_q_ratio.append(ratio)

cov_df['initial_q_ratio'] = initial_q_ratio

## ======== correlation & scatter plot ========

valid = cov_df.dropna(subset=['initial_q_ratio', 'd_tot'])
corr = valid['initial_q_ratio'].corr(valid['d_tot'])
print(f"Correlation (initial_Q/arrival_Q  vs  d_tot): r = {corr:.3f}")
print(f"Mean initial_Q/arrival_Q: {valid['initial_q_ratio'].mean():.3f}")
print(f"Median initial_Q/arrival_Q: {valid['initial_q_ratio'].median():.3f}")

fig, ax = plt.subplots(figsize=(10 / 2.54, 9 / 2.54))
ax.scatter(valid['initial_q_ratio'], valid['d_tot'], s=4, alpha=0.3, color='tab:blue')
ax.set_xlabel('initial Q / arrival Q  (t=-120h vs t=0)')
ax.set_ylabel('d_tot (unattributed fraction)')
ax.set_title(f'Is d_tot explained by trace length?\n(r = {corr:.2f})')

plt.tight_layout()
plt.savefig(ofile_scatter, dpi=150)
print(f'figure saved: \n {ofile_scatter}')

cov_df.to_csv(ocoverage_file, index=False)  # overwrite with the added column
print(f"Updated coverage file (added initial_q_ratio column): {ocoverage_file}")
