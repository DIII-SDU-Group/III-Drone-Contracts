"""Pure configuration journal integrity contracts used by the GC configuration mirror."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping

SHA256 = re.compile(r"^[a-f0-9]{64}$")
JOURNAL_BATCH_SCHEMA = "iii.configuration-journal-batch/v1"
WAL_SCHEMA = "iii.configuration-tuning-wal-entry/v1"
RUNTIME_PROFILES = frozenset({"real", "sim", "hil", "opti_track"})


class ConfigurationCaptureError(RuntimeError):
    """A configuration journal batch failed its fixed contract."""


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

