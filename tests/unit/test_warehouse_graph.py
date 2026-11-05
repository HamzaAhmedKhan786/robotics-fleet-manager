"""Unit tests for warehouse shortest-path routing."""

import pytest

from apps.backend.services.warehouse_graph import (
    build_demo_warehouse,
    shortest_distance,
)


@pytest.fixture
def graph():
    return build_demo_warehouse()


def test_same_station(graph):
    assert shortest_distance(graph, "STATION-A1", "STATION-A1") == 0.0


def test_direct_connection(graph):
    assert shortest_distance(graph, "STATION-A1", "STATION-A2") == 10.0


def test_shortest_path_across_warehouse(graph):
    assert shortest_distance(graph, "STATION-A1", "STATION-B3") == 28.0


def test_unknown_station(graph):
    assert shortest_distance(graph, "UNKNOWN", "STATION-A1") is None


def test_unreachable_station(graph):
    graph["ISOLATED"] = {}
    assert shortest_distance(graph, "ISOLATED", "STATION-A1") is None


def test_rejects_negative_distance(graph):
    graph["STATION-A1"]["STATION-A2"] = -5.0

    with pytest.raises(ValueError):
        shortest_distance(graph, "STATION-A1", "STATION-B3")


def test_rejects_invalid_weight(graph):
    graph["STATION-A1"]["STATION-A2"] = float("nan")

    with pytest.raises(ValueError):
        shortest_distance(graph, "STATION-A1", "STATION-B3")
