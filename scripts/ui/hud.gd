class_name Hud
extends CanvasLayer
## HUD (interface durante o jogo). Todos os elementos visuais estão na cena hud.tscn:
## mova, redimensione, troque imagens e textos direto no editor.
## Este script só ATUALIZA os valores (vida, stamina, frascos, almas, chefe...).
##
## Mapa rápido dos nós principais (cena hud.tscn):
##   CantoSuperiorEsquerdo : orbe, barra de vida, barra de stamina, gotas dos frascos
##   PainelChefe           : nome, barra de vida e subtítulo do chefe (aparece na luta)
##   Atalhos               : 4 slots de item e o destaque do slot selecionado
##   Almas                 : contador de almas        Bussola : progresso até a arena
##   Objetivo              : nome da área e objetivo   Aviso/Dica/TituloArea : textos temporários

## Tempo (s) que a dica de controles fica visível no início.
@export var hint_seconds := 9.0
## Tempo (s) que o título da área fica visível no início.
@export var title_seconds := 4.5
## Distância entre os slots de item (precisa bater com o espaçamento na cena).
@export var slot_step := 42.0

@onready var life_fill: TextureProgressBar = %VidaPreenchimento
@onready var life_trail: TextureProgressBar = %VidaRastro
@onready var stamina_fill: TextureProgressBar = %StaminaPreenchimento
@onready var stamina_trail: TextureProgressBar = %StaminaRastro
@onready var boss_fill: TextureProgressBar = %ChefePreenchimento
@onready var boss_trail: TextureProgressBar = %ChefeRastro
@onready var boss_panel: Control = %PainelChefe
@onready var orb_gem: CanvasItem = %OrbeGema
var flask_drops: Array[TextureRect] = []   # preenchida no _ready com %Gota1..4
@onready var slot_selection: Control = %SelecaoSlot
@onready var oil_label: Label = %TextoOleo
@onready var flask_label: Label = %TextoFrascos
@onready var souls_label: Label = %TextoAlmas
@onready var compass_marker: Control = %MarcadorBussola
@onready var toast: Label = %Aviso
@onready var hint: Label = %Dica
@onready var area_title: Label = %TituloArea
@onready var area_subtitle: Label = %SubtituloArea
@onready var objective_label: Label = %TextoObjetivo
@onready var vignette: CanvasItem = %Vinheta

const DROP_FULL: Texture2D = preload("res://assets/ui/drop_full.png")
const DROP_EMPTY: Texture2D = preload("res://assets/ui/drop_empty.png")

var player: Player
var boss: Boss
var _soul_shown := 0.0
var _soul_target := 0
var _toast_t := 0.0
var _hurt := 0.0
var _sp_flash := 0.0
var _boss_alpha := 0.0
var _boss_visible := false
var _t := 0.0
var _hint_t := 0.0
var _title_t := 0.0
var _progress := 0.0

func _ready() -> void:
	flask_drops.append(%Gota1 as TextureRect)
	flask_drops.append(%Gota2 as TextureRect)
	flask_drops.append(%Gota3 as TextureRect)
	flask_drops.append(%Gota4 as TextureRect)
	_hint_t = hint_seconds
	_title_t = title_seconds
	boss_panel.modulate.a = 0.0
	Game.souls_changed.connect(_on_souls)
	Game.flasks_changed.connect(_on_flasks)
	Game.oil_changed.connect(_on_oil)
	Game.slot_changed.connect(_on_slot)
	Game.notified.connect(show_toast)
	Game.boss_started.connect(_on_boss_started)
	Game.boss_defeated.connect(_on_boss_defeated)
	Game.stamina_denied.connect(func() -> void: _sp_flash = 0.35)
	_on_flasks(Game.flasks)
	_on_oil(Game.oil)
	_on_slot(Game.selected_slot)
	_soul_target = Game.souls
	_soul_shown = float(Game.souls)

# ------------------------------------------------------------------ ligação com o jogo
## Conecta a HUD ao jogador e ao chefe (chamado pelo Level).
func bind(p: Player, b: Boss) -> void:
	player = p
	boss = b
	p.health.changed.connect(_on_hp)
	p.health.damaged.connect(func(_a: float) -> void: _hurt = 1.0)
	p.stamina_changed.connect(_on_stamina)
	_on_hp(p.health.current, p.health.maximum)
	if b != null:
		b.health.changed.connect(_on_boss_hp)
		_on_boss_hp(b.health.current, b.health.maximum)

func set_progress(f: float) -> void:
	_progress = clampf(f, 0.0, 1.0)

func set_objective(text: String) -> void:
	objective_label.text = text

func show_toast(text: String) -> void:
	toast.text = text
	_toast_t = 3.0

func _set_bar(fill: TextureProgressBar, trail: TextureProgressBar, ratio: float) -> void:
	var old := fill.value
	fill.value = ratio
	if ratio > old:
		trail.value = ratio       # curando: o rastro acompanha na hora

func _on_hp(cur: float, maxi: float) -> void:
	_set_bar(life_fill, life_trail, cur / maxi)

func _on_stamina(cur: float, maxi: float) -> void:
	_set_bar(stamina_fill, stamina_trail, cur / maxi)

func _on_boss_hp(cur: float, maxi: float) -> void:
	_set_bar(boss_fill, boss_trail, cur / maxi)

func _on_boss_started() -> void:
	_boss_visible = true
	set_objective("Sobreviva à Sentinela")
	show_toast("A passagem se fechou atrás de você")

func _on_boss_defeated() -> void:
	_boss_visible = false
	set_objective("Sentinela derrotada")

func _on_souls(total: int, _delta: int) -> void:
	_soul_target = total

func _on_flasks(n: int) -> void:
	for i in flask_drops.size():
		flask_drops[i].texture = DROP_FULL if i < n else DROP_EMPTY
	flask_label.text = str(n)

func _on_oil(n: int) -> void:
	oil_label.text = str(n)

func _on_slot(i: int) -> void:
	slot_selection.position = Vector2(float(i) * slot_step, 0.0)

# ------------------------------------------------------------------ animações da HUD
func _process(delta: float) -> void:
	_t += delta
	# o "rastro" claro que mostra o dano recente desce devagar até a barra
	for pair in [[life_fill, life_trail], [stamina_fill, stamina_trail], [boss_fill, boss_trail]]:
		var f := pair[0] as TextureProgressBar
		var tr := pair[1] as TextureProgressBar
		if tr.value > f.value:
			tr.value = maxf(f.value, tr.value - delta * 0.30)
	# stamina: pisca vermelho quando falta
	_sp_flash = maxf(0.0, _sp_flash - delta)
	if _sp_flash > 0.0:
		stamina_fill.modulate = Color(1.6, 0.5, 0.5)
	elif stamina_fill.value < 0.12:
		stamina_fill.modulate = Color(1.3, 0.7, 0.6) if int(_t * 6.0) % 2 == 0 else Color.WHITE
	else:
		stamina_fill.modulate = Color.WHITE
	# contador de almas "rola" até o valor real
	_soul_shown = move_toward(_soul_shown, float(_soul_target), maxf(40.0, absf(float(_soul_target) - _soul_shown) * 4.0) * delta)
	souls_label.text = str(roundi(_soul_shown))
	orb_gem.modulate = Color(1, 1, 1, 0.85 + 0.15 * sin(_t * 2.0))
	# vinheta escurece nas bordas; fica vermelha ao tomar dano e pulsa com pouca vida
	_hurt = maxf(0.0, _hurt - delta * 1.6)
	var low := 0.0
	if player != null and player.health.ratio() < 0.3 and not player.is_dead():
		low = 0.25 + 0.15 * sin(_t * 4.0)
	vignette.modulate = Color(1.0, 1.0 - _hurt * 0.7 - low * 0.5, 1.0 - _hurt * 0.7 - low * 0.5, 0.45 + _hurt * 0.55 + low)
	# painel do chefe aparece/desaparece
	_boss_alpha = move_toward(_boss_alpha, 1.0 if _boss_visible else 0.0, delta * 1.5)
	boss_panel.modulate.a = _boss_alpha
	# textos temporários
	_toast_t = maxf(0.0, _toast_t - delta)
	toast.modulate.a = clampf(_toast_t, 0.0, 1.0)
	_hint_t = maxf(0.0, _hint_t - delta)
	hint.modulate.a = clampf(_hint_t, 0.0, 1.0) * 0.8
	_title_t = maxf(0.0, _title_t - delta)
	var ta := clampf(minf(_title_t, title_seconds - _title_t) * 1.2, 0.0, 1.0)
	area_title.modulate.a = ta
	area_subtitle.modulate.a = ta
	compass_marker.position.x = 6.0 + _progress * (260.0 - 12.0 - 13.0)
