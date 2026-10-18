package com.safeiot.privyhub.identity

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * CL-B4: the v3 setup bytes against the host's own vectors
 * (`resources/cl_b4/setup_vectors_v3.json`, made by
 * `docs/memory/evidence/cl_b4_2026-10-18/make_vectors_v3.py`: each body, in
 * the exact form [SessionProtocol.setupBodyV3] writes, was accepted by the
 * host's `SessionGate._setup` in process, with `token_issued` at sig_v 3).
 */
@Suppress("UNCHECKED_CAST")
class SessionProtocolV3Test {

    private val doc: Map<String, Any?> by lazy {
        val text = SessionProtocolV3Test::class.java.classLoader!!
            .getResource("cl_b4/setup_vectors_v3.json")!!.readText()
        MiniJson.parse(text) as Map<String, Any?>
    }

    private val vectors get() = doc["vectors"] as List<Map<String, Any?>>

    @Test
    fun constantsMatchTheHost() {
        assertEquals(doc["setup_canon_v3"], SessionProtocol.SETUP_CANON_V3)
        assertEquals(listOf("opus"), SessionProtocol.AUDIO_CODECS)
    }

    @Test
    fun canonSignatureAndBodyMatchEveryHostAcceptedVector() {
        assertEquals(3, vectors.size)
        for (v in vectors) {
            val name = v["name"] as String
            assertEquals(name, true, v["host_accepted"])
            val media = SessionProtocolV2Test.ip(v["media_host"])!!
            val overlay = SessionProtocolV2Test.ip(v["overlay_host"])
            val video = (v["video_port"] as Long).toInt()
            val audio = (v["audio_port"] as Long).toInt()
            val codecs = v["audio_codecs"] as List<String>
            val device = v["device_id"] as String
            val nonce = v["nonce"] as String
            val canon = SessionProtocol.setupCanonicalV3(device, nonce, media, video, audio, overlay, codecs)
            assertEquals(name, v["canonical_sha256"], SessionProtocolTest.sha256Hex(canon))
            assertEquals(name, (v["canonical_bytes"] as Long).toInt(), canon.toByteArray().size)
            val sig = SessionProtocol.signV3(v["key_hex"] as String, device, nonce, media, video, audio, overlay, codecs)
            assertEquals(name, v["sig"], sig)
            val body = SessionProtocol.setupBodyV3(device, nonce, media, video, audio, overlay, codecs, sig)
            assertEquals(name, v["body_sha256"], SessionProtocolTest.sha256Hex(body))
        }
    }

    @Test
    fun theFixedVector() {
        // The same inputs and digest as the host's tests/session_identity/test_cl_b4_sig_v3.py.
        val canon = SessionProtocol.setupCanonicalV3("dev-fixture", "nonce-fixture", "media-host", 48100, 48101, null, listOf("opus"))
        assertEquals("privyhub-session-setup-v3\ndev-fixture\nnonce-fixture\nmedia-host\n48100\n48101\n\nopus", canon)
        assertEquals(
            "c3b6e94a4c75b7ba9b25098d1aac482a8d471905acc05070b8a50161eb90db6e",
            SessionProtocol.hmacSha256Hex("11".repeat(32), canon),
        )
    }

    @Test
    fun v2IsUnchanged() {
        val v2 = SessionProtocol.setupBodyV2("d", "n", "m", 1, 2, null, "s")
        assertEquals("{\"device_id\":\"d\",\"nonce\":\"n\",\"media_host\":\"m\",\"video_port\":1,\"audio_port\":2,\"sig_v\":2,\"sig\":\"s\"}", v2)
        assertTrue(!v2.contains("audio_codecs"))
    }
}
