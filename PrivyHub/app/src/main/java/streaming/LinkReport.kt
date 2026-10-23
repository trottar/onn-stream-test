package com.safeiot.privyhub.streaming

import android.content.Context
import android.net.wifi.WifiManager
import android.os.Build

/**
 * B3: the client's Wi-Fi link quality in its 2-s reports, behind the system
 * property `debug.privyhub.link_report` (CL-B7P's convention; a reboot
 * clears it). B13: absent (or anything but `0`) = ON; `0` turns it off.
 *
 * Read with ACCESS_WIFI_STATE (already declared; a normal permission, no
 * prompt): RSSI, tx / rx link speed, frequency, Wi-Fi standard. No SSID,
 * BSSID, MAC or address is read or sent. At most one read a second
 * ([LinkSampler]), on the two report threads, never on the receive path.
 */
object LinkReportFlag {
    const val PROPERTY = "debug.privyhub.link_report"

    fun parse(value: String?): Boolean = value?.trim() != "0"   // B13: on unless `0`

    /** The property, read through reflection; a failed read is absent, so on (B13). */
    fun fromSystem(): Boolean =
        try {
            val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            parse(get.invoke(null, PROPERTY) as? String)
        } catch (_: Throwable) {
            parse(null)
        }
}

/** One reading; each field null when the platform gave nothing valid. */
data class LinkSample(
    val rssiDbm: Int?,
    val txMbps: Int?,
    val rxMbps: Int?,
    val frequencyMhz: Int?,
    val wifiStandard: Int?,
) {
    /** The valid fields, in a fixed order, as (heartbeat key suffix, value). */
    fun fields(): List<Pair<String, Int>> =
        listOfNotNull(
            rssiDbm?.let { "rssi_dbm" to it },
            txMbps?.let { "tx_mbps" to it },
            rxMbps?.let { "rx_mbps" to it },
            frequencyMhz?.let { "frequency_mhz" to it },
            wifiStandard?.let { "wifi_standard" to it },
        )

    /** The heartbeat's query keys (`&link_<name>=<value>`), the valid fields only. */
    fun query(): String = fields().joinToString("") { (k, v) -> "&link_$k=$v" }

    companion object {
        private const val INVALID_RSSI = -127

        /** The platform's raw values, each kept only when valid. */
        fun of(rssi: Int, txMbps: Int, rxMbps: Int, frequencyMhz: Int, wifiStandard: Int): LinkSample =
            LinkSample(
                rssiDbm = rssi.takeIf { it in (INVALID_RSSI + 1)..-1 },
                txMbps = txMbps.takeIf { it > 0 },
                rxMbps = rxMbps.takeIf { it > 0 },
                frequencyMhz = frequencyMhz.takeIf { it > 0 },
                wifiStandard = wifiStandard.takeIf { it > 0 },
            )
    }
}

/** At most one [read] per [minIntervalNs], whoever asks; the last reading in between. */
class LinkSampler(
    private val read: () -> LinkSample?,
    private val clock: () -> Long = System::nanoTime,
    private val minIntervalNs: Long = 1_000_000_000L,
) {
    private var lastReadNs: Long? = null
    private var last: LinkSample? = null
    var reads = 0L
        private set

    @Synchronized
    fun current(): LinkSample? {
        val now = clock()
        val prev = lastReadNs
        if (prev == null || now - prev >= minIntervalNs) {
            lastReadNs = now
            reads += 1
            last = try {
                read()
            } catch (_: Throwable) {
                null
            }
        }
        return last
    }
}

/** The platform read: WifiManager.getConnectionInfo() (deprecated from API 31, still answered). */
@Suppress("DEPRECATION")
fun readWifi(context: Context): LinkSample? {
    val manager = context.applicationContext.getSystemService(Context.WIFI_SERVICE) as? WifiManager ?: return null
    val info = manager.connectionInfo ?: return null
    val tx = if (Build.VERSION.SDK_INT >= 29) info.txLinkSpeedMbps else info.linkSpeed
    val rx = if (Build.VERSION.SDK_INT >= 29) info.rxLinkSpeedMbps else -1
    val standard = if (Build.VERSION.SDK_INT >= 30) info.wifiStandard else 0
    return LinkSample.of(info.rssi, tx, rx, info.frequency, standard)
}
