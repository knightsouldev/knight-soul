class_name Projectile
extends Node2D
## ORBE DE ALMA disparado pelo espectro. Voa em linha reta pelo chão, é barrado por
## paredes e pode ser esquivado. Os visuais (brilho, núcleo, sombra, luz) são
## nós da cena projectile.tscn.

## Direção do voo (espaço de chão). Definida por quem dispara.
var dir := Vector2.RIGHT
## Velocidade (unidades de chão por segundo).
@export var speed := 150.0
@export var damage := 16.0
## Raio de acerto.
@export var radius := 9.0
## Tempo máximo de vida (s).
@export var life := 4.0

var _trail := 0.0

func _physics_process(delta: float) -> void:
	var step := Iso.to_screen(dir * speed * delta)
	var from := global_position
	var to := from + step
	# parede no caminho? explode
	var q := PhysicsRayQueryParameters2D.create(from, to, 1)
	if not get_world_2d().direct_space_state.intersect_ray(q).is_empty():
		_burst()
		return
	global_position = to
	_trail -= delta
	if _trail <= 0.0:
		_trail = 0.05
		Fx.burst(get_tree(), global_position + Vector2(0, -14), Color(0.7, 0.4, 1.0, 0.7), 2, 14.0, 0.35, 0.0, 2.0)
	for n in get_tree().get_nodes_in_group("player"):
		var p := n as Player
		if p == null or p.is_dead():
			continue
		if Iso.to_ground(p.global_position - global_position).length() <= radius + p.body_radius:
			var info := HitInfo.new()
			info.damage = damage
			info.origin = global_position - Iso.to_screen(dir * 10.0)
			info.knockback = 90.0
			info.source = self
			if p.receive_hit(info):
				_burst()
				return
	life -= delta
	if life <= 0.0:
		_burst()

func _burst() -> void:
	Fx.spark(get_tree(), global_position + Vector2(0, -14), Color(0.8, 0.5, 1.0))
	Fx.burst(get_tree(), global_position + Vector2(0, -14), Color(0.7, 0.4, 1.0, 0.9), 8, 60.0, 0.4, 60.0, 2.0)
	queue_free()
