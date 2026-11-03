package com.safeiot.privyhub.streaming

import java.io.File
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.net.SocketTimeoutException
import java.net.URLDecoder
import java.nio.ByteBuffer
import java.nio.file.Files
import java.util.Collections
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B32: the hold through a brief loss of the screen. B15's style: the activity's surface paths modelled as the activity
 * calls them (`surfaceDestroyed` / `surfaceCreated` / the expiry / the parameter-set callback), against the real
 * [SurfaceHold], the real [RestartGuard] with a file store, the real [RtpH264Receiver] on loopback, the real
 * [NativeControllerSender] sending to a loopback socket, the real [StallMonitor], and a fake host counting starts.
 */
class SurfaceHoldTest {

    private val dir: File = Files.createTempDirectory("b32_store_").toFile()

    private fun freePort(): Int = DatagramSocket(0).use { it.localPort }

    /** The controller's uplink as the host's socket sees it: arrival times of every datagram. */
    private class Uplink {
        val socket = DatagramSocket(0, InetAddress.getLoopbackAddress()).apply { soTimeout = 50 }
        val arrivals: MutableList<Long> = Collections.synchronizedList(mutableListOf<Long>())
        val stalls: MutableList<Int> = Collections.synchronizedList(mutableListOf<Int>())
        @Volatile var running = true
        private val t = Thread {
            val buf = ByteArray(64)
            while (running) {
                val p = DatagramPacket(buf, buf.size)
                try {
                    socket.receive(p)
                    arrivals.add(System.nanoTime() / 1_000_000L)
                    if (p.length == StallPacket.SIZE && buf[0] == 'P'.code.toByte() && buf[2] == 'S'.code.toByte()) {
                        stalls.add(buf[4].toInt())
                    }
                } catch (_: SocketTimeoutException) {
                }
            }
        }.apply { isDaemon = true; start() }

        fun maxGapMs(fromMs: Long, toMs: Long): Long {
            val a = synchronized(arrivals) { arrivals.filter { it in fromMs..toMs }.sorted() }
            if (a.isEmpty()) return Long.MAX_VALUE
            var g = a.first() - fromMs
            for (i in 1 until a.size) g = maxOf(g, a[i] - a[i - 1])
            return maxOf(g, toMs - a.last())
        }

        fun close() { running = false; t.join(500); socket.close() }
    }

    private class Wire(val port: Int, var seq: Int = 100) {
        private val tx = DatagramSocket()
        private var ts = 90_000L
        fun au(idr: Boolean) {
            val nal = byteArrayOf(if (idr) 0x65 else 0x41, 0x11, 0x22, 0x33, 0x44)
            val p = ByteBuffer.allocate(12 + nal.size)
            p.put(0x80.toByte()).put((0x80 or 96).toByte()).putShort(seq.toShort()).putInt(ts.toInt()).putInt(0x1234)
            p.put(nal)
            seq = (seq + 1) and 0xffff
            ts += 1500L
            tx.send(DatagramPacket(p.array(), p.capacity(), InetAddress.getLoopbackAddress(), port))
            Thread.sleep(3)
        }
        fun close() = tx.close()
    }

    /** A fake decoder: built only on a live surface; renders what it is given. */
    private class FakeDecoder(val surface: String) {
        var rendered = 0L
    }

    /**
     * The activity's B32 paths with the hold (or, [hold] null, today's): the start, the surface's loss and return,
     * the expiry, the parameter-set callback. Posts go to [posts].
     */
    private inner class ActivityModel(val hold: SurfaceHold?, val guard: RestartGuard?, uplinkPort: Int, videoPort: Int) {
        val posts: MutableList<String> = Collections.synchronizedList(mutableListOf<String>())
        var sessionStarted = false
        var sender: NativeControllerSender? = null
        var receiver: RtpH264Receiver? = null
        @Volatile var decoder: FakeDecoder? = null
        @Volatile var heldSurface: String? = null
        val monitor = StallMonitor(150L)
        val upPort = uplinkPort
        val vPort = videoPort
        val accessUnits = Collections.synchronizedList(mutableListOf<Int>())

        fun stallInputs(nowMs: Long): StallInputs {
            val i = StallInputs(outputAgeMs = if (decoder != null) 16L else -1L, renderedFrames = decoder?.rendered ?: 0L,
                inGate = false, released = true)
            return hold?.stallAgeMs(nowMs, i.renderedFrames)?.let { a -> i.copy(outputAgeMs = a) } ?: i
        }

        fun startSession(surface: String) {
            if (sessionStarted) return
            sessionStarted = true
            heldSurface = surface
            val restart = guard?.takePending()
            restart?.let { p -> guard?.beginViaStart(p) }
            posts.add(if (restart != null) "start&guard_end=1" else "start")
            sender = NativeControllerSender("127.0.0.1", upPort).also { s ->
                s.stallTick = { now -> monitor.tick(now, stallInputs(now)) }
                s.start()
            }
            receiver = RtpH264Receiver(
                port = vPort,
                onParameterSets = { _, _ -> },
                onAccessUnit = { _, _ ->
                    accessUnits.add(1)
                    // the parameter-set callback's rule: a decoder only on a live surface (the hold), or the closure's
                    if (decoder == null) {
                        val target = if (hold != null) heldSurface else surface
                        if (target != null) { decoder = FakeDecoder(target); hold?.onDecoderBuilt() }
                    }
                    decoder?.let { it.rendered++ }
                },
            ).also { it.start() }
            Thread.sleep(150)
        }

        fun surfaceDestroyed(finishing: Boolean = false) {
            if (sessionStarted && !finishing && hold != null) {
                hold.onSurfaceLost(16L, true)
                sender?.neutralize()
                heldSurface = null
                decoder?.let { hold.onDecoderClosed(it.rendered) }
                decoder = null
                return
            }
            if (sessionStarted) guard?.onSurfaceLost("{\"r\":1}", 16L, 10L, false)
            stopLocalPipeline()
            sessionStarted = false
        }

        fun surfaceCreated(surface: String) {
            if (hold != null && sessionStarted && hold.onSurfaceBack()) {
                heldSurface = surface
                return
            }
            startSession(surface)
        }

        fun expiry() {
            val h = hold ?: return
            if (!h.holding || !h.expired()) return
            h.onExpired()
            guard?.onSurfaceLost("{\"r\":1}", -1L, -1L, false)
            stopLocalPipeline()
            sessionStarted = false
        }

        fun stopLocalPipeline() {
            sender?.stop(); sender = null
            receiver?.stop(); receiver = null
            decoder = null
        }
    }

    private fun decodeRow(q: String): String {
        assertTrue(q, q.startsWith("&surface_lost="))
        return URLDecoder.decode(q.removePrefix("&surface_lost="), "UTF-8")
    }

    // --- the flag ---------------------------------------------------------------------------------------------------

    @Test
    fun theFlagIsOffUnlessOneOrABoundInRange() {
        assertNull(SurfaceHoldFlag.parse(null))
        assertNull(SurfaceHoldFlag.parse(""))
        assertNull(SurfaceHoldFlag.parse("0"))
        assertNull(SurfaceHoldFlag.parse("yes"))
        assertNull(SurfaceHoldFlag.parse("9999"))
        assertNull(SurfaceHoldFlag.parse("30001"))
        assertEquals(12_000L, SurfaceHoldFlag.parse("1"))
        assertEquals(12_000L, SurfaceHoldFlag.parse(" 1 "))
        assertEquals(20_000L, SurfaceHoldFlag.parse("20000"))
        assertNull(SurfaceHoldFlag.fromSystem())   // no SystemProperties on the JVM: off
    }

    // --- the 3-s loss: one session -----------------------------------------------------------------------------------

    @Test
    fun aThreeSecondLossIsOneSessionTheSenderNeverStops() {
        val up = Uplink()
        val vPort = freePort()
        val w = Wire(vPort)
        val hold = SurfaceHold(SurfaceHoldFlag.DEFAULT_BOUND_MS)
        val g = RestartGuard().also { it.attach(FilePendingStore(File(dir, "a.properties")), 1L, 1L) }
        val a = ActivityModel(hold, g, up.socket.localPort, vPort)
        a.startSession("surface-1")
        repeat(15) { w.au(it % 15 == 0) }
        Thread.sleep(50)
        assertNotNull(a.decoder)
        val senderBefore = a.sender
        hold.onPause()
        Thread.sleep(200)
        val lostAt = System.nanoTime() / 1_000_000L
        a.surfaceDestroyed()
        assertTrue(hold.holding)
        assertNull(a.decoder)
        // through the hold: the stream keeps arriving, nothing decodes
        val auBefore = a.accessUnits.size
        repeat(30) { w.au(false); Thread.sleep(30) }
        assertTrue(a.accessUnits.size > auBefore)
        assertNull(a.decoder)
        Thread.sleep(3_000L - (System.nanoTime() / 1_000_000L - lostAt))
        a.surfaceCreated("surface-2")
        val backAt = System.nanoTime() / 1_000_000L
        assertFalse(hold.holding)
        assertTrue(a.sessionStarted)
        assertTrue(senderBefore === a.sender)
        // the next IDR builds the decoder on the new surface; its first frame ends the synthetic age
        w.au(true); Thread.sleep(30)
        assertEquals("surface-2", a.decoder?.surface)
        hold.stallAgeMs(System.nanoTime() / 1_000_000L, a.decoder!!.rendered)
        Thread.sleep(100)
        val end = System.nanoTime() / 1_000_000L
        assertEquals(listOf("start"), a.posts)                       // one session: no second start
        assertTrue("uplink gap ${up.maxGapMs(lostAt - 200, end)}", up.maxGapMs(lostAt - 200, end) < 100L)
        // the stall signal: stalls during the hold, then one stall_end at the picture's return
        val kinds = synchronized(up.stalls) { up.stalls.toList() }
        assertTrue(kinds.count { it == StallPacket.KIND_STALL } >= 20)
        assertEquals(StallPacket.KIND_END, kinds.last())
        assertNull(g.takePending())                                   // the guard never saw a loss
        val row = decodeRow(hold.query())
        assertTrue(row, row.contains("\"outcome\":\"held\""))
        val away = Regex("\"away_ms\":(\\d+)").find(row)!!.groupValues[1].toLong()
        assertTrue("away $away", away in 2_900L..3_300L)
        assertTrue(row, row.contains("\"bound_ms\":12000"))
        assertTrue(row, Regex("\"paused_before_ms\":(\\d+)").find(row)!!.groupValues[1].toLong() >= 150L)
        assertTrue(row, Regex("\"first_frame_ms\":(\\d+)").find(row)!!.groupValues[1].toLong() in 0L..(end - backAt))
        assertEquals("", hold.query())
        val f = hold.reportFields()
        assertEquals(1L, f["losses"]); assertEquals(1L, f["held"]); assertEquals(0L, f["restarted"])
        assertEquals(2L, f["decoders_built"]); assertEquals(15L, f["rendered_before_reattach"])
        a.stopLocalPipeline(); w.close(); up.close()
    }

    // --- the 15-s loss: today's restart --------------------------------------------------------------------------------

    @Test
    fun aFifteenSecondLossIsTodaysRestart() {
        val clock = longArrayOf(100_000L)
        val up = Uplink()
        val vPort = freePort()
        val w = Wire(vPort)
        val hold = SurfaceHold(SurfaceHoldFlag.DEFAULT_BOUND_MS) { clock[0] }
        val g = RestartGuard { clock[0] }.also { it.attach(FilePendingStore(File(dir, "b.properties")), 1L, 1L) }
        val a = ActivityModel(hold, g, up.socket.localPort, vPort)
        a.startSession("surface-1")
        repeat(3) { w.au(it == 0) }
        a.surfaceDestroyed()
        clock[0] += 11_900L
        a.expiry()
        assertTrue(hold.holding)                                       // not yet
        clock[0] += 100L
        a.expiry()                                                     // the bound: today's surface-loss path
        assertFalse(hold.holding)
        assertFalse(a.sessionStarted)
        assertNull(a.sender)
        clock[0] += 3_000L
        a.surfaceCreated("surface-2")                                  // 15 s after the loss
        assertEquals(listOf("start", "start&guard_end=1"), a.posts)
        assertEquals("surface", g.lastCause!!["trigger"])
        val row = decodeRow(hold.query())
        assertTrue(row, row.contains("\"outcome\":\"restarted\""))
        assertTrue(row, row.contains("\"away_ms\":12000"))
        assertEquals(1L, hold.reportFields()["restarted"])
        a.stopLocalPipeline(); w.close(); up.close()
    }

    // --- absent = today -----------------------------------------------------------------------------------------------

    @Test
    fun absentAThreeSecondLossIsTodaysRestart() {
        val up = Uplink()
        val vPort = freePort()
        val w = Wire(vPort)
        val clock = longArrayOf(5_000L)
        val g = RestartGuard { clock[0] }.also { it.attach(FilePendingStore(File(dir, "c.properties")), 1L, 1L) }
        val a = ActivityModel(null, g, up.socket.localPort, vPort)
        a.startSession("surface-1")
        val lostAt = System.nanoTime() / 1_000_000L
        a.surfaceDestroyed()
        assertNull(a.sender)                                           // today: the sender stops with the surface
        Thread.sleep(300)
        clock[0] += 3_000L
        a.surfaceCreated("surface-2")
        assertEquals(listOf("start", "start&guard_end=1"), a.posts)
        assertEquals(3_000L, g.lastCause!!["away_ms"])
        assertTrue(up.maxGapMs(lostAt, lostAt + 290) > 250L)
        a.stopLocalPipeline(); w.close(); up.close()
    }

    // --- the keys --------------------------------------------------------------------------------------------------

    @Test
    fun aPadSystemKeyIsConsumedTheRemotesIsNot() {
        val clock = longArrayOf(1_000L)
        val h = SurfaceHold(12_000L) { clock[0] }
        val pad = SurfaceHold.SOURCE_GAMEPAD or SurfaceHold.SOURCE_JOYSTICK
        val remote = SurfaceHold.SOURCE_KEYBOARD or SurfaceHold.SOURCE_DPAD
        assertTrue(h.onKey(SurfaceHold.KEYCODE_BUTTON_MODE, true, pad))
        assertTrue(h.onKey(SurfaceHold.KEYCODE_BUTTON_MODE, false, pad))
        assertFalse(h.onKey(SurfaceHold.KEYCODE_BUTTON_MODE, true, remote))
        assertFalse(h.onKey(SurfaceHold.KEYCODE_HOME, true, remote))
        assertFalse(h.onKey(96 /* BUTTON_A */, true, pad))
        assertFalse(h.onKey(4 /* BACK */, true, pad))
        assertEquals(1L, h.reportFields()["pad_system_keys_consumed"])
        assertEquals(2L, h.reportFields()["system_keys_passed"])
        clock[0] += 500L
        h.onSurfaceLost(20L, true)
        clock[0] += 1_000L
        assertTrue(h.onSurfaceBack())
        h.stallAgeMs(clock[0], 1L)
        val row = decodeRow(h.query())
        assertTrue(row, row.contains("\"reason\":\"pad_system_key\""))
        assertTrue(row, row.contains("\"keys\":[\"110:pad:c\",\"110:remote:p\",\"3:remote:p\",\"96:pad:p\",\"4:pad:p\"]"))
    }

    @Test
    fun theReasonOrder() {
        val clock = longArrayOf(1_000L)
        fun loss(setup: (SurfaceHold) -> Unit, interactive: Boolean? = true): String {
            val h = SurfaceHold(12_000L) { clock[0] }
            setup(h)
            clock[0] += 300L
            h.onSurfaceLost(0L, interactive)
            clock[0] += 50_000L
            h.onExpired()
            return Regex("\"reason\":\"(\\w+)\"").find(decodeRow(h.query()))!!.groupValues[1]
        }
        assertEquals("remote_system_key", loss({ it.onKey(SurfaceHold.KEYCODE_SETTINGS, true, SurfaceHold.SOURCE_DPAD) }))
        assertEquals("user_leave", loss({ it.onUserLeave(); it.onFocus(false) }))
        assertEquals("screen_off", loss({ it.onFocus(false) }, false))
        assertEquals("input_device", loss({ it.onDevice("removed", 0); it.onTopResumed(false) }))
        assertEquals("top_lost", loss({ it.onTopResumed(false); it.onFocus(false) }))
        assertEquals("focus_lost", loss({ it.onFocus(false) }))
        assertEquals("unknown", loss({ it.onKey(96, true, SurfaceHold.SOURCE_GAMEPAD) }))
        // a key older than the 2-s window is not the cause
        assertEquals("unknown", loss({ it.onKey(SurfaceHold.KEYCODE_BUTTON_MODE, true, SurfaceHold.SOURCE_GAMEPAD); clock[0] += 2_500L }))
    }

    @Test
    fun theRowIsBoundedAndHoldsNoFreeText() {
        val clock = longArrayOf(1_000L)
        val h = SurfaceHold(12_000L) { clock[0] }
        repeat(10) {
            repeat(12) { h.onKey(SurfaceHold.KEYCODE_MENU, true, SurfaceHold.SOURCE_DPAD) }
            repeat(6) { h.onDevice("changed", SurfaceHold.SOURCE_GAMEPAD) }
            h.onSurfaceLost(0L, null)
            clock[0] += 20_000L
            h.onExpired()
        }
        assertEquals(8, h.pendingRows().size)
        assertEquals(2L, h.reportFields()["rows_dropped"])
        val row = decodeRow(h.query())
        assertTrue(row, row.startsWith("{\"seq\":3,"))
        assertTrue(row.length <= SurfaceHold.MAX_ROW_CHARS)
        assertEquals(8, Regex("\"82:remote:p\"").findAll(row).count())
        assertEquals(4, Regex("\"changed:pad:\\d+\"").findAll(row).count())
        assertTrue(row, row.contains("\"interactive\":null"))
        assertEquals("{\"a\":\"xy\",\"b\":[1,true]}", h.encode(linkedMapOf("a" to "x\"y", "b" to listOf(1, true))))
    }

    @Test
    fun theSenderNeutralizeKeepsItRunning() {
        val up = Uplink()
        val s = NativeControllerSender("127.0.0.1", up.socket.localPort)
        s.start()
        Thread.sleep(100)
        val at = System.nanoTime() / 1_000_000L
        s.neutralize()
        Thread.sleep(200)
        val n0 = s.snapshot().packetsSent
        Thread.sleep(100)
        assertTrue(s.snapshot().packetsSent > n0)
        assertTrue(up.maxGapMs(at, at + 290) < 100L)
        assertEquals(0, s.snapshot().lx)
        s.stop(); up.close()
    }
}
