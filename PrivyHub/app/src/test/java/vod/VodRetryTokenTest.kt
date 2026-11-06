package com.safeiot.privyhub.vod

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B43: the movie retry made real, on a discrete-time simulation (ms):
 *  - a fake hub: down (no answer: a reset), refusing every new request for a window (B40's `drop <seconds>`: a
 *    reset), or up; a companion restart ends its sessions, so the onn's cached token is refused (401) until refetched;
 *  - a fake Media3 progressive loader with B43's settled policy (DefaultLoadErrorHandlingPolicy 1.11.0: retry after
 *    min((n-1) x 1000, 5000) ms; the error surfaces only when the buffer is spent and errorCount > 3; progress resets
 *    the count), playing from a 30-s buffer (the VOD load control's maximum);
 *  - the controller's own scheduler, and a fake token port (the identity session's drop + fresh setup).
 * B35's VodRetryTest stays unedited and green beside this.
 */
class VodRetryTokenTest {

    private class Sim {
        var now = 0L
        private val events = mutableListOf<Triple<Long, Int, () -> Unit>>()
        private var seq = 0
        fun at(t: Long, tag: Int = 0, task: () -> Unit) { events.add(Triple(t, tag + (seq++ shl 4), task)) }
        fun cancelTag(tag: Int) { events.removeAll { (it.second and 0xF) == tag } }
        fun runUntil(t: Long) {
            while (true) {
                val next = events.filter { it.first <= t }.minWithOrNull(compareBy({ it.first }, { it.second shr 4 })) ?: break
                events.remove(next)
                now = next.first
                next.third()
            }
            now = t
        }
    }

    private class Hub(val sim: Sim) {
        var downUntil = -1L          // no answer before this
        var refuseUntil = -1L        // B40's window: every new request reset before this
        var sessionEpoch = 0         // a companion restart ends every session
        var refuseForever = false    // the token always refused (a revoked pairing)
        fun restart(downMs: Long) { downUntil = sim.now + downMs; sessionEpoch++ }
        /** null = served; else (Media3 code, reason) of the failure. */
        fun request(tokenEpoch: Int): Pair<Int, String>? = when {
            sim.now < downUntil -> 2001 to VodRetryPolicy.REASON_RESET
            sim.now < refuseUntil -> 2001 to VodRetryPolicy.REASON_RESET
            refuseForever || tokenEpoch != sessionEpoch -> 2004 to VodRetryPolicy.REASON_401
            else -> null
        }
        fun up(): Boolean = sim.now >= downUntil
    }

    private class Rig(sim: Sim, val hub: Hub, withToken: Boolean = true) {
        val sim = sim
        val rows = mutableListOf<Map<String, Any>>()
        var tokenEpoch = 0
        var refreshes = 0
        var offered = mutableListOf<String>()
        var position = 0L
        var playing = true
        var bufferedToMs = 30_000L     // the media position the buffer reaches
        var loaderErrors = 0
        var surfaced = 0
        var retriesAt = mutableListOf<Long>()
        lateinit var c: VodRetryController

        init {
            val scheduler = object : VodRetryController.Scheduler {
                override fun schedule(delayMs: Long, task: () -> Unit) = sim.at(sim.now + delayMs, 1, task)
                override fun cancel() = sim.cancelTag(1)
            }
            val ui = object : VodRetryController.Ui {
                override fun showMark(attempt: Int) {}
                override fun hideMark() {}
                override fun offerRetry() { offered.add("b35") }
                override fun offerRetry(kind: String) { offered.add(kind) }
            }
            val player = object : VodRetryController.Player {
                override fun retryAt(positionMs: Long) {
                    retriesAt.add(positionMs)
                    position = positionMs
                    sim.at(sim.now + 100) { attemptOnce() }
                }
            }
            val token = object : VodRetryController.Token {
                override fun refresh(done: (Boolean) -> Unit) {
                    refreshes++
                    sim.at(sim.now + 50) {
                        val ok = hub.up()
                        if (ok) tokenEpoch = hub.sessionEpoch
                        done(ok)
                    }
                }
            }
            c = VodRetryController(VodRetryPolicy(), player, scheduler, { sim.now }, { rows.add(it) }, ui,
                "movie-b", if (withToken) token else null)
        }

        /** B35's retry: one load; READY or the error back to the controller. */
        private fun attemptOnce() {
            val fail = hub.request(tokenEpoch)
            if (fail == null) {
                playing = true
                bufferedToMs = position + 30_000L
                c.onReady()
            } else {
                c.onError(fail.first, if (fail.first == 2004) "ERROR_CODE_IO_BAD_HTTP_STATUS"
                    else "ERROR_CODE_IO_NETWORK_CONNECTION_FAILED", position, fail.second)
            }
        }

        /** The movie plays in real time; Media3's own loader refills the buffer and retries by its policy. */
        fun playFrom(t0: Long, positionAtT0: Long) {
            position = positionAtT0
            bufferedToMs = positionAtT0 + 30_000L
            tick(t0)
        }

        private fun tick(t: Long) {
            sim.at(t) {
                if (playing) {
                    position += 1_000L
                    if (position >= bufferedToMs) {
                        // the buffer is spent: the loader's error surfaces only past the minimum retry count
                        if (loaderErrors > 3) {
                            playing = false
                            surfaced++
                            val fail = hub.request(tokenEpoch) ?: (2001 to VodRetryPolicy.REASON_RESET)
                            c.onError(fail.first, "ERROR_CODE_IO_NETWORK_CONNECTION_FAILED", position, fail.second)
                            return@at
                        }
                        position -= 1_000L   // stalled (buffering)
                    }
                    tick(t + 1_000L)
                }
            }
        }

        /** The loader: a connection attempt; served = the buffer refilled and the count reset (progress). */
        fun loader(t: Long) {
            sim.at(t) {
                if (!playing) return@at
                if (hub.request(tokenEpoch) == null) {
                    loaderErrors = 0
                    bufferedToMs = position + 30_000L
                    loader(sim.now + 10_000L)       // keeps the buffer topped up
                } else {
                    loaderErrors++
                    loader(sim.now + minOf((loaderErrors - 1) * 1_000L, 5_000L))
                }
            }
        }

        fun events(): List<String> = rows.map { it["event"] as String }
    }

    @Test
    fun aCompanionRestartWithTheMovieOpenTheTokenRefetchedThenResumedAtThePosition() {
        val sim = Sim()
        val hub = Hub(sim)
        val r = Rig(sim, hub)
        // the movie playing at 1 h 50 min; at t=0 the companion restarts: 12 s with no answer, then the old token 401
        hub.restart(12_000L)
        r.c.onError(2001, "ERROR_CODE_IO_NETWORK_CONNECTION_FAILED", 6_600_000L, VodRetryPolicy.REASON_RESET)
        sim.runUntil(200_000L)
        val ev = r.events()
        assertEquals("vod_error", ev.first())
        assertEquals("vod_resumed", ev.last())
        val refused = r.rows.filter { it["reason"] == VodRetryPolicy.REASON_401 }
        assertEquals(1, refused.size)
        assertEquals(true, refused[0]["token_refetched"])
        assertEquals(1, r.refreshes)
        assertTrue(r.retriesAt.all { it == 6_600_000L })
        assertEquals(r.rows.first()["position_ms"], 6_600_000L)
        assertTrue(r.offered.isEmpty())
        assertFalse(r.c.retrying)
        assertTrue((r.rows.last()["elapsed_ms"] as Long) < 30_000L)
    }

    @Test
    fun a45sRefusalThePlayersOwnReconnectGivesUpFirstThenB35RetriesAndResumes() {
        val sim = Sim()
        val hub = Hub(sim)
        val r = Rig(sim, hub)
        r.playFrom(0L, 6_600_000L)
        r.loader(0L)
        sim.runUntil(60_000L)                      // a minute of play, no fault: no rows
        assertTrue(r.rows.isEmpty())
        hub.refuseUntil = sim.now + 45_000L        // `drop 45` at t = 60 s
        sim.runUntil(400_000L)
        assertEquals(1, r.surfaced)                // the player's own reconnect gave up once, after its buffer
        val ev = r.events()
        assertEquals("vod_error", ev.first())
        assertEquals("vod_resumed", ev.last())
        assertTrue(ev.subList(1, ev.size - 1).all { it == "vod_retry" })
        assertTrue(ev.count { it == "vod_retry" } >= 2)
        assertTrue(r.rows.all { it["reason"] == null || it["reason"] == VodRetryPolicy.REASON_RESET })
        val errorAt = r.rows.first()["position_ms"] as Long
        assertTrue(r.retriesAt.all { it == errorAt })
        assertEquals(0, r.refreshes)               // no refusal: no refetch
    }

    @Test
    fun a12sDropTheBufferCoversItNoRowsAsHome2Saw() {
        val sim = Sim()
        val hub = Hub(sim)
        val r = Rig(sim, hub)
        r.playFrom(0L, 1_000_000L)
        r.loader(0L)
        sim.runUntil(60_000L)
        hub.refuseUntil = sim.now + 12_000L
        sim.runUntil(200_000L)
        assertEquals(0, r.surfaced)
        assertTrue(r.rows.isEmpty())
    }

    @Test
    fun theHubDownLostOnlyAfterTheBound() {
        val sim = Sim()
        val hub = Hub(sim)
        val r = Rig(sim, hub)
        hub.restart(10_000_000L)                   // never back within the test
        r.c.onError(2001, "ERROR_CODE_IO_NETWORK_CONNECTION_FAILED", 42_000L, VodRetryPolicy.REASON_RESET)
        sim.runUntil(400_000L)
        val gave = r.rows.last()
        assertEquals("vod_gave_up", gave["event"])
        assertEquals(VodRetryController.KIND_LOST, gave["kind"])
        assertTrue((gave["elapsed_ms"] as Long) > 120_000L)
        r.c.afterTodaysError()
        assertEquals(listOf(VodRetryController.KIND_LOST), r.offered)
    }

    @Test
    fun aRefusalThatPersistsAfterTheRefetchIsRefusedNeverLost() {
        val sim = Sim()
        val hub = Hub(sim)
        hub.refuseForever = true
        val r = Rig(sim, hub)
        r.c.onError(2004, "ERROR_CODE_IO_BAD_HTTP_STATUS", 42_000L, VodRetryPolicy.REASON_401)
        sim.runUntil(400_000L)
        val gave = r.rows.last()
        assertEquals("vod_gave_up", gave["event"])
        assertEquals(VodRetryController.KIND_REFUSED, gave["kind"])
        assertTrue((gave["elapsed_ms"] as Long) < 30_000L)     // not 150 s of futile attempts
        assertEquals(VodRetryPolicy.REFUSALS_MAX, r.refreshes)
        assertTrue(r.rows.filter { it["event"] == "vod_retry" }.all { it["token_refetched"] == true })
        r.c.afterTodaysError()
        assertEquals(listOf(VodRetryController.KIND_REFUSED), r.offered)
    }

    @Test
    fun theRetryButtonRefetchesTheTokenFirst() {
        val sim = Sim()
        val hub = Hub(sim)
        hub.refuseForever = true
        val r = Rig(sim, hub)
        r.c.onError(2004, "ERROR_CODE_IO_BAD_HTTP_STATUS", 42_000L, VodRetryPolicy.REASON_401)
        sim.runUntil(400_000L)
        val before = r.refreshes
        hub.refuseForever = false
        hub.sessionEpoch++                          // the user's Retry after a restart: the old token is dead
        r.c.manualRetry()
        sim.runUntil(500_000L)
        assertEquals(before + 1, r.refreshes)
        assertEquals("vod_resumed", r.events().last())
        val manual = r.rows[r.rows.size - 2]
        assertEquals(1, manual["attempt"])
        assertEquals(true, manual["token_refetched"])
    }

    @Test
    fun withoutTheTokenPortTheRowsAreB35sAsBuilt() {
        val sim = Sim()
        val hub = Hub(sim)
        hub.restart(10_000_000L)
        val r = Rig(sim, hub, withToken = false)
        r.c.onError(2001, "ERROR_CODE_IO_NETWORK_CONNECTION_FAILED", 1L, VodRetryPolicy.REASON_RESET)
        sim.runUntil(400_000L)
        assertTrue(r.rows.none { it.containsKey("reason") || it.containsKey("kind") || it.containsKey("token_refetched") })
        r.c.afterTodaysError()
        assertEquals(listOf("b35"), r.offered)
        // absent: no controller at all (MainActivity builds none without the flag)
        assertFalse(VodRetryController.wanted(false, false))
    }

    @Test
    fun theReasonFromTheCauseChain() {
        assertEquals("401", VodRetryPolicy.reasonOf(2004, 401, false, false))
        assertEquals("403", VodRetryPolicy.reasonOf(2004, 403, false, false))
        assertEquals("reset", VodRetryPolicy.reasonOf(2004, 500, false, false))
        assertEquals("timeout", VodRetryPolicy.reasonOf(2002, null, false, false))
        assertEquals("timeout", VodRetryPolicy.reasonOf(1003, null, false, false))
        assertEquals("timeout", VodRetryPolicy.reasonOf(2001, null, false, true))
        assertEquals("refused", VodRetryPolicy.reasonOf(2001, null, true, false))
        assertEquals("reset", VodRetryPolicy.reasonOf(2001, null, false, false))
        assertEquals("reset", VodRetryPolicy.reasonOf(2000, null, false, false))
    }
}
