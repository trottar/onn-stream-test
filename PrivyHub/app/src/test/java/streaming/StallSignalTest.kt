package com.safeiot.privyhub.streaming

import java.nio.ByteBuffer
import java.nio.ByteOrder
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

/**
 * B7: the client's stall signal. The flag (absent = off), the 24-byte
 * datagram, and the monitor on a fake clock: nothing before the first frame
 * or the startup gate, a stall every 50 ms (not every 8-ms loop) while the
 * output is old or the recovery gate stands, exactly one stall_end.
 */
class StallSignalTest {

    private fun inp(age: Long, frames: Long = 100L, gate: Boolean = false, released: Boolean = true) =
        StallInputs(age, frames, gate, released)

    private fun kind(d: ByteArray) = d[4].toInt()

    @Test
    fun flagTable() {
        assertEquals(150L, StallSignalFlag.parse("1"))
        assertEquals(400L, StallSignalFlag.parse(" 400 "))
        assertEquals(121L, StallSignalFlag.parse("121"))
        assertEquals(2000L, StallSignalFlag.parse("2000"))
        // B19: absent / empty / junk = on at 150; only `0` turns it off
        for (on in listOf(null, "", "120", "2001", "on", "-5", "150ms")) {
            assertEquals(on, 150L, StallSignalFlag.parse(on))
        }
        assertNull(StallSignalFlag.parse("0"))
        assertNull(StallSignalFlag.parse(" 0 "))
    }

    @Test
    fun noAndroidPropertyIsOn() {
        assertEquals(150L, StallSignalFlag.fromSystem())        // B19: a failed read is absent, so on
    }

    @Test
    fun encoding() {
        val d = StallPacket.encode(StallPacket.KIND_STALL, true, 7, 123_456_789_012L, 431L)
        assertEquals(24, d.size)
        val b = ByteBuffer.wrap(d).order(ByteOrder.LITTLE_ENDIAN)
        val magic = ByteArray(4).also { b.get(it) }
        assertArrayEquals("PHS1".toByteArray(), magic)
        assertEquals(1, b.get().toInt())
        assertEquals(1, b.get().toInt())
        assertEquals(0, b.short.toInt())
        assertEquals(7, b.int)
        assertEquals(123_456_789_012L, b.long)
        assertEquals(431, b.int)
    }

    @Test
    fun nothingBeforeTheFirstFrameOrTheStartupGate() {
        val m = StallMonitor(150L)
        assertNull(m.tick(0L, inp(-1L)))                       // no frame yet
        assertNull(m.tick(10L, inp(5_000L, released = false)))  // still in the startup gate
        assertEquals(0L, m.stallsSent)
    }

    @Test
    fun stallEvery50msThenOneEnd() {
        val m = StallMonitor(150L)
        assertNull(m.tick(0L, inp(20L)))
        val sent = mutableListOf<Int>()
        var t = 0L
        var age = 150L
        while (t < 500L) {                                     // the 8-ms loop, 500 ms stalled
            m.tick(t, inp(age))?.let { sent.add(kind(it)) }
            t += 8L; age += 8L
        }
        assertEquals(9, sent.size)                             // ~20 / s (t = 0, then every >= 50 ms), not 62
        assertEquals(setOf(StallPacket.KIND_STALL), sent.toSet())
        val end = m.tick(t, inp(10L))
        assertNotNull(end)
        assertEquals(StallPacket.KIND_END, kind(end!!))
        assertNull(m.tick(t + 8L, inp(12L)))                   // exactly one
        assertEquals(1L, m.endsSent)
        assertNotNull(m.tick(t + 100L, inp(200L)))             // a new episode
    }

    @Test
    fun theRecoveryGateKeepsTheStallThoughFramesAreFresh() {
        val m = StallMonitor(150L)
        val first = m.tick(0L, inp(1_200L))!!
        assertEquals(StallPacket.KIND_STALL, kind(first))
        val gated = m.tick(60L, inp(15L, gate = true))!!      // frames back, the overlay still up
        assertEquals(StallPacket.KIND_STALL, kind(gated))
        assertEquals(1, gated[5].toInt())                      // the gate bit
        assertNull(m.tick(70L, inp(15L, gate = true)))
        assertEquals(StallPacket.KIND_END, kind(m.tick(120L, inp(16L, gate = false))!!))
    }
}
