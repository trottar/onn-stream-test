package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/**
 * B18: the stall monitor's bye -- a finishing activity, before its sender stops, sends PHS1 kind 3 on the next three
 * controller ticks whatever the stall state (the host's B9 state path then saves nothing and holds nothing for the
 * silence that follows); then today's ticks.
 */
class StallByeTest {
    private fun kind(d: ByteArray) = d[4].toInt()
    private fun inp(age: Long, released: Boolean = true) = StallInputs(age, 1_000L, false, released)

    @Test
    fun aRequestedByeGoesOutThreeTimesWhateverTheState() {
        val m = StallMonitor(150L)
        assertNull(m.tick(0L, inp(10L)))                           // playing: nothing today
        m.requestBye()
        val sent = (1..3).map { m.tick(it * 8L, inp(10L, released = false))!! }
        assertEquals(listOf(3, 3, 3), sent.map { kind(it) })
        assertEquals(StallPacket.SIZE, sent[0].size)
        assertEquals(3L, m.byesSent)
        assertNull(m.tick(40L, inp(10L)))                          // then today's tick
        assertEquals(0L, m.stallsSent)
    }

    @Test
    fun withoutARequestNoBye() {
        val m = StallMonitor(150L)
        repeat(10) { m.tick(it * 8L, inp(10L)) }
        assertEquals(0L, m.byesSent)
        assertEquals(3, StallPacket.KIND_BYE)
    }
}
