package com.safeiot.privyhub.streaming

import java.io.File
import java.nio.file.Files
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

/**
 * B19: `debug.privyhub.stall_signal` and `debug.privyhub.restart_guard` absent = ON, `0` = off (as B13's link_report);
 * `link_notice` stays opt-in. The objects are built exactly as the activity's lazy properties build them, from the
 * parse of an absent property, and the B15 paths run through the guard so built (B17's order: the start with
 * `guard_end`, then the report); with `0` it is today's (no guard: start, start).
 */
class ClientDefaultsTest {
    private val dir: File = Files.createTempDirectory("b19_store_").toFile()
    private var n = 0

    /** The activity's lazy property, from a property value. */
    private fun guardFor(value: String?, clock: LongArray): RestartGuard? =
        if (RestartGuardFlag.parse(value)) RestartGuard { clock[0] } else null

    /** One loss and one return on [path]; the host's posts in order. */
    private fun run(value: String?, path: String): List<String> {
        val clock = longArrayOf(1_000L)
        val f = File(dir, "p${n++}.properties")
        val posts = mutableListOf<String>()
        val a = guardFor(value, clock)?.also { it.attach(FilePendingStore(f), 1L, 100L) }
        a?.onSurfaceLost("{\"s\":\"A\"}", 15L, 10L, false)
        clock[0] += 5_000L
        val b = when (path) {
            "surface" -> a
            "recreate" -> guardFor(value, clock)?.also { it.attach(FilePendingStore(f), 2L, 100L) }
            else -> guardFor(value, clock)?.also { it.attach(FilePendingStore(f), 1L, 7_000L) }
        }
        val holds = b?.prepareStart() == true
        val restart = b?.takePending()
        restart?.let { p -> b.beginViaStart(p) }
        posts.add("start" + (if (restart != null) "&guard_end=1" else ""))
        restart?.let { p -> b.noteStartResponse(true); b.reportAfterStart(p) { r -> posts.add("report:$r") } }
        if (b != null) {
            assertEquals(path, restart != null, holds)
            assertEquals(path, path, b.lastCause!!["trigger"])
        }
        return posts
    }

    @Test
    fun absentIsOnAndZeroIsOff() {
        assertEquals(150L, StallSignalFlag.parse(null))
        assertEquals(150L, StallSignalFlag.parse(""))
        assertNull(StallSignalFlag.parse("0"))
        assertEquals(true, RestartGuardFlag.parse(null))
        assertEquals(true, RestartGuardFlag.parse(""))
        assertEquals(false, RestartGuardFlag.parse("0"))
        assertEquals(true, LinkNoticeFlag.parse(null))            // B25: link_notice on unless `0` (moved)
        assertEquals(false, LinkNoticeFlag.parse("0"))
        assertEquals(true, LinkReportFlag.parse(null))            // B13's, unchanged
    }

    @Test
    fun theThreeB15PathsWithThePropertyAbsent() {
        for (path in listOf("surface", "recreate", "process")) {
            assertEquals(path, listOf("start&guard_end=1", "report:{\"s\":\"A\"}"), run(null, path))
        }
    }

    @Test
    fun zeroIsTodaysNoGuard() {
        for (path in listOf("surface", "recreate", "process")) {
            assertEquals(path, listOf("start"), run("0", path))
        }
    }

    @Test
    fun theStallMonitorFromAnAbsentProperty() {
        val m = StallMonitor(StallSignalFlag.parse(null)!!)
        assertNull(m.tick(0L, StallInputs(100L, 10L, false, true)))
        assertNotNull(m.tick(8L, StallInputs(150L, 10L, false, true)))  // a stall from 150 ms
        m.requestBye()
        assertEquals(StallPacket.KIND_BYE, m.tick(16L, StallInputs(10L, 10L, false, true))!![4].toInt())
    }
}
