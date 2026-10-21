"""Zhao et al. (2023, GRL) Fig. 4 (right column) style figure."""
import matplotlib as mpl
mpl.use('Agg')
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
import argparse
from collections import defaultdict

## ======== command-line args ========
parser = argparse.ArgumentParser()
parser.add_argument('exp_name')
parser.add_argument('--mode', choices=['abs', 'frac'], default='abs',
                    help="abs: mean moisture per parcel (Q units); frac: share at each time (stack = 100%%)")
parser.add_argument('--itra-dir', default=None, help='override trajectory csv directory')
parser.add_argument('--outdir', default=None, help='override output directory')
parser.add_argument('--ylabel', default='Mean moisture content per parcel (Q)')
args = parser.parse_args()

## ======== dirs & files ========
exp_name = args.exp_name
base_dir = '/raid/users/imai/work_Chiba_2026'
itra_dir = args.itra_dir or os.path.join(base_dir, 'Work', exp_name, '04_post', 'splited')
ofig_dir = args.outdir or os.path.join(base_dir, 'figure', exp_name)
os.makedirs(ofig_dir, exist_ok=True)
ifiles   = sorted(glob.glob(os.path.join(itra_dir, '*.csv')))
ofile    = os.path.join(ofig_dir, f'moisture_timeseries_by_region_{args.mode}.png')
ocsv     = os.path.join(ofig_dir, 'moisture_timeseries_by_region.csv')

## ======== parameters (same as 14_moisture_contribution.py) ========
time_diff         = -1.0
rh_threshold      = 80.0
p_upper_threshold = 500.0
dq_threshold      = 0.0
PBL_COL      = 'PBL'
P0           = 1014.0
SCALE_HEIGHT = 8000.0
BLH_FACTOR   = 1.5

## ======== regions (edit regions.py) ========
from regions import REGIONS
ORIGIN   = ("Origin", "all")
RESIDUAL = "Residual"
ORIGIN_COLOR, RESIDUAL_COLOR = "gray", "lightgray"


def classify(lon, lat):
    for name, (x0, x1, y0, y1), _ in REGIONS:
        if x0 <= lon < x1 and y0 <= lat < y1:
            return name
    return RESIDUAL


def pressure_to_height(p, p0=P0, scale_height=SCALE_HEIGHT):
    return scale_height * np.log(p0 / p)


def is_precipitating_parcel(df):
    t0 = df[df['time'] == 0.0]
    tp = df[df['time'] == time_diff]
    if t0.empty or tp.empty:
        return False
    return (t0['RH'].values[0] >= rh_threshold) and (t0['p'].values[0] >= p_upper_threshold)


def track_parcel(df):
    """Run the ledger on one parcel; return a DataFrame (index=time) of moisture by category."""
    d = df.sort_values('time').reset_index(drop=True)
    t, lon, lat = d['time'].values, d['lon'].values, d['lat'].values
    p, Q, pbl = d['p'].values, d['Q'].values, d[PBL_COL].values

    ledger = {}                     # key=(category, t) -> value
    tot = defaultdict(float)        # category -> current sum of ledger values

    if Q[0] > 0:
        ledger[(ORIGIN, t[0])] = Q[0]
        tot[ORIGIN] += Q[0]

    rows = [(t[0], dict(tot))]
    for i in range(1, len(d)):
        q_prior = Q[i - 1]
        dq = Q[i] - q_prior

        if dq > dq_threshold:
            is_surface = (BLH_FACTOR * pbl[i - 1] >= pressure_to_height(p[i - 1]))
            cat = (classify(lon[i], lat[i]), 'evap' if is_surface else 'above')
            ledger[(cat, t[i])] = dq
            tot[cat] += dq

        elif dq < -dq_threshold and q_prior > 0:
            dead = []
            for key, val in ledger.items():
                new = val + dq * (val / q_prior)
                if new <= 0:
                    tot[key[0]] -= val          # entry fully drained
                    dead.append(key)
                else:
                    tot[key[0]] += new - val
                    ledger[key] = new
            for key in dead:
                del ledger[key]

        rows.append((t[i], dict(tot)))

    out = pd.DataFrame([r for _, r in rows], index=[x for x, _ in rows]).fillna(0.0)
    out['Q'] = Q
    return out


## ======== main ========
if __name__ == "__main__":
    frames = []
    for f in ifiles:
        df = pd.read_csv(f)
        if not is_precipitating_parcel(df):
            continue
        frames.append(track_parcel(df))

    if not frames:
        raise SystemExit('no precipitating parcels found')

    n_parcels = len(frames)
    allc = pd.concat(frames)
    allc.index.name = 'time'
    sums = allc.groupby(level=0).sum().sort_index()          # sum over parcels, per time
    cats = [c for c in sums.columns if c != 'Q']

    # layer order: Origin, then each region (evap, above), then Residual
#    layer_order = [ORIGIN]
    layer_order = [ORIGIN, (RESIDUAL, 'evap'), (RESIDUAL, 'above')]
    for name, _, _ in REGIONS:
        layer_order += [(name, 'evap'), (name, 'above')]
        #layer_order += [(name, 'evap')]
    #ayer_order += [(RESIDUAL, 'evap'), (RESIDUAL, 'above')]
    for c in layer_order:
        if c not in sums.columns:
            sums[c] = 0.0

    # conservation check: sum of categories should equal sum of Q
    resid = (sums[layer_order].sum(axis=1) - sums['Q']).abs().max()
    print(f"parcels: {n_parcels}   max |sum(categories) - sum(Q)| = {resid:.3g}")

    x = sums.index.values / 24.0
    Y = sums[layer_order].values.T                           # (layers, time)
    ylabel = args.ylabel
    if args.mode == 'abs':
        Y = Y / n_parcels
    else:
        Y = Y / np.where(Y.sum(axis=0) > 0, Y.sum(axis=0), 1.0) * 100.0
        ylabel = 'Share of parcel moisture (%)'

    colors, hatches, labels = [], [], []
    for c in layer_order:
        if c == ORIGIN:
            colors.append(ORIGIN_COLOR); hatches.append(None); labels.append('Origin')
            continue
        name, kind = c
        col = RESIDUAL_COLOR if name == RESIDUAL else dict((n, k) for n, _, k in REGIONS)[name]
        colors.append(col)
        hatches.append('////' if kind == 'evap' else None)
        labels.append(name if kind == 'above' else None)
#        labels.append(name)

    mpl.rcParams['hatch.linewidth'] = 0.2
    fig, ax = plt.subplots(figsize=(7.8, 4.0))
    polys = ax.stackplot(x, Y, colors=colors, labels=[l or '_nolegend_' for l in labels])
    for poly, h, col in zip(polys, hatches, colors):
        if h:
            poly.set_hatch(h)
            poly.set_edgecolor('lightgray')
            poly.set_linewidth(0)

    # final percentage labels on the right (share at the last time step)
    final = sums[layer_order].iloc[-1]
    final_tot = final.sum()
    by_group = {}
    for c in layer_order:
        g = 'Origin' if c == ORIGIN else c[0]
        by_group[g] = by_group.get(g, 0.0) + final[c]
    cum = np.cumsum(Y[:, -1])
    mid = cum - Y[:, -1] / 2.0
    label_pos = {}
    for k, c in enumerate(layer_order):
        g = 'Origin' if c == ORIGIN else c[0]
        label_pos.setdefault(g, []).append(mid[k])
    items = sorted(((np.mean(v), g) for g, v in label_pos.items()))
    ymax = cum[-1] if cum[-1] > 0 else 1.0
    min_gap = 0.06 * ymax
    placed, last = [], -np.inf
    for y, g in items:
        y = max(y, last + min_gap)
        placed.append((y, g)); last = y
    for y, g in placed:
        pct = 100.0 * by_group[g] / final_tot if final_tot > 0 else np.nan
        ax.text(x[-1] + 0.05, y, f"{pct:.1f}%", fontsize=8, va='center')

    ax.set_xlim(x[0], x[-1])
    ax.set_ylim(0, 20)
    ax.set_xticks(np.arange(np.ceil(x[0]), 1))
    ax.set_xticklabels([f"{int(v)} d" for v in np.arange(np.ceil(x[0]), 1)])
    ax.set_xlabel('time relative to arrival')
    ax.set_ylabel(ylabel)
    ax.set_title(f"{exp_name}: moisture gains by region (n={n_parcels} parcels)", fontsize=10)
    ax.grid(alpha=0.2)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.18), ncol=3, fontsize=8, frameon=False)
    fig.subplots_adjust(right=0.88, bottom=0.30)
    fig.savefig(ofile, dpi=150)
    print(f'figure saved: {ofile}')

    # table of final shares (evap / above split) for the text
    rows = []
    for g, v in by_group.items():
        ev = final.get((g, 'evap'), 0.0)
        ab = final.get((g, 'above'), 0.0)
        rows.append({'region': g, 'share_pct': 100 * v / final_tot,
                     'evap_pct': 100 * ev / final_tot, 'above_bl_pct': 100 * ab / final_tot})
    tab = pd.DataFrame(rows)
    print(tab.round(1).to_string(index=False))
    out = (sums[layer_order] / n_parcels).copy()
    out.columns = [f"{c[0]}|{c[1]}" for c in layer_order]
    out.insert(0, 'time_h', sums.index.values)
    out.to_csv(ocsv, index=False)
    print(f'csv saved: {ocsv}')
