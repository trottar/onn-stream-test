package com.safeiot.privyhub.streaming

import android.net.wifi.WifiManager
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B5: the stream's Wi-Fi lock. The flag (absent = off), the lock type per
 * platform level, and the lock's lifecycle on a fake handle: one
 * non-reference-counted lock, idempotent acquire, one release frees it,
 * repeated sessions never stack, a failing platform call never escapes.
 */
class StreamWifiLockTest {

    private class Fake(val throwOnAcquire: Boolean = false) : WifiLockHandle {
        var counted: Boolean? = null
        var acquires = 0
        var releases = 0
        var heldNow = false
        override fun setReferenceCounted(counted: Boolean) { this.counted = counted }
        override fun acquire() {
            if (throwOnAcquire) throw SecurityException("no WAKE_LOCK")
            acquires++; heldNow = true
        }
        override fun release() { releases++; heldNow = false }
        override fun isHeld(): Boolean = heldNow
    }

    @Test
    fun flagTable() {
        assertEquals(StreamWifiLockFlag.Mode.LOW_LATENCY, StreamWifiLockFlag.parse("low_latency"))
        assertEquals(StreamWifiLockFlag.Mode.LOW_LATENCY, StreamWifiLockFlag.parse(" LOW_LATENCY "))
        assertEquals(StreamWifiLockFlag.Mode.HIGH_PERF, StreamWifiLockFlag.parse("high_perf"))
        for (bad in listOf(null, "", "1", "on", "lowlatency", "full")) {
            assertNull(bad, StreamWifiLockFlag.parse(bad))
        }
    }

    @Test
    fun noAndroidPropertyIsOff() {
        assertNull(StreamWifiLockFlag.fromSystem())
    }

    @Suppress("DEPRECATION")
    @Test
    fun lockTypePerPlatform() {
        val ll = StreamWifiLockFlag.Mode.LOW_LATENCY
        assertEquals(WifiManager.WIFI_MODE_FULL_HIGH_PERF, StreamWifiLockFlag.lockType(ll, 28))
        assertEquals(WifiManager.WIFI_MODE_FULL_LOW_LATENCY, StreamWifiLockFlag.lockType(ll, 29))
        assertEquals(WifiManager.WIFI_MODE_FULL_LOW_LATENCY, StreamWifiLockFlag.lockType(ll, 34))
        assertEquals(WifiManager.WIFI_MODE_FULL_HIGH_PERF,
            StreamWifiLockFlag.lockType(StreamWifiLockFlag.Mode.HIGH_PERF, 34))
    }

    @Test
    fun oneLockNotCountedIdempotentAndReleasedOnce() {
        var created = 0
        val fake = Fake()
        val lock = StreamWifiLock(StreamWifiLockFlag.Mode.LOW_LATENCY) { created++; fake }
        lock.acquire()
        lock.acquire()                                   // onResume during a session: no second reference
        assertEquals(1, created)
        assertEquals(false, fake.counted)
        assertEquals(1, fake.acquires)
        assertTrue(lock.held)
        assertEquals(true, lock.heldAtFirstAcquire)
        lock.release()
        lock.release()                                   // onPause then the session's end: one platform release
        assertEquals(1, fake.releases)
        assertFalse(lock.held)
    }

    @Test
    fun repeatedSessionsNeverStack() {
        val fake = Fake()
        val lock = StreamWifiLock(StreamWifiLockFlag.Mode.HIGH_PERF) { fake }
        repeat(5) {
            lock.acquire()
            assertTrue(lock.held)
            lock.release()
            assertFalse(lock.held)
        }
        assertEquals(5, fake.acquires)
        assertEquals(5, fake.releases)
    }

    @Test
    fun releaseBeforeAnyAcquireIsNothing() {
        var created = 0
        val lock = StreamWifiLock(StreamWifiLockFlag.Mode.LOW_LATENCY) { created++; Fake() }
        lock.release()
        assertEquals(0, created)
        assertFalse(lock.held)
        assertNull(lock.heldAtFirstAcquire)
    }

    @Test
    fun aFailingPlatformNeverEscapes() {
        val lock = StreamWifiLock(StreamWifiLockFlag.Mode.LOW_LATENCY) { Fake(throwOnAcquire = true) }
        lock.acquire()
        lock.release()
        assertFalse(lock.held)
        assertEquals(false, lock.heldAtFirstAcquire)
        val none = StreamWifiLock(StreamWifiLockFlag.Mode.LOW_LATENCY) { null }   // no WifiManager
        none.acquire()
        none.release()
        assertFalse(none.held)
    }
}
