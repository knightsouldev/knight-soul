class_name Fx
extends RefCounted
## FÁBRICA DE EFEITOS VISUAIS. Os scripts de jogo chamam Fx.spark(...), Fx.slash(...) etc.
##  - spark e slash são CENAS editáveis (res://scenes/effects/).
##  - burst/blood/dust/heal_fx/souls_fx são partículas leves criadas por código
##    (cor, quantidade e velocidade estão nos parâmetros de cada função).

const SPARK_SCENE: PackedScene = preload("res://scenes/effects/spark.tscn")
const SLASH_SCENE: PackedScene = preload("res://scenes/effects/slash.tscn")

## Camada onde os efeitos entram (o nó "Mundo" do Level está no grupo "fx_layer").
static func world(tree: SceneTree) -> Node:
	var n := tree.get_first_node_in_group("fx_layer")
	if n != null:
		return n
	return tree.current_scene

## Faísca de impacto.
static func spark(tree: SceneTree, pos: Vector2, tint: Color = Color(1.0, 0.92, 0.75)) -> void:
	var s := SPARK_SCENE.instantiate() as AnimatedSprite2D
	s.modulate = tint
	world(tree).add_child(s)
	s.global_position = pos

## Arco de corte da espada. dir_ground = direção do golpe em espaço de chão.
static func slash(tree: SceneTree, pos: Vector2, dir_ground: Vector2, flip: bool, tint: Color = Color(1, 1, 1, 0.95)) -> void:
	var s := SLASH_SCENE.instantiate() as SlashEffect
	world(tree).add_child(s)
	s.global_position = pos
	s.setup(dir_ground, flip, tint)

## Explosão de partículas genérica.
static func burst(tree: SceneTree, pos: Vector2, color: Color, amount: int = 10, speed: float = 90.0, life: float = 0.5, gravity: float = 220.0, size: float = 2.0, up_bias: bool = false) -> void:
	var p := CPUParticles2D.new()
	p.emitting = false
	p.one_shot = true
	p.amount = amount
	p.lifetime = life
	p.explosiveness = 1.0
	p.direction = Vector2(0, -1) if up_bias else Vector2(0, -0.4)
	p.spread = 70.0 if up_bias else 180.0
	p.initial_velocity_min = speed * 0.4
	p.initial_velocity_max = speed
	p.gravity = Vector2(0, gravity)
	p.scale_amount_min = size * 0.6
	p.scale_amount_max = size
	p.color = color
	p.z_index = 19
	world(tree).add_child(p)
	p.global_position = pos
	p.emitting = true
	tree.create_timer(life + 0.3).timeout.connect(p.queue_free)

static func blood(tree: SceneTree, pos: Vector2, color: Color) -> void:
	burst(tree, pos, color, 12, 110.0, 0.55, 380.0, 2.4)

static func dust(tree: SceneTree, pos: Vector2) -> void:
	burst(tree, pos, Color(0.55, 0.5, 0.42, 0.6), 7, 34.0, 0.45, -10.0, 3.0)

static func heal_fx(tree: SceneTree, pos: Vector2) -> void:
	burst(tree, pos, Color(0.45, 0.75, 1.0, 0.9), 16, 55.0, 0.9, -60.0, 2.2, true)

static func souls_fx(tree: SceneTree, pos: Vector2) -> void:
	burst(tree, pos, Color(0.5, 0.8, 1.0, 0.9), 14, 40.0, 1.1, -70.0, 2.4, true)

## Anel de choque no chão (golpe de área do chefe).
static func ring(tree: SceneTree, pos: Vector2, radius: float, color: Color, duration: float = 0.45) -> void:
	var r := Shockwave.new()
	r.max_radius = radius
	r.color = color
	r.duration = duration
	world(tree).add_child(r)
	r.global_position = pos

## Rachadura roxa no chão (some sozinha).
static func crack(tree: SceneTree, pos: Vector2) -> void:
	var s := Sprite2D.new()
	s.texture = load("res://assets/effects/crack.png") as Texture2D
	s.z_index = -6
	s.modulate = Color(1, 1, 1, 0.9)
	world(tree).add_child(s)
	s.global_position = pos
	var tw := s.create_tween()
	tw.tween_interval(1.4)
	tw.tween_property(s, "modulate:a", 0.0, 1.6)
	tw.tween_callback(s.queue_free)

## Treme a câmera (qualquer Camera2D no grupo "camera" com método shake).
static func shake(tree: SceneTree, amount: float) -> void:
	tree.call_group("camera", "shake", amount)
