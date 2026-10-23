#!/usr/bin/env python3
"""Migrate Minecraft 1.20.1 advancement block-use triggers to the 1.20 data format."""
from pathlib import Path
import json
import sys

ROOT = Path(sys.argv[1]).resolve()
ADV_DIR = ROOT / "src/main/resources/data/sporenwerk/advancements"
CHANGED = []
ISSUES = []

def location_check(predicate):
    return {"condition": "minecraft:location_check", "predicate": predicate}

def match_tool(predicate):
    return {"condition": "minecraft:match_tool", "predicate": predicate}

def migrate_criterion(criterion):
    trigger = criterion.get("trigger")
    conditions = criterion.get("conditions")
    if not isinstance(conditions, dict):
        return False

    if trigger == "minecraft:placed_block":
        # Since 1.20, placed_block uses conditions.location as an array of loot predicates.
        legacy_keys = {"block", "item", "state"}
        location = conditions.get("location")
        has_legacy = bool(legacy_keys.intersection(conditions)) or isinstance(location, dict)
        if not has_legacy:
            return False

        predicates = list(location) if isinstance(location, list) else []
        if isinstance(location, dict):
            predicates.append(location_check(location))

        block = conditions.pop("block", None)
        state = conditions.pop("state", None)
        item = conditions.pop("item", None)

        if block is not None and state is not None:
            block_name = block if isinstance(block, str) else None
            if block_name is None:
                predicates.append(location_check({"block": block, "state": state}))
            else:
                predicates.append({
                    "condition": "minecraft:block_state_property",
                    "block": block_name,
                    "properties": state
                })
        elif block is not None:
            if isinstance(block, str):
                predicates.append(location_check({"block": {"blocks": [block]}}))
            else:
                predicates.append(location_check({"block": block}))
        if item is not None:
            predicates.append(match_tool(item))

        conditions.pop("location", None)
        conditions["location"] = predicates
        return True

    if trigger == "minecraft:item_used_on_block":
        # The 1.20.1 schema folds item and location into conditions.location[].
        location = conditions.get("location")
        item = conditions.pop("item", None)
        if item is None and not isinstance(location, dict):
            return False
        predicates = list(location) if isinstance(location, list) else []
        if item is not None:
            predicates.append(match_tool(item))
        if isinstance(location, dict):
            predicates.append(location_check(location))
        conditions["location"] = predicates
        return True

    return False

for path in sorted(ADV_DIR.rglob("*.json")):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        ISSUES.append(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
        continue
    changed = False
    for criterion in data.get("criteria", {}).values():
        if migrate_criterion(criterion):
            changed = True
    if changed:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        CHANGED.append(str(path.relative_to(ROOT)))

# Validate 1.20.1 semantics: location must be a list for these trigger types.
for path in sorted(ADV_DIR.rglob("*.json")):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        continue
    for criterion_name, criterion in data.get("criteria", {}).items():
        trigger = criterion.get("trigger")
        conditions = criterion.get("conditions", {})
        if trigger in {"minecraft:placed_block", "minecraft:item_used_on_block"}:
            if not isinstance(conditions.get("location"), list):
                ISSUES.append(
                    f"{path.relative_to(ROOT)} criterion {criterion_name}: "
                    f"{trigger} must use conditions.location as an array"
                )
            for legacy_key in ("block", "item", "state"):
                if legacy_key in conditions:
                    ISSUES.append(
                        f"{path.relative_to(ROOT)} criterion {criterion_name}: "
                        f"legacy {legacy_key} must be migrated into location predicates"
                    )

if ISSUES:
    raise SystemExit("Advancement schema validation failed:\n- " + "\n- ".join(ISSUES))

print(f"Advancement schema validation passed; migrated {len(CHANGED)} files:")
for name in CHANGED:
    print(" - " + name)
