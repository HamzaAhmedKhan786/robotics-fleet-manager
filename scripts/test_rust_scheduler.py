"""Verify Python can call the Rust scheduling engine."""

import fleet_scheduler

robots = [
    ("AMR-001", True, 85.0, 12.0),
    ("AMR-002", True, 45.0, 5.0),
    ("AMR-003", False, 90.0, 2.0),
]

selected = fleet_scheduler.select_robot(robots)

print("Selected robot:", selected)

assert selected == "AMR-002"
print("Python-Rust integration successful!")
