package com.safeiot.privyhub.streaming

import android.view.Gravity
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** B72 (a): the N64 layout card at the top, the overlay's text pushed under it; `n64_card_top=0` = B67's centre. */
class B72ClientTest {

    @Test
    fun overlayPaddingUnderTheCard() {
        // a card laid out from 48 to 210 px: the overlay's text starts 24 px under it
        assertEquals(234, N64LayoutCard.overlayTopPadding(210))
        // never less than the overlay's own padding
        assertEquals(32, N64LayoutCard.overlayTopPadding(0))
        assertEquals(40, N64LayoutCard.overlayTopPadding(0, 40))
    }

    @Test
    fun gravityTopOrB67sCentre() {
        assertEquals(Gravity.TOP or Gravity.CENTER_HORIZONTAL, N64LayoutCard.gravity(true))
        assertEquals(Gravity.CENTER, N64LayoutCard.gravity(false))
        assertEquals(Gravity.TOP, N64LayoutCard.gravity(true) and Gravity.VERTICAL_GRAVITY_MASK)   // not centred down
    }

    @Test
    fun theProperty() {
        assertTrue(N64LayoutCard.parseTop(null))
        assertTrue(N64LayoutCard.parseTop(""))
        assertFalse(N64LayoutCard.parseTop("0"))
        assertFalse(N64LayoutCard.parseTop("off"))
        assertEquals("debug.privyhub.n64_card_top", N64LayoutCard.PROPERTY_TOP)
    }

    @Test
    fun theTopLayoutIsShownOnceMore() {
        // an onn that saw B67's centred card (`shown` true) sees the top card once: its own key
        assertEquals("shown_top", N64LayoutCard.shownKey(true))
        assertEquals(N64LayoutCard.KEY_SHOWN, N64LayoutCard.shownKey(false))     // the property off: B67's key
        assertTrue(N64LayoutCard.shouldShow("n64", true, false))
    }

    @Test
    fun b67sRuleUnchanged() {
        assertTrue(N64LayoutCard.shouldShow("n64", true, false))
        assertFalse(N64LayoutCard.shouldShow("ps1", true, false))
        assertFalse(N64LayoutCard.shouldShow("n64", false, false))
    }
}
