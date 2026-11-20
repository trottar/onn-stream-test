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
    /**
     * G6-SCREEN1: the video box's height for the measured width: **4:3**, integer (1200 -> 900; G6-HM3's was 16:9,
     * 675). Never a constant (design §2).
     */
    fun videoBoxHeight(widthPx: Int): Int = if (widthPx <= 0) 0 else widthPx * 3 / 4

    /** G6-HM3's 16:9 box (1200 -> 675): the fallback below, and the picture's height when it is not cropped. */
    fun videoBoxHeight16x9(widthPx: Int): Int = if (widthPx <= 0) 0 else widthPx * 9 / 16

    /**
     * G6-SCREEN1: the box on a real screen: 4:3 when the pad region left under it keeps at least the PS2 layout's
     * reference shape ([Ps2TouchLayout.REF_H] / [Ps2TouchLayout.REF_W] of the width, so the cluster is never squeezed
     * vertically); otherwise G6-HM3's 16:9. The tablet (1200 x 2000): 900, leaving 1100 = exactly the reference.
     */
    fun videoBoxHeight(widthPx: Int, heightPx: Int): Int {
        val box = videoBoxHeight(widthPx)
        val refW = Ps2TouchLayout.REF_W.toInt()
        val need = (widthPx * Ps2TouchLayout.REF_H.toInt() + refW - 1) / refW     // whole px, rounded up (1200 -> 1100)
        return if (widthPx > 0 && heightPx - box >= need) box else videoBoxHeight16x9(widthPx)
    }

    /** The pad region's height under the box (never negative). */
    fun padRegionHeight(widthPx: Int, heightPx: Int): Int = (heightPx - videoBoxHeight(widthPx, heightPx)).coerceAtLeast(0)

    /**
     * G6-SCREEN1: the systems whose every game the hub shows 4:3 (proved from the hub's files, read only:
     * `docs/memory/evidence/G6_SCREEN1_4X3_PICTURE_2026-11-20.md` §1.2). The catalog entry's `system` id. Any other
     * system, an unknown one, or none is not cropped.
     */
    val CROP_4X3_SYSTEMS: Set<String> = setOf("snes", "n64")

    /** The hub's stream, in stream pixels (1280 x 720; the picture is scaled, so any 16:9 size crops the same). */
    const val STREAM_W = 1280
    const val STREAM_H = 720

    /** Crop this session's picture to 4:3: a proven system, and a 4:3 box (the 16:9 fallback never crops). */
    fun crop43(system: String?, boxW: Int, boxH: Int): Boolean =
        boxW > 0 && boxH == videoBoxHeight(boxW) && system?.trim()?.lowercase() in CROP_4X3_SYSTEMS

    /** The handheld report's `video_crop`. */
    fun videoCrop(crop: Boolean): String = if (crop) "4:3" else "none"

    /** The shown rectangle of the stream, `x,y,WxH` in stream pixels: the centre 4:3 (`160,0,960x720`) or all of it. */
    fun videoSourceRect(crop: Boolean, streamW: Int = STREAM_W, streamH: Int = STREAM_H): String =
        if (crop) {
            val w = streamH * 4 / 3
            "${(streamW - w) / 2},0,${w}x$streamH"
        } else {
            "0,0,${streamW}x$streamH"
        }

    /**
     * The video surface in the box: `[left, top, width, height]`. Cropped: 16:9 of the box's height, centred (1600 x
     * 900 at x −200 on the tablet), so the stream's side bars fall off the screen's edges. Not cropped: the 16:9
     * picture full width at the top of the box (1200 x 675); the rest of the box is the background.
     */
    fun surfaceRect(boxW: Int, boxH: Int, crop: Boolean): IntArray =
        if (crop) {
            val w = boxH * 16 / 9
            intArrayOf((boxW - w) / 2, 0, w, boxH)
        } else {
            intArrayOf(0, 0, boxW, videoBoxHeight16x9(boxW))
        }

    /** G6-HM4: a catalog row of 3 cards (3 x (300 + 12) dp + 24 dp of padding): the onn's width exactly. */
    const val CATALOG_FULL_WIDTH_DP = 960

    /**
     * G6-HM4 (the user's Q-B4 (a)): the main app's catalog columns. 1 on the TV guide list and 3 otherwise, as today;
     * **2** only with the handheld choice on a touchscreen device narrower than [CATALOG_FULL_WIDTH_DP] (the tablet
     * upright, 800 dp). The cards keep their 300 dp.
     */
    fun catalogColumns(handheld: Boolean, touchscreen: Boolean, widthDp: Int, tvGuideList: Boolean): Int =
        when {
            tvGuideList -> 1
            handheld && touchscreen && widthDp < CATALOG_FULL_WIDTH_DP -> 2
            else -> 3
        }
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
