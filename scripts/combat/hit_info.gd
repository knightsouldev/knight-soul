class_name HitInfo
extends RefCounted
## Dados de um golpe: quem causou, quanto dano e de onde veio.

var damage := 10.0
var origin := Vector2.ZERO        # posicao de tela do atacante
var knockback := 80.0             # impulso em unidades de chao/s
var source: Node = null
var heavy := false                # golpes pesados interrompem acoes do alvo por mais tempo
