"""Pure configuration journal/capture integrity contracts shared by GC and CLI."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any, Mapping

SHA256 = re.compile(r"^[a-f0-9]{64}$")
CAPTURE_SOURCE_SCHEMA = "iii.configuration-capture-source/v1"
CAPTURE_SCHEMA = "iii.configuration-capture/v1"
RECEIPT_SCHEMA = "iii.configuration-capture-receipt/v1"
JOURNAL_BATCH_SCHEMA = "iii.configuration-journal-batch/v1"
WAL_SCHEMA = "iii.configuration-tuning-wal-entry/v1"
RUNTIME_PROFILES = frozenset({"real", "sim", "hil", "opti_track"})


class ConfigurationCaptureError(RuntimeError):
    """A journal, source, capture, or receipt failed its fixed contract."""


def canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ConfigurationCaptureError(f"value is not canonical JSON: {exc}") from exc


def content_identity(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def validate_journal_batch(
    value: Mapping[str, Any],
    *,
    previous_sequence: int,
    previous_checksum: str | None,
) -> tuple[int, str | None, bool]:
    fields = {
        "schema",
        "session",
        "baseline_values",
        "after_sequence",
        "through_sequence",
        "head_sequence",
        "head_checksum",
        "entries",
        "complete",
    }
    if set(value) != fields or value.get("schema") != JOURNAL_BATCH_SCHEMA:
        raise ConfigurationCaptureError(
            "configuration journal batch fields are invalid"
        )
    if value["after_sequence"] != previous_sequence:
        raise ConfigurationCaptureError(
            "configuration journal batch does not continue the local cursor"
        )
    if not isinstance(value["entries"], list) or not isinstance(
        value["baseline_values"], dict
    ):
        raise ConfigurationCaptureError(
            "configuration journal batch payload is invalid"
        )
    session = value["session"]
    if session is None:
        if (
            value["entries"]
            or value["baseline_values"]
            or value["after_sequence"] != 0
            or value["through_sequence"] != 0
            or value["head_sequence"] != 0
            or value["head_checksum"] is not None
            or value["complete"] is not True
        ):
            raise ConfigurationCaptureError(
                "empty configuration journal is inconsistent"
            )
        return previous_sequence, previous_checksum, True
    session_fields = {
        "session_id",
        "baseline_id",
        "target_id",
        "runtime_profile",
        "release_id",
        "workspace_id",
        "manifest_id",
        "created_at",
        "updated_at",
        "revision",
    }
    if (
        not isinstance(session, dict)
        or set(session) != session_fields
        or not SHA256.fullmatch(str(session.get("session_id", "")))
        or not SHA256.fullmatch(str(session.get("baseline_id", "")))
        or not SHA256.fullmatch(str(session.get("manifest_id", "")))
        or session.get("runtime_profile") not in RUNTIME_PROFILES
        or any(
            not isinstance(session.get(field), str) or not session[field]
            for field in (
                "target_id",
                "release_id",
                "workspace_id",
                "created_at",
                "updated_at",
            )
        )
        or isinstance(session.get("revision"), bool)
        or not isinstance(session.get("revision"), int)
        or session["revision"] < 0
    ):
        raise ConfigurationCaptureError("configuration journal session is invalid")
    canonical_json(value["baseline_values"])
    expected_sequence = previous_sequence + 1
    cursor_checksum = previous_checksum
    entry_fields = {
        "schema",
        "sequence",
        "previous_checksum",
        "checksum",
        "kind",
        "timestamp",
        "session_id",
        "transaction_id",
        "request_id",
        "revision",
        "body",
    }
    for entry in value["entries"]:
        if not isinstance(entry, dict) or set(entry) != entry_fields:
            raise ConfigurationCaptureError(
                "configuration journal entry fields are invalid"
            )
        supplied = entry["checksum"]
        expected = content_identity(
            {key: item for key, item in entry.items() if key != "checksum"}
        )
        if (
            entry["schema"] != WAL_SCHEMA
            or entry["sequence"] != expected_sequence
            or entry["previous_checksum"] != cursor_checksum
            or entry["session_id"] != session["session_id"]
            or supplied != expected
        ):
            raise ConfigurationCaptureError(
                "configuration journal checksum chain is invalid"
            )
        cursor_checksum = supplied
        expected_sequence += 1
    through = (
        value["entries"][-1]["sequence"] if value["entries"] else previous_sequence
    )
    if (
        value["through_sequence"] != through
        or not isinstance(value["head_sequence"], int)
        or through > value["head_sequence"]
        or value["complete"] != (through == value["head_sequence"])
    ):
        raise ConfigurationCaptureError(
            "configuration journal cursor metadata is invalid"
        )
    if value["complete"] and cursor_checksum != value["head_checksum"]:
        raise ConfigurationCaptureError(
            "configuration journal head checksum is invalid"
        )
    return through, cursor_checksum, bool(value["complete"])


def seal_capture(source: Mapping[str, Any]) -> dict[str, Any]:
    _validate_capture_source(source)
    capture = {
        "schema": CAPTURE_SCHEMA,
        "capture_id": "",
        "source": dict(source),
    }
    capture["capture_id"] = content_identity(
        {key: item for key, item in capture.items() if key != "capture_id"}
    )
    return capture


def verify_capture(value: Mapping[str, Any]) -> dict[str, Any]:
    if (
        set(value) != {"schema", "capture_id", "source"}
        or value.get("schema") != CAPTURE_SCHEMA
    ):
        raise ConfigurationCaptureError("configuration capture fields are invalid")
    source = value.get("source")
    if not isinstance(source, dict):
        raise ConfigurationCaptureError("configuration capture source is invalid")
    _validate_capture_source(source)
    expected = content_identity(
        {key: item for key, item in value.items() if key != "capture_id"}
    )
    if value.get("capture_id") != expected:
        raise ConfigurationCaptureError("configuration capture identity is invalid")
    return dict(value)


def capture_receipt(capture: Mapping[str, Any]) -> dict[str, Any]:
    verified = verify_capture(capture)
    source = verified["source"]
    value = {
        "schema": RECEIPT_SCHEMA,
        "receipt_id": "",
        "capture_id": verified["capture_id"],
        "snapshot_id": source["snapshot_id"],
        "content_sha256": source["snapshot_content_sha256"],
        "target_id": source["target_id"],
        "runtime_profile": source["runtime_profile"],
        "release_id": source["release_id"],
        "manifest_id": source["manifest_id"],
    }
    value["receipt_id"] = content_identity(
        {key: item for key, item in value.items() if key != "receipt_id"}
    )
    return value


def _validate_capture_source(value: Mapping[str, Any]) -> None:
    fields = {
        "schema",
        "snapshot_id",
        "snapshot_content_sha256",
        "values",
        "parameter_document",
        "target_id",
        "runtime_profile",
        "release_id",
        "workspace_id",
        "manifest_id",
        "session_id",
        "baseline_id",
        "baseline_values",
        "session_created_at",
        "journal_updated_at",
        "journal_revision",
        "journal_sequence",
        "journal_checksum",
        "journal_head_entry",
        "pending_boot_values",
        "source_is_active",
        "source_is_default",
    }
    if set(value) != fields or value.get("schema") != CAPTURE_SOURCE_SCHEMA:
        raise ConfigurationCaptureError(
            "configuration capture source fields are invalid"
        )
    if not isinstance(value.get("snapshot_id"), str) or not value["snapshot_id"]:
        raise ConfigurationCaptureError(
            "configuration capture snapshot identity is invalid"
        )
    for field in (
        "snapshot_content_sha256",
        "manifest_id",
        "session_id",
        "baseline_id",
    ):
        if not isinstance(value.get(field), str) or not SHA256.fullmatch(value[field]):
            raise ConfigurationCaptureError(f"configuration capture {field} is invalid")
    for field in ("target_id", "release_id", "workspace_id"):
        if not isinstance(value.get(field), str) or not value[field]:
            raise ConfigurationCaptureError(f"configuration capture {field} is invalid")
    if value.get("runtime_profile") not in RUNTIME_PROFILES:
        raise ConfigurationCaptureError(
            "configuration capture runtime_profile is invalid"
        )
    if (value["runtime_profile"] == "sim") != (value["target_id"] == "sim"):
        raise ConfigurationCaptureError(
            "configuration capture logical target and profile differ"
        )
    parsed_timestamps = {}
    for field in ("session_created_at", "journal_updated_at"):
        if not isinstance(value.get(field), str) or not value[field]:
            raise ConfigurationCaptureError(f"configuration capture {field} is invalid")
        try:
            parsed = datetime.fromisoformat(value[field].replace("Z", "+00:00"))
        except ValueError as exc:
            raise ConfigurationCaptureError(
                f"configuration capture {field} is invalid"
            ) from exc
        if parsed.tzinfo is None:
            raise ConfigurationCaptureError(
                f"configuration capture {field} must be timezone-aware"
            )
        parsed_timestamps[field] = parsed
    if (
        parsed_timestamps["journal_updated_at"]
        < parsed_timestamps["session_created_at"]
    ):
        raise ConfigurationCaptureError(
            "configuration capture journal predates its session"
        )
    for field in (
        "values",
        "parameter_document",
        "baseline_values",
        "pending_boot_values",
    ):
        if not isinstance(value.get(field), dict):
            raise ConfigurationCaptureError(f"configuration capture {field} is invalid")
        canonical_json(value[field])
    parameter_document = value["parameter_document"]
    if "/**" not in parameter_document:
        raise ConfigurationCaptureError(
            "configuration capture parameter_document has no wildcard section"
        )

    def validate_parameter_tree(document: Mapping[str, Any]) -> None:
        if "ros__parameters" in document:
            if set(document) != {"ros__parameters"} or not isinstance(
                document["ros__parameters"], dict
            ):
                raise ConfigurationCaptureError(
                    "configuration capture parameter_document shape is invalid"
                )
            canonical_json(document["ros__parameters"])
            return
        if not document:
            raise ConfigurationCaptureError(
                "configuration capture parameter_document shape is invalid"
            )
        for node_name, nested in document.items():
            if (
                not isinstance(node_name, str)
                or not node_name
                or not isinstance(nested, dict)
            ):
                raise ConfigurationCaptureError(
                    "configuration capture parameter_document shape is invalid"
                )
            validate_parameter_tree(nested)

    validate_parameter_tree(parameter_document)
    if parameter_document["/**"]["ros__parameters"] != value["values"]:
        raise ConfigurationCaptureError(
            "configuration capture values differ from the full parameter document"
        )
    for field in ("journal_revision", "journal_sequence"):
        if (
            isinstance(value.get(field), bool)
            or not isinstance(value.get(field), int)
            or value[field] < 0
        ):
            raise ConfigurationCaptureError(f"configuration capture {field} is invalid")
    checksum = value.get("journal_checksum")
    if value["journal_sequence"] == 0:
        if checksum is not None:
            raise ConfigurationCaptureError(
                "empty configuration journal has a checksum"
            )
    elif not isinstance(checksum, str) or not SHA256.fullmatch(checksum):
        raise ConfigurationCaptureError(
            "configuration capture journal checksum is invalid"
        )
    head_entry = value.get("journal_head_entry")
    if value["journal_sequence"] == 0:
        if head_entry is not None:
            raise ConfigurationCaptureError(
                "empty configuration journal has a head entry"
            )
    elif (
        not isinstance(head_entry, dict)
        or set(head_entry)
        != {
            "schema",
            "sequence",
            "previous_checksum",
            "checksum",
            "kind",
            "timestamp",
            "session_id",
            "transaction_id",
            "request_id",
            "revision",
            "body",
        }
        or head_entry.get("schema") != WAL_SCHEMA
        or head_entry.get("sequence") != value["journal_sequence"]
        or head_entry.get("checksum") != checksum
        or head_entry.get("session_id") != value["session_id"]
        or head_entry.get("revision") != value["journal_revision"]
        or head_entry.get("timestamp") != value["journal_updated_at"]
        or head_entry.get("kind")
        not in {
            "prepared",
            "committed",
            "recovered-commit",
            "rejected",
            "aborted",
            "divergent",
            "boot-confirmed",
            "divergence-reconciled",
        }
        or not isinstance(head_entry.get("transaction_id"), str)
        or not SHA256.fullmatch(head_entry["transaction_id"])
        or not isinstance(head_entry.get("request_id"), str)
        or not head_entry["request_id"]
        or not isinstance(head_entry.get("body"), dict)
        or head_entry.get("checksum")
        != content_identity(
            {key: item for key, item in head_entry.items() if key != "checksum"}
        )
    ):
        raise ConfigurationCaptureError(
            "configuration capture journal head entry is invalid"
        )
    if not isinstance(value.get("source_is_active"), bool) or not isinstance(
        value.get("source_is_default"), bool
    ):
        raise ConfigurationCaptureError(
            "configuration capture source flags are invalid"
        )
