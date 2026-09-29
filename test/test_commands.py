from iii_drone_contracts import (
    CommandId,
    ControlOwnerState,
    HandlerPermission,
    Px4AirState,
    Px4ArmingState,
    Px4NavState,
)


def test_stable_command_id_values():
    expected = {
        CommandId.PX4_ARM: "px4.arm",
        CommandId.PX4_TAKEOFF: "px4.takeoff",
        CommandId.PX4_LAND: "px4.land",
        CommandId.PX4_HOLD: "px4.hold",
        CommandId.MISSION_ACTIVATE: "mission.activate",
        CommandId.MISSION_CATALOG_STATUS: "mission.catalog.status",
        CommandId.MISSION_CATALOG_LIST: "mission.catalog.list",
        CommandId.MISSION_CATALOG_SHOW: "mission.catalog.show",
        CommandId.MISSION_CATALOG_SELECT: "mission.catalog.select",
        CommandId.CUSTOM_OPERATION_ACTIVATE: "custom_operation.activate",
        CommandId.CUSTOM_OPERATION_VALIDATE: "custom_operation.validate",
        CommandId.CUSTOM_OPERATION_CANCEL: "custom_operation.cancel",
        CommandId.CUSTOM_OPERATION_FLY_TO_POSITION_START: "custom_operation.fly_to_position.start",
        CommandId.CUSTOM_OPERATION_CABLE_AWARE_FLY_TO_POSITION_START: "custom_operation.cable_aware_fly_to_position.start",
        CommandId.CUSTOM_OPERATION_FLY_TO_OBJECT_START: "custom_operation.fly_to_object.start",
        CommandId.CUSTOM_OPERATION_CABLE_LANDING_START: "custom_operation.cable_landing.start",
        CommandId.CUSTOM_OPERATION_CABLE_TAKEOFF_START: "custom_operation.cable_takeoff.start",
        CommandId.CUSTOM_OPERATION_HOVER_START: "custom_operation.hover.start",
        CommandId.CUSTOM_OPERATION_HOVER_BY_OBJECT_START: "custom_operation.hover_by_object.start",
        CommandId.CUSTOM_OPERATION_HOVER_ON_CABLE_START: "custom_operation.hover_on_cable.start",
        CommandId.PAYLOAD_GRIPPER_OPEN: "payload.gripper.open",
        CommandId.PAYLOAD_GRIPPER_CLOSE: "payload.gripper.close",
        CommandId.PERCEPTION_PL_MAPPER_START: "perception.pl_mapper.start",
        CommandId.PERCEPTION_PL_MAPPER_STOP: "perception.pl_mapper.stop",
        CommandId.PERCEPTION_PL_MAPPER_FREEZE: "perception.pl_mapper.freeze",
        CommandId.PERCEPTION_PL_MAPPER_PAUSE: "perception.pl_mapper.pause",
        CommandId.POWERLINE_OVERVIEW_UPDATE: "powerline.overview.update",
        CommandId.CONFIGURATION_APPLY: "configuration.apply",
        CommandId.RUNTIME_BOOT: "runtime.boot",
        CommandId.RUNTIME_SYSTEM_START: "runtime.system_start",
        CommandId.RUNTIME_SERVICE_RESTART: "runtime.service.restart",
        CommandId.ROSBAG_START: "rosbag.start",
        CommandId.ROSBAG_STOP: "rosbag.stop",
        CommandId.ROSBAG_LIST: "rosbag.list",
        CommandId.ROSBAG_DOWNLOAD: "rosbag.download",
    }

    for command, value in expected.items():
        assert command.value == value


def test_control_owner_states_match_spec():
    assert {state.value for state in ControlOwnerState} == {
        "unknown",
        "px4_manual_or_position",
        "px4_hold",
        "mission",
        "custom_operation_idle",
        "custom_operation_active",
        "transitioning",
        "degraded_conflict",
    }


def test_exact_px4_state_is_separate_from_coarse_control_owner():
    assert Px4ArmingState.ARMED.value == "armed"
    assert Px4AirState.IN_AIR.value == "in_air"
    assert Px4NavState.HOLD.value == "hold"
    assert ControlOwnerState.PX4_HOLD.value == "px4_hold"
    assert Px4NavState.HOLD.value != ControlOwnerState.PX4_HOLD.value


def test_handler_permission_classification_values_are_stable():
    assert HandlerPermission.READ_ONLY.value == "read_only"
    assert HandlerPermission.MUTATING.value == "mutating"
    assert HandlerPermission.FLIGHT_CRITICAL.value == "flight_critical"
    assert HandlerPermission.RUNTIME_MUTATION.value == "runtime_mutation"
