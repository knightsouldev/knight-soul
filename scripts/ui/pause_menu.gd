class_name PauseMenu
extends CanvasLayer
## MENU DE PAUSA (Esc). Visual na cena pause_menu.tscn. Funciona com o jogo pausado
## (o nó está em modo "Always"). Os botões estão ligados aos métodos abaixo pela aba
## "Nó > Sinais" do editor (veja as linhas "connection" na cena).

signal resume_requested
signal restart_requested
signal menu_requested

func _ready() -> void:
	visible = false

func open() -> void:
	visible = true
	get_tree().paused = true
	Sfx.play("click")
	(%BotaoContinuar as Button).grab_focus()

func close() -> void:
	visible = false
	get_tree().paused = false

func _unhandled_input(event: InputEvent) -> void:
	if visible and event.is_action_pressed("pause"):
		close()
		get_viewport().set_input_as_handled()

# Sinais dos botões (ligados na cena)
func _on_continuar_pressed() -> void:
	resume_requested.emit()

func _on_reiniciar_pressed() -> void:
	restart_requested.emit()

func _on_menu_pressed() -> void:
	menu_requested.emit()

func _on_sair_pressed() -> void:
	get_tree().quit()
