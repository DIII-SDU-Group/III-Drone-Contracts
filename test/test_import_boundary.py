import json
import subprocess
import sys


FORBIDDEN_IMPORT_PREFIXES = (
    "rclpy",
    "iii_drone_interfaces",
    "iii_drone_runtime",
    "mavsdk",
    "pymavlink",
)


def test_contracts_import_without_ros_runtime_dependencies():
    # Test collection for the legacy ROS GC-node tests necessarily imports rclpy
    # into this interpreter.  The contract boundary is instead that importing
    # this package in a fresh interpreter must not load runtime dependencies.
    # Keeping the assertion process-local makes it independent of test order.
    probe = """
import importlib
import json
import sys

module = importlib.import_module('iii_drone_contracts')
forbidden = ('rclpy', 'iii_drone_interfaces', 'iii_drone_runtime', 'mavsdk', 'pymavlink')
print(json.dumps({'api_version': module.API_VERSION, 'forbidden': [name for name in sys.modules if name.startswith(forbidden)]}))
"""
    completed = subprocess.run(
        [sys.executable, "-c", probe],
        check=True,
        capture_output=True,
        text=True,
    )
    observed = json.loads(completed.stdout)

    assert observed["api_version"] == "v2alpha1"
    assert observed["forbidden"] == []
