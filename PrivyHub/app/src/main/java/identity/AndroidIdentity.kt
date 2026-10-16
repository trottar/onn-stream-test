package com.safeiot.privyhub.identity

import android.content.Context
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.widget.Toast
import java.io.File
import java.net.DatagramSocket
import java.net.HttpURLConnection
import java.net.Inet4Address
import java.net.InetAddress
import java.net.NetworkInterface
import java.net.URL
import java.security.SecureRandom

/**
 * G3-S2: the Android side of [IdentitySession].
 *
 * - The setting: `identity_v2` in `privyhub_settings`, **default off**.
 * - The device secret: `files/identity/device_secret` (app-private; owner
 *   read/write only), never logged.
 * - The pairing (device id, name, permissions): `privyhub_identity` prefs.
 * - The token: in memory only.
 * - The declared media host: the local address of the route to the hub
 *   (a UDP `connect`, which sends nothing).
 * Log lines carry states and reason codes only; never an address.
 *
 * G3-S3: "Hub host" (`hub_host`, empty = today) overrides the companion host
 * for every call while the setting is on; the overlay interface address is
 * declared at setup; the hub's media requests carry the token.
 */
object PrivyHubIdentity {
    const val SETTINGS_PREFS = "privyhub_settings"
    const val PREF_IDENTITY_V2 = "identity_v2"
    const val PREF_HUB_HOST = "hub_host"
    const val MEDIA_PORT = 8000
    private const val IDENTITY_PREFS = "privyhub_identity"
    private const val TAG = "PrivyHubIdentity"

    @Volatile private var session: IdentitySession? = null

    fun get(context: Context): IdentitySession {
        session?.let { return it }
        synchronized(this) {
            session?.let { return it }
            val app = context.applicationContext
            val s = IdentitySession(
                enabled = { isEnabled(app) },
                store = PrefsIdentityStore(app),
                transport = HttpControlTransport,
                routes = UdpRoute,
                clock = System::currentTimeMillis,
                randomBytes = { n -> ByteArray(n).also { SecureRandom().nextBytes(it) } },
                log = { line -> Log.i(TAG, line) },
            )
            // The visible state: the host's reason code, on screen.
            s.onRefusal = { reason ->
                Handler(Looper.getMainLooper()).post {
                    Toast.makeText(app, "PrivyHub session refused: $reason", Toast.LENGTH_LONG).show()
                }
            }
            session = s
            return s
        }
    }

    fun isEnabled(context: Context): Boolean =
        context.getSharedPreferences(SETTINGS_PREFS, Context.MODE_PRIVATE)
            .getBoolean(PREF_IDENTITY_V2, false)

    fun setEnabled(context: Context, enabled: Boolean) {
        context.getSharedPreferences(SETTINGS_PREFS, Context.MODE_PRIVATE)
            .edit().putBoolean(PREF_IDENTITY_V2, enabled).apply()
        if (!enabled) session?.endSessionLocally()
    }

    /** G3-S3: the stored "Hub host" (the hub's tailnet name, or any hostname); "" = none. */
    fun hubHost(context: Context): String =
        context.getSharedPreferences(SETTINGS_PREFS, Context.MODE_PRIVATE)
            .getString(PREF_HUB_HOST, "")?.trim().orEmpty()

    fun setHubHost(context: Context, host: String) {
        val clean = host.trim()
        if (clean == hubHost(context)) return
        context.getSharedPreferences(SETTINGS_PREFS, Context.MODE_PRIVATE)
            .edit().putString(PREF_HUB_HOST, clean).apply()
        session?.endSessionLocally()   // a new host is a new session
    }

    /**
     * G3-S3: the host every call goes to. The setting off, or no hub host:
     * `companionHost` as given (today). The setting on and a hub host set: the hub host.
     */
    fun effectiveHost(context: Context, companionHost: String): String {
        if (!isEnabled(context)) return companionHost
        return SessionProtocol.effectiveHost(true, hubHost(context), companionHost)
    }

    /**
     * G3-S3: the session header for a request to the hub's range server, only
     * when the URL's host and port are the hub's media endpoint (never on a
     * third-party URL). Off: null at once. A refused setup: null (the host's
     * reason code was already shown).
     */
    fun mediaHeader(context: Context, url: String, hubHost: String): String? {
        if (!isEnabled(context)) return null
        if (!SessionProtocol.isHubMediaUrl(url, hubHost, MEDIA_PORT)) return null
        return try {
            get(context).mediaHeaderFor(hubHost.trim())
        } catch (_: IdentitySession.IdentityRefused) {
            null
        }
    }

    /** G3-S3: adds the media header to a range-server connection (artwork). Off: touches nothing. */
    fun decorateMedia(context: Context, connection: HttpURLConnection, url: String, hubHost: String) {
        if (!isEnabled(context)) return
        mediaHeader(context, url, hubHost)?.let { connection.setRequestProperty(SessionProtocol.HEADER, it) }
    }

    /** G3-S3: a URL as a log line may carry it: under the setting, the host is a 12-hex hash. */
    fun urlForLog(context: Context, url: String): String =
        if (isEnabled(context)) SessionProtocol.urlForLog(url) else url

    /**
     * Adds `X-PrivyHub-Session` to a control-port connection when the setting
     * is on, the device is paired and the path needs a granted permission.
     * Off: returns at once and touches nothing (today's request).
     */
    fun decorate(context: Context, connection: HttpURLConnection, url: String) =
        decorateConnection(connection, url, isEnabled(context)) { get(context) }

    private class PrefsIdentityStore(private val context: Context) : IdentitySession.IdentityStore {
        private val secretFile get() = File(File(context.filesDir, "identity"), "device_secret")
        private val prefs get() = context.getSharedPreferences(IDENTITY_PREFS, Context.MODE_PRIVATE)

        override fun secretHex(): String? =
            secretFile.takeIf { it.isFile }?.readText(Charsets.US_ASCII)?.trim()?.takeIf { it.isNotEmpty() }

        override fun saveSecretHex(hex: String) {
            val dir = secretFile.parentFile!!
            dir.mkdirs()
            dir.setReadable(false, false); dir.setReadable(true, true)
            dir.setExecutable(false, false); dir.setExecutable(true, true)
            val tmp = File(dir, "device_secret.tmp")
            tmp.writeText(hex, Charsets.US_ASCII)
            tmp.setReadable(false, false); tmp.setReadable(true, true)
            tmp.setWritable(false, false); tmp.setWritable(true, true)
            if (!tmp.renameTo(secretFile)) throw IllegalStateException("identity: could not store the secret")
        }

        override fun pairing(): IdentitySession.Pairing? {
            val id = prefs.getString("device_id", null) ?: return null
            return IdentitySession.Pairing(
                id,
                prefs.getString("display_name", "") ?: "",
                (prefs.getString("permissions", "") ?: "").split(',').filter { it.isNotBlank() },
            )
        }

        override fun savePairing(pairing: IdentitySession.Pairing) {
            prefs.edit()
                .putString("device_id", pairing.deviceId)
                .putString("display_name", pairing.displayName)
                .putString("permissions", pairing.permissions.joinToString(","))
                .apply()
        }
    }

    private object HttpControlTransport : IdentitySession.ControlTransport {
        override fun post(url: String, jsonBody: String?): Pair<Int, String> {
            val body = (jsonBody ?: "").toByteArray(Charsets.UTF_8)
            val connection = (URL(url).openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                connectTimeout = 3_000
                readTimeout = 5_000
                useCaches = false
                doInput = true
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
                setFixedLengthStreamingMode(body.size)
            }
            try {
                connection.outputStream.use { it.write(body) }
                val code = connection.responseCode
                val stream = if (code in 200..299) connection.inputStream else connection.errorStream
                return code to (stream?.bufferedReader()?.use { it.readText() }.orEmpty())
            } finally {
                connection.disconnect()
            }
        }
    }

    private object UdpRoute : IdentitySession.LocalRoute {
        override fun localAddressFor(host: String, port: Int): String? =
            try {
                DatagramSocket().use { socket ->
                    socket.connect(InetAddress.getByName(host), port)
                    socket.localAddress?.takeIf { !it.isAnyLocalAddress }?.hostAddress
                }
            } catch (_: Exception) {
                null
            }

        // G3-S3: the overlay interface (the Tailscale app's tunnel): an up
        // interface holding an IPv4 address in the overlay block. Nothing is sent.
        override fun overlayAddress(): String? =
            try {
                NetworkInterface.getNetworkInterfaces()?.toList().orEmpty()
                    .filter { it.isUp && !it.isLoopback }
                    .flatMap { it.inetAddresses.toList() }
                    .filterIsInstance<Inet4Address>()
                    .mapNotNull { it.hostAddress }
                    .firstOrNull { SessionProtocol.isOverlayIpv4(it) }
            } catch (_: Exception) {
                null
            }
    }
}
