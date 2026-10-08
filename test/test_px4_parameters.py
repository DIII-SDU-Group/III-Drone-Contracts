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

SCRIPT = """# PX4 parameter baseline
# MAV ID\tCOMPONENT ID\tPARAM NAME\tVALUE\tTYPE
1\t1\tUXRCE_DDS_PRT\t8888\t6
1\t1\tUXRCE_DDS_DOM_ID\t42\t6

# A float32 parameter although its value is whole.
1\t1\tEKF2_EV_DELAY\t30.0\t9
1\t1\tEKF2_EVP_NOISE\t0.05\t9
"""


def test_a_baseline_is_a_qgroundcontrol_parameter_file_typed_as_px4_stores_it():
    parameters = parse_baseline(SCRIPT)
    assert parameters == {
        "UXRCE_DDS_PRT": 8888,
        "UXRCE_DDS_DOM_ID": 42,
        "EKF2_EV_DELAY": 30.0,
        "EKF2_EVP_NOISE": 0.05,
    }
    assert isinstance(parameters["EKF2_EV_DELAY"], float)
    assert isinstance(parameters["UXRCE_DDS_PRT"], int)


@pytest.mark.parametrize(
    "script",
    [
        "",
        "# only a comment\n",
        "1\t1\tA\t1\t6\n1\t1\tA\t2\t6\n",
        "1\t1\tA\t1\n",
        "1\t1\tA\tone\t6\n",
        "1\t1\tA\t1.5\t6\n",
        "1\t1\tA\t1\t2\n",
        "1\t1\tA_NAME_LONGER_THAN_16\t1\t6\n",
        "param set A 1\n",
    ],
)
def test_anything_but_typed_parameter_rows_is_refused(script):
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
    assert BASELINE_FILES == {
        "real": "real.params",
        "opti_track": "opti_track.params",
        "hil": "hil.params",
    }
