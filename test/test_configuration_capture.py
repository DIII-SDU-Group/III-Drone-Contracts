from __future__ import annotations

import copy

import pytest

from iii_drone_contracts.configuration_capture import (
    ConfigurationCaptureError,
    capture_receipt,
    content_identity,
    seal_capture,
    validate_journal_batch,
    verify_capture,
)


def source(*, profile: str = "real") -> dict:
    head = {
        "schema": "iii.configuration-tuning-wal-entry/v1",
        "sequence": 7,
        "previous_checksum": "f" * 64,
        "checksum": "",
        "kind": "committed",
        "timestamp": "2026-08-27T12:00:03Z",
        "session_id": "d" * 64,
        "transaction_id": "1" * 64,
        "request_id": "request-7",
        "revision": 3,
        "body": {"operator_id": "operator-test"},
    }
    head["checksum"] = content_identity(
        {key: item for key, item in head.items() if key != "checksum"}
    )
    return {
        "schema": "iii.configuration-capture-source/v1",
        "snapshot_id": "snapshots/tuned.yaml",
        "snapshot_content_sha256": "a" * 64,
        "values": {"/control/gain": 2.0},
        "parameter_document": {
            "/**": {"ros__parameters": {"/control/gain": 2.0}},
            "/sensor/example": {"ros__parameters": {"frame_id": "sensor"}},
        },
        "target_id": "drone-1" if profile == "real" else "sim",
        "runtime_profile": profile,
        "release_id": "b" * 64,
        "workspace_id": "workspace-test",
        "manifest_id": "c" * 64,
        "session_id": "d" * 64,
        "baseline_id": "e" * 64,
        "baseline_values": {"/control/gain": 1.0},
        "session_created_at": "2026-08-27T12:00:00Z",
        "journal_updated_at": "2026-08-27T12:00:03Z",
        "journal_revision": 3,
        "journal_sequence": 7,
        "journal_checksum": head["checksum"],
        "journal_head_entry": head,
        "pending_boot_values": {"/control/frame": "odom"},
        "source_is_active": False,
        "source_is_default": False,
    }


@pytest.mark.parametrize("profile", ["real", "sim"])
def test_sealed_capture_and_receipt_are_stable_and_offline_verifiable(profile):
    first = seal_capture(source(profile=profile))
    second = seal_capture(source(profile=profile))

    assert first == second
    assert verify_capture(first) == first
    receipt = capture_receipt(first)
    assert receipt["capture_id"] == first["capture_id"]
    assert receipt["snapshot_id"] == "snapshots/tuned.yaml"
    assert receipt["receipt_id"] == content_identity(
        {key: value for key, value in receipt.items() if key != "receipt_id"}
    )


def test_capture_tamper_and_extended_transport_fail_closed():
    capture = seal_capture(source())
    tampered = copy.deepcopy(capture)
    tampered["source"]["values"]["/control/gain"] = 9.0
    tampered["source"]["parameter_document"]["/**"]["ros__parameters"][
        "/control/gain"
    ] = 9.0
    with pytest.raises(ConfigurationCaptureError, match="identity"):
        verify_capture(tampered)

    extended = copy.deepcopy(capture)
    extended["untrusted"] = True
    with pytest.raises(ConfigurationCaptureError, match="fields"):
        verify_capture(extended)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda value: value.update(runtime_profile="bench"), "runtime_profile"),
        (lambda value: value.update(target_id="sim"), "logical target"),
        (lambda value: value.update(journal_revision=4), "head entry"),
        (
            lambda value: value.update(journal_updated_at="2026-08-27T12:00:04Z"),
            "head entry",
        ),
        (
            lambda value: value.update(session_created_at="2026-08-27T12:00:04Z"),
            "predates",
        ),
    ],
)
def test_capture_source_rejects_mismatched_profile_target_and_journal_provenance(
    mutation, message
):
    value = source()
    mutation(value)

    with pytest.raises(ConfigurationCaptureError, match=message):
        seal_capture(value)


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


def test_journal_batch_requires_exact_local_sequence_and_checksum_continuity():
    one = _entry(1, None)
    two = _entry(2, one["checksum"])
    batch = {
        "schema": "iii.configuration-journal-batch/v1",
        "session": {
            "session_id": "d" * 64,
            "baseline_id": "e" * 64,
            "target_id": "drone-1",
            "runtime_profile": "real",
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
