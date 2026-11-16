extends SceneTree
## B107 (session B): step 19's counts on the hub, read only. Run from a scratch copy of the board game's repo:
##   GODOT --headless --path <copy> --script <this file>
## Builds the character the way checks/step19_round_bodies.gd does (the same definition: a name and the placeholder
## face; two frames), then, for every piece of the body, the three counts _wrapped_round makes (corners facing
## front: n.z > 0.85; sides: |n.x| > 0.92 and |n.y| < 0.3; back: n.z < -0.5 and |n.y| < 0.5; the bar: more than
## four of each), how many corners sit near each cut, and the same counts on the same body model read raw at run time
## by GLTFDocument (no import step, so no import compression) — mapped bind by bind. Prints numbers only. Edits
## nothing; writes nothing.

const CharacterDef = preload("res://characters/character_def.gd")
const CHARACTER_SCENE := "res://characters/character.tscn"
const FACE := "res://characters/placeholders/face_a.png"
const TEMPLATE := "res://models/template_body.glb"
const SHAPE := "Shape"
const CHECKED: Array[String] = ["UpperChest", "Hips", "LeftUpperLeg", "RightLowerLeg"]
const NEAR := 0.02   # a corner within this of a cut is "near" it


func _initialize() -> void:
	_run()


func _run() -> void:
	await process_frame
	var def := CharacterDef.from_dict({"name": "Someone", "photo": FACE})
	var character: Node3D = (load(CHARACTER_SCENE) as PackedScene).instantiate()
	character.definition = def
	root.add_child(character)
	await process_frame
	await process_frame
	print("B107 PROBLEMS ", character.problems)
	if character.body == null:
		quit(2)
		return
	var mesh: Mesh = character.body.mesh
	var to_body: Transform3D = character.body_from_skeleton()
	print("B107 MESH class=%s surfaces=%d" % [mesh.get_class(), mesh.get_surface_count()])
	for s in mesh.get_surface_count():
		var fmt: int = mesh.surface_get_format(s)
		var arrays := mesh.surface_get_arrays(s)
		var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var idx = arrays[Mesh.ARRAY_INDEX]
		print("B107 SURFACE %d vertices=%d indices=%d compressed=%s tangents=%s bones_per_vertex=%d" % [s, verts.size(),
				(idx.size() if idx != null else 0), (fmt & Mesh.ARRAY_FLAG_COMPRESS_ATTRIBUTES) != 0,
				(fmt & Mesh.ARRAY_FORMAT_TANGENT) != 0, (8 if (fmt & Mesh.ARRAY_FLAG_USE_8_BONE_WEIGHTS) != 0 else 4)])
	var imported := _corners(mesh, character.body.skin, character, to_body)
	_report("imported", imported)

	# The same model read raw (GLTFDocument at run time: no import step, no compression), bind by bind.
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	var err := doc.append_from_file(ProjectSettings.globalize_path(TEMPLATE), state)
	if err != OK:
		print("B107 RAW error ", err)
	else:
		var scene := doc.generate_scene(state)
		var raw_mesh: Mesh = null
		var raw_skin: Skin = null
		for candidate in scene.find_children("*", "MeshInstance3D", true, false):
			if candidate.skin != null:
				raw_mesh = candidate.mesh
				raw_skin = candidate.skin
				break
		if raw_mesh == null:
			print("B107 RAW no skinned mesh")
		else:
			var fmt0: int = raw_mesh.surface_get_format(0)
			print("B107 RAW surfaces=%d compressed=%s binds raw=%d imported=%d" % [raw_mesh.get_surface_count(),
					(fmt0 & Mesh.ARRAY_FLAG_COMPRESS_ATTRIBUTES) != 0, raw_skin.get_bind_count(), character.body.skin.get_bind_count()])
			var raw := _corners(raw_mesh, character.body.skin, character, to_body)   # bind index -> the imported skin's name
			_report("raw", raw)
			_compare(imported, raw)
		scene.free()
	quit(0)


## {segment: [[point, normal, uv], ...]}: as step 19's _pictured_corners, for every segment at once.
func _corners(mesh: Mesh, skin: Skin, character: Node3D, to_body: Transform3D) -> Dictionary:
	var found := {}
	for surface in mesh.get_surface_count():
		var arrays := mesh.surface_get_arrays(surface)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
		var bones = arrays[Mesh.ARRAY_BONES]
		if bones == null or bones.is_empty():
			continue
		var each: int = bones.size() / vertices.size()
		for v in vertices.size():
			var bind: int = skin.get_bind_bone(bones[v * each])
			var bone: String = character.skeleton.get_bone_name(bind) if bind >= 0 else str(skin.get_bind_name(bones[v * each]))
			var segment := bone.trim_suffix(SHAPE)
			if not found.has(segment):
				found[segment] = []
			found[segment].append([to_body * vertices[v], (to_body.basis * normals[v]).normalized()])
	return found


func _report(which: String, corners: Dictionary) -> void:
	var names: Array = corners.keys()
	names.sort()
	for segment in names:
		var points: Array = corners[segment]
		var places := {}
		var front := 0
		var sides := 0
		var back := 0
		var near_front := 0
		var near_sides := 0
		var near_back := 0
		var closest := {"front": [], "sides": [], "back": []}
		for c in points:
			var n: Vector3 = c[1]
			places[c[0].snappedf(0.0005)] = true
			if n.z > 0.85:
				front += 1
			if absf(n.x) > 0.92 and absf(n.y) < 0.3:
				sides += 1
			if n.z < -0.5 and absf(n.y) < 0.5:
				back += 1
			# how far each corner is from flipping in or out of each count (the tightest of its conditions)
			var f := absf(n.z - 0.85)
			var s := minf(absf(absf(n.x) - 0.92), absf(absf(n.y) - 0.3)) if (absf(n.x) > 0.92 - NEAR and absf(n.y) < 0.3 + NEAR) else 9.0
			var b := minf(absf(n.z + 0.5), absf(absf(n.y) - 0.5)) if (n.z < -0.5 + NEAR and absf(n.y) < 0.5 + NEAR) else 9.0
			if f < NEAR:
				near_front += 1
			if s < NEAR:
				near_sides += 1
			if b < NEAR:
				near_back += 1
			closest["front"].append(f)
			closest["sides"].append(s)
			closest["back"].append(b)
		for k in closest:
			closest[k].sort()
		if which == "imported" and segment in CHECKED:
			# the corners closest to counting as a side: |n.x| of those with |n.y| < 0.3, largest first; and |n.y| of
			# those with |n.x| > 0.92
			var xs: Array = []
			var ys: Array = []
			for c in points:
				var n: Vector3 = c[1]
				if absf(n.y) < 0.3:
					xs.append(snappedf(absf(n.x), 0.0001))
				if absf(n.x) > 0.92:
					ys.append(snappedf(absf(n.y), 0.0001))
			xs.sort()
			xs.reverse()
			ys.sort()
			print("B107 SIDES %s largest |n.x| with |n.y|<0.3: %s ; |n.y| of those with |n.x|>0.92: %s" % [segment, str(xs.slice(0, 10)), str(ys.slice(0, 10))])
		var mark := " (checked by _wrapped_round)" if segment in CHECKED else ""
		print("B107 %s %s corners=%d places=%d front=%d sides=%d back=%d bar_met=%s near(<%.2f) front=%d sides=%d back=%d nearest front=%.5f sides=%.5f back=%.5f%s" % [
				which, segment, points.size(), places.size(), front, sides, back,
				front > 4 and sides > 4 and back > 4, NEAR, near_front, near_sides, near_back,
				closest["front"][0], closest["sides"][0], closest["back"][0], mark])


## Corner by corner (matched by place), how far the imported normals are from the raw ones, and any corner whose
## count membership differs between the two.
func _compare(imported: Dictionary, raw: Dictionary) -> void:
	for segment in CHECKED:
		if not imported.has(segment) or not raw.has(segment):
			print("B107 COMPARE %s missing" % segment)
			continue
		var by_place := {}
		for c in raw[segment]:
			var key: Vector3 = c[0].snappedf(0.0002)
			if not by_place.has(key):
				by_place[key] = []
			by_place[key].append(c[1])
		var worst := 0.0
		var matched := 0
		var flips := 0
		for c in imported[segment]:
			var key: Vector3 = c[0].snappedf(0.0002)
			if not by_place.has(key):
				continue
			var best := 9.0
			var best_n := Vector3.ZERO
			for n in by_place[key]:
				var d: float = (n - c[1]).length()
				if d < best:
					best = d
					best_n = n
			matched += 1
			worst = maxf(worst, best)
			var a: Vector3 = c[1]
			if (a.z > 0.85) != (best_n.z > 0.85) \
					or ((absf(a.x) > 0.92 and absf(a.y) < 0.3) != (absf(best_n.x) > 0.92 and absf(best_n.y) < 0.3)) \
					or ((a.z < -0.5 and absf(a.y) < 0.5) != (best_n.z < -0.5 and absf(best_n.y) < 0.5)):
				flips += 1
		print("B107 COMPARE %s imported=%d raw=%d matched_by_place=%d worst_normal_difference=%.5f corners_changing_count=%d" % [
				segment, imported[segment].size(), raw[segment].size(), matched, worst, flips])
