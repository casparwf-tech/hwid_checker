"""
Static mapping tables used by parsers and checkers.

Provides:
- EC Level category → HWID component type mapping  (used by device_checker)
- SKIP_CATEGORIES: categories with no HWID field (keyboard, cable, etc.)

Note: Country → HWID region code mapping is in core/checker/region_checker.py
      (_COUNTRY_TO_HWID), derived from Region code list_v2.5a.xls.
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# EC Level "Key Parts" category  →  HWID component type string
# None means the category has no HWID field and should be skipped.
# ---------------------------------------------------------------------------

EC_CATEGORY_TO_HWID_TYPE: dict[str, str | None] = {
    # CPU
    "cpu":                  "cpu",
    # Memory / DRAM
    "memory":               "dram",
    "dram":                 "dram",
    "ram":                  "dram",
    # Storage
    "ufs":                  "storage",
    "storage":              "storage",
    "emmc":                 "storage",
    "ssd":                  "storage",
    # Wireless
    "wlan":                 "wireless",
    "wifi":                 "wireless",
    "wireless":             "wireless",
    "wifi card":            "wireless",
    "wlan card":            "wireless",
    "communication card":   "wireless",
    # Cellular
    "wwan":                 "cellular",
    "wwan card":            "cellular",
    "lte":                  "cellular",
    # Display
    "panel":                "display_panel",
    "display":              "display_panel",
    # Battery
    "battery":              "battery",
    # Touchpad / Clickpad
    "touchpad pcba":        "touchpad",
    "touchpad":             "touchpad",
    "clickpad":             "touchpad",
    # Fingerprint
    "finger print":         "fingerprint",
    "fingerprint":          "fingerprint",
    # Camera
    "camera":               "camera",
    "y4 5m camera":         "camera",
    "ir camera":            "camera",
    # Explicitly skipped (no HWID field)
    "kyb_nb":               None,
    "keyboard":             None,
    "kb":                   None,
    "cable":                None,
    "thermal":              None,
    "thermal module":       None,
    "fan":                  None,
    "thermal pad":          None,
    "adapter":              None,
    "powercord":            None,
    "power cord":           None,
    "ac adapter":           None,
    "antenna":              None,
    "wlan antenna":         None,
    "wwan antenna":         None,
    "speaker":              None,
    "stylus":               None,
    "stylus/pen":           None,
    "pen":                  None,
}

# Categories that should be silently skipped (no result row emitted).
SKIP_CATEGORIES: set[str] = {
    "kyb_nb", "keyboard", "kb", "cable", "thermal", "fan", "thermal pad",
    "thermal module", "adapter", "powercord", "power cord", "ac adapter",
    "antenna", "wlan antenna", "wwan antenna", "speaker", "stylus",
    "stylus/pen", "pen",
}


def normalize_category(raw: str) -> str:
    """Collapse whitespace (including \\n from merged cells) and lowercase."""
    import re
    return re.sub(r"\s+", " ", raw).strip().lower()


def get_hwid_type(ec_category: str) -> str | None:
    """
    Map a raw EC Level category string to a HWID component type.

    Returns:
        str  – HWID type key  (e.g. "dram")
        None – should be skipped entirely
        "UNKNOWN" – present in EC Level but no mapping defined
    """
    key = normalize_category(ec_category)
    if key in EC_CATEGORY_TO_HWID_TYPE:
        return EC_CATEGORY_TO_HWID_TYPE[key]
    # Partial / fuzzy fallback
    for cat_key, hwid_type in EC_CATEGORY_TO_HWID_TYPE.items():
        if cat_key and cat_key in key:
            return hwid_type
    return "UNKNOWN"
