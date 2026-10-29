"""Etapa 2c: gera scenes/areas/ruinas.tscn a partir de tools/data/ruinas.json (conversao unica)."""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(__file__))
from tscn import *

L = json.load(open('tools/data/ruinas.json'))
PROPS = json.load(open('tools/data/props.json'))
S = lambda p: f'res://{p}'
W, H = L['size']
rows = L['grid']


def c2s(cx, cy):
    return ((cx - cy) * 32.0, (cx + cy) * 16.0)


def isf(x, y):
    return 0 <= x < W and 0 <= y < H and rows[y][x] == '.'


def fv(x, y):
    h = abs((x * 73856093) ^ (y * 19349663)) % 100
    for t, v in ((26, 0), (44, 2), (58, 6), (70, 1), (80, 7), (89, 4), (94, 5), (97, 3)):
        if h < t:
            return v
    return 6


REG_NAMES = dict(R1='PatioInicial', C1='CorredorInicial', R2='PatioQuebrado', C1b='Passagem', S1='AlcovaRecompensa', C2='CorredorSul',
                 R3='SalaoGuardioes', C3='CorredorLeste', PL='PracaPortao', C4='CorredorArena', AR='ArenaChefe')
ORDER = ['R1', 'C1', 'R2', 'C1b', 'S1', 'C2', 'R3', 'C3', 'PL', 'C4', 'AR']


def region_of(x, y):
    for k in ORDER:
        x0, y0, x1, y1 = L['regions'][k]
        if x0 - 1 <= x <= x1 + 1 and y0 - 1 <= y <= y1 + 1:
            return REG_NAMES[k]
    return 'Outros'


PT = dict(pillar_tall='PilarAlto', pillar_short='PilarBaixo', pillar_stump='PilarCoto', pillar_broken='PilarQuebrado',
          statue_lantern='EstatuaLanterna', statue_prayer='EstatuaOracao', brazier='Braseiro', blue_pedestal='PedestalAzul',
          candles='Velas', crystal_0='CristalA', crystal_1='CristalB', plant_0='ArbustoA', plant_1='ArbustoB', plant_2='Hera',
          rubble_0='EntulhoA', rubble_1='EntulhoB', rubble_2='EntulhoC', signpost='Placa')

d = Doc('scene')
level_script = d.ext_res('Script', S('scripts/world/level.gd'))
d.node('RuinasEsquecidas', 'Node2D', props=[('script', level_script)])

# ---------------------------------------------------------------- ambiente e fundo
d.node('Ambiente', 'CanvasModulate', '.', props=[('color', col(0.40, 0.43, 0.56, 1))])
grad = d.sub('Gradient', [('offsets', 'PackedFloat32Array(0, 1)'), ('colors', 'PackedColorArray(0.02, 0.03, 0.06, 1, 0.07, 0.1, 0.17, 1)')])
gtex = d.sub('GradientTexture2D', [('gradient', grad), ('width', '8'), ('height', '256'), ('fill_from', v2(0, 0)), ('fill_to', v2(0, 1))])
d.node('FundoCeu', 'CanvasLayer', '.', props=[('layer', '-120')])
d.node('Degrade', 'TextureRect', 'FundoCeu', props=[('anchors_preset', '15'), ('anchor_right', '1.0'), ('anchor_bottom', '1.0'),
                                                    ('grow_horizontal', '2'), ('grow_vertical', '2'), ('texture', gtex), ('expand_mode', '1'), ('stretch_mode', '0')])
d.node('FundoDistante', 'ParallaxBackground', '.', props=[('layer', '-100')])
d.node('Camada', 'ParallaxLayer', 'FundoDistante', props=[('motion_scale', v2(0.22, 0.22)), ('motion_mirroring', v2(1024, 0))])
far = d.ext_res('Texture2D', S('assets/environments/far_ruins.png'))
d.node('RuinasAoFundo', 'Sprite2D', 'FundoDistante/Camada', props=[('modulate', col(0.55, 0.62, 0.85, 0.95)), ('texture', far), ('centered', 'false'), ('offset', v2(0, -40))])

# ---------------------------------------------------------------- camadas do chao
d.node('Camadas', 'Node2D', '.')
mist_script = d.ext_res('Script', S('scripts/world/mist_drift.gd'))
d.node('Neblina', 'Node2D', 'Camadas', props=[('z_index', '-11'), ('script', mist_script)])
fog = d.ext_res('Texture2D', S('assets/environments/fog.png'))
rnd = random.Random(5)
n = 0
for _ in range(46):
    x, y = rnd.randint(0, W - 1), rnd.randint(0, H - 1)
    near = any(isf(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1))
    sx, sy = c2s(x + .5, y + .5)
    px, py = sx + rnd.uniform(-40, 40), sy + rnd.uniform(50, 110)
    sc_x, sc_y, a = rnd.uniform(2.0, 3.6), rnd.uniform(1.0, 1.7), rnd.uniform(0.10, 0.2)
    if not near:
        continue
    n += 1
    d.node(f'Nevoa_{n:02d}', 'Sprite2D', 'Camadas/Neblina', props=[('modulate', col(0.6, 0.7, 0.95, a)), ('position', v2(px, py)),
                                                                  ('scale', v2(sc_x, sc_y)), ('texture', fog)])
tileset = d.ext_res('TileSet', S('resources/tilesets/chao.tres'))
cells = [(x, y, 0, fv(x, y), 0) for y in range(H) for x in range(W) if rows[y][x] == '.']
d.node('Chao', 'TileMapLayer', 'Camadas', props=[('z_index', '-10'), ('position', v2(0, 16)), ('tile_map_data', tile_data(cells)),
                                                 ('tile_set', tileset), ('unique_name_in_owner', 'true')])
d.node('Marcas', 'Node2D', 'Camadas', props=[('z_index', '-9')])
for p in L['props']:
    if not p['k'].startswith('rune_'):
        continue
    tex = d.ext_res('Texture2D', S(f"assets/environments/{p['k']}.png"))
    sx, sy = c2s(p['x'], p['y'])
    nm = 'CirculoRunico' if p['k'] == 'rune_circle' else f"Runa_{p['k'][-1]}_{int(p['x'])}_{int(p['y'])}"
    d.node(nm, 'Sprite2D', 'Camadas/Marcas', props=[('modulate', col(1, 1, 1, 0.95)), ('position', v2(sx, sy)), ('texture', tex)])
    if p['k'] == 'rune_circle':
        ltex = d.ext_res('Texture2D', S('assets/effects/light.png'))
        d.node('LuzCirculo', 'PointLight2D', 'Camadas/Marcas', props=[('position', v2(sx, sy)), ('scale', v2(1, 0.6)), ('color', col(1, 0.75, 0.35)),
                                                                     ('energy', '0.35'), ('texture', ltex), ('texture_scale', '1.7')])

# ---------------------------------------------------------------- bordas automaticas
bscript = d.ext_res('Script', S('scripts/world/bordas_do_chao.gd'))
d.node('BordasDoChao', 'Node2D', '.', props=[('script', bscript), ('floor_layer', nodepath('../Camadas/Chao')), ('unique_name_in_owner', 'true')])

# ---------------------------------------------------------------- mundo (y-sort)
d.node('Mundo', 'Node2D', '.', groups=['fx_layer'], props=[('y_sort_enabled', 'true')])
for grp in ('Paredes', 'Decoracao'):
    d.node(grp, 'Node2D', 'Mundo', props=[('y_sort_enabled', 'true')])
    for k in ORDER:
        d.node(REG_NAMES[k], 'Node2D', f'Mundo/{grp}', props=[('y_sort_enabled', 'true')])
    d.node('Outros', 'Node2D', f'Mundo/{grp}', props=[('y_sort_enabled', 'true')])
for grp in ('Portao', 'Itens', 'Inimigos'):
    d.node(grp, 'Node2D', 'Mundo', props=[('y_sort_enabled', 'true')])

# paredes
wall_scene = d.ext_res('PackedScene', S('scenes/world/pieces/parede.tscn'))
WP = {1: 28, 2: 56, 3: 84}
for w in L['walls']:
    h = w['h']
    if w['deco'] and w['face']:
        f = f"assets/environments/wall_h{h}_{w['deco']}_{w['face']}.png"
    else:
        f = f"assets/environments/wall_h{h}_v{w['v']}.png"
    sx, sy = c2s(w['x'] + .5, w['y'] + .5)
    d.node(f"Parede_{w['x']}_{w['y']}", None, f"Mundo/Paredes/{region_of(w['x'], w['y'])}", instance=wall_scene,
           props=[('position', v2(sx, sy + 14)), ('texture', d.ext_res('Texture2D', S(f))), ('offset', v2(-32, -(WP[h] + 16) - 14))])
for y in range(H):
    for x in range(W):
        if rows[y][x] == 'L':
            sx, sy = c2s(x + .5, y + .5)
            f = f'assets/environments/wall_low_v{(x + y) % 2}.png'
            d.node(f'ParedeBaixa_{x}_{y}', None, f'Mundo/Paredes/{region_of(x, y)}', instance=wall_scene,
                   props=[('position', v2(sx, sy + 14)), ('texture', d.ext_res('Texture2D', S(f))), ('offset', v2(-32, -(14 + 16) - 14)),
                          ('fades_when_hiding_player', 'false')])

# decoracao
count = {}
for p in L['props']:
    k = p['k']
    if k.startswith('rune_') or k not in PT:
        continue
    count[k] = count.get(k, 0) + 1
    sx, sy = c2s(p['x'], p['y'])
    reg = region_of(int(p['x']), int(p['y']))
    d.node(f'{PT[k]}_{count[k]}', None, f'Mundo/Decoracao/{reg}', instance=d.ext_res('PackedScene', S(f'scenes/world/props/{k}.tscn')),
           props=[('position', v2(sx, sy))])

# portao, veu, portal
g = L['gate']
for i in range(4):
    sx, sy = c2s(g['x0'] + i + .5, g['plane_y'])
    d.node(f'Portao_Parte{i + 1}', None, 'Mundo/Portao', instance=d.ext_res('PackedScene', S(f'scenes/world/props/gate_{i}.tscn')),
           props=[('position', v2(sx, sy + 10))])
sx, sy = c2s(g['x0'] + 2.0, g['plane_y'])
d.node('Portao_Veu', None, 'Mundo/Portao', instance=d.ext_res('PackedScene', S('scenes/world/props/gate_veil.tscn')), props=[('position', v2(sx, sy + 10))])
pt = L['portal']
sx, sy = c2s(pt['x'] + 1.0, pt['plane_y'])
d.node('PortalRoxo', None, 'Mundo/Portao', instance=d.ext_res('PackedScene', S('scenes/world/props/portal_plane.tscn')), props=[('position', v2(sx, sy + 10))])

# itens
pick = d.ext_res('PackedScene', S('scenes/effects/pickup.tscn'))
pc = {'souls': 0, 'flask': 0}
for pk in L['pickups']:
    pc[pk['kind']] += 1
    sx, sy = c2s(pk['x'], pk['y'])
    nm = f"EssenciaEsquecida_{pc['souls']}" if pk['kind'] == 'souls' else f"FragmentoDeFrasco_{pc['flask']}"
    pr = [('position', v2(sx, sy)), ('kind', q(pk['kind']))]
    if pk['kind'] == 'souls':
        pr.append(('amount', str(pk['amount'])))
    d.node(nm, None, 'Mundo/Itens', instance=pick, props=pr)

# marcadores
d.node('Marcadores', 'Node2D', '.')
d.node('Patrulhas', 'Node2D', 'Marcadores')
d.node('Bussola', 'Node2D', 'Marcadores', props=[('unique_name_in_owner', 'true')])
for i, p in enumerate(L['path']):
    sx, sy = c2s(*p)
    d.node(f'Ponto{i + 1:02d}', 'Marker2D', 'Marcadores/Bussola', props=[('position', v2(sx, sy))])
sx, sy = c2s(*L['start'])
d.node('PontoInicial', 'Marker2D', 'Marcadores', props=[('position', v2(sx, sy))])
sx, sy = c2s(59.8, 21.5)
d.node('EntradaArena', 'Marker2D', 'Marcadores', props=[('position', v2(sx, sy)), ('unique_name_in_owner', 'true')])

# inimigos
escn = {t: d.ext_res('PackedScene', S(f'scenes/enemies/{t}.tscn')) for t in ('soldier', 'guardian', 'wraith')}
NAMES = dict(soldier='Soldado', guardian='Guardiao', wraith='Espectro')
ec = {}
for e in L['enemies']:
    t = e['t']
    ec[t] = ec.get(t, 0) + 1
    nm = f'{NAMES[t]}_{ec[t]}'
    sx, sy = c2s(e['x'], e['y'])
    pr = [('position', v2(sx, sy))]
    if e.get('patrol'):
        paths = []
        for j, pp in enumerate(e['patrol']):
            mx, my = c2s(*pp)
            mname = f'{nm}_{chr(65 + j)}'
            d.node(mname, 'Marker2D', 'Marcadores/Patrulhas', props=[('position', v2(mx, my))])
            paths.append(nodepath(f'../../../Marcadores/Patrulhas/{mname}'))
        pr.append(('patrol_points', 'Array[NodePath]([' + ', '.join(paths) + '])'))
    d.node(nm, None, 'Mundo/Inimigos', instance=escn[t], props=pr)

# chefe e jogador
sx, sy = c2s(*L['boss_spawn'])
d.node('Chefe', None, 'Mundo', instance=d.ext_res('PackedScene', S('scenes/bosses/sentinela.tscn')), props=[('position', v2(sx, sy)), ('unique_name_in_owner', 'true')])
sx, sy = c2s(*L['start'])
d.node('Jogador', None, 'Mundo', instance=d.ext_res('PackedScene', S('scenes/player/player.tscn')), props=[('position', v2(sx, sy)), ('unique_name_in_owner', 'true')])

# arena: gatilho e barreira de nevoa
d.node('Arena', 'Node2D', '.')
d.node('GatilhoArena', 'Area2D', 'Arena', props=[('collision_layer', '0'), ('collision_mask', '2'), ('unique_name_in_owner', 'true')])
strip = [c2s(57.5, 16.8), c2s(62.5, 16.8), c2s(62.5, 17.6), c2s(57.5, 17.6)]
d.node('Forma', 'CollisionPolygon2D', 'Arena/GatilhoArena', props=[('polygon', pva2(strip))])
bar = L['barrier']
x0, x1, row = bar['cells'][0], bar['cells'][1] + 1, bar['row']
d.node('BarreiraNevoa', 'StaticBody2D', 'Arena', props=[('collision_mask', '0')])
d.node('BarreiraColisao', 'CollisionPolygon2D', 'Arena/BarreiraNevoa', props=[
    ('polygon', pva2([c2s(x0, row), c2s(x1, row), c2s(x1, row + 1), c2s(x0, row + 1)])), ('disabled', 'true'), ('unique_name_in_owner', 'true')])
sx, sy = c2s((x0 + x1) * 0.5, row + 1.0)
d.node('BarreiraVisual', None, 'Arena', instance=d.ext_res('PackedScene', S('scenes/world/props/gate_veil.tscn')),
       props=[('visible', 'false'), ('position', v2(sx, sy + 10)), ('unique_name_in_owner', 'true')])

# interface
for nm, path in (('Hud', 'scenes/ui/hud.tscn'), ('MenuPausa', 'scenes/ui/pause_menu.tscn'), ('TelaFinal', 'scenes/ui/end_screen.tscn')):
    d.node(nm, None, '.', instance=d.ext_res('PackedScene', S(path)), props=[('unique_name_in_owner', 'true')])

d.save('scenes/areas/ruinas.tscn')
write_file('resources/data/ruinas_chao.json', json.dumps(['' .join('.' if c == '.' else '#' for c in r) for r in rows]))
print('ruinas.tscn: nos =', len(d.nodes), ' ext =', len(d.ext))
