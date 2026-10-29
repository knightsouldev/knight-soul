class_name Prop
extends Node2D
## OBJETO DECORATIVO DO CENÁRIO (braseiro, pilar, estátua, cristal, plantas...).
## Cada tipo é uma cena em res://scenes/world/props/. Para decorar o mapa, arraste
## uma delas para dentro de Mundo/Decoracao (ou da área desejada) no Level.
## A origem (0,0) do objeto é o ponto onde ele "pisa no chão".

@export_group("Comportamento")
## Inimigos desviam deste objeto (a célula do chão dele vira obstáculo na navegação).
## A colisão física vem do nó "Corpo" da própria cena.
@export var blocks_navigation := false
## Fica translúcido quando está na frente do jogador (objetos altos).
@export var fades_when_hiding_player := false
## Começa a animação em um quadro aleatório (evita chamas todas iguais).
@export var randomize_animation := true

func _ready() -> void:
	if blocks_navigation:
		add_to_group("bloqueia_navegacao")
	if fades_when_hiding_player:
		add_to_group("oclusor")
	if randomize_animation:
		for child in get_children():
			var a := child as AnimatedSprite2D
			if a != null and a.sprite_frames != null:
				a.frame = randi() % maxi(1, a.sprite_frames.get_frame_count(a.animation))
				a.speed_scale = randf_range(0.9, 1.1)

## Retângulo (em coordenadas locais) que o objeto ocupa na tela; usado no fade de oclusão.
func get_occlusion_rect() -> Rect2:
	for child in get_children():
		var s := child as Sprite2D
		if s != null and s.texture != null and s.visible:
			return Rect2(s.position + s.offset, s.texture.get_size())
		var a := child as AnimatedSprite2D
		if a != null and a.sprite_frames != null:
			var tex := a.sprite_frames.get_frame_texture(a.animation, 0)
			if tex != null:
				return Rect2(a.position + a.offset, tex.get_size())
	return Rect2()
