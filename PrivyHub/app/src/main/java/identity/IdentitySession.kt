package com.safeiot.privyhub.identity

/**
 * G3-S2: the client's session identity, behind the `identity_v2` setting
 * (default off). Pure Kotlin; Android supplies the store, the transport and
 * the route lookup (`AndroidIdentity.kt`).
 *
 * Off: every entry point returns at once — no nonce, no header, no declared
 * endpoint, no store read — so the requests are today's, byte for byte.
 *
 * On, not paired: no header either (the host's legacy LAN path, as today).
 * On and paired: a nonce-signed setup issues a token (refreshed before it
 * expires); it rides as `X-PrivyHub-Session` on every control call whose path
 * needs a permission the host granted. A refusal shows the host's reason code;
 * a token refusal gets one fresh setup and one retry, then a visible state.
 *
 * The device secret never leaves the store except once, in the pairing body
 * — G3-S1's host verifies HMAC-SHA256 and so must hold the key. Nothing here
 * logs an address, the secret or a token.
 *
 * G3-S3: the setup signs v2 (the audio port and, when the device holds one,
 * its overlay interface address); `diagnostics` is on for a paired device;
 * the media requests to the hub's range server carry the token too
 * ([mediaHeaderFor]), or the session's media token for a player that cannot
 * set headers ([mediaTokenFor]).
 */
class IdentitySession(
    private val enabled: () -> Boolean,
    private val store: IdentityStore,
    private val transport: ControlTransport,
    private val routes: LocalRoute,
    private val clock: () -> Long,
    private val randomBytes: (Int) -> ByteArray,
    private val log: (String) -> Unit = {},
    private val videoPort: Int = 48100,
    private val audioPort: Int = 48101,
    private val controlPort: Int = 8765,
) {
    data class Pairing(val deviceId: String, val displayName: String, val permissions: List<String>)

    interface IdentityStore {
        fun secretHex(): String?
        fun saveSecretHex(hex: String)
        fun pairing(): Pairing?
        fun savePairing(pairing: Pairing)
    }

    /** POST `jsonBody` (or an empty body) to `url`; returns (status, body). Throws on I/O failure. */
    fun interface ControlTransport {
        fun post(url: String, jsonBody: String?): Pair<Int, String>
    }

    /** The local address this device uses to reach `host` (no packet is sent). */
    fun interface LocalRoute {
        fun localAddressFor(host: String, port: Int): String?

        /** G3-S3: this device's overlay interface address (IPv4, the overlay block), if any. */
        fun overlayAddress(): String? = null
    }

    class IdentityRefused(val reason: String) : IllegalStateException("Session refused: $reason")

    sealed class PairResult {
        data class Paired(val pairing: Pairing) : PairResult()
        data class Refused(val status: Int, val reason: String) : PairResult()
    }

    private data class Token(
        val value: String,
        val expiresAtMs: Long,
        val permissions: Set<String>,
        val mediaToken: String? = null,
    )

    private var token: Token? = null
    private var hostIdentityOffUntilMs = 0L
    private var setupRefusedUntilMs = 0L
    private var setupRefusedReason: String? = null

    @Volatile var lastReason: String? = null
        private set

    @Volatile var stateText: String = "off"
        private set

    var onRefusal: ((String) -> Unit)? = null

    val isEnabled: Boolean get() = enabled()

    fun currentPairing(): Pairing? = store.pairing()

    // ---- the secret and pairing ---------------------------------------------

    @Synchronized
    fun ensureSecret(): String {
        store.secretHex()?.let { if (it.length == SessionProtocol.SECRET_BYTES * 2) return it }
        val hex = SessionProtocol.bytesToHex(randomBytes(SessionProtocol.SECRET_BYTES))
        store.saveSecretHex(hex)
        log("identity: device secret created")
        return hex
    }

    /** Pair with the code the hub shows. `newSecret` replaces the secret first (explicit re-pair only). */
    @Synchronized
    fun pair(host: String, code: String, displayName: String, newSecret: Boolean = false): PairResult {
        if (newSecret) {
            store.saveSecretHex(SessionProtocol.bytesToHex(randomBytes(SessionProtocol.SECRET_BYTES)))
            log("identity: device secret replaced (re-pair)")
        }
        val secret = ensureSecret()
        val (status, body) = transport.post(
            controlUrl(host, "/session/pair"),
            SessionProtocol.pairBody(code.trim(), displayName.trim(), secret),
        )
        val deviceId = SessionProtocol.jsonStringField(body, "device_id")
        if (status != 200 || deviceId == null) {
            val reason = SessionProtocol.reasonOf(body) ?: "http-$status"
            refused(reason)
            return PairResult.Refused(status, reason)
        }
        val pairing = Pairing(deviceId, displayName.trim(), SessionProtocol.jsonStringArray(body, "permissions"))
        store.savePairing(pairing)
        token = null
        lastReason = null
        stateText = "paired"
        log("identity: paired, permissions=" + pairing.permissions.joinToString(","))
        return PairResult.Paired(pairing)
    }

    // ---- the session ------------------------------------------------------------

    /**
     * The header value for a control call to `url`, or null for none.
     * Throws [IdentityRefused] when paired but the host refused the setup
     * (fail closed: the call is not made without the identity it needs).
     */
    @Synchronized
    fun headerFor(host: String, url: String): String? {
        if (!enabled()) return null
        if (store.pairing() == null) { stateText = "on, not paired (legacy)"; return null }
        val permission = SessionProtocol.requiredPermission(SessionProtocol.pathOf(url)) ?: return null
        return liveToken(host, permission)?.value
    }

    /** G3-S3: the header value for a request to the hub's range server (the `vod` permission). */
    @Synchronized
    fun mediaHeaderFor(host: String): String? {
        if (!enabled()) return null
        return liveToken(host, SessionProtocol.MEDIA_PERMISSION)?.value
    }

    /** G3-S3: the session's media token, for a player that cannot set headers (`?media_token=`). */
    @Synchronized
    fun mediaTokenFor(host: String): String? {
        if (!enabled()) return null
        return liveToken(host, SessionProtocol.MEDIA_PERMISSION)?.mediaToken
    }

    private fun liveToken(host: String, permission: String): Token? {
        val pairing = store.pairing() ?: run { stateText = "on, not paired (legacy)"; return null }
        if (permission !in pairing.permissions && permission !in SessionProtocol.IMPLIED_FOR_PAIRED) return null
        val now = clock()
        if (now < hostIdentityOffUntilMs) return null
        token?.let { if (now < it.expiresAtMs - SessionProtocol.REFRESH_MARGIN_MS) return grantedOrNull(it, permission) }
        if (now < setupRefusedUntilMs) throw IdentityRefused(setupRefusedReason ?: "setup-refused")
        return setup(host, pairing, now)?.let { grantedOrNull(it, permission) }
    }

    private fun grantedOrNull(t: Token, permission: String): Token? =
        if (permission in t.permissions) t else null

    private fun setup(host: String, pairing: Pairing, now: Long): Token? {
        val (nonceStatus, nonceBody) = transport.post(controlUrl(host, "/session/nonce"), null)
        if (nonceStatus == 404) {
            // The host runs without the identity layer (flag absent): today's requests.
            hostIdentityOffUntilMs = now + HOST_OFF_RECHECK_MS
            stateText = "paired; host identity off"
            log("identity: host identity layer absent")
            return null
        }
        val nonce = SessionProtocol.jsonStringField(nonceBody, "nonce")
        if (nonceStatus != 200 || nonce == null) {
            return setupRefused(SessionProtocol.reasonOf(nonceBody) ?: "http-$nonceStatus", now)
        }
        val mediaHost = routes.localAddressFor(host, controlPort)
            ?: return setupRefused("no-local-route", now)
        val secret = ensureSecret()
        // G3-S3: v2 signs the audio port and the overlay interface address (when present).
        val overlayHost = routes.overlayAddress()?.takeIf { SessionProtocol.isOverlayIpv4(it) }
        val sig = SessionProtocol.signV2(secret, pairing.deviceId, nonce, mediaHost, videoPort, audioPort, overlayHost)
        val (status, body) = transport.post(
            controlUrl(host, "/session/setup"),
            SessionProtocol.setupBodyV2(pairing.deviceId, nonce, mediaHost, videoPort, audioPort, overlayHost, sig),
        )
        val value = SessionProtocol.jsonStringField(body, "token")
        val ttl = SessionProtocol.jsonLongField(body, "expires_in_s")
        if (status != 200 || value == null || ttl == null) {
            return setupRefused(SessionProtocol.reasonOf(body) ?: "http-$status", now)
        }
        val granted = SessionProtocol.jsonStringArray(body, "permissions").toSet()
        val t = Token(value, now + ttl * 1000L, granted, SessionProtocol.jsonStringField(body, "media_token"))
        token = t
        // G3-S3: the host's grant is the record (diagnostics added, or a permission revoked).
        if (granted != pairing.permissions.toSet()) {
            store.savePairing(pairing.copy(permissions = granted.toList()))
        }
        setupRefusedUntilMs = 0L
        lastReason = null
        stateText = "session active"
        log("identity: session set up, expires_in_s=$ttl, overlay_declared=${overlayHost != null}")
        return t
    }

    private fun setupRefused(reason: String, now: Long): Token? {
        setupRefusedUntilMs = now + SETUP_COOLDOWN_MS
        setupRefusedReason = reason
        refused(reason)
        throw IdentityRefused(reason)
    }

    private fun refused(reason: String) {
        lastReason = reason
        stateText = "refused: $reason"
        log("identity: refused, reason=$reason")
        onRefusal?.invoke(reason)
    }

    /**
     * After a non-2xx answer to a control call: true = retry the call once
     * (a token refusal; the token is dropped so the retry sets up afresh).
     * Off, or no reason code: false, and nothing changes.
     */
    @Synchronized
    fun onResponse(status: Int, body: String?, attempt: Int): Boolean {
        if (!enabled() || (status != 401 && status != 403)) return false
        val reason = SessionProtocol.reasonOf(body) ?: return false
        if (reason in SessionProtocol.RETRYABLE_REASONS && attempt == 0 && store.pairing() != null) {
            token = null
            log("identity: token refused ($reason), one fresh setup")
            return true
        }
        refused(reason)
        return false
    }

    /** The error text for a refused call: the host's reason code, under the setting only. */
    fun refusalMessage(status: Int, body: String?): String? {
        if (!enabled()) return null
        val reason = SessionProtocol.reasonOf(body) ?: return null
        return "Session refused ($status): $reason"
    }

    @Synchronized
    fun endSessionLocally() {
        token = null
    }

    private fun controlUrl(host: String, path: String): String = "http://$host:$controlPort$path"

    companion object {
        const val SETUP_COOLDOWN_MS = 30_000L
        const val HOST_OFF_RECHECK_MS = 60_000L
    }
}


/**
 * Adds the session header to a control-port connection. Off: returns before
 * touching the connection or the session (today's request, byte for byte).
 */
fun decorateConnection(
    connection: java.net.HttpURLConnection,
    url: String,
    enabled: Boolean,
    session: () -> IdentitySession,
) {
    if (!enabled) return
    val host = try {
        java.net.URL(url).host
    } catch (_: Exception) {
        return
    }
    session().headerFor(host, url)?.let { connection.setRequestProperty(SessionProtocol.HEADER, it) }
}
