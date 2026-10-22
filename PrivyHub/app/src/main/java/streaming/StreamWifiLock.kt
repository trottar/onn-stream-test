package com.safeiot.privyhub.streaming

import android.content.Context
import android.net.wifi.WifiManager
import android.os.Build

/**
 * B5: a Wi-Fi lock for the stream, behind the system property
 * `debug.privyhub.wifi_lock=<low_latency|high_perf>` (CL-B7P's convention; a
 * reboot clears it). Absent = today: no WifiManager call, no lock object.
 *
 * `low_latency` = WIFI_MODE_FULL_LOW_LATENCY (API 29+; active only while
 * connected, screen on, app in the foreground — the platform's own terms),
 * else WIFI_MODE_FULL_HIGH_PERF; `high_perf` = WIFI_MODE_FULL_HIGH_PERF (the
 * host's API-37 docs: deprecated, now replaced by the low-latency lock).
 * Needs WAKE_LOCK, already declared. One non-reference-counted lock per
 * activity: acquire is idempotent, one release frees it, so sessions never
 * stack. No call may fail or delay a stream.
 */
object StreamWifiLockFlag {
    const val PROPERTY = "debug.privyhub.wifi_lock"
    const val TAG = "PrivyHubStreamWifi"

    enum class Mode(val wire: String) { LOW_LATENCY("low_latency"), HIGH_PERF("high_perf") }

    fun parse(value: String?): Mode? =
        when (value?.trim()?.lowercase()) {
            "low_latency" -> Mode.LOW_LATENCY
            "high_perf" -> Mode.HIGH_PERF
            else -> null
        }

    /** The property, read through reflection; any failure is off. */
    fun fromSystem(): Mode? =
        try {
            val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            parse(get.invoke(null, PROPERTY) as? String)
        } catch (_: Throwable) {
            null
        }

    @Suppress("DEPRECATION")
    fun lockType(mode: Mode, sdkInt: Int): Int =
        if (mode == Mode.LOW_LATENCY && sdkInt >= 29) WifiManager.WIFI_MODE_FULL_LOW_LATENCY
        else WifiManager.WIFI_MODE_FULL_HIGH_PERF
}

/** The platform lock's three calls, so the JVM tests can use a fake. */
interface WifiLockHandle {
    fun setReferenceCounted(counted: Boolean)
    fun acquire()
    fun release()
    fun isHeld(): Boolean
}

class StreamWifiLock(val mode: StreamWifiLockFlag.Mode, private val create: () -> WifiLockHandle?) {
    private var handle: WifiLockHandle? = null

    /** Whether the platform reported the lock held at the first acquire (null before it). */
    @Volatile var heldAtFirstAcquire: Boolean? = null
        private set

    val held: Boolean
        get() = try { handle?.isHeld() == true } catch (_: Throwable) { false }

    @Synchronized
    fun acquire() {
        try {
            val h = handle ?: create()?.also {
                it.setReferenceCounted(false)
                handle = it
            } ?: return
            if (!h.isHeld()) h.acquire()
            if (heldAtFirstAcquire == null) heldAtFirstAcquire = h.isHeld()
        } catch (_: Throwable) {
            if (heldAtFirstAcquire == null) heldAtFirstAcquire = false
        }
    }

    @Synchronized
    fun release() {
        try {
            val h = handle ?: return
            if (h.isHeld()) h.release()
        } catch (_: Throwable) {
        }
    }

    companion object {
        /** The activity's lock, or null (the property absent = today). */
        fun fromSystem(context: Context): StreamWifiLock? {
            val mode = StreamWifiLockFlag.fromSystem() ?: return null
            val app = context.applicationContext
            return StreamWifiLock(mode) {
                val manager = app.getSystemService(Context.WIFI_SERVICE) as? WifiManager ?: return@StreamWifiLock null
                val lock = manager.createWifiLock(StreamWifiLockFlag.lockType(mode, Build.VERSION.SDK_INT),
                    StreamWifiLockFlag.TAG)
                object : WifiLockHandle {
                    override fun setReferenceCounted(counted: Boolean) = lock.setReferenceCounted(counted)
                    override fun acquire() = lock.acquire()
                    override fun release() = lock.release()
                    override fun isHeld(): Boolean = lock.isHeld
                }
            }
        }
    }
}
