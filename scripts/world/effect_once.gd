class_name EffectOnce
extends AnimatedSprite2D
## Efeito de sprite que toca uma vez e some (faísca de impacto).

func _ready() -> void:
	play("default")
	animation_finished.connect(queue_free)
