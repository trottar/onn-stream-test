package com.safeiot.privyhub.streaming

import android.app.Activity
import android.content.pm.ActivityInfo
import android.graphics.Bitmap
import android.graphics.Color
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.KeyEvent
import android.view.MotionEvent
import android.view.PixelCopy
import android.view.Surface
import android.view.SurfaceHolder
import android.view.SurfaceView
import android.view.View
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.TextView
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import kotlin.concurrent.thread

class NativeStreamActivity :
    Activity(),
    SurfaceHolder.Callback {

    companion object {
        const val EXTRA_COMPANION_HOST =
            "privyhub_companion_host"

        const val EXTRA_GAME_TITLE =
            "privyhub_game_title"

        fun pausedFrameFileName(
            gameTitle: String
        ): String {

            val token =
                Integer.toHexString(
                    gameTitle
                        .trim()
                        .hashCode()
                )

            return "privyhub_game_paused_$token.jpg"
        }

        private const val CONTROL_PORT = 8765
        private const val VIDEO_PORT = 48100
        private const val AUDIO_PORT = 48101
        private const val INPUT_PORT = 48102
        private const val VIDEO_WIDTH = 1280
        private const val VIDEO_HEIGHT = 720
        private const val VIDEO_FPS = 60
        private const val EXPECTED_HOST_ALPHA = "0.7"
        private const val CLIENT_PROFILER_VERSION = "0.12.2"

        // PRIVYHUB_B1_CLIENT_HEALTH_V1
        private const val CLIENT_HEALTH_INTERVAL_MS =
            2_000L
        private const val CLIENT_HEALTH_INTERVAL_NS =
            CLIENT_HEALTH_INTERVAL_MS *
                1_000_000L
    }

    private lateinit var surfaceView: SurfaceView
    private lateinit var statusView: TextView

    private val uiHandler =
        Handler(
            Looper.getMainLooper()
        )

    @Volatile
    private var decoder:
        AvcLowLatencyDecoder? =
        null

    private var receiver:
        RtpH264Receiver? =
        null

    private var audioReceiver:
        NativeAudioReceiver? =
        null

    private var controllerSender:
        NativeControllerSender? =
        null

    @Volatile
    private var sessionStarted =
        false

    @Volatile
    private var stopping =
        false

    @Volatile
    private var streamState =
        "Preparing receiver..."

    @Volatile
    private var captureDescription =
        "Capture target: waiting..."

    @Volatile
    private var hostAlphaVersion =
        "unknown"

    @Volatile
    private var hostGopFrames =
        0

    @Volatile
    private var hostVideoBitrateKbps =
        0

    @Volatile
    private var hostFecEnabled =
        false

    @Volatile
    private var hostFecGroupSize =
        0

    @Volatile
    private var hostMetadataComplete =
        false

    @Volatile
    private var hostMetadataError =
        ""

    @Volatile
    private var hostCaptureBackend =
        "unknown"

    @Volatile
    private var hostAudioState =
        "Audio host: waiting"

    @Volatile
    private var hostInputState =
        "Controller host: waiting"

    private var lastMetricAtNs =
        0L

    private var lastRtpBytes =
        0L

    private var lastRtpFrames =
        0L

    private var recentVideoMbps =
        0.0

    private var recentVideoFps =
        0.0

    private var lastClientHealthPostAtNs =
        0L

    private var clientHealthSequence =
        0L

    @Volatile
    private var clientHealthPostInFlight =
        false

    @Volatile
    private var sessionStartedAtNs =
        0L

    @Volatile
    private var cachedSessionReport:
        String? =
        null

    // PrivyHub A3 patch 11v2: capture the final rendered gameplay frame.
    @Volatile
    private var pausedFrameCaptureStatus =
        "not_requested"

    @Volatile
    private var pausedFrameBytes =
        0L

    @Volatile
    private var pausedFrameWidth =
        0

    @Volatile
    private var pausedFrameHeight =
        0

    @Volatile
    private var backExitInProgress =
        false

    private val metricsTick =
        object : Runnable {
            override fun run() {
                updateMetrics()
                uiHandler.postDelayed(
                    this,
                    500
                )
            }
        }

    override fun onCreate(
        savedInstanceState: Bundle?
    ) {
        super.onCreate(
            savedInstanceState
        )

        requestedOrientation =
            ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE

        window.addFlags(
            WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
        )

        @Suppress("DEPRECATION")
        window.decorView.systemUiVisibility =
            View.SYSTEM_UI_FLAG_FULLSCREEN or
                View.SYSTEM_UI_FLAG_HIDE_NAVIGATION or
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY

        val root =
            FrameLayout(
                this
            ).apply {
                setBackgroundColor(
                    Color.BLACK
                )
            }

        surfaceView =
            SurfaceView(
                this
            )

        root.addView(
            surfaceView,
            FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
            )
        )

        statusView =
            TextView(
                this
            ).apply {
                setTextColor(
                    Color.WHITE
                )
                setBackgroundColor(
                    0x99000000.toInt()
                )
                textSize = 14f
                setPadding(
                    18,
                    10,
                    18,
                    10
                )
                text =
                    "PrivyHub Native Video Alpha\nPreparing receiver..."
            }

        // two_player_clean_presentation_poc_v0.1.1
        statusView.visibility =
            View.GONE

        val statusLayout =
            FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,
                FrameLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                gravity =
                    Gravity.TOP or
                        Gravity.START
            }

        root.addView(
            statusView,
            statusLayout
        )

        setContentView(
            root
        )

        surfaceView.holder.addCallback(
            this
        )

        uiHandler.post(
            metricsTick
        )
    }

    override fun surfaceCreated(
        holder: SurfaceHolder
    ) {
        if (
            Build.VERSION.SDK_INT >=
            Build.VERSION_CODES.R
        ) {
            try {
                holder.surface.setFrameRate(
                    VIDEO_FPS.toFloat(),
                    Surface.FRAME_RATE_COMPATIBILITY_FIXED_SOURCE
                )
            } catch (_: Exception) {
            }
        }

        startSession(
            holder.surface
        )
    }

    override fun surfaceChanged(
        holder: SurfaceHolder,
        format: Int,
        width: Int,
        height: Int
    ) {
    }

    override fun surfaceDestroyed(
        holder: SurfaceHolder
    ) {
        if (
            Build.VERSION.SDK_INT >=
            Build.VERSION_CODES.R
        ) {
            try {
                holder.surface.setFrameRate(
                    0f,
                    Surface.FRAME_RATE_COMPATIBILITY_DEFAULT
                )
            } catch (_: Exception) {
            }
        }

        if (sessionStarted) {
            cacheSessionReport()
        }

        stopLocalPipeline()
        sessionStarted = false
    }

    override fun onDestroy() {
        uiHandler.removeCallbacks(
            metricsTick
        )

        stopSession()

        super.onDestroy()
    }

    private fun startSession(
        surface: Surface
    ) {
        if (sessionStarted) {
            return
        }

        val host =
            intent.getStringExtra(
                EXTRA_COMPANION_HOST
            )
                ?.trim()
                .orEmpty()

        if (host.isBlank()) {
            statusView.text =
                "Native stream unavailable: companion host is not configured."
            return
        }

        sessionStarted = true
        stopping = false
        cachedSessionReport = null
        pausedFrameCaptureStatus =
            "not_requested"
        pausedFrameBytes =
            0L
        pausedFrameWidth =
            0
        pausedFrameHeight =
            0
        backExitInProgress =
            false
        hostMetadataComplete = false
        hostMetadataError = ""
        sessionStartedAtNs =
            System.nanoTime()
        lastClientHealthPostAtNs =
            0L
        clientHealthSequence =
            0L
        clientHealthPostInFlight =
            false

        audioReceiver =
            NativeAudioReceiver(
                port = AUDIO_PORT
            ).also {
                it.start()
            }

        controllerSender =
            NativeControllerSender(
                host = host,
                port = INPUT_PORT
            ).also {
                it.start()
            }

        receiver =
            RtpH264Receiver(
                port = VIDEO_PORT,
                onParameterSets = { sps, pps ->
                    if (decoder == null) {
                        try {
                            decoder =
                                AvcLowLatencyDecoder(
                                    surface = surface,
                                    width = VIDEO_WIDTH,
                                    height = VIDEO_HEIGHT,
                                    fps = VIDEO_FPS,
                                    sps = sps,
                                    pps = pps
                                )

                            runOnUiThread {
                                streamState =
                                    "Decoder active"

                                updateMetrics()
                            }
                        } catch (error: Exception) {
                            runOnUiThread {
                                statusView.text =
                                    "MediaCodec setup failed\n" +
                                        (
                                            error.message
                                                ?: "Unknown error"
                                        )
                            }
                        }
                    }
                },
                onAccessUnit = { accessUnit, presentationTimeUs ->
                    decoder?.queueAccessUnit(
                        data = accessUnit,
                        presentationTimeUs = presentationTimeUs
                    )
                }
            ).also {
                it.start()
            }

        streamState =
            "Starting host stream..."

        updateMetrics()

        thread(
            start = true,
            isDaemon = true,
            name = "PrivyHub-Native-Session"
        ) {
            try {
                val response =
                    httpPost(
                        "http://$host:$CONTROL_PORT" +
                            "/plugins/games/native-stream-start" +
                            "?port=$VIDEO_PORT",
                        readTimeoutMs =
                            30_000
                    )

                val json =
                    JSONObject(
                        response
                    )

                if (
                    !json.optBoolean(
                        "active",
                        false
                    )
                ) {
                    throw IllegalStateException(
                        json.optString(
                            "message",
                            "Native stream did not remain active"
                        )
                    )
                }

                hostAlphaVersion =
                    json.optString(
                        "alpha_version",
                        "unknown"
                    )

                if (
                    hostAlphaVersion !=
                    EXPECTED_HOST_ALPHA
                ) {
                    throw IllegalStateException(
                        "Companion restart required: client expects " +
                            "v$EXPECTED_HOST_ALPHA but host is " +
                            "v$hostAlphaVersion"
                    )
                }

                hostCaptureBackend =
                    json.optString(
                        "capture_backend",
                        "unknown"
                    )

                hostGopFrames =
                    json.optInt(
                        "gop_frames",
                        0
                    )

                hostVideoBitrateKbps =
                    json.optInt(
                        "source_bitrate_kbps",
                        json.optInt(
                            "bitrate_kbps",
                            0
                        )
                    )

                hostFecEnabled =
                    json.optBoolean(
                        "fec_enabled",
                        false
                    )

                hostFecGroupSize =
                    json.optInt(
                        "fec_group_size",
                        0
                    )

                val capture =
                    json.optJSONObject(
                        "capture_target"
                    )

                captureDescription =
                    if (
                        capture?.optString(
                            "type"
                        ) ==
                        "window"
                    ) {
                        val title =
                            capture.optString(
                                "title",
                                "RetroArch"
                            )

                        val width =
                            capture.optInt(
                                "width",
                                0
                            )

                        val height =
                            capture.optInt(
                                "height",
                                0
                            )

                        "Capture: RetroArch window  " +
                            "${width}x${height}\n" +
                            title
                    } else {
                        val reason =
                            capture?.optString(
                                "fallback_reason",
                                "RetroArch window unavailable"
                            )
                                ?: "RetroArch window unavailable"

                        "Capture: DESKTOP FALLBACK\n$reason"
                    }

                val audio =
                    json.optJSONObject(
                        "audio"
                    )

                hostAudioState =
                    if (
                        audio?.optBoolean(
                            "active",
                            false
                        ) ==
                        true
                    ) {
                        "Audio host: process loopback -> PCM 48k stereo"
                    } else {
                        "Audio host: " +
                            (
                                audio?.optString(
                                    "error",
                                    "inactive"
                                )
                                    ?: "inactive"
                            )
                    }

                val controller =
                    json.optJSONObject(
                        "controller"
                    )

                hostInputState =
                    if (
                        controller?.optBoolean(
                            "active",
                            false
                        ) ==
                        true
                    ) {
                        "Controller host: UDP -> ViGEm X360"
                    } else {
                        "Controller host: " +
                            (
                                controller?.optString(
                                    "error",
                                    "inactive"
                                )
                                    ?: "inactive"
                            )
                    }

                hostMetadataComplete =
                    true

                hostMetadataError =
                    ""

                runOnUiThread {
                    if (decoder == null) {
                        streamState =
                            "Host streaming; waiting for in-band SPS/PPS..."
                    }

                    updateMetrics()
                }

            } catch (error: Exception) {
                hostMetadataComplete =
                    false

                hostMetadataError =
                    (
                        error.message
                            ?: "Unknown error"
                    )

                runOnUiThread {
                    streamState =
                        "Host start response unavailable; " +
                            "stream receiver remains active: " +
                            hostMetadataError

                    updateMetrics()
                }
            }
        }
    }

    private fun stopLocalPipeline() {
        controllerSender?.stop()
        controllerSender = null

        audioReceiver?.stop()
        audioReceiver = null

        receiver?.stop()
        receiver = null

        decoder?.close()
        decoder = null
    }

    private fun stopSession() {
        if (stopping) {
            return
        }

        stopping = true

        val report =
            cacheSessionReport()

        sessionStarted = false

        stopLocalPipeline()

        val host =
            intent.getStringExtra(
                EXTRA_COMPANION_HOST
            )
                ?.trim()
                .orEmpty()

        if (host.isNotBlank()) {
            thread(
                start = true,
                isDaemon = true,
                name = "PrivyHub-Native-Stop"
            ) {
                if (
                    !report.isNullOrBlank()
                ) {
                    try {
                        val encoded =
                            URLEncoder.encode(
                                report,
                                "UTF-8"
                            )

                        httpPost(
                            "http://$host:$CONTROL_PORT" +
                                "/plugins/games/decoder-session-log" +
                                "?report=$encoded"
                        )
                    } catch (_: Exception) {
                        // Logging must never prevent the existing stop path.
                    }
                }

                try {
                    httpPost(
                        "http://$host:$CONTROL_PORT" +
                            "/plugins/games/native-stream-stop"
                    )
                } catch (_: Exception) {
                }
            }
        }
    }


    private fun cacheSessionReport():
        String? {
        val existing =
            cachedSessionReport

        if (!existing.isNullOrBlank()) {
            return existing
        }

        val report =
            buildSessionReport()

        if (report.isBlank()) {
            return null
        }

        cachedSessionReport = report
        return report
    }

    private fun buildSessionReport():
        String {
        val rtp =
            receiver?.snapshot()

        val dec =
            decoder?.snapshot()

        val audio =
            audioReceiver?.snapshot()

        val controller =
            controllerSender?.snapshot()

        if (
            rtp == null &&
            dec == null &&
            audio == null &&
            controller == null
        ) {
            return ""
        }

        val observedFec =
            (
                rtp?.fecParityPackets
                    ?: 0L
            ) >
                0L

        val reportFecEnabled =
            hostFecEnabled ||
                observedFec

        val reportFecGroupSize =
            if (
                hostFecGroupSize >
                0
            ) {
                hostFecGroupSize
            } else if (
                observedFec
            ) {
                8
            } else {
                0
            }

        val reportGopFrames =
            if (
                hostGopFrames >
                0
            ) {
                hostGopFrames
            } else if (
                observedFec
            ) {
                15
            } else {
                0
            }

        val reportBitrateKbps =
            if (
                hostVideoBitrateKbps >
                0
            ) {
                hostVideoBitrateKbps
            } else if (
                observedFec
            ) {
                7000
            } else {
                0
            }

        val nowNs =
            System.nanoTime()

        val durationMs =
            if (sessionStartedAtNs > 0L) {
                (
                    nowNs -
                        sessionStartedAtNs
                ).coerceAtLeast(0L) /
                    1_000_000L
            } else {
                0L
            }

        val root =
            JSONObject()

        root.put(
            "schema",
            "privyhub_native_decoder_session_v1"
        )
        root.put(
            "client_profiler_version",
            CLIENT_PROFILER_VERSION
        )
        root.put(
            "duration_ms",
            durationMs
        )
        root.put(
            "host_alpha",
            hostAlphaVersion
        )
        root.put(
            "encoder_gop_frames",
            reportGopFrames
        )
        root.put(
            "encoder_bitrate_kbps",
            reportBitrateKbps
        )
        root.put(
            "fec_enabled",
            reportFecEnabled
        )
        root.put(
            "fec_group_size",
            reportFecGroupSize
        )
        root.put(
            "host_metadata_complete",
            hostMetadataComplete
        )
        root.put(
            "host_metadata_error",
            hostMetadataError
        )
        root.put(
            "capture_backend",
            hostCaptureBackend
        )
        root.put(
            "capture_description",
            captureDescription
        )
        root.put(
            "paused_frame_capture_status",
            pausedFrameCaptureStatus
        )
        root.put(
            "paused_frame_bytes",
            pausedFrameBytes
        )
        root.put(
            "paused_frame_width",
            pausedFrameWidth
        )
        root.put(
            "paused_frame_height",
            pausedFrameHeight
        )

        if (rtp != null) {
            root.put(
                "video",
                JSONObject().apply {
                    put("packets", rtp.packets)
                    put("bytes", rtp.bytes)
                    put(
                        "lost_packets",
                        rtp.lostPackets
                    )
                    put("frames", rtp.frames)
                    put(
                        "dropped_frames",
                        rtp.droppedFrames
                    )
                    put(
                        "robust_missing_packets",
                        rtp.robustMissingPackets
                    )
                    put(
                        "forward_gap_events",
                        rtp.forwardGapEvents
                    )
                    put(
                        "late_or_reordered_packets",
                        rtp.lateOrReorderedPackets
                    )
                    put(
                        "duplicate_highest_packets",
                        rtp.duplicateHighestPackets
                    )
                    put(
                        "max_forward_gap_packets",
                        rtp.maxForwardGapPackets
                    )
                    put(
                        "sequence_gap_au_drops",
                        rtp.sequenceGapAccessUnitDrops
                    )
                    put(
                        "incomplete_au_drops",
                        rtp.incompleteAccessUnitDrops
                    )
                    put(
                        "fec_parity_packets",
                        rtp.fecParityPackets
                    )
                    put(
                        "fec_parity_bytes",
                        rtp.fecParityBytes
                    )
                    put(
                        "fec_groups_received",
                        rtp.fecGroupsReceived
                    )
                    put(
                        "fec_recovered_packets",
                        rtp.fecRecoveredPackets
                    )
                    put(
                        "fec_recovered_marker_packets",
                        rtp.fecRecoveredMarkerPackets
                    )
                    put(
                        "fec_recovered_idr_packets",
                        rtp.fecRecoveredIdrPackets
                    )
                    put(
                        "fec_gap_holds",
                        rtp.fecGapHolds
                    )
                    put(
                        "fec_hold_timeouts",
                        rtp.fecHoldTimeouts
                    )
                    put(
                        "fec_max_hold_ms",
                        rtp.fecMaxHoldMs
                    )
                    put(
                        "fec_max_held_packets",
                        rtp.fecMaxHeldPackets
                    )
                    put(
                        "fec_unrecoverable_groups",
                        rtp.fecUnrecoverableGroups
                    )
                    put(
                        "ssrc_changes",
                        rtp.ssrcChanges
                    )
                    put(
                        "sequence_resyncs",
                        rtp.sequenceResyncs
                    )
                    put(
                        "largest_resync_jump_packets",
                        rtp.largestResyncJumpPackets
                    )
                    put(
                        "packets_dropped_waiting_for_idr",
                        rtp.packetsDroppedWaitingForIdr
                    )
                    put(
                        "resync_to_idr_ms",
                        rtp.resyncToIdrMs
                    )
                    put(
                        "max_resync_to_idr_ms",
                        rtp.maxResyncToIdrMs
                    )
                    put(
                        "first_clean_idr_ms",
                        rtp.firstCleanIdrMs
                    )
                    put(
                        "waiting_for_idr",
                        rtp.waitingForIdr
                    )
                    put(
                        "idr_frames",
                        rtp.idrFrames
                    )
                    put(
                        "max_frames_between_idr",
                        rtp.maxFramesBetweenIdr
                    )
                    put(
                        "current_frames_since_idr",
                        rtp.currentFramesSinceIdr
                    )
                    put(
                        "recent_fps",
                        recentVideoFps
                    )
                    put(
                        "recent_mbps",
                        recentVideoMbps
                    )
                }
            )
        }

        if (dec != null) {
            root.put(
                "decoder",
                JSONObject().apply {
                    put(
                        "queued_frames",
                        dec.queuedFrames
                    )
                    put(
                        "rendered_frames",
                        dec.renderedFrames
                    )
                    put(
                        "dropped_frames",
                        dec.droppedFrames
                    )
                    put(
                        "queue_depth",
                        dec.queueDepth
                    )
                    put(
                        "max_queue_depth",
                        dec.maxQueueDepth
                    )
                    put(
                        "input_waits",
                        dec.inputWaits
                    )
                    put(
                        "queue_overflow_drops",
                        dec.queueOverflowDrops
                    )
                    put(
                        "stale_output_drops",
                        dec.staleOutputDrops
                    )
                    put(
                        "latest_feed_delay_ms",
                        dec.latestFeedDelayMs
                    )
                    put(
                        "max_feed_delay_ms",
                        dec.maxFeedDelayMs
                    )
                    put(
                        "latest_codec_ms",
                        dec.latestCodecMs
                    )
                    put(
                        "max_codec_ms",
                        dec.maxCodecMs
                    )
                    put(
                        "latest_rx_to_decode_ms",
                        dec.latestReceiveToDecodeMs
                    )
                    put(
                        "max_rx_to_decode_ms",
                        dec.maxReceiveToDecodeMs
                    )
                    put(
                        "timestamp_anomalies",
                        dec.timestampAnomalies
                    )
                    put(
                        "spike_20_ms",
                        dec.spike20ms
                    )
                    put(
                        "spike_50_ms",
                        dec.spike50ms
                    )
                    put(
                        "spike_80_ms",
                        dec.spike80ms
                    )
                    put(
                        "spike_250_ms",
                        dec.spike250ms
                    )
                    put(
                        "spike_500_ms",
                        dec.spike500ms
                    )
                    put(
                        "codec_in_flight",
                        dec.codecInFlight
                    )
                    put(
                        "max_codec_in_flight",
                        dec.maxCodecInFlight
                    )
                    put(
                        "latest_output_gap_ms",
                        dec.latestOutputGapMs
                    )
                    put(
                        "max_output_gap_ms",
                        dec.maxOutputGapMs
                    )
                    put(
                        "codec_name",
                        dec.codecName
                    )
                    put(
                        "hardware_accelerated",
                        dec.hardwareAccelerated
                    )
                    put(
                        "vendor_codec",
                        dec.vendorCodec
                    )
                    put(
                        "low_latency_enabled",
                        dec.lowLatencyEnabled
                    )
                }
            )

            val decoderEvents =
                decoder
                    ?.slowEventsSnapshot()
                    .orEmpty()

            val events =
                JSONArray()

            for (event in decoderEvents) {
                val elapsedMs =
                    if (sessionStartedAtNs > 0L) {
                        (
                            event.eventAtNs -
                                sessionStartedAtNs
                        ).coerceAtLeast(0L) /
                            1_000_000L
                    } else {
                        0L
                    }

                events.put(
                    JSONArray().apply {
                        put(elapsedMs)
                        put(
                            event.receiveToDecodeMs
                        )
                        put(
                            event.feedDelayMs
                        )
                        put(event.codecMs)
                        put(
                            event.codecInFlight
                        )
                        put(
                            event.appQueueDepth
                        )
                        put(
                            event.outputGapMs
                        )
                    }
                )
            }

            root.put(
                "slow_event_columns",
                JSONArray(
                    listOf(
                        "elapsed_ms",
                        "rx_to_decode_ms",
                        "feed_delay_ms",
                        "codec_ms",
                        "codec_in_flight",
                        "app_queue_depth",
                        "output_gap_ms"
                    )
                )
            )
            root.put(
                "slow_events_ge_50_ms",
                events
            )
            root.put(
                "slow_event_retained",
                decoderEvents.size
            )
            root.put(
                "slow_event_capacity",
                128
            )
        }

        if (audio != null) {
            root.put(
                "audio",
                JSONObject().apply {
                    put("packets", audio.packets)
                    put(
                        "lost_packets",
                        audio.lostPackets
                    )
                    put(
                        "pcm_bytes",
                        audio.pcmBytes
                    )
                    put(
                        "write_errors",
                        audio.writeErrors
                    )
                    put(
                        "stale_drops",
                        audio.staleDrops
                    )
                    put(
                        "queue_depth",
                        audio.queueDepth
                    )
                    put(
                        "max_queue_depth",
                        audio.maxQueueDepth
                    )
                    put(
                        "track_buffer_frames",
                        audio.trackBufferFrames
                    )
                    put(
                        "buffered_ms",
                        audio.bufferedMs
                    )
                    put(
                        "underruns",
                        audio.underruns
                    )
                    put(
                        "low_latency_mode",
                        audio.lowLatencyMode
                    )
                    put(
                        "concealed_loss_packets",
                        audio.concealedLossPackets
                    )
                    put(
                        "concealed_underruns",
                        audio.concealedUnderruns
                    )
                    put(
                        "prolonged_starvation_events",
                        audio.prolongedStarvationEvents
                    )
                    put(
                        "smooth_latency_trims",
                        audio.smoothLatencyTrims
                    )
                    put(
                        "crossfaded_packets",
                        audio.crossfadedPackets
                    )
                    put(
                        "max_queue_residence_ms",
                        audio.maxQueueResidenceMs
                    )
                    put(
                        "avg_queue_residence_ms",
                        audio.avgQueueResidenceMs
                    )
                    put(
                        "queue_target_packets",
                        audio.queueTargetPackets
                    )
                    put(
                        "queue_capacity_packets",
                        audio.queueCapacityPackets
                    )
                    put(
                        "startup_prefill_ms",
                        audio.startupPrefillMs
                    )
                }
            )
        }

        if (controller != null) {
            root.put(
                "controller",
                JSONObject().apply {
                    put(
                        "packets_sent",
                        controller.packetsSent
                    )
                    put(
                        "send_errors",
                        controller.sendErrors
                    )
                    put(
                        "motion_events",
                        controller.motionEvents
                    )
                }
            )
        }

        return root.toString()
    }


    private fun maybeSendClientHealth(
        nowNs: Long
    ) {
        if (
            !sessionStarted ||
            stopping ||
            clientHealthPostInFlight
        ) {
            return
        }

        if (
            lastClientHealthPostAtNs > 0L &&
            nowNs - lastClientHealthPostAtNs <
                CLIENT_HEALTH_INTERVAL_NS
        ) {
            return
        }

        val rtp =
            receiver?.snapshot()
                ?: return

        val dec =
            decoder?.snapshot()
                ?: return

        val host =
            intent.getStringExtra(
                EXTRA_COMPANION_HOST
            )
                ?.trim()
                .orEmpty()

        if (host.isBlank()) {
            return
        }

        val elapsedMs =
            if (sessionStartedAtNs > 0L) {
                (
                    nowNs -
                        sessionStartedAtNs
                ).coerceAtLeast(0L) /
                    1_000_000L
            } else {
                0L
            }

        clientHealthSequence +=
            1L

        val payload =
            JSONObject().apply {
                put(
                    "schema",
                    "privyhub_client_health_v1"
                )
                put(
                    "sequence",
                    clientHealthSequence
                )
                put(
                    "interval_ms",
                    CLIENT_HEALTH_INTERVAL_MS
                )
                put(
                    "session_elapsed_ms",
                    elapsedMs
                )
                put(
                    "video",
                    JSONObject().apply {
                        put("packets", rtp.packets)
                        put("lost_packets", rtp.lostPackets)
                        put("dropped_frames", rtp.droppedFrames)
                        put(
                            "fec_recovered_packets",
                            rtp.fecRecoveredPackets
                        )
                        put(
                            "fec_unrecoverable_groups",
                            rtp.fecUnrecoverableGroups
                        )
                        put(
                            "late_or_reordered_packets",
                            rtp.lateOrReorderedPackets
                        )
                        put(
                            "forward_gap_events",
                            rtp.forwardGapEvents
                        )
                        put("recent_fps", recentVideoFps)
                        put("recent_mbps", recentVideoMbps)
                        put("waiting_for_idr", rtp.waitingForIdr)
                    }
                )
                put(
                    "decoder",
                    JSONObject().apply {
                        put("queued_frames", dec.queuedFrames)
                        put("rendered_frames", dec.renderedFrames)
                        put("dropped_frames", dec.droppedFrames)
                        put("queue_depth", dec.queueDepth)
                        put(
                            "queue_overflow_drops",
                            dec.queueOverflowDrops
                        )
                        put(
                            "stale_output_drops",
                            dec.staleOutputDrops
                        )
                        put(
                            "latest_rx_to_decode_ms",
                            dec.latestReceiveToDecodeMs
                        )
                        put(
                            "latest_output_gap_ms",
                            dec.latestOutputGapMs
                        )
                        put(
                            "hardware_accelerated",
                            dec.hardwareAccelerated
                        )
                        put("vendor_codec", dec.vendorCodec)
                        put(
                            "low_latency_enabled",
                            dec.lowLatencyEnabled
                        )
                    }
                )
            }

        lastClientHealthPostAtNs =
            nowNs
        clientHealthPostInFlight =
            true

        thread(
            start = true,
            isDaemon = true,
            name = "PrivyHub-Client-Health"
        ) {
            try {
                httpPostJson(
                    "http://$host:$CONTROL_PORT" +
                        "/diagnostics/client-health",
                    payload
                )
            } catch (_: Exception) {
                // Diagnostic feedback must never disturb gameplay.
            } finally {
                clientHealthPostInFlight =
                    false
            }
        }
    }


    private fun updateMetrics() {
        val rtp =
            receiver?.snapshot()

        val dec =
            decoder?.snapshot()

        val nowNs =
            System.nanoTime()

        if (
            rtp != null &&
            lastMetricAtNs > 0L
        ) {
            val elapsed =
                (
                    nowNs -
                        lastMetricAtNs
                ).toDouble() /
                    1_000_000_000.0

            if (
                elapsed > 0.0
            ) {
                recentVideoMbps =
                    (
                        (
                            rtp.bytes -
                                lastRtpBytes
                        ) *
                            8.0
                    ) /
                        elapsed /
                        1_000_000.0

                recentVideoFps =
                    (
                        rtp.frames -
                            lastRtpFrames
                    ) /
                        elapsed
            }
        }

        if (rtp != null) {
            lastMetricAtNs =
                nowNs

            lastRtpBytes =
                rtp.bytes

            lastRtpFrames =
                rtp.frames
        }

        maybeSendClientHealth(
            nowNs
        )

        statusView.text =
            buildString {
                append(
                    "PrivyHub Native Audio Smoothing Alpha v0.12.2"
                )
                append(
                    "\nHost alpha: $hostAlphaVersion"
                )
                append(
                    "\nCapture backend: $hostCaptureBackend"
                )
                append(
                    "\nFEC: " +
                        if (hostFecEnabled) {
                            "XOR ${hostFecGroupSize}+1  " +
                                "${hostVideoBitrateKbps}kbps source"
                        } else {
                            "off"
                        }
                )
                append(
                    "\nResync: ${rtp?.sequenceResyncs ?: 0}" +
                        "  SSRC=${rtp?.ssrcChanges ?: 0}" +
                        "  waitIDR=${if (rtp?.waitingForIdr == true) "yes" else "no"}"
                )
                append(
                    "\nEncoder GOP: $hostGopFrames frames"
                )
                append(
                    "\n$streamState"
                )
                append(
                    "\n$captureDescription"
                )
                append(
                    "\nOutput: ${VIDEO_WIDTH}x${VIDEO_HEIGHT}@" +
                        "${VIDEO_FPS} H.264 RTP/UDP"
                )

                append(
                    "\n$hostAudioState"
                )
                append(
                    "\n$hostInputState"
                )

                val audio =
                    audioReceiver?.snapshot()

                if (audio != null) {
                    append(
                        "\nAudio packets: ${audio.packets}"
                    )
                    append(
                        "  Lost: ${audio.lostPackets}"
                    )
                    append(
                        "  Stale: ${audio.staleDrops}"
                    )
                    append(
                        "\nAudio queue: ${audio.queueDepth}" +
                            "  Max: ${audio.maxQueueDepth}"
                    )
                    append(
                        "  Track: ${audio.bufferedMs}ms"
                    )
                    append(
                        "\nAudio buffer frames: ${audio.trackBufferFrames}" +
                            "  Underruns: ${audio.underruns}" +
                            "  LL=${if (audio.lowLatencyMode) "yes" else "no"}"
                    )
                    append(
                        "  Write errors: ${audio.writeErrors}"
                    )
                    append(
                        "\nAudio smooth: conceal=${audio.concealedUnderruns}" +
                            " loss=${audio.concealedLossPackets}" +
                            " trims=${audio.smoothLatencyTrims}" +
                            " fades=${audio.crossfadedPackets}"
                    )
                    append(
                        String.format(
                            java.util.Locale.US,
                            "  Queue avg/max: %.1f/%dms",
                            audio.avgQueueResidenceMs,
                            audio.maxQueueResidenceMs
                        )
                    )
                }

                val controller =
                    controllerSender?.snapshot()

                if (controller != null) {
                    append(
                        "\nController sent: ${controller.packetsSent}"
                    )
                    append(
                        "  Errors: ${controller.sendErrors}"
                    )
                    append(
                        "  Motion: ${controller.motionEvents}"
                    )
                    append(
                        "\nL: ${controller.lx},${controller.ly}"
                    )
                    append(
                        "  R: ${controller.rx},${controller.ry}"
                    )
                    append(
                        "  Hat: ${controller.hatX},${controller.hatY}"
                    )
                }

                if (rtp == null) {
                    return@buildString
                }

                append(
                    "\nPackets: ${rtp.packets}"
                )
                append(
                    "  Lost: ${rtp.lostPackets}"
                )
                append(
                    String.format(
                        java.util.Locale.US,
                        "\nVideo RX: %.1f fps  %.2f Mb/s",
                        recentVideoFps,
                        recentVideoMbps
                    )
                )
                append(
                    "\nCodec config: SPS=${if (rtp.hasSps) "yes" else "no"}" +
                        " PPS=${if (rtp.hasPps) "yes" else "no"}"
                )
                append(
                    "\nFrames: ${rtp.frames}"
                )
                append(
                    "  RTP dropped: ${rtp.droppedFrames}"
                )

                if (dec != null) {
                    append(
                        "\nRendered: ${dec.renderedFrames}"
                    )
                    append(
                        "  Decode dropped: ${dec.droppedFrames}"
                    )
                    append(
                        "\nApp queue: ${dec.queueDepth}" +
                            "  Max: ${dec.maxQueueDepth}" +
                            "  OverflowDrops: ${dec.queueOverflowDrops}"
                    )
                    append(
                        "  Stale: ${dec.staleOutputDrops}"
                    )
                    append(
                        "\nFeed: ${dec.latestFeedDelayMs}ms" +
                            "  Max: ${dec.maxFeedDelayMs}ms"
                    )
                    append(
                        "\nCodec: ${dec.latestCodecMs}ms" +
                            "  Max: ${dec.maxCodecMs}ms" +
                            "  InFlight: ${dec.codecInFlight}" +
                            "  MaxIF: ${dec.maxCodecInFlight}"
                    )
                    append(
                        "\nRX->decode: ${dec.latestReceiveToDecodeMs}ms" +
                            "  Max: ${dec.maxReceiveToDecodeMs}ms" +
                            "  PTSbad=${dec.timestampAnomalies}"
                    )
                    append(
                        "\nSpikes 20/50/80/250/500: " +
                            "${dec.spike20ms}/" +
                            "${dec.spike50ms}/" +
                            "${dec.spike80ms}/" +
                            "${dec.spike250ms}/" +
                            "${dec.spike500ms}"
                    )
                    append(
                        "\nOutput gap: ${dec.latestOutputGapMs}ms" +
                            "  Max: ${dec.maxOutputGapMs}ms"
                    )
                    append(
                        "\nDecoder: ${dec.codecName}" +
                            " HW=${if (dec.hardwareAccelerated) "yes" else "no"}" +
                            " Vendor=${if (dec.vendorCodec) "yes" else "no"}" +
                            " LL=${if (dec.lowLatencyEnabled) "yes" else "no"}"
                    )
                }
            }
    }

    // PrivyHub A3 patch 11v2: capture before stream teardown.
    private fun finishAfterPausedFrameCapture() {

        if (!isFinishing) {
            super.onBackPressed()
        }
    }


    private fun persistPausedFrame(
        source: Bitmap
    ): Long {

        val title =
            intent.getStringExtra(
                EXTRA_GAME_TITLE
            )
                ?.trim()
                .orEmpty()

        if (title.isBlank()) {
            throw IllegalStateException(
                "Game title is unavailable for paused-frame storage"
            )
        }

        val target =
            File(
                cacheDir,
                pausedFrameFileName(
                    title
                )
            )

        val temporary =
            File(
                cacheDir,
                target.name + ".tmp"
            )

        val preview =
            Bitmap.createScaledBitmap(
                source,
                480,
                270,
                true
            )

        try {
            FileOutputStream(
                temporary
            ).use { output ->

                val compressed =
                    preview.compress(
                        Bitmap.CompressFormat.JPEG,
                        88,
                        output
                    )

                if (!compressed) {
                    throw IllegalStateException(
                        "Bitmap compression failed"
                    )
                }

                output.fd.sync()
            }

            if (
                target.exists() &&
                !target.delete()
            ) {
                throw IllegalStateException(
                    "Unable to replace previous paused frame"
                )
            }

            if (
                !temporary.renameTo(
                    target
                )
            ) {
                temporary.copyTo(
                    target,
                    overwrite = true
                )
                temporary.delete()
            }

            val size =
                target.length()

            if (size <= 0L) {
                throw IllegalStateException(
                    "Paused-frame output was empty"
                )
            }

            pausedFrameWidth =
                preview.width

            pausedFrameHeight =
                preview.height

            return size

        } finally {
            if (
                preview !==
                source
            ) {
                preview.recycle()
            }

            source.recycle()

            try {
                if (temporary.exists()) {
                    temporary.delete()
                }
            } catch (_: Exception) {
            }
        }
    }


    private fun capturePausedFrameAndFinish() {

        if (backExitInProgress) {
            return
        }

        backExitInProgress =
            true

        pausedFrameCaptureStatus =
            "requested"

        if (
            Build.VERSION.SDK_INT <
            Build.VERSION_CODES.N
        ) {
            pausedFrameCaptureStatus =
                "unsupported_api"

            finishAfterPausedFrameCapture()
            return
        }

        val width =
            surfaceView.width

        val height =
            surfaceView.height

        if (
            width <= 0 ||
            height <= 0 ||
            !surfaceView.holder.surface.isValid
        ) {
            pausedFrameCaptureStatus =
                "surface_unavailable"

            finishAfterPausedFrameCapture()
            return
        }

        val bitmap =
            try {
                Bitmap.createBitmap(
                    width,
                    height,
                    Bitmap.Config.ARGB_8888
                )
            } catch (_: Exception) {
                pausedFrameCaptureStatus =
                    "bitmap_allocation_failed"

                finishAfterPausedFrameCapture()
                return
            }

        pausedFrameCaptureStatus =
            "pixelcopy_pending"

        PixelCopy.request(
            surfaceView,
            bitmap,
            { result ->

                if (
                    result !=
                    PixelCopy.SUCCESS
                ) {
                    pausedFrameCaptureStatus =
                        "pixelcopy_error_$result"

                    bitmap.recycle()

                    finishAfterPausedFrameCapture()
                    return@request
                }

                pausedFrameCaptureStatus =
                    "pixelcopy_complete"

                thread(
                    start = true,
                    isDaemon = true,
                    name = "PrivyHub-Paused-Frame"
                ) {
                    try {
                        pausedFrameBytes =
                            persistPausedFrame(
                                bitmap
                            )

                        pausedFrameCaptureStatus =
                            "saved"

                    } catch (error: Exception) {
                        pausedFrameBytes =
                            0L

                        pausedFrameCaptureStatus =
                            "write_error_" +
                                error.javaClass.simpleName

                        if (!bitmap.isRecycled) {
                            bitmap.recycle()
                        }
                    }

                    uiHandler.post {
                        finishAfterPausedFrameCapture()
                    }
                }
            },
            uiHandler
        )
    }


    override fun dispatchKeyEvent(
        event: KeyEvent
    ): Boolean {

        if (
            event.keyCode ==
            KeyEvent.KEYCODE_BACK
        ) {
            if (
                event.action ==
                KeyEvent.ACTION_UP
            ) {
                capturePausedFrameAndFinish()
            }

            return true
        }

        if (
            controllerSender?.handleKeyEvent(
                event
            ) ==
            true
        ) {
            return true
        }

        return super.dispatchKeyEvent(
            event
        )
    }

    override fun dispatchGenericMotionEvent(
        event: MotionEvent
    ): Boolean {
        if (
            controllerSender?.handleMotionEvent(
                event
            ) ==
            true
        ) {
            return true
        }

        return super.dispatchGenericMotionEvent(
            event
        )
    }


    private fun httpPostJson(
        address: String,
        payload: JSONObject
    ) {
        val body =
            payload.toString()
                .toByteArray(
                    Charsets.UTF_8
                )

        val connection =
            (
                URL(address).openConnection()
                    as HttpURLConnection
                ).apply {
                    requestMethod = "POST"
                    connectTimeout = 1_500
                    readTimeout = 1_500
                    doInput = true
                    doOutput = true
                    setRequestProperty(
                        "Content-Type",
                        "application/json"
                    )
                    setFixedLengthStreamingMode(
                        body.size
                    )
                }

        try {
            connection.outputStream.use {
                it.write(body)
            }

            val code =
                connection.responseCode

            val stream =
                if (code in 200..299) {
                    connection.inputStream
                } else {
                    connection.errorStream
                }

            stream?.close()

            if (code !in 200..299) {
                throw IllegalStateException(
                    "HTTP $code"
                )
            }
        } finally {
            connection.disconnect()
        }
    }


    private fun httpPost(
        address: String,
        readTimeoutMs: Int =
            10_000
    ): String {
        val connection =
            (
                URL(
                    address
                ).openConnection()
                    as HttpURLConnection
                ).apply {
                    requestMethod =
                        "POST"
                    connectTimeout =
                        5_000
                    readTimeout =
                        readTimeoutMs
                    doInput =
                        true
                }

        try {
            val code =
                connection.responseCode

            val stream =
                if (
                    code in
                    200..299
                ) {
                    connection.inputStream
                } else {
                    connection.errorStream
                }

            val body =
                stream
                    ?.bufferedReader()
                    ?.use {
                        it.readText()
                    }
                    .orEmpty()

            if (
                code !in
                200..299
            ) {
                val message =
                    try {
                        JSONObject(
                            body
                        ).optString(
                            "error",
                            body
                        )
                    } catch (_: Exception) {
                        body
                    }

                throw IllegalStateException(
                    message.ifBlank {
                        "HTTP $code"
                    }
                )
            }

            return body

        } finally {
            connection.disconnect()
        }
    }
}
