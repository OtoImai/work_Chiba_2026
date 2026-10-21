"""Source-region boxes shared by 20_moisture_timeseries_by_region.py and 21_plot_regions.py.

(name, (lon0, lon1, lat0, lat1), color)
ORDER MATTERS: the first box that contains an uptake point wins.
Longitudes are in 0-360 style (e.g. 200 = 160W), same as the trajectory data.
"""
REGIONS = [
    ("Near-field (<150E)",         (139, 150, 28, 38), "tab:red"),
    ("Kuroshio Ext. (150-170E)",   (150, 170, 28, 38), "tab:blue"),
    ("Subtropical WP-W (<28N, <165E)",      (139, 165,  9, 28), "tab:green"),
    ("Subtropical WP-E (<28N, >165E)",      (165, 200,  9, 28), "yellowgreen"),
    ("Eastern N. Pacific (>170E)", (170, 200, 28, 38), "tab:purple"),
]
