package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.net.SocketTimeoutException
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * G6-HM2: NativeControllerSender.writePlayerState (design `g6_hm1_2026-11-19` §3), read back from the real send loop
 * over loopback (the PHI1 packet as the hub reads it). The loop keeps sending every player whatever is written.
 */
class G6SenderWriteTest {

    private data class Phi1(val player: Int, val buttons: Int, val lx: Int, val ly: Int, val rx: Int, val ry: Int,
                            val lt: Int, val rt: Int)

    private fun parse(b: ByteArray, n: Int): Phi1? {
        if (n != 36 || b[0] != 'P'.code.toByte() || b[3] != '1'.code.toByte()) return null
        val bb = ByteBuffer.wrap(b, 0, n).order(ByteOrder.LITTLE_ENDIAN)
        val player = bb.get(5).toInt()
        bb.position(20)
        return Phi1(player, bb.int, bb.short.toInt(), bb.short.toInt(), bb.short.toInt(), bb.short.toInt(),
            bb.short.toInt(), bb.short.toInt())
    }

    /** The next packets for [player] seen within [ms] (the newest last). */
    private fun read(sock: DatagramSocket, player: Int, ms: Long): List<Phi1> {
        val out = ArrayList<Phi1>()
        val until = System.currentTimeMillis() + ms
        val buf = ByteArray(64)
        while (System.currentTimeMillis() < until) {
            val p = DatagramPacket(buf, buf.size)
            try { sock.receive(p) } catch (_: SocketTimeoutException) { continue }
            parse(p.data, p.length)?.takeIf { it.player == player }?.let { out.add(it) }
        }
        return out
    }

    private fun withSender(block: (NativeControllerSender, DatagramSocket) -> Unit) {
        DatagramSocket(0, InetAddress.getLoopbackAddress()).use { sock ->
            sock.soTimeout = 50
            val sender = NativeControllerSender(InetAddress.getLoopbackAddress().hostAddress!!, sock.localPort)
            sender.start()
            try { block(sender, sock) } finally { sender.stop() }
        }
    }

    @Test
    fun aWrittenStateIsSentForThatPlayerOnly() = withSender { sender, sock ->
        assertTrue(sender.writePlayerState(1, TouchPadState.XUSB_A or TouchPadState.XUSB_DPAD_UP,
            0, 1234, 0, -1234, 255, 300))
        read(sock, 1, 150)                                                // let older packets pass
        val p1 = read(sock, 1, 200).last()
        assertEquals(TouchPadState.XUSB_A or TouchPadState.XUSB_DPAD_UP, p1.buttons)
        assertEquals(1234, p1.ly); assertEquals(-1234, p1.ry)
        assertEquals(255, p1.lt); assertEquals(255, p1.rt)               // clamped to 255
        val p0 = read(sock, 0, 200).last()
        assertEquals(Phi1(0, 0, 0, 0, 0, 0, 0, 0), p0)                   // the other players untouched
    }

    @Test
    fun neutralizeClearsAWrittenStateAndTheLoopKeepsSending() = withSender { sender, sock ->
        sender.writePlayerState(2, TouchPadState.XUSB_START, 0, 0, 0, 0, 0, 255)
        read(sock, 2, 150)
        assertEquals(TouchPadState.XUSB_START, read(sock, 2, 200).last().buttons)
        sender.neutralize()
        read(sock, 2, 100)
        val after = read(sock, 2, 300)
        assertTrue("the loop keeps sending (never silent): ${after.size}", after.size >= 10)
        assertEquals(Phi1(2, 0, 0, 0, 0, 0, 0, 0), after.last())
    }

    @Test
    fun aPlayerOutsideTheFourIsRefused() = withSender { sender, _ ->
        assertFalse(sender.writePlayerState(-1, 1, 0, 0, 0, 0, 0, 0))
        assertFalse(sender.writePlayerState(4, 1, 0, 0, 0, 0, 0, 0))
    }
}
