#!/bin/bash
set -e -x

conf=$1
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
source "$SCRIPT_DIR"/"$conf"

mkdir -p "$POST_DATA"
cd "$POST_DATA"
ln -sf $RUN_DATA/traced.4.txt ./

OUTDIR="$POST_DATA"/splited
mkdir -p $OUTDIR

awk -v outdir="$OUTDIR" '
/^-+$/ {data=1; next}
data && /^$/ {i++; newfile=1; next}

data {
  file = sprintf("%s/track_%04d.csv", outdir, i)
  if (newfile != 0) {
    print "time,lon,lat,p,T,Q,PBL,RH" > file
    newfile=0
  }
  print $1","$2","$3","$4","$5","$6","$7","$8 >> file
}
' traced.4.txt
