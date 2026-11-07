"""Explicit, validated simulation checkpoint state transitions."""
from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Checkpoint:
    elapsed: float = 0.0
    paused: bool = False
    completed: bool = False
    version: int = 0


def transition(cp: Checkpoint, action: str, duration: float, delta: float = 0.0) -> Checkpoint:
    if duration <= 0 or delta < 0:
        raise ValueError("Invalid duration or delta")
    if action == "pause" and not cp.completed:
        return replace(cp, paused=True, version=cp.version + 1)
    if action == "resume" and not cp.completed:
        return replace(cp, paused=False, version=cp.version + 1)
    if action == "advance" and not cp.paused and not cp.completed:
        elapsed = min(duration, cp.elapsed + delta)
        return replace(cp, elapsed=elapsed, completed=elapsed >= duration, version=cp.version + 1)
    if action == "restart":
        return Checkpoint(version=cp.version + 1)
    raise ValueError(f"Invalid checkpoint transition: {action}")
