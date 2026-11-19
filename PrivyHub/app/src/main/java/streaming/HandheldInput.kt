package com.safeiot.privyhub.streaming

/**
 * G6-HM2: the handheld mode's pure helpers (no Android types; JVM-tested). Design:
 * `docs/memory/evidence/g6_hm1_2026-11-19/design_written_before_code.md` (hashed before this code), §2 and §6.
 * Nothing on the onn calls these: they are used only by the handheld activity (G6-HM3).
 */
object HandheldInput {
    /** android.view.InputDevice.SOURCE_TOUCHSCREEN (the test checks the other sources against it). */
    const val SOURCE_TOUCHSCREEN = 0x00001002

    /**
     * The touchscreen, and nothing else of B70's pointer class: a mouse (0x2002), a touchpad (0x100008), a relative
     * mouse (0x20004) and touch navigation (0x200000) stay consumed by [PointerGuard]. A stylus reported together with
     * the screen (0x5002) passes: the S Pen acts as a finger (disclosed, design §6).
     */
    fun isTouchscreen(source: Int): Boolean = (source and SOURCE_TOUCHSCREEN) == SOURCE_TOUCHSCREEN
}

object HandheldGeometry {
    /** The video box's height for the measured width: 16:9, integer (1200 -> 675). Never a constant (design §2). */
    fun videoBoxHeight(widthPx: Int): Int = if (widthPx <= 0) 0 else widthPx * 9 / 16

    /** The pad region's height under the box (never negative). */
    fun padRegionHeight(widthPx: Int, heightPx: Int): Int = (heightPx - videoBoxHeight(widthPx)).coerceAtLeast(0)
}

/**
 * G6-HM2: the touch pad as a [PadDevice] for the slots and the prompt (design §5). It passes [PadSlots.eligible]
 * unchanged (GAMEPAD | JOYSTICK, a gamepad button, a face button, stick / hat, not virtual), so nothing in [PadSlots]
 * changes. Its key is fixed: sha256("0:0:privyhub-touchpad"), 6 hex = `01097c`; its class is `gamepad`.
 * It is never in AndroidPadDevice.connected(): the handheld activity adds it to its own connected list (hook H4),
 * without which [PlayerPrompt]'s open-slot rule would count its P1 as free.
 */
object TouchPadDevice : PadDevice {
    const val KEY = "01097c"
    override val descriptor: String = "privyhub-touchpad"
    override val vendorId: Int = 0
    override val productId: Int = 0
    override val sources: Int = 0x01000411          // SOURCE_GAMEPAD | SOURCE_JOYSTICK
    override val controllerNumber: Int = 0
    override val hasGamepadButton: Boolean = true
    override val isVirtual: Boolean = false
    override val hasFaceButton: Boolean = true
    override val hasStickOrHat: Boolean = true
}
