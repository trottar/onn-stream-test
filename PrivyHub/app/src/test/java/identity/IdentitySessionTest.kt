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
                    val expected = SessionProtocol.sign(
                        key!!, SessionProtocol.jsonStringField(b, "device_id")!!, nonce,
                        SessionProtocol.jsonStringField(b, "media_host")!!, SessionProtocol.jsonLongField(b, "video_port")!!.toInt(),
                    )
                    if (expected != SessionProtocol.jsonStringField(b, "sig"))
                        return 401 to "{\"ok\": false, \"error\": \"session refused\", \"reason\": \"bad-signature\"}"
                    200 to "{\n  \"ok\": true,\n  \"token\": \"tok-${++counter}\",\n  \"expires_in_s\": 28800,\n  \"client_id\": \"dev-00112233aabbccdd\",\n  \"permissions\": [\n    \"games\",\n    \"tv\",\n    \"vod\"\n  ]\n}"
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
    private val session = IdentitySession(
        enabled = { on },
        store = store,
        transport = host,
        routes = { _, _ -> localAddress },
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
}
