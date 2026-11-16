# China Timelapse

A map of China seen from space, with a time slider. It shows night lights, one picture a year from 1992 to 2021, and the high-speed rail network drawing itself in as each line opened. Built-up land, metro systems and airports are planned.

Live map: https://adakin97.github.io/china-timelapse/

## What is here

- `index.html`: the whole map page. One file, no build step. It uses MapLibre.
- `data/lights/<year>.webp`: one picture of night lights per year, transparent where dark.
- `data/years.json`: the map window and the lit area for each year.
- `data/rail.geojson`: high-speed rail lines, each with its opening year. `data/rail.json`: length open by year.
- `data/china.geojson`, `data/land.geojson`: borders and coastline.
- `scripts/`: the Python that produced the data files.

## Data and credit

- **Night lights:** Li, X., Zhou, Y., Zhao, M. and Zhao, X. (2020). A harmonized global nighttime light dataset 1992-2018. *Scientific Data* 7, 168. https://doi.org/10.1038/s41597-020-0510-y, with the authors' extension to 2021. Read from the copy in the Google Earth Engine community catalogue (`projects/sat-io/open-datasets/Harmonized_NTL`).
- **High-speed rail:** © OpenStreetMap contributors, Open Database Licence (ODbL), https://www.openstreetmap.org/copyright. `data/rail.geojson` is derived from OpenStreetMap and is offered under the same licence.
- **Borders:** Aliyun DataV boundary service (`geo.datav.aliyun.com/areas_v3/bound/100000_full.json`). They follow China's official standard map. Several of these boundaries are disputed.
- **Coastline:** Natural Earth, 1:50m land, public domain.

The data sets are the work of their authors. This repository adds the pipeline that cuts them to China, the yearly pictures and the map.

## Rebuild the data

Needs Python with `earthengine-api`, `numpy`, `pillow`, `pyproj`, `requests` and `shapely`, and a Google Earth Engine account (set the project name in `scripts/config.py`).

    # borders and coastline: download the three source files into data/raw/src/ first
    #   china_full.json     https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json
    #   china_outline.json  https://geo.datav.aliyun.com/areas_v3/bound/100000.json
    #   ne_50m_land.geojson https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_land.geojson
    python scripts/build_boundaries.py

    python scripts/fetch_lights.py     # one grid per year into data/raw/ (about 50 MB each, not committed)
    python scripts/build_lights.py     # pictures and years.json

    python scripts/fetch_rail.py       # high-speed tracks from OpenStreetMap into data/raw/rail/
    python scripts/build_rail.py       # rail.geojson and rail.json

## View it locally

    python -m http.server 8000

then open http://localhost:8000.

## Known limits

- Each lights picture is a three-year weighted average centred on its year. The raw yearly grids flicker when played as a film, because different satellites flew in different years.
- Faint light (below 10 on the 0 to 63 scale) is not drawn, because the newer sensor sees glow the older one could not.
- Rail opening years are volunteers' tags in OpenStreetMap. About 70% of tracks carry one. Tracks without take the year of the nearest dated track on the same line, and 25 lines with no dated track at all use a hand-entered table in `scripts/build_rail.py` that still needs checking against a second source. About 1,100 km of route has no year and is left out.
- Rail length is half the mapped track length, as an estimate of route length. It comes out about 5% below the officially reported network for 2021.
- OpenStreetMap's high-speed tag includes lines of 200 km/h and above.
- Two generations of satellite sensor are joined between 2013 and 2014. The source data corrects for this, but a small step can remain.
- The older sensor saturates in city centres, so the brightest cores do not get brighter in the pictures.
- The pictures are about 1.7 km per pixel. They are meant for the national view, not street level.
