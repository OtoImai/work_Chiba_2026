#!/usr/bin/env python
"""到着時(t=0)のRHとTの散布図を、実験(初期時刻)ごとに2x2で描く。

ERA5のRHは T>0℃で水面、T<-23℃で氷面、その間は混合相に対する飽和。
RH>100%がどの温度帯に出ているかを確認するための図。

使い方:
    python 19_rh_vs_T.py "data/00z/*.csv" "data/06z/*.csv" "data/12z/*.csv" "data/18z/*.csv" \
        --names 00UTC 06UTC 12UTC 18UTC
前提: 1ファイル=1トラジェクトリ、行=時刻、t=0 の行が到着時刻。
"""
import argparse
import glob
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_arrival(pattern, time_col, t_col, rh_col):
    rows = []
    for f in sorted(glob.glob(pattern)):
        df = pd.read_csv(f)
        a = df[np.isclose(df[time_col], 0.0)]
        if len(a) == 0:
            continue
        rows.append((a[t_col].iloc[0], a[rh_col].iloc[0]))
    arr = np.array(rows, dtype=float)
    if len(arr) == 0:
        raise SystemExit(f"到着時刻の行が見つかりません: {pattern}")
    T, RH = arr[:, 0], arr[:, 1]
    if np.nanmean(T) > 100:  # Kと判断
        T = T - 273.15
    return T, RH


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("patterns", nargs="+", help="各実験のCSVのglobパターン")
    ap.add_argument("--names", nargs="*")
    ap.add_argument("--time-col", default="time")
    ap.add_argument("--t-col", default="T")
    ap.add_argument("--rh-col", default="RH")
    ap.add_argument("--out", default="rh_vs_T.png")
    args = ap.parse_args()
    names = args.names or args.patterns

    n = len(args.patterns)
    ncol = 2
    nrow = int(np.ceil(n / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(10, 4.2 * nrow),
                             sharex=True, sharey=True, squeeze=False)
    bins = [(-100, -23), (-23, 0), (0, 100)]
    labels = ["T<-23℃(氷面)", "-23〜0℃(混合相)", "T>0℃(水面)"]

    for ax, pat, name in zip(axes.ravel(), args.patterns, names):
        T, RH = load_arrival(pat, args.time_col, args.t_col, args.rh_col)
        ax.scatter(T, RH, s=6, alpha=0.4, color="tab:red")
        ax.axhline(100, color="k", lw=0.8, ls="--")
        ax.axvline(0, color="gray", lw=0.8, ls=":")
        ax.axvline(-23, color="gray", lw=0.8, ls=":")
        ax.set_title(name)
        ax.set_xlabel("arrival (t=0) T [°C]")
        ax.set_ylabel("arrival (t=0) RH [%]")
        ax.grid(alpha=0.3)

        print(f"--- {name} (n={len(T)})")
        for (lo, hi), lab in zip(bins, labels):
            m = (T >= lo) & (T < hi)
            if m.sum() == 0:
                continue
            print(f"  {lab}: n={m.sum():4d}  RH>100%: {100 * np.mean(RH[m] > 100):5.1f}%"
                  f"  max RH={RH[m].max():.0f}")

    for ax in axes.ravel()[n:]:
        ax.set_visible(False)

    fig.tight_layout()
    fig.savefig(args.out, dpi=150)
    print(f"saved: {args.out}")


if __name__ == "__main__":
    main()
