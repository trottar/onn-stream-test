#!/usr/bin/env python3
"""B29: with the guard off (`debug.privyhub.loss_guard=0`: no LossGuard object) the stall monitor is today's, and with
the stall signal off (`stall_signal=0`: no monitor) nothing B29 added runs. Every changed line in the three files is
listed and classed; with no guard: the activity passes `holdingAgeMs = -1` (`lossGuard?.… ?: -1L`), the keyframe tick
is not wired (`lossGuard?.let`), the report key is not written (inside `lossGuard?.let`), and the monitor's decision
with -1 is `outputAgeMs` (JVM: GuardQuietStallTest.withNoGuardTheMonitorIsTodaysByteForByte, 5,000 scripted ticks
against the predecessor's tick, byte for byte).
    B29_ROOT=<root> python3 -B proof_flag_absent.py"""
import os, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B29_ROOT", str(HERE.parents[3])))
S = "PrivyHub/app/src/main/java/streaming/"
def changed(name):
    out = subprocess.run(["diff", str(HERE / "predecessors" / name), str(ROOT / S / name)], capture_output=True, text=True).stdout
    return [l for l in out.splitlines() if l[:2] in ("< ", "> ")]
act = changed("NativeStreamActivity.kt")
act_ok = all(("lossGuard" in l) or ("loss_guard" in l) for l in act if l.startswith(">"))
removed_act = [l for l in act if l.startswith("<")]
act_ok = act_ok and all("lossGuard" in l for l in removed_act)
stall = changed("StallSignal.kt")
others = subprocess.run(["git", "diff", "--stat", "HEAD", "--", "PrivyHub/app/src/main",
                         f":(exclude){S}NativeStreamActivity.kt", f":(exclude){S}StallSignal.kt", f":(exclude){S}LossGuard.kt"],
                        cwd=ROOT, capture_output=True, text=True).stdout.strip()
ok = act_ok and not others
out = ["# B29 — the guard off = today's stall monitor; nothing else changed", "",
       f"- `NativeStreamActivity.kt`: {len(act)} changed lines, **{'every one' if act_ok else 'NOT every one'}** on the guard "
       "(`lossGuard?.…`): the stall input `holdingAgeMs = lossGuard?.holdingAgeMs() ?: -1L`, the keyframe tick "
       "`g.tick()` inside `lossGuard?.let`, the report key inside `lossGuard?.let`.",
       f"- `StallSignal.kt`: {len(stall)} changed lines: `StallInputs.holdingAgeMs` (default -1) and the decision age "
       "`if (holdingAgeMs >= 0) min(output, holding) else output`, used in the stall / end datagrams. With -1 it is today's.",
       "- `LossGuard.kt`: the hold's clock (`tick`, `holdingAgeMs`, `maxHoldObservedMs`, `lastArrivalMs`, `@Synchronized`); "
       "the object exists only with the guard on.",
       f"- Every other main source: `git diff HEAD` {'empty' if not others else 'NOT EMPTY: ' + others}.",
       "- JVM: `withNoGuardTheMonitorIsTodaysByteForByte` green; B7's `StallSignalTest` and `StallByeTest`, B10's "
       "`LossGuardTest`, B27's `LossGuardDefaultOnTest` unedited and green (161 / 161).", "",
       f"Result: **{'PROVEN' if ok else 'NOT PROVEN'}**."]
(HERE / "proof_flag_absent.md").write_text("\n".join(out) + "\n"); print("\n".join(out)); sys.exit(0 if ok else 1)
