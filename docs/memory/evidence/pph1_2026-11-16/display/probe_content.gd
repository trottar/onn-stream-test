extends SceneTree
## PP-H1 (A's own, off both repos): what the game's registry finds, with and without --content (counts only).
func _initialize() -> void:
	var reg = load("res://core/registry.gd")
	var pics = load("res://props/pictures.gd")
	print("CONTENT roots %d; characters %d; boards %d" % [reg.roots().size(), reg.characters().size(), reg.boards().size()])
	var names := []
	for m in pics.get_script_method_list():
		names.append(m["name"])
	print("CONTENT pictures.gd static methods: ", ", ".join(names))
	quit(0)
