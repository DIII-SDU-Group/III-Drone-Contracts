"""Configuration manifest and snapshot contracts."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import Field, model_validator

from .envelopes import ContractModel, utc_now


class ParameterValueType(str, Enum):
    BOOL = "bool"
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    STRING_ARRAY = "string_array"
    INTEGER_ARRAY = "integer_array"
    FLOAT_ARRAY = "float_array"


class RestartRequired(str, Enum):
    NONE = "none"
    NODE = "node"
    RUNTIME = "runtime"


class ParameterConstraint(ContractModel):
    minimum: float | int | None = None
    maximum: float | int | None = None
    step: float | int | None = None
    choices: list[Any] | None = None
    regex: str | None = None
    unit: str | None = None


class ParameterDefinition(ContractModel):
    node_id: str
    group_id: str
    name: str
    value_type: ParameterValueType
    current_value: Any
    loaded_value: Any | None = None
    default_value: Any | None = None
    description: str | None = None
    constraints: ParameterConstraint | None = None
    restart_required: RestartRequired = RestartRequired.NONE
    readonly: bool = False
    reference: str | None = None


class ParameterGroup(ContractModel):
    group_id: str
    label: str
    node_id: str
    description: str | None = None
    parameters: list[ParameterDefinition] = Field(default_factory=list)


class ParameterNode(ContractModel):
    node_id: str
    label: str
    groups: list[ParameterGroup] = Field(default_factory=list)


class SnapshotSummary(ContractModel):
    snapshot_id: str
    label: str
    created_at: datetime | None = None
    is_default: bool = False
    is_loaded: bool = False


class ConfigurationStatus(ContractModel):
    pending_edits: bool = False
    unsaved: bool = False
    non_default: bool = False
    loaded_snapshot_id: str | None = None
    default_snapshot_id: str | None = None
    badges: list[Literal["Pending edits", "Unsaved", "Non-default"]] = Field(default_factory=list)

    @model_validator(mode="after")
    def encode_badge_precedence(self):
        badges: list[str] = []
        if self.pending_edits:
            badges.append("Pending edits")
        if self.unsaved:
            badges.append("Unsaved")
        elif self.non_default:
            badges.append("Non-default")
        self.badges = badges
        return self


class ConfigurationManifest(ContractModel):
    nodes: list[ParameterNode] = Field(default_factory=list)
    loaded_snapshot: SnapshotSummary | None = None
    default_snapshot: SnapshotSummary | None = None
    available_snapshots: list[SnapshotSummary] = Field(default_factory=list)
    status: ConfigurationStatus = Field(default_factory=ConfigurationStatus)
    generated_at: datetime = Field(default_factory=utc_now)


class ParameterEdit(ContractModel):
    node_id: str
    name: str
    value: Any


class ParameterApplyResult(ContractModel):
    node_id: str
    name: str
    success: bool
    message: str | None = None
    applied_value: Any | None = None
    restart_required: RestartRequired = RestartRequired.NONE


class ConfigurationApplyRequest(ContractModel):
    edits: list[ParameterEdit]


class ConfigurationApplyResponse(ContractModel):
    ok: bool
    results: list[ParameterApplyResult]
    status: ConfigurationStatus = Field(default_factory=ConfigurationStatus)


class SnapshotSaveRequest(ContractModel):
    label: str
    overwrite_snapshot_id: str | None = None


class SnapshotLoadRequest(ContractModel):
    snapshot_id: str


class SnapshotDownloadRequest(ContractModel):
    snapshot_id: str


class SnapshotSetDefaultRequest(ContractModel):
    snapshot_id: str


class SnapshotOperationResponse(ContractModel):
    ok: bool
    snapshot: SnapshotSummary | None = None
    status: ConfigurationStatus = Field(default_factory=ConfigurationStatus)
    message: str | None = None
