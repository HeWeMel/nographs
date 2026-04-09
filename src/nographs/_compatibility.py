from ._types import T

# --- MyPyC issues ---

try:
    from mypy_extensions import trait
except (
    ModuleNotFoundError
):  # pragma: no cover  # Not reachable if mypy_extensions are installed

    def trait(cls: T) -> T:
        return cls
