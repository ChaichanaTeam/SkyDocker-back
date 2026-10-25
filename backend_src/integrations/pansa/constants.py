from pathlib import Path


LOGIN_PATH = "/v1/front/login"
ZONES_PATH = "/v1/zones"
ZONE_TYPES_PATH = "/v1/zones/types"
ACTIVATIONS_PATH = "/v1/activ/activations"
NOTAMS_PATH = "/v1/notams"
KML_PATH = "/v1/kml"

KML_MIME = "application/vnd.google-earth.kml+xml"
TIMEOUT_SECONDS = 120


# api.dronemap.pansa.pl does not send the intermediate certificate of its chain
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
