class_name Telegraph
extends Node2D
## Indicador de perigo no chao (circulo, cone ou faixa), desenhado em espaco de chao.

enum Shape { CIRCLE, CONE, LINE }

var shape: Shape = Shape.CIRCLE
var radius := 100.0
var dir := Vector2.RIGHT
var arc_deg := 90.0
var length := 200.0
var width := 40.0
var progress := 0.0
var active := false
var col := Color(0.85, 0.15, 0.2)

func _ready() -> void:
	z_index = -5

func show_circle(r: float, c: Color) -> void:
	shape = Shape.CIRCLE
	radius = r
	col = c
	progress = 0.0
	active = true
	queue_redraw()

func show_cone(r: float, arc: float, d: Vector2, c: Color) -> void:
	shape = Shape.CONE
	radius = r
	arc_deg = arc
	dir = d
	col = c
	progress = 0.0
	active = true
	queue_redraw()

func show_line(len_: float, w: float, d: Vector2, c: Color) -> void:
	shape = Shape.LINE
	length = len_
	width = w
	dir = d
	col = c
	progress = 0.0
	active = true
	queue_redraw()

func set_progress(p: float) -> void:
	progress = clampf(p, 0.0, 1.0)
	queue_redraw()

func hide_it() -> void:
	active = false
	queue_redraw()

func _cone_points(r: float) -> PackedVector2Array:
	var pts := PackedVector2Array()
	pts.append(Vector2.ZERO)
	var a0 := dir.angle() - deg_to_rad(arc_deg) * 0.5
	var steps := 16
	for i in steps + 1:
		var a := a0 + deg_to_rad(arc_deg) * float(i) / float(steps)
		pts.append(Vector2(cos(a), sin(a)) * r)
	return pts

func _line_points(len_: float) -> PackedVector2Array:
	var n := Vector2(-dir.y, dir.x) * width * 0.5
	var f := dir * len_
	return PackedVector2Array([n, n + f, -n + f, -n])

func _draw() -> void:
	if not active:
		return
	draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, 0.5))
	var fill := Color(col.r, col.g, col.b, 0.10 + 0.10 * progress)
	var edge := Color(col.r, col.g, col.b, 0.55 + 0.4 * progress)
	var inner := Color(col.r, col.g, col.b, 0.22 + 0.30 * progress)
	match shape:
		Shape.CIRCLE:
			draw_circle(Vector2.ZERO, radius, fill)
			draw_circle(Vector2.ZERO, radius * progress, inner)
			draw_arc(Vector2.ZERO, radius, 0.0, TAU, 56, edge, 2.5)
		Shape.CONE:
			draw_colored_polygon(_cone_points(radius), fill)
			draw_colored_polygon(_cone_points(radius * progress), inner)
			var outline := _cone_points(radius)
			outline.append(outline[0])
			draw_polyline(outline, edge, 2.5)
		Shape.LINE:
			draw_colored_polygon(_line_points(length), fill)
			draw_colored_polygon(_line_points(length * progress), inner)
			var o := _line_points(length)
			o.append(o[0])
			draw_polyline(o, edge, 2.5)
