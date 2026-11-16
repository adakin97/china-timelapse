"""Download one night-lights grid per year for China from Google Earth Engine.

Source: Li, Zhou, Zhao and Zhao (2020), "A harmonized global nighttime light dataset 1992-2018",
Scientific Data 7:168, extended by the authors to 2021. DMSP years 1992-2013, VIIRS converted to
DMSP-like values for 2014-2021. Values are 0 to 63.

Each year is averaged down to the map's picture grid in Web Mercator and saved as
data/raw/ntl_<year>.npy (float32). Reruns skip years already on disk.
"""
import io, sys
from pathlib import Path
import numpy as np, requests, ee
sys.path.insert(0, str(Path(__file__).parent))
from config import *

RAW = Path(__file__).parent.parent / "data" / "raw"
DMSP = "projects/sat-io/open-datasets/Harmonized_NTL/dmsp"
VIIRS = "projects/sat-io/open-datasets/Harmonized_NTL/viirs"
HALF = HEIGHT // 2                # fetched in two bands to stay under the download size limit


def image(year):
    if year <= 2013:
        return ee.Image(f"{DMSP}/Harmonized_DN_NTL_{year}_calDMSP")
    return ee.Image(f"{VIIRS}/Harmonized_DN_NTL_{year}_simVIIRS")


def fetch(year):
    img = image(year).unmask(0).toFloat()
    img = img.reduceResolution(ee.Reducer.mean(), maxPixels=64)
    parts = []
    for row0, rows in ((0, HALF), (HALF, HEIGHT - HALF)):
        top = Y1 - row0 * PX
        url = img.getDownloadURL({"format": "NPY", "crs": "EPSG:3857",
                                  "crs_transform": [PX, 0, X0, 0, -PX, top],
                                  "dimensions": [WIDTH, rows]})
        r = requests.get(url, timeout=600); r.raise_for_status()
        a = np.load(io.BytesIO(r.content))
        parts.append(a[a.dtype.names[0]].astype(np.float32))
    return np.vstack(parts)


def main():
    ee.Initialize(project=EE_PROJECT)
    RAW.mkdir(parents=True, exist_ok=True)
    for year in range(FIRST_YEAR, LAST_YEAR + 1):
        out = RAW / f"ntl_{year}.npy"
        if out.exists():
            continue
        a = fetch(year)
        assert a.shape == (HEIGHT, WIDTH), a.shape
        np.save(out, a)
        print(year, a.shape, "max", float(a.max()), "mean", round(float(a.mean()), 3), flush=True)


if __name__ == "__main__":
    main()
