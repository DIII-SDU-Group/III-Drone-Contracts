from iii_drone_contracts import (
    ConfigurationApplyRequest,
    ConfigurationApplyResponse,
    ConfigurationManifest,
    ConfigurationStatus,
    ParameterApplyResult,
    ParameterConstraint,
    ParameterDefinition,
    ParameterEdit,
    ParameterGroup,
    ParameterNode,
    ParameterValueType,
    RestartRequired,
    SnapshotLoadRequest,
    SnapshotOperationResponse,
    SnapshotSaveRequest,
    SnapshotSetDefaultRequest,
    SnapshotSummary,
)


def test_manifest_supports_grouping_constraints_and_restart_metadata():
    parameter = ParameterDefinition(
        node_id="configuration_server",
        group_id="flight",
        name="takeoff_height",
        value_type=ParameterValueType.FLOAT,
        current_value=1.5,
        loaded_value=1.2,
        default_value=1.0,
        constraints=ParameterConstraint(
            minimum=0.5,
            maximum_expression="/flight/ceiling_m - 0.5",
            unit="m",
        ),
        restart_required=RestartRequired.NODE,
        description="Takeoff height.",
    )
    manifest = ConfigurationManifest(
        nodes=[
            ParameterNode(
                node_id="configuration_server",
                label="Configuration Server",
                groups=[ParameterGroup(group_id="flight", label="Flight", node_id="configuration_server", parameters=[parameter])],
            )
        ],
        loaded_snapshot=SnapshotSummary(snapshot_id="test", label="Test", is_loaded=True),
        default_snapshot=SnapshotSummary(snapshot_id="default", label="Default", is_default=True),
    )

    actual = ConfigurationManifest.model_validate_json(manifest.model_dump_json())

    loaded_parameter = actual.nodes[0].groups[0].parameters[0]
    assert loaded_parameter.constraints.unit == "m"
    assert loaded_parameter.constraints.maximum_expression == "/flight/ceiling_m - 0.5"
    assert loaded_parameter.restart_required == RestartRequired.NODE
    assert loaded_parameter.default_value == 1.0


def test_apply_results_return_per_parameter_success_and_error():
    request = ConfigurationApplyRequest(
        edits=[ParameterEdit(node_id="configuration_server", name="takeoff_height", value=2.0)],
        request_id="request-1",
        expected_revision=3,
        operator_id="operator-1",
    )
    response = ConfigurationApplyResponse(
        ok=False,
        results=[
            ParameterApplyResult(
                node_id="configuration_server",
                name="takeoff_height",
                success=False,
                message="out of range",
            )
        ],
    )

    assert ConfigurationApplyRequest.model_validate_json(request.model_dump_json()).edits[0].value == 2.0
    assert ConfigurationApplyRequest.model_validate_json(request.model_dump_json()).expected_revision == 3
    assert ConfigurationApplyResponse.model_validate_json(response.model_dump_json()).results[0].message == "out of range"


def test_snapshot_operations_are_modeled():
    save = SnapshotSaveRequest(label="flight-test")
    load = SnapshotLoadRequest(snapshot_id="flight-test")
    default = SnapshotSetDefaultRequest(snapshot_id="flight-test")
    response = SnapshotOperationResponse(
        ok=True,
        snapshot=SnapshotSummary(snapshot_id="flight-test", label="Flight Test", is_loaded=True),
    )

    assert save.label == "flight-test"
    assert load.snapshot_id == "flight-test"
    assert default.snapshot_id == "flight-test"
    assert SnapshotOperationResponse.model_validate_json(response.model_dump_json()).snapshot.is_loaded


def test_badge_semantics_prefer_unsaved_over_non_default():
    status = ConfigurationStatus(pending_edits=True, unsaved=True, non_default=True)

    actual = ConfigurationStatus.model_validate_json(status.model_dump_json())

    assert actual.badges == ["Pending edits", "Unsaved"]


def test_non_default_badge_shows_when_not_unsaved():
    status = ConfigurationStatus(pending_edits=False, unsaved=False, non_default=True)

    assert status.badges == ["Non-default"]
