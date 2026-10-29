class_name Player
extends Actor
## CAVALEIRO ERRANTE (o jogador).
##
## Estados (variável "state"): IDLE (parado), MOVE (andando), ATTACK, DODGE (esquiva),
## HURT (levou dano), HEAL (bebendo o frasco) e DEAD.
##
## Um ataque tem 3 fases: preparação (não machuca) -> golpe (hitbox em arco) -> recuperação.
## A esquiva só cancela a recuperação do ataque, nunca a preparação nem o golpe.
##
## Os nós visuais (Sprite, Sombra, Colisao, Vida, Luz, Camera) estão na cena player.tscn.
## Todos os números abaixo aparecem no Inspector ao selecionar o nó Jogador.

enum State { IDLE, MOVE, ATTACK, DODGE, HURT, HEAL, DEAD }

## Avisa a HUD quando a stamina muda.
signal stamina_changed(current: float, maximum: float)

@export_group("Movimento")
## Velocidade de caminhada (unidades de chão por segundo).
@export var move_speed := 104.0
## Quão rápido acelera ao começar a andar.
@export var acceleration := 1100.0
## Quão rápido freia ao soltar as teclas.
@export var deceleration := 1500.0

@export_group("Stamina")
@export var max_stamina := 100.0
## Stamina recuperada por segundo.
@export var stamina_regen_per_second := 36.0
## Espera (s) depois de gastar stamina antes de começar a recuperar.
@export var stamina_regen_delay := 0.7
## Espera maior quando a stamina chega a zero.
@export var stamina_exhausted_delay := 1.4

@export_group("Ataque com espada")
@export var attack_stamina_cost := 17.0
## Preparação do golpe (não causa dano).
@export var attack_windup := 0.14
## Janela em que a espada acerta.
@export var attack_active_time := 0.12
## Recuperação depois do golpe.
@export var attack_recovery := 0.32
## Dano do 1º e do 2º golpe do combo.
@export var attack_damage: PackedFloat32Array = [24.0, 28.0]
## Alcance do golpe.
@export var attack_reach := 62.0
## Abertura do golpe em graus.
@export var attack_arc_deg := 135.0
## Avanço do corpo durante o golpe.
@export var attack_lunge_speed := 120.0
## Empurrão aplicado no inimigo.
@export var attack_knockback := 110.0
## Tempo (s) depois do ataque para encadear o 2º golpe.
@export var combo_window := 0.40

@export_group("Esquiva")
@export var dodge_stamina_cost := 20.0
## Duração total da esquiva.
@export var dodge_duration := 0.42
## Tempo em que realmente se desloca.
@export var dodge_move_time := 0.34
## Distância percorrida.
@export var dodge_distance := 94.0
## Invulnerável a partir deste instante (s)...
@export var dodge_iframes_start := 0.03
## ...até este instante (s).
@export var dodge_iframes_end := 0.30

@export_group("Dano recebido")
## Tempo atordoado ao levar um golpe.
@export var hurt_stun_time := 0.30
## Invulnerabilidade curta depois de levar dano.
@export var mercy_iframes_time := 0.55

@export_group("Cura e itens")
## Duração da animação de beber o frasco.
@export var heal_duration := 0.9
## Em que momento (s) a vida é restaurada.
@export var heal_apply_at := 0.5
@export var heal_amount := 48.0
## Duração do Óleo de Lâmina.
@export var oil_duration := 14.0
## Multiplicador de dano com óleo.
@export var oil_damage_multiplier := 1.35
## Efeito passivo do Manto do Andarilho (slot 4): custo da esquiva × este valor.
@export var cloak_dodge_cost_multiplier := 0.85

var state: State = State.IDLE
var state_t := 0.0
var stamina := 100.0
var stamina_wait := 0.0
var invuln_t := 0.0
var combo_timer := 0.0
var combo_index := 0
var attack_index := 0
var attack_aim := Vector2.RIGHT
var attack_buffer := false
var slash_spawned := false
var hit_ids: Dictionary = {}
var dodge_dir := Vector2.RIGHT
var heal_applied := false
var oil_t := 0.0
var current_hurt_stun := 0.3
var control_enabled := true
var light: PointLight2D
var cam: CameraRig
var _dust_t := 0.0

func _ready() -> void:
	super._ready()
	add_to_group("player")
	light = $Luz as PointLight2D
	cam = $Camera as CameraRig
	cam.make_current()
	stamina = max_stamina
	set_facing(Vector2(1, 1))
	play_loop("idle")

func is_invulnerable() -> bool:
	if invuln_t > 0.0:
		return true
	return state == State.DODGE and state_t >= dodge_iframes_start and state_t <= dodge_iframes_end

func is_dead() -> bool:
	return state == State.DEAD

# ------------------------------------------------------------------ entrada
func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("slot_1"):
		Game.select_slot(0)
	elif event.is_action_pressed("slot_2"):
		Game.select_slot(1)
	elif event.is_action_pressed("slot_3"):
		Game.select_slot(2)
	elif event.is_action_pressed("slot_4"):
		Game.select_slot(3)
	elif event.is_action_pressed("slot_next"):
		Game.select_slot(Game.selected_slot + 1)
	elif event.is_action_pressed("slot_prev"):
		Game.select_slot(Game.selected_slot - 1)

## Direção do cursor do mouse em relação ao jogador (espaço de chão).
func _aim_dir() -> Vector2:
	var g := Iso.to_ground(get_global_mouse_position() - global_position)
	if g.length() > 8.0:
		return g.normalized()
	return facing

func _read_move() -> Vector2:
	if not control_enabled:
		return Vector2.ZERO
	return Input.get_vector("move_left", "move_right", "move_up", "move_down")

# ------------------------------------------------------------------ loop principal
func _physics_process(delta: float) -> void:
	state_t += delta
	invuln_t = maxf(0.0, invuln_t - delta)
	combo_timer = maxf(0.0, combo_timer - delta)
	oil_t = maxf(0.0, oil_t - delta)
	_update_stamina(delta)
	var mv := _read_move()
	match state:
		State.IDLE, State.MOVE:
			_state_free(delta, mv)
		State.ATTACK:
			_state_attack(delta)
		State.DODGE:
			_state_dodge(delta)
		State.HURT:
			_state_hurt(delta)
		State.HEAL:
			_state_heal(delta)
		State.DEAD:
			ground_vel = Vector2.ZERO
			move_actor(Vector2.ZERO, delta)
	if state != State.DEAD:
		_push_out_of_enemies()
	light.energy = 0.5 + (0.08 if oil_t > 0.0 else 0.0)

func _update_stamina(delta: float) -> void:
	stamina_wait = maxf(0.0, stamina_wait - delta)
	if stamina_wait <= 0.0 and state != State.ATTACK and state != State.DODGE and state != State.DEAD:
		stamina = minf(max_stamina, stamina + stamina_regen_per_second * delta)
	stamina_changed.emit(stamina, max_stamina)

func _spend(cost: float) -> void:
	stamina = maxf(0.0, stamina - cost)
	stamina_wait = stamina_exhausted_delay if stamina <= 0.5 else stamina_regen_delay

func _can_spend() -> bool:
	if stamina <= 0.5:
		Game.stamina_denied.emit()
		return false
	return true

# ------------------------------------------------------------------ livre (parado / andando)
func _state_free(delta: float, mv: Vector2) -> void:
	if control_enabled:
		if Input.is_action_just_pressed("heal") and _try_heal():
			return
		if Input.is_action_just_pressed("use_item") and _use_selected():
			return
		if Input.is_action_just_pressed("dodge") and _try_dodge(mv):
			return
		if Input.is_action_just_pressed("attack") and _try_attack():
			return
	var want := mv * move_speed
	var rate := acceleration if want.length() > 0.1 else deceleration
	ground_vel = ground_vel.move_toward(want, rate * delta)
	if mv.length() > 0.1:
		state = State.MOVE
		set_facing(mv)
		play_loop("walk")
	else:
		state = State.IDLE
		play_loop("idle")
	move_actor(ground_vel, delta)

# ------------------------------------------------------------------ ataque
func _try_attack() -> bool:
	if not _can_spend():
		return false
	_spend(attack_stamina_cost)
	attack_index = combo_index if combo_timer > 0.0 else 0
	combo_index = 1 - attack_index
	attack_aim = _aim_dir()
	set_facing(attack_aim)
	state = State.ATTACK
	state_t = 0.0
	hit_ids.clear()
	slash_spawned = false
	attack_buffer = false
	Sfx.play("swing_%d" % attack_index, -2.0)
	return true

func _state_attack(delta: float) -> void:
	var wind := attack_windup
	var act := attack_active_time
	var rec := attack_recovery
	var phase := 0
	var p := 0.0
	if state_t < wind:
		p = state_t / wind
	elif state_t < wind + act:
		phase = 1
		p = (state_t - wind) / act
	else:
		phase = 2
		p = minf(1.0, (state_t - wind - act) / rec)
	# a animação "attack1"/"attack2" tem 6 quadros: 2 de preparação, 2 de golpe, 2 de recuperação
	show_frame("attack%d" % (attack_index + 1), Actor.phase_frame(2, 2, 2, phase, p))
	if phase == 1:
		ground_vel = attack_aim * attack_lunge_speed * (1.0 - p * 0.6)
		_attack_hit_check()
		if not slash_spawned:
			slash_spawned = true
			Fx.slash(get_tree(), global_position + Vector2(0, -14), attack_aim, attack_index == 1,
				Color(1.0, 0.8, 0.45, 0.95) if oil_t > 0.0 else Color(1, 1, 1, 0.95))
	else:
		ground_vel = ground_vel.move_toward(Vector2.ZERO, 1200.0 * delta)
	move_actor(ground_vel, delta)
	if Input.is_action_just_pressed("attack"):
		attack_buffer = true
	if phase == 2 and control_enabled:
		if Input.is_action_just_pressed("dodge") and p >= 0.35 and _try_dodge(_read_move()):
			return
		if attack_buffer and p >= 0.55:
			combo_index = 1 - attack_index
			combo_timer = combo_window
			if _try_attack():
				return
			attack_buffer = false
	if state_t >= wind + act + rec:
		combo_index = 1 - attack_index
		combo_timer = combo_window
		state = State.IDLE
		ground_vel = Vector2.ZERO

## Testa quem está dentro do arco do golpe. Cada inimigo só é atingido uma vez por golpe.
func _attack_hit_check() -> void:
	var dmg: float = attack_damage[attack_index]
	if oil_t > 0.0:
		dmg *= oil_damage_multiplier
	var space := get_world_2d().direct_space_state
	for n in get_tree().get_nodes_in_group("enemies"):
		var e := n as Enemy
		if e == null or not e.is_targetable():
			continue
		var id := e.get_instance_id()
		if hit_ids.has(id):
			continue
		if not CombatUtil.arc_hit(global_position, attack_aim, attack_reach, attack_arc_deg, e.global_position, e.body_radius):
			continue
		# paredes bloqueiam o golpe
		if not CombatUtil.line_of_sight(space, global_position, e.global_position):
			continue
		hit_ids[id] = true
		var info := HitInfo.new()
		info.damage = dmg
		info.origin = global_position
		info.knockback = attack_knockback
		info.source = self
		if e.receive_hit(info):
			Game.hit_stop(0.05)
			Fx.shake(get_tree(), 2.0)

# ------------------------------------------------------------------ esquiva
func _try_dodge(mv: Vector2) -> bool:
	if not _can_spend():
		return false
	_spend(dodge_stamina_cost * cloak_dodge_cost_multiplier)
	dodge_dir = mv.normalized() if mv.length() > 0.1 else -facing
	set_facing(dodge_dir)
	state = State.DODGE
	state_t = 0.0
	_dust_t = 0.0
	Sfx.play("dodge", -3.0)
	Fx.dust(get_tree(), global_position)
	return true

func _state_dodge(delta: float) -> void:
	var mt := dodge_move_time
	if state_t < mt:
		var u := state_t / mt
		var v := (dodge_distance / mt) * (1.4 - 0.8 * u)
		ground_vel = dodge_dir * v
		_dust_t -= delta
		if _dust_t <= 0.0:
			_dust_t = 0.09
			Fx.dust(get_tree(), global_position)
	else:
		ground_vel = Vector2.ZERO
	show_frame("dodge", int(clampf(state_t / mt, 0.0, 0.999) * 5.0))
	move_actor(ground_vel, delta)
	if state_t >= dodge_duration:
		state = State.IDLE
		ground_vel = Vector2.ZERO

# ------------------------------------------------------------------ cura e itens
func _try_heal() -> bool:
	if Game.flasks <= 0:
		Game.notify("Sem frascos restantes")
		return false
	if health.current >= health.maximum - 0.5:
		Game.notify("Vida cheia")
		return false
	state = State.HEAL
	state_t = 0.0
	heal_applied = false
	ground_vel = Vector2.ZERO
	return true

func _state_heal(delta: float) -> void:
	ground_vel = ground_vel.move_toward(Vector2.ZERO, 1500.0 * delta)
	move_actor(ground_vel, delta)
	var p := clampf(state_t / heal_duration, 0.0, 0.999)
	show_frame("heal", int(p * 5.0))
	# o frasco só é gasto no momento em que a cura acontece (se for interrompido, não perde)
	if not heal_applied and state_t >= heal_apply_at:
		heal_applied = true
		if Game.use_flask():
			health.heal(heal_amount)
			Sfx.play("heal", -2.0, 1.0, 0.0)
			Fx.heal_fx(get_tree(), global_position + Vector2(0, -10))
			flash(0.7, Color(0.5, 0.8, 1.0), 4.0)
	if state_t >= heal_duration:
		state = State.IDLE

## Usa o item selecionado na HUD (tecla E).
func _use_selected() -> bool:
	match Game.selected_slot:
		0:
			Game.notify("Espada Gasta: ataque leve (clique / J)")
		1:
			if oil_t > 0.0:
				Game.notify("Óleo de Lâmina já está ativo")
			elif Game.use_oil():
				oil_t = oil_duration
				Sfx.play("pickup", -6.0, 0.8)
				Fx.burst(get_tree(), global_position + Vector2(0, -16), Color(1.0, 0.7, 0.3, 0.9), 14, 50.0, 0.7, -40.0, 2.0, true)
				Game.notify("Lâmina banhada em óleo: +35% de dano")
				return true
			else:
				Game.notify("Sem Óleo de Lâmina")
		2:
			return _try_heal()
		3:
			Game.notify("Manto do Andarilho (passivo): esquiva custa 15% menos stamina")
	return false

# ------------------------------------------------------------------ dano
func receive_hit(info: HitInfo) -> bool:
	if state == State.DEAD or Game.run_state != "playing":
		return false
	if Game.god_mode or is_invulnerable():
		return false
	health.damage(info.damage)
	var away := Iso.to_ground(global_position - info.origin)
	away = away.normalized() if away.length() > 0.01 else -facing
	knock_vel = away * info.knockback
	invuln_t = mercy_iframes_time
	flash(1.0, Color(1.0, 0.25, 0.25), 7.0)
	Fx.blood(get_tree(), chest_pos(), Color(0.65, 0.07, 0.1))
	Fx.spark(get_tree(), chest_pos(), Color(1.0, 0.5, 0.4))
	Sfx.play("hurt", 0.0)
	Game.hit_stop(0.07)
	Fx.shake(get_tree(), 5.0 if info.heavy else 3.0)
	attack_buffer = false
	if health.dead:
		return true
	state = State.HURT
	state_t = 0.0
	current_hurt_stun = hurt_stun_time * (1.4 if info.heavy else 1.0)
	return true

func _state_hurt(delta: float) -> void:
	ground_vel = Vector2.ZERO
	show_frame("hurt", 0 if state_t < current_hurt_stun * 0.55 else 1)
	move_actor(Vector2.ZERO, delta)
	if state_t >= current_hurt_stun:
		state = State.IDLE

func _on_health_died() -> void:
	state = State.DEAD
	state_t = 0.0
	ground_vel = Vector2.ZERO
	play_once("death", 0.9)
	Sfx.play("defeat", -4.0, 1.0, 0.0)
	Sfx.stop_music(2.5)
	await get_tree().create_timer(1.9, true, false, true).timeout
	Game.on_player_died()

# ------------------------------------------------------------------ colisão suave com inimigos
## Os inimigos não bloqueiam o jogador como paredes; em vez disso ele é empurrado para fora.
func _push_out_of_enemies() -> void:
	for n in get_tree().get_nodes_in_group("enemies"):
		var e := n as Enemy
		if e == null or not e.is_targetable():
			continue
		var d := Iso.to_ground(global_position - e.global_position)
		var min_d := body_radius + e.body_radius * 0.85
		var l := d.length()
		if l < min_d:
			var dir := d / l if l > 0.01 else -facing
			move_and_collide(Iso.to_screen(dir * (min_d - l)))
