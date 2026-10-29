extends Control
## MENU PRINCIPAL (cena main_menu.tscn). Todo o visual está na cena; aqui só ficam
## as ações dos botões. Para mudar o título, cores ou posições, edite a cena.

@onready var controls_panel: Control = %PainelControles
@onready var start_button: Button = %BotaoIniciar

func _ready() -> void:
	controls_panel.visible = false
	start_button.grab_focus()
	Sfx.play_music("ambient", 2.0)

# Sinais dos botões (ligados na cena)
func _on_iniciar_pressed() -> void:
	Sfx.play("click")
	get_tree().change_scene_to_file("res://scenes/areas/ruinas.tscn")

func _on_controles_pressed() -> void:
	controls_panel.visible = not controls_panel.visible

func _on_sair_pressed() -> void:
	get_tree().quit()
