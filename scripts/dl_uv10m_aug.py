# ERA5 hourly single levels: 10m u,v の 8月・6時間おき・領域限定 を 1991-2020 年分ダウンロード
# 事前に ~/.cdsapirc を設定しておくこと
import os
import cdsapi

OUTDIR = "/raid/users/imai/ERA5/data/hourly6h_aug/single"
os.makedirs(OUTDIR, exist_ok=True)

c = cdsapi.Client()

for year in range(1991, 2021):
    out = f"{OUTDIR}/uv10m_{year}08.nc"
    if os.path.exists(out):
        continue
    c.retrieve(
        "reanalysis-era5-single-levels",
        {
            "product_type": "reanalysis",
            "variable": [
                "10m_u_component_of_wind",
                "10m_v_component_of_wind",
            ],
            "year": str(year),
            "month": "08",
            "day": [f"{d:02d}" for d in range(1, 32)],
            "time": ["00:00", "06:00", "12:00", "18:00"],
            "area": [50, 110, 0, 185],      # N, W, S, E
            "data_format": "netcdf",
            "download_format": "unarchived",
        },
        out,
    )
