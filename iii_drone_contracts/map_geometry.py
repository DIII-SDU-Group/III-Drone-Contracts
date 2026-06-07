"""Frontend-friendly map and geometry contracts."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field

from .envelopes import ContractModel, DomainMetadata, utc_now


class MapProjection(str, Enum):
    POWERLINE_ORTHOGONAL = "powerline_orthogonal"
    TOP_DOWN = "top_down"


class MapSourceStatus(str, Enum):
    AVAILABLE = "available"
    STALE = "stale"
    MISSING = "missing"
    DEGRADED = "degraded"


class Point2D(ContractModel):
    x: float
    y: float


class Point3D(ContractModel):
    x: float
    y: float
    z: float


class Bounds2D(ContractModel):
    min_x: float
    min_y: float
    max_x: float
    max_y: float


class PoseProjection(ContractModel):
    projection: MapProjection
    position: Point2D
    yaw_degrees: float | None = None
    altitude_m: float | None = None


class ConductorGeometry(ContractModel):
    conductor_id: str
    points: list[Point2D]
    source: str
    source_status: MapSourceStatus = MapSourceStatus.AVAILABLE
    updated_at: datetime | None = None


class PowerlineFrameStatus(DomainMetadata):
    projection: MapProjection = MapProjection.POWERLINE_ORTHOGONAL
    status: MapSourceStatus = MapSourceStatus.MISSING
    reference_source: str | None = None
    reason: str | None = None


class TargetState(ContractModel):
    target_id: str | None = None
    position: Point2D | None = None
    label: str | None = None
    status: MapSourceStatus = MapSourceStatus.MISSING
    updated_at: datetime | None = None


class PolylineLayer(ContractModel):
    label: str
    points: list[Point2D] = Field(default_factory=list)
    source_status: MapSourceStatus = MapSourceStatus.MISSING
    updated_at: datetime | None = None


class MapState(DomainMetadata):
    projection_options: list[MapProjection] = Field(
        default_factory=lambda: [MapProjection.POWERLINE_ORTHOGONAL, MapProjection.TOP_DOWN]
    )
    active_projection: MapProjection = MapProjection.POWERLINE_ORTHOGONAL
    frame: PowerlineFrameStatus = Field(default_factory=PowerlineFrameStatus)
    live_conductors: list[ConductorGeometry] = Field(default_factory=list)
    recent_live_conductors: list[ConductorGeometry] = Field(default_factory=list)
    stored_overview_conductors: list[ConductorGeometry] = Field(default_factory=list)
    drone_pose: PoseProjection | None = None
    target_state: TargetState = Field(default_factory=TargetState)
    target_history: list[Point2D] = Field(default_factory=list)
    trajectory: PolylineLayer | None = None
    drone_trail: PolylineLayer | None = None
    auto_fit_bounds: Bounds2D | None = None
    generated_at: datetime = Field(default_factory=utc_now)

    @classmethod
    def empty(cls, reason: str = "no map sources available") -> "MapState":
        return cls(
            frame=PowerlineFrameStatus(status=MapSourceStatus.MISSING, reason=reason),
            degraded_reason=reason,
        )
