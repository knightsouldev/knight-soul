"""Renderiza uma previa do nivel replicando a matematica de scripts/world/level.gd
(piso, penhascos, paredes, props com ancora, y-sort, luzes aditivas aproximadas).
Uso: python3 tools/preview_level.py out.png cx cy [largura altura] [zoom]"""
import json, math, sys
import numpy as np
from PIL import Image

lvl = json.load(open('tools/data/ruinas.json'))
props = json.load(open('tools/data/props.json'))
W, H = lvl['size']
rows = lvl['grid']
cache = {}
def img(p):
    p = p.replace('res://', '')
    if p not in cache:
        cache[p] = Image.open(p).convert('RGBA')
    return cache[p]
def c2s(cx, cy):
    return ((cx - cy) * 32.0, (cx + cy) * 16.0)
def isf(x, y):
    return 0 <= x < W and 0 <= y < H and rows[y][x] == '.'
def fv(x, y):
    h = abs((x * 73856093) ^ (y * 19349663)) % 100
    for t, v in ((26, 0), (44, 2), (58, 6), (70, 1), (80, 7), (89, 4), (94, 5), (97, 3)):
        if h < t: return v
    return 6

items = []   # (layer, sorty, image, x, y)
lights = []
for y in range(H):
    for x in range(W):
        if not isf(x, y): continue
        sx, sy = c2s(x + .5, y + .5)
        items.append((-10, 0, img(f'assets/environments/floor_{fv(x,y):02d}.png'), sx - 32, sy - 16))
        if not isf(x + 1, y):
            items.append((-12, 0, img(f'assets/environments/cliff_R_{abs(x*7+y*3)%3}.png'), sx, sy))
        if not isf(x, y + 1):
            items.append((-12, 0, img(f'assets/environments/cliff_L_{abs(x*5+y*11)%3}.png'), sx - 32, sy))
for p in lvl['props']:
    if p['k'].startswith('rune_'):
        im = img(f"assets/environments/{p['k']}.png")
        sx, sy = c2s(p['x'], p['y'])
        items.append((-9, 0, im, sx - im.size[0] / 2, sy - im.size[1] / 2))

WP = {1: 28, 2: 56, 3: 84}
for w in lvl['walls']:
    sx, sy = c2s(w['x'] + .5, w['y'] + .5)
    ny = sy + 14
    h = w['h']
    if w['deco'] and w['face']:
        f = f"assets/environments/wall_h{h}_{w['deco']}_{w['face']}.png"
    else:
        f = f"assets/environments/wall_h{h}_v{w['v']}.png"
    items.append((0, ny, img(f), sx - 32, ny - (WP[h] + 16) - 14))
for y in range(H):
    for x in range(W):
        if rows[y][x] == 'L':
            sx, sy = c2s(x + .5, y + .5)
            ny = sy + 14
            items.append((0, ny, img(f'assets/environments/wall_low_v{(x+y)%2}.png'), sx - 32, ny - 30 - 14))

def prop(k, cx, cy, bias=0, frame=0):
    m = props[k]
    sx, sy = c2s(cx, cy)
    ny = sy + bias
    im = img(m['file'])
    fw = m['fw']
    fr = im.crop((frame * fw, 0, frame * fw + fw, im.size[1]))
    items.append((0, ny, fr, sx - m['ax'], ny - m['ay'] - bias))
    if 'light' in m and k not in ('candles',):
        l = m['light']
        lights.append((sx + l['dx'], ny - bias + l['dy'], l['color'], l['energy'], l['scale'] * .55))
for p in lvl['props']:
    if p['k'].startswith('rune_') or p['k'] not in props: continue
    prop(p['k'], p['x'], p['y'], frame=hash((p['x'], p['y'])) % props[p['k']]['frames'])
g = lvl['gate']
for i in range(4): prop(f'gate_{i}', g['x0'] + i + .5, g['plane_y'], 10)
prop('gate_veil', g['x0'] + 2.0, g['plane_y'], 10)
pt = lvl['portal']
prop('portal_plane', pt['x'] + 1.0, pt['plane_y'], 10)

# jogador e chefe para referencia de escala
meta = json.load(open('tools/data/actors.json'))
def actor(name, anim, cx, cy, frame=0, view='front', flip=False):
    m = meta[name]
    im = img(f"assets/{m['folder']}/{name}_{anim}_{view}.png")
    fw, fh = m['fw'], m['fh']
    fr = im.crop((frame * fw, 0, frame * fw + fw, fh))
    if flip: fr = fr.transpose(Image.FLIP_LEFT_RIGHT)
    sx, sy = c2s(cx, cy)
    items.append((0, sy, fr, sx - fw / 2, sy - (fh - m['foot'])))
st = lvl['start']
actor('player', 'idle', st[0], st[1])
actor('boss', 'idle', lvl['boss_spawn'][0], lvl['boss_spawn'][1])
for e in lvl['enemies']:
    nm = e['t']
    actor(nm, 'idle', e['x'], e['y'], flip=True)
actor('player', 'attack1', 61.0, 12.5, frame=3)

items.sort(key=lambda t: (t[0], t[1]))

def render(out, ccx, ccy, w=800, h=450, zoom=2):
    cxs, cys = c2s(ccx, ccy)
    x0, y0 = cxs - w / 2, cys - h / 2
    canvas = Image.new('RGBA', (w, h), (10, 14, 24, 255))
    for layer, sy, im, x, y in items:
        px, py = int(round(x - x0)), int(round(y - y0))
        if px > w or py > h or px + im.size[0] < 0 or py + im.size[1] < 0: continue
        canvas.alpha_composite(im, (px, py)) if (0 <= px and 0 <= py and px + im.size[0] <= w and py + im.size[1] <= h) else _clip(canvas, im, px, py)
    arr = np.array(canvas).astype(np.float32)
    amb = np.array([0.40, 0.43, 0.56], np.float32)
    light = np.zeros((h, w, 3), np.float32) + amb
    yy, xx = np.mgrid[0:h, 0:w]
    for lx, ly, col, en, sc in lights:
        dx = (xx - (lx - x0)) / (128 * sc)
        dy = (yy - (ly - y0)) / (128 * sc * 0.6)
        d = np.hypot(dx, dy)
        a = np.clip(1 - d, 0, 1)
        a = np.where(a > 0.65, 1.0, a / 0.65 * 0.55 + (0.45 if False else 0)) * (a > 0)
        a = (np.clip(1 - d, 0, 1) ** 1.6)
        for i in range(3):
            light[..., i] += a * col[i] * en
    arr[..., :3] = np.clip(arr[..., :3] * light, 0, 255)
    im = Image.fromarray(arr.astype(np.uint8), 'RGBA').convert('RGB')
    im = im.resize((w * zoom, h * zoom), Image.NEAREST)
    im.save(out)

def _clip(canvas, im, px, py):
    w, h = canvas.size
    sx0, sy0 = max(0, -px), max(0, -py)
    ex, ey = min(im.size[0], w - px), min(im.size[1], h - py)
    if ex <= sx0 or ey <= sy0: return
    canvas.alpha_composite(im.crop((sx0, sy0, ex, ey)), (max(0, px), max(0, py)))

if __name__ == '__main__':
    out = sys.argv[1]
    cx, cy = float(sys.argv[2]), float(sys.argv[3])
    w = int(sys.argv[4]) if len(sys.argv) > 4 else 800
    h = int(sys.argv[5]) if len(sys.argv) > 5 else 450
    z = int(sys.argv[6]) if len(sys.argv) > 6 else 1
    render(out, cx, cy, w, h, z)
