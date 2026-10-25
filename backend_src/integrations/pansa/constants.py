from pathlib import Path


LOGIN_PATH = "/v1/front/login"
ZONES_PATH = "/v1/zones"
ZONE_TYPES_PATH = "/v1/zones/types"
ACTIVATIONS_PATH = "/v1/activ/activations"
NOTAMS_PATH = "/v1/notams"

TIMEOUT_SECONDS = 120


# api.dronemap.pansa.pl does not send the intermediate certificate of its chain
INTERMEDIATE_CA = Path(__file__).with_name("gdig2.pem")
