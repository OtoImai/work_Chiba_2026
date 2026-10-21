#!/bin/bash
set -e -x
conf=$2

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
#source "$SCRIPT_DIR"/config.sh
source "$SCRIPT_DIR"/"$conf"

START_T=$1
INIT_TIME=$(echo "$START_T" | sed 's/ /_/' | sed 's/-//g')

mkdir -p "$INIT_DATA"
cd "$INIT_DATA"

ln -sf "$INPUT_DATA"/P*_* ./

echo $REGION1 > regionf
startf "$INIT_TIME" startf.2 "$INIT_METHOD"

rm -f P*_*
