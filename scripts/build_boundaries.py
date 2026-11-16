"""Build the border and coastline files the map draws.

Borders: China's official depiction, from the Aliyun DataV boundary service (provinces, national
outline and the dashed line in the South China Sea). Those files use China's GCJ-02 coordinates,
which sit up to about 500 m from GPS coordinates, so they are shifted back to WGS-84 here.
Coastline for context: Natural Earth 1:50m land (public domain), which carries no borders.

Inputs are expected in data/raw/src/ (see README for the download addresses).
"""
import json, math
from pathlib import Path
from shapely.geometry import shape, mapping, box

ROOT = Path(__file__).parent.parent
SRC = ROOT / "data" / "raw" / "src"
A, EE = 6378245.0, 0.00669342162296594323


def _dlat(x, y):
    r = -100 + 2 * x + 3 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    r += (20 * math.sin(6 * x * math.pi) + 20 * math.sin(2 * x * math.pi)) * 2 / 3
    r += (20 * math.sin(y * math.pi) + 40 * math.sin(y / 3 * math.pi)) * 2 / 3
    r += (160 * math.sin(y / 12 * math.pi) + 320 * math.sin(y * math.pi / 30)) * 2 / 3
    return r


def _dlon(x, y):
    r = 300 + x + 2 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    r += (20 * math.sin(6 * x * math.pi) + 20 * math.sin(2 * x * math.pi)) * 2 / 3
    r += (20 * math.sin(x * math.pi) + 40 * math.sin(x / 3 * math.pi)) * 2 / 3
    r += (150 * math.sin(x / 12 * math.pi) + 300 * math.sin(x / 30 * math.pi)) * 2 / 3
    return r


def gcj_to_wgs(lon, lat):
    dlat, dlon = _dlat(lon - 105, lat - 35), _dlon(lon - 105, lat - 35)
    rad = math.radians(lat); magic = 1 - EE * math.sin(rad) ** 2; sq = math.sqrt(magic)
    dlat = dlat * 180 / ((A * (1 - EE)) / (magic * sq) * math.pi)
    dlon = dlon * 180 / (A / sq * math.cos(rad) * math.pi)
    return round(lon - dlon, 5), round(lat - dlat, 5)


def fix(coords):
    if isinstance(coords[0], (int, float)):
        return list(gcj_to_wgs(coords[0], coords[1]))
    return [fix(c) for c in coords]


def main():
    full = json.loads((SRC / "china_full.json").read_text(encoding="utf-8"))
    outline = json.loads((SRC / "china_outline.json").read_text(encoding="utf-8"))
    feats = []
    for f in outline["features"]:
        feats.append({"type": "Feature", "properties": {"kind": "country"},
                      "geometry": {"type": f["geometry"]["type"], "coordinates": fix(f["geometry"]["coordinates"])}})
    for f in full["features"]:
        code = str(f["properties"].get("adcode"))
        kind = "dashline" if code.endswith("_JD") else "province"
        g = shape({"type": f["geometry"]["type"], "coordinates": fix(f["geometry"]["coordinates"])})
        g = g.simplify(0.01, preserve_topology=True) if kind == "province" else g
        feats.append({"type": "Feature", "properties": {"kind": kind, "code": code}, "geometry": mapping(g)})
    (ROOT / "data" / "china.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")))
    land = json.loads((SRC / "ne_50m_land.geojson").read_text(encoding="utf-8"))
    win = box(40, -12, 165, 68); out = []
    for f in land["features"]:
        g = shape(f["geometry"]).intersection(win)
        if not g.is_empty:
            out.append({"type": "Feature", "properties": {}, "geometry": mapping(g)})
    txt = json.dumps({"type": "FeatureCollection", "features": out}, separators=(",", ":"))
    import re
    txt = re.sub(r"(\d+\.\d{3})\d+", r"\1", txt)
    (ROOT / "data" / "land.geojson").write_text(txt)
    kinds = {}
    for f in feats: kinds[f["properties"]["kind"]] = kinds.get(f["properties"]["kind"], 0) + 1
    print(kinds, "land parts", len(out))


if __name__ == "__main__":
    main()
