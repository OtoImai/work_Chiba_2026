#!/bin/bash
set -e -x

BASEDIR=/raid/users/imai/work_Chiba_2026
FIGSDIR="$BASEDIR"/figure/synop
DATADIR="$BASEDIR"/data
PRSDIR="$DATADIR"/pressure
SFCDIR="$DATADIR"/single
CLMDIR="$DATADIR"/clim

mkdir -p "$FIGSDIR"

FIGURENAME=ivt

lon0=110
lon1=185
lat0=5
lat1=60

time=00z13
