"""
Data models for HWID Checker.
All data classes are pure Python with no UI or I/O dependencies.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------

@dataclass
class ODCountry:
    """A single shipping country parsed from the OD Country List."""
    name: str          # e.g. "Japan"
    geo: str = ""      # e.g. "AP"


@dataclass
class ECComponent:
    """A component row from the EC Level KPL sheet."""
    category: str      # raw text, e.g. "CPU", "Memory", "WLAN"
    vendor: str
    description: str
    lbg_pn: str
    lcfc_pn: str       # join key


@dataclass
class AVLComponent:
    """A component row from the AVL List sheet."""
    category: str      # raw text (forward-filled)
    vendor: str
    mpn: str           # manufacturer part number
    lcfc_pn: str       # join key
    lnv_pn: str
    avl_status: str    # e.g. "QUALIFIED", "DRAFT"
    google_avl_url: str
    component_id: str = ""   # extracted from URL
    qual_id: str = ""        # extracted from URL


# ---------------------------------------------------------------------------
# Result models
# ---------------------------------------------------------------------------

@dataclass
class RegionResult:
    """Check result for a single OD country."""
    country_name: str
    geo: str
    possible_codes: list[str]    # candidate region codes from mapping table
    status: str                  # OK | MISSING | UNKNOWN_MAPPING
    matched_code: str = ""       # the code that matched (if OK)
    note: str = ""


@dataclass
class DeviceResult:
    """Check result for a single EC+AVL component pair."""
    lcfc_pn: str
    category: str          # raw EC Level category
    hwid_type: str         # normalized, e.g. "dram", "cpu"
    vendor: str
    description: str
    avl_status: str        # raw AVL status
    google_avl_url: str
    hwid_key: str          # constructed key used for lookup, e.g. "dram_5199_15673"
    # Check outcome
    check_status: str      # OK | MISSING | UNSUPPORTED | NO_AVL_ID |
                           # POSSIBLE_MATCH | UNKNOWN_CATEGORY |
                           # NOT_IN_AVL | AVL_NOT_QUALIFIED
    hwid_db_status: str = ""   # actual "status" value in HWID DB, or "-"
    note: str = ""


# ---------------------------------------------------------------------------
# Aggregate report
# ---------------------------------------------------------------------------

@dataclass
class CheckReport:
    """Full check report produced by one run."""
    project_name: str
    run_time: str
    region_results: list[RegionResult] = field(default_factory=list)
    device_results: list[DeviceResult] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Summary helpers
    # ------------------------------------------------------------------

    def region_summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for r in self.region_results:
            counts[r.status] = counts.get(r.status, 0) + 1
        return counts

    def device_summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for d in self.device_results:
            counts[d.check_status] = counts.get(d.check_status, 0) + 1
        return counts

    def has_issues(self) -> bool:
        """Return True if any non-OK / non-skip issues found."""
        bad = {
            "MISSING", "UNSUPPORTED", "NO_AVL_ID", "POSSIBLE_MATCH",
            "UNKNOWN_MAPPING", "UNKNOWN_CATEGORY",
            "NOT_IN_AVL", "AVL_NOT_QUALIFIED",
        }
        return (
            any(r.status in bad for r in self.region_results)
            or any(d.check_status in bad for d in self.device_results)
        )
