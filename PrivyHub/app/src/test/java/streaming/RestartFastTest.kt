package com.safeiot.privyhub.streaming

import java.io.File
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.nio.ByteBuffer
import java.nio.file.Files
import java.util.concurrent.atomic.AtomicLong
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B22: a guarded restart's release at the new stream's first fresh frame, armed only by the host's `restart_fast` key.
 * The decision table on an injected clock; then the real RtpH264Receiver on loopback across an encoder switch (SSRC
 * A's frames, the host's response, SSRC B's P-frames rejected, B's IDR) with B16's fake decoder and the activity's
 * 50-ms tick; then B17's harness (a temp-file store, a slow fake host: 300 ms per post) with the key: the start, the
 * report, the ready; the rebuilt audio receiver started at the ready's return, not at the response. CL-B12 cell 1 press
 * 2's rows: the switch ~0.5 s after the start's entry, the IDR 14 ms after it.
 */
class RestartFastTest {

    private fun inputs(
        released: Boolean = false, inFlight: Boolean = false, meta: Boolean = true, ssrc: Long = 1L,
        waitingForIdr: Boolean = false, frames: Long = 11L, age: Long = 10L, report: Boolean = true,
    ) = RestartFastInputs(released, inFlight, meta, ssrc, waitingForIdr, frames, age, report)

    @Test
    fun theDecisionTable() {
        val clock = longArrayOf(1_000L)
        val r = RestartFast(ssrcAtStart = 0L, needSwitch = true) { clock[0] }
        assertFalse(r.tick(inputs()))                               // not armed before the response
        r.onResponse()
        assertFalse(r.tick(inputs(meta = false)))
        assertFalse(r.tick(inputs(released = true)))
        assertFalse(r.tick(inputs(inFlight = true)))
        assertFalse(r.tick(inputs(ssrc = 0L, frames = 50L)))       // the old encoder's frames: no switch yet
        clock[0] += 400L
        assertFalse(r.tick(inputs(ssrc = 1L, frames = 50L)))       // the switch seen: its frame count is the baseline
        assertEquals(400L, r.responseToSwitchMs)
        assertFalse(r.tick(inputs(frames = 50L)))                  // nothing rendered after the switch
        assertFalse(r.tick(inputs(frames = 51L, waitingForIdr = true)))
        assertFalse(r.tick(inputs(frames = 51L, age = 101L)))      // stale (press 1's 854-ms stall is waited out)
        assertFalse(r.tick(inputs(frames = 51L, age = -1L)))
        clock[0] += 120L
        assertTrue(r.tick(inputs(frames = 51L, age = 100L)))
        assertEquals("fast", r.releasedBy)
        assertEquals(120L, r.switchToReleaseMs)
        assertEquals(520L, r.responseToReleaseMs)
        assertEquals(0L, r.reportWaitMs)
        assertFalse(r.tick(inputs(frames = 60L)))                   // once
        r.noteRelease()
        assertEquals("fast", r.releasedBy)
    }

    @Test
    fun noSwitchNeededWhenTheHostSaysNoOldStream() {
        val r = RestartFast(ssrcAtStart = 0L, needSwitch = false) { 0L }
        r.onResponse()
        assertFalse(r.tick(inputs(ssrc = 0L, frames = 0L)))         // baseline 0
        assertTrue(r.tick(inputs(ssrc = 0L, frames = 1L)))
    }

    @Test
    fun theReleaseWaitsForTheOldReportCappedAtOneSecond() {
        val clock = longArrayOf(0L)
        val r = RestartFast(0L, true) { clock[0] }
        r.onResponse()
        assertFalse(r.tick(inputs(frames = 5L, report = false)))   // the switch's baseline
        clock[0] += 300L
        assertFalse(r.tick(inputs(frames = 6L, report = false)))   // fresh, but the report is still in flight
        clock[0] += 50L
        assertTrue(r.tick(inputs(frames = 7L, report = true)))      // the report done: the release
        assertEquals(50L, r.reportWaitMs)

        val c2 = longArrayOf(0L)
        val s = RestartFast(0L, true) { c2[0] }
        s.onResponse()
        assertFalse(s.tick(inputs(frames = 5L, report = false)))
        c2[0] += 300L
        assertFalse(s.tick(inputs(frames = 6L, report = false)))
        c2[0] += 699L
        assertFalse(s.tick(inputs(frames = 7L, report = false)))
        c2[0] += 1L
        assertTrue(s.tick(inputs(frames = 8L, report = false)))     // 1,000 ms after the response: a slow report
        assertEquals(700L, s.reportWaitMs)                          // never holds the game
    }

    @Test
    fun theGatesReleaseIsNamedAndItsResetsCounted() {
        val clock = longArrayOf(0L)
        val r = RestartFast(0L, true) { clock[0] }
        r.onResponse()
        r.noteGateReset("queue")
        r.noteGateReset("dropped")
        clock[0] += 3_900L
        r.noteRelease()
        assertEquals("gate", r.releasedBy)
        assertEquals(3_900L, r.responseToReleaseMs)
        assertEquals(2L, r.gateResets)
        assertEquals("dropped", r.gateLastReset)
        assertFalse(r.tick(inputs(frames = 99L)))
    }

    @Test
    fun theAudioIsTakenOnce() {
        val r = RestartFast(0L, true)
        assertTrue(r.takeAudio())
        assertFalse(r.takeAudio())
    }

    @Test
    fun theHintKeysAreTheHostsFields() {
        assertEquals("restart_fast", RestartFastHint.KEY)
        assertEquals("armed", RestartFastHint.ARMED)
        assertEquals("old_stream_active", RestartFastHint.OLD_STREAM)
    }

    // --- the real receiver across an encoder switch (B16's loopback form) ---

    private fun freePort(): Int = DatagramSocket(0).use { it.localPort }

    private class Wire(val port: Int, val ssrc: Int, var seq: Int) {
        private val tx = DatagramSocket()
        private var ts = 90_000L

        fun au(idr: Boolean) {
            val nal = byteArrayOf(if (idr) 0x65 else 0x41, 0x11, 0x22, 0x33, 0x44)
            val p = ByteBuffer.allocate(12 + nal.size)
            p.put(0x80.toByte()).put((0x80 or 96).toByte()).putShort(seq.toShort()).putInt(ts.toInt()).putInt(ssrc)
            p.put(nal)
            seq = (seq + 1) and 0xffff
            ts += 1500L
            tx.send(DatagramPacket(p.array(), p.capacity(), InetAddress.getLoopbackAddress(), port))
            Thread.sleep(3)
        }

        fun close() = tx.close()
    }

    @Test
    fun theOldEncodersFramesNeverReleaseTheNewStreamsFirstFrameDoes() {
        val frames = AtomicLong(0L)
        val lastOutAt = AtomicLong(-1L)
        val port = freePort()
        val rx = RtpH264Receiver(
            port = port,
            onParameterSets = { _, _ -> },
            onAccessUnit = { _, _ -> frames.incrementAndGet(); lastOutAt.set(System.nanoTime() / 1_000_000L) },
        ).also { it.start(); Thread.sleep(150) }
        val old = Wire(port, 0x1111, 100)
        repeat(4) { old.au(it == 0) }                              // the old encoder, heard by the new instance
        Thread.sleep(60)
        val ssrcAtStart = rx.snapshot().ssrcChanges                // the start's POST
        assertEquals(0L, ssrcAtStart)
        val r = RestartFast(ssrcAtStart, needSwitch = true)
        r.onResponse()                                              // the fast response, before the host's teardown
        fun tick(): Boolean {
            val now = System.nanoTime() / 1_000_000L
            val age = lastOutAt.get().let { if (it < 0L) -1L else now - it }
            val s = rx.snapshot()
            return r.tick(inputs(ssrc = s.ssrcChanges, waitingForIdr = s.waitingForIdr, frames = frames.get(), age = age))
        }
        repeat(3) { old.au(false) }                                // still the old encoder after the response
        Thread.sleep(20)
        assertFalse(tick())
        assertFalse(tick())
        val new = Wire(port, 0x2222, 7)
        repeat(3) { new.au(false) }                                // the new encoder's P-frames: rejected, IDR wait
        Thread.sleep(50)
        assertEquals(1L, rx.snapshot().ssrcChanges)
        assertTrue(rx.snapshot().waitingForIdr)
        assertFalse(tick())                                        // the switch's baseline taken here
        assertFalse(tick())
        val beforeIdr = frames.get()
        new.au(true)                                               // the new encoder's IDR
        new.au(false)
        Thread.sleep(50)
        assertTrue(frames.get() > beforeIdr)
        assertFalse(rx.snapshot().waitingForIdr)
        assertTrue(tick())                                         // the first tick after the IDR's frame
        assertEquals("fast", r.releasedBy)
        assertTrue(r.switchToReleaseMs in 0L..200L)
        rx.stop()
        old.close()
        new.close()
    }

    // --- B17's harness with the key: the order, the audio ---

    private val dir: File = Files.createTempDirectory("b22_store_").toFile()
    private var n = 0
    private fun storeFile(): File = File(dir, "pending_${n++}.properties")

    private class Audio(val clock: LongArray) {
        var startedAtMs = -1L
        fun start() { startedAtMs = clock[0] }
    }

    /** 300 ms per post on the clock; the start answers `guard_end` and, when [fast], the `restart_fast` key. */
    private class SlowHost(val clock: LongArray, val fast: Boolean) {
        val posts = mutableListOf<Pair<String, Long>>()
        fun post(what: String): Pair<Boolean, Boolean> {
            posts.add(what to clock[0])
            clock[0] += 300L
            val guarded = what.endsWith("&guard_end=1")
            return guarded to (guarded && fast)
        }
        fun names() = posts.map { it.first }
    }

    private class Run(val audioAfter: Audio, val responseAt: Long, val fast: RestartFast?)

    /** The activity, B17 + B22: the held receiver, the start, the key, the report thread, the rebuilt receiver. */
    private fun startB22(g: RestartGuard, host: SlowHost, clock: LongArray): Run {
        clock[0] += 670L                                           // CL-B11: creation -> startSession
        val holds = g.prepareStart()
        assertTrue(holds)
        val restart = g.takePending()!!
        g.beginViaStart(restart)
        val ssrcAtStart = 0L
        val (acked, key) = host.post("start?port=48100&guard_end=1")
        val responseAt = clock[0]
        val fast = if (key) RestartFast(ssrcAtStart, true) { clock[0] }.also { it.onResponse() } else null
        g.noteStartResponse(acked)
        val after = Audio(clock)
        if (fast == null) after.start()                            // B11's rebuild at the response: today
        g.reportAfterStart(restart) { r -> host.post("report:$r") }   // its own thread in the app
        fast?.reportDone = true
        return Run(after, responseAt, fast)
    }

    private fun lose(g: RestartGuard, clock: LongArray) {
        g.onSurfaceLost("{\"session\":\"A\"}", 15L, 10L, false)
        clock[0] += 19_500L
    }

    @Test
    fun withTheKeyTheAudioWaitsForTheReadyAndTheOrderHolds() {
        val clock = longArrayOf(1_000L)
        val f = storeFile()
        val a = RestartGuard { clock[0] }.also { it.attach(FilePendingStore(f), 1L, 100L) }
        lose(a, clock)
        val b = RestartGuard { clock[0] }.also { it.attach(FilePendingStore(f), 2L, 100L) }
        val host = SlowHost(clock, fast = true)
        val run = startB22(b, host, clock)
        val fast = run.fast!!
        assertEquals(-1L, run.audioAfter.startedAtMs)              // not at the response
        clock[0] += 400L                                           // the switch, then the new stream's first frame
        assertFalse(fast.tick(inputs(ssrc = 1L, frames = 10L)))
        clock[0] += 50L
        assertTrue(fast.tick(inputs(ssrc = 1L, frames = 11L)))
        host.post("ready")
        if (fast.takeAudio()) run.audioAfter.start()               // the ready's return
        assertEquals(listOf("start?port=48100&guard_end=1", "report:{\"session\":\"A\"}", "ready"), host.names())
        assertTrue(run.audioAfter.startedAtMs > host.posts.last().second)
        assertEquals(true, b.lastCause!!["host_ended_session"])
        assertEquals(true, b.lastCause!!["old_report_posted"])
        assertEquals("via_start", b.lastCause!!["flush"])
    }

    @Test
    fun withoutTheKeyB17sOrderAndTheAudioAtTheResponse() {
        val clock = longArrayOf(1_000L)
        val f = storeFile()
        val a = RestartGuard { clock[0] }.also { it.attach(FilePendingStore(f), 1L, 100L) }
        lose(a, clock)
        val b = RestartGuard { clock[0] }.also { it.attach(FilePendingStore(f), 2L, 100L) }
        val host = SlowHost(clock, fast = false)
        val run = startB22(b, host, clock)
        assertNull(run.fast)
        assertEquals(run.responseAt, run.audioAfter.startedAtMs)          // at the response, as B17's
        assertEquals(listOf("start?port=48100&guard_end=1", "report:{\"session\":\"A\"}"), host.names())
    }

    @Test
    fun theGuardOffMeansNoGuardedStartSoNoKeyIsRead() {
        assertFalse(RestartGuardFlag.parse("0"))
        assertTrue(RestartGuardFlag.parse(null))                   // B19: absent = on
    }
}
