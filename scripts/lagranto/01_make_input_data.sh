#!/bin/bash
set -e -x

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)

source "$SCRIPT_DIR/config.sh"

START_T="$1"
END_T="$2"

mkdir -p "$INPUT_DATA"

cat << eof > tmp_grid.txt
gridtype = lonlat
xsize    = 1441
ysize    = 721
xfirst   = 0
xinc     = 0.25
yfirst   = 90
yinc     = -0.25
eof

CURRENT="$START_T"
while [ "$(date -d "$CURRENT" +%s)" -ge "$(date -d "$END_T" +%s)" ]; do	
	yyyy=$(date -d "$CURRENT" +%Y)
	mm=$(date -d "$CURRENT" +%m)
	dd=$(date -d "$CURRENT" +%d)
	hh=$(date -d "$CURRENT" +%H)

	echo "## PROCESSING ${yyyy}-${mm}-${dd} T${hh}"

  ps_file="$ERA5DIR"/single/ps_${yyyy}${mm}.nc
  u_file="$ERA5DIR"/pressure/u${yyyy}${mm}.nc
  v_file="$ERA5DIR"/pressure/v${yyyy}${mm}.nc
  w_file="$ERA5DIR"/pressure/w${yyyy}${mm}.nc
  t_file="$ERA5DIR"/pressure/t${yyyy}${mm}.nc
  q_file="$ERA5DIR"/pressure/q${yyyy}${mm}.nc
  r_file="$ERA5DIR"/pressure/rh${yyyy}${mm}.nc

  find $ps_file; find $u_file; find $v_file; find $w_file;

  TMPDIR=TMP_${yyyy}${mm}${dd}${hh}
  mkdir -p $TMPDIR

  echo "## SEL DATE"
  cdo seldate,${yyyy}-${mm}-${dd}T${hh}:00:00 $ps_file "$TMPDIR"/ps.nc
  cdo seldate,${yyyy}-${mm}-${dd}T${hh}:00:00 $u_file "$TMPDIR"/u.nc
  cdo seldate,${yyyy}-${mm}-${dd}T${hh}:00:00 $v_file "$TMPDIR"/v.nc
  cdo seldate,${yyyy}-${mm}-${dd}T${hh}:00:00 $w_file "$TMPDIR"/w.nc
  cdo seldate,${yyyy}-${mm}-${dd}T${hh}:00:00 $t_file "$TMPDIR"/t.nc
  cdo seldate,${yyyy}-${mm}-${dd}T${hh}:00:00 $q_file "$TMPDIR"/q.nc
  cdo seldate,${yyyy}-${mm}-${dd}T${hh}:00:00 $r_file "$TMPDIR"/r.nc

  echo "## RENAME"
  cdo chname,u,U "$TMPDIR"/u.nc "$TMPDIR"/u2.nc
  cdo chname,v,V "$TMPDIR"/v.nc "$TMPDIR"/v2.nc
  cdo chname,w,OMEGA "$TMPDIR"/w.nc "$TMPDIR"/w2.nc
  cdo chname,sp,PS "$TMPDIR"/ps.nc "$TMPDIR"/ps2.nc
  cdo chname,t,T "$TMPDIR"/t.nc "$TMPDIR"/t2.nc
  cdo chname,q,Q "$TMPDIR"/q.nc "$TMPDIR"/q2.nc
  cdo chname,r,RH "$TMPDIR"/r.nc "$TMPDIR"/r2.nc

  echo "## UNITS"
  cdo divc,100 $TMPDIR/ps2.nc $TMPDIR/ps3.nc

  echo "## MERGING"
  OFILE="$INPUT_DATA"/P${yyyy}${mm}${dd}_${hh}
  cdo merge $TMPDIR/u2.nc $TMPDIR/v2.nc $TMPDIR/w2.nc $TMPDIR/ps3.nc $TMPDIR/t2.nc $TMPDIR/q2.nc $TMPDIR/r2.nc  "$TMPDIR"/merged0.nc

  cdo settaxis,${yyyy}-${mm}-${dd},${hh}:00:00,6hour "$TMPDIR"/merged0.nc "$TMPDIR"/merged_time.nc

  echo "## REGRID"
  cdo remapcon,tmp_grid.txt "$TMPDIR"/merged_time.nc "$TMPDIR"/merged.nc   
  echo "## RENAME"
  cdo chname,longitude,lon,latitude,lat "$TMPDIR"/merged.nc "$TMPDIR"/merged2.nc
	cdo chname,pressure_level,lev "$TMPDIR"/merged2.nc "$TMPDIR"/merged3.nc
  cdo invertlat "$TMPDIR"/merged3.nc "$OFILE"                               
  echo "SAVED: ${OFILE}"

	rm -rf "$TMPDIR"
	CURRENT=$(date -d "$CURRENT -6 hours" +"%Y-%m-%d %H")

done
rm -f tmp_grid.txt

python << eof
import xarray as xr
from pathlib import Path

datadir = Path("$INPUT_DATA")
files = sorted(datadir.glob("P*_*"))

for f in files:
  print(f"processing: {f.name}")

  try:
    ds = xr.open_dataset(f)

    if "valid_time" in ds:
      ds = ds.rename({"valid_time": "time"})

    if "time" in ds:
      ds["time"].encoding.pop("units", None)
      ds["time"].encoding.pop("calendar", None)

      ds["time"].attrs["standard_name"] = "time"
      ds["time"].attrs["axis"] = "T"

    tmp = f.with_suffix(".tmp")
    ds.to_netcdf(tmp)
    tmp.replace(f)

    ds.close()

  except Exception as e:
    print(f"skip {f.name}: {e}")

eof
