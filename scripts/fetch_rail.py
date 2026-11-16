"""Download China's high-speed rail tracks from OpenStreetMap (through the Overpass service).

Step 1 asks for the tags of every track tagged railway=rail and highspeed=yes inside China.
Step 2 asks for the shapes of those tracks by id, 1,500 at a time, which is light work for the
server. Every answer is kept on disk, so a rerun only fetches what is missing. The result is
data/raw/rail/ways_geom.json (large, not committed).
"""
import json, time
from pathlib import Path
import requests

RAW = Path(__file__).parent.parent / "data" / "raw" / "rail"
SERVERS = ["https://overpass.openstreetmap.fr/api/interpreter", "https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter",
           "https://overpass.kumi.systems/api/interpreter"]
TAGS_QUERY = """[out:json][timeout:300];
area["ISO3166-1"="CN"][admin_level=2]->.a;
way(area.a)["railway"="rail"]["highspeed"="yes"];
out tags;"""
BATCH = 1500


def ask(q):
    for attempt in range(9):
        url = SERVERS[attempt % len(SERVERS)]
        try:
            r = requests.post(url, data={"data": q}, timeout=120, headers={"User-Agent": "timelapse-map-build/0.1"})
            if r.status_code == 200 and r.content.lstrip()[:1] == b"{":
                return r.json()
            print("  ", url.split("/")[2], r.status_code, flush=True)
        except requests.RequestException as e:
            print("  ", url.split("/")[2], type(e).__name__, flush=True)
        time.sleep(10)
    raise SystemExit("all servers failed; rerun later, finished parts are kept")


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    tags_file = RAW / "ways_tags.json"
    if not tags_file.exists():
        tags_file.write_text(json.dumps(ask(TAGS_QUERY)), encoding="utf-8")
    tagged = {e["id"]: e.get("tags", {}) for e in json.loads(tags_file.read_text(encoding="utf-8"))["elements"]}
    ids = sorted(tagged)
    ways = []
    for k in range(0, len(ids), BATCH):
        p = RAW / f"geom_{k // BATCH:03d}.json"
        if not p.exists():
            d = ask(f"[out:json][timeout:200];way(id:{','.join(map(str, ids[k:k + BATCH]))});out skel geom;")
            p.write_text(json.dumps(d), encoding="utf-8")
            print("part", k // BATCH, "of", (len(ids) - 1) // BATCH, len(d["elements"]), flush=True)
            time.sleep(2)
        for el in json.loads(p.read_text(encoding="utf-8"))["elements"]:
            el["tags"] = tagged.get(el["id"], {})
            ways.append(el)
    (RAW / "ways_geom.json").write_text(json.dumps({"elements": ways}), encoding="utf-8")
    print("ways", len(ways), "of", len(ids))


if __name__ == "__main__":
    main()
