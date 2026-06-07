"""Custom operation request schemas for runtime API commands."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field

from .envelopes import ContractModel


class CustomOperationName(str, Enum):
    FLY_TO_POSITION = "fly_to_position"
    CABLE_AWARE_FLY_TO_POSITION = "cable_aware_fly_to_position"
    FLY_TO_OBJECT = "fly_to_object"
    CABLE_LANDING = "cable_landing"
    CABLE_TAKEOFF = "cable_takeoff"
    HOVER = "hover"
    HOVER_BY_OBJECT = "hover_by_object"
    HOVER_ON_CABLE = "hover_on_cable"


class PositionOperationRequest(ContractModel):
    frame_id: str
    x: float
    y: float
    z: float
    yaw: float


class TargetOperationRequest(ContractModel):
    target_id: int
    target_type: int | None = None
    reference_frame_id: str | None = None
    target: dict[str, Any] | None = None


class CableLandingRequest(ContractModel):
    target_cable_id: int


class CableTakeoffRequest(CableLandingRequest):
    target_cable_distance: float


class HoverRequest(ContractModel):
    duration_s: float
    sustain_duration_s: float = 0.0
    sustain_action: bool = False


class HoverByObjectRequest(TargetOperationRequest):
    duration_s: float
    sustain_action: bool = False


class HoverOnCableRequest(CableLandingRequest):
    duration_s: float
    target_z_velocity: float = 0.0
    target_yaw_rate: float = 0.0
    sustain_action: bool = False


class CustomOperationValidateRequest(ContractModel):
    operation: CustomOperationName
    arguments: dict[str, Any] = Field(default_factory=dict)


class CustomOperationStartRequest(CustomOperationValidateRequest):
    hold_confirmed: bool = False
