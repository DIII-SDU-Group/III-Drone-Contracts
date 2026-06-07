from setuptools import find_packages, setup

package_name = "iii_drone_contracts"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools", "pydantic>=2,<3"],
    tests_require=["pytest"],
    zip_safe=True,
    maintainer="ffn",
    maintainer_email="ffn@sdu.dk",
    description="ROS-free Pydantic API contracts for III-Drone operator/runtime APIs.",
    license="Proprietary",
)
