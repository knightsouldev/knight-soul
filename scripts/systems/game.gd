extends Node
## AUTOLOAD "Game": estado da tentativa atual (almas, frascos, item selecionado)
## e sinais globais que a interface e o mundo escutam.
## Autoloads ficam em Projeto > Configurações do Projeto > Autoload.

signal souls_changed(total: int, delta: int)
signal flasks_changed(current: int)
signal oil_changed(charges: int)
signal slot_changed(slot: int)
signal notified(text: String)
signal player_died
signal boss_started
signal boss_defeated
signal stamina_denied

## Quantos frascos de cura o jogador começa com (e o máximo).
const FLASKS_MAX := 4
## Cargas de Óleo de Lâmina no início.
const OIL_MAX := 2

var souls := 0
var flasks := FLASKS_MAX
var oil := OIL_MAX
var selected_slot := 0
var run_state := "playing"      # "playing" | "dead" | "victory"
var god_mode := false           # tecla F1 (depuração)
var _hit_stop_id := 0

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_ensure_actions()

## Zera tudo para uma nova tentativa (chamado quando a fase começa).
func reset_run() -> void:
	Engine.time_scale = 1.0
	_hit_stop_id += 1
	get_tree().paused = false
	souls = 0
	flasks = FLASKS_MAX
	oil = OIL_MAX
	selected_slot = 0
	run_state = "playing"
	souls_changed.emit(souls, 0)
	flasks_changed.emit(flasks)
	oil_changed.emit(oil)
	slot_changed.emit(selected_slot)

func add_souls(amount: int) -> void:
	souls += amount
	souls_changed.emit(souls, amount)

func use_flask() -> bool:
	if flasks <= 0:
		return false
	flasks -= 1
	flasks_changed.emit(flasks)
	return true

func use_oil() -> bool:
	if oil <= 0:
		return false
	oil -= 1
	oil_changed.emit(oil)
	return true

func refill_items() -> void:
	flasks = FLASKS_MAX
	oil = OIL_MAX
	flasks_changed.emit(flasks)
	oil_changed.emit(oil)

func select_slot(i: int) -> void:
	selected_slot = posmod(i, 4)
	slot_changed.emit(selected_slot)

## Mostra uma mensagem curta na tela (a HUD escuta este sinal).
func notify(text: String) -> void:
	notified.emit(text)

func on_player_died() -> void:
	if run_state != "playing":
		return
	run_state = "dead"
	player_died.emit()

func on_boss_defeated() -> void:
	if run_state != "playing":
		return
	run_state = "victory"
	boss_defeated.emit()

## Congela o jogo por instantes ao acertar golpes (sensação de peso).
func hit_stop(duration: float, time_scale: float = 0.06) -> void:
	_hit_stop_id += 1
	var id := _hit_stop_id
	Engine.time_scale = time_scale
	await get_tree().create_timer(duration, true, false, true).timeout
	if id == _hit_stop_id:
		Engine.time_scale = 1.0

# --------------------------------------------------------------------------
# Entradas padrão. As ações também estão em project.godot (editáveis em
# Projeto > Configurações do Projeto > Mapa de Entrada). Se alguma estiver
# ausente, este trecho a recria.
# --------------------------------------------------------------------------
func _ensure_actions() -> void:
	var defaults := {
		"move_left": [KEY_A, KEY_LEFT], "move_right": [KEY_D, KEY_RIGHT],
		"move_up": [KEY_W, KEY_UP], "move_down": [KEY_S, KEY_DOWN],
		"dodge": [KEY_SPACE, KEY_SHIFT], "heal": [KEY_Q, KEY_R], "use_item": [KEY_E],
		"slot_1": [KEY_1], "slot_2": [KEY_2], "slot_3": [KEY_3], "slot_4": [KEY_4],
		"pause": [KEY_ESCAPE, KEY_P], "confirm": [KEY_ENTER, KEY_KP_ENTER],
	}
	for action in defaults.keys():
		if InputMap.has_action(action):
			continue
		InputMap.add_action(action)
		for k in defaults[action]:
			var ev := InputEventKey.new()
			ev.physical_keycode = k as Key
			InputMap.action_add_event(action, ev)
	if not InputMap.has_action("attack"):
		InputMap.add_action("attack")
		var mb := InputEventMouseButton.new()
		mb.button_index = MOUSE_BUTTON_LEFT
		InputMap.action_add_event("attack", mb)
		var kj := InputEventKey.new()
		kj.physical_keycode = KEY_J
		InputMap.action_add_event("attack", kj)
	if not InputMap.has_action("slot_next"):
		InputMap.add_action("slot_next")
		var wd := InputEventMouseButton.new()
		wd.button_index = MOUSE_BUTTON_WHEEL_DOWN
		InputMap.action_add_event("slot_next", wd)
	if not InputMap.has_action("slot_prev"):
		InputMap.add_action("slot_prev")
		var wu := InputEventMouseButton.new()
		wu.button_index = MOUSE_BUTTON_WHEEL_UP
		InputMap.action_add_event("slot_prev", wu)
