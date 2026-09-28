package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** CL-B1: the report body and the grown slow-event rings. */
class DecoderReportUploadTest {

    @Test
    fun bodyIsTheReportAsUtf8() {
        // Rule: the body is the report's exact UTF-8 bytes, no encoding step.
        val report = """{"schema":"privyhub_native_decoder_session_v2","t":"ü–"}"""
        assertEquals(report, String(DecoderReportUpload.encode(report), Charsets.UTF_8))
        assertEquals("/plugins/games/decoder-session-log", DecoderReportUpload.PATH)
        assertTrue(DecoderReportUpload.CONTENT_TYPE.startsWith("application/json"))
    }

    @Test
    fun ringsHoldATwentyFourTransitionSession() {
        // Rule: MARKED holds 24 transitions at ~5 events per cycle window twice over;
        // RECENT covers a 20-minute hold at ~0.63 events/s.
        assertTrue(AvcLowLatencyDecoder.MAX_MARKED_SLOW_EVENTS >= 24 * 5 * 2)
        assertTrue(AvcLowLatencyDecoder.MAX_RECENT_SLOW_EVENTS >= (20 * 60 * 0.63).toInt())
        assertEquals(256, AvcLowLatencyDecoder.MAX_MARKED_SLOW_EVENTS)
        assertEquals(1024, AvcLowLatencyDecoder.MAX_RECENT_SLOW_EVENTS)
    }

    @Test
    fun reportedTotalCapacityIsTheSumOfTheSegments() {
        // Rule: `slow_event_capacity` keeps its meaning (the total of both segments); it
        // is no longer a literal 128 (the first arm build reported 128 with 1,280 rows).
        val src = java.io.File("src/main/java/streaming/NativeStreamActivity.kt").readText()
        val i = src.indexOf("\"slow_event_capacity\",")
        assertTrue(i > 0)
        assertTrue(src.substring(i, i + 200).contains("MAX_MARKED_SLOW_EVENTS"))
    }

    @Test
    fun aFullReportStaysUnderTheCompanionCap() {
        // Rule: a 24-transition report (~32.4K) plus both rings full (1,280 rows at ~23.3
        // chars) stays under the companion's MAX_REPORT_CHARS, 128,000.
        val rows = AvcLowLatencyDecoder.MAX_MARKED_SLOW_EVENTS + AvcLowLatencyDecoder.MAX_RECENT_SLOW_EVENTS
        val estimate = 32_435 + ((rows - 128) * 23.3).toInt()
        assertTrue(estimate < 128_000)
    }
}
