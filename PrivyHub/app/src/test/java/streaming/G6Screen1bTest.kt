package com.safeiot.privyhub.streaming

import com.safeiot.privyhub.streaming.HandheldGeometry.Fill
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/**
 * G6-SCREEN1b: PS2 cropped to 4:3 when the hub's reply says the launch ran without the widescreen patch; PS1's
 * narrower picture stretched to the 4:3 box; the launch request's `display=handheld` only from the handheld screen.
 */
class G6Screen1bTest {

    // the fill per system: PS2 only with the reply's widescreen false; PS1 stretched; SNES / N64 as SCREEN1
    @Test
    fun theFillPerSystem() {
        assertEquals(Fill.CROP_4X3, HandheldGeometry.fill("ps2", false, 1200, 900))
        assertEquals(Fill.NONE, HandheldGeometry.fill("ps2", null, 1200, 900))       // no field: an older hub
        assertEquals(Fill.NONE, HandheldGeometry.fill("ps2", true, 1200, 900))
        assertEquals(Fill.STRETCH_PS1, HandheldGeometry.fill("ps1", null, 1200, 900))
        assertEquals(Fill.STRETCH_PS1, HandheldGeometry.fill(" PS1 ", false, 1200, 900))
        for (s in listOf("snes", "n64")) assertEquals(s, Fill.CROP_4X3, HandheldGeometry.fill(s, null, 1200, 900))
        for (s in listOf("gamecube", "party", "nes", "genesis", "", "unknown", null))
            assertEquals("$s", Fill.NONE, HandheldGeometry.fill(s, false, 1200, 900))
        // the 16:9 fallback box: nothing filled
        for (s in listOf("ps2", "ps1", "snes")) assertEquals(s, Fill.NONE, HandheldGeometry.fill(s, false, 1200, 675))
        assertEquals("4:3", HandheldGeometry.videoCrop(Fill.CROP_4X3))
        assertEquals("stretch", HandheldGeometry.videoCrop(Fill.STRETCH_PS1))
        assertEquals("none", HandheldGeometry.videoCrop(Fill.NONE))
    }

    // PS2's crop is SCREEN1's centre 4:3
    @Test
    fun ps2CropsTheCentre4x3() {
        assertEquals("160,0,960x720", HandheldGeometry.videoSourceRect(Fill.CROP_4X3))
        assertArrayEquals(intArrayOf(-200, 0, 1600, 900), HandheldGeometry.surfaceRect(1200, 900, Fill.CROP_4X3))
    }

    // PS1's content, derived from C5-M4's measured box (x 302, 1316 wide at 1920) and checked against the core's aspect
    @Test
    fun ps1ContentIs202By876FromTheEvidence() {
        assertArrayEquals(intArrayOf(202, 0, 876, 720), HandheldGeometry.ps1Content())
        assertEquals("202,0,876x720", HandheldGeometry.videoSourceRect(Fill.STRETCH_PS1))
        assertEquals(876.0, 1.2190 * 720, 2.0)                                           // 877.7
        val c = HandheldGeometry.ps1Content()
        assertEquals(640, c[0] + c[2] / 2)                                               // centred in the stream
    }

    // PS1 stretched: the surface scaled so the content fills the 1200 x 900 box (about 9.6 % wider than true shape)
    @Test
    fun ps1IsStretchedToTheBox() {
        val r = HandheldGeometry.surfaceRect(1200, 900, Fill.STRETCH_PS1)
        assertArrayEquals(intArrayOf(-276, 0, 1753, 900), r)
        val sx = r[2] / 1280.0
        assertEquals(0.0, r[0] + 202 * sx, 1.0)                                          // the content's left at the box's left
        assertEquals(1200.0, r[0] + (202 + 876) * sx, 1.0)                                // its right at the box's right
        val shown = (876 * sx / 900) / (876.0 / 720)                                     // shown aspect over the true one
        assertEquals(1.096, shown, 0.002)
    }

    // the launch request's field: only for the handheld screen, nothing otherwise (the onn's URL as today)
    @Test
    fun theRequestFieldOnlyFromTheHandheldPath() {
        assertEquals("&display=handheld", HandheldGeometry.launchSuffix(true))
        assertEquals("", HandheldGeometry.launchSuffix(false))
        val main = File("src/main/java/MainActivity.kt").readText()
        val uses = Regex("""HandheldGeometry\.launchSuffix\(([^)]*\))\)""").findAll(main).map { it.groupValues[1] }.toList()
        assertEquals(listOf("useHandheldGameScreen()"), uses)
        assertTrue(main.contains("\"/plugins/games/launch?id=\$gameId\$cheatQuerySuffix\$modQuerySuffix\""))
    }
}
