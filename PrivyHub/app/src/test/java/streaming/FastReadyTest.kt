package com.safeiot.privyhub.streaming

import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.nio.ByteBuffer
import java.util.concurrent.atomic.AtomicLong
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B16: the recovery gate's ready at the first decodable frame. The decision table, then the real RtpH264Receiver on
 * loopback across a 4-s `@down` gap (a forward sequence jump: the resync, the P-frames after it rejected while the
 * receiver waits for an IDR, then the IDR) with a fake decoder (its frame count and last output time) and the
 * activity's 50-ms tick.
 */
class FastReadyTest {

    private fun inputs(
        recovery: Boolean = true, released: Boolean = false, inFlight: Boolean = false, meta: Boolean = true,
        waitingForIdr: Boolean = false, frames: Long = 11L, age: Long = 10L,
    ) = FastReadyInputs(recovery, released, inFlight, meta, waitingForIdr, frames, age)

    @Test
    fun theDecisionTable() {
        val f = FastReady()
        assertFalse(f.tick(inputs()))                             // no recovery entered yet
        f.onRecoveryEntered(10L)
        assertFalse(f.tick(inputs(recovery = false)))             // the startup gate: never
        assertFalse(f.tick(inputs(released = true)))
        assertFalse(f.tick(inputs(inFlight = true)))
        assertFalse(f.tick(inputs(frames = 10L)))                 // nothing rendered since the recovery began
        assertFalse(f.tick(inputs(waitingForIdr = true)))
        assertFalse(f.tick(inputs(age = 101L)))
        assertFalse(f.tick(inputs(age = -1L)))
        assertFalse(f.tick(inputs(meta = false)))
        assertTrue(f.tick(inputs(age = 100L)))
        assertEquals(1L, f.releases)
        assertFalse(f.tick(inputs()))                             // once per recovery
        f.onRecoveryEntered(20L)
        assertTrue(f.tick(inputs(frames = 21L)))
        assertEquals(2L, f.releases)
    }

    @Test
    fun theHintKeyIsTheHostsField() {
        assertEquals("stall_resume", FastReadyHint.KEY)
        assertEquals("fast_ready", FastReadyHint.FIELD)
    }

    private fun freePort(): Int = DatagramSocket(0).use { it.localPort }

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

        /** The 4-s dark span: the packets the downlink lost (~1,000 a second at 7 Mbps). */
        fun darkFor(packets: Int) {
            seq = (seq + packets) and 0xffff
            ts += 90L * 4_000L
        }

        fun close() = tx.close()
    }

    @Test
    fun aFourSecondDownGapReleasesAtTheFirstTickAfterTheIdrsFrame() {
        val frames = AtomicLong(0L)
        val lastOutAt = AtomicLong(-1L)
        val port = freePort()
        val rx = RtpH264Receiver(
            port = port,
            onParameterSets = { _, _ -> },
            onAccessUnit = { _, _ -> frames.incrementAndGet(); lastOutAt.set(System.nanoTime() / 1_000_000L) },
        ).also { it.start(); Thread.sleep(150) }
        val w = Wire(port)
        repeat(4) { w.au(it == 0) }                                // playing
        Thread.sleep(80)
        assertEquals(4L, frames.get())
        val f = FastReady()
        f.onRecoveryEntered(frames.get())                          // the client's gate at 1 s of output silence
        fun tick(): Boolean {
            val now = System.nanoTime() / 1_000_000L
            val age = lastOutAt.get().let { if (it < 0L) -1L else now - it }
            return f.tick(inputs(waitingForIdr = rx.snapshot().waitingForIdr, frames = frames.get(), age = age))
        }
        w.darkFor(4_000)                                           // the downlink returns after 4 s
        repeat(3) { w.au(false) }                                  // P-frames: no reference, rejected
        val ticksBefore = mutableListOf<Boolean>()
        repeat(5) { Thread.sleep(50); ticksBefore.add(tick()) }   // up to one GOP (250 ms) before the IDR
        assertEquals(4L, frames.get())
        assertTrue(rx.snapshot().waitingForIdr)
        assertEquals(listOf(false, false, false, false, false), ticksBefore)
        w.au(true)                                                 // the IDR
        w.au(false)
        Thread.sleep(50)
        assertTrue(frames.get() > 4L)
        assertFalse(rx.snapshot().waitingForIdr)
        assertTrue(tick())                                         // the first tick after the IDR's frame: the ready
        assertEquals(1L, f.releases)
        assertTrue(f.lastFrameToPostMs in 0L..50L)
        assertFalse(tick())
        rx.stop()
        w.close()
    }
}
