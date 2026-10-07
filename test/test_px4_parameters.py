from pathlib import Path

import pytest

from iii_drone_contracts.px4_parameters import (
    BASELINE_FILES,
    CHECKED_PROFILES,
    BaselineError,
    describe,
    load_baseline,
    mismatches,
    parse_baseline,
)

SCRIPT = """# comment
param set UXRCE_DDS_PRT 8888
param set UXRCE_DDS_DOM_ID 42

param set EKF2_EVP_NOISE 0.05
param save
reboot
"""


def test_a_baseline_is_its_param_set_lines_with_numeric_values():
    assert parse_baseline(SCRIPT) == {
        "UXRCE_DDS_PRT": 8888,
        "UXRCE_DDS_DOM_ID": 42,
        "EKF2_EVP_NOISE": 0.05,
    }


@pytest.mark.parametrize(
    "script",
    ["", "param set A 1\nparam set A 2\n", "param set A\n", "param set A one\n", "mavlink start\n"],
)
def test_anything_but_plain_param_set_lines_is_refused(script):
    with pytest.raises(BaselineError):
        parse_baseline(script)


def test_the_dds_domain_follows_the_provisioned_stack_domain(tmp_path: Path):
    (tmp_path / BASELINE_FILES["opti_track"]).write_text(SCRIPT, encoding="utf-8")
    assert load_baseline("opti_track", tmp_path)["UXRCE_DDS_DOM_ID"] == 42
    assert load_baseline("opti_track", tmp_path, ros_domain_id=7)["UXRCE_DDS_DOM_ID"] == 7
    with pytest.raises(BaselineError):
        load_baseline("sim", tmp_path)
    with pytest.raises(BaselineError):
        load_baseline("real", tmp_path)


def test_values_compare_across_px4_int_and_float_storage():
    expected = {"EKF2_EV_DELAY": 30, "EKF2_EVP_NOISE": 0.05, "EKF2_EV_CTRL": 11, "SYS_HAS_GPS": 0}
    # PX4 stores EKF2_EV_DELAY as float32, and 0.05 is not exact in float32.
    actual = {"EKF2_EV_DELAY": 30.0, "EKF2_EVP_NOISE": 0.05000000074505806, "EKF2_EV_CTRL": 0}
    assert mismatches(expected, actual) == [
        {"name": "EKF2_EV_CTRL", "expected": 11, "actual": 0},
        {"name": "SYS_HAS_GPS", "expected": 0, "actual": None},
    ]
    assert describe(mismatches(expected, actual)) == (
        "EKF2_EV_CTRL is 0 (baseline 11), SYS_HAS_GPS is unreadable (baseline 0)"
    )


def test_only_profiles_that_fly_the_flight_controller_are_checked_at_boot():
    assert CHECKED_PROFILES == {"real", "opti_track"}
    assert set(BASELINE_FILES) == {"real", "opti_track", "hil"}
