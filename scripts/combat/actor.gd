class_name Actor
extends CharacterBody2D
## BASE DE TODO PERSONAGEM (jogador, inimigos e chefe).
##
## Cuida de: vida, sprite com duas vistas (frente/costas) + espelhamento,
## flash de dano, movimento em "espaço de chão" e empurrão (knockback).
##
## A cena do personagem precisa ter estes filhos (já vêm prontos nas cenas):
##   Sprite   (AnimatedSprite2D)  -> aparência e animações
##   Sombra   (Sprite2D)          -> sombra no chão
##   Colisao  (CollisionShape2D)  -> colisão com paredes
##   Vida     (Node com health.gd)
##
## "Espaço de chão": o mapa é isométrico (losangos 2:1). Para que distâncias e
## ângulos sejam reais, as contas usam a tela com o eixo Y dobrado (veja iso.gd).

@export_group("Corpo")
## Vida máxima.
@export var max_health := 100.0
## Raio do corpo (colisão suave entre personagens e área que o golpe precisa tocar).
@export var body_radius := 10.0
## Se ligado, o tamanho da colisão e da sombra seguem o raio acima.
@export var auto_fit_collision := true

var health: Health
var sprite: AnimatedSprite2D
var shadow: Sprite2D
var body_shape: CollisionShape2D
var facing := Vector2(1, 1).normalized()   # direção em espaço de chão
var view_back := false                      # true = mostrando as costas
var ground_vel := Vector2.ZERO              # velocidade desejada (espaço de chão)
var knock_vel := Vector2.ZERO               # empurrão de golpes recebidos
var dead := false

var _mat: ShaderMaterial
var _flash := 0.0
var _flash_decay := 8.0
var _cur_base := ""

## Liga os nós da cena. Os scripts filhos chamam super._ready() primeiro.
func _ready() -> void:
	sprite = $Sprite as AnimatedSprite2D
	shadow = $Sombra as Sprite2D
	body_shape = $Colisao as CollisionShape2D
	health = $Vida as Health
	_mat = sprite.material as ShaderMaterial
	if auto_fit_collision:
		_fit_collision_to_radius()
	health.setup(max_health)
	health.died.connect(_on_health_died)

func _fit_collision_to_radius() -> void:
	var shp := ConvexPolygonShape2D.new()
	var pts := PackedVector2Array()
	for i in 8:
		var a := TAU * float(i) / 8.0 + TAU / 16.0
		pts.append(Vector2(cos(a) * body_radius * 0.8, sin(a) * body_radius * 0.4))
	shp.points = pts
	body_shape.shape = shp
	shadow.scale = Vector2.ONE * (body_radius * 2.8 / 64.0)

# ------------------------------------------------------------------ visual
## Define para onde o personagem olha (espaço de chão). Escolhe frente/costas e espelha.
func set_facing(dir_ground: Vector2) -> void:
	if dir_ground.length() < 0.01:
		return
	facing = dir_ground.normalized()
	if absf(facing.y) > 0.28:
		view_back = facing.y < 0.0
	if absf(facing.x) > 0.12:
		sprite.flip_h = facing.x < 0.0

## Nome real da animação: "walk" vira "walk_front" ou "walk_back".
func anim_name(base: String) -> String:
	return base + ("_back" if view_back else "_front")

func play_loop(base: String, speed: float = 1.0) -> void:
	var n := anim_name(base)
	if sprite.animation != StringName(n) or not sprite.is_playing():
		var f := sprite.frame
		var same := _cur_base == base
		sprite.play(n)
		if same:
			sprite.frame = f
	sprite.speed_scale = speed
	_cur_base = base

func play_once(base: String, speed: float = 1.0) -> void:
	sprite.speed_scale = speed
	sprite.play(anim_name(base))
	_cur_base = base

## Mostra um quadro específico (animações guiadas por fases: ataque, cura, esquiva).
func show_frame(base: String, idx: int) -> void:
	var n := anim_name(base)
	if sprite.animation != StringName(n):
		sprite.animation = n
	sprite.stop()
	sprite.frame = clampi(idx, 0, sprite.sprite_frames.get_frame_count(n) - 1)
	_cur_base = base

## Converte (fase, progresso 0..1) em número do quadro. Fase 0 = preparação,
## 1 = golpe, 2 = recuperação. Os 3 números dizem quantos quadros cada fase tem.
static func phase_frame(wind_n: int, act_n: int, rec_n: int, phase: int, p: float) -> int:
	var q := clampf(p, 0.0, 0.999)
	if phase == 0:
		return int(q * float(wind_n))
	if phase == 1:
		return wind_n + int(q * float(act_n))
	return wind_n + act_n + int(q * float(rec_n))

## Faz o sprite piscar numa cor (dano = branco/vermelho, cura = azul).
func flash(strength: float = 1.0, color: Color = Color.WHITE, decay: float = 8.0) -> void:
	_flash = strength
	_flash_decay = decay
	_mat.set_shader_parameter("flash_color", color)
	_mat.set_shader_parameter("flash", _flash)

func _process(delta: float) -> void:
	if _flash > 0.0:
		_flash = maxf(0.0, _flash - delta * _flash_decay)
		_mat.set_shader_parameter("flash", _flash)

# ------------------------------------------------------------------ movimento
## Move o personagem. vel_ground está em espaço de chão (convertido para a tela aqui).
func move_actor(vel_ground: Vector2, delta: float) -> void:
	velocity = Iso.to_screen(vel_ground + knock_vel)
	move_and_slide()
	knock_vel = knock_vel.move_toward(Vector2.ZERO, 620.0 * delta)

func ground_dist_to(other: Node2D) -> float:
	return Iso.to_ground(other.global_position - global_position).length()

func ground_dir_to(point_screen: Vector2) -> Vector2:
	var d := Iso.to_ground(point_screen - global_position)
	return d.normalized() if d.length() > 0.01 else facing

## Posição do "peito" (onde saem faíscas e sangue).
func chest_pos() -> Vector2:
	return global_position + Vector2(0.0, -18.0)

# ------------------------------------------------------------------ para sobrescrever
## Recebe um golpe. Retorna true se o golpe foi aplicado.
func receive_hit(_info: HitInfo) -> bool:
	return false

func _on_health_died() -> void:
	pass
