#Expected shape of a country object returned by Nager.Date.

# a country as it appears nested inside another country's "borders" list
BORDER_SCHEMA = {
    "type": "object",
    "required": ["commonName", "officialName", "countryCode", "region"],
    "properties": {
        "commonName": {"type": "string", "minLength": 1},
        "officialName": {"type": "string", "minLength": 1},
        "countryCode": {"type": "string", "pattern": "^[A-Z]{2}$"},
        "region": {"type": "string", "minLength": 1},
        "nativeName": {"type": ["string", "null"]},
    },
}

# the full /CountryInfo response
COUNTRY_SCHEMA = {
    "type": "object",
    "required": ["commonName", "officialName", "countryCode", "region", "borders"],
    "properties": {
        "commonName": {"type": "string", "minLength": 1},
        "officialName": {"type": "string", "minLength": 1},
        "countryCode": {"type": "string", "pattern": "^[A-Z]{2}$"},
        "region": {"type": "string", "minLength": 1},
        "nativeName": {"type": ["string", "null"]},
        # Landlocked-by-sea countries return an empty array, not null.
        "borders": {"type": ["array", "null"], "items": BORDER_SCHEMA},
    },
}
