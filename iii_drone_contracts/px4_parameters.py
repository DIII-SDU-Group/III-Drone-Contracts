"""PX4 parameter baselines per runtime profile.

The baseline of a profile is the set of PX4 parameters the III stack relies on
there. Each lives standalone in ``deployment/px4/parameters/<profile>.params``,
a QGroundControl parameter file: tab-separated ``MAV ID, COMPONENT ID, PARAM
NAME, VALUE, TYPE`` rows and ``#`` comment lines. `iii px4 param-baseline`
applies it, and the Pi checks it before every system boot and start.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Mapping

Number = int | float

# Runtime profile -> parameter file. The HIL baseline is for the physical
# flight controller, which HIL keeps connected but does not fly.
BASELINE_FILES: Mapping[str, str] = {
    "hil": "hil.params",
    "opti_track": "opti_track.params",
    "real": "real.params",
}
# Where the files live in the workspace, on the ground computer and on the Pi.
BASELINE_DIRECTORY = "deployment/px4/parameters"
# Profiles whose flying PX4 is the physical flight controller: the Pi checks
# their baseline before every system boot and start.
CHECKED_PROFILES = frozenset({"real", "opti_track"})
# Follows the stack's ROS domain provisioned on the Pi, not the file's value.
STACK_DOMAIN_PARAMETER = "UXRCE_DDS_DOM_ID"
APPLY_COMMAND = "iii px4 param-baseline --profile {profile}"
# MAVLink parameter types PX4 uses.
_INT32 = "6"
_REAL32 = "9"


class BaselineError(ValueError):
    """A baseline file is missing or is not a QGroundControl parameter file."""


def parse_baseline(text: str) -> dict[str, Number]:
    """The parameters of a baseline file, typed as PX4 stores them."""

    parameters: dict[str, Number] = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 5:
            raise BaselineError(
                f"not a `MAV ID, COMPONENT ID, NAME, VALUE, TYPE` row: {line!r}"
            )
        name, value, kind = fields[2].strip(), fields[3].strip(), fields[4].strip()
        if not name or len(name) > 16:
            raise BaselineError(f"invalid PX4 parameter name {name!r}")
        if name in parameters:
            raise BaselineError(f"{name} is set twice")
        try:
            if kind == _INT32:
                parameters[name] = int(value, 10)
            elif kind == _REAL32:
                parameters[name] = float(value)
            else:
                raise BaselineError(f"{name} has the unsupported type {kind!r}")
        except ValueError:
            raise BaselineError(f"{name} has the invalid value {value!r}") from None
    if not parameters:
        raise BaselineError("the baseline holds no parameter")
    return parameters


def load_baseline(
    profile: str, directory: Path, *, ros_domain_id: int | None = None
) -> dict[str, Number]:
    """The baseline of a profile, with the DDS domain the stack actually uses."""

    try:
        path = Path(directory) / BASELINE_FILES[profile]
    except KeyError:
        raise BaselineError(f"profile {profile!r} has no PX4 parameter baseline") from None
    try:
        parameters = parse_baseline(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise BaselineError(f"cannot read the PX4 baseline {path}: {exc.strerror}") from None
    if ros_domain_id is not None and STACK_DOMAIN_PARAMETER in parameters:
        parameters[STACK_DOMAIN_PARAMETER] = int(ros_domain_id)
    return parameters


def values_match(expected: Number, actual: Number | None) -> bool:
    """PX4 stores int32 and float32; compare within float32 resolution."""

    if actual is None:
        return False
    return math.isclose(float(expected), float(actual), rel_tol=1e-6, abs_tol=1e-6)


def _readable(value: Number | None) -> Number | None:
    # A float32 such as 0.1 arrives as 0.10000000149011612.
    return float(f"{value:.7g}") if isinstance(value, float) else value


def mismatches(
    expected: Mapping[str, Number], actual: Mapping[str, Number | None]
) -> list[dict[str, Number | str | None]]:
    """Baseline parameters whose value on the flight controller differs."""

    return [
        {"name": name, "expected": value, "actual": _readable(actual.get(name))}
        for name, value in expected.items()
        if not values_match(value, actual.get(name))
    ]


def describe(differences: list[dict[str, Number | str | None]]) -> str:
    return ", ".join(
        f"{item['name']} is {'unreadable' if item['actual'] is None else item['actual']}"
        f" (baseline {item['expected']})"
        for item in differences
    )
