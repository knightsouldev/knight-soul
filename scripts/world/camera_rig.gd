class_name CameraRig
extends Camera2D
## Câmera que segue o jogador suavemente, com tremor de tela e limites do mapa.
## É filha do Jogador na cena player.tscn. Os limites são ajustados pelo Level.

## Quão rápido a câmera alcança o jogador.
@export var follow_speed := 7.0

var _shake := 0.0

func _ready() -> void:
	add_to_group("camera")
	position_smoothing_enabled = true
	position_smoothing_speed = follow_speed

## Treme a tela (chamado por Fx.shake). amount = força em pixels.
func shake(amount: float) -> void:
	_shake = maxf(_shake, amount)

func set_world_limits(r: Rect2) -> void:
	limit_left = int(r.position.x)
	limit_top = int(r.position.y)
	limit_right = int(r.end.x)
	limit_bottom = int(r.end.y)

func _process(delta: float) -> void:
	_shake = move_toward(_shake, 0.0, delta * 30.0)
	if _shake > 0.05:
		offset = Vector2(roundf(randf_range(-1.0, 1.0) * _shake), roundf(randf_range(-1.0, 1.0) * _shake))
	else:
		offset = Vector2.ZERO
