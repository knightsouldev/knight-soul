class_name MistDrift
extends Node2D
## Faz os sprites de névoa (filhos deste nó) deslizarem devagar para o lado.
## Para mudar a névoa: mova/duplique/apague os filhos, ou mude a cor (Modulate) deles.

## Velocidade horizontal (pixels por segundo).
@export var speed := 3.0
## Quando um filho passa deste X, volta para trás.
@export var wrap_x := 3200.0
## Quanto volta ao dar a volta.
@export var wrap_distance := 5200.0

func _process(delta: float) -> void:
	for c in get_children():
		var s := c as Node2D
		if s == null:
			continue
		s.position.x += speed * delta
		if s.position.x > wrap_x:
			s.position.x -= wrap_distance
