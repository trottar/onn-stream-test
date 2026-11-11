# The proof (2026-11-11 20:31:35-20:32:17Z): `tools/h7_minigame_proof.py --system ps1 --state <kept copy> --as-is --runs 3 --rule rule.json`, per state

| state | expected | winner | agreement | values (each run) | reason | met | RetroArch after |
| --- | --- | --- | --- | --- | --- | --- | --- |
| begin | no winner yet | None | 3 of 3 | 0 / 0 ; 0 / 0 ; 0 / 0 | no winner yet | True | 0 |
| end P1 (won) | P1 | P1 | 3 of 3 | 140 / 70 ; 140 / 70 ; 140 / 70 | — | True | 0 |
| end P2 (won) | P2 | P2 | 3 of 3 | 133 / 140 ; 133 / 140 ; 133 / 140 | — | True | 0 |
| end P1 b (mid-fight, P1 ahead) | P1 | P1 | 3 of 3 | 140 / 100 ; 140 / 100 ; 140 / 100 | — | True | 0 |
| end P2 b (mid-fight, P2 ahead) | P2 | P2 | 3 of 3 | 110 / 140 ; 110 / 140 ; 110 / 140 | — | True | 0 |

**The proof MET:** begin → "no winner yet" 3 of 3; each of the four "end" states → its player 3 of 3.

The raw lines (JSON, one per state):
```
begin: {"system": "ps1", "seconds": 0, "state_loaded": true, "as_is": true, "runs": 3, "agreement": "3 of 3", "winner": null, "per_run": [{"winner": null, "values": {"P1": 0, "P2": 0}, "reason": "no winner yet"}, {"winner": null, "values": {"P1": 0, "P2": 0}, "reason": "no winner yet"}, {"winner": null, "values": {"P1": 0, "P2": 0}, "reason": "no winner yet"}], "reason": "no winner yet"}
end P1: {"system": "ps1", "seconds": 0, "state_loaded": true, "as_is": true, "runs": 3, "agreement": "3 of 3", "winner": "P1", "per_run": [{"winner": "P1", "values": {"P1": 140, "P2": 70}}, {"winner": "P1", "values": {"P1": 140, "P2": 70}}, {"winner": "P1", "values": {"P1": 140, "P2": 70}}]}
end P2: {"system": "ps1", "seconds": 0, "state_loaded": true, "as_is": true, "runs": 3, "agreement": "3 of 3", "winner": "P2", "per_run": [{"winner": "P2", "values": {"P1": 133, "P2": 140}}, {"winner": "P2", "values": {"P1": 133, "P2": 140}}, {"winner": "P2", "values": {"P1": 133, "P2": 140}}]}
end P1 b: {"system": "ps1", "seconds": 0, "state_loaded": true, "as_is": true, "runs": 3, "agreement": "3 of 3", "winner": "P1", "per_run": [{"winner": "P1", "values": {"P1": 140, "P2": 100}}, {"winner": "P1", "values": {"P1": 140, "P2": 100}}, {"winner": "P1", "values": {"P1": 140, "P2": 100}}]}
end P2 b: {"system": "ps1", "seconds": 0, "state_loaded": true, "as_is": true, "runs": 3, "agreement": "3 of 3", "winner": "P2", "per_run": [{"winner": "P2", "values": {"P1": 110, "P2": 140}}, {"winner": "P2", "values": {"P1": 110, "P2": 140}}, {"winner": "P2", "values": {"P1": 110, "P2": 140}}]}
```
