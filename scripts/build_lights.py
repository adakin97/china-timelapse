"""Turn the yearly night-lights grids into the pictures the map shows, plus one line of numbers per year.

Reads data/raw/ntl_<year>.npy, writes data/lights/<year>.webp (transparent where dark) and
data/years.json (brightly lit area and total light inside China's border as drawn on the map).
"""
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).parent))
from config import *

ROOT = Path(__file__).parent.parent
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "lights"
LIT = 20.0    # "brightly lit". Lower cut-offs give a jumpy series after 2014, when the newer, more
              # sensitive sensor picks up faint glow the older one could not see.
FEATHER = 140 # pixels over which the picture fades out at its edges, so the data window has no hard border

# colour ramp: value (0-63) -> red, green, blue, opacity
# Nothing is drawn below 10: faint values are where the two sensors disagree most.
STOPS = np.array([[0, 255, 120, 30, 0], [10, 255, 130, 40, 0], [16, 255, 150, 50, 120], [26, 255, 190, 90, 200],
                  [42, 255, 226, 150, 240], [58, 255, 248, 225, 255], [63, 255, 255, 255, 255]], dtype=float)


def colourise(a):
    rgba = np.empty(a.shape + (4,), dtype=np.uint8)
    for k in range(4):
        rgba[..., k] = np.interp(a, STOPS[:, 0], STOPS[:, k + 1]).astype(np.uint8)
    edge = np.minimum.outer(np.minimum(np.arange(a.shape[0]), np.arange(a.shape[0])[::-1]),
                            np.minimum(np.arange(a.shape[1]), np.arange(a.shape[1])[::-1]))
    rgba[..., 3] = (rgba[..., 3] * np.clip(edge / FEATHER, 0, 1)).astype(np.uint8)
    return rgba


def china_mask():
    gj = json.loads((ROOT / "data" / "china.geojson").read_text())
    im = Image.new("L", (WIDTH, HEIGHT), 0); d = ImageDraw.Draw(im)
    for f in gj["features"]:
        if f["properties"]["kind"] != "province":
            continue
        g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            ring = [((merc_x(x) - X0) / PX, (Y1 - merc_y(y)) / PX) for x, y in poly[0]]
            if len(ring) > 2:
                d.polygon(ring, fill=1)
    return np.asarray(im, dtype=bool)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mask = china_mask()
    rows = np.arange(HEIGHT) + 0.5
    lat = np.degrees(2 * np.arctan(np.exp((Y1 - rows * PX) / R)) - math.pi / 2)
    km2 = ((PX * np.cos(np.radians(lat))) ** 2 / 1e6)[:, None]      # true ground area of a pixel in each row
    years = []
    for year in range(FIRST_YEAR, LAST_YEAR + 1):
        p = RAW / f"ntl_{year}.npy"
        if not p.exists():
            continue
        a = np.load(p)
        Image.fromarray(colourise(a), "RGBA").save(OUT / f"{year}.webp", quality=80, method=4)
        inside = np.where(mask, a, 0)
        years.append({"year": year, "lit_km2": int(((inside > LIT) * km2).sum()),
                      "light": int((np.where(inside > LIT, inside, 0) * km2).sum())})
        print(years[-1], round((OUT / f"{year}.webp").stat().st_size / 1e6, 2), "MB", flush=True)
    (ROOT / "data" / "years.json").write_text(json.dumps({
        "bounds": [LON_W, LAT_S, LON_E, LAT_N], "years": years}, indent=1))


if __name__ == "__main__":
    main()
