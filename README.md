# KNIGHT SOULS — Demo 1 «Ruínas Esquecidas» · versão 2 (refatorada e editável)

RPG de ação 2D isométrico, fantasia sombria, combate soulslike. **Godot 4.3+** (testado apenas por verificação estática; veja abaixo).
👉 **Para editar o jogo, comece por [`GUIA_DE_EDICAO.md`](GUIA_DE_EDICAO.md).**

> ⚠️ **Status de verificação:** esta versão foi produzida num ambiente **sem a Godot**. Nenhuma parte foi executada no motor.
> A versão 1 (código gerando tudo em tempo de execução) você já abriu e rodou; a versão 2 muda **a estrutura**, não o jogo.
> Os testes realmente feitos estão em [Testes](#testes-realizados). Se aparecer erro na primeira execução, copie a mensagem
> do painel *Saída/Depurador* (arquivo e linha) e envie.

## Como abrir
1. Descompacte, abra a Godot (4.3 ou mais nova; a 4.6 funciona com o aviso de conversão) → **Importar** → `project.godot`.
2. Aguarde a importação. Abra `scenes/areas/ruinas.tscn` e olhe a árvore de nós e a tela 2D: **o cenário agora aparece no editor**.
3. **F5** joga (menu principal → *Iniciar jornada*).

Controles e teclas de depuração: veja o fim do `GUIA_DE_EDICAO.md` e o menu de pausa. (WASD, clique = atacar, Espaço = esquiva, Q = curar,
E = usar item, 1–4 = itens, Esc = pausa; `F1` invencível, `F3` vai à arena, `F2` chefe com 8%).

## O que foi preservado (sem mudar)
* **Gameplay e identidade visual:** mesmos sprites, tiles, props, HUD, áudio, fontes, números de balanceamento (padrões idênticos
  aos da v1: vida, dano, tempos, stamina, esquiva, cura, 3 ataques do chefe, fase 2, vulnerabilidade, recompensas).
* **Sistemas:** estados e ataques do jogador, IA dos 3 inimigos, chefe (estados, telegráficos, investida com atordoamento na parede,
  golpe de área, fase 2, combo), hitboxes em arco/círculo/faixa com oclusão por parede, navegação A*, hit-stop, tremor, partículas,
  iluminação 2D, névoa, fade de paredes, ciclo morrer/vencer/reiniciar, itens, bússola, música e efeitos.
* **O mapa:** mesmo layout (1066 células de chão, 238 paredes, 102 props, 9 inimigos, 4 itens, portão, portal, arena) — conferido pelas contagens.

## O que foi alterado

| Antes (v1) | Agora (v2) |
|---|---|
| `ruinas.tscn` era só 1 nó; o `level.gd` construía tudo por código a partir de um JSON | **452 nós** na cena: chão em **`TileMapLayer` + `TileSet`**, paredes/decoração/inimigos/itens como **instâncias de cenas**, marcadores, gatilho da arena, HUD |
| Personagens: sprite, sombra, colisão, vida e luz criados em código | Cenas com nós identificáveis: `Colisao`, `Sombra`, `Sprite` (AnimatedSprite2D), `Vida`, `Luz`, `Camera`, `Telegrafo` |
| Animações montadas em código lendo JSON | **`resources/frames/*.tres`** (SpriteFrames editável no painel de animação) |
| Números em `balance.gd` | **`@export`** no Inspector: jogador (`player.gd`), chefe (`boss.gd`) e **arquivos `EnemyStats` (`resources/stats/*.tres`)** para os inimigos |
| HUD/menus construídos em código (`UiKit`) | Cenas `hud.tscn`, `pause_menu.tscn`, `end_screen.tscn`, `main_menu.tscn` com nós nomeados; botões ligados por **sinais na própria cena**; tema `tema_medieval.tres` |
| Props: sprites montados a partir de `props.json` | 1 cena por tipo em `scenes/world/props/` (sprite, colisão `Corpo`, `Luz`, `Brilho`, `Brasas`) |
| Colisões de borda e penhascos gerados no `Level` | Nó **`BordasDoChao`** (`@tool`, gera a partir do chão pintado; aparece no editor) |
| Patrulhas/spawns em JSON | `Marker2D` visíveis em `Marcadores/` ligados por `NodePath` |
| Efeitos faísca/corte/projétil/item criados em código | Cenas em `scenes/effects/` |
| Comentários sem acento, nomes de grupos em inglês | Comentários e documentação em português, `@export_group` e dicas (`##`) em português |

**Removidos** (substituídos): `balance.gd`, `actor_art.gd`, `ui_kit.gd` e a leitura de JSON em tempo de execução. Os dados dos geradores
passaram para `tools/data/`. Os scripts que fizeram a conversão ficam em `tools/conversao_para_cenas/` **apenas como histórico** (não rode: sobrescrevem edições).

## Estrutura
```
project.godot  GUIA_DE_EDICAO.md  README.md
scenes/  areas/ruinas.tscn  player/  enemies/  bosses/  ui/  main/  effects/  world/{props,pieces}
scripts/ combat/ player/ enemies/ bosses/ world/ ui/ systems/
resources/ frames/ stats/ tilesets/ themes/ shaders/ data/ruinas_chao.json (rede de segurança)
assets/    characters enemies bosses environments props effects ui audio fonts
tools/     geradores de assets (Python), verificadores, previa
```
Arquitetura para crescer: **Actor → Player / Enemy → Wraith / Boss**; novos inimigos = cena + `EnemyStats.tres`; novos chefes = cena que
herda de `boss.gd`/`enemy.gd`; novas áreas = nova cena com `Level` (chão no TileMapLayer, `%Nomes` únicos); `Game` guarda o estado global.

## Testes realizados
Feitos de verdade (Python, neste ambiente):
* `tools/check_scenes.py` — verificador estrutural de **40 cenas e 20 recursos**: todo `ExtResource/SubResource` resolve; todos os arquivos
  referenciados existem; hierarquia de nós válida e sem duplicatas; tipo do nó × `extends` do script; toda propriedade definida nas cenas
  é `@export` do script (ou nativa conhecida), inclusive overrides de instâncias; todo `$Nome` e `%Nome` usado pelos scripts existe
  nas cenas que os usam; métodos dos sinais existem; `NodePath` exportados resolvem. **Validado com testes negativos** (6 falhas
  injetadas foram detectadas).
* `tools/check_project.py` — referências `res://`, símbolos entre classes, `:=` sobre Variant, indentação, balanceamento, animações e sons existentes.
* `tools/preview_scene.py` — renderiza uma prévia **lendo o `ruinas.tscn`** (decodifica o TileMapLayer, resolve instâncias e offsets):
  1066 células, 238 paredes, 102 props, 11 atores; imagem conferida visualmente (`docs/previa_*.png`; iluminação aproximada, **não é captura do jogo**).
* Comparação programática do `balance.gd` da v1 com os novos `@export` e `.tres` (jogador, 4 fichas de inimigos, 3 ataques do chefe, fase 2): **0 divergências** nos valores padrão.

**NÃO testado (exige a Godot):** abertura/importação, parse dos scripts, qualquer execução, física/colisões, sensação do combate, desempenho,
iluminação final, mortes/reinícios seguidos, console sem erros, e **como o editor exibe cada cena**.

### Pontos que mais merecem sua atenção na primeira abertura
1. **Chão (`TileMapLayer`)**: os dados dos tiles foram escritos no formato binário do `tile_map_data` e o alinhamento assume que a Godot centra a
   célula (0,0) em (0,0) do layer (por isso `Position = (0,16)`). Se o chão aparecer vazio ou deslocado ~16 px, veja o item 7 do guia. O jogo tem **duas
   redes de segurança** em `level.gd`: se o TileMap vier vazio ele é reconstruído de `resources/data/ruinas_chao.json`, e se estiver desalinhado ele é
   corrigido ao rodar (com aviso no painel *Saída*).
2. **Penhascos e bordas** só aparecem no editor se `BordasDoChao` rodar como `@tool` sem erro (senão marque `regenerate`).
3. Ao rodar, observe o painel **Saída** por erros de script; envie-os se houver.

## Limitações conhecidas
Mesmas da v1 (arte procedural, áudio sintetizado, sem gamepad/salvamento) e: o mapa continua sendo editado "peça a peça" (sem editor de salas);
as animações dos personagens são geradas por scripts Python (`tools/gen_chars.py`) — para mudá-las à mão, substitua os PNGs mantendo as proporções.
