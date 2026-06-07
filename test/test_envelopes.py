import pytest
from pydantic import ValidationError

from iii_drone_contracts import (
    API_VERSION,
    ActionStartResponse,
    ApiIdentity,
    CommandRequest,
    CommandResponse,
    CommandResultMessage,
    DomainName,
    GenericDomainState,
    OperatorEvent,
    OperatorStatePatch,
    OperatorStateSnapshot,
    ServiceCallRequest,
    ServiceCallResponse,
    WebSocketMessage,
)
from iii_drone_contracts.envelopes import ApiError, CommandRejection, ErrorCode, EventSource


def _round_trip(model):
    return type(model).model_validate_json(model.model_dump_json())


def test_api_identity_includes_version_metadata():
    identity = ApiIdentity(runtime_id="sim-1", runtime_name="sim", profile="sim")

    actual = _round_trip(identity)

    assert actual.compatibility.api_version == API_VERSION
    assert actual.runtime_id == "sim-1"


def test_command_and_service_envelopes_round_trip():
    command = CommandRequest(request_id="req-1", command_id="px4.arm", parameters={"hold_ms": 1500})
    service = ServiceCallRequest(
        request_id="req-2",
        service_type="configuration.read",
        service_name="configuration.get_manifest",
    )

    assert _round_trip(command).parameters == {"hold_ms": 1500}
    assert _round_trip(service).service_name == "configuration.get_manifest"


def test_command_responses_and_rejections_validate():
    rejection = CommandRejection(
        code=ErrorCode.STALE_STATE,
        message="vehicle state is stale",
        request_id="req-3",
        command_id="runtime.stop",
        stale_reason="vehicle heartbeat timed out",
    )
    response = CommandResponse(
        request_id="req-3",
        command_id="runtime.stop",
        accepted=False,
        rejection=rejection,
    )

    actual = _round_trip(response)

    assert not actual.accepted
    assert actual.rejection.code == ErrorCode.STALE_STATE


def test_action_service_ws_and_event_envelopes_round_trip():
    action = ActionStartResponse(
        request_id="req-4",
        command_id="custom_operation.fly_to_position.start",
        accepted=True,
        started=True,
        action_id="action-1",
    )
    service = ServiceCallResponse(
        request_id="req-5",
        service_type="logs",
        service_name="logs.list_sources",
        ok=True,
        result={"sources": []},
    )
    event = OperatorEvent(
        event_id="event-1",
        source=EventSource.RUNTIME,
        category="command",
        message="command accepted",
        command_id=action.command_id,
    )
    result = CommandResultMessage(
        request_id=action.request_id,
        command_id=action.command_id,
        status="running",
        action_id=action.action_id,
    )

    assert _round_trip(action).action_id == "action-1"
    assert _round_trip(service).ok is True
    assert _round_trip(event).source == EventSource.RUNTIME
    assert _round_trip(result).status == "running"


def test_snapshot_patch_and_websocket_message_round_trip():
    state = GenericDomainState(source_label="daemon", freshness="fresh", value={"booted": True})
    snapshot = OperatorStateSnapshot()
    snapshot.system.booted = True
    snapshot.system.latest = {"booted": True}
    patch = OperatorStatePatch(domain=DomainName.SYSTEM, state=state, patch_id="patch-1")
    message = WebSocketMessage(message_type="patch", message_id="msg-1", payload=patch)

    assert _round_trip(snapshot).system.latest == {"booted": True}
    assert _round_trip(patch).domain == DomainName.SYSTEM
    assert _round_trip(message).message_type == "patch"


def test_invalid_examples_are_rejected():
    with pytest.raises(ValidationError):
        CommandRequest(request_id="req-6", command_id="px4.hold", unexpected=True)

    with pytest.raises(ValidationError):
        WebSocketMessage(message_type="invalid", message_id="msg-2", payload={})

    with pytest.raises(ValidationError):
        ApiError(code="not-a-code", message="bad")
