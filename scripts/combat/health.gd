class_name Health
extends Node
## Componente de vida, independente de quem o possui.

signal changed(current: float, maximum: float)
signal damaged(amount: float)
signal died

var maximum := 100.0
var current := 100.0
var dead := false

func setup(max_hp: float) -> void:
	maximum = max_hp
	current = max_hp
	dead = false
	changed.emit(current, maximum)

func damage(amount: float) -> void:
	if dead:
		return
	current = maxf(0.0, current - amount)
	damaged.emit(amount)
	changed.emit(current, maximum)
	if current <= 0.0:
		dead = true
		died.emit()

func heal(amount: float) -> float:
	if dead:
		return 0.0
	var before := current
	current = minf(maximum, current + amount)
	changed.emit(current, maximum)
	return current - before

func ratio() -> float:
	return current / maximum if maximum > 0.0 else 0.0
