from iii_drone_contracts import (
    ConfigurationDomainState,
    ControlDomainState,
    DomainName,
    EventSource,
    OperatorEvent,
    OperatorStatePatch,
    OperatorStateSnapshot,
    PayloadDomainState,
    VehicleDomainState,
)


def test_operator_snapshot_contains_all_agreed_domains():
    snapshot = OperatorStateSnapshot()

    for domain in [
        "system",
        "vehicle",
        "control",
        "mission",
        "operation",
        "perception",
        "powerline",
        "payload",
        "configuration",
        "simulation",
        "rosbag",
        "events",
    ]:
        assert hasattr(snapshot, domain)
        state = getattr(snapshot, domain)
        assert hasattr(state, "source_timestamp")
        assert hasattr(state, "runtime_timestamp")
        assert hasattr(state, "freshness")
        assert hasattr(state, "source_availability")
        assert hasattr(state, "degraded_reason")
        assert hasattr(state, "error_reason")


def test_per_domain_patches_validate():
    patches = [
        OperatorStatePatch(domain=DomainName.VEHICLE, state=VehicleDomainState(armed=True, in_air=False)),
        OperatorStatePatch(domain=DomainName.CONTROL, state=ControlDomainState(owner="px4_hold")),
        OperatorStatePatch(domain=DomainName.PAYLOAD, state=PayloadDomainState(gripper_status="open")),
        OperatorStatePatch(
            domain=DomainName.CONFIGURATION,
            state=ConfigurationDomainState(pending_edits=True, unsaved=True),
        ),
    ]

    for patch in patches:
        assert OperatorStatePatch.model_validate_json(patch.model_dump_json()).domain == patch.domain


def test_events_domain_supports_runtime_and_local_sources():
    runtime_event = OperatorEvent(
        event_id="runtime-1",
        source=EventSource.RUNTIME,
        category="health",
        message="daemon degraded",
    )
    local_event = OperatorEvent(
        event_id="frontend-1",
        source=EventSource.FRONTEND,
        category="session",
        message="reconnecting",
    )
    snapshot = OperatorStateSnapshot()
    snapshot.events.recent_events = [runtime_event, local_event]

    actual = OperatorStateSnapshot.model_validate_json(snapshot.model_dump_json())

    assert [event.source for event in actual.events.recent_events] == [
        EventSource.RUNTIME,
        EventSource.FRONTEND,
    ]
