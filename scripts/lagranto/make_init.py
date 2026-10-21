import numpy as np

lons = np.arange(139.5, 141.0 + 0.001, 0.1)
lats = np.arange(34.9, 35.9 + 0.001, 0.1)

with open('start_poiunts.txt', 'w') as f:
    for lon in lons:
        for lat in lats:
            f.write(f'{lon:.3f} {lat:.3f}\n' )
