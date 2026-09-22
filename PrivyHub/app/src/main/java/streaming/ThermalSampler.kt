package com.safeiot.privyhub.streaming

import android.content.Context
import android.os.Build
import android.os.PowerManager
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/**
 * D-BASE-T1 piece 1: the onn's own thermal state, as a trace.
 *
 * Three sources, each best-effort and each allowed to be absent:
 *
 *  - `PowerManager.getCurrentThermalStatus()` (API 29+), the 0-6
 *    NONE..SHUTDOWN scale. Always available on this build's minimum.
 *  - `PowerManager.getThermalHeadroom(10)` (API 30+), a forecast in the
 *    0..1+ range where 1.0 is the throttling point. It returns NaN when the
 *    device does not implement it, and **NaN is recorded as NaN** — a
 *    device that cannot forecast is a finding, not a value to invent.
 *  - each `/sys/class/thermal/thermal_zoneN` directory's `temp` and
 *    `type`, kept only for zones readable without root. Many Android TV
 *    boxes expose the SoC zone world-readable; if none are, the report
 *    says so.
 *
 * Read at most every [MIN_READ_INTERVAL_MS]; the caller may tick faster.
 * Nothing here touches the decode, audio or transport path: it is called
 * from the existing metrics tick and every failure is swallowed.
 */
class ThermalSampler(
    context: Context
) {
    companion object {
        /** The client ticks at 500 ms; sampling is capped to this. */
        const val MIN_READ_INTERVAL_MS = 10_000L

        /** One entry per minute of a four-hour session. */
        const val MAX_SERIES_ENTRIES = 240

        private const val SERIES_INTERVAL_MS = 60_000L

        private const val ZONE_ROOT = "/sys/class/thermal"

        /**
         * A plausible-temperature window. Zones report millidegrees on
         * nearly every device but a few report degrees, so a value is
         * divided by 1000 only when that lands it in range.
         */
        private const val MIN_PLAUSIBLE_C = -40.0
        private const val MAX_PLAUSIBLE_C = 150.0
    }

    private data class ZoneStats(
        val startC: Double,
        var minC: Double,
        var maxC: Double,
        var endC: Double,
        var samples: Long
    )

    private val powerManager =
        context.getSystemService(
            Context.POWER_SERVICE
        ) as? PowerManager

    private val zoneFiles: List<Pair<String, File>> =
        discoverZones()

    private var lastReadAtNs = 0L
    private var startedAtNs = 0L
    private var lastSeriesAtNs = 0L

    @Volatile
    private var statusChanges = 0L

    private var statusMin = Int.MAX_VALUE
    private var statusMax = Int.MIN_VALUE
    private var statusEnd = -1
    private var statusSamples = 0L

    private var headroomMin = Double.NaN
    private var headroomMax = Double.NaN
    private var headroomEnd = Double.NaN
    private var headroomSamples = 0L

    private val zoneStats = LinkedHashMap<String, ZoneStats>()

    /** [elapsed_ms, hottest_zone_c or headroom] rows, capped. */
    private val series = ArrayList<DoubleArray>()
    private var seriesDropped = 0L

    private val listener =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            PowerManager.OnThermalStatusChangedListener {
                statusChanges += 1L
            }
        } else {
            null
        }

    // --- lifecycle ---------------------------------------------------

    fun start(
        nowNs: Long
    ) {
        startedAtNs = nowNs
        lastSeriesAtNs = 0L

        val pm = powerManager ?: return
        val l = listener ?: return

        try {
            pm.addThermalStatusListener(l)
        } catch (_: Throwable) {
            // A device that refuses the listener still reports status by
            // polling; the count simply stays 0.
        }
    }

    fun stop() {
        val pm = powerManager ?: return
        val l = listener ?: return

        try {
            pm.removeThermalStatusListener(l)
        } catch (_: Throwable) {
        }
    }

    // --- sampling ----------------------------------------------------

    /** Reads at most every [MIN_READ_INTERVAL_MS]; safe to call per tick. */
    fun sample(
        nowNs: Long
    ) {
        if (
            lastReadAtNs > 0L &&
            nowNs - lastReadAtNs <
            MIN_READ_INTERVAL_MS * 1_000_000L
        ) {
            return
        }

        lastReadAtNs = nowNs

        readStatus()
        readHeadroom()
        val zones = readZones()

        recordSeries(
            nowNs,
            zones
        )
    }

    private fun readStatus() {
        val pm = powerManager ?: return

        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) {
            return
        }

        val status =
            try {
                pm.currentThermalStatus
            } catch (_: Throwable) {
                return
            }

        statusEnd = status
        statusSamples += 1L

        if (status < statusMin) {
            statusMin = status
        }

        if (status > statusMax) {
            statusMax = status
        }
    }

    private fun readHeadroom() {
        val pm = powerManager ?: return

        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) {
            return
        }

        val headroom =
            try {
                pm.getThermalHeadroom(10).toDouble()
            } catch (_: Throwable) {
                return
            }

        headroomEnd = headroom

        if (headroom.isNaN()) {
            // Recorded as NaN on purpose: the device does not forecast.
            return
        }

        headroomSamples += 1L

        if (headroomMin.isNaN() || headroom < headroomMin) {
            headroomMin = headroom
        }

        if (headroomMax.isNaN() || headroom > headroomMax) {
            headroomMax = headroom
        }
    }

    private fun readZones(): Map<String, Double> {
        val out = LinkedHashMap<String, Double>()

        for ((name, file) in zoneFiles) {
            val c = readZoneCelsius(file) ?: continue

            out[name] = c

            val stats = zoneStats[name]

            if (stats == null) {
                zoneStats[name] =
                    ZoneStats(
                        startC = c,
                        minC = c,
                        maxC = c,
                        endC = c,
                        samples = 1L
                    )
            } else {
                stats.endC = c
                stats.samples += 1L

                if (c < stats.minC) {
                    stats.minC = c
                }

                if (c > stats.maxC) {
                    stats.maxC = c
                }
            }
        }

        return out
    }

    private fun recordSeries(
        nowNs: Long,
        zones: Map<String, Double>
    ) {
        if (
            lastSeriesAtNs > 0L &&
            nowNs - lastSeriesAtNs <
            SERIES_INTERVAL_MS * 1_000_000L
        ) {
            return
        }

        lastSeriesAtNs = nowNs

        // The hottest zone is the series when zones are readable, else
        // headroom. A device that reports neither — the onn is one: its
        // `/sys/class/thermal` is permission-denied and its headroom reads
        // NaN — still reports `thermal_status`, so that is the third
        // fallback rather than leaving the series empty. `seriesSource()`
        // names which of the three a given report used.
        val value =
            zones.values.maxOrNull()
                ?: headroomEnd.takeIf { !it.isNaN() }
                ?: statusEnd.takeIf { it >= 0 }?.toDouble()
                ?: return

        if (value.isNaN()) {
            return
        }

        if (series.size >= MAX_SERIES_ENTRIES) {
            seriesDropped += 1L
            return
        }

        val elapsedMs =
            if (startedAtNs > 0L) {
                (nowNs - startedAtNs)
                    .coerceAtLeast(0L) / 1_000_000L
            } else {
                0L
            }

        series.add(
            doubleArrayOf(
                elapsedMs.toDouble(),
                value
            )
        )
    }

    // --- readers -----------------------------------------------------

    private fun discoverZones(): List<Pair<String, File>> {
        val out = ArrayList<Pair<String, File>>()

        val root = File(ZONE_ROOT)

        val children =
            try {
                root.listFiles()
            } catch (_: Throwable) {
                null
            }
                ?: return out

        for (dir in children.sortedBy { it.name }) {
            if (!dir.name.startsWith("thermal_zone")) {
                continue
            }

            val temp = File(dir, "temp")

            if (!temp.canRead()) {
                continue
            }

            // A zone that cannot be read once will not be read later.
            if (readZoneCelsius(temp) == null) {
                continue
            }

            val type =
                readTrimmed(File(dir, "type"))
                    ?.takeIf { it.isNotBlank() }
                    ?: dir.name

            // Two zones can share a type; keep both, distinguished.
            var name = type
            var suffix = 2

            while (out.any { it.first == name }) {
                name = "$type#$suffix"
                suffix += 1
            }

            out.add(name to temp)
        }

        return out
    }

    private fun readZoneCelsius(
        file: File
    ): Double? {
        val raw =
            readTrimmed(file)
                ?.toDoubleOrNull()
                ?: return null

        val scaled = raw / 1000.0

        if (scaled in MIN_PLAUSIBLE_C..MAX_PLAUSIBLE_C) {
            return Math.round(scaled * 10.0) / 10.0
        }

        if (raw in MIN_PLAUSIBLE_C..MAX_PLAUSIBLE_C) {
            return Math.round(raw * 10.0) / 10.0
        }

        return null
    }

    private fun readTrimmed(
        file: File
    ): String? {
        return try {
            file.readText().trim()
        } catch (_: Throwable) {
            null
        }
    }

    // --- output ------------------------------------------------------

    /** The newest status, for the heartbeat. -1 before the first read. */
    fun statusNow(): Int = statusEnd

    /** The newest headroom, for the heartbeat. NaN when unsupported. */
    fun headroomNow(): Double = headroomEnd

    /** The newest zone readings, for the heartbeat. Empty when none. */
    fun zonesNow(): Map<String, Double> {
        val out = LinkedHashMap<String, Double>()

        for ((name, stats) in zoneStats) {
            out[name] = stats.endC
        }

        return out
    }

    /** `name=c,name=c` — compact enough for a heartbeat query string. */
    fun zonesNowCompact(): String {
        return zonesNow()
            .entries
            .joinToString(",") { "${it.key}=${it.value}" }
    }

    /** True when no thermal zone on this device was readable. */
    fun zonesReadable(): Boolean = zoneFiles.isNotEmpty()

    fun reportJson(): JSONObject {
        val root = JSONObject()

        root.put(
            "status_samples",
            statusSamples
        )
        root.put(
            "status_min",
            if (statusMin == Int.MAX_VALUE) -1 else statusMin
        )
        root.put(
            "status_max",
            if (statusMax == Int.MIN_VALUE) -1 else statusMax
        )
        root.put(
            "status_end",
            statusEnd
        )
        root.put(
            "status_changes",
            statusChanges
        )

        root.put(
            "headroom_supported",
            headroomSamples > 0L
        )
        root.put(
            "headroom_samples",
            headroomSamples
        )
        putDouble(
            root,
            "headroom_min",
            headroomMin
        )
        putDouble(
            root,
            "headroom_max",
            headroomMax
        )
        putDouble(
            root,
            "headroom_end",
            headroomEnd
        )

        root.put(
            "zones_readable",
            zoneFiles.size
        )

        val zones = JSONObject()

        for ((name, stats) in zoneStats) {
            zones.put(
                name,
                JSONObject().apply {
                    put("start_c", stats.startC)
                    put("min_c", stats.minC)
                    put("max_c", stats.maxC)
                    put("end_c", stats.endC)
                    put("samples", stats.samples)
                }
            )
        }

        root.put(
            "zones_c",
            zones
        )

        root.put(
            "series_columns",
            JSONArray().apply {
                put("elapsed_ms")
                put(seriesSource())
            }
        )

        val rows = JSONArray()

        for (row in series) {
            rows.put(
                JSONArray().apply {
                    put(row[0].toLong())
                    put(row[1])
                }
            )
        }

        root.put(
            "series",
            rows
        )
        root.put(
            "series_retained",
            series.size
        )
        root.put(
            "series_capacity",
            MAX_SERIES_ENTRIES
        )
        root.put(
            "series_dropped",
            seriesDropped
        )

        return root
    }

    /** Which of the three signals the series actually carries. */
    private fun seriesSource(): String {
        return when {
            zoneFiles.isNotEmpty() -> "hottest_zone_c"
            headroomSamples > 0L -> "headroom"
            else -> "thermal_status"
        }
    }

    private fun putDouble(
        target: JSONObject,
        key: String,
        value: Double
    ) {
        // JSONObject rejects NaN, and NaN is exactly what an unsupported
        // headroom reads, so it is carried as the string "NaN" rather than
        // replaced by a number that would be a lie.
        if (value.isNaN()) {
            target.put(key, "NaN")
        } else {
            target.put(key, value)
        }
    }
}
