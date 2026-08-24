#!/usr/bin/env python3
"""Generate TypeScript types from III-Drone Pydantic contracts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from iii_drone_contracts import (  # noqa: E402
    ActionStartResponse,
    ApiCompatibility,
    ApiError,
    ApiIdentity,
    CommandRejection,
    CommandRequest,
    CommandResponse,
    CommandResultMessage,
    ConfigurationApplyRequest,
    ConfigurationApplyResponse,
    ConfigurationManifest,
    MapState,
    OperatorEvent,
    OperatorStatePatch,
    OperatorStateSnapshot,
    ServiceCallRequest,
    ServiceCallResponse,
    WebSocketMessage,
)


MODELS = [
    ApiCompatibility,
    ApiIdentity,
    ApiError,
    CommandRejection,
    CommandRequest,
    CommandResponse,
    ActionStartResponse,
    ServiceCallRequest,
    ServiceCallResponse,
    CommandResultMessage,
    OperatorEvent,
    OperatorStatePatch,
    OperatorStateSnapshot,
    ConfigurationManifest,
    ConfigurationApplyRequest,
    ConfigurationApplyResponse,
    MapState,
    WebSocketMessage,
]


HEADER = """// GENERATED FILE - DO NOT EDIT MANUALLY.
// Source: III-Drone-Contracts Pydantic models.
/* eslint-disable */

"""


def ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def schema_type(schema: dict[str, Any], defs: dict[str, Any]) -> str:
    if "$ref" in schema:
        return ref_name(schema["$ref"])
    if "const" in schema:
        return json.dumps(schema["const"])
    if "enum" in schema:
        return " | ".join(json.dumps(value) for value in schema["enum"])
    if "anyOf" in schema:
        return " | ".join(schema_type(item, defs) for item in schema["anyOf"])
    if "oneOf" in schema:
        return " | ".join(schema_type(item, defs) for item in schema["oneOf"])

    schema_kind = schema.get("type")
    if isinstance(schema_kind, list):
        return " | ".join(schema_type({"type": item}, defs) for item in schema_kind)
    if schema_kind == "null":
        return "null"
    if schema_kind == "string":
        return "string"
    if schema_kind in {"integer", "number"}:
        return "number"
    if schema_kind == "boolean":
        return "boolean"
    if schema_kind == "array":
        return f"Array<{schema_type(schema.get('items', {}), defs)}>"
    if schema_kind == "object" or "properties" in schema:
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        if not properties:
            additional = schema.get("additionalProperties")
            if isinstance(additional, dict):
                return f"Record<string, {schema_type(additional, defs)}>"
            return "Record<string, unknown>"
        parts = []
        for name, prop_schema in properties.items():
            optional = "" if name in required else "?"
            parts.append(f"{json.dumps(name)}{optional}: {schema_type(prop_schema, defs)}")
        return "{ " + "; ".join(parts) + " }"
    return "unknown"


def emit_named_schema(name: str, schema: dict[str, Any], defs: dict[str, Any]) -> str:
    if "enum" in schema:
        return f"export type {name} = {schema_type(schema, defs)};\n"

    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    lines = [f"export interface {name} {{"]
    for prop_name, prop_schema in properties.items():
        optional = "" if prop_name in required else "?"
        lines.append(f"  {prop_name}{optional}: {schema_type(prop_schema, defs)};")
    lines.append("}\n")
    return "\n".join(lines)


def render() -> str:
    all_defs: dict[str, Any] = {}
    root_schemas: dict[str, dict[str, Any]] = {}
    for model in MODELS:
        schema = model.model_json_schema(ref_template="#/$defs/{model}")
        all_defs.update(schema.get("$defs", {}))
        root_schemas[model.__name__] = {key: value for key, value in schema.items() if key != "$defs"}

    output = [HEADER]
    for name in sorted(all_defs):
        output.append(emit_named_schema(name, all_defs[name], all_defs))
    for name in sorted(root_schemas):
        output.append(emit_named_schema(name, root_schemas[name], all_defs))
    output.append(
        "export const CONTRACT_MODEL_NAMES = "
        + json.dumps(sorted(root_schemas), indent=2)
        + " as const;\n"
    )
    return "\n".join(output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    content = render()
    if args.check:
        existing = args.output.read_text(encoding="utf-8") if args.output.exists() else ""
        if existing != content:
            print(f"{args.output} is not current; regenerate contract types.", file=sys.stderr)
            return 1
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
