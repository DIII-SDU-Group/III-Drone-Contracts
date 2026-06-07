from iii_drone_contracts import (
    CableLandingRequest,
    CableTakeoffRequest,
    CustomOperationName,
    CustomOperationStartRequest,
    CustomOperationValidateRequest,
    HoverByObjectRequest,
    HoverOnCableRequest,
    HoverRequest,
    PositionOperationRequest,
    TargetOperationRequest,
)


def test_custom_operation_request_schemas_round_trip():
    examples = [
        PositionOperationRequest(frame_id="map", x=0.0, y=1.0, z=2.0, yaw=0.5),
        TargetOperationRequest(target_id=7),
        CableLandingRequest(target_cable_id=1),
        CableTakeoffRequest(target_cable_id=1, target_cable_distance=0.5),
        HoverRequest(duration_s=2.0),
        HoverByObjectRequest(target_id=7, duration_s=2.0),
        HoverOnCableRequest(target_cable_id=1, duration_s=2.0),
        CustomOperationValidateRequest(operation=CustomOperationName.HOVER, arguments={"duration_s": 2.0}),
        CustomOperationStartRequest(
            operation=CustomOperationName.FLY_TO_POSITION,
            arguments={"frame_id": "map", "x": 0.0, "y": 0.0, "z": 1.0, "yaw": 0.0},
            hold_confirmed=True,
        ),
    ]

    for example in examples:
        actual = type(example).model_validate_json(example.model_dump_json())
        assert actual == example
