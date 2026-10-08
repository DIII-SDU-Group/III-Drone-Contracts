from iii_drone_contracts import (
    ConfigurationDomainState,
    ControlDomainState,
    DomainName,
    EventSource,
    ExternalVisionState,
    MissionDomainState,
    MissionModeRegistryEntry,
    OperatorEvent,
    OperatorStatePatch,
    OperatorStateSnapshot,
    PayloadDomainState,
    ProfileCapabilities,
    SystemDomainState,
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


def test_mission_domain_has_typed_mode_registry_entries():
    state = MissionDomainState(
        active_spec_id="inspection.yaml",
        required_modes_registered=True,
        modes=[
            MissionModeRegistryEntry(
                mode_key="inspection_demo",
                display_name="Inspection Demo",
                mode_id=30,
                registered=True,
                active=True,
                tree_running=True,
                freshness="fresh",
            )
        ],
    )

    payload = state.model_dump(mode="json")
    assert payload["modes"][0]["mode_key"] == "inspection_demo"
    assert payload["modes"][0]["mode_id"] == 30
    assert payload["modes"][0]["tree_success"] is None


def test_vehicle_external_vision_block_is_optional_and_round_trips():
    assert VehicleDomainState().external_vision is None
    state = VehicleDomainState(
        external_vision=ExternalVisionState(
            ready=True,
            freshness="fresh",
            relay_level="ok",
            relay_freshness="fresh",
            relay_stale=False,
            input_rate_hz=120.0,
            last_input_age_ms=8.0,
            origin_sent=True,
            rigid_body_id="1",
            ev_pos_fused=True,
            ev_hgt_fused=True,
            ev_yaw_fused=True,
            fusion_freshness="fresh",
            origin_valid=True,
            origin_freshness="fresh",
        )
    )

    actual = VehicleDomainState.model_validate_json(state.model_dump_json()).external_vision

    assert actual.ready is True
    assert actual.relay_level == "ok"
    assert (actual.ev_pos_fused, actual.ev_hgt_fused, actual.ev_yaw_fused) == (True, True, True)
    assert ExternalVisionState().relay_level == "unknown"
    assert ExternalVisionState().freshness == "unknown"


def test_system_domain_carries_profile_capabilities_to_operator_clients():
    snapshot = OperatorStateSnapshot()
    assert snapshot.system.capabilities is None
    snapshot.system = SystemDomainState(
        capabilities=ProfileCapabilities(profile="opti_track", payload_available=False, custom_operations=["hover"])
    )

    actual = OperatorStateSnapshot.model_validate_json(snapshot.model_dump_json()).system.capabilities

    assert actual.profile == "opti_track"
    assert actual.payload_available is False
    assert actual.custom_operations == ["hover"]
