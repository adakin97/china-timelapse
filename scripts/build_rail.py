"""Turn the OpenStreetMap high-speed tracks into the dated rail layer the map draws.

Each track gets an opening year:
  1. from its own start_date (or opening_date) tag, where OpenStreetMap has one;
  2. otherwise from the nearest dated track with the same line name (marked est = estimated);
  3. otherwise from the short hand-entered table MANUAL below, for the longer lines that have no
     dated track at all (also marked est);
  4. otherwise it is left out, and listed in data/raw/rail/undated.txt for checking.

Writes data/rail.geojson (lines with year "y", name "n", est 0/1) and data/rail.json (length open by year).
Lengths: OpenStreetMap maps each of the two tracks of a line separately, so route length is taken
as half the track length. That is an approximation.
"""
import json, collections
from pathlib import Path
import numpy as np
from pyproj import Geod
from shapely.geometry import LineString, MultiLineString, mapping
from shapely.ops import linemerge

ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "raw" / "rail"
GEOD = Geod(ellps="WGS84")
SKIP_SERVICE = {"yard", "siding", "spur", "crossover"}
FIRST, LAST = 1999, 2026

# Opening years for lines with no dated track in OpenStreetMap. Entered by hand from the publicly
# reported opening dates; where a line opened in stages the year of the last stage is used, so a
# line never appears before it existed. These need checking against a second source.
MANUAL = {
    "银西高速线": 2020,   # Yinchuan-Xi'an
    "银兰高速线": 2022,   # Yinchuan-Lanzhou (first stage 2019)
    "怀衡线": 2018,       # Huaihua-Hengyang
    "成渝高速线": 2015,   # Chengdu-Chongqing
    "兰渝线": 2017,       # Lanzhou-Chongqing (earlier stages 2015-16)
    "衢九线": 2017,       # Quzhou-Jiujiang
    "渝万高速线": 2016,   # Chongqing-Wanzhou
    "潍烟高速线": 2024,   # Weifang-Yantai
    "柳南客专线": 2013,   # Liuzhou-Nanning
    "武九客专线": 2017,   # Wuhan-Jiujiang
    "新通客专线": 2018,   # Xinmin-Tongliao
    "楚大线": 2018,       # Chuxiong-Dali
    "京唐城际线": 2022,   # Beijing-Tangshan
    "邕北线": 2013,       # Nanning-Beihai
    "梅汕线": 2019,       # Meizhou-Chaoshan
    "安六客专线": 2020,   # Anshun-Liupanshui
    "弥蒙高速线": 2022,   # Mile-Mengzi
    "盘营高速线": 2013,   # Panjin-Yingkou
    "中老昆万线": 2021,   # China-Laos railway
    "武咸城际线": 2013,   # Wuhan-Xianning
    "成灌线": 2010,       # Chengdu-Dujiangyan
    "崇礼线": 2019,       # Chongli
    "京滨城际线": 2022,   # Beijing-Binhai
    "钦防线": 2013,       # Qinzhou-Fangchenggang
    "防东线": 2023,       # Fangchenggang-Dongxing
}


def year_of(tags):
    for k in ("start_date", "opening_date"):
        v = tags.get(k, "")[:4]
        if v.isdigit() and FIRST <= int(v) <= LAST:
            return int(v)
    return None


def main():
    ways = json.loads((RAW / "ways_geom.json").read_text(encoding="utf-8"))["elements"]
    recs = []
    for w in ways:
        t = w.get("tags", {})
        if t.get("service") in SKIP_SERVICE or len(w.get("geometry", [])) < 2:
            continue
        xy = np.array([(p["lon"], p["lat"]) for p in w["geometry"]])
        recs.append({"name": t.get("name") or "", "en": t.get("name:en") or "", "y": year_of(t), "est": 0, "xy": xy,
                     "km": GEOD.line_length(xy[:, 0], xy[:, 1]) / 1000, "mid": xy[len(xy) // 2]})
    by_name = collections.defaultdict(list)
    for r in recs:
        by_name[r["name"]].append(r)
    undated = collections.Counter()
    for name, rs in by_name.items():
        dated = [r for r in rs if r["y"]]
        todo = [r for r in rs if not r["y"]]
        if not todo:
            continue
        if not dated and name in MANUAL:
            for r in todo:
                r["y"], r["est"] = MANUAL[name], 1
            continue
        if not dated or not name:
            for r in todo:
                undated[name] += r["km"]
            continue
        pts = np.array([r["mid"] for r in dated]); yrs = np.array([r["y"] for r in dated])
        for r in todo:
            d = (pts[:, 0] - r["mid"][0]) ** 2 + (pts[:, 1] - r["mid"][1]) ** 2
            r["y"], r["est"] = int(yrs[d.argmin()]), 1
    (RAW / "undated.txt").write_text("\n".join(f"{n}\t{k / 2:.0f}" for n, k in undated.most_common()), encoding="utf-8")
    groups = collections.defaultdict(list)
    km_year = collections.Counter(); km_est = 0.0
    for r in recs:
        if not r["y"]:
            continue
        groups[(r["y"], r["en"] or r["name"], r["est"])].append(LineString(r["xy"]).simplify(0.004))
        km_year[r["y"]] += r["km"] / 2; km_est += r["est"] * r["km"] / 2
    feats = []
    for (y, n, est), lines in sorted(groups.items()):
        m = linemerge(lines) if len(lines) > 1 else lines[0]
        m = m.simplify(0.004)
        feats.append({"type": "Feature", "properties": {"y": y, "n": n, "est": est}, "geometry": mapping(m)})
    txt = json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":"), ensure_ascii=False)
    import re
    txt = re.sub(r"(\d+\.\d{4})\d+", r"\1", txt)
    (ROOT / "data" / "rail.geojson").write_text(txt, encoding="utf-8")
    total, rows = 0.0, []
    for y in range(min(km_year), LAST + 1):
        total += km_year.get(y, 0); rows.append({"year": y, "km": int(round(total, -1))})
    (ROOT / "data" / "rail.json").write_text(json.dumps({"years": rows, "note": "route km, estimated as half of track km"}, indent=1))
    all_km = sum(r["km"] for r in recs) / 2
    print(f"tracks {len(recs)}; route km dated {total:.0f} of {all_km:.0f}; of which year estimated {km_est:.0f}; undated {sum(undated.values()) / 2:.0f}")
    print("by year:", {r["year"]: r["km"] for r in rows})
    print("features", len(feats), "file MB", round(len(txt) / 1e6, 2))


if __name__ == "__main__":
    main()
