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
    ProfileCapabilities,
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


def test_api_identity_advertises_optional_profile_capabilities():
    restricted = ApiIdentity(
        runtime_id="iii-runtime",
        runtime_name="III Runtime",
        profile="opti_track",
        capabilities=ProfileCapabilities(
            profile="opti_track",
            payload_available=False,
            perception_available=False,
            overviews_available=False,
            cable_intents_available=False,
            custom_operations=["fly_to_position", "follow_waypoint_path", "hover"],
        ),
    )

    actual = _round_trip(restricted)

    assert actual.capabilities.payload_available is False
    assert actual.capabilities.custom_operations == ["fly_to_position", "follow_waypoint_path", "hover"]
    # A runtime that advertises nothing (or only defaults) restricts nothing.
    assert _round_trip(ApiIdentity(runtime_id="sim-1", runtime_name="sim")).capabilities is None
    default = ProfileCapabilities()
    assert default.payload_available and default.cable_intents_available
    assert default.custom_operations is None


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


def test_profile_restricted_rejection_is_a_typed_error_code():
    rejection = CommandRejection(
        code=ErrorCode.PROFILE_RESTRICTED,
        message="payload control is not available in the opti_track profile",
        request_id="req-7",
        command_id="payload.gripper.open",
    )

    actual = _round_trip(rejection)

    assert ErrorCode.PROFILE_RESTRICTED.value == "profile_restricted"
    assert actual.code == "profile_restricted"
    assert actual.retryable is False


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
