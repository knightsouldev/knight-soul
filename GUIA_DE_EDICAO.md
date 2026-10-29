# Guia rápido de edição — Knight Souls

Este projeto agora é **editável no editor da Godot**: tudo o que você vê no jogo existe como nós nas cenas.
Salve sempre com **Ctrl+S**; desfaça com **Ctrl+Z**. Dê **F5** para testar.

> Como achar as coisas: painel **Arquivos** (embaixo à esquerda) → duplo clique numa cena `.tscn` para abri-la.
> Painel **Cena** (em cima à esquerda) = a árvore de nós. **Inspector** (à direita) = propriedades do nó selecionado.

## 1. Mapa das pastas

| Quero mexer em... | Abra |
|---|---|
| A fase inteira | `scenes/areas/ruinas.tscn` |
| Jogador | `scenes/player/player.tscn` |
| Inimigos | `scenes/enemies/` (soldier, guardian, wraith) |
| Chefe | `scenes/bosses/sentinela.tscn` |
| HUD | `scenes/ui/hud.tscn` · pausa: `pause_menu.tscn` · vitória/derrota: `end_screen.tscn` |
| Menu inicial | `scenes/main/main_menu.tscn` |
| Objetos do cenário (braseiros, pilares...) | `scenes/world/props/` |
| Número de vida/dano dos inimigos | `resources/stats/*.tres` |
| Animações (quais quadros, velocidade) | `resources/frames/*.tres` |
| Imagens | `assets/` |

## 2. Editar o cenário (`ruinas.tscn`)

Árvore principal: **Camadas** (chão), **Mundo** (paredes, decoração, itens, inimigos, chefe, jogador),
**Marcadores**, **Arena**, **Hud**.

* **Pintar/apagar chão:** selecione o nó **Camadas/Chao** (TileMapLayer). Abre-se o painel **TileMap** embaixo: escolha uma
  das 8 pedras e pinte com o mouse (borracha para apagar). As **paredes invisíveis e os penhascos se ajustam sozinhos**
  quando você roda o jogo. Para ver os penhascos já no editor, selecione **BordasDoChao** e marque `regenerate`.
* **Mover um objeto/parede:** clique nele na tela (ou na árvore) e arraste, ou mude `Position` no Inspector.
* **Colocar um objeto novo:** arraste um arquivo de `scenes/world/props/` (ex.: `brazier.tscn`) para dentro de
  **Mundo/Decoracao/** (escolha a subpasta da área). Depois posicione. `Ctrl+D` duplica o selecionado.
* **Trocar o tipo de uma parede:** selecione a parede (em **Mundo/Paredes/...**) e, no Inspector, mude **Texture**
  (as paredes estão em `assets/environments/wall_*.png`; o número depois de `h` é a altura). *Se mudar a altura, ajuste `Offset`
  também: Y = −(altura em pixels + 30). Alturas: h1=28, h2=56, h3=84; o mais simples é trocar entre imagens da mesma altura.*
* **Por que objetos passam "atrás" ou "na frente"?** Os nós de **Mundo** usam *Y-Sort*: quem tem Y maior aparece na frente. Por isso
  a origem (o ponto `Position`) de cada objeto é onde ele "pisa no chão".
* **Inimigos:** arraste `soldier.tscn`/`guardian.tscn`/`wraith.tscn` para **Mundo/Inimigos** e posicione.
  **Patrulha:** crie um `Marker2D` em **Marcadores/Patrulhas** (botão direito → Adicionar nó filho), posicione e arraste-o para a lista
  **Patrol Points** do inimigo (Inspector). Sem pontos = fica parado.
* **Itens no chão:** arraste `scenes/effects/pickup.tscn` para **Mundo/Itens**; no Inspector escolha `Kind` (souls ou flask) e `Amount`.
* **Onde o jogador nasce:** mova o nó **Mundo/Jogador**. **Chefe:** mova **Mundo/Chefe**.
* **Gatilho da luta:** **Arena/GatilhoArena** (a faixa invisível que começa a luta). **Barreira de névoa:** **Arena/BarreiraNevoa**.
* **Bússola da HUD:** os pontos em **Marcadores/Bussola** formam a rota; mova-os se mudar o caminho.
* **Ver as colisões:** menu **Depuração → Formas de colisão visíveis**, depois F5.

## 3. Trocar sprites

* **Substituir uma imagem:** coloque um PNG com **o mesmo nome e o mesmo tamanho** em `assets/` (a Godot reimporta sozinha).
* **Personagens:** cada animação é uma "tira" de quadros lado a lado (`assets/characters`, `enemies`, `bosses`). As animações
  são montadas em `resources/frames/<personagem>.tres`: abra, e o painel **SpriteFrames** mostra os quadros e a velocidade.
* **Mudar o sprite de um nó:** selecione o nó **Sprite** do personagem → Inspector → **Sprite Frames**.
* **Criar um inimigo novo:** duplique `soldier.tscn` (botão direito → Duplicar), troque o **Sprite Frames**, e duplique
  `resources/stats/soldier.tres` para dar números próprios; aponte **Stats** do novo inimigo para ele.

## 4. Editar a HUD e os menus

Abra `scenes/ui/hud.tscn`. Cada pedaço é um nó com nome em português: `CantoSuperiorEsquerdo` (vida, stamina, orbe, frascos),
`PainelChefe`, `Atalhos` (4 slots), `Almas`, `Bussola`, `Objetivo`, textos temporários (`Aviso`, `Dica`, `TituloArea`).

* **Mover/redimensionar:** selecione e arraste (ou use as propriedades de *Layout*). Elementos "colados" a um canto usam **âncoras**
  (por isso se adaptam à janela).
* **Trocar imagem:** nó `TextureRect` → **Texture**; barras: `TextureProgressBar` → **Texture Progress**.
* **Mudar texto/cor/fonte:** nós `Label` → **Text** e *Theme Overrides*. Botões e fonte geral: `resources/themes/tema_medieval.tres`.
* **Botões:** a aba **Nó → Sinais** mostra o que cada botão chama (`_on_..._pressed`).

## 5. Onde está cada comportamento (scripts)

| Assunto | Script |
|---|---|
| Movimento, ataque, esquiva, cura, stamina | `scripts/player/player.gd` |
| Base de personagens (sprite, flash, knockback) | `scripts/combat/actor.gd` |
| Vida | `scripts/combat/health.gd` |
| Acertos em arco/círculo/faixa | `scripts/combat/combat_util.gd` |
| Aviso de perigo no chão | `scripts/combat/telegraph.gd` |
| IA de soldado e guardião | `scripts/enemies/enemy.gd` |
| Espectro e projétil | `scripts/enemies/wraith.gd`, `projectile.gd` |
| **Chefe** (estados, 3 ataques, fase 2) | `scripts/bosses/boss.gd` |
| A fase (liga tudo, gatilho do chefe, A*) | `scripts/world/level.gd` |
| Colisão/penhascos automáticos do chão | `scripts/world/bordas_do_chao.gd` |
| HUD / pausa / tela final / menu | `scripts/ui/*.gd` |
| Estado global (almas, frascos), entradas | `scripts/systems/game.gd` (autoload) |
| Sons e música | `scripts/systems/sfx.gd` |

Abrir um script: duplo clique no arquivo. Comentários em português explicam cada parte.

## 6. Ajustar números (sem programar)

* **Jogador:** selecione **Jogador** na cena player.tscn → Inspector: grupos *Movimento*, *Stamina*, *Ataque*, *Esquiva*, *Cura*.
* **Inimigos:** abra `resources/stats/soldier.tres` (etc.) e mude vida, dano, tempos de preparação/recuperação, alcance.
* **Chefe:** selecione o nó do chefe → Inspector: *Golpe pesado*, *Investida*, *Golpe de área*, *Fases*; vida em `stats/sentinela.tres`.

## 7. Se algo der errado

* **Chão desalinhado das paredes** (deslocado ~16 px): em ruinas.tscn selecione **Camadas/Chao** e mude `Position` Y entre `16` e `0`.
  (O jogo corrige sozinho ao rodar e avisa o valor certo no painel **Saída**.)
* **Erro vermelho ao rodar:** copie a mensagem do painel **Depurador/Saída** (arquivo e linha) e peça ajuda à IA com ela.
* **Teclas de teste:** `F1` invencível · `F3` vai para a entrada da arena · `F2` (na luta) chefe com 8% de vida.
* **Não rode** os scripts da pasta `tools/conversao_para_cenas` (sobrescrevem suas edições).
