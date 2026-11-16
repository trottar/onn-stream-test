extends SceneTree
## Hub mini game check: the mini game that asks the hub (minigames/hub_minigame.gd).
##
## Run from the repo root:
##   GODOT --headless --path . --script res://checks/hub_minigame_check.gd
##
## Needs no hub and none of the owner's pictures: it answers as a small hub of
## its own on loopback (or uses the one named in PRIVYPARTY_CHECK_HUB, the
## same answers; what it was asked is then that hub's to check). Asserts that:
##   - a win for player 1 and a win for player 2 come back as the hub's scores,
##     in the order of the players given
##   - the players' pads reach the hub as their seats, in the order given
##     (a player's seat is the pad they joined with)
##   - the hub giving the mini game up, refusing it, having none for that
##     many players, or not being there at all is a draw (everyone the same)
##   - the mini game is ended on the hub whenever it was started
##   - while it waits the board's controls see no pad; afterwards they do
##   - it fits the registry's contract and the picker can offer it for two
## Exit code 0 = PASS, 1 = FAIL.

const HubMinigame = preload("res://minigames/hub_minigame.gd")
const Registry = preload("res://core/registry.gd")

var _checked := 0
var _failures: Array[String] = []
var _server := TCPServer.new()
var _port := 0
var _calls: Array[String] = []    # every path the stand-in hub was asked, in order
var _polls := {}                  # scenario -> result calls so far


class Witness extends Node:  # stands where the board's controls stand: sees what reaches them
	var pads := 0

	func _input(event: InputEvent) -> void:
		if event is InputEventJoypadButton and event.pressed:
			pads += 1


class FakeControls extends Node:
	var players: Array[String] = []


class FakeStage extends Node:
	var controls: Node


func _initialize() -> void:
	_run()


func _run() -> void:
	await process_frame
	print("HUB MINIGAME CHECK: a mini game played on the hub")
	var base := OS.get_environment("PRIVYPARTY_CHECK_HUB")
	if base == "":
		for p in range(18765, 18800):
			if _server.listen(p, "127.0.0.1") == OK:
				_port = p
				break
		_expect(_port != 0, "the stand-in hub listens on loopback")
		base = "http://127.0.0.1:%d" % _port
		_serve()

	var witness := Witness.new()
	root.add_child(witness)
	var stage := FakeStage.new()
	var controls := FakeControls.new()
	stage.controls = controls
	root.add_child(stage)
	stage.add_child(controls)

	var two := [{"index": 0, "name": "A", "coins": 0}, {"index": 1, "name": "B", "coins": 0}]
	controls.players = ["pad0", "pad1"]
	_same(await _play(stage, base, "win1", two), [1, 0], "player 1's win comes back as the hub's scores")
	_expect_asked(_asked("win1", "party-minigame-start?id=mg_one&seats=1,2"), "the seats in the order of the players given")
	_expect_asked(_asked("win1", "party-minigame-end"), "the mini game ended on the hub")
	_same(await _play(stage, base, "win2", two), [0, 1], "player 2's win comes back as the hub's scores")

	# the players given the other way round, and joined with each other's pads
	var swapped := [{"index": 1, "name": "B", "coins": 0}, {"index": 0, "name": "A", "coins": 0}]
	controls.players = ["pad1", "pad0"]
	_same(await _play(stage, base, "win1", swapped), [1, 0], "the scores follow the order of the players given")
	_expect_asked(_asked("win1", "seats=1,2"), "each player's seat is the pad they joined with")

	# the pads, while it waits and after
	controls.players = ["pad0", "pad1"]
	witness.pads = 0
	var during := [0]
	var poke := func():
		await create_timer(1.5).timeout
		await _press()
		during[0] = witness.pads
	poke.call()
	_same(await _play(stage, base, "slow", two), [0, 1], "a slow mini game still comes back")
	_same(during[0], 0, "while it waits the board's controls see no pad")
	await _press()
	_same(witness.pads, 1, "afterwards they do")
	_expect(not root.get_children().any(func(n): return n is HubMinigame.PadGate), "the gate is gone")

	_same(await _play(stage, base, "giveup", two), [0, 0], "a give-up is a draw")
	_expect_asked(_asked("giveup", "party-minigame-end"), "a given-up mini game is ended on the hub too")
	_same(await _play(stage, base, "refused", two), [0, 0], "a refusal is a draw")
	_expect_asked(not _asked("refused", "party-minigame-end"), "a refused mini game is not ended (it never started)")
	_same(await _play(stage, base, "four", two), [0, 0], "no mini game for this many players is a draw")
	_same(await _play(stage, "http://127.0.0.1:9", "nohub", two), [0, 0], "no hub is a draw")

	var script: Script = load("res://minigames/hub_minigame.gd")
	var constants: Dictionary = script.get_script_constant_map()
	_expect(Registry.register_minigame(script), "it follows the registry's contract")
	_same([int(constants["MIN_PLAYERS"]), int(constants["MAX_PLAYERS"])], [2, 2], "it is offered for two players")
	_expect(Registry.minigames().has(str(constants["ID"])), "the registry lists it")

	_server.stop()
	print("")
	if _failures.is_empty():
		print("HUB MINIGAME CHECK: PASS (%d assertions)" % _checked)
		quit(0)
	else:
		for f in _failures:
			print("  FAIL: ", f)
		print("HUB MINIGAME CHECK: FAIL (%d of %d assertions)" % [_failures.size(), _checked])
		quit(1)


func _play(stage: Node, base: String, scenario: String, players: Array) -> Array:
	OS.set_environment("PRIVYPARTY_HUB", base + "/s/" + scenario if scenario != "nohub" else base)
	var minigame = HubMinigame.new()
	minigame.stage = stage
	return await minigame.play(players)


func _press() -> void:
	var press := InputEventJoypadButton.new()
	press.device = 0
	press.button_index = JOY_BUTTON_A
	press.pressed = true
	Input.parse_input_event(press)
	var release := press.duplicate()
	release.pressed = false
	Input.parse_input_event(release)
	await process_frame  # input given this way reaches the nodes at the next frame
	await process_frame


## Whether the stand-in hub was asked this. With an outside hub (PRIVYPARTY_CHECK_HUB) these are that hub's to
## record, and the assertions that use this are left to it.
func _asked(scenario: String, what: String) -> bool:
	return _calls.any(func(c): return c.begins_with("/s/" + scenario + "/") and c.contains(what))


func _expect_asked(condition: bool, what: String) -> void:
	if _port != 0:
		_expect(condition, what)


# --- the stand-in hub -----------------------------------------------------------

func _serve() -> void:
	while _server.is_listening():
		while _server.is_connection_available():
			_answer(_server.take_connection())
		await process_frame


func _answer(peer: StreamPeerTCP) -> void:
	var text := ""
	var waited := 0
	while not text.contains("\r\n\r\n") and waited < 200:
		peer.poll()
		var n := peer.get_available_bytes()
		if n > 0:
			text += peer.get_utf8_string(n)
		else:
			waited += 1
			await process_frame
	var path := text.get_slice(" ", 1)
	_calls.append(path)
	var parts := path.split("/")  # "", "s", scenario, "plugins", "games", action?query
	var scenario := parts[2] if parts.size() > 2 else ""
	var action := path.get_slice("/plugins/games/", 1).get_slice("?", 0)
	var code := 200
	var body := {"ok": true}
	match action:
		"party-minigames":
			body["minigames"] = [{"id": "mg_one", "players": 4 if scenario == "four" else 2}]
		"party-minigame-start":
			if scenario == "refused":
				code = 400
				body = {"ok": false, "error": "a mini game is already on"}
			else:
				body["state"] = "starting"
		"party-minigame-result":
			_polls[scenario] = int(_polls.get(scenario, 0)) + 1
			var n: int = _polls[scenario]
			var needed := 3 if scenario == "slow" else 1
			if n <= needed:
				body.merge({"state": "playing", "recognised": true})
			elif scenario == "giveup":
				body.merge({"state": "given_up", "why": "no end within 900 s", "scores": null})
			else:
				body.merge({"state": "ended", "class": "end_P1", "scores": [0, 1] if scenario in ["win2", "slow"] else [1, 0]})
		"party-minigame-end":
			body["ended"] = true
		_:
			code = 404
			body = {"ok": false, "error": "Unknown Games plugin action"}
	var json := JSON.stringify(body)
	var head := "HTTP/1.1 %d X\r\nContent-Type: application/json\r\nContent-Length: %d\r\nConnection: close\r\n\r\n" % [code, json.to_utf8_buffer().size()]
	peer.put_data((head + json).to_utf8_buffer())
	await process_frame
	peer.disconnect_from_host()


# --- the assertions ------------------------------------------------------------

func _expect(condition: bool, what: String) -> bool:
	_checked += 1
	if not condition:
		_failures.append(what)
	return condition


func _same(actual, expected, what: String) -> void:
	_expect(actual == expected, "%s (got %s, wanted %s)" % [what, str(actual), str(expected)])
