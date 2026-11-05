
"""Type declarations for the compiled Rust scheduler."""

def select_robot(
    robots: list[tuple[str, bool, float, float]],
) -> str | None: ...
