from __future__ import annotations

import copy

import pytest

from iii_drone_contracts.configuration_capture import (
    ConfigurationCaptureError,
    content_identity,
    validate_journal_batch,
)


def _entry(sequence: int, previous: str | None) -> dict:
    value = {
        "schema": "iii.configuration-tuning-wal-entry/v1",
        "sequence": sequence,
        "previous_checksum": previous,
        "checksum": "",
        "kind": "committed",
        "timestamp": f"2026-08-27T12:00:0{sequence}Z",
        "session_id": "d" * 64,
        "transaction_id": str(sequence) * 64,
        "request_id": f"request-{sequence}",
        "revision": sequence,
        "body": {},
    }
    value["checksum"] = content_identity(
        {key: item for key, item in value.items() if key != "checksum"}
    )
    return value


@pytest.mark.parametrize("runtime_profile", ["real", "sim", "hil", "opti_track"])
def test_journal_batch_requires_exact_local_sequence_and_checksum_continuity(
    runtime_profile,
):
    one = _entry(1, None)
    two = _entry(2, one["checksum"])
    batch = {
        "schema": "iii.configuration-journal-batch/v1",
        "session": {
            "session_id": "d" * 64,
            "baseline_id": "e" * 64,
            "target_id": "drone-1",
            "runtime_profile": runtime_profile,
            "release_id": "b" * 64,
            "workspace_id": "workspace-test",
            "manifest_id": "c" * 64,
            "created_at": "2026-08-27T12:00:00Z",
            "updated_at": "2026-08-27T12:00:02Z",
            "revision": 2,
        },
        "baseline_values": {"/control/gain": 1.0},
        "after_sequence": 0,
        "through_sequence": 2,
        "head_sequence": 2,
        "head_checksum": two["checksum"],
        "entries": [one, two],
        "complete": True,
    }
    assert validate_journal_batch(
        batch, previous_sequence=0, previous_checksum=None
    ) == (2, two["checksum"], True)

    broken = copy.deepcopy(batch)
    broken["entries"][1]["previous_checksum"] = "0" * 64
    with pytest.raises(ConfigurationCaptureError, match="checksum chain"):
        validate_journal_batch(broken, previous_sequence=0, previous_checksum=None)

    with pytest.raises(ConfigurationCaptureError, match="local cursor"):
        validate_journal_batch(
            batch, previous_sequence=1, previous_checksum=one["checksum"]
        )
