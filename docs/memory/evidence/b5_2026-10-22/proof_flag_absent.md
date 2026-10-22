# B5 — property absent = today (NativeStreamActivity.kt vs predecessors/)

- lines removed or changed: **0**
- lines added: 25; outside the allowed forms: **0**
- result: **PROVEN**: with `debug.privyhub.wifi_lock` absent, `streamWifiLock` is null (`StreamWifiLockFlag.fromSystem()` → null; JVM test `noAndroidPropertyIsOff`), every hook is a null-safe no-op, the two new overrides only call `super` first, and the report gains no key. New work when absent: one reflective `SystemProperties.get` per activity (B3's pattern).

Added lines:

```
    // B5: the lock follows the foreground (low-latency mode works only there); null = today.
    override fun onPause() {
        super.onPause()
        streamWifiLock?.release()
    }

    override fun onResume() {
        super.onResume()
        if (sessionStarted) streamWifiLock?.acquire()
    }

        // B5: the Wi-Fi lock for the session (null = today)
        streamWifiLock?.acquire()
        // B5: the Wi-Fi lock never outlives the session (null = today)
        streamWifiLock?.release()

        // B5: the lock asked and whether the platform held it (null = today: no key)
        streamWifiLock?.let { lock ->
            root.put("wifi_lock_mode", lock.mode.wire)
            root.put("wifi_lock_held", lock.heldAtFirstAcquire ?: false)
        }

    // B5: the stream's Wi-Fi lock, only with debug.privyhub.wifi_lock=<low_latency|high_perf> (null = today).
    private val streamWifiLock: StreamWifiLock? by lazy { StreamWifiLock.fromSystem(this) }

```
