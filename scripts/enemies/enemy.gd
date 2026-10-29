class_name Enemy
extends Actor
## INIMIGO CORPO A CORPO (Soldado Corrompido e Guardião Decaído usam este script).
## Os números ficam num arquivo de atributos (EnemyStats, em res://resources/stats/).
##
## Estados da IA (variável "ai"):
##   IDLE/PATROL -> ALERT (notou o jogador) -> CHASE (persegue)
##   -> WINDUP (prepara o golpe, mostra o aviso vermelho no chão) -> ATTACK (golpe)
##   -> RECOVER (parado, vulnerável) -> volta a CHASE.   HURT = atordoado.  DEAD = morto.
##
## O espectro (wraith.gd) e o chefe (boss.gd) herdam deste script.

enum AI { IDLE, PATROL, ALERT, CHASE, WINDUP, ATTACK, RECOVER, HURT, DEAD }

@export_group("Atributos")
## Arquivo .tres com vida, dano, velocidades, alcance etc. (veja EnemyStats).
@export var stats: EnemyStats

@export_group("Patrulha")
## Marcadores (Marker2D) por onde ele anda. Vazio = fica parado no lugar.
## Arraste os nós "Marker2D" da pasta Marcadores/Patrulhas para cá.
@export var patrol_points: Array[NodePath] = []

@export_group("Animação do ataque")
## Quantos quadros da animação "attack" são de preparação, de golpe e de recuperação.
@export var attack_frames_windup := 3
@export var attack_frames_strike := 2
@export var attack_frames_recover := 3

@export_group("Efeitos")
## Cor das partículas ao ser ferido.
@export var blood_color := Color(0.35, 0.1, 0.5)
## Cor do aviso de perigo no chão.
@export var telegraph_color := Color(0.9, 0.18, 0.2)

var ai: AI = AI.IDLE
var ai_t := 0.0
var home := Vector2.ZERO
var patrol: Array[Vector2] = []
var patrol_i := 0
var wait_t := 0.0
var target: Player = null
var level: Node = null
var path: Array[Vector2] = []
var repath_t := 0.0
var attack_cd := 0.0
var attack_hit := false
var attack_dir := Vector2.RIGHT
var aggro := false
var tele: Telegraph

func _ready() -> void:
	# a vida e o raio do corpo vêm do arquivo de atributos
	max_health = stats.max_health
	body_radius = stats.body_radius
	super._ready()
	tele = $Telegrafo as Telegraph
	add_to_group("enemies")
	home = global_position
	level = get_tree().get_first_node_in_group("level")
	for p in patrol_points:
		var m := get_node_or_null(p) as Node2D
		if m != null:
			patrol.append(m.global_position)
	set_facing(Vector2(-1, 1))
	play_loop("idle")
	ai_t = randf() * 2.0

func is_targetable() -> bool:
	return not dead

func _find_target() -> void:
	if target == null or not is_instance_valid(target):
		target = get_tree().get_first_node_in_group("player") as Player

func _target_alive() -> bool:
	return target != null and is_instance_valid(target) and not target.is_dead()

func _physics_process(delta: float) -> void:
	if dead:
		_dead_tick(delta)
		return
	_find_target()
	ai_t += delta
	attack_cd = maxf(0.0, attack_cd - delta)
	repath_t -= delta
	_think(delta)

func _dead_tick(delta: float) -> void:
	knock_vel = knock_vel.move_toward(Vector2.ZERO, 500.0 * delta)
	velocity = Iso.to_screen(knock_vel)
	move_and_slide()

# ------------------------------------------------------------------ IA (corpo a corpo)
func _think(delta: float) -> void:
	var dist := 99999.0
	var los := false
	if _target_alive():
		dist = ground_dist_to(target)
		los = _los_to(target.global_position)
	match ai:
		AI.IDLE, AI.PATROL:
			_think_idle(delta, dist, los)
		AI.ALERT:
			ground_vel = ground_vel.move_toward(Vector2.ZERO, 900.0 * delta)
			if _target_alive():
				set_facing(ground_dir_to(target.global_position))
			play_loop("idle")
			if ai_t >= 0.4:
				_enter(AI.CHASE)
		AI.CHASE:
			_think_chase(delta, dist, los)
		AI.WINDUP:
			_think_windup(delta)
		AI.ATTACK:
			_think_attack(delta)
		AI.RECOVER:
			_think_recover(delta)
		AI.HURT:
			_think_hurt(delta)
	ground_vel += _separation() * delta
	move_actor(ground_vel, delta)

func _enter(s: AI) -> void:
	ai = s
	ai_t = 0.0

func _think_idle(delta: float, dist: float, los: bool) -> void:
	# notou o jogador?
	if _target_alive() and Game.run_state == "playing":
		if (dist < stats.detect_range and los) or (aggro and dist < stats.lose_range):
			aggro = true
			Fx.burst(get_tree(), chest_pos() + Vector2(0, -12), Color(0.8, 0.4, 1.0, 0.9), 6, 30.0, 0.5, -30.0, 2.0, true)
			_enter(AI.ALERT)
			return
	if patrol.size() >= 2:
		var dest: Vector2 = patrol[patrol_i]
		var d := Iso.to_ground(dest - global_position)
		if wait_t > 0.0:
			wait_t -= delta
			ground_vel = ground_vel.move_toward(Vector2.ZERO, 900.0 * delta)
			play_loop("idle")
		elif d.length() < 10.0:
			patrol_i = (patrol_i + 1) % patrol.size()
			wait_t = 1.2
		else:
			_go_to(dest, stats.walk_speed, delta)
			play_loop("walk")
	else:
		var back := Iso.to_ground(home - global_position)
		if back.length() > 14.0 and not aggro:
			_go_to(home, stats.walk_speed, delta)
			play_loop("walk")
		else:
			ground_vel = ground_vel.move_toward(Vector2.ZERO, 900.0 * delta)
			play_loop("idle")

func _think_chase(delta: float, dist: float, los: bool) -> void:
	if not _target_alive() or dist > stats.lose_range:
		aggro = false
		_enter(AI.IDLE)
		return
	var rng := stats.attack_range
	if dist <= rng and attack_cd <= 0.0 and los:
		_start_windup()
		return
	if dist > rng * 0.85:
		_go_to(target.global_position, stats.chase_speed, delta)
		play_loop("walk", clampf(stats.chase_speed / 70.0, 0.6, 1.2))
	else:
		ground_vel = ground_vel.move_toward(Vector2.ZERO, 900.0 * delta)
		set_facing(ground_dir_to(target.global_position))
		play_loop("idle")

func _start_windup() -> void:
	_enter(AI.WINDUP)
	attack_dir = ground_dir_to(target.global_position)
	set_facing(attack_dir)
	attack_hit = false
	tele.show_cone(stats.attack_reach, stats.attack_arc_deg, attack_dir, telegraph_color)
	Sfx.play("swing_1", -10.0, 0.7)

func _think_windup(delta: float) -> void:
	var w := stats.windup_time
	var p := clampf(ai_t / w, 0.0, 1.0)
	ground_vel = ground_vel.move_toward(Vector2.ZERO, 1200.0 * delta)
	# acompanha o jogador só na primeira parte da preparação (depois a direção trava)
	if p < 0.6 and _target_alive():
		attack_dir = attack_dir.lerp(ground_dir_to(target.global_position), 0.12).normalized()
		set_facing(attack_dir)
		tele.dir = attack_dir
	tele.set_progress(p)
	show_frame("attack", Actor.phase_frame(attack_frames_windup, attack_frames_strike, attack_frames_recover, 0, p))
	if ai_t >= w:
		tele.hide_it()
		_enter(AI.ATTACK)
		Sfx.play("swing_0", -3.0, 0.75)

func _think_attack(_delta: float) -> void:
	var a := stats.active_time
	var p := clampf(ai_t / a, 0.0, 1.0)
	ground_vel = attack_dir * stats.lunge_speed * (1.0 - p)
	show_frame("attack", Actor.phase_frame(attack_frames_windup, attack_frames_strike, attack_frames_recover, 1, p))
	if not attack_hit and _target_alive():
		if CombatUtil.arc_hit(global_position, attack_dir, stats.attack_reach, stats.attack_arc_deg, target.global_position, target.body_radius):
			if CombatUtil.line_of_sight(get_world_2d().direct_space_state, global_position, target.global_position):
				attack_hit = true
				var info := HitInfo.new()
				info.damage = stats.damage
				info.origin = global_position
				info.knockback = 140.0
				info.source = self
				info.heavy = stats.windup_time > 0.8
				target.receive_hit(info)
	if ai_t >= a:
		_enter(AI.RECOVER)

func _think_recover(delta: float) -> void:
	var r := stats.recover_time
	var p := clampf(ai_t / r, 0.0, 1.0)
	ground_vel = ground_vel.move_toward(Vector2.ZERO, 900.0 * delta)
	show_frame("attack", Actor.phase_frame(attack_frames_windup, attack_frames_strike, attack_frames_recover, 2, p))
	if ai_t >= r:
		attack_cd = stats.cooldown_time
		_enter(AI.CHASE)

func _think_hurt(_delta: float) -> void:
	var s := stats.stagger_time
	ground_vel = Vector2.ZERO
	show_frame("hurt", 0 if ai_t < s * 0.5 else 1)
	if ai_t >= s:
		_enter(AI.CHASE)

# ------------------------------------------------------------------ navegação
func _los_to(p: Vector2) -> bool:
	return CombatUtil.line_of_sight(get_world_2d().direct_space_state, global_position, p)

## Anda até dest. Se há parede no caminho, segue a rota calculada pelo Level (A*).
func _go_to(dest: Vector2, speed: float, delta: float) -> void:
	var goal := dest
	if not _los_to(dest) and level != null and level.has_method("find_path"):
		if repath_t <= 0.0 or path.is_empty():
			path = level.find_path(global_position, dest)
			repath_t = 0.45
		while not path.is_empty() and Iso.to_ground(path[0] - global_position).length() < 9.0:
			path.pop_front()
		if not path.is_empty():
			goal = path[0]
	var d := Iso.to_ground(goal - global_position)
	if d.length() > 1.0:
		var dir := d.normalized()
		ground_vel = ground_vel.move_toward(dir * speed, 900.0 * delta)
		set_facing(dir)

## Afasta inimigos que estão sobrepostos entre si.
func _separation() -> Vector2:
	var push := Vector2.ZERO
	for n in get_tree().get_nodes_in_group("enemies"):
		if n == self:
			continue
		var e := n as Enemy
		if e == null:
			continue
		var d := Iso.to_ground(global_position - e.global_position)
		var min_d := body_radius + e.body_radius
		var l := d.length()
		if l < min_d and l > 0.01:
			push += d / l * (min_d - l) * 8.0
	return push

# ------------------------------------------------------------------ dano e morte
func receive_hit(info: HitInfo) -> bool:
	if dead:
		return false
	_apply_damage(info)
	return true

func _apply_damage(info: HitInfo) -> void:
	var away := Iso.to_ground(global_position - info.origin)
	away = away.normalized() if away.length() > 0.01 else -facing
	knock_vel = away * info.knockback * stats.knockback_multiplier
	flash(1.0, Color.WHITE, 9.0)
	Fx.spark(get_tree(), chest_pos(), Color(1.0, 0.92, 0.75))
	Fx.blood(get_tree(), chest_pos(), blood_color)
	Sfx.play("hit_heavy" if info.heavy else "hit", -1.0)
	aggro = true
	health.damage(info.damage)
	if dead or health.dead:
		return
	if stats.stagger_time > 0.0 and ai != AI.ATTACK:
		tele.hide_it()
		_enter(AI.HURT)

func _on_health_died() -> void:
	dead = true
	ai = AI.DEAD
	if tele != null:
		tele.hide_it()
	remove_from_group("enemies")
	body_shape.set_deferred("disabled", true)
	play_once("death", 1.0)
	Sfx.play("enemy_die", -2.0)
	Fx.souls_fx(get_tree(), chest_pos())
	Game.add_souls(stats.souls_reward)
	_after_death()

## Gancho para tipos especiais (o espectro se dissolve).
func _after_death() -> void:
	shadow.modulate.a = 0.5
