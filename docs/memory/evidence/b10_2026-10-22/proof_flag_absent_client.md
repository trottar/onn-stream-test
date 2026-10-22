# B10 (client) — property absent = the CONFIRMED client (only added lines, all in the allowed forms)

| file | removed / changed | added | outside the forms |
| --- | ---: | ---: | ---: |
| `RtpH264Receiver.kt` | **0** | 12 | **0** |
| `NativeStreamActivity.kt` | **0** | 20 | **0** |
| `NativeControllerSender.kt` | **0** | 9 | **0** |

Result: **PROVEN**. New file `LossGuard.kt` (the flag, the datagram, the guard) is reached only through `lossGuard`, null without the property.

### RtpH264Receiver.kt

```

    // B10: the loss guard (LossGuard; only debug.privyhub.loss_guard sets it). null = today.
    @Volatile
    var lossGuard: LossGuard? = null

                // B10: a dropped access unit (null = today)
                if (!waitingForIdr) lossGuard?.onDrop()
                } else if (lossGuard?.deliver(isIdr) == false) {
                    // B10: held, not queued -- the surface keeps the last complete frame until the next IDR

                // B10: a dropped access unit (null = today)
                if (currentCorrupt && !waitingForIdr) lossGuard?.onDrop()
```

### NativeStreamActivity.kt

```
        // B10: the loss guard's keyframe request on the controller socket (null = today)
        lossGuard?.let { g -> controllerSender?.keyframeTick = { g.takeRequest() } }
        // B10: the loss guard on the receiver (null = today)
        receiver?.lossGuard = lossGuard
        // B10: the loss guard's mode and counters (null = today: no key)
        lossGuard?.let { g ->
            root.put("loss_guard_mode", g.mode.wire)
            root.put("frames_after_dropped_reference", g.framesAfterDroppedReference.get())
            root.put("loss_guard_episodes", g.episodes.get())
            root.put("loss_guard_frames_held", g.framesHeld.get())
            root.put("loss_guard_timeouts", g.timeouts.get())
            root.put("loss_guard_max_wait_ms", g.maxWaitObservedMs.get())
            root.put("keyframe_requests_sent", g.requestsSent.get())
        }


    // B10: the loss guard, only with debug.privyhub.loss_guard=<1|count> (null = today).
    private val lossGuard: LossGuard? by lazy { LossGuardFlag.fromSystem()?.let { LossGuard(it) } }
                // B10: the loss guard's counters (null = today: nothing)
                (lossGuard?.query() ?: "") +
```

### NativeControllerSender.kt

```

    // B10: the loss guard's keyframe request (LossGuard.takeRequest via the activity; null = today)
    @Volatile
    var keyframeTick: (() -> ByteArray?)? = null
                // B10: the loss guard's one keyframe_request per episode (null = today)
                keyframeTick?.invoke()?.let { d ->
                    try { socket.send(DatagramPacket(d, d.size)) } catch (_: Exception) { sendErrors.incrementAndGet() }
                }

```

