"""B20: `PRIVYHUB_LINK_RECOVERY=1` -- one host line for the link-recovery stack.

It means exactly the six stack lines, each `=1`: PRIVYHUB_INPUT_HOLD, PRIVYHUB_INPUT_HOLD_B6, PRIVYHUB_INPUT_HOLD_B8,
PRIVYHUB_INPUT_HOLD_REWIND, PRIVYHUB_STALL_SIGNAL, PRIVYHUB_STALL_RESUME (B2 / B6 / B8 / B4-B9-B12 / B7 / B12-B16-B18),
and nothing more. An explicit individual flag wins (any value present, `0` included -- each module reads `0` as
ignored, i.e. off), so a bench can turn one part off. **Absent = today**: nothing imports this module, nothing is read.
Design: `docs/memory/evidence/b20_2026-10-24/design_written_before_code.md` (hashed before this code).

The six are read at import (`plugins/games.py`, `games/emulator_manager.py`) and at wire time (the `environ` the plugin
passes), so `apply` puts the implied ones into the process environment before the first read; both import sites call
it (idempotent). The service's `/proc/<pid>/environ` keeps the drop-in as written (the umbrella line); `describe` is
the readers' view of what it implies.
"""

from __future__ import annotations

from typing import Any, Iterable, MutableMapping, Mapping

FLAG_ENV = "PRIVYHUB_LINK_RECOVERY"
STACK = ("PRIVYHUB_INPUT_HOLD", "PRIVYHUB_INPUT_HOLD_B6", "PRIVYHUB_INPUT_HOLD_B8", "PRIVYHUB_INPUT_HOLD_REWIND",
         "PRIVYHUB_STALL_SIGNAL", "PRIVYHUB_STALL_RESUME")


def on(environ: Mapping[str, str]) -> bool:
    return (environ.get(FLAG_ENV) or "").strip() == "1"


def implied(environ: Mapping[str, str]) -> dict[str, str]:
    """The stack lines the umbrella adds: those not present (an explicit one, any value, wins); {} unless `=1`."""
    if not on(environ):
        return {}
    return {k: "1" for k in STACK if k not in environ}


def apply(environ: MutableMapping[str, str]) -> dict[str, Any]:
    """Puts the implied lines into `environ` (setdefault; idempotent). Returns what it did."""
    add = implied(environ)
    explicit = {k: environ[k] for k in STACK if k in environ and k not in add}
    for k, v in add.items():
        environ.setdefault(k, v)
    return {"umbrella": on(environ), "implied": sorted(add), "explicit": explicit}


def describe(lines: Iterable[str]) -> dict[str, Any] | None:
    """The readers' view, from a `KEY=VAL` list (a service's `/proc/<pid>/environ`): None without the umbrella line;
    else each of the six as it will act (`implied` or the explicit value)."""
    env: dict[str, str] = {}
    for line in lines:
        k, sep, v = str(line).partition("=")
        if sep:
            env[k] = v
    if FLAG_ENV not in env:
        return None
    if not on(env):
        return {"umbrella": env[FLAG_ENV][:32], "on": False, "stack": {}}
    return {"umbrella": "1", "on": True, "stack": {k: (f"explicit {env[k][:32]}" if k in env else "implied 1") for k in STACK}}
