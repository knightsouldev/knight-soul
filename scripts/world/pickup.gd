class_name Pickup
extends Node2D
## ITEM NO CHÃO: orbe de almas ou fragmento de frasco. É coletado ao chegar perto.
## Para colocar um novo no mapa: arraste scenes/effects/pickup.tscn para o Level e
## escolha o tipo e a quantidade no Inspector.

## "souls" = dá almas; "flask" = restaura frascos de cura e óleo.
@export_enum("souls", "flask") var kind := "souls"
## Quantidade de almas (só vale para "souls").
@export var amount := 100
## Distância (unidades de chão) para coletar.
@export var pickup_radius := 24.0

var _t := 0.0
var _visual: Node2D

func _ready() -> void:
	_t = randf() * 6.0
	var orb := $Orbe as AnimatedSprite2D
	var flask := $IconeFrasco as Sprite2D
	orb.visible = kind == "souls"
	flask.visible = kind == "flask"
	_visual = orb if kind == "souls" else flask
	orb.play("default")

func _physics_process(delta: float) -> void:
	_t += delta
	# flutua para cima e para baixo
	_visual.position.y = -18.0 + sin(_t * 2.5) * 3.0
	var p := get_tree().get_first_node_in_group("player") as Player
	if p == null or p.is_dead():
		return
	if Iso.to_ground(p.global_position - global_position).length() < pickup_radius:
		_collect()

func _collect() -> void:
	Sfx.play("pickup", -2.0)
	Fx.souls_fx(get_tree(), global_position + Vector2(0, -14))
	if kind == "souls":
		Game.add_souls(amount)
		Game.notify("Essência esquecida: +%d almas" % amount)
	else:
		Game.refill_items()
		Game.notify("Frascos e óleo restaurados")
	queue_free()
