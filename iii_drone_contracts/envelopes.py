"""Core runtime API envelope contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from . import API_VERSION


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class ApiCompatibility(ContractModel):
    api_version: str = API_VERSION
    min_client_version: str | None = None
    schema_revision: str = "v2alpha1"


class ApiIdentity(ContractModel):
    runtime_id: str
    runtime_name: str
    profile: str | None = None
    host_label: str | None = None
    compatibility: ApiCompatibility = Field(default_factory=ApiCompatibility)
    server_time: datetime = Field(default_factory=utc_now)


class ErrorCode(str, Enum):
    AUTHENTICATION_REQUIRED = "authentication_required"
    FORBIDDEN = "forbidden"
    CONFLICT = "conflict"
    INVALID_REQUEST = "invalid_request"
    UNSUPPORTED = "unsupported"
    STALE_STATE = "stale_state"
    DEGRADED_STATE = "degraded_state"
    HANDLER_UNAVAILABLE = "handler_unavailable"
    INTERNAL_ERROR = "internal_error"


class ApiError(ContractModel):
    code: ErrorCode
    message: str
    request_id: str | None = None
    command_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)


class CommandRejection(ApiError):
    retryable: bool = False
    degraded_reason: str | None = None
    stale_reason: str | None = None


class RequestEnvelope(ContractModel):
    request_id: str
    issued_at: datetime = Field(default_factory=utc_now)
    client_label: str | None = None
    client_version: str | None = None


class CommandRequest(RequestEnvelope):
    command_id: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class ServiceCallRequest(RequestEnvelope):
    service_type: str
    service_name: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class CommandResponse(ContractModel):
    request_id: str
    command_id: str
    accepted: bool
    message: str | None = None
    rejection: CommandRejection | None = None
    result: dict[str, Any] | None = None
    timestamp: datetime = Field(default_factory=utc_now)


class ActionStartResponse(CommandResponse):
    action_id: str | None = None
    started: bool = False


class ServiceCallResponse(ContractModel):
    request_id: str
    service_type: str
    service_name: str
    ok: bool
    result: dict[str, Any] | None = None
    error: ApiError | None = None
    timestamp: datetime = Field(default_factory=utc_now)


class Freshness(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    UNKNOWN = "unknown"


class SourceAvailability(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class DomainName(str, Enum):
    SYSTEM = "system"
    VEHICLE = "vehicle"
    CONTROL = "control"
    MISSION = "mission"
    OPERATION = "operation"
    PERCEPTION = "perception"
    POWERLINE = "powerline"
    MAP = "map"
    PAYLOAD = "payload"
    CONFIGURATION = "configuration"
    SIMULATION = "simulation"
    ROSBAG = "rosbag"
    EVENTS = "events"


class DomainMetadata(ContractModel):
    source_label: str | None = None
    source_timestamp: datetime | None = None
    runtime_timestamp: datetime = Field(default_factory=utc_now)
    freshness: Freshness = Freshness.UNKNOWN
    source_availability: SourceAvailability = SourceAvailability.UNKNOWN
    degraded_reason: str | None = None
    error_reason: str | None = None


class GenericDomainState(DomainMetadata):
    value: dict[str, Any] = Field(default_factory=dict)


class SystemDomainState(DomainMetadata):
    latest: dict[str, Any] = Field(default_factory=dict)
    api_state: str = "unknown"
    daemon_state: str = "unknown"
    booted: bool | None = None
    active: bool | None = None


class VehicleDomainState(DomainMetadata):
    latest: dict[str, Any] = Field(default_factory=dict)
    armed: bool | None = None
    in_air: bool | None = None
    nav_state: str | None = None
    flight_mode: str | None = None
    failsafe: bool | None = None


class ControlDomainState(DomainMetadata):
    latest: dict[str, Any] = Field(default_factory=dict)
    owner: str = "unknown"
    active_setpoint_owner: str | None = None
    transition_target: str | None = None


class MissionDomainState(DomainMetadata):
    latest: dict[str, Any] = Field(default_factory=dict)
    active_spec_id: str | None = None
    mission_state: str = "unknown"
    required_modes_registered: bool | None = None


class OperationDomainState(DomainMetadata):
    latest: dict[str, Any] = Field(default_factory=dict)
    active_operation_id: str | None = None
    active_operation_type: str | None = None
    status: str = "idle"


class PerceptionDomainState(DomainMetadata):
    latest: dict[str, Any] = Field(default_factory=dict)
    pl_mapper_state: str = "unknown"
    pl_direction_status: str = "unknown"
    hough_status: str = "unknown"


class PowerlineDomainState(DomainMetadata):
    latest: dict[str, Any] = Field(default_factory=dict)
    stored_overview_status: str = "unknown"
    live_perception_status: str = "unknown"


class PayloadDomainState(DomainMetadata):
    latest: dict[str, Any] = Field(default_factory=dict)
    gripper_status: str = "unknown"
    charger_status: str = "unknown"
    battery_voltage: float | None = None
    charging_power: float | None = None


class ConfigurationDomainState(DomainMetadata):
    latest: dict[str, Any] = Field(default_factory=dict)
    active_snapshot_id: str | None = None
    pending_edits: bool = False
    unsaved: bool = False
    non_default: bool = False


class SimulationDomainState(DomainMetadata):
    latest: dict[str, Any] = Field(default_factory=dict)
    profile: str = "unknown"
    px4_gazebo_status: str = "unknown"


class RosbagDomainState(DomainMetadata):
    latest: dict[str, Any] = Field(default_factory=dict)
    recording: bool = False
    recording_id: str | None = None
    output_dir: str | None = None
    owner: str = "unknown"
    size_bytes: int | None = None


class EventsDomainState(DomainMetadata):
    latest: dict[str, Any] = Field(default_factory=dict)
    recent_events: list["OperatorEvent"] = Field(default_factory=list)


DomainState = (
    SystemDomainState
    | VehicleDomainState
    | ControlDomainState
    | MissionDomainState
    | OperationDomainState
    | PerceptionDomainState
    | PowerlineDomainState
    | PayloadDomainState
    | ConfigurationDomainState
    | SimulationDomainState
    | RosbagDomainState
    | EventsDomainState
    | GenericDomainState
)


class OperatorStateSnapshot(ContractModel):
    compatibility: ApiCompatibility = Field(default_factory=ApiCompatibility)
    generated_at: datetime = Field(default_factory=utc_now)
    system: SystemDomainState = Field(default_factory=SystemDomainState)
    vehicle: VehicleDomainState = Field(default_factory=VehicleDomainState)
    control: ControlDomainState = Field(default_factory=ControlDomainState)
    mission: MissionDomainState = Field(default_factory=MissionDomainState)
    operation: OperationDomainState = Field(default_factory=OperationDomainState)
    perception: PerceptionDomainState = Field(default_factory=PerceptionDomainState)
    powerline: PowerlineDomainState = Field(default_factory=PowerlineDomainState)
    map: GenericDomainState = Field(default_factory=lambda: GenericDomainState(source_label="runtime_map"))
    payload: PayloadDomainState = Field(default_factory=PayloadDomainState)
    configuration: ConfigurationDomainState = Field(default_factory=ConfigurationDomainState)
    simulation: SimulationDomainState = Field(default_factory=SimulationDomainState)
    rosbag: RosbagDomainState = Field(default_factory=RosbagDomainState)
    events: EventsDomainState = Field(default_factory=EventsDomainState)


class OperatorStatePatch(ContractModel):
    domain: DomainName
    state: DomainState
    patch_id: str | None = None
    generated_at: datetime = Field(default_factory=utc_now)


class EventSource(str, Enum):
    RUNTIME = "runtime"
    GC_PROXY = "gc_proxy"
    FRONTEND = "frontend"
    CLI = "cli"
    ROS = "ros"


class OperatorEvent(ContractModel):
    event_id: str
    source: EventSource
    category: str
    severity: Literal["debug", "info", "warning", "error", "critical"] = "info"
    message: str
    request_id: str | None = None
    command_id: str | None = None
    domain: DomainName | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)


class CommandResultMessage(ContractModel):
    request_id: str
    command_id: str
    status: Literal["accepted", "running", "succeeded", "failed", "rejected", "cancelled"]
    action_id: str | None = None
    result: dict[str, Any] | None = None
    rejection: CommandRejection | None = None
    timestamp: datetime = Field(default_factory=utc_now)


class WebSocketMessage(ContractModel):
    message_type: Literal["snapshot", "patch", "event", "command_result"]
    message_id: str
    payload: OperatorStateSnapshot | OperatorStatePatch | OperatorEvent | CommandResultMessage
    sent_at: datetime = Field(default_factory=utc_now)
