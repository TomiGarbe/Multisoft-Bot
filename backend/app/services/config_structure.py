from __future__ import annotations

from copy import deepcopy
from typing import Any

BASE_SECTION_ORDER = ("identity", "tone", "rules", "objectives", "data_collection")


def default_config_document() -> dict[str, Any]:
    return {
        "version": 1,
        "sections": [
            {
                "id": "identity",
                "type": "identity",
                "label": "Identity",
                "enabled": True,
                "priority": 100,
                "fields": {
                    "bot_name": "",
                    "company_name": "",
                    "industry": "",
                    "language": "es",
                    "location": "",
                    "description": "",
                    "website": "",
                    "socials": [{"network": "", "url": ""}],
                },
                "custom_fields": [],
                "notes": "",
            },
            {
                "id": "tone",
                "type": "tone",
                "label": "Tone",
                "enabled": True,
                "priority": 90,
                "fields": {
                    "tone": "",
                    "formality": "",
                    "response_length": "",
                    "emoji_usage": "",
                    "style_rules": [],
                    "conversation_examples": [],
                },
                "custom_fields": [],
                "notes": "",
            },
            {
                "id": "rules",
                "type": "rules",
                "label": "Rules",
                "enabled": True,
                "priority": 95,
                "fields": {
                    "global_rules": [],
                    "business_rules": [],
                    "safety_rules": [],
                },
                "custom_fields": [],
                "notes": "",
            },
            {
                "id": "objectives",
                "type": "objective",
                "label": "Objectives",
                "enabled": True,
                "priority": 85,
                "custom_fields": [],
                "notes": "",
                "entries": [
                    {
                        "id": "",
                        "name": "",
                        "enabled": True,
                        "applies_to": ["{{user.type}}"],
                        "objective": "",
                        "description": "",
                        "success_condition": "",
                        "guidelines": [],
                        "rules": [],
                        "custom_fields": [],
                        "notes": "",
                    }
                ],
            },
            {
                "id": "data_collection",
                "type": "data_collection",
                "label": "Data Collection",
                "enabled": True,
                "priority": 80,
                "custom_fields": [],
                "notes": "",
                "entries": [
                    {
                        "id": "",
                        "name": "",
                        "enabled": True,
                        "applies_to": ["{{user.type}}"],
                        "display_field": "",
                        "fields": [
                            {
                                "key": "",
                                "label": "",
                                "type": "text",
                                "description": "",
                                "examples": [],
                                "required": False,
                                "validation_hint": "",
                                "is_name_field": False,
                            }
                        ],
                        "custom_fields": [],
                        "notes": "",
                    }
                ],
            },
        ],
    }


def _to_section_map(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sections = config.get("sections")
    if not isinstance(sections, list):
        return {}
    section_map: dict[str, dict[str, Any]] = {}
    for section in sections:
        if not isinstance(section, dict):
            continue
        section_id = section.get("id")
        if isinstance(section_id, str) and section_id:
            section_map[section_id] = section
    return section_map


def normalize_config_document(raw_config: Any) -> dict[str, Any]:
    base = default_config_document()
    if not isinstance(raw_config, dict):
        return base

    if isinstance(raw_config.get("sections"), list):
        config = deepcopy(raw_config)
        config.setdefault("version", 1)
        return config

    section_map = _to_section_map(base)
    legacy = raw_config

    if isinstance(legacy.get("identity"), dict):
        section_map["identity"]["fields"] = legacy["identity"]
    if isinstance(legacy.get("tone"), dict):
        section_map["tone"]["fields"] = legacy["tone"]
    if isinstance(legacy.get("rules"), dict):
        rules_fields = dict(legacy["rules"])
        if "rules" in rules_fields and isinstance(rules_fields.get("rules"), list):
            rules_fields["global_rules"] = rules_fields.get("global_rules") or rules_fields.get("rules")
            rules_fields.pop("rules", None)
        section_map["rules"]["fields"] = rules_fields
    if isinstance(legacy.get("objectives"), list):
        section_map["objectives"]["entries"] = legacy["objectives"]
    data_collection = legacy.get("data_collection")
    if isinstance(data_collection, list):
        section_map["data_collection"]["entries"] = data_collection
    elif isinstance(data_collection, dict):
        section_map["data_collection"]["entries"] = [data_collection]

    base["version"] = legacy.get("version", 1) if isinstance(legacy.get("version"), int) else 1
    base["sections"] = [section_map[key] for key in BASE_SECTION_ORDER if key in section_map]
    return base


def section_by_id(config: dict[str, Any], section_id: str) -> dict[str, Any]:
    return _to_section_map(normalize_config_document(config)).get(section_id, {})


def section_fields(config: dict[str, Any], section_id: str) -> dict[str, Any]:
    section = section_by_id(config, section_id)
    fields = section.get("fields")
    return fields if isinstance(fields, dict) else {}


def section_entries(config: dict[str, Any], section_id: str) -> list[dict[str, Any]]:
    section = section_by_id(config, section_id)
    entries = section.get("entries")
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if isinstance(entry, dict)]
