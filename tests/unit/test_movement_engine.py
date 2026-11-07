"""Rust movement adapter tests; uses the compiled PyO3 extension."""
import fleet_scheduler
import pytest

from apps.backend.services.movement_engine import sample_position, station_position


def test_rust_exports() -> None:
    assert callable(fleet_scheduler.shortest_path)
    assert callable(fleet_scheduler.sample_route)
    assert callable(fleet_scheduler.estimate_energy)


def test_station_coordinates() -> None:
    assert station_position("STATION-A1") == (-6.0, -4.0)
    assert station_position("STATION-Z9") is None


def test_rust_movement_halfway_and_end() -> None:
    route = ["STATION-A1", "STATION-A2", "STATION-B2"]
    x, z, progress = sample_position(route, 7, 14)
    assert (x, z, progress) == pytest.approx((0.0, -3.0, 0.5))
    assert sample_position(route, 20, 14) == pytest.approx((0.0, 4.0, 1.0))


def test_invalid_route() -> None:
    with pytest.raises(ValueError, match="Unsupported station"):
        sample_position(["STATION-Z9"], 0, 10)
