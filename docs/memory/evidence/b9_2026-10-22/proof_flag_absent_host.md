# B9 (host) — against B8's tree (predecessors/)

| file | method | B9 items | whole module vs predecessor |
| --- | --- | --- | --- |
| `companion/hold_rewind.py` | guarded items removed | 5: `if raw in ('all', 'state'):`; `if (environ.get(FLAG_ENV) or '').strip() in ('1', 'state'):`; `b9: Any = None`; `if self.b9 is not None and self.b9.handles(pending):`; `if (environ.get(FLAG_ENV) or '').strip() in ('1', 'state'):` | **identical** |
| `companion/input_hold.py` | guarded items removed | 2: `state_mark: Any = None`; `if self.state_mark is not None:` | **identical** |
| `companion/stall_signal.py` | two nodes set back | the module docstring; DEFAULT_MS 150 -> 400 | **identical** |

Result: **ALL IDENTICAL** (beyond the stated changes).
