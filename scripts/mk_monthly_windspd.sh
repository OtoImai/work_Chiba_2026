#!/bin/bash
# 6時間おきの u10,v10 から風速を作り、1991-2020 の 8月の平均風速(気候値)を作る
set -e -x

SRC=/raid/users/imai/ERA5/data/hourly6h_aug/single
OUT=/raid/users/imai/work_Chiba_2026/data/clim/single/wspd_aug_1991_2020_6h.nc
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

for y in $(seq 1991 2020); do
  # 各ステップで風速を計算 (u,v は同じファイルに入っている想定)
  cdo -O expr,'wspd=sqrt(u10*u10+v10*v10)' "$SRC"/uv10m_${y}08.nc "$TMP"/ws_${y}.nc
done

cdo -O mergetime "$TMP"/ws_????.nc "$TMP"/ws_all.nc
cdo ntime "$TMP"/ws_all.nc            # 30年 x 31日 x 4 = 3720 になるはず
cdo -O timmean "$TMP"/ws_all.nc "$OUT"
cdo -O setattribute,wspd@units="m s-1" "$OUT" "${OUT%.nc}_u.nc" && mv "${OUT%.nc}_u.nc" "$OUT"
cdo info -fldmean -sellonlatbox,130,150,20,30 "$OUT"
