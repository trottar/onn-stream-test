package com.safeiot.privyhub.identity

import java.math.BigInteger
import java.net.InetAddress
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * G3-S3: the v2 setup bytes against the host's own vectors
 * (`resources/g3_s3/setup_vectors_v2.json`, made by
 * `docs/memory/evidence/g3_s3_2026-10-16/make_vectors_v2.py`: each vector was
 * accepted by the host's `SessionGate._setup` in process). Addresses are
 * given as integers and built here.
 */
@Suppress("UNCHECKED_CAST")
class SessionProtocolV2Test {

    companion object {
        val doc: Map<String, Any?> by lazy {
            val text = SessionProtocolV2Test::class.java.classLoader!!
                .getResource("g3_s3/setup_vectors_v2.json")!!.readText()
            MiniJson.parse(text) as Map<String, Any?>
        }

        fun ip(hexint: Any?): String? =
            (hexint as String?)?.let {
                val v = BigInteger(it.removePrefix("0x").removePrefix("0X"), 16).toInt()
                InetAddress.getByAddress(
                    byteArrayOf((v ushr 24).toByte(), (v ushr 16).toByte(), (v ushr 8).toByte(), v.toByte())
                ).hostAddress!!
            }

        fun body(name: String): String = (doc["host_bodies"] as Map<String, Any?>)[name] as String
    }

    private val vectors get() = doc["vectors"] as List<Map<String, Any?>>

    @Test
    fun constantsMatchTheHost() {
        assertEquals(doc["setup_canon_v2"], SessionProtocol.SETUP_CANON_V2)
        assertEquals(doc["media_permission"], SessionProtocol.MEDIA_PERMISSION)
        assertEquals(doc["media_token_param"], SessionProtocol.MEDIA_TOKEN_PARAM)
        val implied = (doc["default_paired_permissions"] as List<String>).toSet() - setOf("games", "tv", "vod")
        assertEquals(implied, SessionProtocol.IMPLIED_FOR_PAIRED)
    }

    @Test
    fun canonAndSignatureMatchEveryHostAcceptedVector() {
        assertEquals(3, vectors.size)
        for (v in vectors) {
            val name = v["name"] as String
            assertEquals(name, true, v["host_accepted"])
            val media = ip(v["media_host"])!!
            val overlay = ip(v["overlay_host"])
            val video = (v["video_port"] as Long).toInt()
            val audio = (v["audio_port"] as Long).toInt()
            val canon = SessionProtocol.setupCanonicalV2(v["device_id"] as String, v["nonce"] as String, media, video, audio, overlay)
            assertEquals(name, v["canonical_sha256"], SessionProtocolTest.sha256Hex(canon))
            assertEquals(name, (v["canonical_bytes"] as Long).toInt(), canon.toByteArray().size)
            assertEquals(
                name,
                v["sig"],
                SessionProtocol.signV2(v["key_hex"] as String, v["device_id"] as String, v["nonce"] as String, media, video, audio, overlay),
            )
            overlay?.let { assertTrue(name, SessionProtocol.isOverlayIpv4(it)) }
        }
    }

    @Test
    fun setupBodyV2Shape() {
        val v = vectors[1]
        val media = ip(v["media_host"])!!
        val overlay = ip(v["overlay_host"])!!
        val parsed = MiniJson.parse(
            SessionProtocol.setupBodyV2(v["device_id"] as String, v["nonce"] as String, media, 48100, 48101, overlay, v["sig"] as String)
        ) as Map<String, Any?>
        assertEquals(
            listOf("device_id", "nonce", "media_host", "video_port", "audio_port", "overlay_host", "sig_v", "sig"),
            parsed.keys.toList(),
        )
        assertEquals(2L, parsed["sig_v"])
        assertEquals(overlay, parsed["overlay_host"])
        val without = MiniJson.parse(
            SessionProtocol.setupBodyV2("d", "n", media, 48100, 48101, null, "s")
        ) as Map<String, Any?>
        assertFalse(without.containsKey("overlay_host"))
    }

    @Test
    fun overlayBlock() {
        assertTrue(SessionProtocol.isOverlayIpv4(ip("0x64400000")!!))
        assertTrue(SessionProtocol.isOverlayIpv4(ip("0x647FFFFF")!!))
        assertFalse(SessionProtocol.isOverlayIpv4(ip("0x64800000")!!))
        assertFalse(SessionProtocol.isOverlayIpv4(ip("0x643FFFFF")!!))
        assertFalse(SessionProtocol.isOverlayIpv4(ip("0xC0A86439")!!))
        assertFalse(SessionProtocol.isOverlayIpv4("hub.invalid"))
        assertFalse(SessionProtocol.isOverlayIpv4("1.2.3"))
    }

    @Test
    fun permissionMapMatchesTheHost() {
        for ((path, permission) in doc["permission_map"] as Map<String, Any?>) {
            assertEquals(path, permission, SessionProtocol.requiredPermission(path))
        }
    }

    @Test
    fun hostBodiesParse() {
        val ok = body("setup_ok_v2")
        assertEquals("fixture-media-token", SessionProtocol.jsonStringField(ok, "media_token"))
        assertEquals("fixture-token", SessionProtocol.jsonStringField(ok, "token"))
        assertEquals(listOf("games", "tv", "vod", "diagnostics"), SessionProtocol.jsonStringArray(ok, "permissions"))
        assertEquals("endpoint-port-mismatch", SessionProtocol.reasonOf(body("port_mismatch")))
        assertEquals("media-token-unknown", SessionProtocol.reasonOf(body("media_token_unknown")))
        assertEquals("permission-denied", SessionProtocol.reasonOf(body("diagnostics_denied")))
    }
}
