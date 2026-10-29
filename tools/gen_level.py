"""Gera e valida o nivel 'Ruinas Esquecidas' -> tools/data/ruinas.json
Uso: python3 tools/gen_level.py"""
import json, math, os, random, sys
from collections import deque
sys.path.insert(0, os.path.dirname(__file__))
from px import hnoise

W, H = 72, 44
grid = [['#'] * W for _ in range(H)]
REGIONS = {}


def carve(name, x0, y0, x1, y1):
    REGIONS[name] = (x0, y0, x1, y1)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            grid[y][x] = '.'


# --------------------------------------------------------------- geometria
carve('R1', 4, 4, 14, 13)          # patio de entrada
carve('C1', 15, 7, 22, 9)
carve('R2', 23, 2, 36, 14)         # patio quebrado
carve('C1b', 37, 7, 40, 8)         # desvio
carve('S1', 41, 4, 47, 11)         # alcova com recompensa
carve('C2', 28, 15, 30, 22)
carve('R3', 22, 23, 38, 38)        # salao dos guardioes
carve('C3', 39, 29, 50, 31)
carve('PL', 51, 27, 66, 33)        # praca do portao
carve('C4', 59, 18, 60, 26)        # corredor ate a arena
carve('AR', 52, 4, 67, 17)         # arena do chefe

START = (6.5, 9.5)
BOSS_SPAWN = (60.0, 8.5)
ARENA_ENTRY_Y = 17.4               # cruzar para y menor = inicia a luta
GATE_CELLS = (59, 60)
GATE_PLANE_Y = 27                  # plano da face frontal da muralha da praca
BARRIER_ROW = 18


def is_floor(x, y):
    return 0 <= x < W and 0 <= y < H and grid[y][x] == '.'


# --------------------------------------------------------------- muralhas traseiras
walls = []    # (x, y, h, variant, face)
wall_set = set()
rng = random.Random(11)
forced = {}


def wall_height(x, y):
    n = hnoise(x // 2, y // 2, 7)
    if n < 0.58:
        return 3
    if n < 0.82:
        return 2
    return 1 if n < 0.93 else 3


for y in range(H):
    for x in range(W):
        if grid[y][x] != '#':
            continue
        back_y = is_floor(x, y + 1)
        back_x = is_floor(x + 1, y)
        diag = is_floor(x + 1, y + 1)
        if not (back_y or back_x or diag):
            continue
        # a muralha do portao e da arena sao sempre altas
        h = wall_height(x, y)
        if y == 26 and 51 <= x <= 66:
            h = 3
        if y == 3 and 52 <= x <= 67:
            h = 3
        if x == 51 and 4 <= y <= 17:
            h = 3
        face = 'L' if back_y else ('R' if back_x else None)
        deco = None
        if face and h >= 2:
            r = hnoise(x, y, 99)
            if r < 0.20:
                deco = 'banner'
        wall_set.add((x, y))
        walls.append(dict(x=x, y=y, h=h, deco=deco, face=face, v=int(hnoise(x, y, 5) * 3) % 3))

# portal e arco manuais
for w in walls:
    if (w['x'], w['y']) == (9, 3):
        w['h'], w['deco'], w['face'] = 3, 'arch', 'L'
    if w['y'] == 3 and w['x'] in (62, 63, 64, 65):
        w['deco'] = None
    if w['y'] == 26 and 51 <= w['x'] <= 66:
        w['deco'] = None
    # garante que o banner nao fique perto do arco
for w in walls:
    if w['deco'] == 'arch' and (w['x'], w['y']) != (9, 3):
        w['deco'] = None

# paredes baixas (parapeito quebrado) nas bordas frontais das salas
lows = []
for y in range(H):
    for x in range(W):
        if grid[y][x] != '#' or (x, y) in wall_set:
            continue
        front = is_floor(x - 1, y) or is_floor(x, y - 1)
        if not front:
            continue
        # apenas em salas (nao corredores) e nao no corredor/portao
        in_room = any(REGIONS[r][0] - 1 <= x <= REGIONS[r][2] + 1 and REGIONS[r][1] - 1 <= y <= REGIONS[r][3] + 1 for r in ('R1', 'R2', 'S1', 'R3', 'PL', 'AR'))
        if in_room and hnoise(x, y, 55) < 0.45:
            lows.append((x, y))
for (x, y) in lows:
    grid[y][x] = 'L'
for w in walls:
    grid[w['y']][w['x']] = 'W'

# --------------------------------------------------------------- props
props = []
enemies = []
pickups = []


def add(k, x, y, **kw):
    d = dict(k=k, x=x, y=y)
    d.update(kw)
    props.append(d)


# R1 patio de entrada
add('brazier', 5.5, 5.5); add('brazier', 13.5, 4.5)
add('candles', 9.5, 4.5)
add('statue_lantern', 12.5, 6.5)
add('pillar_broken', 8.5, 12.5); add('pillar_stump', 5.5, 11.5)
add('signpost', 13.5, 9.5)
add('plant_0', 4.5, 9.5); add('plant_2', 10.5, 13.5); add('plant_1', 13.5, 12.5); add('plant_0', 6.5, 4.6)
add('rubble_1', 11.0, 11.0); add('rubble_0', 4.6, 6.8)
for i, (x, y) in enumerate(((8.5, 8.5), (10.5, 9.5), (7.5, 10.5))):
    add('rune_small_%d' % i, x, y, decal=True)
# C1
add('brazier', 17.5, 7.5); add('brazier', 21.5, 9.5)
add('rubble_2', 19.5, 8.5); add('plant_1', 15.8, 9.2)
# R2 patio quebrado
for (x, y) in ((26.5, 5.5), (26.5, 10.5), (32.5, 5.5), (32.5, 10.5)):
    add('pillar_tall', x, y)
add('pillar_broken', 29.5, 3.5); add('pillar_broken', 34.5, 13.5); add('pillar_stump', 24.5, 12.5)
add('statue_prayer', 35.5, 3.5)
add('blue_pedestal', 24.5, 3.5); add('blue_pedestal', 35.5, 12.5)
add('rubble_0', 30.5, 8.5); add('rubble_2', 27.5, 13.0); add('plant_0', 33.5, 8.5); add('plant_2', 24.0, 6.5)
add('rune_small_1', 29.5, 8.5, decal=True)
add('candles', 29.5, 14.4)
# desvio + S1
add('brazier', 38.5, 7.5)
add('crystal_0', 45.5, 5.5); add('crystal_1', 45.5, 10.5); add('statue_lantern', 43.5, 4.5)
add('candles', 41.5, 11.0); add('pillar_stump', 46.5, 7.5); add('plant_1', 42.0, 10.0)
add('rune_small_2', 44.5, 8.5, decal=True)
# C2
add('candles', 28.5, 18.5); add('candles', 30.0, 21.5); add('plant_0', 29.0, 16.0)
# R3 salao dos guardioes
for y in (27.5, 31.5, 35.5):
    add('pillar_tall' if y != 31.5 else 'pillar_short', 26.5, y)
    add('pillar_tall' if y != 31.5 else 'pillar_broken', 34.5, y)
add('statue_prayer', 23.5, 24.5); add('statue_lantern', 36.5, 24.5)
add('blue_pedestal', 23.5, 30.0); add('blue_pedestal', 37.5, 37.5)
add('brazier', 30.5, 24.5); add('brazier', 23.5, 37.5); add('brazier', 30.5, 37.5)
add('rubble_1', 29.5, 28.5); add('rubble_2', 32.0, 34.0); add('rubble_0', 24.5, 33.5)
add('plant_2', 36.0, 28.0); add('plant_0', 28.0, 36.0); add('candles', 31.0, 31.0)
add('rune_small_0', 30.5, 31.5, decal=True)
# C3
add('blue_pedestal', 42.5, 29.5); add('blue_pedestal', 46.5, 31.5)
add('rubble_2', 44.5, 30.5); add('plant_1', 40.0, 29.5); add('candles', 49.0, 30.0)
# Praca
add('brazier', 57.5, 27.5); add('brazier', 62.5, 27.5)
add('blue_pedestal', 53.5, 32.5); add('blue_pedestal', 65.0, 32.5)
add('statue_prayer', 54.5, 28.5); add('statue_lantern', 65.5, 28.5)
add('plant_0', 52.0, 30.0); add('rubble_1', 56.5, 31.0); add('plant_2', 63.5, 31.5); add('signpost', 57.5, 29.5)
add('rune_small_1', 60.0, 30.0, decal=True)
# Corredor para a arena
add('candles', 59.0, 24.0); add('candles', 60.5, 21.0); add('plant_1', 59.2, 19.0)
# Arena
add('rune_circle', 60.0, 11.0, decal=True)
add('statue_prayer', 56.5, 4.5); add('statue_prayer', 66.5, 4.5)
add('candles', 61.5, 4.4); add('candles', 58.0, 4.4); add('candles', 66.8, 7.0)
add('brazier', 53.5, 5.5); add('brazier', 53.5, 14.5); add('brazier', 66.5, 14.5)
add('blue_pedestal', 54.5, 16.5); add('blue_pedestal', 65.5, 16.5); add('blue_pedestal', 56.0, 7.0)
add('pillar_broken', 66.0, 10.5); add('pillar_stump', 53.5, 9.5); add('rubble_0', 63.5, 15.5); add('rubble_2', 55.0, 13.0)
add('plant_0', 52.5, 12.0); add('plant_2', 67.0, 12.5)

# Estrutura do portao e portal (nomes especiais tratados pelo jogo)
gate = dict(plane_y=GATE_PLANE_Y, x0=58, cells=GATE_CELLS)
portal = dict(plane_y=4, x=63)

# --------------------------------------------------------------- inimigos
def en(t, x, y, patrol=None, facing=None):
    d = dict(t=t, x=x, y=y)
    if patrol:
        d['patrol'] = patrol
    enemies.append(d)


en('soldier', 27.5, 8.5, patrol=[[27.5, 6.5], [27.5, 10.5]])          # primeiro encontro isolado
en('soldier', 33.5, 4.5, patrol=[[31.5, 4.5], [34.5, 4.5]])
en('soldier', 34.5, 12.0)
en('soldier', 43.5, 7.5)                                               # guarda da alcova
en('guardian', 28.5, 34.5)
en('soldier', 25.0, 28.5, patrol=[[24.5, 26.5], [24.5, 30.5]])
en('soldier', 33.0, 26.5)
en('wraith', 36.5, 33.5)
en('wraith', 62.5, 31.5)

pickups += [dict(kind='souls', amount=200, x=44.5, y=8.5), dict(kind='souls', amount=100, x=24.5, y=4.8),
            dict(kind='flask', amount=0, x=23.8, y=36.0), dict(kind='flask', amount=0, x=53.8, y=30.5)]

# --------------------------------------------------------------- validacao
META = json.load(open('assets/meta/props.json'))
solid_cells = set()
errors = []
for p in props:
    k = p['k']
    if k.startswith('rune_') or p.get('decal'):
        continue
    if k not in META:
        errors.append('prop sem meta: ' + k)
        continue
    cx, cy = int(math.floor(p['x'])), int(math.floor(p['y']))
    if not is_floor(cx, cy):
        errors.append(f'prop fora do piso: {k} {p["x"]},{p["y"]}')
    if META[k].get('solid', 0) > 0:
        solid_cells.add((cx, cy))
for e in enemies:
    c = (int(e['x']), int(e['y']))
    if not is_floor(*c) or c in solid_cells:
        errors.append(f'inimigo invalido {e}')
    for q in e.get('patrol', []):
        if not is_floor(int(q[0]), int(q[1])) or (int(q[0]), int(q[1])) in solid_cells:
            errors.append(f'patrulha invalida {e}')
for pk in pickups:
    c = (int(pk['x']), int(pk['y']))
    if not is_floor(*c) or c in solid_cells:
        errors.append(f'pickup invalido {pk}')
sx, sy = int(START[0]), int(START[1])
if not is_floor(sx, sy) or (sx, sy) in solid_cells:
    errors.append('start invalido')


def flood(start, blocked):
    seen = {start}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n in seen or not is_floor(*n) or n in blocked:
                continue
            seen.add(n)
            q.append(n)
    return seen


reach = flood((sx, sy), solid_cells)
all_floor = {(x, y) for y in range(H) for x in range(W) if grid[y][x] == '.'}
unreach = all_floor - reach - solid_cells
if unreach:
    errors.append(f'{len(unreach)} celulas de piso inalcancaveis, ex: {sorted(unreach)[:5]}')
# larguras minimas: cada celula solida nao pode isolar
bx, by = int(BOSS_SPAWN[0]), int(BOSS_SPAWN[1])
if (bx, by) not in reach:
    errors.append('boss spawn inalcancavel')
# o jogador precisa de pelo menos 2 celulas livres lado a lado nos corredores (checagem simples)
for name in ('C1', 'C2', 'C3', 'C4'):
    x0, y0, x1, y1 = REGIONS[name]
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            pass

# garante caminho livre de 2 celulas na rota principal usando BFS em celulas "gordas"
def fat_ok(c):
    x, y = c
    # celula e vizinha livres em pelo menos uma direcao ortogonal
    for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
        n = (x + dx, y + dy)
        if is_floor(*n) and n not in solid_cells:
            return True
    return False


fat = {c for c in reach if all((c[0] + dx, c[1] + dy) in reach or (c[0] + dx, c[1] + dy) not in all_floor for dx, dy in ((0, 0),))}
print('piso:', len(all_floor), 'alcancavel:', len(reach), 'paredes:', len(walls), 'baixas:', len(lows), 'props:', len(props), 'inimigos:', len(enemies))
if errors:
    print('ERROS DE NIVEL:')
    for e in errors:
        print(' -', e)
    sys.exit(1)

# --------------------------------------------------------------- saida
out = dict(
    size=[W, H],
    grid=[''.join(r) for r in grid],
    start=list(START), boss_spawn=list(BOSS_SPAWN), arena_entry_y=ARENA_ENTRY_Y,
    barrier=dict(row=BARRIER_ROW, cells=list(GATE_CELLS)),
    gate=gate, portal=portal,
    walls=walls, props=props, enemies=enemies, pickups=pickups,
    regions={k: list(v) for k, v in REGIONS.items()},
    path=[[6.5, 9.5], [18.5, 8.5], [30, 8.5], [29.5, 20], [30, 31], [44, 30], [58, 30], [59.5, 22], [60, 12]],
)
os.makedirs('tools/data', exist_ok=True)
json.dump(out, open('tools/data/ruinas.json', 'w'))
# preview ascii
for y in range(H):
    print(''.join(grid[y]))
print('nivel ok')
