"""
Device checker.

Logic:
1. Build a lookup dict from AVL List  (key = LCFC PN).
2. For every EC Level component:
   a. Skip silently if its category has no HWID field (keyboard, etc.).
   b. If no AVL entry at all            → NOT_IN_AVL   (report, not skip)
   c. If AVL entry exists but not QUALIFIED → AVL_NOT_QUALIFIED (report per entry)
   d. If QUALIFIED but no Google AVL URL  → NO_AVL_ID  (needs manual check).
   e. Otherwise construct the HWID key and look up in the HWID database:
      - Found, status=supported         → OK
      - Found, status≠supported         → UNSUPPORTED
      - Not found (primary key miss)    → try MPN/part fallback
          * Fallback hit                → POSSIBLE_MATCH (warn, manual check)
          * Fallback miss               → MISSING

HWID key format:
    cpu             → cpu_{component_id}
    all others      → {type}_{component_id}_{qual_id}
"""
from __future__ import annotations
from ..models import ECComponent, AVLComponent, DeviceResult
from ..mappings import get_hwid_type, normalize_category, SKIP_CATEGORIES

_PM_CONTACT = " — Please contact the PM."


# ---------------------------------------------------------------------------
# Key construction
# ---------------------------------------------------------------------------

def _build_hwid_key(hwid_type: str, component_id: str, qual_id: str) -> str:
    if qual_id:
        return f"{hwid_type}_{component_id}_{qual_id}"
    return f"{hwid_type}_{component_id}"


# ---------------------------------------------------------------------------
# HWID lookup (handles #N slot suffixes)
# ---------------------------------------------------------------------------

def _lookup(
    hwid_key: str,
    hwid_type: str,
    hwid_components: dict,
) -> tuple[str, str]:
    """
    Search for hwid_key in hwid_components[hwid_type].

    The HWID DB uses keys like ``dram_5199_15673#2`` for different
    memory slots.  We compare without the ``#N`` suffix.
    If multiple slot entries exist, any 'supported' entry counts as OK.

    Returns:
        (check_status, db_status)
    """
    type_items: dict = hwid_components.get(hwid_type, {})
    base_key = hwid_key.split("#")[0]

    matched_entries = [
        entry for db_key, entry in type_items.items()
        if db_key.split("#")[0] == base_key
    ]
    if matched_entries:
        for entry in matched_entries:
            if entry.get("status") == "supported":
                return "OK", "supported"
        first_status = matched_entries[0].get("status", "unsupported")
        return "UNSUPPORTED", first_status

    return "MISSING", "-"


def _mpn_fallback(
    mpn: str,
    hwid_type: str,
    hwid_components: dict,
) -> str:
    """
    Try to find a HWID entry whose 'part' or 'name' value contains the MPN.
    Returns a note string if a possible match is found, else empty string.
    """
    if not mpn:
        return ""
    type_items = hwid_components.get(hwid_type, {})
    mpn_lower = mpn.lower()
    for db_key, entry in type_items.items():
        values = entry.get("values", {}) or {}
        part = (values.get("part") or values.get("name") or "").lower()
        if part and (mpn_lower in part or part in mpn_lower):
            db_status = entry.get("status", "unknown")
            return (
                f"Possible match by MPN: '{db_key}' "
                f"(DB status: {db_status}) — please verify manually"
            )
    return ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_devices(
    ec_components: list[ECComponent],
    avl_components: list[AVLComponent],
    hwid_components: dict,
) -> list[DeviceResult]:
    """
    Cross-check EC Level components against AVL List and HWID database.

    Args:
        ec_components:   All rows from the EC Level KPL sheet.
        avl_components:  All rows from the AVL List sheet (unfiltered).
        hwid_components: components dict from parse_hwid().

    Returns:
        List of DeviceResult, one per (EC component, AVL entry) pair that
        is relevant for HWID checking.  Silent skips are not included.
    """
    # Build AVL lookup: LCFC_PN → list[AVLComponent]
    avl_by_pn: dict[str, list[AVLComponent]] = {}
    for avl in avl_components:
        pn = avl.lcfc_pn.strip()
        if pn:
            avl_by_pn.setdefault(pn, []).append(avl)

    results: list[DeviceResult] = []

    for ec in ec_components:
        cat_norm = normalize_category(ec.category)

        # a. Skip categories with no HWID field
        if cat_norm in SKIP_CATEGORIES:
            continue

        hwid_type = get_hwid_type(ec.category)

        # b. Unknown category – report but don't crash
        if hwid_type == "UNKNOWN":
            results.append(DeviceResult(
                lcfc_pn=ec.lcfc_pn,
                category=ec.category,
                hwid_type="unknown",
                vendor=ec.vendor,
                description=ec.description,
                avl_status="-",
                google_avl_url="",
                hwid_key="",
                check_status="UNKNOWN_CATEGORY",
                note=f"No HWID type mapping for category '{ec.category}'",
            ))
            continue

        # None means explicitly skipped
        if hwid_type is None:
            continue

        pn = ec.lcfc_pn.strip()
        avl_entries = avl_by_pn.get(pn, [])

        # b. No AVL entry at all → report NOT_IN_AVL
        if not avl_entries:
            results.append(DeviceResult(
                lcfc_pn=pn,
                category=ec.category,
                hwid_type=hwid_type,
                vendor=ec.vendor,
                description=ec.description,
                avl_status="-",
                google_avl_url="",
                hwid_key="",
                check_status="NOT_IN_AVL",
                note="Component exists in EC Level but has no entry in AVL List" + _PM_CONTACT,
            ))
            continue

        for avl in avl_entries:
            # c. AVL entry exists but not QUALIFIED → report AVL_NOT_QUALIFIED
            if avl.avl_status.strip().upper() != "QUALIFIED":
                results.append(DeviceResult(
                    lcfc_pn=pn,
                    category=ec.category,
                    hwid_type=hwid_type,
                    vendor=ec.vendor,
                    description=ec.description,
                    avl_status=avl.avl_status,
                    google_avl_url=avl.google_avl_url,
                    hwid_key="",
                    check_status="AVL_NOT_QUALIFIED",
                    note=f"AVL status is '{avl.avl_status}', not QUALIFIED — check AVL List" + _PM_CONTACT,
                ))
                continue

            # d. QUALIFIED but no AVL URL
            if not avl.component_id:
                results.append(DeviceResult(
                    lcfc_pn=pn,
                    category=ec.category,
                    hwid_type=hwid_type,
                    vendor=ec.vendor,
                    description=ec.description,
                    avl_status=avl.avl_status,
                    google_avl_url=avl.google_avl_url,
                    hwid_key="",
                    check_status="NO_AVL_ID",
                    note="QUALIFIED but Google AVL URL is missing — manual check required" + _PM_CONTACT,
                ))
                continue

            # e. Normal path: look up in HWID DB
            hwid_key = _build_hwid_key(hwid_type, avl.component_id, avl.qual_id)
            check_status, db_status = _lookup(hwid_key, hwid_type, hwid_components)

            note = ""
            if check_status == "MISSING":
                # Try MPN fallback
                fallback_note = _mpn_fallback(avl.mpn, hwid_type, hwid_components)
                if fallback_note:
                    check_status = "POSSIBLE_MATCH"
                    note = fallback_note + _PM_CONTACT
                else:
                    note = f"Key '{hwid_key}' not found in HWID DB under type '{hwid_type}'" + _PM_CONTACT
            elif check_status == "UNSUPPORTED":
                note = f"'{hwid_key}' exists in HWID DB but status is not 'supported'" + _PM_CONTACT

            results.append(DeviceResult(
                lcfc_pn=pn,
                category=ec.category,
                hwid_type=hwid_type,
                vendor=ec.vendor,
                description=ec.description,
                avl_status=avl.avl_status,
                google_avl_url=avl.google_avl_url,
                hwid_key=hwid_key,
                check_status=check_status,
                hwid_db_status=db_status,
                note=note,
            ))

    return results
