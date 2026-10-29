class_name EndScreen
extends CanvasLayer
## TELA FINAL: derrota ("VOCÊ SUCUMBIU") ou vitória ("SENTINELA DERROTADA").
## Visual na cena end_screen.tscn (textos, cores, botões). O script controla só o
## aparecimento gradual e qual versão mostrar.

signal retry_requested
signal menu_requested
signal continue_requested

## Cor do título na derrota / na vitória.
@export var defeat_color := Color(0.72, 0.14, 0.14)
@export var victory_color := Color(0.92, 0.8, 0.5)
## Tempo (s) até os botões aparecerem e poderem ser usados.
@export var buttons_delay := 1.6

@onready var dim: ColorRect = %Escurecer
@onready var title: Label = %Titulo
@onready var subtitle: Label = %Subtitulo
@onready var buttons: Control = %Botoes
@onready var retry_button: Button = %BotaoTentar
@onready var continue_button: Button = %BotaoContinuar

var _t := 0.0
var _shown := false

func _ready() -> void:
	visible = false

func show_defeat() -> void:
	title.text = "VOCÊ SUCUMBIU"
	title.add_theme_color_override("font_color", defeat_color)
	subtitle.text = "As ruínas lembram de cada passo.\nCada tentativa recomeça a jornada do início."
	continue_button.visible = false
	_begin()

func show_victory(souls_total: int) -> void:
	title.text = "SENTINELA DERROTADA"
	title.add_theme_color_override("font_color", victory_color)
	subtitle.text = "Almas libertadas: +1500   ·   Total: %d" % souls_total
	continue_button.visible = true
	_begin()

func _begin() -> void:
	visible = true
	_shown = true
	_t = 0.0
	get_tree().paused = true
	retry_button.call_deferred("grab_focus")

func hide_screen() -> void:
	visible = false
	_shown = false

func _process(delta: float) -> void:
	if not _shown:
		return
	_t += delta
	dim.color.a = clampf(_t / 1.2, 0.0, 0.78)
	title.modulate.a = clampf((_t - 0.3) / 1.0, 0.0, 1.0)
	subtitle.modulate.a = clampf((_t - 1.0) / 1.0, 0.0, 1.0)
	buttons.modulate.a = clampf((_t - buttons_delay) / 0.8, 0.0, 1.0)

func _unhandled_input(event: InputEvent) -> void:
	if _shown and _t >= buttons_delay and event.is_action_pressed("confirm"):
		retry_requested.emit()

# Sinais dos botões (ligados na cena)
func _on_tentar_pressed() -> void:
	retry_requested.emit()

func _on_continuar_pressed() -> void:
	continue_requested.emit()

func _on_menu_pressed() -> void:
	menu_requested.emit()
