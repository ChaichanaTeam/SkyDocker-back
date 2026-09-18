# Additional instruments:
# https://geojson.io/
# https://clupasq.github.io/h3-viewer/


IMPORT_GEOZONES = {
    "summary": "Import geo-zones from file",
    "description": "Imports geo-zones from an uploaded GeoJSON FeatureCollection "
                    "(multipart/form-data, field `file`).\n\n"
                    "Every feature must be a Polygon with `properties.type` from GeoZoneType. "
                    "`name` (or `tag`), `strength`, `height_agl` and `height_amsl` are optional. "
                    "Invalid features are skipped and reported in `errors` (first 20).\n\n"
                    "All zones are attached to the demo country (Poland). "
                    "Pass `?reset=true` to first delete all geo-zones of that country - "
                    "without it a repeated import creates duplicates.",
    "response_description": "Imported and skipped geo-zone counts with skip reasons",
    "responses": {
        200: { "description": "Geo-zones imported" },
        400: { "description": "Invalid JSON, not a FeatureCollection, no features or no valid geo-zones" }
    }
}
