package com.safeiot.privyhub.identity

import java.net.InetAddress
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Test

/**
 * G3-S2: the client's session behaviour — the setting off is today, the
 * header by setting and permission, refresh before expiry, one retry on a
 * token refusal, the reason code shown, fail closed on a refused setup, a
 * host without the identity layer, and no secret or address in a log line.
 *
 * The fake host speaks G3-S1's protocol: it verifies the setup HMAC with the
 * key the client sent at pairing.
 *
 * G3-S3: the fake host verifies the v2 canon when `sig_v` is 2 (the audio
 * port and the overlay address signed), can grant `diagnostics`, and issues a
 * media token; the new cases cover the declared overlay address, diagnostics,
 * the media header and media token, the hub host and the hub-only media rule.
 */
class IdentitySessionTest {

    private val hub = "hub.invalid"
    private val localAddress: String =
        InetAddress.getByAddress(byteArrayOf(0xC0.toByte(), 0xA8.toByte(), 0x64, 0x39)).hostAddress!!

    private class FakeStore : IdentitySession.IdentityStore {
        var secret: String? = null
        var pairing: IdentitySession.Pairing? = null
        var reads = 0
        override fun secretHex(): String? { reads++; return secret }
        override fun saveSecretHex(hex: String) { secret = hex }
        override fun pairing(): IdentitySession.Pairing? { reads++; return pairing }
        override fun savePairing(pairing: IdentitySession.Pairing) { this.pairing = pairing }
    }

    private inner class FakeHost : IdentitySession.ControlTransport {
        val calls = mutableListOf<String>()
        val bodies = mutableListOf<String>()
        var key: String? = null
        var nonces = mutableSetOf<String>()
        var identityLayer = true
        var refuseSetupWith: String? = null
        var counter = 0
        var grant = listOf("games", "tv", "vod")
        override fun post(url: String, jsonBody: String?): Pair<Int, String> {
            val path = SessionProtocol.pathOf(url)
            calls += path
            bodies += jsonBody ?: ""
            if (!identityLayer) return 404 to "{\n  \"ok\": false,\n  \"error\": \"Not found\"\n}"
            return when (path) {
                "/session/pair" -> {
                    if (SessionProtocol.jsonStringField(jsonBody!!, "code") != "123456")
                        return 403 to "{\"ok\": false, \"error\": \"session refused\", \"reason\": \"pairing-bad-code\"}"
                    key = SessionProtocol.jsonStringField(jsonBody, "key")
                    200 to "{\n  \"ok\": true,\n  \"device_id\": \"dev-00112233aabbccdd\",\n  \"permissions\": [\n    \"games\",\n    \"tv\",\n    \"vod\"\n  ]\n}"
                }
                "/session/nonce" -> {
                    val n = "nonce-" + (++counter)
                    nonces += n
                    200 to "{\n  \"ok\": true,\n  \"nonce\": \"$n\",\n  \"expires_in_s\": 60\n}"
                }
                "/session/setup" -> {
                    refuseSetupWith?.let { return 401 to "{\"ok\": false, \"error\": \"session refused\", \"reason\": \"$it\"}" }
                    val b = jsonBody!!
                    val nonce = SessionProtocol.jsonStringField(b, "nonce")!!
                    if (!nonces.remove(nonce)) return 401 to "{\"ok\": false, \"error\": \"session refused\", \"reason\": \"nonce-replayed\"}"
                    val deviceId = SessionProtocol.jsonStringField(b, "device_id")!!
                    val mediaHost = SessionProtocol.jsonStringField(b, "media_host")!!
                    val videoPort = SessionProtocol.jsonLongField(b, "video_port")!!.toInt()
                    val expected = if (SessionProtocol.jsonLongField(b, "sig_v") == 2L) {
                        SessionProtocol.signV2(
                            key!!, deviceId, nonce, mediaHost, videoPort,
                            SessionProtocol.jsonLongField(b, "audio_port")!!.toInt(),
                            SessionProtocol.jsonStringField(b, "overlay_host"),
                        )
                    } else {
                        SessionProtocol.sign(key!!, deviceId, nonce, mediaHost, videoPort)
                    }
                    if (expected != SessionProtocol.jsonStringField(b, "sig"))
                        return 401 to "{\"ok\": false, \"error\": \"session refused\", \"reason\": \"bad-signature\"}"
                    val perms = grant.joinToString(",\n    ", "[\n    ", "\n  ]") { "\"$it\"" }
                    val n = ++counter
                    200 to "{\n  \"ok\": true,\n  \"token\": \"tok-$n\",\n  \"expires_in_s\": 28800,\n  \"client_id\": \"dev-00112233aabbccdd\",\n  \"permissions\": $perms,\n  \"media_token\": \"mtok-$n\"\n}"
                }
                else -> 404 to "{}"
            }
        }
    }

    private var now = 1_000_000L
    private var on = true
    private val logs = mutableListOf<String>()
    private val refusals = mutableListOf<String>()
    private val store = FakeStore()
    private val host = FakeHost()
    private var seed = 0
    private var overlay: String? = null
    private val overlayAddress: String =
        InetAddress.getByAddress(byteArrayOf(0x64, 0x41, 0x12, 0x35)).hostAddress!!
    private val routes = object : IdentitySession.LocalRoute {
        override fun localAddressFor(host: String, port: Int): String? = localAddress
        override fun overlayAddress(): String? = overlay
    }
    private val session = IdentitySession(
        enabled = { on },
        store = store,
        transport = host,
        routes = routes,
        clock = { now },
        randomBytes = { n -> ByteArray(n) { (it + 31 * ++seed).toByte() } },
        log = { logs += it },
    ).also { s -> s.onRefusal = { refusals += it } }

    private val launch = "http://$hub:8765/plugins/games/launch?id=x"

    private fun paired() {
        val r = session.pair(hub, "123456", "onn fixture")
        assertTrue(r is IdentitySession.PairResult.Paired)
    }

    @Test
    fun offIsToday() {
        on = false
        assertNull(session.headerFor(hub, launch))
        assertFalse(session.onResponse(401, "{\"reason\": \"token-expired\"}", 0))
        assertNull(session.refusalMessage(401, "{\"reason\": \"token-expired\"}"))
        assertEquals(emptyList<String>(), host.calls)
        assertEquals(0, store.reads)
    }

    @Test
    fun onButUnpairedIsLegacy() {
        assertNull(session.headerFor(hub, launch))
        assertEquals(emptyList<String>(), host.calls)
    }

    @Test
    fun pairingSendsTheKeyOnceAndStoresThePairing() {
        paired()
        assertEquals(listOf("/session/pair"), host.calls)
        assertEquals(store.secret, host.key)
        assertEquals(64, store.secret!!.length)
        assertEquals(listOf("games", "tv", "vod"), store.pairing!!.permissions)
        val r = session.pair(hub, "000000", "onn fixture")
        assertEquals(IdentitySession.PairResult.Refused(403, "pairing-bad-code"), r)
    }

    @Test
    fun rePairReplacesTheSecretOnlyWhenAsked() {
        paired()
        val first = store.secret
        session.pair(hub, "123456", "onn fixture")
        assertEquals(first, store.secret)
        session.pair(hub, "123456", "onn fixture", newSecret = true)
        assertTrue(first != store.secret)
    }

    @Test
    fun headerByPermissionAndDeclaredEndpoints() {
        paired()
        val token = session.headerFor(hub, launch)
        assertNotNull(token)
        assertEquals(listOf("/session/pair", "/session/nonce", "/session/setup"), host.calls)
        val setupBody = host.bodies.last()
        assertEquals(localAddress, SessionProtocol.jsonStringField(setupBody, "media_host"))
        assertEquals(48100L, SessionProtocol.jsonLongField(setupBody, "video_port"))
        assertEquals(48101L, SessionProtocol.jsonLongField(setupBody, "audio_port"))
        // reused, no new setup
        assertEquals(token, session.headerFor(hub, "http://$hub:8765/plugins/games/native-stream-heartbeat"))
        assertEquals(token, session.headerFor(hub, "http://$hub:8765/sources"))
        // not sent where the host would deny it
        assertNull(session.headerFor(hub, "http://$hub:8765/status"))
        assertNull(session.headerFor(hub, "http://$hub:8765/diagnostics/health"))
        assertEquals(3, host.calls.size)
    }

    @Test
    fun refreshBeforeExpiry() {
        paired()
        val t1 = session.headerFor(hub, launch)
        now += 28_800_000L - SessionProtocol.REFRESH_MARGIN_MS - 1_000L
        assertEquals(t1, session.headerFor(hub, launch))
        now += 2_000L
        val t2 = session.headerFor(hub, launch)
        assertTrue(t1 != t2)
        assertEquals(5, host.calls.size)
    }

    @Test
    fun oneRetryOnATokenRefusalThenVisible() {
        paired()
        session.headerFor(hub, launch)
        val expired = "{\n  \"ok\": false,\n  \"error\": \"session refused\",\n  \"reason\": \"token-expired\"\n}"
        assertTrue(session.onResponse(401, expired, 0))
        assertTrue(refusals.isEmpty())
        assertNotNull(session.headerFor(hub, launch))     // a fresh setup
        assertFalse(session.onResponse(401, expired, 1))
        assertEquals(listOf("token-expired"), refusals)
        assertEquals("token-expired", session.lastReason)
        assertEquals("Session refused (401): token-expired", session.refusalMessage(401, expired))
    }

    @Test
    fun permissionRefusalIsShownNotRetried() {
        paired()
        assertFalse(session.onResponse(403, "{\"reason\": \"permission-denied\"}", 0))
        assertEquals(listOf("permission-denied"), refusals)
        assertFalse(session.onResponse(500, "{\"error\": \"x\"}", 0))
        assertEquals(1, refusals.size)
    }

    @Test
    fun refusedSetupFailsClosedWithCooldown() {
        paired()
        host.refuseSetupWith = "bad-signature"
        try {
            session.headerFor(hub, launch); fail("expected a refusal")
        } catch (e: IdentitySession.IdentityRefused) {
            assertEquals("bad-signature", e.reason)
        }
        val calls = host.calls.size
        try {
            session.headerFor(hub, launch); fail("expected a refusal")
        } catch (e: IdentitySession.IdentityRefused) {
            assertEquals("bad-signature", e.reason)
        }
        assertEquals("no storm inside the cooldown", calls, host.calls.size)
        now += IdentitySession.SETUP_COOLDOWN_MS + 1
        host.refuseSetupWith = null
        assertNotNull(session.headerFor(hub, launch))
    }

    @Test
    fun hostWithoutTheIdentityLayerStillWorks() {
        paired()
        host.identityLayer = false
        assertNull(session.headerFor(hub, launch))
        assertNull(session.headerFor(hub, launch))
        assertEquals(listOf("/session/pair", "/session/nonce"), host.calls)
        assertEquals("paired; host identity off", session.stateText)
    }

    @Test
    fun noSecretTokenOrAddressInLogs() {
        paired()
        val t = session.headerFor(hub, launch)!!
        session.onResponse(401, "{\"reason\": \"token-unknown\"}", 1)
        assertTrue(logs.isNotEmpty())
        for (line in logs) {
            assertFalse(line, line.contains(store.secret!!))
            assertFalse(line, line.contains(t))
            assertFalse(line, line.contains(localAddress))
            assertFalse(line, line.contains(hub))
        }
    }

    // ---- G3-S3 ----------------------------------------------------------------

    @Test
    fun setupSignsV2AndDeclaresTheOverlayAddressWhenPresent() {
        paired()
        session.headerFor(hub, launch)
        var body = host.bodies.last()
        assertEquals(2L, SessionProtocol.jsonLongField(body, "sig_v"))
        assertNull(SessionProtocol.jsonStringField(body, "overlay_host"))
        session.endSessionLocally()
        overlay = overlayAddress
        assertNotNull(session.headerFor(hub, launch))      // the fake host verified the v2 signature
        body = host.bodies.last()
        assertEquals(overlayAddress, SessionProtocol.jsonStringField(body, "overlay_host"))
        assertEquals(localAddress, SessionProtocol.jsonStringField(body, "media_host"))
        // an address outside the overlay block is never declared as the overlay one
        session.endSessionLocally()
        overlay = localAddress
        session.headerFor(hub, launch)
        assertNull(SessionProtocol.jsonStringField(host.bodies.last(), "overlay_host"))
        for (line in logs) {
            assertFalse(line, line.contains(overlayAddress))
            assertFalse(line, line.contains(localAddress))
        }
    }

    @Test
    fun diagnosticsWhenTheHostGrantsIt() {
        host.grant = listOf("games", "tv", "vod", "diagnostics")
        paired()                                   // the pairing listed games, tv, vod
        assertNotNull(session.headerFor(hub, "http://$hub:8765/status"))
        assertNotNull(session.headerFor(hub, "http://$hub:8765/diagnostics/health"))
        assertNotNull(session.headerFor(hub, "http://$hub:8765/diagnostics/client-health"))
        // the host's grant became the stored record
        assertEquals(listOf("games", "tv", "vod", "diagnostics"), store.pairing!!.permissions)
        assertEquals(listOf("/session/pair", "/session/nonce", "/session/setup"), host.calls)
    }

    @Test
    fun tvAndEpgCarryTheToken() {
        paired()
        val t = session.headerFor(hub, launch)
        for (path in listOf("/plugins/tv_state/state", "/plugins/epg/guide?channel_id=x", "/plugins/epg/prefetch", "/sources"))
            assertEquals(path, t, session.headerFor(hub, "http://$hub:8765$path"))
    }

    @Test
    fun mediaHeaderAndMediaToken() {
        paired()
        val header = session.mediaHeaderFor(hub)
        assertNotNull(header)
        assertEquals(header, session.headerFor(hub, launch))   // the same session token
        assertTrue(session.mediaTokenFor(hub)!!.startsWith("mtok-"))
        assertTrue(session.mediaTokenFor(hub) != header)
        on = false
        assertNull(session.mediaHeaderFor(hub))
        assertNull(session.mediaTokenFor(hub))
    }

    @Test
    fun noMediaHeaderWithoutVod() {
        host.grant = listOf("games", "tv")
        paired()
        assertNull(session.mediaHeaderFor(hub))
        assertNotNull(session.headerFor(hub, launch))
    }

    @Test
    fun portMismatchIsShownNotRetried() {
        paired()
        val body = "{\n  \"ok\": false,\n  \"error\": \"session refused\",\n  \"reason\": \"endpoint-port-mismatch\"\n}"
        assertFalse(session.onResponse(403, body, 0))
        assertEquals(listOf("endpoint-port-mismatch"), refusals)
        assertEquals("Session refused (403): endpoint-port-mismatch", session.refusalMessage(403, body))
    }

    @Test
    fun hubHostAndHubOnlyMedia() {
        assertEquals("companion", SessionProtocol.effectiveHost(false, "hub.tailnet.invalid", "companion"))
        assertEquals("companion", SessionProtocol.effectiveHost(true, "", "companion"))
        assertEquals("companion", SessionProtocol.effectiveHost(true, "  ", "companion"))
        assertEquals("hub.tailnet.invalid", SessionProtocol.effectiveHost(true, " hub.tailnet.invalid ", "companion"))
        assertTrue(SessionProtocol.isHubMediaUrl("http://$hub:8000/vod/a.mp4", hub, 8000))
        assertTrue(SessionProtocol.isHubMediaUrl("http://HUB.invalid:8000/live/s.m3u8", hub, 8000))
        assertFalse(SessionProtocol.isHubMediaUrl("http://$hub:8765/plugins/games/status", hub, 8000))
        assertFalse(SessionProtocol.isHubMediaUrl("https://iptv.example.invalid/live.m3u8", hub, 8000))
        assertFalse(SessionProtocol.isHubMediaUrl("http://iptv.example.invalid:8000/x", hub, 8000))
        assertFalse(SessionProtocol.isHubMediaUrl("http://$hub.evil.invalid:8000/x", hub, 8000))
        assertFalse(SessionProtocol.isHubMediaUrl("not a url", hub, 8000))
        assertFalse(SessionProtocol.isHubMediaUrl("http://$hub:8000/x", "", 8000))
    }

    @Test
    fun urlForLogHidesTheHost() {
        val line = SessionProtocol.urlForLog("http://hub.tailnet.invalid:8000/vod/a.mp4")
        assertFalse(line, line.contains("hub.tailnet.invalid"))
        assertTrue(line, line.startsWith("http://h-") && line.endsWith(":8000/vod/a.mp4"))
        assertEquals(12, SessionProtocol.hostHash("x").length)
        assertFalse(SessionProtocol.urlForLog("http://$localAddress:8000/v").contains(localAddress))
    }
}
