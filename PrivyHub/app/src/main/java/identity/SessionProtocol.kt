package com.safeiot.privyhub.identity

import java.net.URI
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

/**
 * G3-S2: the bytes of G3-S1's session protocol, client side. Pure Kotlin (no
 * Android), so the JVM unit tests check it against the host's own vectors.
 *
 * Host contract: `companion/session_identity.py` and §1 of
 * `docs/memory/evidence/G3_S1_SESSION_IDENTITY_HOST_SIDE_2026-10-15.md`.
 */
object SessionProtocol {
    const val HEADER = "X-PrivyHub-Session"
    const val SETUP_CANON = "privyhub-session-setup-v1"
    const val SECRET_BYTES = 32

    // G3-S3: the v2 canon signs the audio port and the overlay address too.
    const val SETUP_CANON_V2 = "privyhub-session-setup-v2"
    const val MEDIA_PERMISSION = "vod"

    // CL-B4: the v3 canon signs v2's fields and the audio codecs this client decodes (G4-W2).
    const val SETUP_CANON_V3 = "privyhub-session-setup-v3"
    val AUDIO_CODECS = listOf("opus")
    const val V3_FALLBACK_REASON = "bad-signature"
    const val MEDIA_TOKEN_PARAM = "media_token"

    /** Granted to a paired device without being listed at pairing (G3-S3: diagnostics, default on). */
    val IMPLIED_FOR_PAIRED = setOf("diagnostics")

    /** Re-run the setup when less than this remains of the token. */
    const val REFRESH_MARGIN_MS = 10L * 60L * 1000L

    /** Refusals that one fresh setup may cure; anything else is shown at once. */
    val RETRYABLE_REASONS = setOf("token-unknown", "token-expired")

    /** The audit's session-setup actions (G3-S1 `SETUP_PATHS`). */
    val SETUP_PATHS = setOf(
        "/plugins/games/launch",
        "/plugins/games/native-stream-start",
        "/plugins/games/recovery-resume",
        "/plugins/games/recovery-copy",
    )

    /** The exact HMAC input G3-S1 signs: five lines joined by '\n', no trailing newline. */
    fun setupCanonical(deviceId: String, nonce: String, mediaHost: String, videoPort: Int): String =
        listOf(SETUP_CANON, deviceId, nonce, mediaHost, videoPort.toString()).joinToString("\n")

    fun hmacSha256Hex(keyHex: String, message: String): String {
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(hexToBytes(keyHex), "HmacSHA256"))
        return bytesToHex(mac.doFinal(message.toByteArray(Charsets.UTF_8)))
    }

    fun sign(keyHex: String, deviceId: String, nonce: String, mediaHost: String, videoPort: Int): String =
        hmacSha256Hex(keyHex, setupCanonical(deviceId, nonce, mediaHost, videoPort))

    /** G3-S3: seven lines; an absent overlay address is the empty string. */
    fun setupCanonicalV2(
        deviceId: String,
        nonce: String,
        mediaHost: String,
        videoPort: Int,
        audioPort: Int,
        overlayHost: String?,
    ): String =
        listOf(SETUP_CANON_V2, deviceId, nonce, mediaHost, videoPort.toString(), audioPort.toString(), overlayHost ?: "")
            .joinToString("\n")

    fun signV2(
        keyHex: String,
        deviceId: String,
        nonce: String,
        mediaHost: String,
        videoPort: Int,
        audioPort: Int,
        overlayHost: String?,
    ): String = hmacSha256Hex(keyHex, setupCanonicalV2(deviceId, nonce, mediaHost, videoPort, audioPort, overlayHost))

    /** CL-B4: v2's seven lines (named v3) and an eighth, the codecs joined by ','. */
    fun setupCanonicalV3(
        deviceId: String,
        nonce: String,
        mediaHost: String,
        videoPort: Int,
        audioPort: Int,
        overlayHost: String?,
        audioCodecs: List<String>,
    ): String =
        listOf(
            SETUP_CANON_V3, deviceId, nonce, mediaHost, videoPort.toString(), audioPort.toString(), overlayHost ?: "",
            audioCodecs.joinToString(","),
        ).joinToString("\n")

    fun signV3(
        keyHex: String,
        deviceId: String,
        nonce: String,
        mediaHost: String,
        videoPort: Int,
        audioPort: Int,
        overlayHost: String?,
        audioCodecs: List<String>,
    ): String =
        hmacSha256Hex(keyHex, setupCanonicalV3(deviceId, nonce, mediaHost, videoPort, audioPort, overlayHost, audioCodecs))

    /** G3-S3: an IPv4 address in the overlay's block (the shared CGNAT /10, Tailscale's range). */
    fun isOverlayIpv4(address: String): Boolean {
        val parts = address.split('.')
        if (parts.size != 4) return false
        val octets = parts.map { it.toIntOrNull() ?: return false }
        if (octets.any { it !in 0..255 }) return false
        val value = (octets[0].toLong() shl 24) or (octets[1].toLong() shl 16) or
            (octets[2].toLong() shl 8) or octets[3].toLong()
        return (value and 0xFFC00000L) == 0x64400000L
    }

    /** G3-S3: the host every call goes to: the hub host when the setting is on and one is set. */
    fun effectiveHost(enabled: Boolean, hubHost: String, companionHost: String): String =
        if (enabled && hubHost.isNotBlank()) hubHost.trim() else companionHost

    /** G3-S3: true only for the hub's own media endpoint (host and port); never a third-party URL. */
    fun isHubMediaUrl(url: String, hubHost: String, mediaPort: Int): Boolean =
        try {
            val uri = URI(url)
            val port = if (uri.port >= 0) uri.port else if (uri.scheme == "http") 80 else 443
            hubHost.isNotBlank() && uri.host != null && uri.host.equals(hubHost.trim(), ignoreCase = true) &&
                port == mediaPort
        } catch (_: Exception) {
            false
        }

    /** G3-S3: a host for a log line: a 12-hex hash, never the value. */
    fun hostHash(host: String): String =
        java.security.MessageDigest.getInstance("SHA-256")
            .digest(host.toByteArray(Charsets.UTF_8))
            .let { bytesToHex(it) }
            .substring(0, 12)

    /** G3-S3: a URL for a log line, its host replaced by [hostHash]. */
    fun urlForLog(url: String): String =
        try {
            val uri = URI(url)
            val host = uri.host ?: return "(url)"
            URI(uri.scheme, null, "h-" + hostHash(host), uri.port, uri.rawPath, null, null).toString()
        } catch (_: Exception) {
            "(url)"
        }

    /** G3-S1 `required_permission`, mirrored: the header is sent only where it is honoured. */
    fun requiredPermission(path: String): String? = when {
        path.startsWith("/plugins/games/") || path == "/diagnostics/client-health" -> "games"
        path.startsWith("/plugins/tv_state/") || path.startsWith("/plugins/epg/") ||
            path.startsWith("/plugins/iptv_org/") || path.startsWith("/sources/") ||
            path == "/sources" || path == "/stop" -> "tv"
        path == "/status" || path.startsWith("/diagnostics/") -> "diagnostics"
        else -> null
    }

    fun pathOf(url: String): String =
        try {
            URI(url).rawPath ?: ""
        } catch (_: Exception) {
            ""
        }

    // ---- JSON, minimal and exact for this protocol's flat bodies ----------

    fun jsonString(value: String): String {
        val out = StringBuilder("\"")
        for (ch in value) {
            when {
                ch == '"' -> out.append("\\\"")
                ch == '\\' -> out.append("\\\\")
                ch == '\n' -> out.append("\\n")
                ch == '\r' -> out.append("\\r")
                ch == '\t' -> out.append("\\t")
                ch < ' ' -> out.append(String.format("\\u%04x", ch.code))
                else -> out.append(ch)
            }
        }
        return out.append('"').toString()
    }

    /**
     * The setup body. The signed fields are exactly G3-S1's; `audio_port` is
     * declared too, but the host as written reads only `media_host` and
     * `video_port` (it ignores the rest, and the signature does not cover it).
     */
    fun setupBody(
        deviceId: String,
        nonce: String,
        mediaHost: String,
        videoPort: Int,
        audioPort: Int,
        sig: String,
    ): String =
        "{" +
            "\"device_id\":" + jsonString(deviceId) + "," +
            "\"nonce\":" + jsonString(nonce) + "," +
            "\"media_host\":" + jsonString(mediaHost) + "," +
            "\"video_port\":" + videoPort + "," +
            "\"audio_port\":" + audioPort + "," +
            "\"sig\":" + jsonString(sig) +
            "}"

    /** G3-S3: the v2 setup body (`sig_v` 2); `overlay_host` only when present. */
    fun setupBodyV2(
        deviceId: String,
        nonce: String,
        mediaHost: String,
        videoPort: Int,
        audioPort: Int,
        overlayHost: String?,
        sig: String,
    ): String =
        "{" +
            "\"device_id\":" + jsonString(deviceId) + "," +
            "\"nonce\":" + jsonString(nonce) + "," +
            "\"media_host\":" + jsonString(mediaHost) + "," +
            "\"video_port\":" + videoPort + "," +
            "\"audio_port\":" + audioPort + "," +
            (if (overlayHost != null) "\"overlay_host\":" + jsonString(overlayHost) + "," else "") +
            "\"sig_v\":2," +
            "\"sig\":" + jsonString(sig) +
            "}"

    /** CL-B4: the v3 setup body (`sig_v` 3): v2's, with `audio_codecs`. */
    fun setupBodyV3(
        deviceId: String,
        nonce: String,
        mediaHost: String,
        videoPort: Int,
        audioPort: Int,
        overlayHost: String?,
        audioCodecs: List<String>,
        sig: String,
    ): String =
        "{" +
            "\"device_id\":" + jsonString(deviceId) + "," +
            "\"nonce\":" + jsonString(nonce) + "," +
            "\"media_host\":" + jsonString(mediaHost) + "," +
            "\"video_port\":" + videoPort + "," +
            "\"audio_port\":" + audioPort + "," +
            (if (overlayHost != null) "\"overlay_host\":" + jsonString(overlayHost) + "," else "") +
            "\"audio_codecs\":[" + audioCodecs.joinToString(",") { jsonString(it) } + "]," +
            "\"sig_v\":3," +
            "\"sig\":" + jsonString(sig) +
            "}"

    fun pairBody(code: String, deviceName: String, keyHex: String): String =
        "{" +
            "\"code\":" + jsonString(code) + "," +
            "\"device_name\":" + jsonString(deviceName) + "," +
            "\"key\":" + jsonString(keyHex) +
            "}"

    private fun unescape(raw: String): String {
        val out = StringBuilder()
        var i = 0
        while (i < raw.length) {
            val ch = raw[i]
            if (ch == '\\' && i + 1 < raw.length) {
                when (val n = raw[i + 1]) {
                    'n' -> out.append('\n')
                    'r' -> out.append('\r')
                    't' -> out.append('\t')
                    'u' -> if (i + 5 < raw.length) {
                        out.append(raw.substring(i + 2, i + 6).toInt(16).toChar()); i += 4
                    }
                    else -> out.append(n)
                }
                i += 2
            } else {
                out.append(ch); i += 1
            }
        }
        return out.toString()
    }

    fun jsonStringField(body: String, name: String): String? =
        Regex("\"" + Regex.escape(name) + "\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\"")
            .find(body)?.groupValues?.get(1)?.let(::unescape)

    fun jsonLongField(body: String, name: String): Long? =
        Regex("\"" + Regex.escape(name) + "\"\\s*:\\s*(-?\\d+)")
            .find(body)?.groupValues?.get(1)?.toLongOrNull()

    fun jsonStringArray(body: String, name: String): List<String> {
        val inner = Regex("\"" + Regex.escape(name) + "\"\\s*:\\s*\\[([^\\]]*)\\]")
            .find(body)?.groupValues?.get(1) ?: return emptyList()
        return Regex("\"((?:[^\"\\\\]|\\\\.)*)\"").findAll(inner).map { unescape(it.groupValues[1]) }.toList()
    }

    fun reasonOf(body: String?): String? = body?.let { jsonStringField(it, "reason") }

    // ---- hex ----------------------------------------------------------------

    fun bytesToHex(bytes: ByteArray): String {
        val digits = "0123456789abcdef"
        val out = StringBuilder(bytes.size * 2)
        for (b in bytes) {
            val v = b.toInt() and 0xff
            out.append(digits[v ushr 4]).append(digits[v and 0x0f])
        }
        return out.toString()
    }

    fun hexToBytes(hex: String): ByteArray {
        require(hex.length % 2 == 0) { "odd hex length" }
        return ByteArray(hex.length / 2) { i -> hex.substring(2 * i, 2 * i + 2).toInt(16).toByte() }
    }
}
