package com.safeiot.privyhub.streaming

import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import android.os.Build
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.SocketTimeoutException
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicLong
import kotlin.concurrent.thread
import kotlin.math.max

data class NativeAudioMetrics(
    val packets: Long,
    val lostPackets: Long,
    val pcmBytes: Long,
    val writeErrors: Long,
    val staleDrops: Long,
    val queueDepth: Int,
    val maxQueueDepth: Int,
    val trackBufferFrames: Int,
    val bufferedMs: Long,
    val underruns: Int,
    val lowLatencyMode: Boolean,
    val concealedLossPackets: Long,
    val concealedUnderruns: Long,
    val prolongedStarvationEvents: Long,
    val smoothLatencyTrims: Long,
    val crossfadedPackets: Long,
    val maxQueueResidenceMs: Long,
    val avgQueueResidenceMs: Double,
    val queueTargetPackets: Int,
    val queueCapacityPackets: Int,
    val startupPrefillMs: Long
)

class NativeAudioReceiver(
    private val port: Int
) {
    companion object {
        private const val HEADER_BYTES = 16
        private const val SAMPLE_RATE = 48_000
        private const val CHANNELS = 2
        private const val BYTES_PER_SAMPLE = 2
        private const val BYTES_PER_FRAME =
            CHANNELS *
                BYTES_PER_SAMPLE

        private const val FRAMES_PER_PACKET = 240
        private const val PACKET_MS = 5

        private const val EXPECTED_PAYLOAD =
            FRAMES_PER_PACKET *
                BYTES_PER_FRAME

        // Hard application reservoir: 8 x 5 ms = 40 ms. This remains bounded
        // and is only 10 ms larger than the prior queue.
        private const val QUEUE_PACKETS = 8

        // Start playback with about 15 ms of application PCM available. The
        // AudioTrack itself remains the same low-latency ~20 ms target.
        private const val TARGET_QUEUE_PACKETS = 3

        private const val STARTUP_PREFILL_TIMEOUT_MS = 100L

        // Wait at most one PCM packet interval before synthesizing continuity.
        private const val STARVATION_POLL_MS = PACKET_MS.toLong()

        // First 10 ms of a starvation episode fades toward silence. Any longer
        // starvation is filled with silence until real PCM returns.
        private const val FADE_CONCEAL_PACKETS = 2

        // 1 ms at 48 kHz. Used only after a trim/concealment boundary.
        private const val CROSSFADE_FRAMES = 48

        // Request a ~20 ms AudioTrack write buffer. Android may adjust this
        // upward to a device-supported value.
        private const val TARGET_TRACK_FRAMES = 960
    }

    private data class PcmPacket(
        val payload: ByteArray?,
        val concealLoss: Boolean,
        val enqueuedNs: Long
    )

    private val queue =
        ArrayBlockingQueue<PcmPacket>(
            QUEUE_PACKETS
        )

    private val packets =
        AtomicLong(0)

    private val lostPackets =
        AtomicLong(0)

    private val pcmBytes =
        AtomicLong(0)

    private val writeErrors =
        AtomicLong(0)

    private val staleDrops =
        AtomicLong(0)

    private val maxQueueDepth =
        AtomicInteger(0)

    private val framesWritten =
        AtomicLong(0)

    private val concealedLossPackets =
        AtomicLong(0)

    private val concealedUnderruns =
        AtomicLong(0)

    private val prolongedStarvationEvents =
        AtomicLong(0)

    private val smoothLatencyTrims =
        AtomicLong(0)

    private val crossfadedPackets =
        AtomicLong(0)

    private val queueResidenceTotalNs =
        AtomicLong(0)

    private val queueResidenceSamples =
        AtomicLong(0)

    private val maxQueueResidenceNs =
        AtomicLong(0)

    @Volatile
    private var running =
        false

    @Volatile
    private var socket:
        DatagramSocket? =
        null

    @Volatile
    private var track:
        AudioTrack? =
        null

    @Volatile
    private var actualTrackBufferFrames =
        0

    @Volatile
    private var lowLatencyMode =
        false

    @Volatile
    private var trimCrossfadePending =
        false

    @Volatile
    private var startupPrefillMs =
        0L

    private var receiveWorker:
        Thread? =
        null

    private var playbackWorker:
        Thread? =
        null

    private var expectedSequence =
        -1

    fun start() {
        if (running) {
            return
        }

        queue.clear()
        expectedSequence =
            -1
        trimCrossfadePending =
            false
        startupPrefillMs =
            0L

        running =
            true

        playbackWorker =
            thread(
                start = true,
                isDaemon = true,
                name = "PrivyHub-Native-Audio-Playback"
            ) {
                playbackLoop()
            }

        receiveWorker =
            thread(
                start = true,
                isDaemon = true,
                name = "PrivyHub-Native-Audio-RX"
            ) {
                receiveLoop()
            }
    }

    fun stop() {
        running =
            false

        try {
            socket?.close()
        } catch (_: Exception) {
        }

        receiveWorker?.interrupt()
        playbackWorker?.interrupt()

        try {
            receiveWorker?.join(
                1000
            )
        } catch (_: InterruptedException) {
            Thread.currentThread()
                .interrupt()
        }

        try {
            playbackWorker?.join(
                1000
            )
        } catch (_: InterruptedException) {
            Thread.currentThread()
                .interrupt()
        }

        receiveWorker =
            null

        playbackWorker =
            null

        socket =
            null

        queue.clear()
    }

    fun snapshot():
        NativeAudioMetrics {
        val currentTrack =
            track

        val playbackHead =
            if (currentTrack != null) {
                try {
                    currentTrack
                        .playbackHeadPosition
                        .toLong() and
                        0xffffffffL
                } catch (_: Exception) {
                    0L
                }
            } else {
                0L
            }

        val bufferedFrames =
            (
                framesWritten.get() -
                    playbackHead
            ).coerceAtLeast(
                0L
            )

        val bufferedMs =
            bufferedFrames *
                1000L /
                SAMPLE_RATE

        val underruns =
            if (
                currentTrack != null &&
                Build.VERSION.SDK_INT >=
                Build.VERSION_CODES.N
            ) {
                try {
                    currentTrack.underrunCount
                } catch (_: Exception) {
                    0
                }
            } else {
                0
            }

        val residenceSamples =
            queueResidenceSamples.get()

        val averageResidenceMs =
            if (
                residenceSamples >
                0L
            ) {
                queueResidenceTotalNs.get()
                    .toDouble() /
                    residenceSamples
                        .toDouble() /
                    1_000_000.0
            } else {
                0.0
            }

        return NativeAudioMetrics(
            packets =
                packets.get(),
            lostPackets =
                lostPackets.get(),
            pcmBytes =
                pcmBytes.get(),
            writeErrors =
                writeErrors.get(),
            staleDrops =
                staleDrops.get(),
            queueDepth =
                queue.size,
            maxQueueDepth =
                maxQueueDepth.get(),
            trackBufferFrames =
                actualTrackBufferFrames,
            bufferedMs =
                bufferedMs,
            underruns =
                underruns,
            lowLatencyMode =
                lowLatencyMode,
            concealedLossPackets =
                concealedLossPackets.get(),
            concealedUnderruns =
                concealedUnderruns.get(),
            prolongedStarvationEvents =
                prolongedStarvationEvents.get(),
            smoothLatencyTrims =
                smoothLatencyTrims.get(),
            crossfadedPackets =
                crossfadedPackets.get(),
            maxQueueResidenceMs =
                maxQueueResidenceNs.get() /
                    1_000_000L,
            avgQueueResidenceMs =
                averageResidenceMs,
            queueTargetPackets =
                TARGET_QUEUE_PACKETS,
            queueCapacityPackets =
                QUEUE_PACKETS,
            startupPrefillMs =
                startupPrefillMs
        )
    }

    private fun createAudioTrack():
        AudioTrack {
        val format =
            AudioFormat.Builder()
                .setEncoding(
                    AudioFormat.ENCODING_PCM_16BIT
                )
                .setSampleRate(
                    SAMPLE_RATE
                )
                .setChannelMask(
                    AudioFormat.CHANNEL_OUT_STEREO
                )
                .build()

        val attributes =
            AudioAttributes.Builder()
                .setUsage(
                    AudioAttributes.USAGE_GAME
                )
                .setContentType(
                    AudioAttributes.CONTENT_TYPE_MUSIC
                )
                .build()

        val minimum =
            AudioTrack.getMinBufferSize(
                SAMPLE_RATE,
                AudioFormat.CHANNEL_OUT_STEREO,
                AudioFormat.ENCODING_PCM_16BIT
            )

        val requestedBytes =
            max(
                minimum,
                TARGET_TRACK_FRAMES *
                    BYTES_PER_FRAME
            )

        val builder =
            AudioTrack.Builder()
                .setAudioAttributes(
                    attributes
                )
                .setAudioFormat(
                    format
                )
                .setTransferMode(
                    AudioTrack.MODE_STREAM
                )
                .setBufferSizeInBytes(
                    requestedBytes
                )

        if (
            Build.VERSION.SDK_INT >=
            Build.VERSION_CODES.O
        ) {
            builder.setPerformanceMode(
                AudioTrack.PERFORMANCE_MODE_LOW_LATENCY
            )
        }

        val created =
            builder.build()

        if (
            Build.VERSION.SDK_INT >=
            Build.VERSION_CODES.N
        ) {
            try {
                created.setBufferSizeInFrames(
                    TARGET_TRACK_FRAMES
                )
            } catch (_: Exception) {
            }
        }

        actualTrackBufferFrames =
            try {
                created.bufferSizeInFrames
            } catch (_: Exception) {
                requestedBytes /
                    BYTES_PER_FRAME
            }

        lowLatencyMode =
            if (
                Build.VERSION.SDK_INT >=
                Build.VERSION_CODES.O
            ) {
                try {
                    created.performanceMode ==
                        AudioTrack.PERFORMANCE_MODE_LOW_LATENCY
                } catch (_: Exception) {
                    false
                }
            } else {
                false
            }

        return created
    }

    private fun receiveLoop() {
        val localSocket =
            try {
                DatagramSocket(
                    port
                )
            } catch (_: Exception) {
                writeErrors.incrementAndGet()
                running =
                    false
                return
            }

        localSocket.soTimeout =
            500

        // Keep the kernel buffer bounded. The application reservoir below is
        // the only intentional jitter/latency storage.
        localSocket.receiveBufferSize =
            64 * 1024

        socket =
            localSocket

        val buffer =
            ByteArray(
                2048
            )

        val packet =
            DatagramPacket(
                buffer,
                buffer.size
            )

        try {
            while (running) {
                try {
                    packet.length =
                        buffer.size

                    localSocket.receive(
                        packet
                    )
                } catch (_: SocketTimeoutException) {
                    continue
                } catch (_: Exception) {
                    if (running) {
                        writeErrors.incrementAndGet()
                    }

                    break
                }

                if (
                    packet.length <
                    HEADER_BYTES
                ) {
                    continue
                }

                if (
                    buffer[0] !=
                    'P'.code.toByte() ||
                    buffer[1] !=
                    'H'.code.toByte() ||
                    buffer[2] !=
                    'A'.code.toByte() ||
                    buffer[3] !=
                    '1'.code.toByte()
                ) {
                    continue
                }

                val header =
                    ByteBuffer.wrap(
                        buffer,
                        0,
                        HEADER_BYTES
                    )
                        .order(
                            ByteOrder.LITTLE_ENDIAN
                        )

                header.position(
                    4
                )

                val version =
                    header.get()
                        .toInt() and
                        0xff

                val channels =
                    header.get()
                        .toInt() and
                        0xff

                val sequence =
                    header.short
                        .toInt() and
                        0xffff

                header.int // sample timestamp

                val frames =
                    header.int

                val payloadBytes =
                    packet.length -
                        HEADER_BYTES

                if (
                    version != 1 ||
                    channels != CHANNELS ||
                    frames != FRAMES_PER_PACKET ||
                    payloadBytes != EXPECTED_PAYLOAD
                ) {
                    continue
                }

                if (
                    expectedSequence >= 0 &&
                    sequence != expectedSequence
                ) {
                    val missing =
                        (
                            sequence -
                                expectedSequence
                        ) and
                            0xffff

                    if (
                        missing in
                        1..32767
                    ) {
                        lostPackets.addAndGet(
                            missing.toLong()
                        )

                        // Preserve at most 10 ms of explicit packet loss. This
                        // keeps A/V time continuous without manufacturing a
                        // large delayed backlog after a bigger network outage.
                        repeat(
                            minOf(
                                missing,
                                2
                            )
                        ) {
                            enqueueConcealment()
                        }

                        if (
                            missing >
                            2
                        ) {
                            // The first real packet after an intentionally
                            // skipped larger hole will be ramped in smoothly.
                            trimCrossfadePending =
                                true
                        }
                    }
                }

                expectedSequence =
                    (
                        sequence + 1
                    ) and
                        0xffff

                packets.incrementAndGet()

                enqueueLatest(
                    buffer.copyOfRange(
                        HEADER_BYTES,
                        HEADER_BYTES +
                            EXPECTED_PAYLOAD
                    )
                )
            }
        } finally {
            try {
                localSocket.close()
            } catch (_: Exception) {
            }
        }
    }

    private fun enqueueLatest(
        payload: ByteArray
    ) {
        enqueuePacket(
            PcmPacket(
                payload =
                    payload,
                concealLoss =
                    false,
                enqueuedNs =
                    System.nanoTime()
            )
        )
    }

    private fun enqueueConcealment() {
        enqueuePacket(
            PcmPacket(
                payload =
                    null,
                concealLoss =
                    true,
                enqueuedNs =
                    System.nanoTime()
            )
        )
    }

    private fun enqueuePacket(
        item: PcmPacket
    ) {
        if (!queue.offer(item)) {
            // Preserve the latest audio and the latency ceiling, but explicitly
            // flag the resulting timeline trim so playback can smooth the next
            // real waveform boundary instead of making a raw PCM cut.
            if (
                queue.poll() !=
                null
            ) {
                staleDrops.incrementAndGet()
                smoothLatencyTrims.incrementAndGet()
                trimCrossfadePending =
                    true
            }

            if (!queue.offer(item)) {
                staleDrops.incrementAndGet()
                return
            }
        }

        val depth =
            queue.size

        while (true) {
            val old =
                maxQueueDepth.get()

            if (
                depth <= old ||
                maxQueueDepth.compareAndSet(
                    old,
                    depth
                )
            ) {
                break
            }
        }
    }

    private fun playbackLoop() {
        val localTrack =
            try {
                createAudioTrack()
            } catch (_: Exception) {
                writeErrors.incrementAndGet()
                running =
                    false
                return
            }

        track =
            localTrack

        var lastLeft =
            0

        var lastRight =
            0

        var hasLastSample =
            false

        var crossfadeNextReal =
            false

        var starvationPackets =
            0

        var starvationEpisodeCounted =
            false

        try {
            val prefillStartedNs =
                System.nanoTime()

            while (
                running &&
                queue.size <
                TARGET_QUEUE_PACKETS &&
                (
                    System.nanoTime() -
                        prefillStartedNs
                ) <
                STARTUP_PREFILL_TIMEOUT_MS *
                    1_000_000L
            ) {
                try {
                    Thread.sleep(
                        1
                    )
                } catch (_: InterruptedException) {
                    if (!running) {
                        break
                    }
                }
            }

            startupPrefillMs =
                (
                    System.nanoTime() -
                        prefillStartedNs
                ).coerceAtLeast(
                    0L
                ) /
                    1_000_000L

            localTrack.play()

            while (running) {
                val item =
                    try {
                        queue.poll(
                            STARVATION_POLL_MS,
                            TimeUnit.MILLISECONDS
                        )
                    } catch (_: InterruptedException) {
                        if (!running) {
                            break
                        }

                        null
                    }

                val nowNs =
                    System.nanoTime()

                var payload:
                    ByteArray

                var isRealPacket =
                    false

                if (item != null) {
                    observeQueueResidence(
                        nowNs -
                            item.enqueuedNs
                    )

                    if (
                        item.concealLoss ||
                        item.payload ==
                        null
                    ) {
                        concealedLossPackets.incrementAndGet()

                        payload =
                            makeContinuityPacket(
                                lastLeft,
                                lastRight,
                                hasLastSample
                            )

                        crossfadeNextReal =
                            true
                    } else {
                        payload =
                            item.payload

                        isRealPacket =
                            true
                    }

                    starvationPackets =
                        0

                    starvationEpisodeCounted =
                        false
                } else {
                    concealedUnderruns.incrementAndGet()

                    starvationPackets +=
                        1

                    if (
                        starvationPackets >
                        FADE_CONCEAL_PACKETS &&
                        !starvationEpisodeCounted
                    ) {
                        prolongedStarvationEvents.incrementAndGet()
                        starvationEpisodeCounted =
                            true
                    }

                    payload =
                        makeContinuityPacket(
                            lastLeft,
                            lastRight,
                            hasLastSample &&
                                starvationPackets <=
                                FADE_CONCEAL_PACKETS
                        )

                    crossfadeNextReal =
                        true
                }

                if (
                    isRealPacket &&
                    (
                        crossfadeNextReal ||
                        trimCrossfadePending
                    ) &&
                    hasLastSample
                ) {
                    payload =
                        payload.copyOf()

                    smoothPacketStart(
                        payload,
                        lastLeft,
                        lastRight
                    )

                    crossfadedPackets.incrementAndGet()

                    crossfadeNextReal =
                        false

                    trimCrossfadePending =
                        false
                } else if (isRealPacket) {
                    crossfadeNextReal =
                        false

                    trimCrossfadePending =
                        false
                }

                val written =
                    try {
                        localTrack.write(
                            payload,
                            0,
                            payload.size,
                            AudioTrack.WRITE_BLOCKING
                        )
                    } catch (_: Exception) {
                        -1
                    }

                if (
                    written >
                    0
                ) {
                    pcmBytes.addAndGet(
                        written.toLong()
                    )

                    framesWritten.addAndGet(
                        (
                            written /
                                BYTES_PER_FRAME
                        ).toLong()
                    )

                    if (
                        written >=
                        BYTES_PER_FRAME
                    ) {
                        val lastFrameOffset =
                            written -
                                BYTES_PER_FRAME

                        lastLeft =
                            readPcm16(
                                payload,
                                lastFrameOffset
                            )

                        lastRight =
                            readPcm16(
                                payload,
                                lastFrameOffset +
                                    BYTES_PER_SAMPLE
                            )

                        hasLastSample =
                            true
                    }
                } else {
                    writeErrors.incrementAndGet()
                }
            }
        } finally {
            try {
                localTrack.pause()
            } catch (_: Exception) {
            }

            try {
                localTrack.flush()
            } catch (_: Exception) {
            }

            try {
                localTrack.release()
            } catch (_: Exception) {
            }

            track =
                null
        }
    }

    private fun makeContinuityPacket(
        lastLeft: Int,
        lastRight: Int,
        fadeFromLast: Boolean
    ):
        ByteArray {
        val output =
            ByteArray(
                EXPECTED_PAYLOAD
            )

        if (!fadeFromLast) {
            return output
        }

        val denominator =
            max(
                1,
                FRAMES_PER_PACKET -
                    1
            )

        for (
            frame in
            0 until
            FRAMES_PER_PACKET
        ) {
            val remaining =
                FRAMES_PER_PACKET -
                    1 -
                    frame

            val left =
                lastLeft *
                    remaining /
                    denominator

            val right =
                lastRight *
                    remaining /
                    denominator

            val offset =
                frame *
                    BYTES_PER_FRAME

            writePcm16(
                output,
                offset,
                left
            )

            writePcm16(
                output,
                offset +
                    BYTES_PER_SAMPLE,
                right
            )
        }

        return output
    }

    private fun smoothPacketStart(
        payload: ByteArray,
        lastLeft: Int,
        lastRight: Int
    ) {
        val frames =
            minOf(
                CROSSFADE_FRAMES,
                payload.size /
                    BYTES_PER_FRAME
            )

        if (
            frames <=
            0
        ) {
            return
        }

        val denominator =
            max(
                1,
                frames
            )

        for (
            frame in
            0 until
            frames
        ) {
            val offset =
                frame *
                    BYTES_PER_FRAME

            val originalLeft =
                readPcm16(
                    payload,
                    offset
                )

            val originalRight =
                readPcm16(
                    payload,
                    offset +
                        BYTES_PER_SAMPLE
                )

            val incomingWeight =
                frame +
                    1

            val previousWeight =
                denominator -
                    incomingWeight

            val left =
                (
                    lastLeft *
                        previousWeight +
                        originalLeft *
                        incomingWeight
                ) /
                    denominator

            val right =
                (
                    lastRight *
                        previousWeight +
                        originalRight *
                        incomingWeight
                ) /
                    denominator

            writePcm16(
                payload,
                offset,
                left
            )

            writePcm16(
                payload,
                offset +
                    BYTES_PER_SAMPLE,
                right
            )
        }
    }

    private fun observeQueueResidence(
        residenceNs: Long
    ) {
        val safe =
            residenceNs.coerceAtLeast(
                0L
            )

        queueResidenceTotalNs.addAndGet(
            safe
        )

        queueResidenceSamples.incrementAndGet()

        while (true) {
            val old =
                maxQueueResidenceNs.get()

            if (
                safe <= old ||
                maxQueueResidenceNs.compareAndSet(
                    old,
                    safe
                )
            ) {
                break
            }
        }
    }

    private fun readPcm16(
        data: ByteArray,
        offset: Int
    ):
        Int {
        val value =
            (
                data[offset]
                    .toInt() and
                    0xff
            ) or
                (
                    (
                        data[
                            offset +
                                1
                        ].toInt() and
                            0xff
                    ) shl
                        8
                )

        return if (
            value >=
            0x8000
        ) {
            value -
                0x10000
        } else {
            value
        }
    }

    private fun writePcm16(
        data: ByteArray,
        offset: Int,
        value: Int
    ) {
        val clipped =
            value.coerceIn(
                -32768,
                32767
            )

        data[offset] =
            clipped.toByte()

        data[
            offset +
                1
        ] =
            (
                clipped shr
                    8
            ).toByte()
    }
}
