"""D-BASE-R3: link-drop self-recovery state machine (host side).

Behaviour and every constant here were decided by the user and are recorded
in `docs/memory/investigations/LINK_DROP_RECOVERY_DESIGN.md`. This module is
the wiring between pieces that already exist; it introduces no transport, no
decoder configuration and no new emulator control path.

    PLAYING           --client silent >= DESYNC_MS, or client posts desync-->
    PAUSED_RECOVERING --client posts native-stream-ready after the gate----->  PLAYING
    PAUSED_RECOVERING --GIVE_UP_MS elapsed---------------------------------->  PAUSED_SAVED
    PAUSED_SAVED      --user resumes from the launcher; gate passes--------->  PLAYING
    PAUSED_SAVED      --END_MS elapsed------------------------------------->  ENDED

The host is the authority: it pauses on its own evidence (controller-packet
silence, measured in the controller receive loop) because a client behind a
dead link cannot ask for anything. The client's own detector is secondary and
arrives as `native-stream-desync`.

Pausing and resuming go through `EmulatorManager.pause()` / `.resume()` only.
`PAUSE_TOGGLE` is a toggle and those methods confirm RetroArch's state after
sending; a recovery path that sent the command directly could invert the
emulator's state against the companion's.
"""

from __future__ import annotations

import json
import threading
import time

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from games.log_rotation import append_line


# --- Decisions, from the design note. Do not tune these here. ---------------

DESYNC_MS = 1_000
RECOVERY_CLEAN_TICKS = 3
GIVE_UP_MS = 120_000
END_MS = 1_800_000
RESTART_AFTER_MS = 2_000
RESTART_BACKOFF_MS = 5_000
RESTART_BACKOFF_CAP_MS = 30_000

MONITOR_INTERVAL_S = 0.25

# D-BASE-R4 item 4. This log gets a handful of lines per session rather than
# one every two seconds, so a smaller bound still covers a long history.
MAX_LOG_BYTES = 1024 * 1024
KEEP_ROTATED = 3

STATE_PLAYING = "PLAYING"
STATE_PAUSED_RECOVERING = "PAUSED_RECOVERING"
STATE_PAUSED_SAVED = "PAUSED_SAVED"
STATE_ENDED = "ENDED"

SCHEMA = "privyhub_native_stream_recovery_v1"


def _now_utc_text() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


class LinkDropRecovery:
    """Owns the recovery state for one native stream session.

    Every callback is supplied by the plugin so this module never imports the
    emulator or the stream manager, and so a caller can exercise it without
    either.
    """

    def __init__(
        self,
        project_root: Path,
        *,
        pause_game: Callable[[], Any],
        resume_game: Callable[[], Any],
        save_recovery_state: Callable[[], dict[str, Any]],
        restart_encoder: Callable[[], dict[str, Any]],
        full_start_encoder: Callable[[], dict[str, Any]],
        stream_active: Callable[[], bool],
        end_session: Callable[[], Any],
        client_packet_age_ms: Callable[[], float | None],
        recovery_save_detail: Callable[[], dict[str, Any]],
    ) -> None:
        self.project_root = Path(project_root)
        self._pause_game = pause_game
        self._resume_game = resume_game
        self._save_recovery_state = save_recovery_state
        self._restart_encoder = restart_encoder
        self._full_start_encoder = full_start_encoder
        self._stream_active = stream_active
        self._end_session = end_session
        self._client_packet_age_ms = client_packet_age_ms
        self._recovery_save_detail = recovery_save_detail

        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._running = threading.Event()

        self._state = STATE_ENDED
        self._state_since = time.monotonic()
        self._restarts = 0
        self._restart_backoff_ms = RESTART_BACKOFF_MS
        self._last_restart_at: float | None = None
        self._client_present_since: float | None = None
        self._last_heartbeat: dict[str, Any] | None = None
        self._last_heartbeat_at: float | None = None
        # D-BASE-R3a fix 2: the two newest heartbeats, each
        # (received_monotonic, last_output_age_ms). One reading cannot show
        # that the age is still rising, and a reading taken before the
        # restart became eligible is not evidence about now.
        self._heartbeat_history: list[tuple[float, int]] = []
        self._saved_at_utc: str | None = None
        self._last_desync_reason: str | None = None
        self._pending_transition_error: str | None = None

    # --- log ---------------------------------------------------------------

    def log_path(self) -> Path:
        return (
            self.project_root
            / "logs"
            / "games"
            / "native_stream_recovery.log"
        )

    def _log(
        self,
        event: str,
        **fields: Any,
    ) -> None:
        record: dict[str, Any] = {
            "schema": SCHEMA,
            "at_utc": _now_utc_text(),
            "event": event,
            "state": self._state,
        }
        record.update(fields)

        path = self.log_path()

        try:
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            append_line(
                path,
                json.dumps(record),
                max_bytes=MAX_LOG_BYTES,
                keep=KEEP_ROTATED,
            )
        except OSError:
            # A recovery that cannot be written down must still run.
            pass

    # --- lifecycle ---------------------------------------------------------

    def session_started(self) -> None:
        """A native stream session is live and the game is playing."""
        with self._lock:
            self._state = STATE_PLAYING
            self._state_since = time.monotonic()
            self._restarts = 0
            self._restart_backoff_ms = RESTART_BACKOFF_MS
            self._last_restart_at = None
            self._client_present_since = time.monotonic()
            self._last_heartbeat = None
            self._last_heartbeat_at = None
            self._heartbeat_history = []
            self._last_desync_reason = None
            self._pending_transition_error = None
            self._log("session_started")

        self._ensure_monitor()

    def session_ended(self) -> None:
        with self._lock:
            if self._state != STATE_ENDED:
                self._log("session_ended")
            self._state = STATE_ENDED
            self._state_since = time.monotonic()
            self._client_present_since = None

        self._stop_monitor()

    def _ensure_monitor(self) -> None:
        if self._running.is_set():
            return

        self._running.set()
        thread = threading.Thread(
            target=self._monitor_loop,
            name="PrivyHub-Link-Drop-Recovery",
            daemon=True,
        )
        self._thread = thread
        thread.start()

    def _stop_monitor(self) -> None:
        self._running.clear()

    # --- inputs ------------------------------------------------------------

    def note_client_silence(
        self,
        age_ms: float,
    ) -> None:
        """The controller receive loop saw >= DESYNC_MS with no packet."""
        self._enter_recovery(
            trigger="controller_silence",
            age_ms=float(age_ms),
        )

    def note_client_desync(
        self,
        reason: str,
        age_ms: float,
    ) -> None:
        """The client posted native-stream-desync."""
        self._enter_recovery(
            trigger=f"client_{reason or 'desync'}",
            age_ms=float(age_ms),
        )

    def note_heartbeat(
        self,
        record: dict[str, Any],
    ) -> None:
        now = time.monotonic()

        try:
            age_ms = int(
                record.get("last_output_age_ms", -1)
            )
        except (TypeError, ValueError):
            age_ms = -1

        with self._lock:
            self._last_heartbeat = dict(record)
            self._last_heartbeat_at = now
            self._heartbeat_history.append(
                (now, age_ms)
            )
            del self._heartbeat_history[:-2]

    def note_stream_start(self) -> None:
        """The client re-entered the stream (RESUME PLAYING)."""
        with self._lock:
            if self._state in (
                STATE_PAUSED_RECOVERING,
                STATE_PAUSED_SAVED,
            ):
                self._client_present_since = time.monotonic()
                self._log("client_stream_restart")

    def note_gameplay_released(self) -> dict[str, Any]:
        """The client passed the gate and the host resumed the game.

        One entry point for both uses of the gate: the startup release and
        the recovery release. Returns what happened so a caller can log it.
        """
        with self._lock:
            state = self._state

        if state in (
            STATE_PAUSED_RECOVERING,
            STATE_PAUSED_SAVED,
        ):
            self.note_stream_ready()
            return {
                "recovered": True,
                "from_state": state,
            }

        self.session_started()
        return {
            "recovered": False,
            "from_state": state,
        }

    def note_stream_ready(self) -> bool:
        """The client passed the gate. True when this resumed a recovery."""
        with self._lock:
            if self._state not in (
                STATE_PAUSED_RECOVERING,
                STATE_PAUSED_SAVED,
            ):
                if self._state != STATE_PLAYING:
                    self._state = STATE_PLAYING
                    self._state_since = time.monotonic()
                return False

            previous = self._state
            recovering_ms = int(
                (time.monotonic() - self._state_since) * 1000.0
            )
            self._state = STATE_PLAYING
            self._state_since = time.monotonic()
            self._restart_backoff_ms = RESTART_BACKOFF_MS
            self._last_restart_at = None
            self._client_present_since = time.monotonic()
            self._log(
                "resumed",
                from_state=previous,
                recovering_ms=recovering_ms,
                restarts=self._restarts,
            )
            return True

    # --- transitions -------------------------------------------------------

    def _enter_recovery(
        self,
        *,
        trigger: str,
        age_ms: float,
    ) -> None:
        with self._lock:
            if self._state != STATE_PLAYING:
                return

            self._state = STATE_PAUSED_RECOVERING
            self._state_since = time.monotonic()
            self._last_desync_reason = trigger
            self._restart_backoff_ms = RESTART_BACKOFF_MS
            self._last_restart_at = None

        paused_error = ""

        try:
            self._pause_game()
        except Exception as exc:
            paused_error = f"{type(exc).__name__}: {exc}"

        with self._lock:
            self._pending_transition_error = paused_error or None
            self._log(
                "desync_pause",
                trigger=trigger,
                age_ms=round(float(age_ms), 1),
                pause_error=paused_error or None,
            )

    def _give_up_and_save(self) -> None:
        saved: dict[str, Any] = {}
        error = ""

        try:
            saved = self._save_recovery_state()
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"

        with self._lock:
            self._state = STATE_PAUSED_SAVED
            self._state_since = time.monotonic()
            self._saved_at_utc = (
                _now_utc_text() if not error else None
            )
            self._log(
                "gave_up_saved",
                restarts=self._restarts,
                state_file=saved.get("state_file"),
                save_error=error or None,
            )

    def _end_after_timeout(self) -> None:
        error = ""

        try:
            self._end_session()
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"

        with self._lock:
            self._state = STATE_ENDED
            self._state_since = time.monotonic()
            self._log(
                "ended_after_link_loss",
                end_error=error or None,
            )

        self._stop_monitor()

    def _maybe_restart_encoder(
        self,
        now: float,
    ) -> None:
        with self._lock:
            if self._state != STATE_PAUSED_RECOVERING:
                return

            present_since = self._client_present_since

            if present_since is None:
                return

            if (now - present_since) * 1000.0 < RESTART_AFTER_MS:
                return

            # D-BASE-R3a fix 2: the moment this restart became eligible. A
            # heartbeat received before it describes a stream that has since
            # had time to come back, and acting on it restarts a stream that
            # is already healthy — which cost ~1.5 s on every short outage.
            if self._last_restart_at is None:
                eligible_at = (
                    self._state_since
                    + RESTART_AFTER_MS / 1000.0
                )
            else:
                eligible_at = (
                    self._last_restart_at
                    + self._restart_backoff_ms / 1000.0
                )

            if now < eligible_at:
                return

            history = list(self._heartbeat_history)

        if len(history) < 2:
            # Not enough evidence yet. Two heartbeats are 2 s apart, so this
            # only delays the first restart of a session, never blocks it.
            return

        (older_at, older_age), (newer_at, newer_age) = history[-2:]

        age_pair = [older_age, newer_age]

        still_rising = (
            older_age >= DESYNC_MS
            and newer_age >= DESYNC_MS
            and newer_age >= older_age
        )

        if not still_rising:
            # Either video is flowing to the client again, or the age is
            # falling. The gate owns the rest.
            return

        if newer_at < eligible_at:
            # The newest reading predates eligibility; it says nothing about
            # the stream now.
            return

        # The client is reachable and video still is not reaching it.
        #
        # D-BASE-R3a fix 1: pick the primitive that can actually work. The
        # C3.L1 cycle replaces a running encoder; after it has failed once
        # there is no encoder to replace (its failure path leaves
        # `_process = None`), `_running_locked()` is false, and every later
        # cycle raises before doing anything — which left a session stuck in
        # PAUSED_RECOVERING long after the link came back. When the session
        # has no encoder, bring one up with the same start path
        # `native-stream-start` uses instead. Neither branch touches the
        # emulator.
        try:
            has_encoder = bool(self._stream_active())
        except Exception:
            has_encoder = False

        method = "restart" if has_encoder else "full_start"

        cycle: dict[str, Any] = {}
        error = ""

        try:
            if has_encoder:
                cycle = self._restart_encoder()
            else:
                cycle = self._full_start_encoder()
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"

        with self._lock:
            self._last_restart_at = time.monotonic()
            self._restarts += 1
            video = (
                cycle.get("video")
                if isinstance(cycle, dict)
                else None
            )
            self._log(
                "encoder_restart",
                attempt=self._restarts,
                method=method,
                backoff_ms=self._restart_backoff_ms,
                last_output_age_ms=newer_age,
                age_pair_ms=age_pair,
                # the C3.L1 cycle record, as the primitive returns it;
                # absent for a full start, which returns a status payload
                cycle=video if isinstance(video, dict) else None,
                restart_error=error or None,
            )
            self._restart_backoff_ms = min(
                self._restart_backoff_ms * 2,
                RESTART_BACKOFF_CAP_MS,
            )

    # --- monitor -----------------------------------------------------------

    def _monitor_loop(self) -> None:
        while self._running.is_set():
            try:
                self._tick()
            except Exception:
                # The monitor must outlive any single failed transition.
                pass

            time.sleep(MONITOR_INTERVAL_S)

    def _tick(self) -> None:
        now = time.monotonic()

        age_ms = None

        try:
            age_ms = self._client_packet_age_ms()
        except Exception:
            age_ms = None

        with self._lock:
            state = self._state

            if age_ms is not None and age_ms < DESYNC_MS:
                if self._client_present_since is None:
                    self._client_present_since = now
            elif age_ms is not None:
                self._client_present_since = None

            state_ms = (now - self._state_since) * 1000.0

        if state == STATE_PAUSED_RECOVERING:
            if state_ms >= GIVE_UP_MS:
                self._give_up_and_save()
                return

            self._maybe_restart_encoder(now)
            return

        if state == STATE_PAUSED_SAVED:
            if state_ms >= END_MS:
                self._end_after_timeout()
            return

    # --- status ------------------------------------------------------------

    def status(self) -> dict[str, Any]:
        detail: dict[str, Any] = {}

        try:
            detail = self._recovery_save_detail() or {}
        except Exception:
            detail = {}

        with self._lock:
            since_ms = int(
                (time.monotonic() - self._state_since) * 1000.0
            )

            last_seen_ms: int | None = None

            try:
                age = self._client_packet_age_ms()
                if age is not None:
                    last_seen_ms = int(age)
            except Exception:
                last_seen_ms = None

            return {
                "state": self._state,
                "since_ms": since_ms,
                "restarts": int(self._restarts),
                "last_client_seen_ms": last_seen_ms,
                "save_available": bool(
                    detail.get("exists", False)
                ),
                "saved_at": (
                    detail.get("saved_at")
                    or self._saved_at_utc
                ),
                "save_game_id": detail.get("game_id"),
                "save_game_title": detail.get("game_title"),
                "desync_reason": self._last_desync_reason,
                "last_error": self._pending_transition_error,
                "constants": {
                    "desync_ms": DESYNC_MS,
                    "recovery_clean_ticks": RECOVERY_CLEAN_TICKS,
                    "give_up_ms": GIVE_UP_MS,
                    "end_ms": END_MS,
                    "restart_after_ms": RESTART_AFTER_MS,
                    "restart_backoff_ms": RESTART_BACKOFF_MS,
                    "restart_backoff_cap_ms": RESTART_BACKOFF_CAP_MS,
                },
            }
