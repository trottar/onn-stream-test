#!/usr/bin/env python3
"""B41: flag absent = the CONFIRMED build's behaviour. For every edited file: the lines B41 removed (each must be one
of the stated replacements) and the lines it added (each must sit in a hunk guarded by the prompt / a claims key, or be
a stated pure insertion). Usage: proof_flag_absent.py BASE_COPY NEW_COPY. Reads only."""
import difflib, sys
from pathlib import Path

base, new = Path(sys.argv[1]), Path(sys.argv[2])
FILES = {
    "PrivyHub/app/src/main/java/streaming/PadSlots.kt": "pure insertion: five methods no B34 / B38 path calls",
    "PrivyHub/app/src/main/java/streaming/NativeControllerSender.kt": "the prompt's field; two lookups and the start line take today's branch when playerPrompt is null",
    "PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt": "every hunk guarded by playerPrompt (null without the property); the slot object's line ORs a false flag",
    "companion/plugins/games.py": "the players block under player_prompt=1; the claims kwarg None without pad_claims",
    "companion/pad_slots.py": "with_claims(slots, None) returns slots unchanged; claims defaults to None",
}
# the removed lines B41 replaces, each with what replaces it and why it is today's when the flag is absent
REPLACED = {
    "        padSlots?.beginStart(connectedPads())":
        "if (prompt != null) prompt.beginStart(...) else padSlots?.beginStart(connectedPads())  -- prompt null: today's",
    "            playerForDevice(device)":
        "(if (prompt != null) prompt.slotFor...(...) else playerForDevice(device))  -- prompt null: today's (key and motion)",
    "    private val padSlots: PadSlots? by lazy { if (PadSlotsFlag.fromSystem()) PadSlotsProcess.slots else null }":
        "PadSlotsFlag.fromSystem() || PlayerPromptFlag.fromSystem()  -- the second false without the property: today's",
    "                            \"?port=$VIDEO_PORT\" + (if (restart != null) \"&guard_end=1\" else \"\") + padSlotsQuery(),":
        "the same + (if (playerPrompt != null) ... else \"\")  -- \"\" without the property: today's",
    "                self._pad_slots_log.start(self._recovery, self._first(query, \"pad_slots\"))":
        "the same + claims=(None without pad_claims)  -- with_claims(x, None) is x: today's row",
    "                                              _pad_slots.updates_by_player(self._native_stream._session_io.controller))":
        "the same + claims=(None without pad_claims)  -- today's row",
    "    def start(self, recovery: Any, raw: str) -> list[dict[str, Any]] | None:":
        "+ claims: str | None = None  -- default None",
    "        slots = parse(raw)":
        "with_claims(parse(raw), claims)  -- claims None: parse(raw) itself",
    "    def heartbeat(self, recovery: Any, raw: str, values: dict[str, Any], updates_by_player: Any = None) -> None:":
        "+ claims: str | None = None  -- default None",
}
GUARDS = ("B41", "prompt", "Prompt", "claims", "player_count", "players")
fails = 0
for f, why in FILES.items():
    a = (base / f).read_text().splitlines(); b = (new / f).read_text().splitlines()
    removed, added_hunks = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag in ("replace", "delete"):
            removed += a[i1:i2]
        if tag in ("replace", "insert"):
            added_hunks.append(b[j1:j2])
    print(f"== {f}: {why}")
    for r in removed:
        ok = r in REPLACED
        print(f"   removed {'OK' if ok else 'UNSTATED'}: {r.strip()[:90]}  ->  {REPLACED.get(r, '?')}")
        fails += not ok
    pure = f.endswith("PadSlots.kt")
    for h in added_hunks:
        text = "\n".join(h)
        ok = pure or any(g in text for g in GUARDS)
        if not ok:
            print("   added UNGUARDED hunk:", text[:200]); fails += 1
    print(f"   added hunks: {len(added_hunks)}, lines: {sum(len(h) for h in added_hunks)}, removed lines: {len(removed)}")
print("UNSTATED / UNGUARDED:", fails)
print("PROVEN" if fails == 0 else "NOT PROVEN")
