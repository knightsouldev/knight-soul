class_name Shockwave
extends Node2D
## Anel de choque que se expande no chao (desenhado em espaco de chao, achatado 2:1).

var max_radius := 140.0
var color := Color(0.75, 0.4, 1.0)
var duration := 0.45
var _t := 0.0

func _ready() -> void:
	z_index = 12

func _process(delta: float) -> void:
	_t += delta
	if _t >= duration:
		queue_free()
		return
	queue_redraw()

func _draw() -> void:
	var k := clampf(_t / duration, 0.0, 1.0)
	var r := max_radius * (1.0 - pow(1.0 - k, 3.0))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, 0.5))
	var a := 1.0 - k
	draw_arc(Vector2.ZERO, r, 0.0, TAU, 64, Color(color.r, color.g, color.b, a), 5.0 * (1.0 - k) + 1.5)
	draw_arc(Vector2.ZERO, r * 0.86, 0.0, TAU, 64, Color(1, 1, 1, a * 0.5), 2.0)
