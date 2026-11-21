"""B110: the hub's party mini game — an emulator title played from inside the board game, its result read from the
title's own end screen, everything handed back.

Only with PRIVYHUB_PARTY=1 (the board as the game session, B108) **and** PRIVYHUB_H7=1 (the end-screen watcher and
the rules folder, B103 / B105): `plugins/games.py` imports this module then; either absent = today (no route).

  GET  party-minigames            the titles whose rules folder holds a version-2 spec, a kept begin state and a
                                  sidecar <game id>.party.json ({"players": n, "scores": {end class: [n numbers]}});
                                  ids opaque to the board
  POST party-minigame-start       ?id=<token>&seats=a,b — answers at once ("starting"); the mini game's own actor: the
                                  board's session set aside (it keeps running), the title launched by the manager,
                                  paused, the pads routed (seat a's pad → port 1 …), the stream switched to the title
                                  (if up), B103's start (the begin state, the watch), the pause released → "playing"
  GET  party-minigame-result      starting / playing (recognised) / ended (class, scores in the order of the seats
                                  given) / given_up (why) — never a guess
  POST party-minigame-end         taken at once; the actor: the watch stopped, the title stopped, the route cleared,
                                  the board's session back, the stream switched back (if up); safe to call twice;
                                  also done by the hub itself when the board dies, END / another launch reach stop,
                                  the caller does not come back, or the start is stuck

B114 (the hang PP-H3's second mini game hit): **no lock is held across a launch, a stream start or stop, or a wait on
another thread.** The start held the manager's lock across the stream switch, whose end waited on the live bitrate
controller's lock, held by a client-health report waiting on the manager's lock. Now each manager call takes the
manager's lock for that call only; the stream switch runs on a helper thread with nothing held and is waited for at
most SWITCH_LIMIT_S; the layer's own lock guards its fields only. While a mini game is on, **every route answers
within 2 s**: `status` / `native-stream-status` from a snapshot when a part cannot be read at once, the result from
the mini game's own state, Home / RESUME / END and the board's end **taken at once** onto the mini game's own queue
and **acted on in order** by its actor (RESUME answers with its own start's answer, which the onn needs). A start
still `starting` after START_LIMIT_S is given up by the hub; END always works — if the actor is stuck in a step past
STEP_GRACE_S the end runs without it.

One row per step in the party log (logs/games/party.jsonl), field names and numbers only.

B127 — a mini game **under the title's cheat setup** (the users' Extras setup, e.g. everything unlocked): the sidecar
may carry `"cheat": {"source_index": n, "enabled_cheat_indexes": [...], "profile_id": "<the setup's id>"}` beside
`players` / `scores` / `places_to_scores` (no cheat name); its begin is the setup's own `<game id>.<the profile_id's
first 12 characters>.state` in the rules folder (listed only when it is there). The start checks the setup on the hub
first (`cheat_profiles`: that `profile_id` with the same source and indexes, and B85's expansion giving them back) — else
400 SETUP_GONE, nothing set aside or launched; the title is launched by **the plugin's own launch path with the onn's
Extras query** (`id`, `cheat_source`, `cheat_indexes`), and the session's `profile_id` must then be the sidecar's (else
given up, the title stopped). `h7-start` loads the setup's begin into the setup's own `states/<core>/` (B127 in
`h7_minigame`). A sidecar without `cheat` → today.

B137 — **nothing a player presses reaches a held title before the go.** From the launch's answer to the go the title
is never resumed: paused → the bridge's mute on (every pad neutral, every report dropped) → the watch's load (the
begin) → ADVANCE_FRAMES × RetroArch's `FRAMEADVANCE`, ADVANCE_GAP_S apart (the PS1 core shows a state loaded into a
paused core only after a frame; the N64 core's load runs a frame itself, reading the pads) → the mute off (row
`minigame_frame_advance`) → the watcher reads the redrawn, paused window (RetroArch's "Paused." corner masked) → ready.
The go: the route, the planned switch, the resume — no second load when the title has not run since its begin was
loaded. A practice's way back pauses first, then clears the route and switches, then prepares again the same way.

B139 — a party mini game's own launch writes PARTY_SESSION_SETTINGS into its session config (RetroArch's on-screen
text off: no notices, no "Paused.", no content banner); the users' launches are untouched; the watch reads unmasked.
B140 — after the paused load, frames in ADVANCE_STEPS with a grab after each, until the window moved >= BEGIN_MOVED
from its pre-load picture (or the start is read); never → given up at once ("the title did not show its starting
point"). B141 — from a held title's launch to the go, and on every way back, the pads' Select is not passed (RetroArch's
hotkeys are pairs with Select); from the go on, as today.
B143 — every planned switch arms the audio sender: the new process's sound continues the last run's sequence and
timestamp (the app drops a frame behind what it has played: a new stream at sequence 0 was silent until it passed it).
B144 — a practice's switch arms the stream: the encoder draws the practice's band (B151: "PRACTICE — press Select (Share)
to go back") on the onn's picture (the title's window untouched); the way back's start takes it off. B145 — Select stays
held through a practice too, until a real go. B151 — a practice is left by a Select press on any pad (one already down
at its hand-over counts only once let go and pressed again), or by its time; Start reaches the title as in a real one.
B153 — every planned switch arms the stream's start for its process: the old sound's capture and the old encoder are
killed at once (a SIGTERM'd capture could block on its undrained pipe until a 2-s wait ran out: the long switches), and
the new sound starts before the encoder's 0.75-s check. Every other start (the users') is today's.
B155 — the `minigame_launch` row carries "keys_written": the session config read back after the launch — written by it,
both PARTY_SESSION_SETTINGS keys in it once each with their values.
B158 — a sidecar's `"result": "winner"`: the scores one-hot for the winner (version 2: end_Pk = port k won; version 3:
place 1), the ended row and the result carry `"winner"` (that port's seat). Without the key: today.
B178 — a sidecar's `"result": "score"` with a version-4 spec of n sides (B178's learner: each side's number read on the
final screen): at `ended` the numbers read, port by port, as the scores (the real numbers), `"winner"` the seat of the
one side strictly ahead, null on a tie (the board's draw); a read without n whole numbers → given up; an unreadable
screen is `unknown` as today. Without the key: today.
B191 — a sidecar's `"result": "letters"` with a version-5 spec (each player's letters read in its corner; the player
whose letters spell the word lost): listed as B158's winner entry (end_Pk: port k won). Any other shape: not listed.
Without the key: today.
B182 — a version-4 watch that sees the final screen K times with a number on it not read ends `unreadable`; the
mini game is given up then (why: "the final screen was seen and a number on it was not read"), no scores, no winner —
never the 900-s wait. Versions 2 / 3 never end so: today.
B162 — `POST party-minigame-only?game=<id>` (loopback; `?clear=1` clears): the add-a-game tool's solo setting, kept in
memory only (any restart clears it) — while set, `party-minigames` lists that title alone for its player count. Never
set: today.
"""
from __future__ import annotations

import collections
import hashlib
import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote

import h7_live_read as live
import party_session as party

PLAY_LIMIT_S = 900.0        # a match not ended within this is given up (a draw to the board)
UNKNOWN_LIMIT_S = 30.0      # an unknown screen read this long running is given up
POLL_GONE_S = 120.0         # no result call this long while playing: the caller is gone, the hub ends it
END_WAIT_S = 60.0           # no end call this long after a final state: the hub ends it
TICK = 0.5
FINAL = ("ended", "given_up")
# B114
START_LIMIT_S = 30.0        # a mini game still starting after this is given up by the hub (a normal start ~5 s)
SWITCH_LIMIT_S = 15.0       # one stream switch's bound (the real one ~1-4 s)
STEP_GRACE_S = 3.0          # END waits this long for the actor to take it before the end runs without the actor
TAKE_WAIT_S = 1.5           # a taken Home / END / board end answers with its own answer if done within this
RESUME_WAIT_S = 25.0        # a taken RESUME waits its turn this long (the onn's read timeout is 30 s)
READ_WAIT_S = 1.5           # a status read waits this long before the last snapshot answers
EMU_TRY_S = 0.2             # the manager's lock is tried in steps of this, an END checked between
MANAGER_BOUND_S = 10.0      # the end's manager calls: give up the wait after this (the title then ended directly)
# B115
PLANNED_GRACE_S = 3.0       # the planned-switch window stays open this long after the switch's start returns
# the onn's calls taken while a mini game is on (route → kind)
PLACES_VERSION = 3          # B123: an end-screen spec with a place for every player (B122)
SCORE_VERSION = 4           # B178: an end-screen spec with each side's number (B178)
LETTERS_VERSION = 5         # B191: an end-screen spec reading each player's letters (the one who spelled the word lost)
TAKEN = {"native-stream-stop": "home", "native-stream-start": "resume_start", "native-stream-ready": "resume_ready",
         "stop": "end"}
# B127
SETUP_GONE = "the cheat setup this mini game names is not on the hub (or its cheats changed): nothing was launched"
SETUP_CHECK_S = 1.5         # the setup check's one manager call: given up after this (the start refused, nothing done)
NOT_UNDER_SETUP = "the title did not start under its cheat setup"
# B131: the onn's SAVE / LOAD while a mini game is starting or playing
STATE_REFUSED = {"save-state": "not during a mini game: nothing was saved",
                 "load-state": "not during a mini game: nothing was loaded"}
_HEX64 = re.compile(r"^[0-9A-Fa-f]{64}$")
# B133 / B134: the title prepared behind the board, handed over on the board's go; practice
PRACTICE_S = 90.0          # a practice left after this long playing (or by the Select button on any pad, B151)
XUSB_BACK = 0x0020         # the pad report's Select (Back / Share) bit (native_session_io: XUSB_BACK)
NO_GO = "no mini game is waiting for the go"
NOT_RECOGNISED = "the title's start screen was not recognised"
# B139: a party mini game's own launch writes these into its session config (RetroArch's on-screen text off: the
# notices, "Paused." and the content banner — nothing of RetroArch's on the title's window, paused or running)
PARTY_SESSION_SETTINGS = {"video_font_enable": "false", "menu_show_load_content_animation": "false"}
SESSION_CONFIG_NAME = "privyhub-session.cfg"   # B155: where the emulator writes them (read back after the launch)
PARTY_LABEL_MASK = False    # B139: no text left on the window, so the watch reads it unmasked
# B137
ADVANCE_FRAMES = 2          # B137's fixed count (B140: replaced by ADVANCE_STEPS; kept for the row's history)
ADVANCE_GAP_S = 0.05        # between FRAMEADVANCEs (>= 50 ms: each one counts; 2 ms apart they merge)
# B140: after the paused load, frames in steps until the window has moved from its pre-load picture (or the start read)
ADVANCE_STEPS = (0, 2, 4, 8, 16, 30)   # frames per step: cumulative 0, 2, 6, 14, 30, 60 (the cap)
ADVANCE_SETTLE_S = 0.08     # after a step's last frame, before its grab
BEGIN_MOVED = 0.20          # the share of 64 x 48 cells moved > 16 grey levels: the begin is on the window (H7-D2:
                            # a paused window 0.0, RetroArch's notices <= 0.10, the boot frame -> the begin >= 0.51)
NO_BEGIN = "the title did not show its starting point"
# B162: the add-a-game tool's one-title setting (party-minigame-only, loopback)
NOT_LISTED = "not a listed mini game: nothing set"

_local = threading.local()


def inside() -> bool:
    """True on the mini game's own threads running a taken call or a bounded read (they take today's path)."""
    return bool(getattr(_local, "inside", False))


class _Abort(Exception):
    """The start's steps stop: an end was asked for (or done) while starting."""


class PlannedSwitch:
    """B115: the recovery told that a capture restart is planned (`recovery._planned_switch`, set only here): while
    the window is open the client's video-stall datagrams (stall / stall end) and its desync are not taken — no
    client_stall, no desync_pause, no stall save, no stall_handover_v2, no key to the board. The window opens just
    before a mini game's switch and closes PLANNED_GRACE_S after the switch's start returns. What still counts: the
    controller's silence (the pads' packets stopping), a stall that outlasts the window, the recovery's own monitor."""

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self._lock = threading.Lock()
        self.seq = 0
        self.windows: dict[int, dict] = {}        # each switch's own window (two may overlap by their grace)

    def open(self, which: str, bound_s: float) -> int:
        with self._lock:
            self.seq += 1
            now = self.clock()
            self.windows[self.seq] = {"which": which, "opened_at": now, "until": now + bound_s,
                                      "counts": {"stall": 0, "end": 0, "desync": 0}}
            for old in [k for k in self.windows if k <= self.seq - 8]:
                del self.windows[old]
            return self.seq

    def close_after(self, seq: int, grace_s: float) -> float | None:
        with self._lock:
            w = self.windows.get(seq)
            if w is None:
                return None
            w["until"] = min(w["until"], self.clock() + grace_s)
            return w["until"]

    def _covering(self, at: float) -> dict | None:
        for k in sorted(self.windows, reverse=True):
            w = self.windows[k]
            if w["opened_at"] <= at <= w["until"]:
                return w
        return None

    def covers(self, at: float | None = None) -> bool:
        with self._lock:
            return self._covering(self.clock() if at is None else at) is not None

    def swallow(self, what: str, at: float | None = None) -> bool:
        """True (and counted) when `what` ("stall" / "end" / "desync") falls in an open window: not taken."""
        with self._lock:
            w = self._covering(self.clock() if at is None else at)
            if w is None:
                return False
            w["counts"][what] = w["counts"].get(what, 0) + 1
            return True

    def report(self, seq: int) -> dict | None:
        with self._lock:
            w = self.windows.get(seq)
            if w is None:
                return None
            return {"window": w["which"], "open_s": round(w["until"] - w["opened_at"], 2),
                    "stalls_not_taken": w["counts"]["stall"], "stall_ends_not_taken": w["counts"]["end"],
                    "desyncs_not_taken": w["counts"]["desync"]}


class PartyMinigames:
    def __init__(self, plugin: Any, environ=os.environ, clock=time.monotonic):
        self.p = plugin
        self.emu = plugin._emulator
        self.environ = environ
        self.clock = clock
        self._salt = os.urandom(8)
        self._lock = threading.Lock()           # the fields below and each mini game's; never held across a call
        self._cond = threading.Condition(self._lock)
        self.mg: dict | None = None            # the current (or last) mini game
        self.play_limit_s, self.unknown_limit_s = PLAY_LIMIT_S, UNKNOWN_LIMIT_S
        self.poll_gone_s, self.end_wait_s, self.tick = POLL_GONE_S, END_WAIT_S, TICK
        self.start_limit_s, self.switch_limit_s, self.step_grace_s = START_LIMIT_S, SWITCH_LIMIT_S, STEP_GRACE_S
        self.practice_s = PRACTICE_S               # B134
        self.advance_frames, self.advance_gap_s = ADVANCE_FRAMES, ADVANCE_GAP_S     # B137
        self.advance_steps, self.advance_settle_s, self.begin_moved = ADVANCE_STEPS, ADVANCE_SETTLE_S, BEGIN_MOVED  # B140
        self.stream_needed = True               # B112's bench sets False (no stream, no switch)
        self._reads: dict[str, dict] = {}       # B114: the last good answer of each bounded read, its helper
        self.only: dict | None = None           # B162: the title under a solo's test (memory only), else None

    # --- rows ---------------------------------------------------------------------------------------------------------
    def row(self, fields: dict) -> None:
        party.row(self.emu._project_path, fields)

    # --- the list -----------------------------------------------------------------------------------------------------
    def _token(self, game: str) -> str:
        return "mg_" + hashlib.sha256(self._salt + game.encode()).hexdigest()[:12]

    def _entries(self) -> dict[str, dict]:
        """{token: {"game", "players", "scores", "classes"}} for every title that has all three files."""
        folder = live.rules_folder(self.environ)
        out: dict[str, dict] = {}
        try:
            names = sorted(p.name for p in folder.iterdir())
        except OSError:
            return out
        from h7_minigame import endscreen
        for name in names:
            if not name.endswith(".endscreen.json"):
                continue
            game = name[: -len(".endscreen.json")]
            if not live._ID.match(game):
                continue
            try:
                spec, _arrays = endscreen().load_spec(folder / name)
                side = json.loads((folder / f"{game}.party.json").read_text(encoding="utf-8"))
                cheat = self._cheat_of(side)                            # B127: None without `cheat` (today)
                if cheat is None:
                    state = folder / f"{game}.state"
                else:
                    from h7_minigame import setup_begin_name
                    state = folder / setup_begin_name(game, cheat["profile_id"])
                if not state.is_file() or state.stat().st_size <= 0:
                    continue
                n = int(side["players"])
                more = {"cheat": cheat} if cheat is not None else {}
                if "result" in side:                                    # B158: winner-only (absent: today)
                    entry = (self._score_entry(spec, side, n) if side.get("result") == "score"     # B178
                             else self._letters_entry(spec, side, n) if side.get("result") == "letters"   # B191
                             else self._winner_entry(spec, side, n))
                    record = self.p._find_game_by_id(game) if entry is not None else None
                    if entry is None or record is None:
                        continue
                    out[self._token(game)] = {"game": game, **entry, **more, "title": str(record.get("title") or "")}
                    continue
                if spec.get("version") == PLACES_VERSION or "places_to_scores" in side:
                    entry = self._places_entry(spec, side, n)          # B123: a place for every player
                    record = self.p._find_game_by_id(game) if entry is not None else None
                    if entry is None or record is None:
                        continue
                    out[self._token(game)] = {"game": game, **entry, **more, "title": str(record.get("title") or "")}
                    continue
                scores = {str(k): [int(x) if float(x).is_integer() else float(x) for x in v]
                          for k, v in dict(side["scores"]).items()}
                ends = list(spec["end_classes"])
                if n < 1 or n > 4 or sorted(scores) != sorted(ends) or any(len(v) != n for v in scores.values()):
                    continue
                record = self.p._find_game_by_id(game)
                if record is None:
                    continue
            except Exception:
                continue
            out[self._token(game)] = {"game": game, "players": n, "scores": scores, "start_class": spec["start_class"],
                                      **more, "title": str(record.get("title") or "")}
        return out

    @staticmethod
    def _cheat_of(side: dict) -> dict | None:
        """B127: the sidecar's `cheat` (the setup the launch needs), checked; None without one; ValueError when malformed
        (the title is then not listed, as any malformed sidecar)."""
        if "cheat" not in side:
            return None
        c = side["cheat"]
        if not isinstance(c, dict):
            raise ValueError("cheat is an object")
        src, idx, pid = c.get("source_index"), c.get("enabled_cheat_indexes"), c.get("profile_id")
        if type(src) is not int or src < 0:
            raise ValueError("source_index is a non-negative integer")
        if (not isinstance(idx, list) or not idx or any(type(i) is not int or i < 0 for i in idx)
                or len(set(idx)) != len(idx)):
            raise ValueError("enabled_cheat_indexes are distinct non-negative integers")
        if not isinstance(pid, str) or not _HEX64.match(pid):
            raise ValueError("profile_id is the setup's id")
        return {"source_index": src, "enabled_cheat_indexes": sorted(idx), "profile_id": pid.upper()}

    @staticmethod
    def _places_entry(spec: dict, side: dict, n: int) -> dict | None:
        """B123: `{"players": n, "places_to_scores": [s1..sn]}` (left out: n, n-1, ..., 1) with a version-3 spec of n
        ports -> the entry, else None (not listed)."""
        if spec.get("version") != PLACES_VERSION or "scores" in side or not 2 <= n <= 4:
            return None
        if int((spec.get("places") or {}).get("ports", 0)) != n:
            return None
        raw = side.get("places_to_scores", list(range(n, 0, -1)))
        if not isinstance(raw, list) or len(raw) != n:
            return None
        p2s = [int(x) if float(x).is_integer() else float(x) for x in raw]
        return {"players": n, "scores": None, "places_to_scores": p2s, "start_class": spec["start_class"]}

    @staticmethod
    def _winner_entry(spec: dict, side: dict, n: int) -> dict | None:
        """B158: `{"players": n, "result": "winner"}` -> the entry, else None (not listed). A version-2 spec's end
        classes must be exactly end_P1..end_Pn (end_Pk: port k won); a version-3 spec of n ports: place 1 won. The
        scores one-hot (1 for the winner, 0 for the rest); `winner_of` / `winner_places` say where the winner is read."""
        if side.get("result") != "winner" or "scores" in side or "places_to_scores" in side or not 2 <= n <= 4:
            return None
        start = {"start_class": spec["start_class"]}
        if spec.get("version") == PLACES_VERSION:
            if int((spec.get("places") or {}).get("ports", 0)) != n:
                return None
            return {"players": n, "scores": None, "places_to_scores": [1] + [0] * (n - 1), "winner_places": True,
                    **start}
        ends = [f"end_P{k}" for k in range(1, n + 1)]
        if sorted(spec.get("end_classes") or []) != sorted(ends):
            return None
        return {"players": n, "scores": {c: [1 if j == k else 0 for j in range(n)] for k, c in enumerate(ends)},
                "winner_of": {c: k + 1 for k, c in enumerate(ends)}, **start}

    @staticmethod
    def _score_entry(spec: dict, side: dict, n: int) -> dict | None:
        """B178: `{"players": n, "result": "score"}` with a version-4 spec of n sides -> the entry (each side's number
        read at the end; the winner the side strictly ahead, a tie a draw), else None (not listed)."""
        if side.get("result") != "score" or "scores" in side or "places_to_scores" in side or not 2 <= n <= 4:
            return None
        if spec.get("version") != SCORE_VERSION or int((spec.get("score") or {}).get("sides", 0)) != n:
            return None
        return {"players": n, "scores": None, "score_read": True, "start_class": spec["start_class"]}

    @staticmethod
    def _letters_entry(spec: dict, side: dict, n: int) -> dict | None:
        """B191: `{"players": 2, "result": "letters"}` with a version-5 spec whose end classes are end_P1, end_P2
        (end_Pk: port k won — the other player's letters spelled the word) -> B158's winner entry, else None (not
        listed). Neither or both spelled, or a corner not read, never ends (no result)."""
        if side.get("result") != "letters" or "scores" in side or "places_to_scores" in side or n != 2:
            return None
        ends = [f"end_P{k}" for k in range(1, n + 1)]
        if spec.get("version") != LETTERS_VERSION or sorted(spec.get("end_classes") or []) != ends:
            return None
        return {"players": n, "scores": {c: [1 if j == k else 0 for j in range(n)] for k, c in enumerate(ends)},
                "winner_of": {c: k + 1 for k, c in enumerate(ends)}, "start_class": spec["start_class"]}

    def listing(self) -> dict:
        entries = self._entries()
        only = self.only
        if only is not None:                     # B162: the title under test alone for its player count
            entries = {t: e for t, e in entries.items()
                       if e["players"] != only["players"] or e["game"] == only["game"]}
        return {"ok": True, "minigames": [{"id": t, "players": e["players"], "title": e["title"]}   # B134: the name
                                          for t, e in sorted(entries.items())]}

    def set_only(self, game_text: str, clear_text: str) -> dict:
        """B162: a bench setting for the add-a-game tool's solo — while set, `party-minigames` lists that title alone for
        its player count (the other counts as they are). Kept in memory only: any restart clears it. One party row when
        set and one when cleared, no title or id in either."""
        if str(clear_text or "").strip():
            if str(clear_text).strip() != "1":
                raise ValueError("clear is 1")
            with self._lock:
                was, self.only = self.only, None
            if was is not None:
                self.row({"step": "minigame_only", "on": False})
            return {"ok": True, "only": False}
        game = str(game_text or "").strip()
        entry = next((e for e in self._entries().values() if e["game"] == game), None) if game else None
        if entry is None:
            raise ValueError(NOT_LISTED)
        with self._lock:
            self.only = {"game": game, "players": entry["players"]}
        self.row({"step": "minigame_only", "on": True, "players": entry["players"]})
        return {"ok": True, "only": True, "players": entry["players"]}

    # --- start --------------------------------------------------------------------------------------------------------
    def start(self, token: str, seats_text: str, bench: bool = False, hold: bool = False) -> dict:
        self.stream_needed = not bench           # B112: with the bench word, the watcher runs with no stream
        if not party.active(self.emu):
            self.row({"step": "minigame_refused", "why": "the board game is not the running session"})
            raise ValueError("the board game is not the running session")
        with self._lock:
            if self.mg is not None and not self._finished(self.mg):
                raise ValueError("a mini game is already on")
        entry = self._entries().get(str(token or "").strip())
        if entry is None:
            raise ValueError("no such mini game")
        try:
            seats = [int(x) for x in str(seats_text or "").split(",") if x.strip()]
        except ValueError:
            raise ValueError("seats are numbers 1-4, comma-separated") from None
        if len(seats) != entry["players"] or len(set(seats)) != len(seats) or not all(1 <= s <= 4 for s in seats):
            raise ValueError(f"this mini game takes {entry['players']} different seats, 1-4")
        if entry.get("cheat") is not None:                       # B127: the setup on the hub, before anything is done
            check = self._setup_check(entry)
            if check is not None:
                self.row({"step": "minigame_refused", "why": "the cheat setup is not on the hub", "check": check})
                raise ValueError(SETUP_GONE)
        now = self.clock()
        mg = {"state": "starting", "seats": seats, "entry": entry, "recognised": None, "class": None,
              "scores": None, "why": None, "places": None, "t0": now, "last_poll": now, "final_at": None,
              "stash": None, "launched": False, "routed": False, "ended_by": None, "closed": False,
              # B114: the actor's step, the taken calls, the end's owner
              "step": None, "step_since": None, "queue": collections.deque(), "end_req": None, "ending": False,
              "title_proc": None, "actor_done": False, "switched_to": None,
              # B133 / B134: a held start — prepared behind the board, handed over on the board's go
              "hold": bool(hold), "phase": None, "go": None, "prep_t0": now, "ready_at": None, "play_t0": None,
              "practice": False, "practice_t0": None, "practices": 0, "practice_end_by": None,
              # B137: the title resumed since its begin was last loaded (then the go loads it again); the mute
              "ran_since_begin": False, "muted": False}
        with self._lock:
            self.mg = mg
        self.row({"step": "minigame_start", "seats": seats, "players": entry["players"],
                  **({"hold": True} if hold else {})})
        threading.Thread(target=self._actor, args=(mg,), daemon=True, name="party-minigame").start()
        threading.Thread(target=self._watch, args=(mg,), daemon=True, name="party-minigame-watch").start()
        return {"ok": True, "state": "starting", "seats": seats}

    def _setup_check(self, entry: dict) -> str | None:
        """B127: None when the sidecar's setup is on the hub as named — `cheat_profiles` lists that `profile_id`, valid,
        with the same source and indexes, and the launch's own expansion (B85, as the launch route does it) gives the
        indexes back (so the launch derives the same setup: no new folder). Else why, in a word. One manager call,
        bounded by SETUP_CHECK_S."""
        cheat = entry["cheat"]
        game = self.p._find_game_by_id(entry["game"])
        if game is None:
            return "no_game"

        def read():
            import cheat_clean as cc
            profiles = self.emu.cheat_profiles(game)
            want = list(cheat["enabled_cheat_indexes"])
            expanded = want
            if cc.enabled():
                expanded = cc.expand(cc.clean(self.emu.cheat_catalog(game), self.p.PROJECT_ROOT),
                                     cheat["source_index"], want)
            return profiles, sorted(expanded or [])
        try:
            profiles, expanded = self._emu_call(None, read, bound=SETUP_CHECK_S, abort=False)
        except TimeoutError:
            return "busy"
        except Exception:
            return "unreadable"
        found = next((p for p in (profiles or {}).get("profiles", []) or []
                      if str(p.get("profile_id", "")).strip().upper() == cheat["profile_id"]), None)
        if found is None:
            return "no_profile"
        if (int(found.get("source_index", -1)) != cheat["source_index"]
                or sorted(int(i) for i in found.get("enabled_cheat_indexes") or []) != cheat["enabled_cheat_indexes"]):
            return "profile_differs"
        if expanded != cheat["enabled_cheat_indexes"]:
            return "cheats_changed"
        return None

    @staticmethod
    def _finished(mg: dict) -> bool:
        return bool(mg["closed"] and mg["actor_done"])

    def _bridge(self):
        try:
            return self.p._native_stream._session_io.controller
        except Exception:
            return None

    def _final(self, mg: dict, state: str, **fields) -> None:
        with self._lock:
            if mg["state"] in FINAL or mg["closed"]:
                return
            mg.update(state=state, final_at=self.clock(), **fields)
        self.row({"step": "minigame_" + state, **{k: v for k, v in fields.items()
                                                  if k in ("class", "scores", "why", "places", "winner")}})

    # --- B114: bounded calls ------------------------------------------------------------------------------------------
    def _emu_call(self, mg: dict | None, fn: Callable[[], Any], bound: float | None = None, abort: bool = True):
        """One manager call under the manager's own lock, for that call only. The lock is tried in EMU_TRY_S steps;
        between them an END stops the start (abort); `bound` gives the wait up (TimeoutError)."""
        lock = self.emu.lock
        deadline = None if bound is None else self.clock() + bound
        while not lock.acquire(timeout=EMU_TRY_S):
            if abort and mg is not None and (mg["end_req"] is not None or mg["closed"]):
                raise _Abort()
            if deadline is not None and self.clock() >= deadline:
                raise TimeoutError("the manager's lock was not free within %.0f s" % bound)
        try:
            if abort and mg is not None and (mg["end_req"] is not None or mg["closed"]):
                raise _Abort()
            return fn()
        finally:
            lock.release()

    def _bounded(self, fn: Callable[[], Any], limit: float) -> tuple[bool, Any]:
        """fn on a helper thread with nothing held; (done, result or exception) after at most `limit` seconds."""
        box: dict = {}
        done = threading.Event()

        def run():
            _local.inside = True
            try:
                box["r"] = fn()
            except BaseException as exc:          # noqa: BLE001 - handed back to the caller
                box["e"] = exc
            finally:
                done.set()
        threading.Thread(target=run, daemon=True, name="party-minigame-call").start()
        if not done.wait(limit):
            return False, None
        return True, box.get("e", box.get("r"))

    def _planned(self) -> PlannedSwitch:
        rec = self.p._recovery
        ps = getattr(rec, "_planned_switch", None)
        if ps is None:
            ps = rec._planned_switch = PlannedSwitch()
        return ps

    def _note_bitrate_planned(self) -> None:
        """B115: the bitrate controller told of the new SSRC (its blackout, as for any restart) but not as a recovery
        restart: no escalation count, so no escalation step for a planned switch."""
        try:
            import adaptive_bitrate_live as abl
            abr = getattr(self.p, "_adaptive_bitrate", None)
            if abl.is_live(abr):
                with abr._lock:
                    abr._emit(abr._policy.note_ssrc_change("minigame_switch"), None)
        except Exception:
            pass

    def _switch_stream(self, which: str, pid: int | None = None, banner: bool = False) -> bool:
        """The onn's stream to the other window (B115: a planned switch for `pid`, the recovery told): the stream's own
        start for that process, with the remembered client, on a helper thread with no lock held (B114), waited for at
        most switch_limit_s. True when switched."""
        if not self.stream_needed or not self.p._recovery_stream_active():
            self.row({"step": "minigame_stream", "window": which, "switched": False, "why": "the stream is not up"})
            return False
        args = getattr(self.p, "_recovery_start_args", None)
        if not isinstance(args, dict) or not args.get("client_ip") or pid is None:
            self.row({"step": "minigame_stream", "window": which, "switched": False,
                      "why": "no remembered client or no process"})
            return False
        ps = self._planned()
        seq = ps.open(which, self.switch_limit_s + PLANNED_GRACE_S)
        t0 = self.clock()
        ns = self.p._native_stream
        self._arm_switch(ns, int(pid))                       # B143: the new process's sound continues the old's
        self._arm_fast(ns, int(pid))                         # B153: the old killed at once, the new sound early
        if banner:                                           # B144: a practice's band on the onn's picture only
            self._arm_banner(ns, int(pid))

        def go():
            return ns.start(client_ip=str(args["client_ip"]), port=int(args["port"]), managed_process_id=int(pid))
        try:
            done, res = self._bounded(go, self.switch_limit_s)
        finally:
            self._arm_switch(ns, None)
            self._arm_fast(ns, None)
            if banner:
                self._arm_banner(ns, None)
            until = ps.close_after(seq, PLANNED_GRACE_S)
            threading.Thread(target=self._window_row, args=(ps, seq, until), daemon=True,
                             name="party-minigame-window").start()
        if not done:
            self.row({"step": "minigame_stream", "window": which, "switched": False, "planned": True,
                      "why": f"the switch did not finish within {self.switch_limit_s:.0f} s"})
            raise TimeoutError(f"the stream switch did not finish within {self.switch_limit_s:.0f} s")
        if isinstance(res, BaseException):
            self.row({"step": "minigame_stream", "window": which, "switched": False, "planned": True,
                      "why": str(res)[:160]})
            return False
        self._note_bitrate_planned()
        self.row({"step": "minigame_stream", "window": which, "switched": True, "planned": True,
                  "seconds": round(self.clock() - t0, 3)})
        return True

    @staticmethod
    def _arm_switch(ns: Any, pid: int | None) -> None:
        """B143: the audio sender's next start for `pid` continues the last run's sequence and timestamp (None: disarmed).
        A stream without the arm (a stub, an old object): nothing."""
        audio = getattr(getattr(ns, "_session_io", None), "audio", None)
        arm = getattr(audio, "party_continue_next", None)
        if callable(arm):
            arm(pid)

    @staticmethod
    def _session_config_path(emu: Any) -> Path | None:
        """B155: the session config every RetroArch launch writes (the emulator's own place for it), or None."""
        where = getattr(emu, "_project_path", None)
        if not callable(where):
            return None
        try:
            return Path(where("data/games/retroarch/config")) / SESSION_CONFIG_NAME
        except Exception:
            return None

    @classmethod
    def _session_config_stamp(cls, emu: Any) -> tuple[int, int] | None:
        path = cls._session_config_path(emu)
        try:
            st = path.stat() if path is not None else None
        except OSError:
            return None
        return None if st is None else (st.st_ino, st.st_mtime_ns)

    @classmethod
    def _keys_written(cls, emu: Any, before: tuple[int, int] | None) -> bool:
        """B155: read back after the launch — True when this launch wrote the session config (its inode or mtime
        changed) and each of PARTY_SESSION_SETTINGS's keys has exactly one assignment there, `key = "value"`."""
        path = cls._session_config_path(emu)
        after = cls._session_config_stamp(emu)
        if path is None or after is None or after == before:
            return False
        try:
            lines = [ln.strip() for ln in path.read_text(encoding="utf-8", errors="replace").splitlines()]
        except OSError:
            return False
        for key, value in PARTY_SESSION_SETTINGS.items():
            assigned = [ln for ln in lines if re.match(rf"^{re.escape(key)}\s*=", ln)]
            if assigned != [f'{key} = "{value}"']:
                return False
        return True

    @staticmethod
    def _arm_fast(ns: Any, pid: int | None) -> None:
        """B153: the stream's next start for `pid` is this planned switch (None: disarmed). A stream without it:
        nothing."""
        arm = getattr(type(ns), "party_switch_next", None) and getattr(ns, "party_switch_next", None)
        if callable(arm):
            arm(pid)

    @staticmethod
    def _arm_banner(ns: Any, pid: int | None) -> None:
        """B144: the stream's next start for `pid` draws the practice banner (None: disarmed). A stream without it:
        nothing."""
        arm = getattr(type(ns), "party_banner_next", None) and getattr(ns, "party_banner_next", None)
        if callable(arm):
            arm(pid)

    def _window_row(self, ps: PlannedSwitch, seq: int, until: float | None) -> None:
        if until is not None:
            time.sleep(max(0.0, until - self.clock()) + 0.05)
        rep = ps.report(seq)
        if rep is not None:
            self.row({"step": "minigame_switch_window", **rep})

    # --- the actor: the start's steps, then every taken call in order -------------------------------------------------
    def _step(self, mg: dict, name: str, fn: Callable[[], Any]):
        with self._cond:
            # B134: a held mini game's steps also run while a practice plays (its way back)
            if (mg["end_req"] is not None or mg["closed"]
                    or mg["state"] not in (("starting", "playing") if mg.get("hold") else ("starting",))):
                raise _Abort()
            mg["step"], mg["step_since"] = name, self.clock()
        try:
            return fn()
        finally:
            with self._cond:
                mg["step"] = None
                self._cond.notify_all()

    def _start_steps(self, mg: dict) -> None:
        emu = self.emu
        mg["stash"] = self._step(mg, "stash", lambda: self._emu_call(mg, emu._party_stash_begin))
        emu._party_mg_stop_hook = lambda: self._end_by_stop(mg)
        game = self.p._find_game_by_id(mg["entry"]["game"])
        cheat = mg["entry"].get("cheat")
        if mg["hold"]:
            self._hold_select(mg, True)              # B141: from the launch to the go

        def launch():
            before = self._session_config_stamp(emu)                        # B155: this launch's write, told apart
            emu._party_session_settings = dict(PARTY_SESSION_SETTINGS)    # B139: this one launch only
            try:
                if cheat is None:
                    emu.launch(game)
                else:                                # B127: the onn's Extras launch, through the plugin's own path
                    self.p.handle_post("launch", self._cheat_query(mg["entry"]["game"], cheat))
            finally:
                emu._party_session_settings = None
            mg["keys_written"] = self._keys_written(emu, before)
            return emu.process
        proc = self._step(mg, "launch", lambda: self._emu_call(mg, launch))
        with self._lock:
            mg["launched"], mg["title_proc"] = True, proc
            late = mg["ending"] or mg["closed"]
        if late:                                     # the end ran while the title launched: it is not left running
            self._kill(proc)
            raise _Abort()
        keys = bool(mg.get("keys_written"))                                # B155
        if cheat is None:
            self.row({"step": "minigame_launch", "pid_owned": True, "keys_written": keys})
        else:
            from h7_minigame import session_profile_id
            matches = session_profile_id(emu) == cheat["profile_id"]
            self.row({"step": "minigame_launch", "pid_owned": True, "cheat": True, "profile_matches": matches,
                      "keys_written": keys})
            if not matches:
                raise RuntimeError(NOT_UNDER_SETUP)
        if mg["hold"]:                               # B133: prepared behind the board, handed over on the go
            self._held_steps(mg, proc)
            return
        self._step(mg, "pause", lambda: self._emu_call(mg, emu.pause))
        bridge = self._bridge()
        if bridge is not None:
            self._step(mg, "route", lambda: bridge.set_party_route({s - 1: k for k, s in enumerate(mg["seats"])}))
            mg["routed"] = True
        self.row({"step": "minigame_route", "ports": {str(k + 1): s for k, s in enumerate(mg["seats"])},
                  "routed": mg["routed"]})
        if self._step(mg, "switch", lambda: self._switch_stream("minigame", getattr(proc, "pid", None))):
            mg["switched_to"] = "minigame"
        runner = self.p._h7_minigame_runner()
        self._step(mg, "watch", lambda: runner.start("1", "", bench=not self.stream_needed))
        self.row({"step": "minigame_watch", "loaded": True})
        self._step(mg, "resume", lambda: self._emu_call(mg, emu.resume))
        with self._lock:
            if mg["state"] == "starting":
                mg["state"] = "playing"
        self.row({"step": "minigame_playing"})

    # --- B133 / B134: the held start ----------------------------------------------------------------------------------
    def _wait(self, mg: dict, until: Callable[[], bool], allowed: tuple = ("starting",)) -> None:
        """Wait (the actor) until `until()` holds; an end asked for, the mini game closed or a final state → _Abort."""
        while True:                                   # B114: `until` runs with no lock held (it may read the watch)
            with self._cond:
                if mg["end_req"] is not None or mg["closed"] or mg["state"] not in allowed:
                    raise _Abort()
            if until():
                return
            with self._cond:
                self._cond.wait(0.1)

    def _hold_select(self, mg: dict, on: bool) -> None:
        """B141: the pads' Select kept from a held title (RetroArch's hotkey pairs) — on / off (no bridge: nothing)."""
        bridge = self._bridge()
        if bridge is None or not hasattr(bridge, "party_hold_select"):
            return
        bridge.party_hold_select(on)
        mg["select_held"] = bool(on)

    def _mute(self, mg: dict, on: bool) -> None:
        """B137: the bridge's mute on / off (no bridge: nothing to mute)."""
        bridge = self._bridge()
        if bridge is None or not hasattr(bridge, "party_mute"):
            return
        bridge.party_mute(on)
        mg["muted"] = bool(on)

    def _grab(self):
        """B140: the title's window as the watcher sees it (None when it cannot be read)."""
        try:
            return self.p._h7_minigame_runner().picture.grab()
        except Exception:
            return None

    @staticmethod
    def _moved(a, b) -> float:
        """B140: the share of 64 x 48 cells (grey, BOX) moved by more than 16 grey levels between two pictures."""
        import numpy as np
        from PIL import Image
        x = np.asarray(a.convert("L").resize((64, 48), Image.BOX), dtype=np.float32)
        y = np.asarray(b.convert("L").resize((64, 48), Image.BOX), dtype=np.float32)
        return float((np.abs(x - y) > 16).mean())

    def _advance(self, mg: dict, pre) -> dict:
        """B140: into the paused title, ADVANCE_STEPS' frames (each FRAMEADVANCE its own manager call, ADVANCE_GAP_S
        apart), ADVANCE_SETTLE_S, a grab — until the grab moved >= BEGIN_MOVED from the pre-load one or the watch has read
        the start; the cap the steps' sum. Then GET_STATUS (PAUSED, else paused again)."""
        emu = self.emu
        runner = self.p._h7_minigame_runner()
        frames = steps = 0
        moved, changed = None, False
        for n in self.advance_steps:
            for _ in range(int(n)):
                self._emu_call(mg, lambda: emu._retroarch_network_request("FRAMEADVANCE", expect_response=False))
                time.sleep(self.advance_gap_s)
            frames += int(n)
            steps += 1
            time.sleep(self.advance_settle_s)
            now = self._grab()
            if pre is not None and now is not None:
                moved = self._moved(pre, now)
                if moved >= self.begin_moved:
                    changed = True
                    break
            try:
                if runner.result().get("recognised") is True:          # the watch has read the start already
                    changed = True
                    break
            except Exception:
                pass
        paused = self._emu_call(mg, emu._retroarch_network_status) == "PAUSED"
        if not paused:
            self._emu_call(mg, emu.pause)
        return {"frames": frames, "batches": steps, "changed": changed,
                "moved": round(moved, 4) if moved is not None else None, "paused": paused}

    def _prepare(self, mg: dict, after_practice: bool = False) -> None:
        """The title made ready behind the board, never resumed (B137): paused, the mute on, the begin loaded (a new
        watch, the label masked), the frames advanced, the mute off; the watcher reads the paused window → "ready".
        Not recognised → RuntimeError."""
        emu = self.emu
        runner = self.p._h7_minigame_runner()
        t0 = self.clock()
        with self._lock:
            mg["phase"], mg["prep_t0"], mg["ready_at"] = "preparing", t0, None
        self._step(mg, "pause", lambda: self._emu_call(mg, emu.pause))
        pre = self._step(mg, "grab", self._grab)                                # B140: the window before the load
        m0 = self.clock()
        self._mute(mg, True)                                                    # B137: no press reaches a frame
        try:
            self._step(mg, "watch", lambda: runner.start("1", "", bench=not self.stream_needed,
                                                          mask_label=PARTY_LABEL_MASK))
            self.row({"step": "minigame_watch", "loaded": True})
            adv = self._step(mg, "advance", lambda: self._advance(mg, pre))
        finally:
            self._mute(mg, False)
        mg["ran_since_begin"] = False
        self.row({"step": "minigame_frame_advance", "frames": adv["frames"], "batches": adv["batches"],
                  "mute_ms": round((self.clock() - m0) * 1000.0, 1), "changed": adv["changed"],
                  "moved": adv["moved"], "paused": adv["paused"]})
        if not adv["changed"]:
            raise RuntimeError(NO_BEGIN)                                        # B140: plainly, at once
        seen: dict = {}

        def recognised() -> bool:
            try:
                r = runner.result()
            except Exception:
                return False
            seen["r"] = r.get("recognised")
            if r.get("state") in ("no_game", "idle", "no_spec"):
                seen["r"] = False
            return seen["r"] is not None
        self._wait(mg, recognised)
        if seen.get("r") is not True:
            raise RuntimeError(NOT_RECOGNISED)
        now = self.clock()
        with self._cond:
            mg["phase"], mg["ready_at"], mg["recognised"] = "ready", now, True
            self._cond.notify_all()
        self.row({"step": "minigame_ready", "prepare_s": round(now - t0, 3),
                  **({"after_practice": True} if after_practice else {})})

    def _handover(self, mg: dict, proc: Any) -> bool:
        """The go: the begin loaded again (paused; the watch kept), the pads routed, the planned switch, the release.
        → True for a practice."""
        emu = self.emu
        runner = self.p._h7_minigame_runner()
        go = mg["go"]
        t0 = self.clock()
        with self._lock:
            mg["phase"] = "handing_over"
        self.row({"step": "minigame_go", "held_s": round(t0 - (mg["ready_at"] or t0), 3),
                  "remembered": bool(go["remembered"]), **({"practice": True} if go["practice"] else {})})
        if not go["practice"]:                              # B145: held through a practice too, until a real go
            self._hold_select(mg, False)                    # B141: from the go on, Select passes as today
        if mg.get("ran_since_begin"):                       # B137: only when the title ran since its begin was loaded
            self._mute(mg, True)
            try:
                self._step(mg, "reload", lambda: runner.reload())
            finally:
                self._mute(mg, False)
            self.row({"step": "minigame_reloaded", "loaded": True})
        if go["practice"]:
            self._bounded(lambda: runner.stop(), 2.0)       # B134: nothing read in a practice
        bridge = self._bridge()
        if bridge is not None:
            self._step(mg, "route", lambda: bridge.set_party_route({s - 1: k for k, s in enumerate(mg["seats"])}))
            mg["routed"] = True
        self.row({"step": "minigame_route", "ports": {str(k + 1): s for k, s in enumerate(mg["seats"])},
                  "routed": mg["routed"]})
        if self._step(mg, "switch", lambda: self._switch_stream("minigame", getattr(proc, "pid", None),
                                                               banner=bool(go["practice"]))):   # B144
            mg["switched_to"] = "minigame"
        if go["practice"] and bridge is not None:
            self._select_hook(mg, bridge)
        runner.label_mask(False)                            # B137: the title runs: no "Paused." to mask
        self._step(mg, "resume", lambda: self._emu_call(mg, emu.resume))
        mg["ran_since_begin"] = True
        now = self.clock()
        with self._cond:
            if mg["state"] == "starting":
                mg["state"], mg["play_t0"], mg["phase"] = "playing", now, None
                if go["practice"]:
                    mg["practice"], mg["practice_t0"], mg["practice_end_by"] = True, now, None
            self._cond.notify_all()
        self.row({"step": "minigame_playing", "handover_s": round(now - t0, 3),
                  **({"practice": True, "n": mg["practices"] + 1} if go["practice"] else {})})
        return bool(go["practice"])

    def _select_hook(self, mg: dict, bridge: Any) -> None:
        """B134 / B151: a Select press on any pad leaves a practice (the bridge's report hook; None again after). A
        player's first state is its Select as the bridge last saw it, so one already down at the hand-over counts only
        once let go and pressed again. Start is not looked at: it reaches the title."""
        last: dict = {}
        seen = getattr(bridge, "party_select_down", None)

        def hook(player: int, buttons: int) -> None:
            down = bool(int(buttons) & XUSB_BACK)
            if player not in last:
                last[player] = bool(seen(player)) if callable(seen) else False
            if down and not last[player]:
                with self._cond:
                    if mg.get("practice") and mg["practice_end_by"] is None:
                        mg["practice_end_by"] = "select_button"
                        self._cond.notify_all()
            last[player] = down
        bridge._party_buttons = hook

    def _way_back(self, mg: dict) -> None:
        """B134: a practice over — (B137) the title paused first, while its pads are still routed; the route cleared,
        the planned switch to the board; then made ready again behind the board (`_prepare`)."""
        emu = self.emu
        bridge = self._bridge()
        if bridge is not None:
            bridge._party_buttons = None
        self._hold_select(mg, True)                         # B141: the way back holds Select again
        now = self.clock()
        self.row({"step": "minigame_practice_end", "by": mg["practice_end_by"] or "time",
                  "practice_s": round(now - (mg["practice_t0"] or now), 3)})
        self._step(mg, "pause", lambda: self._emu_call(mg, emu.pause))        # B137: before the route is cleared
        if mg.get("routed") and bridge is not None:
            self._step(mg, "unroute", lambda: bridge.set_party_route(None))
            mg["routed"] = False
        board = (mg.get("stash") or {}).get("process")
        if self._step(mg, "switch", lambda: self._switch_stream("board", getattr(board, "pid", None))):
            mg["switched_to"] = "board"
        with self._cond:
            mg.update(state="starting", practice=False, practice_t0=None, practice_end_by=None, go=None,
                      practices=mg["practices"] + 1, phase="preparing")
            self._cond.notify_all()

    def _held_steps(self, mg: dict, proc: Any) -> None:
        after = False
        while True:
            self._prepare(mg, after_practice=after)
            self._wait(mg, lambda: mg["go"] is not None)
            if not self._handover(mg, proc):
                return
            self._wait(mg, lambda: mg["practice_end_by"] is not None
                       or self.clock() - (mg["practice_t0"] or self.clock()) >= self.practice_s, ("playing",))
            if mg["practice_end_by"] is None:
                mg["practice_end_by"] = "time"
            self._way_back(mg)
            after = True

    def go(self, practice_text: str = "") -> dict:
        """B133 / B134: the board's go (`practice=1`: a practice) — taken at once; remembered before "ready"."""
        word = str(practice_text or "").strip()
        if word not in ("", "1"):
            raise ValueError("practice is 1")
        with self._cond:
            mg = self.mg
            if (mg is None or not mg.get("hold") or mg["closed"] or mg["end_req"] is not None
                    or mg["state"] in FINAL):
                raise ValueError(NO_GO)
            if mg["go"] is not None and (mg["state"] == "starting" or not mg["practice"]):
                return {"ok": True, "go": "already", "phase": mg["phase"] or mg["state"]}
            if mg["state"] != "starting":                 # a practice playing: its way back comes first
                raise ValueError(NO_GO)
            phase = mg["phase"] or "preparing"            # before the preparation's first step: preparing
            remembered = phase != "ready"
            mg["go"] = {"practice": word == "1", "remembered": remembered, "at": self.clock()}
            self._cond.notify_all()
        return {"ok": True, "go": "remembered" if remembered else "taken", "phase": phase, "practice": word == "1"}

    @staticmethod
    def _cheat_query(game_id: str, cheat: dict) -> str:
        """B127: the onn's Extras launch query for a saved setup (`showExistingGameCheatProfileDialog`'s call)."""
        return (f"id={quote(game_id, safe='')}&cheat_source={int(cheat['source_index'])}"
                f"&cheat_indexes={','.join(str(int(i)) for i in cheat['enabled_cheat_indexes'])}")

    def _actor(self, mg: dict) -> None:
        try:
            self._start_steps(mg)
        except _Abort:
            pass
        except Exception as exc:
            self._final(mg, "given_up", why=f"the mini game did not start: {str(exc)[:160]}")
            self._enqueue(mg, "end_hub", None, by="hub: the start failed")   # B114: the title not left up
        self._serve(mg)

    def _serve(self, mg: dict) -> None:
        """Every taken call in the order taken; ends when the mini game is closed and nothing is left."""
        while True:
            with self._cond:
                while not mg["queue"] and not mg["closed"]:
                    self._cond.wait(0.2)
                if not mg["queue"]:
                    mg["actor_done"] = True
                    self._cond.notify_all()
                    return
                item = mg["queue"].popleft()
            self._do(mg, item)

    def _do(self, mg: dict, item: dict) -> None:
        with self._lock:                              # one runner per item: the actor or the END's guard
            if item.get("claimed"):
                return
            item["claimed"] = True
        kind = item["kind"]
        if kind in ("end", "end_board", "end_hub"):
            self._end_once(mg, item["by"])
        _local.inside = True
        try:
            if item["fn"] is not None:
                item["result"] = item["fn"]()
        except BaseException as exc:                  # noqa: BLE001 - the route raises it in its own thread
            item["error"] = exc
        finally:
            _local.inside = False
            item["done"].set()

    # --- taking the onn's calls and the ends --------------------------------------------------------------------------
    def _enqueue(self, mg: dict, kind: str, fn: Callable[[], Any] | None, by: str | None = None) -> dict | None:
        item = {"kind": kind, "fn": fn, "by": by, "done": threading.Event(), "result": None, "error": None}
        with self._cond:
            if mg["actor_done"]:
                return None
            if kind in ("end", "end_board", "end_hub") and mg["end_req"] is None:
                mg["end_req"] = by
            mg["queue"].append(item)
            state = mg["state"]
            self._cond.notify_all()
        self.row({"step": "minigame_taken", "what": kind, "state": state})
        if kind in ("end", "end_board", "end_hub"):
            threading.Thread(target=self._guard_end, args=(mg, item), daemon=True, name="party-minigame-end").start()
        return item

    def _guard_end(self, mg: dict, item: dict) -> None:
        """END always works: if the actor has not taken the end within step_grace_s (stuck in a step), it runs here."""
        end = self.clock() + self.step_grace_s
        with self._cond:
            while not (mg["ending"] or mg["closed"] or item["done"].is_set()) and self.clock() < end:
                self._cond.wait(0.1)
            if mg["ending"] or mg["closed"] or item["done"].is_set():
                return
            stuck = mg["step"]
            since = mg["step_since"]
        self.row({"step": "minigame_stuck", "what": stuck,
                  "seconds": round(self.clock() - since, 1) if since is not None else None})
        self._do(mg, item)

    def take(self, action: str, fn: Callable[[], Any]) -> dict | None:
        """A route the onn sends while a mini game is on (Home / RESUME / END): taken at once onto the mini game's
        queue and acted on in order. None when no mini game is on (the route runs today's path)."""
        kind = TAKEN.get(action)
        with self._lock:
            mg = self.mg
        if kind is None or mg is None or mg["actor_done"]:
            return None
        if kind == "end":
            self._final(mg, "given_up", why="ended from the onn")
        elif mg.get("hold") and (mg["state"] == "starting" or mg.get("practice")):
            # B133 / B134: Home / RESUME while the TV shows the board (the preparation, the hold) or a practice: the
            # mini game is given up first (the title stopped, the board's session back); the call then acts on the board
            self._final(mg, "given_up", why="the onn's Home during the preparation")
            self._enqueue(mg, "end_hub", None, by="onn: Home during the preparation")
        item = self._enqueue(mg, kind, fn, by="onn" if kind == "end" else None)
        if item is None:
            return None
        wait = RESUME_WAIT_S if kind.startswith("resume") else TAKE_WAIT_S
        if not item["done"].wait(wait):
            if kind.startswith("resume"):
                raise RuntimeError(f"the mini game's calls did not reach this one within {wait:.0f} s")
            with self._lock:
                state = mg["state"]
            return {"ok": True, "plugin": "games", "taken": kind, "minigame": state, "pending": True}
        if item["error"] is not None:
            raise item["error"]
        res = item["result"]
        if isinstance(res, dict) and kind in ("home", "end"):
            res = {**res, "taken": kind}
        return res

    def state_refusal(self, action: str) -> str | None:
        """B131: the onn's SAVE / LOAD while a mini game is starting or playing → the plain line (one row); else None
        (today's path: the manager's own refusal for the board, B108 / B110)."""
        line = STATE_REFUSED.get(action)
        if line is None:
            return None
        with self._lock:
            mg = self.mg
            if mg is None or mg["closed"] or mg["state"] not in ("starting", "playing"):
                return None
            state = mg["state"]
        self.row({"step": "minigame_state_refused", "what": "save" if action == "save-state" else "load",
                  "state": state})
        return line

    def bounded_read(self, action: str, fn: Callable[[], Any]) -> dict | None:
        """`status` / `native-stream-status` while a mini game is on: today's answer if it comes within READ_WAIT_S,
        else the last good one with "snapshot": true (one helper per route at a time). None when no mini game is on."""
        with self._lock:
            mg = self.mg
            if mg is None or self._finished(mg):
                return None
            slot = self._reads.setdefault(action, {"last": None, "busy": None})
            helper = slot["busy"]
            if helper is None:
                helper = slot["busy"] = {"done": threading.Event(), "r": None, "e": None}

                def run(h=helper, s=slot):
                    _local.inside = True
                    try:
                        h["r"] = fn()
                    except BaseException as exc:      # noqa: BLE001
                        h["e"] = exc
                    finally:
                        with self._lock:
                            if h["e"] is None and isinstance(h["r"], dict):
                                s["last"] = h["r"]
                            s["busy"] = None
                        h["done"].set()
                threading.Thread(target=run, daemon=True, name="party-minigame-read").start()
        if helper["done"].wait(READ_WAIT_S):
            if helper["e"] is not None:
                raise helper["e"]
            return helper["r"]
        with self._lock:
            last = slot["last"]
        if last is None:
            return {"ok": True, "plugin": "games", "snapshot": True, "minigame": mg["state"]}
        return {**last, "snapshot": True}

    # --- the watch (from the start) -----------------------------------------------------------------------------------
    def _watch(self, mg: dict) -> None:
        runner = self.p._h7_minigame_runner()
        unknown_since = None
        while True:
            time.sleep(self.tick)
            with self._lock:
                if self.mg is not mg or mg["closed"]:
                    return
                state = mg["state"]
                asked = mg["end_req"] is not None
            now = self.clock()
            stash = mg.get("stash") or {}
            board = stash.get("process")
            if board is not None and board.poll() is not None and not asked:
                self._final(mg, "given_up", why="the board stopped")
                self._enqueue(mg, "end_hub", None, by="hub: the board stopped")
                continue
            if asked:
                continue
            if state in FINAL:
                if now - (mg["final_at"] or now) >= self.end_wait_s:
                    self._enqueue(mg, "end_hub", None, by="hub: no end call")
                continue
            if state == "starting" and mg.get("hold"):     # B133: the limit is the preparation's; the hold has none
                if mg["phase"] in (None, "preparing") and now - mg["prep_t0"] >= self.start_limit_s:
                    self._final(mg, "given_up", why=f"the mini game was not ready within {self.start_limit_s:.0f} s")
                    self._enqueue(mg, "end_hub", None, by="hub: the start was stuck")
                elif mg["phase"] == "ready" and now - mg["last_poll"] >= self.poll_gone_s:
                    self._final(mg, "given_up", why="the board stopped asking")
                    self._enqueue(mg, "end_hub", None, by="hub: the board stopped asking")
                continue
            if state == "starting":
                if now - mg["t0"] >= self.start_limit_s:
                    self._final(mg, "given_up", why=f"the mini game did not start within {self.start_limit_s:.0f} s")
                    self._enqueue(mg, "end_hub", None, by="hub: the start was stuck")
                continue
            if state != "playing":
                continue
            if now - mg["last_poll"] >= self.poll_gone_s:
                self._final(mg, "given_up", why="the board stopped asking")
                continue
            if now - (mg.get("play_t0") or mg["t0"]) >= self.play_limit_s:   # B133: a held start: from the hand-over
                self._final(mg, "given_up", why=f"no end within {self.play_limit_s:.0f} s")
                continue
            if mg.get("practice"):                        # B134: nothing read, nothing scored in a practice
                continue
            try:
                r = runner.result()
            except Exception:
                continue
            with self._lock:
                mg["recognised"] = r.get("recognised")
            if r.get("recognised") is False:
                self._final(mg, "given_up", why="the title's start screen was not recognised")
                continue
            if r.get("state") == "ended":
                cls = r.get("class")
                if mg["entry"].get("score_read"):                         # B178: each side's number, read
                    got = r.get("scores")
                    n = mg["entry"]["players"]
                    if (not isinstance(got, list) or len(got) != n
                            or not all(type(x) is int and x >= 0 for x in got)):
                        self._final(mg, "given_up", why="an end the scores do not name")
                    else:
                        top = max(got)                                    # a tie: no winner (the board's draw)
                        won = mg["seats"][got.index(top)] if got.count(top) == 1 else None
                        self._final(mg, "ended", **{"class": cls, "scores": list(got), "winner": won})
                    continue
                if mg["entry"].get("places_to_scores") is not None:      # B123: the row of places -> the seats' scores
                    places = r.get("places")
                    n = mg["entry"]["players"]
                    if not isinstance(places, list) or sorted(places) != list(range(1, n + 1)):
                        self._final(mg, "given_up", why="an end the places do not name")
                    else:
                        p2s = mg["entry"]["places_to_scores"]
                        won = ({"winner": mg["seats"][list(places).index(1)]}         # B158: winner-only
                               if mg["entry"].get("winner_places") else {})
                        self._final(mg, "ended", **{"class": cls, "places": list(places),
                                                    "scores": [p2s[q - 1] for q in places], **won})
                    continue
                scores = mg["entry"]["scores"].get(cls)
                if scores is None:
                    self._final(mg, "given_up", why="an end the sidecar does not name")
                else:
                    port = (mg["entry"].get("winner_of") or {}).get(cls)              # B158: winner-only
                    won = {"winner": mg["seats"][port - 1]} if port is not None else {}
                    self._final(mg, "ended", **{"class": cls, "scores": list(scores), **won})
                continue
            if r.get("state") == "unreadable":                      # B182: the final screen seen, a number on it
                self._final(mg, "given_up", why="the final screen was seen and a number on it was not read")
                continue                                              # not read: given up now, no result
            if r.get("state") in ("no_game", "idle", "no_spec"):
                self._final(mg, "given_up", why="the watch stopped")
                continue
            if r.get("class") == "unknown":
                unknown_since = unknown_since if unknown_since is not None else now
                if now - unknown_since >= self.unknown_limit_s:
                    self._final(mg, "given_up", why=f"an unknown screen for {self.unknown_limit_s:.0f} s")
            else:
                unknown_since = None

    # --- result / end -------------------------------------------------------------------------------------------------
    def result(self) -> dict:
        with self._lock:
            mg = self.mg
            if mg is None:
                return {"ok": True, "state": "none"}
            mg["last_poll"] = self.clock()
            out = {"ok": True, "state": mg["state"], "seats": mg["seats"], "recognised": mg["recognised"],
                   "class": mg["class"], "scores": mg["scores"], "why": mg["why"], "closed": mg["closed"],
                   "since_s": round(self.clock() - mg["t0"], 1)}
            if mg.get("hold"):                            # B133 / B134: a held start's phase, practices
                if mg["state"] == "starting":
                    out["phase"] = mg["phase"] or "preparing"
                if mg["state"] == "playing" and mg["practice"]:
                    out["practice"] = True
                    out["practice_s"] = round(self.clock() - (mg["practice_t0"] or self.clock()), 1)
                out["practices"] = mg["practices"]
            if mg["entry"].get("places_to_scores") is not None:   # B123: the places read, port by port
                out["places"] = mg["places"]
            if (mg["entry"].get("winner_of") is not None or mg["entry"].get("winner_places")   # B158
                    or mg["entry"].get("score_read")):                                        # B178
                out["winner"] = mg.get("winner")
            return out

    def end(self, by: str = "board") -> dict:
        """The board's end: taken at once, acted on in order; answered with the end done if it is within TAKE_WAIT_S."""
        with self._lock:
            mg = self.mg
            if mg is None:
                return {"ok": True, "state": "none", "ended": False}
            if mg["closed"] or mg["end_req"] is not None:
                again = mg["closed"]
                ans = {"ok": True, "state": mg["state"], "scores": mg["scores"], "ended": True}
                return {**ans, "again": True} if again else {**ans, "pending": True}
        if mg["state"] not in FINAL:
            self._final(mg, "given_up", why=f"ended before a result ({by})")
        item = self._enqueue(mg, "end_board", None, by=by)
        done = item["done"].wait(TAKE_WAIT_S) if item is not None else True
        with self._lock:
            ans = {"ok": True, "state": mg["state"], "scores": mg["scores"], "ended": True}
        return ans if done else {**ans, "pending": True}

    def _end_once(self, mg: dict, by: str, inline: bool = False) -> bool:
        """The end's steps, once per mini game (whoever comes first: the actor, the guard, the manager's stop)."""
        with self._cond:
            if mg["ending"] or mg["closed"]:
                return False
            mg["ending"] = True
            if mg["end_req"] is None:
                mg["end_req"] = by
        try:
            self._end_steps(mg, by, inline)
        finally:
            with self._cond:
                mg["ended_by"] = by
                mg["closed"] = True
                self._cond.notify_all()
            self.row({"step": "minigame_end", "by": by})
        return True

    def _kill(self, proc: Any) -> None:
        try:
            if proc is not None and proc.poll() is None:
                proc.kill()
        except Exception:
            pass

    def _end_steps(self, mg: dict, by: str, inline: bool) -> None:
        """B115's way back: the route cleared, **the stream switched to the board while the title still runs** (the
        board's own pid: the title's stop cannot take the stream), **then** the title stopped, then the board's
        session back. END from the onn and the manager's stop (the session ends): no switch."""
        emu = self.emu
        if mg["state"] not in FINAL:
            self._final(mg, "given_up", why=f"ended before a result ({by})")
        self._bounded(lambda: self.p._h7_minigame_runner().stop(), 2.0)
        if emu._party_mg_stop_hook is not None:
            emu._party_mg_stop_hook = None
        if mg.get("routed"):
            bridge = self._bridge()
            if bridge is not None:
                bridge.set_party_route(None)
        board = (mg.get("stash") or {}).get("process")
        bridge = self._bridge()
        if bridge is not None and getattr(bridge, "_party_buttons", None) is not None:
            bridge._party_buttons = None                  # B134: a practice's Select hook (B151) never outlives it
        if bridge is not None and getattr(bridge, "_party_mute", False):
            bridge.party_mute(False)                      # B137: the mute never outlives the mini game
        if bridge is not None and getattr(bridge, "_party_hold_select", False):
            bridge.party_hold_select(False)               # B141: nor does the Select hold
        if mg.get("hold") and mg.get("switched_to") != "minigame":
            pass                                          # B133: the stream never left the board: no switch back
        elif by not in ("stop", "onn") and not inline and board is not None and board.poll() is None:
            try:
                self._switch_stream("board", getattr(board, "pid", None))
            except Exception:
                pass
        title = mg.get("title_proc")

        def stop_title():
            if emu._party_stash is not None and emu.process is not None and emu.process is title:
                emu.stop()                       # the title, RetroArch's own stop (the hook already cleared)
        if mg.get("launched"):
            try:
                if inline:
                    stop_title()
                else:
                    self._emu_call(None, stop_title, bound=MANAGER_BOUND_S, abort=False)
            except Exception as exc:
                self.row({"step": "minigame_end", "title_stop_failed": str(exc)[:160]})
            self._kill(title)                    # whatever the manager's stop did, the title is not left running
            self.row({"step": "minigame_title_stopped"})
        try:
            if inline:
                emu._party_stash_end()
            else:
                self._emu_call(None, emu._party_stash_end, bound=MANAGER_BOUND_S, abort=False)
            self.row({"step": "minigame_restore", "board_alive": emu.process is not None
                      and emu.process.poll() is None})
        except Exception as exc:
            self.row({"step": "minigame_restore", "failed": str(exc)[:160]})

    def _end_by_stop(self, mg: dict) -> dict:
        """The manager's stop with a mini game on (another launch, launch_orphaned — its caller holds the manager's
        lock): the mini game ended inline, waiting on nothing (no actor, no stream), then the board's own stop (F10)."""
        self._final(mg, "given_up", why="ended from the onn")
        self._end_once(mg, "stop", inline=True)
        return self.emu.stop()
