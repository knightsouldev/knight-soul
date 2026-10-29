class_name Wraith
extends Enemy
## ESPECTRO (Criatura Sobrenatural): flutua, mantém distância do jogador e dispara
## orbes de alma telegrafados (uma linha roxa mostra a direção antes do tiro).
## Herda a navegação e o dano de enemy.gd; só a IA de combate é diferente.

@export_group("Projétil")
## Cena do projétil disparado (res://scenes/effects/projectile.tscn).
@export var projectile_scene: PackedScene
## Altura do sprite acima do chão (ele flutua).
@export var hover_height := 10.0

var strafe_dir := 1.0
var strafe_t := 0.0
var bolt_fired := false

func _ready() -> void:
	super._ready()
	sprite.position = Vector2(0, -hover_height)

func _think(delta: float) -> void:
	var dist := 99999.0
	var los := false
	if _target_alive():
		dist = ground_dist_to(target)
		los = _los_to(target.global_position)
	match ai:
		AI.IDLE, AI.PATROL, AI.ALERT:
			ground_vel = ground_vel.move_toward(Vector2.ZERO, 600.0 * delta)
			play_loop("idle")
			if _target_alive() and Game.run_state == "playing":
				if (dist < stats.detect_range and los) or (aggro and dist < stats.lose_range):
					aggro = true
					_enter(AI.CHASE)
		AI.CHASE:
			_think_engage(delta, dist, los)
		AI.WINDUP:
			_think_cast(delta)
		AI.ATTACK:
			_think_release(delta)
		AI.RECOVER:
			ground_vel = ground_vel.move_toward(Vector2.ZERO, 700.0 * delta)
			show_frame("cast", Actor.phase_frame(4, 1, 2, 2, ai_t / stats.recover_time))
			if ai_t >= stats.recover_time:
				attack_cd = stats.cooldown_time
				_enter(AI.CHASE)
		AI.HURT:
			ground_vel = Vector2.ZERO
			show_frame("hurt", 0 if ai_t < 0.15 else 1)
			if ai_t >= stats.stagger_time:
				_enter(AI.CHASE)
	move_actor(ground_vel, delta)

## Mantém a distância ideal: aproxima, recua ou circula o jogador; atira quando pode.
func _think_engage(delta: float, dist: float, los: bool) -> void:
	if not _target_alive() or dist > stats.lose_range:
		aggro = false
		_enter(AI.IDLE)
		return
	var spd := stats.chase_speed
	set_facing(ground_dir_to(target.global_position))
	play_loop("idle", 1.2)
	if attack_cd <= 0.0 and los and dist > 110.0 and dist < stats.attack_range:
		_enter(AI.WINDUP)
		attack_dir = ground_dir_to(target.global_position)
		bolt_fired = false
		tele.show_line(dist + 30.0, 16.0, attack_dir, Color(0.7, 0.35, 1.0))
		Sfx.play("wraith_cast", -4.0)
		return
	if dist > stats.preferred_distance_max or not los:
		_go_to(target.global_position, spd, delta)
	elif dist < stats.preferred_distance_min:
		var away := -ground_dir_to(target.global_position)
		ground_vel = ground_vel.move_toward(away * spd, 700.0 * delta)
	else:
		strafe_t -= delta
		if strafe_t <= 0.0:
			strafe_t = randf_range(1.5, 3.0)
			strafe_dir = -strafe_dir
		var to_t := ground_dir_to(target.global_position)
		var side := Vector2(-to_t.y, to_t.x) * strafe_dir
		ground_vel = ground_vel.move_toward(side * spd * 0.6, 700.0 * delta)

func _think_cast(delta: float) -> void:
	var w := stats.windup_time
	var p := clampf(ai_t / w, 0.0, 1.0)
	ground_vel = ground_vel.move_toward(Vector2.ZERO, 900.0 * delta)
	if p < 0.7 and _target_alive():
		attack_dir = attack_dir.lerp(ground_dir_to(target.global_position), 0.15).normalized()
		tele.dir = attack_dir
		tele.length = ground_dist_to(target) + 30.0
	set_facing(attack_dir)
	tele.set_progress(p)
	show_frame("cast", Actor.phase_frame(4, 1, 2, 0, p))
	if ai_t >= w:
		tele.hide_it()
		_enter(AI.ATTACK)

func _think_release(_delta: float) -> void:
	ground_vel = Vector2.ZERO
	show_frame("cast", Actor.phase_frame(4, 1, 2, 1, 0.5))
	if not bolt_fired:
		bolt_fired = true
		var b := projectile_scene.instantiate() as Projectile
		b.dir = attack_dir
		b.speed = stats.bolt_speed
		b.damage = stats.damage
		Fx.world(get_tree()).add_child(b)
		b.global_position = global_position + Iso.to_screen(attack_dir * 14.0)
		Sfx.play("wraith_bolt", -3.0)
	if ai_t >= stats.active_time:
		_enter(AI.RECOVER)

func _after_death() -> void:
	Sfx.play("wraith_die", -3.0)
	var tw := create_tween()
	tw.tween_interval(0.8)
	tw.tween_property(self, "modulate:a", 0.0, 1.6)
	tw.tween_callback(queue_free)
