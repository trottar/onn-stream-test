package com.safeiot.privyhub.streaming

import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicLong

/**
 * CL-B5: the Opus decode off the audio receive thread. CL-B4 decoded
 * synchronously on it (3.3 ms per frame on average, 84 ms at most), so the
 * socket was not read while the codec worked; the likely cause of its 40
 * underruns.
 *
 * The receive thread offers what [OpusReorder] releases, in order, to a
 * bounded queue and never waits: a full queue drops the item and counts it.
 * One decode thread takes the items in that order, owns the decoder (made on
 * its first frame, released at its end) and feeds the [Sink] — for an Opus
 * session it is the PCM queue's only producer. Pure Kotlin: the decoder and
 * the sink are injected, so the JVM tests drive it.
 */
class OpusDecodePipeline(
    private val decoderFactory: (Int) -> FrameDecoder,
    private val sink: Sink,
    capacity: Int = DEFAULT_CAPACITY,
    private val clock: () -> Long = System::nanoTime,
) {
    companion object {
        const val DEFAULT_CAPACITY = 64          // ~640 ms of 10-ms frames
        private const val POLL_MS = 200L
        private const val JOIN_MS = 1000L
    }

    interface FrameDecoder {
        val name: String

        /** Decode one packet; [out] gets each PCM output (bytes, length). False if it was not decoded. */
        fun decode(packet: ByteArray, out: (ByteArray, Int) -> Unit): Boolean

        fun release()
    }

    interface Sink {
        fun pcm(packet: ByteArray)

        fun conceal(slots: Int)

        fun crossfade()
    }

    private class Item(
        val frames: Int,
        val payload: ByteArray?,
        val concealSlots: Int,
        val crossfade: Boolean,
        val enqueuedNs: Long,
    )

    private val queue = ArrayBlockingQueue<Item>(capacity)

    @Volatile private var running = false
    private var worker: Thread? = null

    @Volatile var decoder: FrameDecoder? = null
        private set
    @Volatile var decoderName: String = ""
        private set
    @Volatile private var decoderFailed = false

    val framesDecoded = AtomicLong(0)
    val decodeFailures = AtomicLong(0)
    val queueDrops = AtomicLong(0)
    val queueDepthMax = AtomicLong(0)
    val queueWaitMaxNs = AtomicLong(0)
    val decodeCallMaxNs = AtomicLong(0)

    val queueDepth: Int get() = queue.size

    fun start(threadName: String = "PrivyHub-Native-Audio-Opus") {
        if (running) return
        running = true
        worker = Thread({ loop() }, threadName).apply {
            isDaemon = true
            start()
        }
    }

    /** A frame in release order; [payload] null = given up (concealed as frames / 240 slots). Never blocks. */
    fun offerFrame(frames: Int, payload: ByteArray?): Boolean =
        offer(Item(frames, payload, 0, false, clock()))

    /** An outage's concealment (today's cap) and, past the cap, the crossfade. Never blocks. */
    fun offerConceal(slots: Int, crossfade: Boolean): Boolean =
        offer(Item(0, null, slots, crossfade, clock()))

    private fun offer(item: Item): Boolean {
        if (!queue.offer(item)) {
            queueDrops.incrementAndGet()
            return false
        }
        max(queueDepthMax, queue.size.toLong())
        return true
    }

    private fun max(cell: AtomicLong, value: Long) {
        while (true) {
            val old = cell.get()
            if (value <= old || cell.compareAndSet(old, value)) return
        }
    }

    private fun loop() {
        try {
            while (running) {
                val item = try {
                    queue.poll(POLL_MS, TimeUnit.MILLISECONDS)
                } catch (_: InterruptedException) {
                    if (!running) break else continue
                } ?: continue
                max(queueWaitMaxNs, clock() - item.enqueuedNs)
                handle(item)
            }
        } finally {
            decoder?.release()
        }
    }

    private fun handle(item: Item) {
        if (item.frames == 0) {
            sink.conceal(item.concealSlots)
            if (item.crossfade) sink.crossfade()
            return
        }
        val slots = item.frames / OpusFraming.QUEUE_PACKET_FRAMES
        val payload = item.payload
        if (payload == null) {
            sink.conceal(slots)
            return
        }
        val d = decoder ?: if (decoderFailed) null else try {
            decoderFactory(item.frames).also {
                decoder = it
                decoderName = it.name
            }
        } catch (_: Exception) {
            decoderFailed = true
            decoderName = "unavailable"
            null
        }
        if (d == null) {
            decodeFailures.incrementAndGet()
            sink.conceal(slots)
            return
        }
        var produced = 0
        val t0 = clock()
        val ok = try {
            d.decode(payload) { pcm, length ->
                for (chunk in OpusFraming.split(pcm, length)) {
                    sink.pcm(chunk)
                    produced += 1
                }
            }
        } catch (_: Exception) {
            false
        }
        max(decodeCallMaxNs, clock() - t0)
        if (ok) {
            framesDecoded.incrementAndGet()
        } else {
            decodeFailures.incrementAndGet()
            if (produced == 0) sink.conceal(slots)
        }
    }

    /** Stop the thread (it releases the decoder) and drop what is queued. */
    fun stop() {
        running = false
        worker?.interrupt()
        try {
            worker?.join(JOIN_MS)
        } catch (_: InterruptedException) {
            Thread.currentThread().interrupt()
        }
        worker = null
        queue.clear()
    }
}
