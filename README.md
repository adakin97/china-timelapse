# China Timelapse

A map of China seen from space, with a time slider. The first layer shows night lights, one picture a year from 1992 to 2021. Built-up land, high-speed rail, metro systems and airports are planned.

Live map: https://adakin97.github.io/china-timelapse/

## What is here

- `index.html`: the whole map page. One file, no build step. It uses MapLibre.
- `data/lights/<year>.webp`: one picture of night lights per year, transparent where dark.
- `data/years.json`: the map window and the lit area for each year.
- `data/china.geojson`, `data/land.geojson`: borders and coastline.
- `scripts/`: the Python that produced the data files.

## Data and credit

- **Night lights:** Li, X., Zhou, Y., Zhao, M. and Zhao, X. (2020). A harmonized global nighttime light dataset 1992-2018. *Scientific Data* 7, 168. https://doi.org/10.1038/s41597-020-0510-y, with the authors' extension to 2021. Read from the copy in the Google Earth Engine community catalogue (`projects/sat-io/open-datasets/Harmonized_NTL`).
- **Borders:** Aliyun DataV boundary service (`geo.datav.aliyun.com/areas_v3/bound/100000_full.json`). They follow China's official standard map. Several of these boundaries are disputed.
- **Coastline:** Natural Earth, 1:50m land, public domain.

The data sets are the work of their authors. This repository adds the pipeline that cuts them to China, the yearly pictures and the map.

## Rebuild the data

Needs Python with `earthengine-api`, `numpy`, `pillow`, `requests` and `shapely`, and a Google Earth Engine account (set the project name in `scripts/config.py`).

    # borders and coastline: download the three source files into data/raw/src/ first
    #   china_full.json     https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json
    #   china_outline.json  https://geo.datav.aliyun.com/areas_v3/bound/100000.json
    #   ne_50m_land.geojson https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_land.geojson
    python scripts/build_boundaries.py

    python scripts/fetch_lights.py     # one grid per year into data/raw/ (about 50 MB each, not committed)
    python scripts/build_lights.py     # pictures and years.json

## View it locally

    python -m http.server 8000

then open http://localhost:8000.

## Known limits

- Two generations of satellite sensor are joined between 2013 and 2014. The source data corrects for this, but a small step can remain.
- The older sensor saturates in city centres, so the brightest cores do not get brighter in the pictures.
- The pictures are about 1.7 km per pixel. They are meant for the national view, not street level.
