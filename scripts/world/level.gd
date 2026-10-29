class_name Level
extends Node2D
## FASE "RUÍNAS ESQUECIDAS" — o "diretor" da fase.
##
## O cenário em si (chão, paredes, decoração, inimigos, chefe, HUD...) está montado
## na cena ruinas.tscn e é editado direto no editor. Este script só COSTURA as peças:
##   - alinha o chão com o resto do mundo e gera as bordas (colisão + penhascos);
##   - monta a grade de navegação (A*) que os inimigos usam;
##   - ajusta os limites da câmera;
##   - liga a HUD, o menu de pausa e a tela final ao jogador e ao chefe;
##   - dispara a luta contra o chefe (gatilho da arena) e fecha a barreira de névoa;
##   - faz paredes e objetos altos ficarem translúcidos quando escondem o jogador;
##   - reiniciar / voltar ao menu.
##
## Nós usados (têm nome único na cena, por isso o "%Nome"):
##   %Chao (TileMapLayer)  %BordasDoChao  %Jogador  %Chefe  %Hud  %MenuPausa  %TelaFinal
##   %GatilhoArena (Area2D)  %BarreiraColisao  %BarreiraVisual  %Bussola  %EntradaArena

@export_group("Música")
@export var ambient_music := "ambient"
@export var boss_music := "boss"

@export_group("Câmera")
## Folga (pixels) entre o chão e o limite da câmera.
@export var camera_margin := Vector2(260, 280)

@export_group("Oclusão (paredes translúcidas)")
## Opacidade de uma parede/objeto alto quando esconde o jogador.
@export_range(0.1, 1.0) var occluded_alpha := 0.38

@onready var floor_layer: TileMapLayer = %Chao
@onready var borders: BordasDoChao = %BordasDoChao
@onready var player: Player = %Jogador
@onready var boss: Boss = %Chefe
@onready var hud: Hud = %Hud
@onready var pause_menu: PauseMenu = %MenuPausa
@onready var end_screen: EndScreen = %TelaFinal
@onready var arena_trigger: Area2D = %GatilhoArena
@onready var barrier_collision: CollisionPolygon2D = %BarreiraColisao
@onready var barrier_visual: Node2D = %BarreiraVisual
@onready var compass_markers: Node2D = %Bussola
@onready var arena_entry: Marker2D = %EntradaArena

var astar := AStarGrid2D.new()
var boss_started := false
var occluders: Array = []   # Nós com get_occlusion_rect() (grupo "oclusor")
var compass_points: Array[Vector2] = []
var compass_lengths: Array[float] = []
var _prog_t := 0.0
var _occ_t := 0.0

func _ready() -> void:
	add_to_group("level")
	Game.reset_run()
	_prepare_floor()
	borders.build()
	_build_nav()
	_set_camera_limits()
	_build_compass()
	occluders = get_tree().get_nodes_in_group("oclusor")
	arena_trigger.body_entered.connect(_on_arena_entered)
	hud.bind(player, boss)
	pause_menu.resume_requested.connect(pause_menu.close)
	pause_menu.restart_requested.connect(restart)
	pause_menu.menu_requested.connect(go_menu)
	end_screen.retry_requested.connect(restart)
	end_screen.menu_requested.connect(go_menu)
	end_screen.continue_requested.connect(_continue_exploring)
	Game.player_died.connect(_on_player_died)
	Game.boss_defeated.connect(_on_boss_defeated)
	Sfx.play_music(ambient_music, 2.0)

# ------------------------------------------------------------------ chão
func _prepare_floor() -> void:
	# Rede de segurança 1: se por algum motivo o TileMapLayer estiver vazio, reconstrói do arquivo.
	if floor_layer.get_used_cells().is_empty():
		push_warning("O TileMapLayer 'Chao' está vazio; reconstruindo o chão a partir de resources/data/ruinas_chao.json")
		_rebuild_floor_from_json()
	# Rede de segurança 2: alinha o chão à matemática isométrica do jogo (paredes, props e
	# inimigos são posicionados com ela). Se precisar corrigir, avisa o valor certo.
	var c: Vector2i = floor_layer.get_used_cells()[0]
	var expected := Iso.cell_to_screen(Vector2(c.x + 0.5, c.y + 0.5))
	var actual := floor_layer.to_global(floor_layer.map_to_local(c))
	var diff := expected - actual
	if diff.length() > 0.5:
		push_warning("Chão desalinhado em %s px; corrigindo. Para fixar no editor, ajuste a Position do nó Chao para %s" % [diff, floor_layer.position + diff])
		floor_layer.global_position += diff

func _rebuild_floor_from_json() -> void:
	var f := FileAccess.open("res://resources/data/ruinas_chao.json", FileAccess.READ)
	if f == null:
		return
	var rows := JSON.parse_string(f.get_as_text()) as Array
	for y in rows.size():
		var row: String = rows[y]
		for x in row.length():
			if row[x] == ".":
				floor_layer.set_cell(Vector2i(x, y), 0, Vector2i(_floor_variant(x, y), 0))

func _floor_variant(x: int, y: int) -> int:
	var h := absi((x * 73856093) ^ (y * 19349663)) % 100
	for pair in [[26, 0], [44, 2], [58, 6], [70, 1], [80, 7], [89, 4], [94, 5], [97, 3]]:
		if h < pair[0]:
			return pair[1]
	return 6

func _cell_of(screen_pos: Vector2) -> Vector2i:
	return floor_layer.local_to_map(floor_layer.to_local(screen_pos))

# ------------------------------------------------------------------ navegação (A*)
## Grade usada pelos inimigos para contornar paredes. Células sem chão e células de
## objetos marcados como "blocks_navigation" são obstáculos.
func _build_nav() -> void:
	var used := floor_layer.get_used_rect().grow(2)
	astar.region = used
	astar.cell_size = Vector2(1, 1)
	astar.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	astar.update()
	for y in range(used.position.y, used.end.y):
		for x in range(used.position.x, used.end.x):
			if floor_layer.get_cell_source_id(Vector2i(x, y)) == -1:
				astar.set_point_solid(Vector2i(x, y), true)
	for n in get_tree().get_nodes_in_group("bloqueia_navegacao"):
		var cell := _cell_of((n as Node2D).global_position)
		if astar.region.has_point(cell):
			astar.set_point_solid(cell, true)

## Caminho (lista de pontos de tela) entre duas posições; vazio se não houver.
func find_path(from_screen: Vector2, to_screen: Vector2) -> Array[Vector2]:
	var out: Array[Vector2] = []
	var a := _cell_of(from_screen)
	var b := _cell_of(to_screen)
	if not astar.region.has_point(a) or not astar.region.has_point(b):
		return out
	if astar.is_point_solid(b):
		return out
	var was_solid := astar.is_point_solid(a)
	if was_solid:
		astar.set_point_solid(a, false)
	var ids := astar.get_id_path(a, b)
	if was_solid:
		astar.set_point_solid(a, true)
	for i in range(1, ids.size()):
		out.append(floor_layer.to_global(floor_layer.map_to_local(ids[i])))
	return out

# ------------------------------------------------------------------ câmera e bússola
func _set_camera_limits() -> void:
	var minp := Vector2(1e9, 1e9)
	var maxp := Vector2(-1e9, -1e9)
	for c in floor_layer.get_used_cells():
		var p := floor_layer.to_global(floor_layer.map_to_local(c))
		minp = minp.min(p)
		maxp = maxp.max(p)
	player.cam.set_world_limits(Rect2(minp - camera_margin, (maxp - minp) + camera_margin * 2.0))
	player.cam.reset_smoothing()

## A bússola da HUD usa os Marker2D do nó "Bussola" (em ordem) como rota da fase.
func _build_compass() -> void:
	var acc := 0.0
	for m in compass_markers.get_children():
		var p := Iso.to_ground((m as Node2D).global_position)
		if not compass_points.is_empty():
			acc += p.distance_to(compass_points[compass_points.size() - 1])
		compass_points.append(p)
		compass_lengths.append(acc)

func _path_progress() -> float:
	if compass_points.size() < 2:
		return 0.0
	var pc := Iso.to_ground(player.global_position)
	var best_d := 1e9
	var best_len := 0.0
	for i in range(1, compass_points.size()):
		var a: Vector2 = compass_points[i - 1]
		var b: Vector2 = compass_points[i]
		var ab := b - a
		var t := clampf((pc - a).dot(ab) / maxf(ab.length_squared(), 0.001), 0.0, 1.0)
		var d := pc.distance_to(a + ab * t)
		if d < best_d:
			best_d = d
			best_len = compass_lengths[i - 1] + ab.length() * t
	return best_len / maxf(compass_lengths[compass_lengths.size() - 1], 0.001)

# ------------------------------------------------------------------ chefe
func _on_arena_entered(body: Node2D) -> void:
	if boss_started or not (body is Player) or Game.run_state != "playing":
		return
	boss_started = true
	barrier_collision.set_deferred("disabled", false)
	barrier_visual.visible = true
	Sfx.play("fog_seal", 0.0, 1.0, 0.0)
	Fx.shake(get_tree(), 4.0)
	Sfx.play_music(boss_music, 2.5)
	Game.boss_started.emit()
	boss.activate()

func _on_player_died() -> void:
	end_screen.show_defeat()

func _on_boss_defeated() -> void:
	Sfx.play("victory", -2.0, 1.0, 0.0)
	barrier_collision.set_deferred("disabled", true)
	var tw := barrier_visual.create_tween()
	tw.tween_property(barrier_visual, "modulate:a", 0.0, 1.5)
	tw.tween_callback(barrier_visual.hide)
	end_screen.show_victory(Game.souls)

func _continue_exploring() -> void:
	end_screen.hide_screen()
	get_tree().paused = false

func restart() -> void:
	get_tree().paused = false
	Game.reset_run()
	get_tree().reload_current_scene()

func go_menu() -> void:
	get_tree().paused = false
	Engine.time_scale = 1.0
	Sfx.stop_music(0.5)
	get_tree().change_scene_to_file("res://scenes/main/main_menu.tscn")

# ------------------------------------------------------------------ loop
func _physics_process(delta: float) -> void:
	_prog_t -= delta
	if _prog_t <= 0.0:
		_prog_t = 0.2
		hud.set_progress(_path_progress())
	_occ_t -= delta
	if _occ_t <= 0.0:
		_occ_t = 0.05
		_update_occluders(0.05)

## Paredes e objetos altos que estão NA FRENTE do jogador ficam translúcidos.
func _update_occluders(step: float) -> void:
	var pp := player.global_position
	var head := pp + Vector2(0, -20)
	for node in occluders:      # "node" é dinâmico: paredes e props têm get_occlusion_rect()
		if not is_instance_valid(node):
			continue
		var npos: Vector2 = node.global_position
		if absf(npos.x - pp.x) > 150.0 or absf(npos.y - pp.y) > 160.0:
			if node.modulate.a < 1.0:
				node.modulate.a = minf(1.0, node.modulate.a + step * 6.0)
			continue
		var rect: Rect2 = node.get_occlusion_rect()
		var r := Rect2(npos + rect.position, rect.size).grow(3.0)
		var behind := pp.y < npos.y - 2.0
		var want := occluded_alpha if (behind and r.has_point(head)) else 1.0
		node.modulate.a = move_toward(node.modulate.a, want, step * 6.0)

# ------------------------------------------------------------------ entradas globais
func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause"):
		if end_screen.visible:
			return
		if pause_menu.visible:
			pause_menu.close()
		else:
			pause_menu.open()
		get_viewport().set_input_as_handled()
		return
	# teclas de depuração (para testar rápido)
	if event is InputEventKey and event.pressed and not event.echo:
		var k := (event as InputEventKey).keycode
		if k == KEY_F1:
			Game.god_mode = not Game.god_mode
			Game.notify("[debug] invencível: %s" % ("ligado" if Game.god_mode else "desligado"))
		elif k == KEY_F2 and boss_started and not boss.dead:
			boss.health.damage(boss.health.current - boss.health.maximum * 0.08)
			Game.notify("[debug] chefe com 8% de vida")
		elif k == KEY_F3 and not boss_started:
			player.global_position = arena_entry.global_position
			player.cam.reset_smoothing()
			Game.notify("[debug] teleporte para a entrada da arena")
