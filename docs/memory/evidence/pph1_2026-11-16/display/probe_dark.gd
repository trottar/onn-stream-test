extends SceneTree
## PP-H1 probe (session A's own; kept off both repos; edits nothing): the game's own main scene with a window,
## Witch Hill picked as player 1 would in the lobby, four of the registry's characters standing on the board's
## darkest space, the darkest mood held (the board's own hold_mood(1.0): fog at its most, the ground mist, the lit
## lamps), and the game's own camera following the first of them, as when it is that player's turn.
## Godot's own --print-fps gives the frames a second. Runs until the game's quit (F10 / a close request).
## User args (after --): --content=<folder> (read by the game's registry), --mist=0 (fog and lamps off through the
## game's own setting).

const MAIN := "res://game/main.tscn"
const BOARD := "witch_hill"

var main: Node
var _t0 := 0


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var mist_on := not args.has("--mist=0")
	main = (load(MAIN) as PackedScene).instantiate()
	root.add_child(main)
	current_scene = main
	_setup.call_deferred(mist_on)


func _setup(mist_on: bool) -> void:
	await process_frame
	var ok: bool = main.set_board(BOARD)
	var board = main.board
	var darkest := ""
	var most := -1.0
	for id in board.board.ids():
		var m: float = board.mood_at(board.space_position(id))
		if m > most:
			most = m
			darkest = id
	var ids: Array = main._character_ids()
	for i in 4:
		var c: Node3D = main._add_character(ids[i % ids.size()])
		c.position = board.standing_spot(darkest, i, 4)
		c.play("idle")
	var settings = load("res://game/settings.gd")
	settings.mist = mist_on
	main.apply_mist()
	board.hold_mood(1.0)
	main.camera.follow(main.characters[0], true)
	var info := RenderingServer.get_video_adapter_name()
	print("PROBE ready: board %s %s; darkest space mood %.2f; figures %d; mist %s; fog %.3f; adapter %s; method %s; driver %s; vsync %d; max_fps %d" % [
		BOARD, "ok" if ok else "NOT SET", most, main.characters.size(), mist_on, board.fog_shown, info,
		ProjectSettings.get_setting("rendering/renderer/rendering_method"), RenderingServer.get_current_rendering_driver_name(),
		DisplayServer.window_get_vsync_mode(), Engine.max_fps])
	var size := DisplayServer.window_get_size()
	print("PROBE window: %dx%d; lamps lit %d; mist layers shown %d" % [size.x, size.y, _lamps(board), _layers(board)])
	_t0 = Time.get_ticks_msec()
	while true:
		await create_timer(10.0).timeout
		print("PROBE t=%ds fog %.3f lamps %d mist layers %d fps %.1f" % [(Time.get_ticks_msec() - _t0) / 1000, board.fog_shown,
			_lamps(board), _layers(board), Engine.get_frames_per_second()])


func _lamps(board) -> int:
	var n := 0
	var scenery = board.get_node_or_null("Scenery")
	if scenery != null:
		for piece in scenery.get_children():
			if piece.get("lamp") != null and piece.lamp.visible:
				n += 1
	return n


func _layers(board) -> int:
	return board.mist_layers.filter(func(layer): return is_instance_valid(layer) and layer.visible).size()
