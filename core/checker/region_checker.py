"""
Region checker — v2 (static mapping from Region code list_v2.5a.xls).

Logic:
1. Load the pre-built country → [hwid_codes] mapping derived from
   "Region code list_v2.5a.xls" (sheet: "Region code").
2. For every OD country name:
   a. Normalise the name and look it up in the mapping table.
   b. If not found → UNKNOWN_MAPPING (manual check needed).
   c. If found, check which of the expected codes are present in the
      HWID database's region_field:
      - All expected codes present  → OK
      - Some or all missing         → MISSING  (lists which are absent)
"""
from __future__ import annotations
import re
from ..models import ODCountry, RegionResult

_SWPM_CONTACT = " — Please contact SWPM."


# ---------------------------------------------------------------------------
# Static mapping built from Region code list_v2.5a.xls (sheet "Region code")
# key = normalised country name (lowercase, stripped)
# value = list of required HWID region codes
# ---------------------------------------------------------------------------
_COUNTRY_TO_HWID: dict[str, list[str]] = {
    # Item 1 — Canada (grouped by ISO alpha-2 CA)
    "canada":                       ["ca.fr", "ca.ansi", "ca.hybrid"],
    "canada (french keyboard)":     ["ca.fr"],
    "canada (us keyboard)":         ["ca.ansi"],
    "canada (hybrid)":              ["ca.hybrid"],
    # Item 2 — Nordics (group)
    "nordics":                      ["nordic"],
    "nordic":                       ["nordic"],
    "finland":                      ["fi"],
    "sweden":                       ["nordic"],
    "norway":                       ["nordic"],
    "denmark":                      ["nordic"],
    # Item 3 — France
    "france":                       ["fr"],
    # Item 4 — Germany
    "germany":                      ["de"],
    # Item 5 — India
    "india":                        ["in"],
    # Item 6 — Russia
    "russia":                       ["ru"],
    # Item 7 — Singapore
    "singapore":                    ["sg"],
    # Item 8 — Switzerland
    "switzerland":                  ["ch"],
    # Item 9 — UK Group
    "uk_group":                     ["gb.usext"],
    "uk group":                     ["gb.usext"],
    "uk":                           ["gb"],
    "united kingdom":               ["gb"],
    "ireland":                      ["ie"],
    # Item 10 — USA
    "usa":                          ["us"],
    "united states":                ["us"],
    "us":                           ["us"],
    # Item 11 — LA Group
    "la group":                     ["latam-es-419"],
    "latin america":                ["latam-es-419"],
    "mexico (edu only)":            ["latam-es-419"],
    "mexico":                       ["latam-es-419"],
    "peru":                         ["latam-es-419"],
    "colombia":                     ["latam-es-419"],
    # Item 12 — Chile
    "chile":                        ["latam-es-419"],
    # Item 13 — Spain
    "spain":                        ["es"],
    # Item 14 — Belgium
    "belgium":                      ["be"],
    # Item 15 — Italy
    "italy":                        ["it"],
    # Item 16 — Philippines
    "philippines":                  ["ph"],
    # Item 17 — Poland
    "poland":                       ["pl"],
    # Item 18 — Czech-Slovakia Group
    "czech-slovakia(group)":        ["cz"],
    "czech-slovakia group":         ["cz"],
    "czech republic":               ["cz"],
    "czechia":                      ["cz"],
    "slovakia":                     ["sk"],
    # Item 19 — South Africa
    "south africa":                 ["za.us"],
    # Item 20 — Saudi Arabia
    "saudi arabia":                 ["sa"],
    # Item 21 — UAE Group
    "uae(united arab emirates) group": ["ae"],
    "uae group":                    ["ae"],
    "uae":                          ["ae"],
    "united arab emirates":         ["ae"],
    "qatar":                        ["gcc"],
    "kuwait":                       ["kw"],
    "bahrain":                      ["gcc"],
    "oman":                         ["gcc"],
    # Item 22 — Israel
    "israel":                       ["il"],
    # Item 23 — Netherlands
    "netherlands":                  ["nl"],
    # Item 24 — Romania
    "romania":                      ["ro"],
    # Item 25 — Australia
    "australia":                    ["au"],
    # Item 26 — New Zealand
    "new zealand":                  ["nz"],
    # Item 27 — Indonesia
    "indonesia":                    ["id"],
    # Item 28 — Portugal
    "portugal":                     ["pt"],
    # Item 29 — Argentina
    "argentina":                    ["ar"],
    # Item 30 — Japan
    "japan":                        ["jp", "jp.us"],
    # Item 31 — Türkiye / Turkey
    "türkiye":                      ["tr"],
    "turkiye":                      ["tr"],
    "turkey":                       ["tr"],
    # Item 32 — Puerto Rico
    "puerto rico":                  ["pr"],
    # Item 33 — Thailand
    "thailand":                     ["th"],
    # Item 34 — Taiwan
    "taiwan":                       ["tw"],
    # Item 35 — Hongkong
    "hongkong":                     ["hk"],
    "hong kong":                    ["hk"],
    # Item 36 — Malaysia
    "malaysia":                     ["my"],
    # Item 37 — South Korea
    "south korea":                  ["kr"],
    "korea":                        ["kr"],
    # Item 38 — Iceland
    "iceland":                      ["is"],
    # Item 39 — Brazil
    "brazil":                       ["br.abnt"],
    # Item 40 — Austria
    "austria":                      ["at"],
    # Item 41 — Bulgaria
    "bulgaria":                     ["bg"],
    # Item 42 — Greece
    "greece":                       ["gr"],
    # Item 43 — Vietnam
    "vietnam":                      ["vn"],
    # Item 44 — Croatia/Slovenia Group
    "croatia_slovenia(group)":      ["hr"],
    "croatia slovenia group":       ["hr"],
    "croatia":                      ["hr"],
    "egypt":                        ["eg"],
    # Item 45 — Kazakhstan
    "kazakhstan":                   ["kz"],
    # Item 46 — Jordan
    "jordan":                       ["jo"],
    # Item 47 — Guernsey
    "guernsey":                     ["gg"],
    # Item 48 — Ukraine
    "ukraine":                      ["ua"],
    # Item 49 — Caribbean Group
    "caribbean_group":              ["tt"],
    "caribbean group":              ["tt"],
    "trinidad & tobago":            ["tt"],
    "trinidad and tobago":          ["tt"],
    # Item 50 — CA Group (Central America)
    "ca group":                     ["latam-es-419", "us"],
    "belize":                       ["bz"],
    "el salvador":                  ["sv"],
    # Item 51 — Pakistan (no HWID code per xls, mark as unknown)
    "uruguay":                      ["uy"],
}


# ---------------------------------------------------------------------------
# Normalise helper
# ---------------------------------------------------------------------------

def _normalise(name: str) -> str:
    """Lowercase, strip, collapse multiple spaces."""
    return re.sub(r"\s+", " ", name.strip().lower())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_regions(
    countries: list[ODCountry],
    hwid_region_codes: list[str],
) -> list[RegionResult]:
    """
    Check that every OD shipping country has all its expected HWID region
    codes present in the database.

    The expected codes are looked up from the static _COUNTRY_TO_HWID table
    (derived from Region code list_v2.5a.xls).

    Args:
        countries:         All countries from the OD Country List sheet.
        hwid_region_codes: All codes from encoded_fields.region_field in HWID DB.

    Returns:
        One RegionResult per OD country.
    """
    hwid_set = set(hwid_region_codes)
    results: list[RegionResult] = []

    for country in countries:
        name = country.name.strip()
        key = _normalise(name)

        expected_codes = _COUNTRY_TO_HWID.get(key)

        if expected_codes is None:
            results.append(RegionResult(
                country_name=name,
                geo=country.geo,
                possible_codes=[],
                status="UNKNOWN_MAPPING",
                note=(
                    f"'{name}' not found in region mapping table. "
                    "Please check Region code list_v2.5a.xls or add manually."
                    + _SWPM_CONTACT
                ),
            ))
            continue

        missing = [c for c in expected_codes if c not in hwid_set]
        present = [c for c in expected_codes if c in hwid_set]

        if not missing:
            results.append(RegionResult(
                country_name=name,
                geo=country.geo,
                possible_codes=expected_codes,
                status="OK",
                matched_code=", ".join(present),
            ))
        else:
            results.append(RegionResult(
                country_name=name,
                geo=country.geo,
                possible_codes=expected_codes,
                status="MISSING",
                matched_code=", ".join(present) if present else "",
                note=(
                    f"Missing region code(s): {', '.join(missing)}"
                    + (f" | Present: {', '.join(present)}" if present else "")
                    + _SWPM_CONTACT
                ),
            ))

    return results
