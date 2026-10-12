import collections
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from loguru import logger
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

from .constants import HEIGHT, KML_NS, STRENGTH, SUBTYPE_R


def classify(name: str, restriction: str, typ: str) -> str:
    if restriction == 'DRA-P' or typ == 'DRAP':
        return 'dra_p'
    m = re.match(r'\W*DRA-(RL|RM|RH)\b', name)
    if m:
        return 'dra_' + m[1].lower()
    if restriction == 'DRA-I' or typ == 'DRAI':
        return 'dra_i'
    if restriction == 'DRA-R':
        return SUBTYPE_R.get(typ, 'dra_rl')
    if typ == 'DRAR':
        return 'dra_rl'
    return 'unknown'


def kml_to_geojson(src: Path, dst: Path) -> dict[str, Any]:
    out, stats, problems = [], collections.Counter(), []
    for pm in ET.parse(src).getroot().iter('{%s}Placemark' % KML_NS['k']):
        name = pm.findtext('k:name', '', KML_NS).strip()
        desc = pm.findtext('k:description', '', KML_NS)
        d = re.match(r'Restriction: (.*?), Type: (.*?), Min', desc)
        zt = classify(name, d[1], d[2])
        for poly in pm.iter('{%s}Polygon' % KML_NS['k']):
            txt = poly.find('.//k:outerBoundaryIs//k:coordinates', KML_NS).text
            ring = [[float(v) for v in p.split(',')[:2]] for p in txt.split()]
            if ring[0] != ring[-1]:
                ring.append(ring[0])
            if len(ring) < 4:
                problems.append(name); continue
            g = Polygon(ring)
            if not g.is_valid:
                g = g.buffer(0)
                if g.geom_type == 'MultiPolygon':
                    g = max(g.geoms, key=lambda p: p.area)
                problems.append(name)
            g = orient(g, 1.0)
            ring = [[round(x, 7), round(y, 7)] for x, y in g.exterior.coords]
            holes = [[[round(x, 7), round(y, 7)] for x, y in r.coords] for r in g.interiors]
            hm = re.search(r'Min: (\d+) ft, Max: (\d+) ft', desc)
            out.append({
                'type': 'Feature',
                'properties': {
                    'tag': name,
                    'type': zt,
                    'strength': STRENGTH.get(zt, 0),
                    'height_agl': HEIGHT.get(zt),
                    'source_restriction': d[1],
                    'source_type': d[2],
                    'min_ft': int(hm[1]) if hm else None,
                    'max_ft': int(hm[2]) if hm else None,
                },
                'geometry': {'type': 'Polygon', 'coordinates': [ring] + holes},
            })
            stats[(d[1], d[2], zt)] += 1

    with open(dst, 'w', encoding='utf-8') as f:
        json.dump({'type': 'FeatureCollection', 'features': out}, f, ensure_ascii=False)

    types = collections.Counter(z['properties']['type'] for z in out)
    logger.info(f"PANSA KML converted: {len(out)} zones, fixed geometries: {problems}")
    for k, v in sorted(stats.items()):
        logger.debug(f"{k} {v}")

    return {
        "zones": len(out),
        "fixed": problems,
        "types": dict(types),
    }
