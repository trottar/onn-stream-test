package com.safeiot.privyhub.diagnostics

import android.content.res.ColorStateList
import android.graphics.Color
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.StateListDrawable
import android.os.Bundle
import android.view.Gravity
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

import androidx.appcompat.app.AppCompatActivity

import org.json.JSONArray
import org.json.JSONObject

import java.net.HttpURLConnection
import java.net.URL
import java.util.Locale
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors


class DiagnosticsActivity : AppCompatActivity() {

    companion object {
        const val EXTRA_COMPANION_HOST =
            "companion_host"

        private const val CONTROL_PORT =
            8765

        private const val CONNECT_TIMEOUT_MS =
            3_000

        private const val READ_TIMEOUT_MS =
            3_000

        private const val SELF_TEST_READ_TIMEOUT_MS =
            8_000

        private const val BUNDLE_READ_TIMEOUT_MS =
            60_000

        private const val HEALTH_SCHEMA =
            "privyhub_diagnostics_health_v1"

        private const val SELF_TEST_SCHEMA =
            "privyhub_diagnostics_self_test_v1"

        private const val BUNDLE_SCHEMA =
            "privyhub_support_bundle_result_v1"

        // PRIVYHUB_B1_DIAGNOSTICS_ACTIVITY_V1
        // PRIVYHUB_B1_B2_COMPLETION_UI_V1
        private const val UI_VERSION =
            "B1.13"
    }


    private val networkExecutor: ExecutorService =
        Executors.newSingleThreadExecutor()

    @Volatile
    private var destroyed =
        false

    private lateinit var statusView:
        TextView

    private lateinit var detailView:
        TextView

    private lateinit var refreshButton:
        Button

    private lateinit var selfTestButton:
        Button

    private lateinit var collectButton:
        Button


    override fun onCreate(
        savedInstanceState: Bundle?
    ) {
        super.onCreate(
            savedInstanceState
        )

        setContentView(
            buildContent()
        )

        refreshButton.setOnClickListener {
            refreshHealth(
                selfTest = false
            )
        }

        selfTestButton.setOnClickListener {
            refreshHealth(
                selfTest = true
            )
        }

        collectButton.setOnClickListener {
            collectDiagnostics()
        }

        refreshHealth(
            selfTest = false
        )
    }


    override fun onDestroy() {
        destroyed =
            true

        networkExecutor.shutdownNow()

        super.onDestroy()
    }


    private fun buildContent(): ScrollView {

        val scroll =
            ScrollView(this).apply {
                setBackgroundColor(
                    Color.rgb(
                        16,
                        16,
                        16
                    )
                )
                isFillViewport =
                    true
            }

        val content =
            LinearLayout(this).apply {
                orientation =
                    LinearLayout.VERTICAL

                val padding =
                    dp(24)

                setPadding(
                    padding,
                    padding,
                    padding,
                    padding
                )
            }

        val title =
            TextView(this).apply {
                text =
                    "PrivyHub Diagnostics"

                textSize =
                    26f

                setTextColor(
                    Color.WHITE
                )

                gravity =
                    Gravity.START

                setPadding(
                    0,
                    0,
                    0,
                    dp(12)
                )
            }

        statusView =
            TextView(this).apply {
                text =
                    "Loading health snapshot..."

                textSize =
                    17f

                setTextColor(
                    Color.WHITE
                )

                setPadding(
                    0,
                    0,
                    0,
                    dp(14)
                )
            }

        val actions =
            LinearLayout(this).apply {
                orientation =
                    LinearLayout.HORIZONTAL
            }

        refreshButton =
            diagnosticButton(
                "REFRESH"
            )

        selfTestButton =
            diagnosticButton(
                "RUN SELF-TEST"
            )

        collectButton =
            diagnosticButton(
                "COLLECT DIAGNOSTICS"
            )

        val closeButton =
            diagnosticButton(
                "CLOSE"
            )

        actions.addView(
            refreshButton,
            weightedButtonParams()
        )

        actions.addView(
            selfTestButton,
            weightedButtonParams()
        )

        actions.addView(
            collectButton,
            weightedButtonParams()
        )

        actions.addView(
            closeButton,
            weightedButtonParams()
        )

        closeButton.setOnClickListener {
            finish()
        }

        detailView =
            TextView(this).apply {
                text =
                    "Waiting for health data."

                textSize =
                    15f

                setTextColor(
                    Color.WHITE
                )

                setTextIsSelectable(
                    true
                )

                setPadding(
                    0,
                    dp(18),
                    0,
                    dp(24)
                )
            }

        content.addView(
            title,
            ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
        )

        content.addView(
            statusView,
            ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
        )

        content.addView(
            actions,
            ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
        )

        content.addView(
            detailView,
            ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
        )

        scroll.addView(
            content,
            ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
        )

        return scroll
    }


    private fun diagnosticButton(
        label: String
    ): Button {

        val states =
            arrayOf(
                intArrayOf(
                    android.R.attr.state_pressed
                ),
                intArrayOf(
                    android.R.attr.state_focused
                ),
                intArrayOf()
            )

        val backgrounds =
            intArrayOf(
                Color.CYAN,
                Color.LTGRAY,
                Color.rgb(
                    48,
                    48,
                    48
                )
            )

        val textColors =
            intArrayOf(
                Color.BLACK,
                Color.BLACK,
                Color.WHITE
            )

        val background =
            StateListDrawable().apply {
                for (
                    index
                    in states.indices
                ) {
                    addState(
                        states[index],
                        ColorDrawable(
                            backgrounds[index]
                        )
                    )
                }
            }

        return Button(this).apply {
            text =
                label

            textSize =
                14f

            isAllCaps =
                false

            isFocusable =
                true

            this.background =
                background

            setTextColor(
                ColorStateList(
                    states,
                    textColors
                )
            )

            setPadding(
                dp(10),
                dp(10),
                dp(10),
                dp(10)
            )
        }
    }


    private fun weightedButtonParams(): LinearLayout.LayoutParams {

        return LinearLayout.LayoutParams(
            0,
            ViewGroup.LayoutParams.WRAP_CONTENT,
            1f
        ).apply {
            marginEnd =
                dp(8)
        }
    }


    private fun refreshHealth(
        selfTest: Boolean
    ) {

        val host =
            intent.getStringExtra(
                EXTRA_COMPANION_HOST
            )
                ?.trim()
                .orEmpty()

        if (host.isBlank()) {
            statusView.text =
                "Companion host is not configured."

            detailView.text =
                "Return to PrivyHub Settings and save the companion host first."

            return
        }

        setBusy(
            true,
            if (selfTest) {
                "Running self-test..."
            } else {
                "Refreshing diagnostics..."
            },
            if (selfTest) {
                "self_test"
            } else {
                "refresh"
            }
        )

        networkExecutor.execute {

            try {
                val result =
                    if (selfTest) {
                        fetchSelfTest(
                            host
                        )
                    } else {
                        fetchHealth(
                            host
                        )
                    }

                val detail =
                    if (selfTest) {
                        formatSelfTest(
                            result
                        )
                    } else {
                        formatHealth(
                            result
                        )
                    }

                val headline =
                    formatHeadline(
                        result,
                        selfTest
                    )

                if (!destroyed) {
                    runOnUiThread {
                        setBusy(
                            false,
                            headline
                        )

                        detailView.text =
                            detail
                    }
                }

            } catch (
                error: Exception
            ) {

                if (!destroyed) {
                    runOnUiThread {
                        setBusy(
                            false,
                            "Diagnostics unavailable"
                        )

                        detailView.text =
                            "Unable to read the PrivyHub health endpoint.\n" +
                                "Error class: " +
                                error.javaClass.simpleName +
                                "\n\nNo network address was written to the diagnostic UI."
                    }
                }
            }
        }
    }


    private fun setBusy(
        busy: Boolean,
        message: String,
        activeAction: String? = null
    ) {

        // PRIVYHUB_B2_GUI_ACTION_FEEDBACK_V1
        refreshButton.text =
            if (
                busy
                && activeAction == "refresh"
            ) {
                "REFRESHING..."
            } else {
                "REFRESH"
            }

        selfTestButton.text =
            if (
                busy
                && activeAction == "self_test"
            ) {
                "RUNNING..."
            } else {
                "RUN SELF-TEST"
            }

        collectButton.text =
            if (
                busy
                && activeAction == "collect"
            ) {
                "COLLECTING..."
            } else {
                "COLLECT DIAGNOSTICS"
            }

        refreshButton.isEnabled =
            !busy

        selfTestButton.isEnabled =
            !busy

        collectButton.isEnabled =
            !busy

        statusView.text =
            message
    }


    private fun companionHost(): String {

        return intent.getStringExtra(
            EXTRA_COMPANION_HOST
        )
            ?.trim()
            .orEmpty()
    }


    private fun requestJson(
        host: String,
        path: String,
        method: String,
        readTimeoutMs: Int
    ): JSONObject {

        val connection =
            (
                URL(
                    "http://$host:$CONTROL_PORT" +
                        path
                )
                    .openConnection()
                    as HttpURLConnection
                ).apply {

                requestMethod =
                    method

                connectTimeout =
                    CONNECT_TIMEOUT_MS

                readTimeout =
                    readTimeoutMs

                useCaches =
                    false

                setRequestProperty(
                    "Cache-Control",
                    "no-cache"
                )

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
                throw IllegalStateException(
                    "Diagnostics endpoint HTTP status was not successful"
                )
            }

            return JSONObject(
                body
            )

        } finally {
            connection.disconnect()
        }
    }


    private fun fetchHealth(
        host: String
    ): JSONObject {

        return requestJson(
            host,
            "/diagnostics/health",
            "GET",
            READ_TIMEOUT_MS
        )
    }


    private fun fetchSelfTest(
        host: String
    ): JSONObject {

        val result =
            requestJson(
                host,
                "/diagnostics/self-test",
                "POST",
                SELF_TEST_READ_TIMEOUT_MS
            )

        if (
            result.optString(
                "schema",
                ""
            )
            != SELF_TEST_SCHEMA
        ) {
            throw IllegalStateException(
                "Self-test schema was not recognized"
            )
        }

        return result
    }


    private fun collectDiagnostics() {

        val host =
            companionHost()

        if (host.isBlank()) {
            statusView.text =
                "Companion host is not configured."

            detailView.text =
                "Return to PrivyHub Settings and save the companion host first."

            return
        }

        setBusy(
            true,
            "Collecting sanitized diagnostics...",
            "collect"
        )

        networkExecutor.execute {

            try {
                val result =
                    requestJson(
                        host,
                        "/diagnostics/bundle",
                        "POST",
                        BUNDLE_READ_TIMEOUT_MS
                    )

                if (
                    result.optString(
                        "schema",
                        ""
                    )
                    != BUNDLE_SCHEMA
                ) {
                    throw IllegalStateException(
                        "Bundle response schema was not recognized"
                    )
                }

                val filename =
                    result.optString(
                        "filename",
                        "SHARE_ME.zip"
                    )

                val relativePath =
                    result.optString(
                        "relative_path",
                        ""
                    )

                val sizeBytes =
                    result.optLong(
                        "size_bytes",
                        0L
                    )

                val sha256 =
                    result.optString(
                        "sha256",
                        ""
                    )

                if (!destroyed) {
                    runOnUiThread {
                        setBusy(
                            false,
                            "Diagnostics bundle created"
                        )

                        detailView.text =
                            buildString {
                                append(
                                    "SANITIZED SUPPORT BUNDLE\n\n"
                                )
                                append(
                                    "File: "
                                )
                                append(
                                    filename
                                )
                                append(
                                    "\nLocation on companion: "
                                )
                                append(
                                    relativePath
                                )
                                append(
                                    "\nSize: "
                                )
                                append(
                                    sizeBytes
                                )
                                append(
                                    " bytes"
                                )
                                append(
                                    "\nSHA-256: "
                                )
                                append(
                                    sha256
                                )
                                append(
                                    "\n\nOnly SHARE_ME.zip should be shared for support."
                                )
                            }
                    }
                }

            } catch (
                error: Exception
            ) {

                if (!destroyed) {
                    runOnUiThread {
                        setBusy(
                            false,
                            "Diagnostics bundle failed"
                        )

                        detailView.text =
                            "Unable to create the sanitized diagnostics bundle.\n" +
                                "Error class: " +
                                error.javaClass.simpleName +
                                "\n\nNo network address was written to the diagnostic UI."
                    }
                }
            }
        }
    }


    private fun formatHeadline(
        root: JSONObject,
        selfTest: Boolean
    ): String {

        if (selfTest) {
            val status =
                root.optJSONObject(
                    "overall"
                )
                    ?.optString(
                        "status",
                        "unknown"
                    )
                    ?: "unknown"

            return "Self-test: " +
                status.uppercase(
                    Locale.US
                )
        }

        val overall =
            root.optJSONObject(
                "overall"
            )

        val health =
            overall
                ?.optString(
                    "health",
                    "unknown"
                )
                ?: "unknown"

        return "Overall: " +
            health.uppercase(
                Locale.US
            )
    }


    private fun formatHealth(
        root: JSONObject
    ): String {

        val schema =
            root.optString(
                "schema",
                "<missing>"
            )

        val overall =
            root.optJSONObject(
                "overall"
            )

        val resources =
            root.optJSONObject(
                "resources"
            )

        val collection =
            root.optJSONObject(
                "collection"
            )

        val session =
            root.optJSONObject(
                "session"
            )

        return buildString {

            append(
                "Diagnostics UI "
            )
            append(
                UI_VERSION
            )

            append(
                "\nHealth schema: "
            )
            append(
                schema
            )

            append(
                "\nOverall: "
            )
            append(
                overall
                    ?.optString(
                        "health",
                        "unknown"
                    )
                    ?: "unknown"
            )

            append(
                " / "
            )
            append(
                overall
                    ?.optString(
                        "severity",
                        "unknown"
                    )
                    ?: "unknown"
            )

            append(
                "\nEvent: "
            )
            append(
                overall
                    ?.optString(
                        "event_code",
                        "<none>"
                    )
                    ?: "<none>"
            )

            append(
                "\nGame active: "
            )
            append(
                session
                    ?.optBoolean(
                        "game_active",
                        false
                    )
                    ?: false
            )

            append(
                "\nNative stream active: "
            )
            append(
                session
                    ?.optBoolean(
                        "native_stream_active",
                        false
                    )
                    ?: false
            )

            append(
                "\n\nCOMPONENTS\n"
            )

            val components =
                root.optJSONArray(
                    "components"
                )
                    ?: JSONArray()

            for (
                index
                in 0
                until components.length()
            ) {

                val item =
                    components.optJSONObject(
                        index
                    )
                        ?: continue

                appendComponent(
                    this,
                    item
                )
            }

            append(
                "\nRESOURCES\n"
            )

            append(
                "Availability: "
            )
            append(
                resources
                    ?.optString(
                        "availability",
                        "unknown"
                    )
                    ?: "unknown"
            )

            append(
                "\nScope: "
            )
            append(
                resources
                    ?.optString(
                        "measurement_scope",
                        "none"
                    )
                    ?: "none"
            )

            val sampling =
                resources
                    ?.optJSONObject(
                        "sampling"
                    )

            append(
                "\nSampling active: "
            )
            append(
                sampling
                    ?.optBoolean(
                        "active",
                        false
                    )
                    ?: false
            )

            append(
                "\nSamples: "
            )
            append(
                sampling
                    ?.optInt(
                        "sample_count",
                        0
                    )
                    ?: 0
            )

            append(
                "\nInterval: "
            )
            append(
                sampling
                    ?.optDouble(
                        "sample_interval_seconds",
                        0.0
                    )
                    ?: 0.0
            )
            append(
                " s"
            )

            val optimization =
                resources
                    ?.optJSONObject(
                        "optimization"
                    )

            append(
                "\nCapacity class: "
            )
            append(
                optimization
                    ?.optString(
                        "capacity_classification",
                        "unclassified"
                    )
                    ?: "unclassified"
            )

            append(
                "\nStream profile fit: "
            )
            append(
                optimization
                    ?.optString(
                        "stream_profile_fit",
                        "unclassified"
                    )
                    ?: "unclassified"
            )

            append(
                "\nBenchmark thresholds applied: "
            )
            append(
                optimization
                    ?.optBoolean(
                        "benchmark_thresholds_applied",
                        false
                    )
                    ?: false
            )

            append(
                "\n\nCLIENT FEEDBACK\n"
            )

            append(
                "Available: "
            )
            append(
                collection
                    ?.optBoolean(
                        "client_feedback_available",
                        false
                    )
                    ?: false
            )

            append(
                "\nFresh: "
            )
            append(
                collection
                    ?.optBoolean(
                        "client_feedback_fresh",
                        false
                    )
                    ?: false
            )

            append(
                "\nPayload bytes: "
            )
            append(
                collection
                    ?.optInt(
                        "client_feedback_payload_bytes",
                        0
                    )
                    ?: 0
            )

            append(
                "\nNew resource sampler: "
            )
            append(
                collection
                    ?.optBoolean(
                        "new_resource_sampler_started",
                        false
                    )
                    ?: false
            )

            appendEventHistory(
                this,
                root
            )
        }
    }


    private fun appendEventHistory(
        output: StringBuilder,
        root: JSONObject
    ) {

        val history =
            root.optJSONObject(
                "event_history"
            )
                ?: return

        val events =
            history.optJSONArray(
                "events"
            )
                ?: return

        output.append(
            "\n\nRECENT EVENTS"
        )

        output.append(
            "\nBounded: "
        )

        output.append(
            history.optBoolean(
                "bounded",
                false
            )
        )

        output.append(
            " / "
        )

        output.append(
            history.optInt(
                "count",
                0
            )
        )

        output.append(
            " of "
        )

        output.append(
            history.optInt(
                "capacity",
                0
            )
        )

        val start =
            maxOf(
                0,
                events.length() - 10
            )

        for (
            index
            in start
            until events.length()
        ) {
            val item =
                events.optJSONObject(
                    index
                )
                    ?: continue

            output.append(
                "\n"
            )

            output.append(
                item.optString(
                    "component",
                    "unknown"
                )
            )

            output.append(
                ": "
            )

            output.append(
                item.optString(
                    "event_code",
                    "<none>"
                )
            )

            output.append(
                " / "
            )

            output.append(
                item.optString(
                    "event_kind",
                    "event"
                )
            )
        }
    }


    private fun appendComponent(
        output: StringBuilder,
        item: JSONObject
    ) {

        val component =
            item.optString(
                "component",
                "unknown"
            )

        val health =
            item.optString(
                "health",
                "unknown"
            )

        val severity =
            item.optString(
                "severity",
                "info"
            )

        val event =
            item.optString(
                "event_code",
                "<none>"
            )

        output.append(
            "\n"
        )

        output.append(
            component
        )

        output.append(
            ": "
        )

        output.append(
            health.uppercase(
                Locale.US
            )
        )

        output.append(
            " / "
        )

        output.append(
            severity
        )

        output.append(
            "\n  "
        )

        output.append(
            event
        )

        val measurements =
            item.optJSONObject(
                "measurements"
            )
                ?: return

        when (
            component
        ) {

            "end_to_end_path" -> {

                appendMeasurement(
                    output,
                    measurements,
                    "recent_fps",
                    "Receive FPS"
                )

                appendMeasurement(
                    output,
                    measurements,
                    "recent_mbps",
                    "Receive Mbps"
                )

                appendMeasurement(
                    output,
                    measurements,
                    "delta_fec_recovered_packets",
                    "FEC recovered delta"
                )

                appendMeasurement(
                    output,
                    measurements,
                    "delta_fec_unrecoverable_groups",
                    "FEC unrecoverable delta"
                )
            }

            "decoder" -> {

                appendMeasurement(
                    output,
                    measurements,
                    "hardware_accelerated",
                    "Hardware decode"
                )

                appendMeasurement(
                    output,
                    measurements,
                    "delta_rendered_frames",
                    "Rendered delta"
                )

                appendMeasurement(
                    output,
                    measurements,
                    "delta_stale_output_drops",
                    "Stale shedding delta"
                )

                appendMeasurement(
                    output,
                    measurements,
                    "delta_dropped_frames",
                    "Decoder drops delta"
                )

                appendMeasurement(
                    output,
                    measurements,
                    "delta_queue_overflow_drops",
                    "Queue overflow delta"
                )

                appendMeasurement(
                    output,
                    measurements,
                    "queue_depth",
                    "Queue depth"
                )

                appendMeasurement(
                    output,
                    measurements,
                    "latest_rx_to_decode_ms",
                    "RX-to-decode ms"
                )

                appendMeasurement(
                    output,
                    measurements,
                    "latest_output_gap_ms",
                    "Output gap ms"
                )
            }
        }
    }


    private fun appendMeasurement(
        output: StringBuilder,
        objectValue: JSONObject,
        key: String,
        label: String
    ) {

        if (!objectValue.has(key)) {
            return
        }

        val value =
            objectValue.opt(
                key
            )

        if (
            value == null ||
            value == JSONObject.NULL
        ) {
            return
        }

        output.append(
            "\n    "
        )

        output.append(
            label
        )

        output.append(
            ": "
        )

        output.append(
            value.toString()
        )
    }


    private fun formatSelfTest(
        root: JSONObject
    ): String {

        val healthRoot =
            root.optJSONObject(
                "health"
            )
                ?: root

        var failures =
            0

        var warnings =
            0

        val lines =
            mutableListOf<String>()

        fun check(
            label: String,
            status: String,
            detail: String
        ) {

            lines.add(
                "$status  $label" +
                    if (
                        detail.isBlank()
                    ) {
                        ""
                    } else {
                        " — $detail"
                    }
            )

            if (
                status == "FAIL"
            ) {
                failures++
            } else if (
                status == "WARN"
            ) {
                warnings++
            }
        }

        val schema =
            healthRoot.optString(
                "schema",
                ""
            )

        check(
            "Health contract",
            if (
                schema ==
                HEALTH_SCHEMA
            ) {
                "PASS"
            } else {
                "FAIL"
            },
            schema.ifBlank {
                "missing"
            }
        )

        val components =
            healthRoot.optJSONArray(
                "components"
            )
                ?: JSONArray()

        check(
            "Component model",
            if (
                components.length() >=
                11
            ) {
                "PASS"
            } else {
                "FAIL"
            },
            "${components.length()} components"
        )

        for (
            index
            in 0
            until components.length()
        ) {

            val item =
                components.optJSONObject(
                    index
                )
                    ?: continue

            val severity =
                item.optString(
                    "severity",
                    "info"
                )

            val status =
                when (
                    severity
                ) {
                    "error" ->
                        "FAIL"

                    "warning" ->
                        "WARN"

                    else ->
                        "PASS"
                }

            check(
                item.optString(
                    "component",
                    "unknown"
                ),
                status,
                item.optString(
                    "event_code",
                    "<none>"
                )
            )
        }

        val collection =
            healthRoot.optJSONObject(
                "collection"
            )

        val newSampler =
            collection
                ?.optBoolean(
                    "new_resource_sampler_started",
                    true
                )
                ?: true

        check(
            "Resource sampling contract",
            if (!newSampler) {
                "PASS"
            } else {
                "FAIL"
            },
            if (!newSampler) {
                "existing telemetry only"
            } else {
                "unexpected sampler reported"
            }
        )

        val resources =
            healthRoot.optJSONObject(
                "resources"
            )

        val optimization =
            resources
                ?.optJSONObject(
                    "optimization"
                )

        val thresholds =
            optimization
                ?.optBoolean(
                    "benchmark_thresholds_applied",
                    true
                )
                ?: true

        check(
            "Benchmark threshold guard",
            if (!thresholds) {
                "PASS"
            } else {
                "FAIL"
            },
            if (!thresholds) {
                "Phase E thresholds not applied"
            } else {
                "unexpected thresholds active"
            }
        )

        val session =
            healthRoot.optJSONObject(
                "session"
            )

        val streamActive =
            session
                ?.optBoolean(
                    "native_stream_active",
                    false
                )
                ?: false

        if (streamActive) {

            val feedbackFresh =
                collection
                    ?.optBoolean(
                        "client_feedback_fresh",
                        false
                    )
                    ?: false

            check(
                "Live client feedback",
                if (feedbackFresh) {
                    "PASS"
                } else {
                    "WARN"
                },
                if (feedbackFresh) {
                    "fresh"
                } else {
                    "active stream has no fresh client feedback"
                }
            )

        } else {

            check(
                "Live client feedback",
                "PASS",
                "not required while stream is idle"
            )
        }

        val dedicatedChecks =
            root.optJSONArray(
                "checks"
            )
                ?: JSONArray()

        for (
            index
            in 0
            until dedicatedChecks.length()
        ) {
            val item =
                dedicatedChecks.optJSONObject(
                    index
                )
                    ?: continue

            check(
                item.optString(
                    "check_id",
                    "dedicated_check"
                ),
                item.optString(
                    "status",
                    "WARN"
                ),
                item.optString(
                    "event_code",
                    "<none>"
                )
            )
        }

        val overall =
            when {
                failures > 0 ->
                    "FAIL"

                warnings > 0 ->
                    "WARN"

                else ->
                    "PASS"
            }

        return buildString {

            append(
                "SELF-TEST "
            )

            append(
                overall
            )

            append(
                "\nFailures: "
            )

            append(
                failures
            )

            append(
                "\nWarnings: "
            )

            append(
                warnings
            )

            append(
                "\n\n"
            )

            lines.forEach {
                append(
                    it
                )

                append(
                    "\n"
                )
            }

            append(
                "\nHealth/event classifications and dedicated bounded checks come " +
                    "from the companion contract; this screen does not create separate " +
                    "performance thresholds."
            )
        }
    }


    private fun dp(
        value: Int
    ): Int {

        return (
            value *
                resources.displayMetrics.density
            ).toInt()
    }
}
