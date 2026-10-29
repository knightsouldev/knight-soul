class_name Boss
extends Enemy
## SENTINELA DA RUÍNA — Guardião das Almas Perdidas.
##
## COMO O CHEFE FUNCIONA (leia de cima para baixo):
##   1. DORMANT  - parado esperando. O Level chama activate() quando o jogador entra na arena.
##   2. INTRO    - ruge e treme a tela (intro_duration). Não toma dano nesse tempo.
##   3. CHASE    - anda até o jogador e escolhe um ataque (_choose_attack).
##   4. WINDUP   - PREPARAÇÃO: o aviso no chão enche (cone, faixa ou círculo). É a hora de esquivar.
##   5. ACTIVE   - o ataque acontece (causa dano uma vez só).
##   6. RECOVER  - recuperação: parado e VULNERÁVEL (leva mais dano). Hora de contra-atacar.
##   (STUN = bateu na parede ao investir, fica atordoado; ENRAGE = ruge ao entrar na fase 2.)
##
## OS 3 ATAQUES:
##   strike  Golpe pesado  -> cone vermelho à frente. Perto do jogador.
##   charge  Investida     -> faixa laranja. Corre em linha reta; trava a direção no meio da preparação.
##   slam    Golpe de área -> círculo roxo ao redor dele. Usado se o jogador fica colado nele.
##
## FASE 2 (vida abaixo de phase2_health_ratio): preparações mais curtas, anda mais rápido
## e às vezes encadeia strike -> slam.
##
## Atributos gerais (vida, velocidade, almas) ficam em res://resources/stats/sentinela.tres.
## Os números de cada ataque estão nos @export abaixo, editáveis no Inspector.

enum BS { DORMANT, INTRO, CHASE, WINDUP, ACTIVE, RECOVER, STUN, ENRAGE, DEAD }

signal intro_finished

@export_group("Abertura e fases")
## Duração do rugido de abertura.
@export var intro_duration := 2.4
## Duração do rugido ao entrar na fase 2.
@export var enrage_duration := 1.5
## Dano extra quando ele está se recuperando (1.25 = +25%).
@export var vulnerable_damage_multiplier := 1.25
## A fase 2 começa quando a vida chega a esta fração (0.5 = metade).
@export_range(0.05, 0.95) var phase2_health_ratio := 0.5
## Fase 2: multiplica o tempo de preparação (menor = mais rápido).
@export var phase2_windup_multiplier := 0.82
## Fase 2: multiplica o tempo de recuperação.
@export var phase2_recover_multiplier := 0.85
## Fase 2: multiplica a velocidade de caminhada.
@export var phase2_speed_multiplier := 1.12
## Fase 2: chance de emendar um golpe de área depois do golpe pesado.
@export_range(0.0, 1.0) var phase2_combo_chance := 0.4

@export_group("Escolha do ataque")
## Até esta distância ele usa golpe pesado (ou golpe de área).
@export var melee_distance := 105.0
## Distâncias entre as quais ele pode investir.
@export var charge_min_distance := 175.0
@export var charge_max_distance_pick := 330.0

@export_group("Golpe pesado (strike)")
@export var strike_windup := 0.95
@export var strike_active := 0.16
@export var strike_recover := 1.05
@export var strike_damage := 34.0
@export var strike_reach := 128.0
@export var strike_arc_deg := 80.0
@export var strike_knockback := 170.0
@export var strike_lunge_speed := 80.0

@export_group("Investida (charge)")
@export var charge_windup := 0.95
@export var charge_speed := 430.0
## Distância máxima da corrida.
@export var charge_max_distance := 300.0
## Largura da faixa de perigo.
@export var charge_width := 56.0
@export var charge_damage := 30.0
@export var charge_recover := 1.0
## Tempo atordoado se bater na parede.
@export var charge_wall_stun := 1.8
## Em que ponto da preparação (0 a 1) a direção trava.
@export_range(0.1, 1.0) var charge_lock_at := 0.55
@export var charge_knockback := 200.0
## Espera mínima entre duas investidas.
@export var charge_cooldown := 4.0

@export_group("Golpe de área (slam)")
@export var slam_windup := 1.15
@export var slam_active := 0.18
@export var slam_recover := 1.0
@export var slam_damage := 38.0
@export var slam_radius := 140.0
@export var slam_knockback := 220.0

var bs: BS = BS.DORMANT
var bt := 0.0
var attack_kind := ""
var last_kind := ""
var queued_attack := ""
var charge_cd := 3.0
var since_attack := 0.0
var close_time := 0.0
var phase2 := false
var pending_phase2 := false
var charge_dir := Vector2.RIGHT
var charge_locked := false
var charge_travel := 0.0
var hit_done := false
var wind_len := 1.0
var rec_len := 1.0

func _ready() -> void:
	super._ready()
	telegraph_color = Color(0.95, 0.15, 0.18)
	set_facing(Vector2(0, 1))
	play_loop("idle")
	health.changed.connect(_on_hp_changed)

func is_targetable() -> bool:
	return bs != BS.DEAD

## Chamado pelo Level quando o jogador entra na arena.
func activate() -> void:
	if bs != BS.DORMANT:
		return
	bs = BS.INTRO
	bt = 0.0
	Sfx.play("boss_roar", 0.0, 1.0, 0.0)
	Fx.shake(get_tree(), 5.0)

func _on_hp_changed(cur: float, maxi: float) -> void:
	if not phase2 and not pending_phase2 and cur > 0.0 and cur / maxi <= phase2_health_ratio:
		pending_phase2 = true

# ------------------------------------------------------------------ loop principal
func _physics_process(delta: float) -> void:
	if bs == BS.DEAD:
		_dead_tick(delta)
		return
	_find_target()
	bt += delta
	charge_cd = maxf(0.0, charge_cd - delta)
	since_attack += delta
	repath_t -= delta
	var dist := 99999.0
	if _target_alive():
		dist = ground_dist_to(target)
		if dist < 85.0:
			close_time += delta       # quanto tempo o jogador ficou colado nele
		else:
			close_time = maxf(0.0, close_time - delta * 2.0)
	match bs:
		BS.DORMANT:
			play_loop("idle")
			move_actor(Vector2.ZERO, delta)
		BS.INTRO:
			_do_intro(delta)
		BS.CHASE:
			_do_chase(delta, dist)
		BS.WINDUP:
			_do_windup(delta)
		BS.ACTIVE:
			_do_active(delta)
		BS.RECOVER:
			_do_recover(delta)
		BS.STUN:
			_do_stun(delta)
		BS.ENRAGE:
			_do_enrage(delta)

func _go(s: BS) -> void:
	bs = s
	bt = 0.0

func _walk_speed() -> float:
	return stats.walk_speed * (phase2_speed_multiplier if phase2 else 1.0)

func _windup_mult() -> float:
	return phase2_windup_multiplier if phase2 else 1.0

func _recover_mult() -> float:
	return phase2_recover_multiplier if phase2 else 1.0

# ------------------------------------------------------------------ abertura e fase 2
func _do_intro(delta: float) -> void:
	ground_vel = Vector2.ZERO
	play_loop("idle", 0.6)
	if _target_alive():
		set_facing(ground_dir_to(target.global_position))
	if int(bt * 6.0) % 2 == 0 and bt < intro_duration * 0.7:
		Fx.shake(get_tree(), 2.5)
	move_actor(Vector2.ZERO, delta)
	if bt >= intro_duration:
		intro_finished.emit()
		_go(BS.CHASE)

func _do_enrage(delta: float) -> void:
	ground_vel = Vector2.ZERO
	play_loop("idle", 0.5)
	move_actor(Vector2.ZERO, delta)
	if bt < 0.15:
		Fx.ring(get_tree(), global_position, 170.0, Color(0.8, 0.4, 1.0), 0.7)
	if bt >= enrage_duration:
		phase2 = true
		pending_phase2 = false
		_go(BS.CHASE)

# ------------------------------------------------------------------ perseguição e escolha do ataque
func _do_chase(delta: float, dist: float) -> void:
	if not _target_alive():
		ground_vel = ground_vel.move_toward(Vector2.ZERO, 900.0 * delta)
		play_loop("idle")
		move_actor(ground_vel, delta)
		return
	if pending_phase2:
		Sfx.play("boss_roar", 0.0, 1.2, 0.0)
		Fx.shake(get_tree(), 6.0)
		_go(BS.ENRAGE)
		return
	var los := _los_to(target.global_position)
	if since_attack > 0.5:
		var pick := _choose_attack(dist, los)
		if pick != "":
			_start_attack(pick)
			return
	_go_to(target.global_position, _walk_speed(), delta)
	play_loop("walk", _walk_speed() / 58.0)
	move_actor(ground_vel, delta)

## Decide o próximo ataque pela distância ao jogador. Retorna "" se ainda deve andar.
func _choose_attack(dist: float, los: bool) -> String:
	if not los:
		return ""
	if dist <= melee_distance:
		if close_time > 2.6 or (last_kind == "strike" and randf() < 0.4):
			return "slam"
		return "strike"
	if dist >= charge_min_distance and dist <= charge_max_distance_pick and charge_cd <= 0.0:
		return "charge"
	return ""

func _start_attack(kind_: String) -> void:
	attack_kind = kind_
	last_kind = kind_
	hit_done = false
	charge_locked = false
	charge_travel = 0.0
	attack_dir = ground_dir_to(target.global_position)
	set_facing(attack_dir)
	Sfx.play("boss_telegraph", -2.0, 1.0, 0.0)
	match kind_:
		"strike":
			wind_len = strike_windup * _windup_mult()
			tele.show_cone(strike_reach, strike_arc_deg, attack_dir, Color(0.95, 0.15, 0.18))
		"charge":
			wind_len = charge_windup * _windup_mult()
			charge_dir = attack_dir
			tele.show_line(charge_max_distance, charge_width, attack_dir, Color(1.0, 0.5, 0.12))
		"slam":
			wind_len = slam_windup * _windup_mult()
			tele.show_circle(slam_radius, Color(0.7, 0.25, 1.0))
	_go(BS.WINDUP)

# ------------------------------------------------------------------ preparação (aviso no chão)
# As animações "strike", "slam" (9 quadros: 4 preparação + 2 golpe + 3 recuperação) e
# "charge" (8 quadros: 3 + 2 + 3) são tocadas quadro a quadro conforme a fase.
func _do_windup(delta: float) -> void:
	var p := clampf(bt / wind_len, 0.0, 1.0)
	ground_vel = ground_vel.move_toward(Vector2.ZERO, 1400.0 * delta)
	match attack_kind:
		"strike":
			if p < 0.6 and _target_alive():
				attack_dir = attack_dir.lerp(ground_dir_to(target.global_position), 0.10).normalized()
				tele.dir = attack_dir
			set_facing(attack_dir)
			show_frame("strike", Actor.phase_frame(4, 2, 3, 0, p))
		"charge":
			if p < charge_lock_at and _target_alive():
				charge_dir = charge_dir.lerp(ground_dir_to(target.global_position), 0.14).normalized()
				tele.dir = charge_dir
			elif not charge_locked:
				charge_locked = true
				tele.col = Color(1.0, 0.25, 0.1)     # avisa: direção travada
			set_facing(charge_dir)
			show_frame("charge", Actor.phase_frame(3, 2, 3, 0, p))
		"slam":
			show_frame("slam", Actor.phase_frame(4, 2, 3, 0, p))
			if _target_alive():
				set_facing(ground_dir_to(target.global_position))
	tele.set_progress(p)
	move_actor(ground_vel, delta)
	if bt >= wind_len:
		tele.hide_it()
		_begin_active()

func _begin_active() -> void:
	_go(BS.ACTIVE)
	match attack_kind:
		"strike":
			Sfx.play("swing_0", 2.0, 0.5)
		"charge":
			Sfx.play("boss_charge", 0.0, 1.0, 0.0)
		"slam":
			Sfx.play("boss_slam", 2.0, 1.0, 0.0)
			Fx.shake(get_tree(), 8.0)
			Fx.ring(get_tree(), global_position, slam_radius, Color(0.8, 0.45, 1.0), 0.5)
			Fx.crack(get_tree(), global_position)
			Fx.burst(get_tree(), global_position + Vector2(0, -6), Color(0.45, 0.4, 0.35, 0.9), 18, 110.0, 0.6, 260.0, 3.0)

# ------------------------------------------------------------------ execução do ataque
func _hurt_player(dmg: float, knock: float) -> void:
	var info := HitInfo.new()
	info.damage = dmg
	info.origin = global_position
	info.knockback = knock
	info.source = self
	info.heavy = true
	target.receive_hit(info)

func _do_active(delta: float) -> void:
	match attack_kind:
		"strike":
			var p := clampf(bt / strike_active, 0.0, 1.0)
			ground_vel = attack_dir * strike_lunge_speed * (1.0 - p)
			show_frame("strike", Actor.phase_frame(4, 2, 3, 1, p))
			if not hit_done and _target_alive():
				if CombatUtil.arc_hit(global_position, attack_dir, strike_reach, strike_arc_deg, target.global_position, target.body_radius):
					if CombatUtil.line_of_sight(get_world_2d().direct_space_state, global_position, target.global_position):
						hit_done = true
						_hurt_player(strike_damage, strike_knockback)
			move_actor(ground_vel, delta)
			if bt >= strike_active:
				rec_len = strike_recover * _recover_mult()
				if phase2 and randf() < phase2_combo_chance:
					queued_attack = "slam"     # combo: emenda o golpe de área
					rec_len = 0.4
				_go(BS.RECOVER)
		"charge":
			ground_vel = charge_dir * charge_speed
			set_facing(charge_dir)
			show_frame("charge", 3 + (int(bt * 12.0) % 2))
			var before := global_position
			move_actor(ground_vel, delta)
			charge_travel += Iso.to_ground(global_position - before).length()
			if not hit_done and _target_alive():
				if ground_dist_to(target) <= body_radius * 0.9 + target.body_radius + 6.0:
					hit_done = true
					_hurt_player(charge_damage, charge_knockback)
					_end_charge(false)
					return
			if get_slide_collision_count() > 0 and charge_travel > 20.0:
				_end_charge(true)          # bateu na parede
			elif charge_travel >= charge_max_distance:
				_end_charge(false)
		"slam":
			var p3 := clampf(bt / slam_active, 0.0, 1.0)
			ground_vel = Vector2.ZERO
			show_frame("slam", Actor.phase_frame(4, 2, 3, 1, p3))
			if not hit_done and _target_alive():
				if CombatUtil.circle_hit(global_position, slam_radius, target.global_position, target.body_radius):
					hit_done = true
					_hurt_player(slam_damage, slam_knockback)
			move_actor(Vector2.ZERO, delta)
			if bt >= slam_active:
				rec_len = slam_recover * _recover_mult()
				_go(BS.RECOVER)

func _end_charge(hit_wall: bool) -> void:
	ground_vel = Vector2.ZERO
	charge_cd = charge_cooldown
	if hit_wall:
		Sfx.play("boss_slam", 0.0, 0.9, 0.0)
		Fx.shake(get_tree(), 7.0)
		Fx.burst(get_tree(), global_position + Vector2(0, -20), Color(0.5, 0.45, 0.4, 0.9), 16, 100.0, 0.6, 260.0, 3.0)
		Fx.spark(get_tree(), global_position + Vector2(0, -30), Color(1, 0.8, 0.5))
		_go(BS.STUN)
	else:
		rec_len = charge_recover * _recover_mult()
		_go(BS.RECOVER)

# ------------------------------------------------------------------ recuperação (vulnerável)
func _do_recover(delta: float) -> void:
	var p := clampf(bt / rec_len, 0.0, 1.0)
	ground_vel = ground_vel.move_toward(Vector2.ZERO, 900.0 * delta)
	var wind_frames := 3 if attack_kind == "charge" else 4
	show_frame(attack_kind, Actor.phase_frame(wind_frames, 2, 3, 2, p))
	move_actor(ground_vel, delta)
	if bt >= rec_len:
		since_attack = 0.0
		if queued_attack != "" and _target_alive():
			var q := queued_attack
			queued_attack = ""
			_start_attack(q)
		else:
			_go(BS.CHASE)

func _do_stun(delta: float) -> void:
	ground_vel = Vector2.ZERO
	show_frame("charge", 5 + mini(2, int(bt / charge_wall_stun * 3.0)))
	move_actor(Vector2.ZERO, delta)
	if bt >= charge_wall_stun:
		since_attack = 0.0
		_go(BS.CHASE)

# ------------------------------------------------------------------ dano e morte
func receive_hit(info: HitInfo) -> bool:
	if bs == BS.DEAD or bs == BS.DORMANT or bs == BS.INTRO:
		return false
	var vulnerable := bs == BS.RECOVER or bs == BS.STUN
	var dmg := info.damage * (vulnerable_damage_multiplier if vulnerable else 1.0)
	flash(0.8, Color(1, 1, 1) if not vulnerable else Color(1.0, 0.8, 0.6), 9.0)
	Fx.spark(get_tree(), chest_pos() + Vector2(randf_range(-8, 8), randf_range(-14, 6)), Color(1.0, 0.92, 0.75))
	Fx.blood(get_tree(), chest_pos(), blood_color)
	Sfx.play("hit_heavy", -1.0)
	health.damage(dmg)
	return true

func _on_health_died() -> void:
	bs = BS.DEAD
	dead = true
	ai = AI.DEAD
	tele.hide_it()
	remove_from_group("enemies")
	body_shape.set_deferred("disabled", true)
	ground_vel = Vector2.ZERO
	play_once("death", 0.55)
	Sfx.play("boss_die", 0.0, 1.0, 0.0)
	Sfx.stop_music(1.5)
	Fx.shake(get_tree(), 8.0)
	Game.hit_stop(0.25, 0.1)
	Fx.ring(get_tree(), global_position, 200.0, Color(0.75, 0.4, 1.0), 1.0)
	Fx.burst(get_tree(), global_position + Vector2(0, -40), Color(0.75, 0.45, 1.0, 0.9), 40, 90.0, 1.6, -30.0, 3.0, true)
	Game.add_souls(stats.souls_reward)
	await get_tree().create_timer(2.6, true, false, true).timeout
	Fx.souls_fx(get_tree(), global_position + Vector2(0, -40))
	await get_tree().create_timer(1.0, true, false, true).timeout
	Game.on_boss_defeated()
