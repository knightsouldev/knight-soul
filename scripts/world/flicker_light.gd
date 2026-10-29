class_name FlickerLight
extends PointLight2D
## LUZ QUE TREMULA (tochas, chamas azuis, portal). O brilho base é o "Energy" da luz.

## Liga/desliga o tremor.
@export var flicker := true
## Intensidade do tremor (0 = nenhuma).
@export var flicker_strength := 1.0

var _base := 1.0
var _phase := 0.0

func _ready() -> void:
	_base = energy
	_phase = randf() * TAU

func _process(_delta: float) -> void:
	if not flicker:
		return
	var t := Time.get_ticks_msec() / 1000.0
	var wobble := 0.08 * sin(t * 9.0 + _phase) + 0.06 * sin(t * 23.0 + _phase * 2.0)
	energy = _base * (0.88 + wobble * flicker_strength)
