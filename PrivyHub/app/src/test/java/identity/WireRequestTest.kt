package com.safeiot.privyhub.identity

import java.io.ByteArrayOutputStream
import java.net.HttpURLConnection
import java.net.InetAddress
import java.net.ServerSocket
import java.net.URL
import kotlin.concurrent.thread
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * G3-S2: the bytes on the wire. A control POST is built exactly as
 * `MainActivity.httpPost` builds it, captured raw by a loopback socket, with
 * and without the identity hook. Off = today's request, byte for byte; on and
 * paired = the same request plus one `X-PrivyHub-Session` line.
 */
class WireRequestTest {

    private fun capture(build: (HttpURLConnection, String) -> Unit): String {
        ServerSocket(0, 1, InetAddress.getLoopbackAddress()).use { server ->
            val got = ByteArrayOutputStream()
            val t = thread {
                server.accept().use { s ->
                    val input = s.getInputStream()
                    val buf = ByteArray(1)
                    while (true) {
                        if (input.read(buf) < 0) break
                        got.write(buf[0].toInt())
                        if (got.toString(Charsets.ISO_8859_1.name()).endsWith("\r\n\r\n")) break
                    }
                    s.getOutputStream().write(
                        "HTTP/1.0 200 OK\r\nContent-Type: application/json\r\nContent-Length: 2\r\n\r\n{}".toByteArray()
                    )
                }
            }
            val url = "http://localhost:${server.localPort}/plugins/games/launch?id=fixture"
            val c = URL(url).openConnection() as HttpURLConnection
            try {
                // MainActivity.httpPost's request, field by field.
                c.requestMethod = "POST"
                c.connectTimeout = 2_000
                c.readTimeout = 5_000
                c.useCaches = false
                c.doOutput = false
                c.setRequestProperty("Content-Length", "0")
                c.setRequestProperty("Cache-Control", "no-cache")
                build(c, url)
                assertEquals(200, c.responseCode)
                c.inputStream.close()
            } finally {
                c.disconnect()
            }
            t.join(5_000)
            return got.toString(Charsets.ISO_8859_1.name())
        }
    }

    private fun normalisePort(raw: String): String = raw.replace(Regex("localhost:\\d+"), "localhost:<port>")

    private fun pairedSession(): IdentitySession {
        var counter = 0
        var key: String? = null
        val store = object : IdentitySession.IdentityStore {
            var secret: String? = null
            var pairing: IdentitySession.Pairing? = null
            override fun secretHex() = secret
            override fun saveSecretHex(hex: String) { secret = hex }
            override fun pairing() = pairing
            override fun savePairing(pairing: IdentitySession.Pairing) { this.pairing = pairing }
        }
        val session = IdentitySession(
            enabled = { true },
            store = store,
            transport = { url, body ->
                when (SessionProtocol.pathOf(url)) {
                    "/session/pair" -> { key = SessionProtocol.jsonStringField(body!!, "key")
                        200 to "{\"device_id\": \"dev-0011223344556677\", \"permissions\": [\"games\", \"tv\", \"vod\"]}" }
                    "/session/nonce" -> 200 to "{\"nonce\": \"n-${++counter}\"}"
                    else -> 200 to "{\"token\": \"tok-wire\", \"expires_in_s\": 28800, \"permissions\": [\"games\", \"tv\", \"vod\"]}"
                }
            },
            routes = { _, _ -> "media-host-fixture" },
            clock = { 0L },
            randomBytes = { n -> ByteArray(n) { it.toByte() } },
        )
        session.pair("localhost", "123456", "wire fixture")
        assertTrue(key != null)
        return session
    }

    @Test
    fun offIsTodayByteForByte() {
        val today = normalisePort(capture { _, _ -> })
        var touched = false
        val off = normalisePort(capture { c, url -> decorateConnection(c, url, false) { touched = true; pairedSession() } })
        assertEquals(today, off)
        assertFalse("the session is not even built when off", touched)
        assertFalse(today.contains(SessionProtocol.HEADER))
    }

    @Test
    fun onAndPairedAddsOnlyTheHeader() {
        val session = pairedSession()
        val today = normalisePort(capture { _, _ -> })
        val on = normalisePort(capture { c, url -> decorateConnection(c, url, true) { session } })
        assertTrue(on.contains("${SessionProtocol.HEADER}: tok-wire\r\n"))
        val without = on.split("\r\n").filterNot { it.startsWith(SessionProtocol.HEADER + ":") }.joinToString("\r\n")
        assertEquals(today, without)
    }
}
