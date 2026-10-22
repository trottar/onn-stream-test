# B7 (client) — property absent = B5's client (only added lines, all in the allowed forms)

| file | removed / changed | added | outside the forms |
| --- | ---: | ---: | ---: |
| `NativeStreamActivity.kt` | **0** | 21 | **0** |
| `NativeControllerSender.kt` | **0** | 9 | **0** |
| `AvcLowLatencyDecoder.kt` | **0** | 3 | **0** |

Result: **PROVEN**. New file `StallSignal.kt` (the flag, the datagram, the monitor) is reached only through `stallMonitor`, null without the property.

### NativeStreamActivity.kt

```
        // B7: the stall signal on the controller socket (null = today)
        stallMonitor?.let { m -> controllerSender?.stallTick = { now -> m.tick(now, stallInputs()) } }
        // B7: the stall signal's threshold and counts (null = today: no key)
        stallMonitor?.let { m ->
            root.put("stall_signal_ms", m.thresholdMs)
            root.put("stall_signal_stalls_sent", m.stallsSent)
            root.put("stall_signal_ends_sent", m.endsSent)
        }

    // B7: the stall signal's monitor, only with debug.privyhub.stall_signal=<1|ms> (null = today).
    private val stallMonitor: StallMonitor? by lazy { StallSignalFlag.fromSystem()?.let { StallMonitor(it) } }

    // B7: what the player sees: the output's age, the frame id, the recovery gate (read by the controller thread).
    private fun stallInputs(): StallInputs =
        StallInputs(
            outputAgeMs = decoder?.lastOutputAgeMs() ?: -1L,
            renderedFrames = decoder?.renderedFrameCount() ?: 0L,
            inGate = recoveryActive && !gameplayReleased,
            released = gameplayReleased || recoveryActive,
        )

```

### NativeControllerSender.kt

```

    // B7: the stall signal's tick (StallMonitor via the activity; null = today)
    @Volatile
    var stallTick: ((Long) -> ByteArray?)? = null
                // B7: a stall / stall_end datagram when one is due (null = today)
                stallTick?.invoke(System.nanoTime() / 1_000_000L)?.let { d ->
                    try { socket.send(DatagramPacket(d, d.size)) } catch (_: Exception) { sendErrors.incrementAndGet() }
                }

```

### AvcLowLatencyDecoder.kt

```
    // B7: the rendered-frame count, cheap (the stall signal's frame id)
    fun renderedFrameCount(): Long = renderedFrames.get()

```

