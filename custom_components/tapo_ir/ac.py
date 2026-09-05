"""Pure Tapo AC state parsing and payload validation."""
from __future__ import annotations

from typing import Any

REQUIRED_AC_FIELDS = frozenset({"P", "M", "T", "S", "D"})


class AcStateError(ValueError):
    """Raised when a complete AC command cannot be built safely."""


def parse_ac_status(child: dict[str, Any]) -> dict[str, int]:
    """Parse the compact P/M/T/S/D status returned for AC remotes."""
    state: dict[str, int] = {}
    if isinstance(ac_status := child.get("ac_status"), str):
        for part in ac_status.split("_"):
            if len(part) < 2 or part[0] not in REQUIRED_AC_FIELDS:
                continue
            try:
                state[part[0]] = int(part[1:])
            except ValueError:
                continue

    fallbacks = {
        "P": child.get("on"),
        "M": child.get("ac_mode"),
        "T": child.get("current_temp"),
        "S": child.get("wind_speed"),
        "D": child.get("wind_direct"),
    }
    for key, value in fallbacks.items():
        if key not in state and value is not None:
            try:
                parsed = int(value)
            except (TypeError, ValueError, OverflowError):
                continue
            if isinstance(value, float) and value != parsed:
                continue
            if key == "P" and parsed not in (0, 1):
                continue
            state[key] = parsed
    return state


def build_ac_payload(state: dict[str, int]) -> dict[str, Any]:
    """Build a command only when every required state field is known."""
    missing = sorted(REQUIRED_AC_FIELDS - state.keys())
    if missing:
        raise AcStateError(
            "The hub has not reported a complete AC state; missing "
            + ", ".join(missing)
        )
    if any(type(state[key]) is not int for key in REQUIRED_AC_FIELDS):
        raise AcStateError("AC state fields must be integers")
    if state["P"] not in (0, 1):
        raise AcStateError("AC power state must be 0 or 1")
    return {
        "power": bool(state["P"]),
        "on": bool(state["P"]),
        "mode": state["M"],
        "temp": state["T"],
        "wind_speed": state["S"],
        "wind_direct": state["D"],
    }
