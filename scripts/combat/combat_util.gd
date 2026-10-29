class_name CombatUtil
extends RefCounted
## Testes de acerto em "espaco de chao" (y dobrado) e oclusao por paredes.

## Arco (cone) a partir de origin, na direcao dir_ground.
static func arc_hit(origin: Vector2, dir_ground: Vector2, reach: float, arc_deg: float, target: Vector2, target_radius: float) -> bool:
	var d := Iso.to_ground(target - origin)
	var dist := d.length()
	if dist > reach + target_radius:
		return false
	if dist <= target_radius + 6.0:
		return true
	var ang := absf(rad_to_deg(dir_ground.angle_to(d)))
	var slack := rad_to_deg(asin(clampf(target_radius / dist, 0.0, 1.0)))
	return ang <= arc_deg * 0.5 + slack

static func circle_hit(origin: Vector2, radius: float, target: Vector2, target_radius: float) -> bool:
	return Iso.to_ground(target - origin).length() <= radius + target_radius

## Faixa retangular (investidas).
static func line_hit(origin: Vector2, dir_ground: Vector2, length: float, width: float, target: Vector2, target_radius: float) -> bool:
	var d := Iso.to_ground(target - origin)
	var along := d.dot(dir_ground)
	var perp := absf(d.cross(dir_ground))
	return along > -target_radius and along <= length + target_radius and perp <= width * 0.5 + target_radius

## Verdadeiro se nao ha parede (camada 1) entre os dois pontos de tela.
static func line_of_sight(space: PhysicsDirectSpaceState2D, a: Vector2, b: Vector2) -> bool:
	var q := PhysicsRayQueryParameters2D.create(a, b, 1)
	q.collide_with_areas = false
	return space.intersect_ray(q).is_empty()
