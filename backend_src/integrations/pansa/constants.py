from pathlib import Path


API = "https://api.dronemap.pansa.pl"
API_KEY = "4b705300-8dfa-11ee-b9d1-0242ac120002"
KML_MIME = "application/vnd.google-earth.kml+xml"
HEADERS = {
    "x-api-key": API_KEY,
    "Origin": "https://dronemap.pansa.pl",
    "Referer": "https://dronemap.pansa.pl/",
    "User-Agent": "Mozilla/5.0",
}
TIMEOUT_SECONDS = 120


INTERMEDIATE_CA = Path(__file__).with_name("gdig2.pem")


KML_NS = {'k': 'http://www.opengis.net/kml/2.2'}

STRENGTH = {'dra_i': 1, 'dra_rh': 2, 'dra_rm': 3, 'dra_rl': 4, 'dra_p': 5}
HEIGHT = {'dra_p': 0, 'dra_rh': 100, 'dra_rm': 30, 'dra_rl': 0, 'dra_i': None}

SUBTYPE_R = {
    'CTR': 'dra_rh', 'ATZ': 'dra_rh',
    'CTR6KM': 'dra_rm', 'ATZ6KM': 'dra_rm',
    'CTR1KM': 'dra_rl', 'ATZ1KM': 'dra_rl',
    'MCTR': 'dra_rl', 'MCTR2KM': 'dra_rl', 'D': 'dra_rl', 'TRA': 'dra_rl',
    'R': 'dra_rl', 'RPA': 'dra_rl',
}
