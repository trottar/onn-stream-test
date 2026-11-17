extends "res://rules/minigame.gd"
## A mini game played on the hub: an emulator game the hub runs beside the board.
##
## A module like any other (core/registry.gd's contract); the rules only see
## its scores through their one seam, play(players) -> scores. It asks the hub
## the board runs on (loopback HTTP) which mini games it has, picks one that
## fits the number of players (seeded from the game's seed, as the picker is),
## starts it with the players' pads in order, waits while the players play it
## on the emulator, and gives back the scores the hub read from the game's own
## end screen. While it waits, the board does not react to the pads (a gate
## of its own swallows joypad input; keys still work, so the hub can still
## close the board). Anything that goes wrong is a draw: no hub, no mini game
## for this many players, a refusal, a give-up — one plain line in the log.
## It only awaits; it never holds the board's frame. While it waits the board
## draws at most IDLE_FPS frames a second (nobody sees it: the TV shows the
## hub's game), and its own frame rate is back as soon as the wait ends.

const ID := "hub"
const TITLE := "On the hub"
## Two players (a duel) play one of the hub's two-player games, four (a
## round's end) one of its four-player games; three: a draw (none fits).
const MIN_PLAYERS := 2
const MAX_PLAYERS := 4

## Where the hub answers. PRIVYPARTY_HUB (the computer's setting) overrides it.
const HUB := "http://127.0.0.1:8765"
const LIST := "/plugins/games/party-minigames"
const START := "/plugins/games/party-minigame-start"
const RESULT := "/plugins/games/party-minigame-result"
const END := "/plugins/games/party-minigame-end"
const POLL_SECONDS := 1.0
const REQUEST_SECONDS := 10.0
## The hub gives a mini game up after 15 minutes; this is the board's own bound.
const LIMIT_SECONDS := 1200.0
const MISSED_POLLS := 10
## The board's frame cap while the hub's game is on the TV (Engine.max_fps).
const IDLE_FPS := 10

var stage: Node

static var _played := 0


## Swallows joypad input while a mini game plays on the hub: the last node in
## the tree gets input first, so the board's controls never see the pads.
## While it is in the tree the board draws at most IDLE_FPS frames a second;
## the board's own cap comes back with restore(), or when the gate leaves the
## tree however that happens (the end, the board quitting, the scene going).
class PadGate extends Node:
	var _own_fps := -1

	func _enter_tree() -> void:
		if _own_fps < 0:
			_own_fps = Engine.max_fps
			if _own_fps == 0 or _own_fps > IDLE_FPS:  # 0 is no cap; a lower cap of the board's own stays
				Engine.max_fps = IDLE_FPS

	func _ready() -> void:
		process_mode = Node.PROCESS_MODE_ALWAYS

	func _exit_tree() -> void:
		restore()

	func restore() -> void:
		if _own_fps >= 0:
			Engine.max_fps = _own_fps
			_own_fps = -1

	func _input(event: InputEvent) -> void:
		if event is InputEventJoypadButton or event is InputEventJoypadMotion:
			get_viewport().set_input_as_handled()


func play(players: Array) -> Array:
	var tree := _tree()
	if tree == null:
		return _draw(players, "no scene tree")
	var hub := OS.get_environment("PRIVYPARTY_HUB")
	if hub == "":
		hub = HUB
	var listed: Dictionary = await _call(tree, "GET", hub + LIST)
	if not listed.get("ok", false):
		return _draw(players, "no hub (%s)" % listed.get("error", "no answer"))
	var fitting: Array = []
	for entry in listed.get("minigames", []):
		if int(entry.get("players", 0)) == players.size():
			fitting.append(str(entry.get("id", "")))
	if fitting.is_empty():
		return _draw(players, "no mini game on the hub for %d players" % players.size())
	fitting.sort()
	var random := RandomNumberGenerator.new()
	random.seed = (_game_seed(tree) ^ 0x48554221) + _played
	_played += 1
	var id: String = fitting[random.randi_range(0, fitting.size() - 1)]
	var seats: Array[String] = []
	for player in players:
		seats.append(str(_seat_of(player)))
	var started: Dictionary = await _call(tree, "POST", "%s%s?id=%s&seats=%s" % [hub, START, id, ",".join(seats)])
	if not started.get("ok", false):
		return _draw(players, "the hub refused (%s)" % started.get("error", "no answer"))

	var gate := PadGate.new()
	tree.root.add_child(gate)
	var scores: Array = []
	var why := ""
	var waited := 0.0
	var missed := 0
	while true:
		await tree.create_timer(POLL_SECONDS).timeout
		waited += POLL_SECONDS
		var result: Dictionary = await _call(tree, "GET", hub + RESULT)
		if not result.get("ok", false):
			missed += 1
			if missed >= MISSED_POLLS:
				why = "the hub stopped answering"
				break
			continue
		missed = 0
		var state := str(result.get("state", ""))
		if state == "ended":
			for number in result.get("scores", []):  # JSON numbers come as floats: whole ones back to ints
				scores.append(int(number) if float(number) == floorf(float(number)) else float(number))
			break
		if state == "given_up":
			why = "the hub gave it up (%s)" % str(result.get("why", ""))
			break
		if state != "starting" and state != "playing":
			why = "the hub has no mini game on (%s)" % state
			break
		if waited >= LIMIT_SECONDS:
			why = "no result within %d s" % int(LIMIT_SECONDS)
			break
	gate.restore()  # the board's own frame rate before the hub hands the TV back
	await _call(tree, "POST", hub + END)
	if gate.get_parent() != null:
		gate.get_parent().remove_child(gate)
	gate.free()
	if why != "" or scores.size() != players.size():
		return _draw(players, why if why != "" else "the hub's scores do not fit the players")
	print("PrivyParty: hub mini game: scores %s for seats %s" % [str(scores), ",".join(seats)])
	return scores


## The pad a player plays with (1-4: the hub's seat), from the board's own
## record of who joined with what; a player on the keyboard keeps their place.
func _seat_of(player: Dictionary) -> int:
	var index := int(player.get("index", 0))
	var controls = stage.get("controls") if stage != null else null
	if controls != null and index < controls.players.size():
		var device: String = controls.players[index]
		if device.begins_with("pad"):
			return int(device.substr(3)) + 1
	return index + 1


func _draw(players: Array, why: String) -> Array:
	print("PrivyParty: hub mini game: a draw: %s" % why)
	var scores: Array = []
	scores.resize(players.size())
	scores.fill(0)  # everyone the same: the seam's draw
	return scores


func _tree() -> SceneTree:
	if stage != null and stage.is_inside_tree():
		return stage.get_tree()
	return Engine.get_main_loop() as SceneTree


static func _game_seed(tree: SceneTree) -> int:
	var scene := tree.current_scene
	if scene != null and scene.get("seed_value") != null:
		return int(scene.get("seed_value"))
	return 0


## One HTTP call; its JSON answer as a Dictionary, {"ok": false, "error"} when
## there is none. Awaits; never blocks.
static func _call(tree: SceneTree, method: String, url: String) -> Dictionary:
	var http := HTTPRequest.new()
	http.timeout = REQUEST_SECONDS
	tree.root.add_child(http)
	var how := HTTPClient.METHOD_POST if method == "POST" else HTTPClient.METHOD_GET
	var err := http.request(url, [], how, "")
	var answer := {"ok": false, "error": "no answer"}
	if err == OK:
		var got: Array = await http.request_completed
		var body: PackedByteArray = got[3]
		var parsed = JSON.parse_string(body.get_string_from_utf8()) if body.size() > 0 else null
		if typeof(parsed) == TYPE_DICTIONARY:
			answer = parsed
			if int(got[1]) >= 400:
				answer["ok"] = false
		elif int(got[0]) != HTTPRequest.RESULT_SUCCESS:
			answer = {"ok": false, "error": "no hub"}
	http.queue_free()
	return answer
