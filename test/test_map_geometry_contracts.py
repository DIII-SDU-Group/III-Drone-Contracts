from iii_drone_contracts import (
    Bounds2D,
    ConductorGeometry,
    MapProjection,
    MapSourceStatus,
    MapState,
    Point2D,
    PolylineLayer,
    PoseProjection,
    PowerlineFrameStatus,
    TargetState,
)


def _round_trip(state: MapState) -> MapState:
    return MapState.model_validate_json(state.model_dump_json())


def test_empty_map_state_has_explicit_degraded_reason():
    state = MapState.empty()

    actual = _round_trip(state)

    assert actual.frame.status == MapSourceStatus.MISSING
    assert actual.degraded_reason == "no map sources available"


def test_live_only_map_state_distinguishes_live_perception():
    state = MapState(
        frame=PowerlineFrameStatus(
            status=MapSourceStatus.AVAILABLE,
            reference_source="live_perception",
        ),
        live_conductors=[
            ConductorGeometry(
                conductor_id="live-1",
                source="live_perception",
                points=[Point2D(x=0.0, y=0.0), Point2D(x=1.0, y=0.0)],
            )
        ],
        auto_fit_bounds=Bounds2D(min_x=0.0, min_y=0.0, max_x=1.0, max_y=1.0),
    )

    actual = _round_trip(state)

    assert len(actual.live_conductors) == 1
    assert actual.stored_overview_conductors == []
    assert actual.auto_fit_bounds.max_x == 1.0


def test_overview_only_map_state_distinguishes_stored_geometry():
    state = MapState(
        frame=PowerlineFrameStatus(
            status=MapSourceStatus.AVAILABLE,
            reference_source="stored_overview",
        ),
        stored_overview_conductors=[
            ConductorGeometry(
                conductor_id="stored-1",
                source="stored_overview",
                points=[Point2D(x=-1.0, y=0.0), Point2D(x=1.0, y=0.0)],
            )
        ],
    )

    actual = _round_trip(state)

    assert actual.live_conductors == []
    assert actual.stored_overview_conductors[0].source == "stored_overview"


def test_combined_map_state_supports_layers_and_projections():
    state = MapState(
        active_projection=MapProjection.TOP_DOWN,
        frame=PowerlineFrameStatus(status=MapSourceStatus.AVAILABLE, reference_source="stored_overview"),
        live_conductors=[
            ConductorGeometry(
                conductor_id="live-1",
                source="live_perception",
                source_status=MapSourceStatus.STALE,
                points=[Point2D(x=0.0, y=0.5)],
            )
        ],
        stored_overview_conductors=[
            ConductorGeometry(
                conductor_id="stored-1",
                source="stored_overview",
                points=[Point2D(x=0.0, y=0.0), Point2D(x=2.0, y=0.0)],
            )
        ],
        drone_pose=PoseProjection(
            projection=MapProjection.TOP_DOWN,
            position=Point2D(x=0.5, y=0.5),
            yaw_degrees=90.0,
            altitude_m=2.0,
        ),
        target_state=TargetState(target_id="target-1", position=Point2D(x=1.0, y=0.0), status=MapSourceStatus.AVAILABLE),
        target_history=[Point2D(x=0.5, y=0.0)],
        trajectory=PolylineLayer(label="trajectory", points=[Point2D(x=0.0, y=0.0), Point2D(x=1.0, y=1.0)]),
        drone_trail=PolylineLayer(label="drone_trail", points=[Point2D(x=0.25, y=0.25)]),
        auto_fit_bounds=Bounds2D(min_x=-1.0, min_y=-1.0, max_x=2.0, max_y=1.0),
    )

    actual = _round_trip(state)

    assert MapProjection.POWERLINE_ORTHOGONAL in actual.projection_options
    assert MapProjection.TOP_DOWN in actual.projection_options
    assert actual.live_conductors[0].source_status == MapSourceStatus.STALE
    assert actual.target_state.status == MapSourceStatus.AVAILABLE
    assert actual.drone_trail.points[0].x == 0.25
