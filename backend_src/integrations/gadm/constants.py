import pycountry


# GADM 4.1 country outlines (level 0) as GeoJSON in lon/lat, about 10 m precision
BASE_URL = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/"

TIMEOUT_SECONDS = 60

# GADM data is free for non-commercial use with a credit line
ATTRIBUTION = "GADM 4.1, gadm.org"


def file_name(country_tag: str) -> str:
    """GADM names files by ISO 3166-1 alpha-3, e.g. gadm41_POL_0.json for PL."""
    country = pycountry.countries.get(alpha_2=country_tag.upper())
    if country is None:
        raise ValueError(f"Unknown country code {country_tag}")

    return f"gadm41_{country.alpha_3}_0.json"
