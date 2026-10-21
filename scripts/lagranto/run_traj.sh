#!/bin/bash
set -e -x

# ========================
# LOAD CONFIG
# ========================
conf=$1
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
source "$SCRIPT_DIR"/"$conf"

LOGDIR="$WORKDIR"/logs
mkdir -p "$LOGDIR"
STAMP=$(date +"%Y%m%d_%H%M%S")

export LAGRANTO=/raid/users/imai/Work/lagranto.ecmwf
export PATH=$LAGRANTO/bin:$PATH

# ========================
# TIME SETTING
# ========================

START_T=$(echo "$START" | sed 's/T/ /')
END_T=$(date -d  "$START_T -${BACK_HOURS} hours" +"%Y-%m-%d %H")

echo "START = $START_T"
echo " END  = $END_T"

NCORES=8

sleep 1
echo "# ========================"
echo "# MAKE INPUT DATA         "
echo "# ========================"
#bash "$SCRIPT_DIR/01_make_input_data.sh" "$START_T" "$END_T" "$conf" > "$LOGDIR/01_${STAMP}.log" 2>&1
#bash "$SCRIPT_DIR/01_make_input_data_para.sh" "$START_T" "$END_T" "$NCORES" "$conf" > "$LOGDIR/01_${STAMP}.log" 2>&1
mkdir "$INPUT_DATA"
ln -sf "$BASE"/Work/20260814_box_7day/01_input_data/P* "$INPUT_DATA"


sleep 1
echo "# ========================"
echo "# MAKE INITIAL POSITION   "
echo "# ========================"
bash "$SCRIPT_DIR/02_make_init_parcel.sh" "$START_T" "$conf" > "$LOGDIR/02_${STAMP}.log" 2>&1

sleep 1
echo "# ========================"
echo "# RUN CALCULATION         "
echo "# ========================"
bash "$SCRIPT_DIR/03_run.sh" "$START_T" "$END_T" "$conf" > "$LOGDIR/03_${STAMP}.log" 2>&1

sleep 1
echo "# ========================"
echo "# POST PROCESS            "
echo "# ========================"

bash "$SCRIPT_DIR/04_sep_traj4.sh" "$conf" > "$LOGDIR/04_${STAMP}.log" 2>&1
