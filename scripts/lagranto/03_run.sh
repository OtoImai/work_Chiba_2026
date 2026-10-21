#!/bin/bash
set -e -x

conf=$3
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
source "$SCRIPT_DIR"/"$conf"

START=$(echo "$1" | sed 's/ /_/' | sed 's/-//g')
END=$(echo "$2" | sed 's/ /_/' | sed 's/-//g')

mkdir -p "$RUN_DATA"
cd "$RUN_DATA"

ln -sf "$INPUT_DATA"/P*_* ./
ln -sf "$INIT_DATA"/startf.2 ./
ln -sf "$INIT_DATA"/regionf ./

caltra "$START" "$END" startf.2 traj.4 -j

trainfo traj.4 list > traj.4.txt

trace traj.4 traj.4.tmp -f T 1.0
trace traj.4.tmp traj.4.tmp2 -f Q 1000.0
trace traj.4.tmp2 traj.4.tmp3 -f PBL 1.0
trace traj.4.tmp3 traj.4.traced -f RH 1.0

trainfo traj.4.traced list > traced.4.txt

rm -f P*_* startf.2 regionf traj.4.tmp traj.4.tmp2 traj.4.tmp3
