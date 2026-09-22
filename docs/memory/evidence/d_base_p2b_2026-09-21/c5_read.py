"""Incidental C5/C5a read: every discontinuity across every P2b session,
accepted or rejected, with the C5a counters."""
import json
import os

SESS = "/home/privyhub/Projects/onn-stream-test/logs/games/decoder_sessions"
S = os.path.dirname(os.path.abspath(__file__))

rows = []
seen = set()
for line in open(os.path.join(S, "all_sessions.txt")):
    p = line.split()
    if len(p) < 3 or not p[2].startswith("native_decoder"):
        continue
    label, arm, fname = p[0], p[1], p[2]
    status = "accepted" if "accepted" in line else "rejected"
    if fname in seen:
        continue
    seen.add(fname)
    r = json.load(open(os.path.join(SESS, fname)))["report"]
    v = r["video"]
    for d, i in zip(r["stream_discontinuities"], r["first_idr_after_discontinuity"]):
        rows.append({
            "session": label, "arm": arm, "status": status,
            "elapsed_ms": d["elapsed_ms"], "type": d["type"],
            "jump_packets": d["jump_packets"],
            "resync_to_idr_ms": i["resync_to_idr_ms"],
            "rejected_idr_aus": i["rejected_idr_aus"],
            "dropped_non_idr_aus": i["dropped_non_idr_aus"],
            "au_complete": i["au_complete"],
            "au_fec_recovered": i["au_fec_recovered"],
            "au_fec_unrecoverable_group": i["au_fec_unrecoverable_group"],
        })

print("session,arm,status,elapsed_ms,type,jump_packets,resync_to_idr_ms,"
      "rejected_idr_aus,dropped_non_idr_aus,au_complete,au_fec_recovered,"
      "au_fec_unrecoverable_group")
for r in rows:
    print(",".join(str(r[k]) for k in
                   ("session", "arm", "status", "elapsed_ms", "type",
                    "jump_packets", "resync_to_idr_ms", "rejected_idr_aus",
                    "dropped_non_idr_aus", "au_complete", "au_fec_recovered",
                    "au_fec_unrecoverable_group")))

seq = [r for r in rows if r["type"] == "sequence_resync"]
over = [r for r in seq if r["resync_to_idr_ms"] > 250]
under = [r for r in seq if r["resync_to_idr_ms"] <= 250]
print()
print("discontinuities total: %d (sequence_resync %d, ssrc_change %d)"
      % (len(rows), len(seq), len(rows) - len(seq)))
print("sequence resyncs > 250 ms: %d" % len(over))
for r in over:
    print("   %s %s: %d ms, jump %d, rejected_idr_aus %d, dropped_non_idr %d, complete %s"
          % (r["session"], r["type"], r["resync_to_idr_ms"], r["jump_packets"],
             r["rejected_idr_aus"], r["dropped_non_idr_aus"], r["au_complete"]))
print("sequence resyncs <= 250 ms: %d, of which with rejected_idr_aus > 0: %d"
      % (len(under), len([r for r in under if r["rejected_idr_aus"] > 0])))

if len(rows) < 6 or not over:
    verdict = ("INDETERMINATE (%d discontinuities, %d over 250 ms)"
               % (len(rows), len(over)))
elif all(r["rejected_idr_aus"] >= 1 for r in over) and \
        all(r["rejected_idr_aus"] == 0 for r in under):
    verdict = "CONFIRMED"
elif any(r["rejected_idr_aus"] == 0 for r in over):
    verdict = "FALSIFIED (a resync over 250 ms rejected no IDR)"
else:
    verdict = "MIXED"
print()
print("C5a pre-registered verdict: " + verdict)
