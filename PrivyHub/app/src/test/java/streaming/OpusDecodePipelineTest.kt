package com.safeiot.privyhub.streaming

import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * CL-B5: the decode off the receive thread. The offer never waits on the
 * codec; the decode thread keeps the release order (frames, given-up frames
 * and an outage's concealment interleaved); a full queue drops and counts;
 * the maxima are tracked; stop releases the decoder.
 */
class OpusDecodePipelineTest {

    /** "Decodes" a packet to 480 frames whose bytes all equal the packet's first byte. */
    private class FakeDecoder(private val gate: CountDownLatch? = null, private val failOn: Int = -1) :
        OpusDecodePipeline.FrameDecoder {
        override val name = "fake"
        @Volatile var released = false
        @Volatile var calls = 0
        override fun decode(packet: ByteArray, out: (ByteArray, Int) -> Unit): Boolean {
            gate?.await(5, TimeUnit.SECONDS)
            calls += 1
            if (packet[0].toInt() == failOn) return false
            out(ByteArray(1920) { packet[0] }, 1920)
            return true
        }
        override fun release() { released = true }
    }

    private class Recorder : OpusDecodePipeline.Sink {
        val events = java.util.Collections.synchronizedList(mutableListOf<String>())
        override fun pcm(packet: ByteArray) { events += "pcm${packet[0]}" }
        override fun conceal(slots: Int) { events += "conceal$slots" }
        override fun crossfade() { events += "crossfade" }
    }

    private fun waitFor(cond: () -> Boolean) {
        val deadline = System.nanoTime() + 5_000_000_000L
        while (!cond() && System.nanoTime() < deadline) Thread.sleep(2)
        assertTrue("timed out", cond())
    }

    @Test
    fun theReleaseOrderIsKept() {
        val dec = FakeDecoder()
        val sink = Recorder()
        val p = OpusDecodePipeline({ dec }, sink)
        p.start()
        p.offerFrame(480, byteArrayOf(1))
        p.offerFrame(480, null)                 // given up: 2 slots
        p.offerFrame(480, byteArrayOf(3))
        p.offerConceal(6, true)                 // an outage past the cap
        p.offerFrame(480, byteArrayOf(4))
        waitFor { sink.events.size == 9 }
        assertEquals(
            listOf("pcm1", "pcm1", "conceal2", "pcm3", "pcm3", "conceal6", "crossfade", "pcm4", "pcm4"),
            sink.events.toList(),
        )
        assertEquals(3, p.framesDecoded.get())
        assertEquals("fake", p.decoderName)
        p.stop()
        assertTrue(dec.released)
    }

    @Test
    fun theOfferNeverWaitsOnTheCodec() {
        val gate = CountDownLatch(1)                       // the decoder blocks until released
        val sink = Recorder()
        val p = OpusDecodePipeline({ FakeDecoder(gate) }, sink, capacity = 8)
        p.start()
        val t0 = System.nanoTime()
        var accepted = 0
        for (i in 0 until 20) if (p.offerFrame(480, byteArrayOf(i.toByte()))) accepted += 1
        val elapsedMs = (System.nanoTime() - t0) / 1_000_000
        assertTrue("offers took $elapsedMs ms", elapsedMs < 200)
        // one item is inside the blocked decode call, 8 queued; the rest dropped and counted
        assertTrue(accepted in 8..9)
        assertEquals((20 - accepted).toLong(), p.queueDrops.get())
        assertEquals(8L, p.queueDepthMax.get())
        gate.countDown()
        waitFor { p.framesDecoded.get() == accepted.toLong() }
        assertTrue(p.queueWaitMaxNs.get() > 0)
        assertTrue(p.decodeCallMaxNs.get() > 0)
        p.stop()
    }

    @Test
    fun aFailedDecodeIsConcealedAndCounted() {
        val sink = Recorder()
        val p = OpusDecodePipeline({ FakeDecoder(failOn = 2) }, sink)
        p.start()
        p.offerFrame(480, byteArrayOf(1))
        p.offerFrame(480, byteArrayOf(2))
        p.offerFrame(480, byteArrayOf(3))
        waitFor { sink.events.size == 5 }
        assertEquals(listOf("pcm1", "pcm1", "conceal2", "pcm3", "pcm3"), sink.events.toList())
        assertEquals(1L, p.decodeFailures.get())
        p.stop()
    }

    @Test
    fun noDecoderMeansConcealment() {
        val sink = Recorder()
        val p = OpusDecodePipeline({ throw IllegalStateException("no codec") }, sink)
        p.start()
        p.offerFrame(960, byteArrayOf(1))                  // 20-ms frame: 4 slots
        p.offerFrame(480, byteArrayOf(2))
        waitFor { sink.events.size == 2 }
        assertEquals(listOf("conceal4", "conceal2"), sink.events.toList())
        assertEquals("unavailable", p.decoderName)
        assertEquals(2L, p.decodeFailures.get())
        p.stop()
    }

    @Test
    fun stopEndsTheThreadAndClears() {
        val dec = FakeDecoder()
        val p = OpusDecodePipeline({ dec }, Recorder())
        p.start()
        p.offerFrame(480, byteArrayOf(1))
        waitFor { p.framesDecoded.get() == 1L }
        p.stop()
        assertTrue(dec.released)
        assertEquals(0, p.queueDepth)
        assertFalse(Thread.getAllStackTraces().keys.any { it.name == "PrivyHub-Native-Audio-Opus" && it.isAlive })
    }
}
