"""B69 (test hygiene, B53's helper): every temporary directory a tests/gamecube_session run creates is removed when that run ends.

HOME-6 prep found ~6.9 GiB of these suites' fixture trees (formatted 8-MB cards, fake game trees) left in the hub's /tmp
tmpfs by B49-B52's runs, which never removed their mkdtemp() dirs. Imported by each test module; it tracks only the
dirs made in this process and removes them at exit (never anything else)."""

from __future__ import annotations

import atexit
import shutil
import tempfile

_made: list[str] = []
_mkdtemp = tempfile.mkdtemp


def _tracked(*args, **kwargs):
    d = _mkdtemp(*args, **kwargs)
    _made.append(d)
    return d


if getattr(tempfile.mkdtemp, "__name__", "") != "_tracked":
    tempfile.mkdtemp = _tracked
    atexit.register(lambda: [shutil.rmtree(d, ignore_errors=True) for d in _made])
