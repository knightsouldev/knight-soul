class_name SlashEffect
extends Node2D
## Arco branco do golpe de espada. A cena aplica um achatamento 2:1 (escala Y = 0.5) para
## o arco "deitar" no chão isométrico; o filho "Arco" é girado para a direção do golpe.

@onready var arc: AnimatedSprite2D = $Arco

## dir_ground: direção do golpe (espaço de chão). flip: inverte o arco (2º golpe do combo).
func setup(dir_ground: Vector2, flip: bool, tint: Color) -> void:
	arc.rotation = dir_ground.angle()
	arc.scale = Vector2(1.25, -1.25 if flip else 1.25)
	arc.modulate = tint
	arc.play("default")
	arc.animation_finished.connect(queue_free)
