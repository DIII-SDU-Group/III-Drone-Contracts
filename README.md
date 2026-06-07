# III-Drone-Contracts

ROS-free API contract package for the III-Drone operator/runtime boundary.

This repository owns the Pydantic models, stable command identifiers, enums,
API metadata, and JSON schema used by:

- `iii-runtime-api` in `III-Drone-Runtime`.
- the thin ground-control proxy in `III-Drone-GC`.
- generated TypeScript types consumed by the GUI v2 frontend.

## Ownership Rules

- This package must remain importable without ROS 2 installed.
- Do not import `rclpy`, generated ROS messages, MAVSDK, `III-Drone-Interfaces`,
  `III-Drone-Runtime`, or other runtime-heavy packages here.
- Keep the package focused on JSON-serializable API contracts and schema
  generation helpers.

## Development

```bash
python3 -m pytest test
```

Generate TypeScript contracts from the workspace root:

```bash
python3 src/III-Drone-Contracts/scripts/generate_typescript.py \
  --output src/III-Drone-GC/frontend/src/generated/contracts.ts
```

Generated TypeScript files must carry a "do not edit manually" header and be
refreshed whenever contract models change.

Check freshness without modifying generated files:

```bash
python3 src/III-Drone-Contracts/scripts/generate_typescript.py \
  --output src/III-Drone-GC/frontend/src/generated/contracts.ts \
  --check
```

The workspace full-suite runner also performs this check:

```bash
scripts/workspace/run_iii_test_suite.sh
```
