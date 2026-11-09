package com.safeiot.privyhub.streaming

/**
 * B70: in a game the pads' touchpads (a pointer device to Android) and any mouse do nothing: their events are consumed,
 * the onn's pointer is hidden (the null pointer icon) and captured at focus (so Android draws neither its arrow nor the
 * touchpad's own touch spots). The remote's D-pad / OK and the pads' buttons and sticks are never touched: their
 * sources carry no pointer bit. `debug.privyhub.pointer_hide=0` = today (nothing consumed, no icon, no capture).
 *
 * The DualShock / DualSense touchpad press arrives from the touchpad's own device as a pointer click, not as a pad
 * button, so it is swallowed with the rest (listed; no PrivyHub layout uses it).
 */
class PointerGuard(val enabled: Boolean) {

    /** What the activity does for the guard (a fake in the tests). */
    interface Host {
        fun hideIcon()
        fun requestCapture()
        fun releaseCapture()
    }

    var consumed: Int = 0
        private set
    var captureRequests: Int = 0
        private set

    fun consumeMotion(source: Int): Boolean = take(source)
    fun consumeTouch(source: Int): Boolean = take(source)
    fun consumeKey(source: Int): Boolean = take(source)
    fun consumeTrackball(): Boolean = enabled.also { if (it) consumed += 1 }

    private fun take(source: Int): Boolean {
        if (!enabled || !isPointerSource(source)) return false
        consumed += 1
        return true
    }

    /** After the views exist: every view's icon is the null icon (guard on only). */
    fun onAttach(host: Host) {
        if (enabled) host.hideIcon()
    }

    /** Capture needs a focused window; Android drops it when the focus goes. */
    fun onFocus(host: Host, hasFocus: Boolean) {
        if (!enabled) return
        if (hasFocus) {
            captureRequests += 1
            host.requestCapture()
        } else {
            host.releaseCapture()
        }
    }

    companion object {
        const val PROPERTY = "debug.privyhub.pointer_hide"

        // android.view.InputDevice's values (the test checks them against the SDK's)
        const val SOURCE_CLASS_POINTER = 0x00000002
        const val SOURCE_MOUSE = 0x00002002
        const val SOURCE_TOUCHPAD = 0x00100008
        const val SOURCE_MOUSE_RELATIVE = 0x00020004
        const val SOURCE_TOUCH_NAVIGATION = 0x00200000

        private val FULL = intArrayOf(SOURCE_MOUSE, SOURCE_TOUCHPAD, SOURCE_MOUSE_RELATIVE, SOURCE_TOUCH_NAVIGATION)

        /** A pointer source: the pointer class bit (mouse, touchscreen, stylus, a touchpad as a pointer), or one of the
         *  touchpad / mouse sources by its full pattern (never a keyboard, D-pad, gamepad or joystick source). */
        fun isPointerSource(source: Int): Boolean =
            (source and SOURCE_CLASS_POINTER) != 0 || FULL.any { (source and it) == it }

        fun parse(value: String?): Boolean = value?.trim().let { it != "0" && it != "off" }

        fun fromSystem(): Boolean =
            try {
                val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
                parse(get.invoke(null, PROPERTY) as? String)
            } catch (_: Throwable) {
                parse(null)
            }
    }
}
