"""Stable command identifiers and permission-relevant enums."""

from __future__ import annotations

from enum import Enum


class CommandId(str, Enum):
    PX4_ARM = "px4.arm"
    PX4_TAKEOFF = "px4.takeoff"
    PX4_LAND = "px4.land"
    PX4_HOLD = "px4.hold"

    MISSION_ACTIVATE = "mission.activate"
    MISSION_RECHARGE_NOW = "mission.recharge_now"
    MISSION_STAY_ON_CABLE = "mission.stay_on_cable"
    MISSION_LEAVE_CABLE_NOW = "mission.leave_cable_now"
    CUSTOM_OPERATION_ACTIVATE = "custom_operation.activate"

    CUSTOM_OPERATION_VALIDATE = "custom_operation.validate"
    CUSTOM_OPERATION_CANCEL = "custom_operation.cancel"
    CUSTOM_OPERATION_FLY_TO_POSITION_START = "custom_operation.fly_to_position.start"
    CUSTOM_OPERATION_CABLE_AWARE_FLY_TO_POSITION_START = (
        "custom_operation.cable_aware_fly_to_position.start"
    )
    CUSTOM_OPERATION_FLY_TO_OBJECT_START = "custom_operation.fly_to_object.start"
    CUSTOM_OPERATION_CABLE_LANDING_START = "custom_operation.cable_landing.start"
    CUSTOM_OPERATION_CABLE_TAKEOFF_START = "custom_operation.cable_takeoff.start"
    CUSTOM_OPERATION_HOVER_START = "custom_operation.hover.start"
    CUSTOM_OPERATION_HOVER_BY_OBJECT_START = "custom_operation.hover_by_object.start"
    CUSTOM_OPERATION_HOVER_ON_CABLE_START = "custom_operation.hover_on_cable.start"

    PAYLOAD_GRIPPER_OPEN = "payload.gripper.open"
    PAYLOAD_GRIPPER_CLOSE = "payload.gripper.close"

    PERCEPTION_PL_MAPPER_START = "perception.pl_mapper.start"
    PERCEPTION_PL_MAPPER_STOP = "perception.pl_mapper.stop"
    PERCEPTION_PL_MAPPER_FREEZE = "perception.pl_mapper.freeze"
    PERCEPTION_PL_MAPPER_PAUSE = "perception.pl_mapper.pause"
    POWERLINE_OVERVIEW_UPDATE = "powerline.overview.update"
    PYLON_CAPTURE_CURRENT = "pylon.capture_current"
    PYLON_OVERVIEW_CLEAR = "pylon.overview.clear"

    CONFIGURATION_APPLY = "configuration.apply"
    CONFIGURATION_SAVE_SNAPSHOT = "configuration.snapshot.save"
    CONFIGURATION_LOAD_SNAPSHOT = "configuration.snapshot.load"
    CONFIGURATION_DOWNLOAD_SNAPSHOT = "configuration.snapshot.download"
    CONFIGURATION_SET_DEFAULT_SNAPSHOT = "configuration.snapshot.set_default"
    CONFIGURATION_LIST_SNAPSHOTS = "configuration.snapshot.list"

    RUNTIME_BOOT = "runtime.boot"
    RUNTIME_SYSTEM_START = "runtime.system_start"
    RUNTIME_START = "runtime.start"
    RUNTIME_STOP = "runtime.stop"
    RUNTIME_RESTART = "runtime.restart"
    RUNTIME_PARAMETER_COLD_RESTART = "runtime.parameter_cold_restart"
    RUNTIME_SHUTDOWN = "runtime.shutdown"
    RUNTIME_SERVICE_START = "runtime.service.start"
    RUNTIME_SERVICE_STOP = "runtime.service.stop"
    RUNTIME_SERVICE_RESTART = "runtime.service.restart"
    RUNTIME_STATUS = "runtime.status"
    RUNTIME_LIST_ENTITIES = "runtime.list_entities"
    RUNTIME_LIST_SERVICES = "runtime.list_services"

    ROSBAG_START = "rosbag.start"
    ROSBAG_STOP = "rosbag.stop"
    ROSBAG_LIST = "rosbag.list"
    ROSBAG_DOWNLOAD = "rosbag.download"


class ControlOwnerState(str, Enum):
    UNKNOWN = "unknown"
    PX4_MANUAL_OR_POSITION = "px4_manual_or_position"
    PX4_HOLD = "px4_hold"
    MISSION = "mission"
    CUSTOM_OPERATION_IDLE = "custom_operation_idle"
    CUSTOM_OPERATION_ACTIVE = "custom_operation_active"
    TRANSITIONING = "transitioning"
    DEGRADED_CONFLICT = "degraded_conflict"


class Px4ArmingState(str, Enum):
    UNKNOWN = "unknown"
    DISARMED = "disarmed"
    ARMED = "armed"


class Px4AirState(str, Enum):
    UNKNOWN = "unknown"
    LANDED = "landed"
    IN_AIR = "in_air"


class Px4NavState(str, Enum):
    UNKNOWN = "unknown"
    MANUAL = "manual"
    POSITION = "position"
    HOLD = "hold"
    TAKEOFF = "takeoff"
    LAND = "land"
    MISSION = "mission"
    OFFBOARD = "offboard"
    FAILSAFE = "failsafe"


class HandlerPermission(str, Enum):
    READ_ONLY = "read_only"
    MUTATING = "mutating"
    FLIGHT_CRITICAL = "flight_critical"
    RUNTIME_MUTATION = "runtime_mutation"
