# expected shape of a holiday object returned by Nager.Date

HOLIDAY_SCHEMA = {
    "type": "object",
    "required": ["date", "localName", "name", "countryCode", "fixed", "global", "types"],
    "properties": {
        "date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
        "localName": {"type": "string", "minLength": 1},
        "name": {"type": "string", "minLength": 1},
        "countryCode": {"type": "string", "pattern": "^[A-Z]{2}$"},
        "fixed": {"type": "boolean"},
        # False for holidays that apply only to some subdivisions.
        "global": {"type": "boolean"},
        # null for nationwide holidays, ISO 3166-2 codes otherwise.
        "counties": {"type": ["array", "null"], "items": {"type": "string"}},
        "launchYear": {"type": ["integer", "null"]},
        "types": {"type": "array", "items": {"type": "string"}, "minItems": 1},
    },
}
