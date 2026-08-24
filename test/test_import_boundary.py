import importlib
import sys


FORBIDDEN_IMPORT_PREFIXES = (
    "rclpy",
    "iii_drone_interfaces",
    "iii_drone_runtime",
    "mavsdk",
    "pymavlink",
)


def test_contracts_import_without_ros_runtime_dependencies():
    module = importlib.import_module("iii_drone_contracts")

    assert module.API_VERSION == "v2alpha1"
    assert not any(name.startswith(FORBIDDEN_IMPORT_PREFIXES) for name in sys.modules)
