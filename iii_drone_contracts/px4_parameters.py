"""PX4 parameter baselines per runtime profile.

The baseline of a profile is the set of PX4 parameters the III stack relies on
there. Its single source is the profile's NSH script in ``deployment/px4``,
which can also be run by hand in a PX4 console. `iii px4 param-baseline`
applies it, and the Pi checks it before every system boot and start.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Mapping

Number = int | float

# Runtime profile -> NSH baseline in deployment/px4. The HIL baseline is for
# the physical flight controller, which HIL keeps connected but does not fly.
BASELINE_FILES: Mapping[str, str] = {
    "hil": "hil-ethernet.nsh",
    "opti_track": "opti-track.nsh",
    "real": "real.nsh",
}
# Profiles whose flying PX4 is the physical flight controller: the Pi checks
# their baseline before every system boot and start.
CHECKED_PROFILES = frozenset({"real", "opti_track"})
# Follows the stack's ROS domain provisioned on the Pi, not the script's value.
STACK_DOMAIN_PARAMETER = "UXRCE_DDS_DOM_ID"
APPLY_COMMAND = "iii px4 param-baseline --profile {profile}"


class BaselineError(ValueError):
    """A baseline script is missing or is not a plain list of `param set` lines."""


def _number(text: str) -> Number:
    try:
        return int(text, 10)
    except ValueError:
        return float(text)


def parse_baseline(text: str) -> dict[str, Number]:
    """The parameters an NSH baseline sets, in order."""

    parameters: dict[str, Number] = {}
    for line in text.splitlines():
        words = line.split()
        if not words or words[0].startswith("#") or words in (["param", "save"], ["reboot"]):
            continue
        if len(words) != 4 or words[:2] != ["param", "set"]:
            raise BaselineError(f"not a `param set NAME VALUE` line: {line!r}")
        name = words[2]
        if name in parameters:
            raise BaselineError(f"{name} is set twice")
        try:
            parameters[name] = _number(words[3])
        except ValueError:
            raise BaselineError(f"{name} has a non-numeric value {words[3]!r}") from None
    if not parameters:
        raise BaselineError("the baseline sets no parameter")
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
