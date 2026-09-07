package com.safeiot.privyhub.streaming

import android.view.InputDevice
import android.view.KeyEvent
import android.view.MotionEvent
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.concurrent.atomic.AtomicLong
import kotlin.concurrent.thread
import kotlin.math.abs
import kotlin.math.roundToInt

data class NativeControllerMetrics(
    val packetsSent: Long,
    val sendErrors: Long,
    val motionEvents: Long,
    val lx: Int,
    val ly: Int,
    val rx: Int,
    val ry: Int,
    val hatX: Int,
    val hatY: Int
)

class NativeControllerSender(
    private val host: String,
    private val port: Int
) {
    companion object {
        const val TWO_PLAYER_POC_VERSION =
            "two_player_poc_v0.1"

        private const val PLAYER_COUNT =
            2

        private const val XUSB_DPAD_UP = 0x0001
        private const val XUSB_DPAD_DOWN = 0x0002
        private const val XUSB_DPAD_LEFT = 0x0004
        private const val XUSB_DPAD_RIGHT = 0x0008
        private const val XUSB_START = 0x0010
        private const val XUSB_BACK = 0x0020
        private const val XUSB_LEFT_THUMB = 0x0040
        private const val XUSB_RIGHT_THUMB = 0x0080
        private const val XUSB_LEFT_SHOULDER = 0x0100
        private const val XUSB_RIGHT_SHOULDER = 0x0200
        private const val XUSB_A = 0x1000
        private const val XUSB_B = 0x2000
        private const val XUSB_X = 0x4000
        private const val XUSB_Y = 0x8000
    }

    private data class State(
        var buttons: Int = 0,
        var lx: Short = 0,
        var ly: Short = 0,
        var rx: Short = 0,
        var ry: Short = 0,
        var lt: Int = 0,
        var rt: Int = 0,
        var digitalLt: Boolean = false,
        var digitalRt: Boolean = false,
        var hatX: Int = 0,
        var hatY: Int = 0
    )

    private val states =
        Array(PLAYER_COUNT) {
            State()
        }

    private val devicePlayers =
        mutableMapOf<String, Int>()

    private val lock =
        Any()

    private val packetsSent =
        AtomicLong(0)

    private val sendErrors =
        AtomicLong(0)

    private val motionEvents =
        AtomicLong(0)

    @Volatile
    private var running =
        false

    private var worker:
        Thread? =
        null

    fun start() {
        if (running) {
            return
        }

        synchronized(lock) {
            devicePlayers.clear()

            for (state in states) {
                resetState(state)
            }
        }

        running = true

        worker =
            thread(
                start = true,
                isDaemon = true,
                name = "PrivyHub-Native-Controller"
            ) {
                sendLoop()
            }
    }

    fun stop() {
        synchronized(lock) {
            for (state in states) {
                resetState(state)
            }

            devicePlayers.clear()
        }

        running = false

        try {
            worker?.join(500)
        } catch (_: InterruptedException) {
            Thread.currentThread().interrupt()
        }

        worker = null
    }

    fun snapshot():
        NativeControllerMetrics {
        val current =
            synchronized(lock) {
                states[0].copy()
            }

        return NativeControllerMetrics(
            packetsSent = packetsSent.get(),
            sendErrors = sendErrors.get(),
            motionEvents = motionEvents.get(),
            lx = current.lx.toInt(),
            ly = current.ly.toInt(),
            rx = current.rx.toInt(),
            ry = current.ry.toInt(),
            hatX = current.hatX,
            hatY = current.hatY
        )
    }

    fun handleKeyEvent(
        event: KeyEvent
    ): Boolean {
        val bit =
            when (event.keyCode) {
                KeyEvent.KEYCODE_DPAD_UP -> XUSB_DPAD_UP
                KeyEvent.KEYCODE_DPAD_DOWN -> XUSB_DPAD_DOWN
                KeyEvent.KEYCODE_DPAD_LEFT -> XUSB_DPAD_LEFT
                KeyEvent.KEYCODE_DPAD_RIGHT -> XUSB_DPAD_RIGHT
                KeyEvent.KEYCODE_BUTTON_START -> XUSB_START
                KeyEvent.KEYCODE_BUTTON_SELECT -> XUSB_BACK
                KeyEvent.KEYCODE_BUTTON_THUMBL -> XUSB_LEFT_THUMB
                KeyEvent.KEYCODE_BUTTON_THUMBR -> XUSB_RIGHT_THUMB
                KeyEvent.KEYCODE_BUTTON_L1 -> XUSB_LEFT_SHOULDER
                KeyEvent.KEYCODE_BUTTON_R1 -> XUSB_RIGHT_SHOULDER
                KeyEvent.KEYCODE_BUTTON_A -> XUSB_A
                KeyEvent.KEYCODE_BUTTON_B -> XUSB_B
                KeyEvent.KEYCODE_BUTTON_X -> XUSB_X
                KeyEvent.KEYCODE_BUTTON_Y -> XUSB_Y
                else -> 0
            }

        val isDigitalTrigger =
            event.keyCode == KeyEvent.KEYCODE_BUTTON_L2 ||
                event.keyCode == KeyEvent.KEYCODE_BUTTON_R2

        if (bit == 0 && !isDigitalTrigger) {
            return false
        }

        val device =
            event.device
                ?: return false

        if (!isControllerDevice(device)) {
            return false
        }

        val player =
            playerForDevice(device)
                ?: return false

        synchronized(lock) {
            val state = states[player]

            if (bit != 0) {
                if (event.action == KeyEvent.ACTION_DOWN) {
                    state.buttons =
                        state.buttons or bit
                } else if (event.action == KeyEvent.ACTION_UP) {
                    state.buttons =
                        state.buttons and bit.inv()
                }
            }

            if (event.keyCode == KeyEvent.KEYCODE_BUTTON_L2) {
                state.digitalLt =
                    event.action == KeyEvent.ACTION_DOWN
            }

            if (event.keyCode == KeyEvent.KEYCODE_BUTTON_R2) {
                state.digitalRt =
                    event.action == KeyEvent.ACTION_DOWN
            }
        }

        return true
    }

    fun handleMotionEvent(
        event: MotionEvent
    ): Boolean {
        if (event.action != MotionEvent.ACTION_MOVE) {
            return false
        }

        val source = event.source

        val isJoystick =
            (source and InputDevice.SOURCE_JOYSTICK) ==
                InputDevice.SOURCE_JOYSTICK

        val isGamepad =
            (source and InputDevice.SOURCE_GAMEPAD) ==
                InputDevice.SOURCE_GAMEPAD

        val device =
            event.device
                ?: return false

        val hasGameAxes =
            device.getMotionRange(
                MotionEvent.AXIS_X,
                source
            ) != null ||
                device.getMotionRange(
                    MotionEvent.AXIS_Y,
                    source
                ) != null ||
                device.getMotionRange(
                    MotionEvent.AXIS_HAT_X,
                    source
                ) != null ||
                device.getMotionRange(
                    MotionEvent.AXIS_HAT_Y,
                    source
                ) != null

        if (!isJoystick && !isGamepad && !hasGameAxes) {
            return false
        }

        val player =
            playerForDevice(device)
                ?: return false

        val lx =
            stickAxis(
                event,
                device,
                MotionEvent.AXIS_X
            )

        val ly =
            stickAxis(
                event,
                device,
                MotionEvent.AXIS_Y
            )

        val rightX =
            when {
                device.getMotionRange(
                    MotionEvent.AXIS_Z,
                    source
                ) != null ->
                    MotionEvent.AXIS_Z

                device.getMotionRange(
                    MotionEvent.AXIS_RX,
                    source
                ) != null ->
                    MotionEvent.AXIS_RX

                else ->
                    MotionEvent.AXIS_Z
            }

        val rightY =
            when {
                device.getMotionRange(
                    MotionEvent.AXIS_RZ,
                    source
                ) != null ->
                    MotionEvent.AXIS_RZ

                device.getMotionRange(
                    MotionEvent.AXIS_RY,
                    source
                ) != null ->
                    MotionEvent.AXIS_RY

                else ->
                    MotionEvent.AXIS_RZ
            }

        val rx =
            stickAxis(
                event,
                device,
                rightX
            )

        val ry =
            stickAxis(
                event,
                device,
                rightY
            )

        val lt =
            triggerAxis(
                event,
                device,
                MotionEvent.AXIS_LTRIGGER,
                MotionEvent.AXIS_BRAKE
            )

        val rt =
            triggerAxis(
                event,
                device,
                MotionEvent.AXIS_RTRIGGER,
                MotionEvent.AXIS_GAS
            )

        val hatX =
            event.getAxisValue(
                MotionEvent.AXIS_HAT_X
            )

        val hatY =
            event.getAxisValue(
                MotionEvent.AXIS_HAT_Y
            )

        val hatXDigital =
            when {
                hatX <= -0.5f -> -1
                hatX >= 0.5f -> 1
                else -> 0
            }

        val hatYDigital =
            when {
                hatY <= -0.5f -> -1
                hatY >= 0.5f -> 1
                else -> 0
            }

        synchronized(lock) {
            val state = states[player]

            state.lx = toStick(lx)
            state.ly = toStick(-ly)
            state.rx = toStick(rx)
            state.ry = toStick(-ry)
            state.lt = toTrigger(lt)
            state.rt = toTrigger(rt)
            state.hatX = hatXDigital
            state.hatY = hatYDigital

            val dpadMask =
                XUSB_DPAD_UP or
                    XUSB_DPAD_DOWN or
                    XUSB_DPAD_LEFT or
                    XUSB_DPAD_RIGHT

            state.buttons =
                state.buttons and dpadMask.inv()

            if (hatXDigital < 0) {
                state.buttons =
                    state.buttons or XUSB_DPAD_LEFT
            } else if (hatXDigital > 0) {
                state.buttons =
                    state.buttons or XUSB_DPAD_RIGHT
            }

            if (hatYDigital < 0) {
                state.buttons =
                    state.buttons or XUSB_DPAD_UP
            } else if (hatYDigital > 0) {
                state.buttons =
                    state.buttons or XUSB_DPAD_DOWN
            }
        }

        motionEvents.incrementAndGet()

        return true
    }

    private fun isControllerDevice(
        device: InputDevice
    ): Boolean {
        val sources = device.sources

        return (
            (sources and InputDevice.SOURCE_GAMEPAD) ==
                InputDevice.SOURCE_GAMEPAD
        ) || (
            (sources and InputDevice.SOURCE_JOYSTICK) ==
                InputDevice.SOURCE_JOYSTICK
        )
    }

    private fun playerForDevice(
        device: InputDevice
    ): Int? {
        val descriptor =
            device.descriptor
                ?.takeIf {
                    it.isNotBlank()
                }
                ?: "id:${device.id}"

        return synchronized(lock) {
            devicePlayers[descriptor]
                ?: run {
                    val assigned =
                        (0 until PLAYER_COUNT)
                            .firstOrNull {
                                it !in devicePlayers.values
                            }

                    if (assigned != null) {
                        devicePlayers[descriptor] =
                            assigned
                    }

                    assigned
                }
        }
    }

    private fun resetState(
        state: State
    ) {
        state.buttons = 0
        state.lx = 0
        state.ly = 0
        state.rx = 0
        state.ry = 0
        state.lt = 0
        state.rt = 0
        state.digitalLt = false
        state.digitalRt = false
        state.hatX = 0
        state.hatY = 0
    }

    private fun stickAxis(
        event: MotionEvent,
        device: InputDevice,
        axis: Int
    ): Float {
        val range =
            device.getMotionRange(
                axis,
                event.source
            )
                ?: return 0f

        val value =
            event.getAxisValue(axis)

        return if (abs(value) <= range.flat) {
            0f
        } else {
            value.coerceIn(-1f, 1f)
        }
    }

    private fun triggerAxis(
        event: MotionEvent,
        device: InputDevice,
        primary: Int,
        fallback: Int
    ): Float {
        val source = event.source

        val axis =
            if (
                device.getMotionRange(
                    primary,
                    source
                ) != null
            ) {
                primary
            } else {
                fallback
            }

        val range =
            device.getMotionRange(
                axis,
                source
            )
                ?: return 0f

        val raw =
            event.getAxisValue(axis)

        val span =
            range.max - range.min

        if (span <= 0f) {
            return raw.coerceIn(0f, 1f)
        }

        return (
            (raw - range.min) / span
        ).coerceIn(0f, 1f)
    }

    private fun toStick(
        value: Float
    ): Short {
        val scaled =
            (
                value.coerceIn(-1f, 1f) *
                    32767f
            ).roundToInt()

        return scaled.coerceIn(
            -32768,
            32767
        ).toShort()
    }

    private fun toTrigger(
        value: Float
    ): Int {
        return (
            value.coerceIn(0f, 1f) *
                255f
        ).roundToInt()
            .coerceIn(
                0,
                255
            )
    }

    private fun sendLoop() {
        val address =
            try {
                InetAddress.getByName(host)
            } catch (_: Exception) {
                sendErrors.incrementAndGet()
                running = false
                return
            }

        val socket =
            DatagramSocket()

        var sequence = 0

        try {
            socket.connect(
                address,
                port
            )

            while (running) {
                val snapshots =
                    synchronized(lock) {
                        Array(PLAYER_COUNT) {
                            states[it].copy()
                        }
                    }

                for (
                    player in
                    0 until PLAYER_COUNT
                ) {
                    val snapshot =
                        snapshots[player]

                    val lt =
                        maxOf(
                            snapshot.lt,
                            if (snapshot.digitalLt) {
                                255
                            } else {
                                0
                            }
                        )

                    val rt =
                        maxOf(
                            snapshot.rt,
                            if (snapshot.digitalRt) {
                                255
                            } else {
                                0
                            }
                        )

                    val data =
                        ByteBuffer.allocate(36)
                            .order(
                                ByteOrder.LITTLE_ENDIAN
                            )
                            .apply {
                                put(
                                    byteArrayOf(
                                        'P'.code.toByte(),
                                        'H'.code.toByte(),
                                        'I'.code.toByte(),
                                        '1'.code.toByte()
                                    )
                                )
                                put(1.toByte())
                                put(player.toByte())
                                putShort(0.toShort())
                                putInt(sequence)
                                putLong(
                                    System.nanoTime() /
                                        1000L
                                )
                                putInt(snapshot.buttons)
                                putShort(snapshot.lx)
                                putShort(snapshot.ly)
                                putShort(snapshot.rx)
                                putShort(snapshot.ry)
                                putShort(lt.toShort())
                                putShort(rt.toShort())
                            }
                            .array()

                    try {
                        socket.send(
                            DatagramPacket(
                                data,
                                data.size
                            )
                        )

                        packetsSent.incrementAndGet()
                    } catch (_: Exception) {
                        sendErrors.incrementAndGet()
                    }

                    sequence += 1
                }

                try {
                    Thread.sleep(8)
                } catch (_: InterruptedException) {
                    Thread.currentThread().interrupt()
                    break
                }
            }
        } finally {
            try {
                socket.close()
            } catch (_: Exception) {
            }
        }
    }
}
