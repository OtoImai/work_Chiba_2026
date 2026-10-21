import cdsapi
import os

c = cdsapi.Client()

dataset = "reanalysis-era5-pressure-levels"

var_dict = {
    "z": "geopotential",
    "q": "specific_humidity",
    "t": "temperature",
    "u": "u_component_of_wind",
    "v": "v_component_of_wind",
    "w": "vertical_velocity",
    "rh": "relative_humidity"
}

levels = [
    "100","150",
    "200","250","300","400","500","600",
    "700","775","850","925","1000"
]

out_dir = '../data/pressure'
os.makedirs(out_dir, exist_ok=True)

area = [90, 60, 0, 180]
times = ["00:00", "06:00", "12:00", "18:00"]

for vshort, vlong in var_dict.items():
    for year in range(2026, 2027):
        for month in range(8,9):

            yyyymm = f"{year}{month:02d}"
            outfile = os.path.join(out_dir, f"{vshort}_{yyyymm}.nc")

            request = {
                "product_type": "reanalysis",
                "variable": vlong,
                "pressure_level": levels,
                "year": str(year),
                "month": f"{month:02d}",
                "day" : [f"{d:02d}" for d in range(1,32)],
                "time": [
                            "00:00", "01:00", "02:00",
                            "03:00", "04:00", "05:00",
                            "06:00", "07:00", "08:00",
                            "09:00", "10:00", "11:00",
                            "12:00", "13:00", "14:00",
                            "15:00", "16:00", "17:00",
                            "18:00", "19:00", "20:00",
                            "21:00", "22:00", "23:00"
                        ],
                #"area": area,
                #"grid": [1.0, 1.0],
                "data_format": "netcdf"
            }

            print("Downloading", outfile)

            c.retrieve(
                dataset,
                request,
                outfile
            )
    print(f"DONE: {vlong}")
print("DONE ALL")


