package com.safeiot.privyhub.identity

import java.math.BigInteger
import java.net.InetAddress
import java.security.MessageDigest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * G3-S2: the client's protocol bytes against G3-S1's own vectors
 * (`resources/g3_s2/setup_vectors.json`, made by G3-S1's `sign()` and
 * `SessionGate`; addresses given as integers and built here).
 */
@Suppress("UNCHECKED_CAST")
class SessionProtocolTest {

    companion object {
        val doc: Map<String, Any?> by lazy {
            val text = SessionProtocolTest::class.java.classLoader!!
                .getResource("g3_s2/setup_vectors.json")!!.readText()
            MiniJson.parse(text) as Map<String, Any?>
        }

        fun hostOf(spec: Map<String, Any?>): String =
            (spec["ipv4_int"] as String?)?.let {
                val v = BigInteger(it.removePrefix("0x").removePrefix("0X"), 16).toInt()
                InetAddress.getByAddress(
                    byteArrayOf((v ushr 24).toByte(), (v ushr 16).toByte(), (v ushr 8).toByte(), v.toByte())
                ).hostAddress!!
            } ?: spec["text"] as String

        fun sha256Hex(s: String): String =
            SessionProtocol.bytesToHex(MessageDigest.getInstance("SHA-256").digest(s.toByteArray(Charsets.UTF_8)))

        fun response(name: String): Pair<Int, String> {
            val r = (doc["host_responses"] as Map<String, Any?>)[name] as Map<String, Any?>
            return (r["status"] as Long).toInt() to (r["body"] as String)
        }
    }

    private val vectors get() = doc["vectors"] as List<Map<String, Any?>>

    @Test
    fun constantsMatchTheHost() {
        assertEquals(doc["setup_canon"], SessionProtocol.SETUP_CANON)
        assertEquals(doc["header"], SessionProtocol.HEADER)
    }

    @Test
    fun hmacInputAndSignatureMatchEveryVector() {
        assertEquals(3, vectors.size)
        for (v in vectors) {
            val host = hostOf(v["media_host"] as Map<String, Any?>)
            val port = (v["video_port"] as Long).toInt()
            val canon = SessionProtocol.setupCanonical(v["device_id"] as String, v["nonce"] as String, host, port)
            assertEquals(v["name"] as String, v["canonical_sha256"], sha256Hex(canon))
            assertEquals(v["name"] as String, (v["canonical_bytes"] as Long).toInt(), canon.toByteArray().size)
            assertEquals(
                v["name"] as String,
                v["sig"],
                SessionProtocol.sign(v["key_hex"] as String, v["device_id"] as String, v["nonce"] as String, host, port),
            )
        }
    }

    @Test
    fun setupBodyShape() {
        val v = vectors[1]
        val host = hostOf(v["media_host"] as Map<String, Any?>)
        val body = SessionProtocol.setupBody(v["device_id"] as String, v["nonce"] as String, host, 48100, 48101, v["sig"] as String)
        val parsed = MiniJson.parse(body) as Map<String, Any?>
        assertEquals(listOf("device_id", "nonce", "media_host", "video_port", "audio_port", "sig"), parsed.keys.toList())
        assertEquals(48100L, parsed["video_port"])
        assertEquals(48101L, parsed["audio_port"])
        assertEquals(host, parsed["media_host"])
        assertEquals(v["sig"], parsed["sig"])
    }

    @Test
    fun pairBodyEscapes() {
        val name = "onn \"living room\" \\ tab\t"
        val parsed = MiniJson.parse(SessionProtocol.pairBody("012345", name, "ab".repeat(32))) as Map<String, Any?>
        assertEquals(listOf("code", "device_name", "key"), parsed.keys.toList())
        assertEquals(name, parsed["device_name"])
    }

    @Test
    fun permissionMapMatchesTheHost() {
        for ((path, permission) in doc["permission_paths"] as Map<String, Any?>) {
            assertEquals(path, permission, SessionProtocol.requiredPermission(path))
        }
        assertEquals("/plugins/games/launch", SessionProtocol.pathOf("http://hub.invalid:8765/plugins/games/launch?id=x"))
    }

    @Test
    fun hostResponsesParse() {
        val (st, nonce) = response("nonce_ok")
        assertEquals(200, st)
        assertTrue(SessionProtocol.jsonStringField(nonce, "nonce")!!.length >= 24)
        val (_, setup) = response("setup_ok")
        assertTrue(SessionProtocol.jsonStringField(setup, "token")!!.isNotEmpty())
        assertEquals(doc["token_ttl_s"], SessionProtocol.jsonLongField(setup, "expires_in_s"))
        assertEquals(listOf("games", "tv", "vod"), SessionProtocol.jsonStringArray(setup, "permissions"))
        val (_, pair) = response("pair_ok")
        assertTrue(SessionProtocol.jsonStringField(pair, "device_id")!!.startsWith("dev-"))
        assertEquals("pairing-closed", SessionProtocol.reasonOf(response("pair_closed").second))
        assertEquals("nonce-unknown", SessionProtocol.reasonOf(response("setup_nonce_unknown").second))
        assertEquals("legacy-overlay", SessionProtocol.reasonOf(response("legacy_overlay").second))
        assertEquals("permission-unknown", SessionProtocol.reasonOf(response("permission_unknown").second))
        assertEquals("token-expired", SessionProtocol.reasonOf(response("token_expired").second))
        assertEquals(404, response("host_flag_off_nonce").first)
        assertNull(SessionProtocol.reasonOf(response("host_flag_off_nonce").second))
    }
}
