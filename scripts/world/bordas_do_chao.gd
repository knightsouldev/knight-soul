@tool
class_name BordasDoChao
extends Node2D
## BORDAS AUTOMÁTICAS DO CHÃO.
##
## Olha para o TileMapLayer do chão e gera sozinho:
##   1) as PAREDES INVISÍVEIS (colisão) em volta de todo o chão — o jogador e os
##      inimigos não caem no abismo nem atravessam as muralhas;
##   2) os PENHASCOS (as faces de pedra que descem pela borda da plataforma).
##
## Por isso, quando você pintar/apagar chão no TileMapLayer, as bordas se ajustam
## sozinhas: basta rodar o jogo (ou marcar "regenerate" para ver os penhascos no editor).
## Nada precisa ser desenhado à mão.

## O TileMapLayer do chão (nó "Chao").
@export var floor_layer: TileMapLayer
## Gera as paredes invisíveis de colisão.
@export var generate_collision := true
## Gera os penhascos visuais.
@export var generate_cliffs := true
## Marque para regenerar as bordas aqui no editor depois de mudar o chão.
@export var regenerate := false:
	set(value):
		regenerate = false
		if value and is_inside_tree():
			build()

const CLIFF_LEFT: Array[Texture2D] = [
	preload("res://assets/environments/cliff_L_0.png"),
	preload("res://assets/environments/cliff_L_1.png"),
	preload("res://assets/environments/cliff_L_2.png"),
]
const CLIFF_RIGHT: Array[Texture2D] = [
	preload("res://assets/environments/cliff_R_0.png"),
	preload("res://assets/environments/cliff_R_1.png"),
	preload("res://assets/environments/cliff_R_2.png"),
]

var _generated: Array[Node] = []

func _ready() -> void:
	# No editor mostramos os penhascos para você ver o cenário completo.
	# No jogo, o Level chama build() depois de alinhar o chão.
	if Engine.is_editor_hint():
		build()

## (Re)constrói colisões e penhascos a partir do chão atual.
func build() -> void:
	for n in _generated:
		if is_instance_valid(n):
			n.queue_free()
	_generated.clear()
	if floor_layer == null or floor_layer.tile_set == null:
		return
	var cells := {}
	for c in floor_layer.get_used_cells():
		cells[c] = true
	if cells.is_empty():
		return
	var rect := floor_layer.get_used_rect()
	if generate_cliffs:
		_build_cliffs(cells)
	if generate_collision and not Engine.is_editor_hint():
		_build_collision(cells, rect)

func _cell_center(cell: Vector2i) -> Vector2:
	return to_local(floor_layer.to_global(floor_layer.map_to_local(cell)))

func _near_floor(cells: Dictionary, x: int, y: int) -> bool:
	for dy in range(-1, 2):
		for dx in range(-1, 2):
			if cells.has(Vector2i(x + dx, y + dy)):
				return true
	return false

func _is_border(cells: Dictionary, x: int, y: int) -> bool:
	return not cells.has(Vector2i(x, y)) and _near_floor(cells, x, y)

func _build_collision(cells: Dictionary, rect: Rect2i) -> void:
	var half := Vector2(floor_layer.tile_set.tile_size) * 0.5
	var body := StaticBody2D.new()
	body.name = "ColisaoGerada"
	body.collision_layer = 1     # camada "world"
	body.collision_mask = 0
	add_child(body)
	_generated.append(body)
	for y in range(rect.position.y - 1, rect.end.y + 1):
		var x := rect.position.x - 1
		while x <= rect.end.x:
			if _is_border(cells, x, y):
				var x0 := x
				while x <= rect.end.x and _is_border(cells, x, y):
					x += 1
				var c0 := _cell_center(Vector2i(x0, y))
				var c1 := _cell_center(Vector2i(x - 1, y))
				# faixa de células vizinhas = paralelogramo
				var poly := CollisionPolygon2D.new()
				poly.polygon = PackedVector2Array([
					c0 + Vector2(0, -half.y), c1 + Vector2(half.x, 0),
					c1 + Vector2(0, half.y), c0 + Vector2(-half.x, 0)])
				body.add_child(poly)
			else:
				x += 1

func _build_cliffs(cells: Dictionary) -> void:
	var holder := Node2D.new()
	holder.name = "PenhascosGerados"
	holder.z_index = -12
	add_child(holder)
	_generated.append(holder)
	var half := Vector2(floor_layer.tile_set.tile_size) * 0.5
	for key in cells.keys():
		var cell: Vector2i = key
		var c := _cell_center(cell)
		if not cells.has(Vector2i(cell.x + 1, cell.y)):
			var s := Sprite2D.new()
			s.texture = CLIFF_RIGHT[absi(cell.x * 7 + cell.y * 3) % 3]
			s.centered = false
			s.position = c
			holder.add_child(s)
		if not cells.has(Vector2i(cell.x, cell.y + 1)):
			var s2 := Sprite2D.new()
			s2.texture = CLIFF_LEFT[absi(cell.x * 5 + cell.y * 11) % 3]
			s2.centered = false
			s2.position = c + Vector2(-half.x, 0)
			holder.add_child(s2)
