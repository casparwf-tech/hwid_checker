"""
HWID Database parser.

Reads the YAML-format HWID database file used in Chromebook projects.
The file contains custom YAML tags (e.g. !region_field, !region_component)
which are handled gracefully by registering a multi-constructor.

Returns a dict with:
    project_name  : str
    region_codes  : list[str]          – all codes in encoded_fields.region_field
    components    : dict[type, dict]   – components[type][key] = {status, values}
"""
from __future__ import annotations
import yaml
from pathlib import Path


# ---------------------------------------------------------------------------
# Custom YAML tag handling
# ---------------------------------------------------------------------------

def _make_loader() -> type:
    """Return a SafeLoader subclass that ignores unknown tags."""

    class _HWIDLoader(yaml.SafeLoader):
        pass

    def _handle_unknown_tag(loader: yaml.Loader, tag_suffix: str, node: yaml.Node):
        if isinstance(node, yaml.SequenceNode):
            return loader.construct_sequence(node, deep=True)
        if isinstance(node, yaml.MappingNode):
            return loader.construct_mapping(node, deep=True)
        return loader.construct_scalar(node)

    yaml.add_multi_constructor("!", _handle_unknown_tag, Loader=_HWIDLoader)
    return _HWIDLoader


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_hwid(filepath: str) -> dict:
    """
    Parse a HWID database YAML file.

    Returns:
        {
            "project_name": str,
            "region_codes": list[str],
            "components":   {
                "<type>": {
                    "<hwid_key>": {"status": str, "values": dict},
                    ...
                },
                ...
            }
        }
    """
    loader_cls = _make_loader()

    with open(filepath, "r", encoding="utf-8") as fh:
        data = yaml.load(fh, Loader=loader_cls)

    if not isinstance(data, dict):
        raise ValueError("HWID file did not parse as a YAML mapping.")

    result: dict = {
        "project_name": Path(filepath).name,
        "region_codes": [],
        "components": {},
    }

    # ---- region codes ----
    encoded = data.get("encoded_fields", {}) or {}
    region_field = encoded.get("region_field", [])
    if isinstance(region_field, list):
        result["region_codes"] = [
            str(code).strip() for code in region_field if code
        ]

    # ---- components ----
    components_section = data.get("components", {}) or {}
    for comp_type, comp_data in components_section.items():
        if comp_type == "region":
            # region is managed separately
            continue
        if not isinstance(comp_data, dict):
            continue

        items = comp_data.get("items", {})
        if not isinstance(items, dict):
            continue

        result["components"][comp_type] = {}
        for key, entry in items.items():
            if not isinstance(entry, dict):
                continue
            result["components"][comp_type][str(key)] = {
                "status": str(entry.get("status", "unknown")),
                "values": entry.get("values", {}) or {},
            }

    return result
