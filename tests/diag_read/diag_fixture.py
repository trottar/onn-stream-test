"""B36: a fake evening for diag_read / diag_keeper tests (temp dirs only; times UTC; no address, no title).

Two client sessions of a PS1 golf-class title (game id 33df…): session 1 10:00:00-10:05:00 on remote-direct with a
pad_slots row (two pads), a 300-ms uplink silence at 10:01:00, a 420-ms stall at 10:02:00 paused and released by
`resume` (B33's why `no_loss`), an in-place step 4000 -> 5000 at 10:03:00 (B32), a surface_lost at 10:04:58 (B32), then
the client's restart 10:05:00.5; session 2 10:05:01-10:08:00 at 4000, ended by the user (bye inside a control gap);
the WAN row (RTT 120 / 400) closed after session 1; the next report carries the restart's cause (surface, 1500 / 2000);
VOD client and range rows.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

DAY = "2026-10-30"
T = datetime(2026, 10, 30, 10, 0, 0)
GAME_LOG = "20261030-055900-game_ps1_33df0000aaaa1111.log"     # local EDT 05:59:00 = 09:59:00Z


def iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"


def at(s: float) -> datetime:
    return T + timedelta(seconds=s)


def rec(s: float, event: str, **kw) -> str:
    return json.dumps({"schema": "privyhub_native_stream_recovery_v1", "at_utc": iso(at(s)), "event": event,
                       "state": kw.pop("state", "PLAYING"), **kw})


def logs() -> dict[str, str]:
    """log name -> its text (JSON lines)."""
    r = [rec(-2, "remote_config", **{"class": "remote-direct"}), rec(0, "session_started"),
         rec(1, "pad_slots", slots={"0": "pad-a", "1": "pad-b"}),
         rec(120, "client_stall", age_ms=420.0), rec(120.1, "desync_pause", trigger="client_stall", age_ms=420.0),
         rec(120.5, "input_release", via="stall_end", method="resume", why="no_loss"),
         rec(298, "surface_lost", reason="pause", keys=["BUTTON_MODE"], bound_ms=10000, outcome="restart"),
         rec(300, "session_ended"), rec(300.5, "restart_fast"), rec(301, "session_started"),
         rec(479.9, "session_end_bye"), rec(480, "session_ended")]
    lad, hb = [], []
    for i in range(0, 481, 2):
        kb = 4000 if i < 180 or i > 300 else 5000
        lad.append(json.dumps({"at_utc": iso(at(i)), "event": "sample", "stream_kbps": kb, "state": "HOLD",
                               "output_gap_ms": 250 if i == 200 else 10, "waiting_for_idr": False}))
        if i == 180:
            lad.append(json.dumps({"at_utc": iso(at(180)), "event": "transition", "from_kbps": 4000, "to_kbps": 5000,
                                   "path_class": "remote"}))
            # B32-host: `in_place` rides the step's transition_done row (adaptive_bitrate_live.py)
            lad.append(json.dumps({"at_utc": iso(at(180.6)), "event": "transition_done", "from_kbps": 4000,
                                   "to_kbps": 5000, "in_place": True, "ssrc_unchanged": True, "splice_gap_ms": 18}))
    seq, base = 0, 0
    for i in range(0, 481, 2):
        if i == 302:
            seq, base = 0, i
        seq += 1
        e = (i - base) * 1000
        hb.append(json.dumps({"received_at_utc": iso(at(i)), "sequence": seq, "elapsed_ms": e,
                              "rendered_frames": e * 60 // 1000 - (40 if i >= 100 and base == 0 else 0),
                              "lost_packets": 40 if (i >= 150 and base == 0) else 0, "stream_resyncs": 0,
                              "audio_underruns": 1 if i >= 10 else 0, "audio_prolonged_starvation_events": 0,
                              "last_output_age_ms": 10, "link_rssi_dbm": -55,
                              **({"pad_slots": {"0": "pad-a", "1": "pad-b"}} if base == 0 else {})}))
    gaps = [json.dumps({"start_utc": iso(at(60)), "end_utc": iso(at(60.3)), "gap_ms": 300.0}),
            json.dumps({"start_utc": iso(at(479.5)), "end_utc": iso(at(481)), "gap_ms": 1500.0})]
    end1 = (at(300) - datetime(1970, 1, 1)).total_seconds()
    wan = [json.dumps({"class": "clean", "closed_unix_s": end1 + 3, "measures": {"rtt_ms": {"value": {"p50": 120.0, "p95": 400.0}}}})]
    vod_c = [json.dumps({"at_utc": iso(at(600)), "event": "vod_error", "error": "IO", "position_ms": 6000000}),
             json.dumps({"at_utc": iso(at(602)), "event": "vod_retry", "attempt": 1}),
             json.dumps({"at_utc": iso(at(604)), "event": "vod_resumed", "position_ms": 6000000})]
    vod_r = [json.dumps({"at_utc": iso(at(590)), "range": "bytes=0-", "bytes": 1000, "duration_ms": 10, "closed": "reset"}),
             json.dumps({"at_utc": iso(at(603)), "range": "bytes=500-", "bytes": 500, "duration_ms": 5, "closed": "eof"})]
    return {"native_stream_recovery.log": "\n".join(r) + "\n", "adaptive_bitrate_shadow.jsonl": "\n".join(lad) + "\n",
            "native_stream_heartbeat.log": "\n".join(hb) + "\n", "native_stream_ctrl_gaps.log": "\n".join(gaps) + "\n",
            "wan_sessions.jsonl": "\n".join(wan) + "\n", "vod_client.jsonl": "\n".join(vod_c) + "\n",
            "vod_range.jsonl": "\n".join(vod_r) + "\n"}


def report() -> dict:
    return {"schema": "x", "received_at_utc": iso(at(480.5)),
            "report": {"restart_cause": {"trigger": "surface", "paused_before_loss_ms": 1500, "away_ms": 2000},
                       "slow_events_top_gap": [], "stream_discontinuities": []}}


TOP = ("wan_sessions.jsonl", "vod_client.jsonl", "vod_range.jsonl")


def write_keeper_dir(d: Path, split: bool = True) -> Path:
    """B30's layout: raw/<key>/<NNNNNN>_<UTC><ext>; each log in two chunks split mid-line when `split`."""
    for name, text in logs().items():
        key = name if name in TOP else f"games__{name}"
        p = Path(d) / "raw" / key
        p.mkdir(parents=True, exist_ok=True)
        ext = "".join(Path(name).suffixes)
        cut = len(text) // 2 + 7 if split else len(text)
        (p / f"000000_20261030T100500Z{ext}").write_text(text[:cut])
        (p / f"000001_20261030T101000Z{ext}").write_text(text[cut:])
    rp = Path(d) / "raw" / "games__decoder_sessions"
    rp.mkdir(parents=True, exist_ok=True)
    (rp / "000000_native_decoder_20261030_100800_500.json").write_text(json.dumps(report()))
    gp = Path(d) / "raw" / f"games__{GAME_LOG}"
    gp.mkdir(parents=True, exist_ok=True)
    (gp / "000000_20261030T100000Z.log").write_text("[INFO] fake\n")
    sp = Path(d) / "samples"
    sp.mkdir(parents=True, exist_ok=True)
    (sp / "overlay.jsonl").write_text("".join(json.dumps({"at_utc": iso(at(m * 60)), "path": "direct", "connected": True}) + "\n"
                                              for m in range(-1, 12)))
    return Path(d)


def write_live(logs_root: Path) -> Path:
    """The live layout: logs/games/<log>, logs/<top>, decoder_sessions/, the game log."""
    g = Path(logs_root) / "games"
    (g / "decoder_sessions").mkdir(parents=True, exist_ok=True)
    (g / "stream_log_archive").mkdir(exist_ok=True)
    for name, text in logs().items():
        (Path(logs_root) / name if name in TOP else g / name).write_text(text)
    (g / "decoder_sessions" / "native_decoder_20261030_100800_500.json").write_text(json.dumps(report()))
    (g / GAME_LOG).write_text("[INFO] fake\n")
    return Path(logs_root)
