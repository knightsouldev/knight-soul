class_name WallPiece
extends Sprite2D
## BLOCO DE PAREDE do cenário. Cada bloco é um Sprite2D (com este script) instanciado
## a partir de scenes/world/pieces/parede.tscn.
##
## COMO EDITAR: selecione o bloco e
##   - mude a propriedade "Texture" para trocar o tipo (altura 1, 2 ou 3, com ou sem
##     estandarte/arco) — as imagens estão em assets/environments/wall_*.png;
##   - arraste-o para mover. A posição (0,0) do nó é o ponto de ordenação (y-sort),
##     por isso a imagem é deslocada pelo "Offset" (já ajustado em cada bloco).

## Fica translúcido quando está na frente do jogador (paredes altas).
@export var fades_when_hiding_player := true

func _ready() -> void:
	if fades_when_hiding_player:
		add_to_group("oclusor")

func get_occlusion_rect() -> Rect2:
	return get_rect()
