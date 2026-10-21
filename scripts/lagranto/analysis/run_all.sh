#!/usr/bin/env bash
#
#   nohup ./run_all.sh > run_all.out 2>&1 &                       # デフォルトの4時刻
#   nohup ./run_all.sh 20260814_00z 20260814_06z > run_all.out 2>&1 &
#   nohup ./run_all.sh -p > run_all.out 2>&1 &                    # 実験間を並列実行
#

PYTHON=${PYTHON:-python}
DEFAULT_EXPS=(20260814_box_7day_1300 20260814_box_7day_1306 20260814_box_7day_1312 20260814_box_7day_1318)

SCRIPTS=(11_*.py 12_*.py 13_*.py 14_*.py 15_*.py 16_*.py 17_*.py 19_*.py)  # .old は拡張子が違うので除外される

PARALLEL=0
if [[ "${1:-}" == "-p" ]]; then
    PARALLEL=1
    shift
fi
EXPS=("$@")
[[ ${#EXPS[@]} -eq 0 ]] && EXPS=("${DEFAULT_EXPS[@]}")

cd "$(dirname "$0")" || exit 1
STAMP=$(date +%Y%m%d_%H%M%S)
LOGROOT="logs/${STAMP}"
mkdir -p "$LOGROOT"
SUMMARY="${LOGROOT}/summary.log"

log() { echo "[$(date '+%F %T')] $*" | tee -a "$SUMMARY"; }

run_exp() {
    local exp=$1
    local logdir="${LOGROOT}/${exp}"
    mkdir -p "$logdir"
    log "=== START ${exp} ==="
    for s in "${SCRIPTS[@]}"; do
        if [[ ! -f "$s" ]]; then
            log "[${exp}] SKIP ${s} (not found)"
            continue
        fi
        local t0=$SECONDS
        log "[${exp}] RUN  ${s}"
        "$PYTHON" "$s" "$exp" > "${logdir}/${s%.py}.log" 2>&1
        local rc=$?
        if [[ $rc -ne 0 ]]; then
            log "[${exp}] FAIL ${s} (exit ${rc}, $((SECONDS - t0))s) -> この実験は中断"
            log "=== ABORT ${exp} ==="
            return $rc
        fi
        log "[${exp}] OK   ${s} ($((SECONDS - t0))s)"
    done
    log "=== DONE ${exp} ==="
}

log "scripts: ${SCRIPTS[*]}"
log "experiments: ${EXPS[*]} (parallel=${PARALLEL})"

pids=()
for exp in "${EXPS[@]}"; do
    if [[ $PARALLEL -eq 1 ]]; then
        run_exp "$exp" &
        pids+=($!)
    else
        run_exp "$exp"
    fi
done

fail=0
for pid in "${pids[@]}"; do
    wait "$pid" || fail=1
done

log "ALL FINISHED (fail=${fail})"
exit $fail
