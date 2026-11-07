package com.safeiot.privyhub.streaming

import android.view.InputDevice
import android.view.KeyEvent
import android.view.MotionEvent
import org.json.JSONArray
import org.json.JSONObject
import java.security.MessageDigest

/**
 * B34: stable player slots, gamepads only, behind the system property `debug.privyhub.pad_slots=stable`
 * (CL-B7P's convention). Absent / empty / any other value = today: no object; the sender hands out slots in
 * first-input order, clears them at every start and stop, and takes any device with stick or hat axes (TRIP-R2 §3).
 *
 * With it: slots by the device's key (sha256 of vendor:product:descriptor, 6 hex -- the descriptor never leaves this
 * file), kept in one object per process across starts and self-restarts (a new process starts empty); only a device
 * with SOURCE_GAMEPAD / SOURCE_JOYSTICK and at least one gamepad button is eligible (a remote or an air mouse with
 * axes is not); at each start the connected pads without a slot take the lowest free slots in the system's
 * controller-number order, so the slots do not depend on which pad presses first; a later pad takes the lowest free
 * slot; a pad that leaves keeps its slot (reused only when all four are held and that pad is gone).
 * Design: `docs/memory/evidence/b34_2026-10-31/design_written_before_code.md` (hashed before this code).
 * B38: a real gamepad only -- also a face button (A / B / X / Y) and stick or hat axes. The onn's own input devices
 * (its "virtual-remote", which declares GAMEPAD and took slot 0 in HOME-1 C4; its remote keyboard; gpio-keys) are
 * key-only, so they never take a slot; no vendor, product or name is compared.
 * Design: `docs/memory/evidence/b38_2026-11-02/design_written_before_code.md` (hashed before this code).
 * B42 (G-A12, 2026-11-06): **on by default** -- absent / empty / junk = stable; `off` / `0` = today's first-input order.
 */
object PadSlotsFlag {
    const val PROPERTY = "debug.privyhub.pad_slots"

    // B42: stable unless `off` / `0` (the user's G-A12 "yes", 2026-11-06, after HOME-2 C4'); `0` as B27's convention
    fun parse(value: String?): Boolean = value?.trim().let { it != "off" && it != "0" }

    /** The property, read through reflection; a failed read is absent, so stable (B42). */
    fun fromSystem(): Boolean =
        try {
            val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            parse(get.invoke(null, PROPERTY) as? String)
        } catch (_: Throwable) {
            parse(null)
        }
}

/** What the slots read from a device (fakes on the JVM; [AndroidPadDevice] on the onn). */
interface PadDevice {
    val descriptor: String
    val vendorId: Int
    val productId: Int
    val sources: Int
    val controllerNumber: Int
    val hasGamepadButton: Boolean
    val isVirtual: Boolean
    /** B38: A / B / X / Y present (defaults keep B34's fakes as they were). */
    val hasFaceButton: Boolean get() = hasGamepadButton
    /** B38: a joystick motion range for the stick or the hat (a remote-class device has none). */
    val hasStickOrHat: Boolean get() = (sources and 0x01000010) == 0x01000010
}

class AndroidPadDevice(private val d: InputDevice) : PadDevice {
    override val descriptor: String get() = d.descriptor?.takeIf { it.isNotBlank() } ?: "id:${d.id}"
    override val vendorId: Int get() = d.vendorId
    override val productId: Int get() = d.productId
    override val sources: Int get() = d.sources
    override val controllerNumber: Int get() = d.controllerNumber
    override val hasGamepadButton: Boolean get() = d.hasKeys(*BUTTONS).any { it }
    override val isVirtual: Boolean get() = d.isVirtual
    override val hasFaceButton: Boolean get() = d.hasKeys(*FACE).any { it }
    override val hasStickOrHat: Boolean
        get() = AXES.any { d.getMotionRange(it, InputDevice.SOURCE_JOYSTICK) != null }

    companion object {
        /** B38: the face buttons (the PS buttons map to these codes). */
        val FACE = intArrayOf(
            KeyEvent.KEYCODE_BUTTON_A, KeyEvent.KEYCODE_BUTTON_B, KeyEvent.KEYCODE_BUTTON_X, KeyEvent.KEYCODE_BUTTON_Y,
        )
        /** B38: the stick and the hat. */
        val AXES = intArrayOf(MotionEvent.AXIS_X, MotionEvent.AXIS_Y, MotionEvent.AXIS_HAT_X, MotionEvent.AXIS_HAT_Y)

        val BUTTONS = intArrayOf(
            KeyEvent.KEYCODE_BUTTON_A, KeyEvent.KEYCODE_BUTTON_B, KeyEvent.KEYCODE_BUTTON_X,
            KeyEvent.KEYCODE_BUTTON_Y, KeyEvent.KEYCODE_BUTTON_L1, KeyEvent.KEYCODE_BUTTON_R1,
            KeyEvent.KEYCODE_BUTTON_START, KeyEvent.KEYCODE_BUTTON_SELECT,
        )

        /** Every connected input device, through the system's own list. */
        fun connected(): List<PadDevice> =
            InputDevice.getDeviceIds().toList().mapNotNull { id -> InputDevice.getDevice(id)?.let { d -> AndroidPadDevice(d) } }
    }
}

class PadSlots(private val count: Int = 4) {
    data class Slot(val slot: Int, val pad: String, val cls: String)

    private val byKey = HashMap<String, Int>()
    private val classOf = HashMap<String, String>()
    private val lock = Any()

    /** At each stream start: the connected pads without a slot take the lowest free ones, by controller number. */
    fun beginStart(connected: List<PadDevice>) {
        synchronized(lock) {
            connected.filter { eligible(it) }
                .map { it to key(it) }
                .distinctBy { it.second }
                .filter { it.second !in byKey }
                .sortedWith(compareBy({ order(it.first.controllerNumber) }, { it.second }))
                .forEach { (d, k) -> assign(d, k, connected) }
        }
    }

    /** The slot for an event's device: kept if it has one; else the lowest free (or a gone pad's); null if none. */
    fun slotFor(device: PadDevice, connected: () -> List<PadDevice>): Int? {
        if (!eligible(device)) return null
        val k = key(device)
        synchronized(lock) {
            byKey[k]?.let { return it }
            return assign(device, k, connected())
        }
    }

    fun map(): List<Slot> = synchronized(lock) {
        byKey.entries.sortedBy { it.value }.map { Slot(it.value, it.key, classOf[it.key] ?: "gamepad") }
    }

    /** `slot:pad:class` joined by `,` in slot order (the heartbeat's and the start's `pad_slots`). */
    fun mapString(): String = map().joinToString(",") { "${it.slot}:${it.pad}:${it.cls}" }

    fun toJson(): JSONArray = JSONArray().apply {
        map().forEach { s -> put(JSONObject().put("slot", s.slot).put("pad", s.pad).put("class", s.cls)) }
    }

    // B41: the player prompt's reads and writes (additive; B34 / B38's paths above do not call them)

    /** The slot an eligible device holds now, or null; never assigns. */
    fun slotOf(d: PadDevice): Int? = if (!eligible(d)) null else slotOfKey(key(d))

    fun slotOfKey(k: String): Int? = synchronized(lock) { byKey[k] }

    /** The key holding a slot, or null. */
    fun holderOf(slot: Int): String? = synchronized(lock) { byKey.entries.firstOrNull { it.value == slot }?.key }

    /** The device takes this slot (its old slot, and the slot's old holder, let go). */
    fun claim(d: PadDevice, slot: Int) {
        val k = key(d)
        synchronized(lock) {
            byKey.entries.removeAll { it.value == slot || it.key == k }
            byKey[k] = slot
            classOf[k] = vendorClass(d.vendorId)
        }
    }

    /** The slot's holder lets go; its key, or null when the slot was free. */
    fun release(slot: Int): String? = synchronized(lock) {
        val k = byKey.entries.firstOrNull { it.value == slot }?.key ?: return null
        byKey.remove(k)
        classOf.remove(k)
        k
    }

    /** B46: the chooser's opening empties the map (the claims re-form it); not called by B34 / B38 / B41's paths. */
    fun clearAll() {
        synchronized(lock) {
            byKey.clear()
            classOf.clear()
        }
    }

    private fun assign(d: PadDevice, k: String, connected: List<PadDevice>): Int? {
        val free = (0 until count).firstOrNull { it !in byKey.values }
        val slot = free ?: run {
            val present = connected.filter { eligible(it) }.map { key(it) }.toSet()
            byKey.entries.filter { it.key !in present }.minByOrNull { it.value }?.also {
                byKey.remove(it.key)
                classOf.remove(it.key)
            }?.value
        } ?: return null
        byKey[k] = slot
        classOf[k] = vendorClass(d.vendorId)
        return slot
    }

    companion object {
        private const val GAMEPAD = 0x00000401   // InputDevice.SOURCE_GAMEPAD
        private const val JOYSTICK = 0x01000010  // InputDevice.SOURCE_JOYSTICK

        fun eligible(d: PadDevice): Boolean =
            !d.isVirtual &&
                ((d.sources and GAMEPAD) == GAMEPAD || (d.sources and JOYSTICK) == JOYSTICK) &&
                d.hasGamepadButton &&
                // B38: a real gamepad -- a face button and stick / hat axes (the onn's key-only devices have none)
                d.hasFaceButton && d.hasStickOrHat

        fun key(d: PadDevice): String {
            val h = MessageDigest.getInstance("SHA-256")
                .digest("${d.vendorId}:${d.productId}:${d.descriptor}".toByteArray())
            return h.take(3).joinToString("") { "%02x".format(it) }
        }

        private fun order(controllerNumber: Int): Int = if (controllerNumber > 0) controllerNumber else Int.MAX_VALUE

        fun vendorClass(vendorId: Int): String = when (vendorId) {
            0x054c -> "sony"
            0x045e -> "microsoft"
            0x057e -> "nintendo"
            0x2dc8 -> "8bitdo"
            0x046d -> "logitech"
            0x18d1 -> "google"
            else -> "gamepad"
        }
    }
}

/** One per process: the slots outlive the activity (a self-restart, a recreation); a new process starts empty. */
object PadSlotsProcess {
    val slots: PadSlots = PadSlots()
}
