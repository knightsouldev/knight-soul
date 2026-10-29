class_name Iso
extends RefCounted
## Matematica isometrica 2:1. Celulas do mapa sao losangos de 64x32.
## "Espaco de chao" = tela com y dobrado: distancias e angulos ali sao reais.

static func cell_to_screen(c: Vector2) -> Vector2:
	return Vector2((c.x - c.y) * 32.0, (c.x + c.y) * 16.0)

static func screen_to_cell(s: Vector2) -> Vector2:
	return Vector2((s.x / 32.0 + s.y / 16.0) * 0.5, (s.y / 16.0 - s.x / 32.0) * 0.5)

static func to_ground(v: Vector2) -> Vector2:
	return Vector2(v.x, v.y * 2.0)

static func to_screen(g: Vector2) -> Vector2:
	return Vector2(g.x, g.y * 0.5)
