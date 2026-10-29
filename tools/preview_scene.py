"""Renderiza uma PREVIA a partir do proprio scenes/areas/ruinas.tscn (nao do JSON): decodifica o TileMapLayer,
resolve instancias (paredes, props, atores) e aplica offsets/texturas das cenas. Valida o conteudo gerado.
Uso: python3 tools/preview_scene.py saida.png cx cy [w h zoom]   (cx,cy em coordenadas de celula)"""
import base64, math, os, re, struct, sys
import numpy as np
from PIL import Image

def read(p): return open(p, encoding='utf-8').read()
def parse_vec(s):
    m = re.match(r'Vector2\(([-\d.e]+), ([-\d.e]+)\)', s); return (float(m.group(1)), float(m.group(2))) if m else None
def parse_col(s):
    m = re.match(r'Color\(([-\d., e]+)\)', s); return tuple(float(x) for x in m.group(1).split(',')) if m else (1, 1, 1, 1)

def parse_scene(path):
    t = read(path)
    ext = {}
    for m in re.finditer(r'^\[ext_resource ([^\]]*)\]', t, re.M):
        a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1))); ext[a['id']] = a['path'].replace('res://', '')
    nodes = []
    for b in re.split(r'^(?=\[node )', t, flags=re.M):
        if not b.startswith('[node '): continue
        head = b.split('\n', 1)[0]
        a = dict(re.findall(r'(\w+)="([^"]*)"', head))
        inst = re.search(r'instance=ExtResource\("([^"]+)"\)', head)
        props = {}
        for line in b.split('\n')[1:]:
            mm = re.match(r'^([\w/]+) = (.*)$', line)
            if mm: props[mm.group(1)] = mm.group(2)
        nodes.append(dict(name=a['name'], type=a.get('type'), parent=a.get('parent'), inst=ext[inst.group(1)] if inst else None, props=props, ext=ext))
    return nodes

_img = {}
def img(p):
    if p not in _img: _img[p] = Image.open(p).convert('RGBA')
    return _img[p]
def tex_of(n, key='texture'):
    v = n['props'].get(key)
    if not v: return None
    return img(n['ext'][re.search(r'"([^"]+)"', v).group(1)])

def first_frame(n):
    """Primeiro quadro de um AnimatedSprite2D (resolve o .tres de SpriteFrames)."""
    sf = n['props'].get('sprite_frames')
    if not sf: return None
    path = n['ext'][re.search(r'"([^"]+)"', sf).group(1)]
    t = read(path)
    ext = {}
    for m in re.finditer(r'^\[ext_resource ([^\]]*)\]', t, re.M):
        a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1))); ext[a['id']] = a['path'].replace('res://', '')
    anim = re.search(r'&"(\w+)"', n['props'].get('animation', '&"default"')).group(1)
    # procura a animacao pedida
    for m in re.finditer(r'"frames": \[\{\n"duration": [\d.]+,\n"texture": SubResource\("([^"]+)"\)', t):
        pass
    blocks = re.findall(r'\{\n"frames": \[(.*?)\],\n"loop": \w+,\n"name": &"(\w+)"', t, re.S)
    chosen = None
    for frs, name in blocks:
        if name == anim or (chosen is None and anim == 'default'):
            chosen = frs; break
    if chosen is None: chosen = blocks[0][0]
    sid = re.search(r'SubResource\("([^"]+)"\)', chosen).group(1)
    m = re.search(rf'\[sub_resource type="AtlasTexture" id="{sid}"\]\natlas = ExtResource\("([^"]+)"\)\nregion = Rect2\(([\d., ]+)\)', t)
    x, y, w, h = [int(float(v)) for v in m.group(2).split(',')]
    return img(ext[m.group(1)]).crop((x, y, x + w, y + h))

def sprite_of_scene(path):
    """Retorna (root_props, sprite_node) de uma cena de prop/ator."""
    nodes = parse_scene(path)
    root = nodes[0]
    spr = next((n for n in nodes[1:] if n['type'] in ('Sprite2D', 'AnimatedSprite2D') and n['parent'] == '.' and n['name'] in ('Sprite',)), None)
    return nodes, root, spr

def render(scene='scenes/areas/ruinas.tscn', out='/tmp/scene.png', cx=9, cy=8, w=800, h=450, zoom=2):
    nodes = parse_scene(scene)
    items = []
    layer_pos = (0, 0)
    floor_cells = []
    for n in nodes:
        if n['name'] == 'Chao':
            layer_pos = parse_vec(n['props']['position'])
            raw = base64.b64decode(re.search(r'"([^"]+)"', n['props']['tile_map_data']).group(1))
            assert struct.unpack('<H', raw[:2])[0] == 0
            for i in range(2, len(raw), 12):
                x, y, s, ax, ay, alt = struct.unpack('<hhHHHH', raw[i:i + 12]); floor_cells.append((x, y, ax))
    atlas = img('assets/environments/chao_atlas.png')
    cells = {(x, y) for x, y, _ in floor_cells}
    for x, y, ax in floor_cells:
        px, py = (x - y) * 32 + layer_pos[0], (x + y) * 16 + layer_pos[1]
        items.append((-10, 0, atlas.crop((ax * 64, 0, ax * 64 + 64, 32)), px - 32, py - 16))
        # penhascos gerados por BordasDoChao (mesma regra do script)
        if (x + 1, y) not in cells:
            items.append((-12, 0, img(f'assets/environments/cliff_R_{abs(x * 7 + y * 3) % 3}.png'), px, py))
        if (x, y + 1) not in cells:
            items.append((-12, 0, img(f'assets/environments/cliff_L_{abs(x * 5 + y * 11) % 3}.png'), px - 32, py))
    # decals
    for n in nodes:
        if n['parent'] == 'Camadas/Marcas' and n['type'] == 'Sprite2D':
            im = tex_of(n); p = parse_vec(n['props']['position']); items.append((-9, 0, im, p[0] - im.size[0] / 2, p[1] - im.size[1] / 2))
    counts = dict(paredes=0, props=0, atores=0, itens=0)
    for n in nodes:
        if not n['inst'] or not n['parent'] or not n['parent'].startswith('Mundo'): continue
        if n['name'] in ('Hud',): continue
        pos = parse_vec(n['props'].get('position', 'Vector2(0, 0)'))
        if n['props'].get('visible') == 'false': continue
        sub_nodes, root, spr = sprite_of_scene(n['inst'])
        if root['type'] == 'Sprite2D':      # parede
            im = tex_of(n) or tex_of(root)
            off = parse_vec(n['props'].get('offset') or root['props']['offset'])
            items.append((0, pos[1], im, pos[0] + off[0], pos[1] + off[1])); counts['paredes'] += 1
        elif root['type'] == 'CharacterBody2D':
            fr = first_frame(spr); off = parse_vec(spr['props'].get('offset', 'Vector2(0, 0)'))
            items.append((0, pos[1], fr, pos[0] + off[0] - fr.size[0] / 2, pos[1] + off[1] - fr.size[1] / 2)); counts['atores'] += 1
        elif spr is not None:
            im = tex_of(spr) if spr['type'] == 'Sprite2D' else first_frame(spr)
            off = parse_vec(spr['props'].get('offset', 'Vector2(0, 0)'))
            items.append((0, pos[1], im, pos[0] + off[0], pos[1] + off[1])); counts['props'] += 1
        elif root['type'] == 'Node2D':
            counts['itens'] += 1
    items.sort(key=lambda t: (t[0], t[1]))
    sx, sy = (cx - cy) * 32.0, (cx + cy) * 16.0
    x0, y0 = sx - w / 2, sy - h / 2
    canvas = Image.new('RGBA', (w, h), (10, 14, 24, 255))
    for layer, _, im, x, y in items:
        px, py = int(round(x - x0)), int(round(y - y0))
        if px > w or py > h or px + im.size[0] < 0 or py + im.size[1] < 0: continue
        sxo, syo = max(0, -px), max(0, -py)
        ex, ey = min(im.size[0], w - px), min(im.size[1], h - py)
        canvas.alpha_composite(im.crop((sxo, syo, ex, ey)), (max(0, px), max(0, py)))
    arr = np.array(canvas).astype(np.float32); arr[..., :3] *= np.array([0.62, 0.66, 0.8], np.float32)
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGBA').convert('RGB').resize((w * zoom, h * zoom), Image.NEAREST).save(out)
    return counts, len(floor_cells)

if __name__ == '__main__':
    a = sys.argv
    z = int(a[6]) if len(a) > 6 else 1
    print(render(out=a[1], cx=float(a[2]), cy=float(a[3]), w=int(a[4]) if len(a) > 4 else 800, h=int(a[5]) if len(a) > 5 else 450, zoom=z))
