package com.safeiot.privyhub.streaming

import android.media.MediaCodec
import android.media.MediaCodecInfo
import android.media.MediaFormat
import android.os.Build
import android.view.Surface
import java.nio.ByteBuffer
import java.util.ArrayDeque
import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicLong
import kotlin.concurrent.thread

data class DecoderMetrics(
    val queuedFrames: Long,
    val renderedFrames: Long,
    val droppedFrames: Long,
    val queueDepth: Int,
    val maxQueueDepth: Int,
    val inputWaits: Long,
    val queueOverflowDrops: Long,
    val staleOutputDrops: Long,
    val latestFeedDelayMs: Long,
    val maxFeedDelayMs: Long,
    val latestCodecMs: Long,
    val maxCodecMs: Long,
    val latestReceiveToDecodeMs: Long,
    val maxReceiveToDecodeMs: Long,
    val timestampAnomalies: Long,
    val spike20ms: Long,
    val spike50ms: Long,
    val spike80ms: Long,
    val spike250ms: Long,
    val spike500ms: Long,
    val codecInFlight: Long,
    val maxCodecInFlight: Long,
    val latestOutputGapMs: Long,
    val maxOutputGapMs: Long,
    val codecName: String,
    val hardwareAccelerated: Boolean,
    val vendorCodec: Boolean,
    val lowLatencyEnabled: Boolean
)

data class DecoderSlowEvent(
    val eventAtNs: Long,
    val receiveToDecodeMs: Long,
    val feedDelayMs: Long,
    val codecMs: Long,
    val codecInFlight: Long,
    val appQueueDepth: Int,
    val outputGapMs: Long
)

class AvcLowLatencyDecoder(
    surface: Surface,
    width: Int,
    height: Int,
    fps: Int,
    sps: ByteArray,
    pps: ByteArray
) {
    companion object {
        private const val INPUT_QUEUE_CAPACITY = 4
        private const val SLOW_EVENT_THRESHOLD_MS = 50L
        private const val MAX_SLOW_EVENTS = 128
    }

    private data class EncodedFrame(
        val data: ByteArray,
        val presentationTimeUs: Long
    )

    private val queue =
        ArrayBlockingQueue<EncodedFrame>(
            INPUT_QUEUE_CAPACITY
        )

    private val queuedFrames = AtomicLong(0)
    private val renderedFrames = AtomicLong(0)
    private val droppedFrames = AtomicLong(0)
    private val inputWaits = AtomicLong(0)
    private val queueOverflowDrops = AtomicLong(0)
    private val staleOutputDrops = AtomicLong(0)
    private val maxQueueDepth = AtomicInteger(0)
    private val latestFeedDelayMs = AtomicLong(0)
    private val maxFeedDelayMs = AtomicLong(0)
    private val latestCodecMs = AtomicLong(0)
    private val maxCodecMs = AtomicLong(0)
    private val latestReceiveToDecodeMs = AtomicLong(0)
    private val maxReceiveToDecodeMs = AtomicLong(0)
    private val timestampAnomalies = AtomicLong(0)
    private val spike20ms = AtomicLong(0)
    private val spike50ms = AtomicLong(0)
    private val spike80ms = AtomicLong(0)
    private val spike250ms = AtomicLong(0)
    private val spike500ms = AtomicLong(0)
    private val codecInputs = AtomicLong(0)
    private val codecOutputs = AtomicLong(0)
    private val maxCodecInFlight = AtomicLong(0)
    private val latestOutputGapMs = AtomicLong(0)
    private val maxOutputGapMs = AtomicLong(0)

    private val feedTimesUs =
        ConcurrentHashMap<Long, Long>()

    private val slowEventsLock = Any()

    private val slowEvents =
        ArrayDeque<DecoderSlowEvent>(
            MAX_SLOW_EVENTS
        )

    @Volatile
    private var lastOutputAtUs = 0L

    @Volatile
    private var running = true

    @Volatile
    private var lowLatencyEnabled = false

    private val codec =
        MediaCodec.createDecoderByType(
            MediaFormat.MIMETYPE_VIDEO_AVC
        )

    private val codecName: String
    private val hardwareAccelerated: Boolean
    private val vendorCodec: Boolean
    private val worker: Thread

    init {
        codecName =
            try {
                codec.name
            } catch (_: Exception) {
                "unknown"
            }

        if (
            Build.VERSION.SDK_INT >=
            Build.VERSION_CODES.Q
        ) {
            hardwareAccelerated =
                try {
                    codec.codecInfo
                        .isHardwareAccelerated
                } catch (_: Exception) {
                    false
                }

            vendorCodec =
                try {
                    codec.codecInfo.isVendor
                } catch (_: Exception) {
                    false
                }
        } else {
            hardwareAccelerated = false
            vendorCodec = false
        }

        val format =
            MediaFormat.createVideoFormat(
                MediaFormat.MIMETYPE_VIDEO_AVC,
                width,
                height
            )

        format.setInteger(
            MediaFormat.KEY_MAX_INPUT_SIZE,
            1024 * 1024
        )

        format.setInteger(
            MediaFormat.KEY_PRIORITY,
            0
        )

        format.setFloat(
            MediaFormat.KEY_OPERATING_RATE,
            fps.toFloat()
        )

        format.setByteBuffer(
            "csd-0",
            ByteBuffer.wrap(
                withStartCode(sps)
            )
        )

        format.setByteBuffer(
            "csd-1",
            ByteBuffer.wrap(
                withStartCode(pps)
            )
        )

        if (
            Build.VERSION.SDK_INT >=
            Build.VERSION_CODES.R
        ) {
            try {
                val capabilities =
                    codec.codecInfo
                        .getCapabilitiesForType(
                            MediaFormat.MIMETYPE_VIDEO_AVC
                        )

                if (
                    capabilities
                        .isFeatureSupported(
                            MediaCodecInfo
                                .CodecCapabilities
                                .FEATURE_LowLatency
                        )
                ) {
                    format.setInteger(
                        MediaFormat.KEY_LOW_LATENCY,
                        1
                    )
                    lowLatencyEnabled = true
                }
            } catch (_: Exception) {
                lowLatencyEnabled = false
            }
        }

        codec.configure(
            format,
            surface,
            null,
            0
        )
        codec.start()

        worker =
            thread(
                start = true,
                isDaemon = true,
                name = "PrivyHub-MediaCodec"
            ) {
                decoderLoop()
            }
    }

    fun queueAccessUnit(
        data: ByteArray,
        presentationTimeUs: Long
    ) {
        if (!running) {
            return
        }

        val frame =
            EncodedFrame(
                data = data,
                presentationTimeUs =
                    presentationTimeUs
            )

        if (!queue.offer(frame)) {
            // Preserve v0.7 behavior for diagnosis only.
            queue.poll()
            droppedFrames.incrementAndGet()
            queueOverflowDrops.incrementAndGet()

            if (!queue.offer(frame)) {
                droppedFrames.incrementAndGet()
                return
            }
        }

        queuedFrames.incrementAndGet()

        updateMax(
            maxQueueDepth,
            queue.size
        )
    }

    fun snapshot(): DecoderMetrics {
        return DecoderMetrics(
            queuedFrames = queuedFrames.get(),
            renderedFrames = renderedFrames.get(),
            droppedFrames = droppedFrames.get(),
            queueDepth = queue.size,
            maxQueueDepth = maxQueueDepth.get(),
            inputWaits = inputWaits.get(),
            queueOverflowDrops =
                queueOverflowDrops.get(),
            staleOutputDrops =
                staleOutputDrops.get(),
            latestFeedDelayMs =
                latestFeedDelayMs.get(),
            maxFeedDelayMs =
                maxFeedDelayMs.get(),
            latestCodecMs =
                latestCodecMs.get(),
            maxCodecMs =
                maxCodecMs.get(),
            latestReceiveToDecodeMs =
                latestReceiveToDecodeMs.get(),
            maxReceiveToDecodeMs =
                maxReceiveToDecodeMs.get(),
            timestampAnomalies =
                timestampAnomalies.get(),
            spike20ms = spike20ms.get(),
            spike50ms = spike50ms.get(),
            spike80ms = spike80ms.get(),
            spike250ms = spike250ms.get(),
            spike500ms = spike500ms.get(),
            codecInFlight =
                (
                    codecInputs.get() -
                        codecOutputs.get()
                ).coerceAtLeast(0L),
            maxCodecInFlight =
                maxCodecInFlight.get(),
            latestOutputGapMs =
                latestOutputGapMs.get(),
            maxOutputGapMs =
                maxOutputGapMs.get(),
            codecName = codecName,
            hardwareAccelerated =
                hardwareAccelerated,
            vendorCodec = vendorCodec,
            lowLatencyEnabled =
                lowLatencyEnabled
        )
    }

    fun slowEventsSnapshot():
        List<DecoderSlowEvent> {
        synchronized(slowEventsLock) {
            return slowEvents.toList()
        }
    }

    fun close() {
        running = false
        worker.interrupt()

        try {
            worker.join(1000)
        } catch (_: InterruptedException) {
            Thread.currentThread()
                .interrupt()
        }
    }

    private fun decoderLoop() {
        val info =
            MediaCodec.BufferInfo()

        var pending:
            EncodedFrame? =
            null

        try {
            while (running) {
                drainOutputs(info)

                if (pending == null) {
                    pending =
                        try {
                            queue.poll(
                                2,
                                TimeUnit.MILLISECONDS
                            )
                        } catch (_: InterruptedException) {
                            if (!running) {
                                break
                            }
                            null
                        }
                }

                val frame = pending

                if (frame != null) {
                    val inputIndex =
                        codec.dequeueInputBuffer(
                            1_000
                        )

                    if (inputIndex >= 0) {
                        val inputBuffer =
                            codec.getInputBuffer(
                                inputIndex
                            )

                        if (
                            inputBuffer != null &&
                            frame.data.size <=
                            inputBuffer.capacity()
                        ) {
                            inputBuffer.clear()
                            inputBuffer.put(frame.data)

                            val feedAtUs =
                                System.nanoTime() /
                                    1000L

                            val feedDelayMs =
                                (
                                    feedAtUs -
                                        frame.presentationTimeUs
                                ).coerceAtLeast(0L) /
                                    1000L

                            latestFeedDelayMs.set(
                                feedDelayMs
                            )
                            updateMax(
                                maxFeedDelayMs,
                                feedDelayMs
                            )

                            feedTimesUs[
                                frame.presentationTimeUs
                            ] = feedAtUs

                            codec.queueInputBuffer(
                                inputIndex,
                                0,
                                frame.data.size,
                                frame.presentationTimeUs,
                                0
                            )

                            val inputs =
                                codecInputs
                                    .incrementAndGet()

                            val inFlight =
                                (
                                    inputs -
                                        codecOutputs.get()
                                ).coerceAtLeast(0L)

                            updateMax(
                                maxCodecInFlight,
                                inFlight
                            )
                        } else {
                            droppedFrames
                                .incrementAndGet()

                            codec.queueInputBuffer(
                                inputIndex,
                                0,
                                0,
                                frame.presentationTimeUs,
                                0
                            )
                        }

                        pending = null
                    } else {
                        inputWaits.incrementAndGet()
                    }
                }

                drainOutputs(info)
            }
        } finally {
            try {
                codec.stop()
            } catch (_: Exception) {
            }

            try {
                codec.release()
            } catch (_: Exception) {
            }
        }
    }

    private fun drainOutputs(
        info: MediaCodec.BufferInfo
    ) {
        while (running) {
            val outputIndex =
                codec.dequeueOutputBuffer(
                    info,
                    0
                )

            if (outputIndex >= 0) {
                val nowUs =
                    System.nanoTime() /
                        1000L

                val latencyMs =
                    (
                        nowUs -
                            info.presentationTimeUs
                    ).coerceAtLeast(0L) /
                        1000L

                val plausibleTimestamp =
                    latencyMs <= 10_000L

                if (plausibleTimestamp) {
                    latestReceiveToDecodeMs.set(
                        latencyMs
                    )
                    updateMax(
                        maxReceiveToDecodeMs,
                        latencyMs
                    )

                    if (latencyMs >= 20L) {
                        spike20ms.incrementAndGet()
                    }
                    if (latencyMs >= 50L) {
                        spike50ms.incrementAndGet()
                    }
                    if (latencyMs >= 80L) {
                        spike80ms.incrementAndGet()
                    }
                    if (latencyMs >= 250L) {
                        spike250ms.incrementAndGet()
                    }
                    if (latencyMs >= 500L) {
                        spike500ms.incrementAndGet()
                    }
                } else {
                    timestampAnomalies
                        .incrementAndGet()
                }

                val feedAtUs =
                    feedTimesUs.remove(
                        info.presentationTimeUs
                    )

                var frameFeedDelayMs = -1L
                var frameCodecMs = -1L

                if (feedAtUs != null) {
                    frameFeedDelayMs =
                        (
                            feedAtUs -
                                info.presentationTimeUs
                        ).coerceAtLeast(0L) /
                            1000L

                    frameCodecMs =
                        (
                            nowUs -
                                feedAtUs
                        ).coerceAtLeast(0L) /
                            1000L

                    latestCodecMs.set(
                        frameCodecMs
                    )
                    updateMax(
                        maxCodecMs,
                        frameCodecMs
                    )
                }

                val outputs =
                    codecOutputs
                        .incrementAndGet()

                val inFlight =
                    (
                        codecInputs.get() -
                            outputs
                    ).coerceAtLeast(0L)

                var frameOutputGapMs = 0L

                if (lastOutputAtUs > 0L) {
                    frameOutputGapMs =
                        (
                            nowUs -
                                lastOutputAtUs
                        ).coerceAtLeast(0L) /
                            1000L

                    latestOutputGapMs.set(
                        frameOutputGapMs
                    )
                    updateMax(
                        maxOutputGapMs,
                        frameOutputGapMs
                    )
                }

                lastOutputAtUs = nowUs

                if (
                    plausibleTimestamp &&
                    latencyMs >=
                    SLOW_EVENT_THRESHOLD_MS
                ) {
                    recordSlowEvent(
                        DecoderSlowEvent(
                            eventAtNs =
                                nowUs * 1000L,
                            receiveToDecodeMs =
                                latencyMs,
                            feedDelayMs =
                                frameFeedDelayMs,
                            codecMs =
                                frameCodecMs,
                            codecInFlight =
                                inFlight,
                            appQueueDepth =
                                queue.size,
                            outputGapMs =
                                frameOutputGapMs
                        )
                    )
                }

                if (latencyMs > 60L) {
                    // Same v0.7 stale-presentation policy.
                    codec.releaseOutputBuffer(
                        outputIndex,
                        false
                    )
                    staleOutputDrops
                        .incrementAndGet()
                } else {
                    codec.releaseOutputBuffer(
                        outputIndex,
                        System.nanoTime()
                    )
                    renderedFrames
                        .incrementAndGet()
                }

                continue
            }

            if (
                outputIndex ==
                MediaCodec
                    .INFO_OUTPUT_FORMAT_CHANGED
            ) {
                continue
            }

            break
        }
    }

    private fun recordSlowEvent(
        event: DecoderSlowEvent
    ) {
        synchronized(slowEventsLock) {
            while (
                slowEvents.size >=
                MAX_SLOW_EVENTS
            ) {
                slowEvents.removeFirst()
            }
            slowEvents.addLast(event)
        }
    }

    private fun updateMax(
        target: AtomicLong,
        value: Long
    ) {
        while (true) {
            val old = target.get()

            if (
                value <= old ||
                target.compareAndSet(
                    old,
                    value
                )
            ) {
                return
            }
        }
    }

    private fun updateMax(
        target: AtomicInteger,
        value: Int
    ) {
        while (true) {
            val old = target.get()

            if (
                value <= old ||
                target.compareAndSet(
                    old,
                    value
                )
            ) {
                return
            }
        }
    }

    private fun withStartCode(
        nal: ByteArray
    ): ByteArray {
        val output =
            ByteArray(4 + nal.size)

        output[0] = 0
        output[1] = 0
        output[2] = 0
        output[3] = 1

        System.arraycopy(
            nal,
            0,
            output,
            4,
            nal.size
        )

        return output
    }
}
