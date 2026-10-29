class_name EnemyStats
extends Resource
## Ficha de atributos de um inimigo. Cada tipo de inimigo tem um arquivo .tres em
## res://resources/stats/ (soldier.tres, guardian.tres...). Para criar um inimigo novo:
## duplique um .tres, mude os números aqui no Inspector e aponte o inimigo para ele.
## Distâncias estão em "unidades de chão" (≈ pixels na horizontal; 1 célula ≈ 45 unidades).

@export_group("Vida e corpo")
## Vida máxima.
@export var max_health := 60.0
## Raio do corpo (usado em colisão suave e para saber se o golpe do jogador acerta).
@export var body_radius := 11.0

@export_group("Movimento")
## Velocidade ao patrulhar ou voltar para casa.
@export var walk_speed := 46.0
## Velocidade ao perseguir o jogador.
@export var chase_speed := 84.0

@export_group("Percepção")
## Distância em que ele nota o jogador (precisa de linha de visão).
@export var detect_range := 200.0
## Distância em que ele desiste da perseguição.
@export var lose_range := 360.0

@export_group("Ataque corpo a corpo")
## Distância (até o jogador) em que ele começa a preparar o golpe.
@export var attack_range := 46.0
## Alcance real do golpe.
@export var attack_reach := 58.0
## Abertura do golpe em graus (cone).
@export var attack_arc_deg := 100.0
## Tempo de preparação (o jogador vê o aviso vermelho no chão).
@export var windup_time := 0.55
## Tempo em que o golpe machuca.
@export var active_time := 0.12
## Tempo parado depois do golpe (momento de contra-atacar).
@export var recover_time := 0.80
## Pausa mínima entre dois ataques.
@export var cooldown_time := 0.6
## Dano causado ao jogador.
@export var damage := 14.0
## Avanço rápido durante o golpe.
@export var lunge_speed := 90.0

@export_group("Reação a dano")
## Quanto tempo fica atordoado ao ser atingido (0 = nunca cambaleia).
@export var stagger_time := 0.38
## Multiplicador do empurrão recebido (1 = normal, 0 = imóvel).
@export var knockback_multiplier := 1.0

@export_group("Recompensa")
## Almas dadas ao morrer.
@export var souls_reward := 40

@export_group("Ataque à distância (espectro)")
## Velocidade do projétil.
@export var bolt_speed := 150.0
## Distância mínima que prefere manter do jogador.
@export var preferred_distance_min := 150.0
## Distância máxima que prefere manter do jogador.
@export var preferred_distance_max := 250.0
