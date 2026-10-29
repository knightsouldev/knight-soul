"""Gera tiles, paredes, penhascos, props e efeitos de ambiente do Knight Souls.
Uso: python3 tools/gen_env.py  (rodar a partir da raiz do projeto)"""
import json, math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from px import *

OUT_ENV = 'assets/environments'
OUT_PROP = 'assets/props'
OUT_FX = 'assets/effects'
META = {}   # props meta -> tools/data/props.json
for d in (OUT_ENV, OUT_PROP, OUT_FX, 'tools/data'):
    os.makedirs(d, exist_ok=True)

# ---------------------------------------------------------------- piso
def stone_color(h, base=None, lit=1.0):
    base = base or P['stone_m']
    k = (0.78 + 0.44 * h) * lit
    return shade(base, k)


def floor_tile(seed, moss=0.12, crack=0.0, tone=1.0, warm=0.0):
    img = Image.new('RGBA', (64, 32), (0, 0, 0, 0))
    px = img.load()
    N = 4
    for y in range(32):
        for x in range(64):
            uv = iso_uv(x, y)
            if uv is None:
                continue
            u, v = uv
            r = int(v * N)
            up = u * N + (0.5 if r % 2 else 0.0)
            c = int(math.floor(up))
            fu = up - c
            fv = v * N - r
            h = hnoise(c + 100 * (r % 2), r, seed)
            col = stone_color(h, P['stone_m'], tone)
            if warm:
                col = mix(col, P['stone_w'], warm * (0.3 + 0.7 * h))
            # chanfro
            if fu < 0.30 or fv < 0.30:
                col = shade(col, 1.14)
            if fu > 0.72 or fv > 0.72:
                col = shade(col, 0.82)
            # grao
            col = shade(col, 0.93 + 0.14 * hnoise(x, y, seed + 5))
            mortar = fu < 0.06 or fu > 0.95 or fv < 0.07 or fv > 0.95
            if u < 0.02 or u > 0.98 or v < 0.03 or v > 0.97:
                mortar = True
            if mortar:
                col = shade(P['mortar'], 0.9 + 0.3 * hnoise(x, y, seed + 9))
            # musgo
            m = fbm(u * 6 + seed * 0.37, v * 6, seed, 3)
            if m > 1.0 - moss * 1.9 or (mortar and m > 1.0 - moss * 2.8):
                t = min(1.0, (m - (1.0 - moss * 1.9)) * 7 + (0.35 if mortar else 0))
                mc = mix(P['moss_d'], P['moss_l'], hnoise(x, y, seed + 3))
                col = mix(col, mc, max(0.25, min(0.9, t)))
            # rachaduras
            if crack:
                cn = abs(fbm(u * 3.3 + seed, v * 3.3, seed + 7, 2) - 0.5)
                if cn < crack:
                    col = shade(P['mortar'], 1.1)
            px[x, y] = (*col, 255)
    return img


def gen_floors():
    specs = [(1, 0.10, 0, 1.0, 0.0), (2, 0.18, 0, 0.95, 0.1), (3, 0.06, 0, 1.08, 0.2), (4, 0.30, 0, 0.9, 0.0),
             (5, 0.12, 0.012, 1.0, 0.0), (6, 0.22, 0.014, 0.88, 0.0), (7, 0.05, 0, 1.12, 0.3), (8, 0.14, 0, 0.82, 0.0)]
    for i, s in enumerate(specs):
        save(floor_tile(*s), f'{OUT_ENV}/floor_{i:02d}.png')
    return len(specs)


# ---------------------------------------------------------------- prismas (blocos)
def prism(a, h, seed=1, moss=0.3, courses=14, brick=18, top_moss=0.16, tone=1.0, top_tone=1.1):
    """Prisma isometrico: topo losango 2a x a + faces laterais de altura h. Imagem (2a, a+h)."""
    W, H = 2 * a, a + h
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px = img.load()
    for x in range(W):
        left = x < a
        top_edge = a / 2 + x / 2 if left else a - (x - a) / 2
        s = x if left else x - a
        for y in range(H):
            dx = (x + 0.5 - a) / a
            dy = (y + 0.5 - a / 2) / (a / 2)
            in_top = abs(dx) + abs(dy) <= 1.0
            if in_top:
                u = (dx + dy) / 2 + 0.5
                v = (dy - dx) / 2 + 0.5
                r = int(v * 3)
                up = u * 3 + (0.5 if r % 2 else 0)
                fu, fv = up - math.floor(up), v * 3 - r
                hh = hnoise(int(math.floor(up)), r, seed + 40)
                col = shade(P['stone_m'], (0.8 + 0.4 * hh) * top_tone * tone)
                if fu < 0.12 or fv < 0.12 or fu > 0.92 or fv > 0.92:
                    col = shade(P['mortar'], 1.3)
                if u < 0.06 or v < 0.06:
                    col = shade(col, 1.25)
                col = shade(col, 0.92 + 0.16 * hnoise(x, y, seed + 6))
                m = fbm(u * 5 + seed, v * 5, seed, 3)
                if m > 1.0 - top_moss * 1.6:
                    col = mix(col, mix(P['moss_d'], P['moss_l'], hnoise(x, y, seed + 2)), 0.6)
                px[x, y] = (*col, 255)
                continue
            t = y - top_edge
            if t < 0 or t >= h or (y < a / 2 and False):
                continue
            ci = int(t // courses)
            ft = t - ci * courses
            off = (brick / 2) if ci % 2 else 0
            bi = int((s + off) // brick)
            fb = (s + off) - bi * brick
            hh = hnoise(bi + ci * 31, ci, seed + (0 if left else 77))
            face_k = (0.80 if left else 0.52) * tone
            col = shade(P['stone_m'], (0.78 + 0.42 * hh) * face_k)
            if ft < 1.5:
                col = shade(col, 1.18)
            if ft > courses - 2.2:
                col = shade(col, 0.78)
            if fb < 1.0 or ft < 0.6:
                col = shade(P['mortar'], 1.0 + 0.4 * (1 if left else 0))
            col = shade(col, 0.9 + 0.2 * hnoise(x, y, seed + 8))
            # musgo escorrendo do topo
            ln = 2 + 16 * fbm(x * 0.35 + seed, 3.1, seed + 4, 2)
            if t < ln * moss * 2.2 and fbm(x * 0.5, y * 0.3, seed + 13, 2) > 0.38:
                col = mix(col, mix(P['moss_d'], P['moss_m'], hnoise(x, y, seed + 21)), 0.8)
            # AO na base
            if t > h - 4:
                col = shade(col, 0.72 + 0.07 * (h - t))
            # quina vertical
            if x == a - 1:
                col = shade(col, 1.3)
            if x == a:
                col = shade(col, 0.8)
            px[x, y] = (*col, 255)
    return img


def stack(parts, pad=2):
    """parts: lista de (imagem, a, h) de baixo p/ cima. Retorna (img, (ax, ay)) com ancora no centro da base."""
    placed = []
    cy = 0.0
    for im, a, h in parts:
        placed.append((im, a, h, cy))
        cy -= h
    minx = -max(p[1] for p in placed)
    maxx = max(p[1] for p in placed)
    topy = min(p[3] - p[2] - p[1] / 2 for p in placed)
    boty = max(p[3] + p[1] / 2 for p in placed)
    W = int(maxx - minx) + 2 * pad
    H = int(math.ceil(boty - topy)) + 2 * pad
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ox = -minx + pad
    oy = -topy + pad
    for im, a, h, c in placed:
        out.alpha_composite(im, (int(round(ox - a)), int(round(oy + c - h - a / 2))))
    return out, (int(round(ox)), int(round(oy)))


WALL_H = {1: 28, 2: 56, 3: 84}


def decorate_face(img, a, h, kind, face):
    """Banner ou arco baked na face esquerda ('L') ou direita ('R') de um prisma de largura 2a."""
    if kind is None:
        return img
    fw = a
    flat = Image.new('RGBA', (fw, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(flat)
    if kind == 'banner':
        bw, bh = 14, min(h - 8, 46)
        x0 = (fw - bw) // 2
        d.rectangle([x0 - 1, 3, x0 + bw, 4], fill=(*P['bronze'], 255))
        cloth = (66, 44, 38)
        for yy in range(5, 5 + bh):
            tail = yy > 5 + bh - 7
            for xx in range(x0, x0 + bw):
                if tail and abs(xx - (x0 + bw / 2 - 0.5)) < (yy - (5 + bh - 7)) * 0.5:
                    continue
                k = 0.85 + 0.25 * hnoise(xx, yy, 3)
                d.point((xx, yy), fill=(*shade(cloth, k), 255))
        cx, cy = x0 + bw // 2, 5 + bh // 2 - 2
        gold = (*P['gold'], 255)
        for ang in range(0, 360, 45):
            dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            for r in range(1, 5):
                d.point((int(round(cx + dx * r)), int(round(cy + dy * r))), fill=gold)
        d.point((cx, cy), fill=(*P['gold_l'], 255))
    elif kind == 'arch':
        aw, ah = 22, min(h - 6, 44)
        x0 = (fw - aw) // 2
        y0 = h - ah - 1
        for xx in range(x0 - 2, x0 + aw + 2):
            for yy in range(y0 - 3, h):
                cx = x0 + aw / 2 - 0.5
                inside = (abs(xx - cx) <= aw / 2) and (yy >= y0 + aw / 2 or (abs(xx - cx) ** 2 + (yy - (y0 + aw / 2)) ** 2) <= (aw / 2) ** 2)
                outer = (abs(xx - cx) <= aw / 2 + 2.5) and (yy >= y0 + aw / 2 or (abs(xx - cx) ** 2 + (yy - (y0 + aw / 2)) ** 2) <= (aw / 2 + 2.5) ** 2)
                if inside:
                    t = (yy - y0) / ah
                    d.point((xx, yy), fill=(*shade((22, 20, 26), 0.6 + 0.9 * t * t), 255))
                elif outer:
                    d.point((xx, yy), fill=(*shade(P['stone_l'], 0.8 + 0.3 * hnoise(xx, yy, 5)), 255))
        # degraus
        for i in range(2):
            d.rectangle([x0 - 2 - i, h - 2 - i * 2, x0 + aw + 1 + i, h - 1 - i * 2], fill=(*shade(P['stone_m'], 0.9 - i * 0.15), 255))
    slope = 0.5 if face == 'L' else -0.5
    sh = shear(flat, slope)
    # posiciona sobre a face (x0 = 0 para L, a para R)
    base_x = 0 if face == 'L' else a
    top0 = (a / 2) if face == 'L' else a  # y da aresta superior no inicio da face
    yoff = int(round(top0)) if face == 'L' else int(round(top0 - (fw) * 0.5))
    # mascara: so desenha onde a face existe (alfa do prisma)
    dst = np.array(img)
    srcn = np.array(sh)
    for y in range(srcn.shape[0]):
        for x in range(srcn.shape[1]):
            if srcn[y, x, 3] == 0:
                continue
            X, Y = base_x + x, yoff + y
            if 0 <= X < dst.shape[1] and 0 <= Y < dst.shape[0] and dst[Y, X, 3] > 0:
                # nao cobre o topo: so abaixo da aresta superior
                dst[Y, X] = srcn[y, x]
                # escurece pela face
                k = 0.88 if face == 'L' else 0.62
                dst[Y, X, :3] = np.clip(dst[Y, X, :3] * k, 0, 255).astype(np.uint8)
    return Image.fromarray(dst, 'RGBA')


def gen_walls():
    meta = {}
    for hu, hp in WALL_H.items():
        for var in range(3):
            img = prism(32, hp, seed=hu * 10 + var, moss=0.25 + 0.1 * var, tone=1.0)
            save(img, f'{OUT_ENV}/wall_h{hu}_v{var}.png')
        if hu >= 2:
            base = prism(32, hp, seed=hu * 10 + 5, moss=0.3)
            for kind in ('banner', 'arch'):
                for face in ('L', 'R'):
                    img = decorate_face(base.copy(), 32, hp, kind, face)
                    save(img, f'{OUT_ENV}/wall_h{hu}_{kind}_{face}.png')
    # parapeito baixo
    for var in range(2):
        save(prism(32, 14, seed=90 + var, courses=14, moss=0.3), f'{OUT_ENV}/wall_low_v{var}.png')


# ---------------------------------------------------------------- penhascos
def cliff(side, seed, D=84):
    W, H = 32, 16 + D
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px = img.load()
    for x in range(W):
        top = x / 2 if side == 'L' else 16 - x / 2
        for y in range(H):
            t = y - top
            if t < 0:
                continue
            ci = int(t // 14)
            ft = t - ci * 14
            off = 9 if ci % 2 else 0
            bi = int((x + off) // 18)
            fb = (x + off) - bi * 18
            hh = hnoise(bi + ci * 31, ci, seed + (0 if side == 'L' else 77))
            k = (0.80 if side == 'L' else 0.52)
            col = shade(P['stone_m'], (0.78 + 0.42 * hh) * k)
            if ft < 1.5:
                col = shade(col, 1.15)
            if fb < 1.0 or ft < 0.6:
                col = shade(P['mortar'], 1.1)
            col = shade(col, 0.9 + 0.2 * hnoise(x, y, seed + 8))
            ln = 3 + 18 * fbm(x * 0.3 + seed, 1.7, seed + 4, 2)
            if t < ln and fbm(x * 0.5, y * 0.3, seed + 13, 2) > 0.36:
                col = mix(col, mix(P['moss_d'], P['moss_m'], hnoise(x, y, seed + 21)), 0.8)
            # neblina: escurece e azula com a profundidade, esmaece
            f = max(0.0, (t - 10) / (D - 10))
            col = mix(col, (12, 15, 26), min(0.97, f * 1.25))
            rag = D - 6 * fbm(x * 0.4 + seed, 9.0, seed + 31, 2) * 2
            alpha = 1.0 if t < rag * 0.78 else max(0.0, 1.0 - (t - rag * 0.78) / (rag * 0.22))
            if hnoise(x, y, seed + 51) > alpha + 0.05:
                continue
            px[x, y] = (*col, 255)
    # raizes pendentes
    rnd = random.Random(seed)
    for _ in range(3):
        x = rnd.randint(2, W - 3)
        top = x / 2 if side == 'L' else 16 - x / 2
        ln = rnd.randint(14, 40)
        for t in range(ln):
            y = int(top + 2 + t)
            if y < H and px[x, y][3] == 0 or t < 6:
                if y < H:
                    px[x, y] = (*mix(P['moss_d'], (14, 18, 30), t / ln), 255)
    return img


def gen_cliffs():
    for side in ('L', 'R'):
        for v in range(3):
            save(cliff(side, 11 + v * 5), f'{OUT_ENV}/cliff_{side}_{v}.png')


# ---------------------------------------------------------------- runas no chao
def rune_circle(size=320):
    """Circulo runico desenhado em 'espaco de chao' (quadrado) e achatado 2:1."""
    S = 4
    big = Image.new('RGBA', (size * S, size * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    c = size * S / 2
    gold = (*P['gold'], 255)
    dim = (*shade(P['gold'], 0.6), 255)

    def ring(r, w, col=gold):
        d.ellipse([c - r * S, c - r * S, c + r * S, c + r * S], outline=col, width=int(w * S))
    R = size / 2 - 4
    ring(R, 2.2)
    ring(R - 7, 1.0, dim)
    ring(R - 34, 1.6)
    ring(R - 41, 0.8, dim)
    ring(R * 0.42, 1.4)
    ring(R * 0.18, 1.6)
    # tick marks entre aneis
    for i in range(96):
        a = i / 96 * math.tau
        r0, r1 = R - 34, R - 41
        L = 1.0 if i % 4 else 1.8
        d.line([c + math.cos(a) * r0 * S, c + math.sin(a) * r0 * S, c + math.cos(a) * (r0 - 4 * L) * S, c + math.sin(a) * (r0 - 4 * L) * S], fill=dim, width=int(1 * S))
    # runas no anel externo (glifos pseudo-aleatorios)
    rnd = random.Random(7)
    for i in range(36):
        a = i / 36 * math.tau
        rr = R - 20.5
        cx, cy = c + math.cos(a) * rr * S, c + math.sin(a) * rr * S
        for _ in range(rnd.randint(2, 3)):
            ang = a + rnd.choice([0, math.pi / 2]) + rnd.uniform(-0.2, 0.2)
            L = rnd.uniform(2.5, 6) * S
            ox, oy = rnd.uniform(-3, 3) * S, rnd.uniform(-3, 3) * S
            d.line([cx + ox, cy + oy, cx + ox + math.cos(ang) * L, cy + oy + math.sin(ang) * L], fill=gold, width=int(1.1 * S))
    # estrela de 8 pontas
    for k, (len_, w) in enumerate(((R * 0.80, 2.0), (R * 0.62, 1.4))):
        for i in range(8):
            a = i / 8 * math.tau + (math.pi / 8 if k else 0)
            tip = (c + math.cos(a) * len_ * S, c + math.sin(a) * len_ * S)
            l1 = (c + math.cos(a + 0.18) * R * 0.2 * S, c + math.sin(a + 0.18) * R * 0.2 * S)
            r1 = (c + math.cos(a - 0.18) * R * 0.2 * S, c + math.sin(a - 0.18) * R * 0.2 * S)
            d.polygon([tip, l1, r1], outline=gold if k == 0 else dim, width=int(w * S))
    # losangos internos
    d.polygon([(c, c - R * 0.12 * S), (c + R * 0.12 * S, c), (c, c + R * 0.12 * S), (c - R * 0.12 * S, c)], fill=gold)
    small = big.resize((size, size), Image.LANCZOS)
    arr = np.array(small).astype(np.float32)
    # erosao: apaga trechos com ruido
    for y in range(size):
        for x in range(size):
            n = fbm(x * 0.045, y * 0.045, 3, 3)
            k = 1.0 if n > 0.42 else max(0.0, (n - 0.30) / 0.12)
            arr[y, x, 3] *= (0.25 + 0.75 * k) * (0.7 + 0.3 * hnoise(x, y, 5))
    small = Image.fromarray(arr.astype(np.uint8), 'RGBA')
    return small.resize((size, size // 2), Image.BOX)


def gen_decals():
    save(rune_circle(320), f'{OUT_ENV}/rune_circle.png')
    # runas menores (marcas soltas pelo chao)
    for i in range(3):
        rnd = random.Random(30 + i)
        im = Image.new('RGBA', (64, 32), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        S = 4
        big = Image.new('RGBA', (64 * S, 64 * S), (0, 0, 0, 0))
        bd = ImageDraw.Draw(big)
        gold = (*shade(P['gold'], 0.8), 255)
        bd.ellipse([8 * S, 8 * S, 56 * S, 56 * S], outline=gold, width=S)
        for _ in range(7):
            a = rnd.uniform(0, math.tau)
            x, y = 32 + math.cos(a) * 20, 32 + math.sin(a) * 20
            ang = a + rnd.choice([0, 1.57])
            bd.line([x * S, y * S, (x + math.cos(ang) * 5) * S, (y + math.sin(ang) * 5) * S], fill=gold, width=S)
        if i == 1:
            bd.polygon([(32 * S, 18 * S), (46 * S, 32 * S), (32 * S, 46 * S), (18 * S, 32 * S)], outline=gold, width=S)
        arr = np.array(big.resize((64, 64), Image.LANCZOS)).astype(np.float32)
        for y in range(64):
            for x in range(64):
                if fbm(x * 0.08 + i * 9, y * 0.08, 2, 2) < 0.4:
                    arr[y, x, 3] *= 0.2
        save(Image.fromarray(arr.astype(np.uint8), 'RGBA').resize((64, 32), Image.BOX), f'{OUT_ENV}/rune_small_{i}.png')


# ---------------------------------------------------------------- props
def crop_union(frames, anchor):
    boxes = [f.getbbox() for f in frames if f.getbbox()]
    x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
    x1 = max(b[2] for b in boxes); y1 = max(b[3] for b in boxes)
    out = [f.crop((x0, y0, x1, y1)) for f in frames]
    return out, (anchor[0] - x0, anchor[1] - y0)


def strip(frames):
    w, h = frames[0].size
    sheet = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f, (i * w, 0))
    return sheet


def add_prop(name, frames, anchor, fps=0, solid=0.0, light=None, tall=False, extra=None):
    frames, anchor = crop_union(frames, anchor)
    save(strip(frames), f'{OUT_PROP}/{name}.png')
    m = dict(file=f'res://{OUT_PROP}/{name}.png', frames=len(frames), fps=fps, fw=frames[0].size[0], fh=frames[0].size[1],
             ax=anchor[0], ay=anchor[1], solid=solid, tall=tall)
    if light:
        m['light'] = light
    if extra:
        m.update(extra)
    META[name] = m


def flame(w, h, t, kind='fire', seed=0, scale=1.0):
    """Chama animada sobre uma tela w x h; base centrada embaixo. kind: fire|blue."""
    S = 4
    r = Rig(w, h, S)
    pal = {
        'fire': (P['fire_d'], P['fire'], P['fire_l'], (255, 244, 200)),
        'blue': (P['blue_d'], P['blue'], P['blue_l'], (235, 250, 255)),
    }[kind]
    cx = w / 2
    base = h - 1
    tt = t * math.tau
    for lay, (col, hh, ww) in enumerate(zip(pal, (1.0, 0.78, 0.55, 0.30), (1.0, 0.75, 0.52, 0.28))):
        sway = math.sin(tt + lay * 0.7 + seed) * 1.4 * scale
        fh = (h * 0.95) * hh * (0.88 + 0.12 * math.sin(tt * 2 + seed + lay))
        fw = (w * 0.42) * ww * scale
        pts = [(cx - fw, base), (cx - fw * 0.9, base - fh * 0.35), (cx - fw * 0.35 + sway * 0.4, base - fh * 0.7),
               (cx + sway * 1.2, base - fh), (cx + fw * 0.35 + sway * 0.4, base - fh * 0.7), (cx + fw * 0.9, base - fh * 0.35), (cx + fw, base)]
        r.flat(poly(pts), col)
        r.flat(ell(cx, base - fw * 0.5, fw, fw * 0.75), col)
    return r.finish(outline=False)


def gen_pillars():
    for name, parts_fn, tall in (
        ('pillar_tall', lambda: [(prism(19, 9, 61, 0.2), 19, 9), (prism(14, 64, 62, 0.35, brick=14, courses=16), 14, 64), (prism(18, 8, 63, 0.2), 18, 8)], True),
        ('pillar_short', lambda: [(prism(19, 9, 71, 0.25), 19, 9), (prism(14, 30, 72, 0.4, brick=14, courses=15), 14, 30), (prism(18, 6, 73, 0.2), 18, 6)], False),
        ('pillar_stump', lambda: [(prism(19, 9, 81, 0.3), 19, 9), (prism(14, 12, 82, 0.5, brick=14, courses=12), 14, 12)], False),
    ):
        im, anc = stack(parts_fn())
        add_prop(name, [im], anc, solid=0.30, tall=tall)
    # pilar quebrado com topo irregular
    parts = [(prism(19, 9, 91, 0.25), 19, 9), (prism(14, 44, 92, 0.4, brick=14, courses=15), 14, 44)]
    im, anc = stack(parts)
    arr = np.array(im)
    H, W = arr.shape[:2]
    for x in range(W):
        cut = int(7 + 9 * hnoise(x // 2, 1, 4) + (x - W / 2) * 0.35)
        arr[:max(0, cut), x] = 0
    add_prop('pillar_broken', [Image.fromarray(arr, 'RGBA')], anc, solid=0.30)
    # pedestal de estatua
    im, anc = stack([(prism(22, 8, 101, 0.25), 22, 8), (prism(17, 16, 102, 0.3, brick=14, courses=16), 17, 16), (prism(21, 5, 103, 0.2), 21, 5)])
    add_prop('pedestal', [im], anc, solid=0.36)


def statue_figure(kind, t=0.0, seed=1):
    W, H = 44, 70
    r = Rig(W, H, 4)
    st = (92, 90, 78)
    stone_d = (46, 45, 42)
    cx = 22
    if kind == 'lantern':
        # manto
        r.part(poly([(cx - 8, 26), (cx + 8, 26), (cx + 13, 66), (cx - 13, 66)]), st, stone_d)
        r.part(ell(cx, 28, 9.5, 5), st, stone_d)                       # ombros
        r.part(poly([(cx - 7, 12), (cx + 7, 12), (cx + 9, 30), (cx - 9, 30)]), mix(st, (60, 60, 50), 0.2), stone_d)   # capuz base
        r.part(ell(cx, 14, 7.6, 8.8), st, stone_d)                    # capuz
        r.flat(ell(cx + 0.5, 16, 4.4, 5.4), (24, 22, 24))             # sombra do rosto
        # braco com lanterna
        r.part(limb((cx + 7, 28), (cx + 12, 40), 5, 4), st, stone_d)
        r.part(limb((cx - 7, 28), (cx - 4, 42), 5, 4), st, stone_d)
        # lanterna
        lx, ly = cx + 14, 44
        r.part(rect(lx - 3, ly - 1, lx + 3, ly + 7), P['bronze_d'], (30, 22, 12))
        r.part(rect(lx - 2, ly - 4, lx + 2, ly - 2), P['bronze'])
        k = 0.8 + 0.2 * math.sin(t * math.tau)
        r.glow(rect(lx - 2, ly, lx + 2, ly + 6), mix(P['blue'], P['blue_l'], k * 0.8), 255)
        # dobras do manto
        for i in range(-3, 4):
            r.detail(line((cx + i * 3, 34), (cx + i * 4.2, 66), 0.7), stone_d, 150)
    else:  # oracao
        r.part(poly([(cx - 8, 26), (cx + 8, 26), (cx + 13, 66), (cx - 13, 66)]), st, stone_d)
        r.part(ell(cx, 28, 9.5, 5), st, stone_d)
        r.part(ell(cx, 14, 7.6, 8.8), st, stone_d)
        r.flat(ell(cx, 16, 4.2, 5.2), (24, 22, 24))
        r.part(limb((cx - 7, 29), (cx - 1, 38), 5, 4), st, stone_d)
        r.part(limb((cx + 7, 29), (cx + 1, 38), 5, 4), st, stone_d)
        r.part(ell(cx, 39, 3, 2.4), st, stone_d)
        for i in range(-3, 4):
            r.detail(line((cx + i * 3, 36), (cx + i * 4.2, 66), 0.7), stone_d, 150)
    # musgo
    rnd = random.Random(seed)
    for _ in range(14):
        x, y = rnd.uniform(cx - 10, cx + 10), rnd.uniform(8, 64)
        r.detail(ell(x, y, rnd.uniform(1.0, 2.2), rnd.uniform(1.0, 2.6)), mix(P['moss_d'], P['moss_m'], rnd.random()), 170)
    return r.finish()


def gen_statues():
    ped, panc = stack([(prism(22, 8, 101, 0.25), 22, 8), (prism(17, 16, 102, 0.3, brick=14, courses=16), 17, 16), (prism(21, 5, 103, 0.2), 21, 5)])
    top_y = panc[1] - 29 - 22 / 2 + 1   # centro do topo do pedestal (aprox)
    for kind in ('lantern', 'prayer'):
        frames = []
        n = 4 if kind == 'lantern' else 1
        for i in range(n):
            fig = statue_figure(kind, i / n)
            W = max(ped.size[0], fig.size[0]) + 4
            H = ped.size[1] + fig.size[1]
            im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            px_, py_ = (W - ped.size[0]) // 2, H - ped.size[1]
            im.alpha_composite(ped, (px_, py_))
            # base da figura no centro do topo do pedestal
            top_center = (px_ + panc[0], py_ + panc[1] - 29)
            im.alpha_composite(fig, (top_center[0] - fig.size[0] // 2, top_center[1] - fig.size[1] + 2))
            frames.append(im)
        anc = (px_ + panc[0], py_ + panc[1])
        add_prop('statue_' + kind, frames, anc, fps=5 if n > 1 else 0, solid=0.38, tall=True,
                 light=dict(color=[0.45, 0.7, 1.0], energy=0.55, scale=1.4, dx=14, dy=-34) if kind == 'lantern' else None)


def gen_fires():
    # braseiro de tocha
    ped, panc = stack([(prism(15, 6, 111, 0.15), 15, 6), (prism(10, 20, 112, 0.2, brick=12, courses=10), 10, 20), (prism(14, 3, 113, 0.1), 14, 3)])

    def brazier_frame(i, n, kind):
        fl = flame(22, 34, i / n, kind, seed=i)
        W, H = max(ped.size[0], 34) + 2, ped.size[1] + 24
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        px_, py_ = (W - ped.size[0]) // 2, H - ped.size[1]
        im.alpha_composite(ped, (px_, py_))
        cx = px_ + panc[0]
        topy = py_ + panc[1] - 29
        d = ImageDraw.Draw(im)
        # tigela de bronze
        d.polygon([(cx - 11, topy - 2), (cx + 11, topy - 2), (cx + 7, topy + 5), (cx - 7, topy + 5)], fill=(*P['bronze'], 255))
        d.line([(cx - 11, topy - 2), (cx + 11, topy - 2)], fill=(*P['gold'], 255), width=1)
        d.ellipse([cx - 11, topy - 5, cx + 11, topy + 1], fill=(*P['bronze_d'], 255), outline=(*P['gold'], 255))
        d.ellipse([cx - 8, topy - 4, cx + 8, topy], fill=(60, 30, 14, 255))
        im.alpha_composite(fl, (cx - 11, topy - 2 - 32))
        return im, (cx, py_ + panc[1])
    frames = []
    for i in range(6):
        im, anc = brazier_frame(i, 6, 'fire')
        frames.append(im)
    add_prop('brazier', frames, anc, fps=9, solid=0.30, light=dict(color=[1.0, 0.62, 0.28], energy=1.15, scale=3.3, dx=0, dy=-38, flicker=True))
    # pedestal de chama azul
    ped2, panc2 = stack([(prism(15, 6, 121, 0.2), 15, 6), (prism(11, 30, 122, 0.3, brick=12, courses=10), 11, 30), (prism(14, 4, 123, 0.2), 14, 4)])
    frames = []
    for i in range(6):
        fl = flame(20, 32, i / 6, 'blue', seed=i + 3)
        W, H = max(ped2.size[0], 34) + 2, ped2.size[1] + 24
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        px_, py_ = (W - ped2.size[0]) // 2, H - ped2.size[1]
        im.alpha_composite(ped2, (px_, py_))
        cx = px_ + panc2[0]
        topy = py_ + panc2[1] - 40
        d = ImageDraw.Draw(im)
        d.ellipse([cx - 11, topy - 5, cx + 11, topy + 2], fill=(*P['bronze_d'], 255), outline=(*P['bronze'], 255))
        d.ellipse([cx - 8, topy - 4, cx + 8, topy], fill=(20, 40, 70, 255))
        im.alpha_composite(fl, (cx - 10, topy - 1 - 30))
        frames.append(im)
        anc2 = (cx, py_ + panc2[1])
    add_prop('blue_pedestal', frames, anc2, fps=8, solid=0.30, light=dict(color=[0.35, 0.65, 1.0], energy=1.0, scale=3.0, dx=0, dy=-52, flicker=True))
    # velas
    frames = []
    for i in range(4):
        W, H = 30, 30
        r = Rig(W, H, 4)
        for (x, hgt) in ((9, 8), (16, 12), (22, 7)):
            r.part(rect(x - 1.8, H - 3 - hgt, x + 1.8, H - 3), (214, 200, 168), (130, 118, 96))
        im = r.finish()
        for (x, hgt), s in zip(((9, 8), (16, 12), (22, 7)), (0, 2, 4)):
            fl = flame(6, 9, (i / 4 + s * 0.13) % 1, 'fire', seed=s, scale=0.9)
            im.alpha_composite(fl, (x - 3, H - 3 - hgt - 8))
        frames.append(im)
    add_prop('candles', frames, (15, 27), fps=7, light=dict(color=[1.0, 0.65, 0.32], energy=0.55, scale=1.3, dx=0, dy=-14, flicker=True))


def gen_crystals():
    for v in range(2):
        rnd = random.Random(50 + v)
        W, H = 40, 44
        r = Rig(W, H, 4)
        n = 4 + v
        for i in range(n):
            bx = 20 + (i - (n - 1) / 2) * 6 + rnd.uniform(-1.5, 1.5)
            hh = rnd.uniform(14, 32) * (1.1 if i == n // 2 else 0.85)
            w = rnd.uniform(3.2, 5.0)
            lean = rnd.uniform(-4, 4)
            base_y = H - 4 - rnd.uniform(0, 4)
            pts = [(bx - w, base_y), (bx - w * 0.8 + lean * 0.4, base_y - hh * 0.7), (bx + lean, base_y - hh), (bx + w * 0.8 + lean * 0.4, base_y - hh * 0.7), (bx + w, base_y)]
            r.part(poly(pts), P['blue'], P['blue_d'], P['blue_l'], bevel=1.4)
            r.detail(poly([(bx, base_y), (bx + lean * 0.3, base_y - hh * 0.8), (bx + w * 0.8 + lean * 0.4, base_y - hh * 0.7), (bx + w, base_y)]), P['blue_d'], 120)
        r.part(ell(20, H - 3, 15, 4), P['stone_d'], (20, 18, 16))
        im = r.finish()
        add_prop(f'crystal_{v}', [im], (20, H - 3), solid=0.25, light=dict(color=[0.35, 0.62, 1.0], energy=0.8, scale=2.0, dx=0, dy=-12))


def gen_plants():
    for v in range(3):
        rnd = random.Random(70 + v)
        W, H = 40, 34
        r = Rig(W, H, 4)
        if v < 2:   # arbusto morto / espinhoso
            for i in range(9):
                a = rnd.uniform(-70, 70)
                dx, dy = math.sin(math.radians(a)), -math.cos(math.radians(a))
                L = rnd.uniform(9, 20)
                x0, y0 = 20 + rnd.uniform(-3, 3), H - 3
                x1, y1 = x0 + dx * L, y0 + dy * L
                col = mix(P['moss_d'], (40, 34, 24), rnd.random())
                r.flat(line((x0, y0), (x1, y1), 1.1), col)
                for _ in range(2):
                    t = rnd.uniform(0.4, 0.9)
                    bx, by = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                    r.flat(line((bx, by), (bx + rnd.uniform(-5, 5), by - rnd.uniform(2, 7)), 0.8), col)
            for _ in range(10):
                x, y = 20 + rnd.uniform(-12, 12), H - 3 - rnd.uniform(2, 16)
                r.flat(ell(x, y, 2.2, 1.6), mix(P['moss_d'], P['moss_l'], rnd.random()))
        else:       # tufo de hera
            for _ in range(24):
                x, y = 20 + rnd.uniform(-13, 13), H - 4 - rnd.uniform(0, 12) * (1 - abs(x if False else 0))
                r.part(ell(x, y, rnd.uniform(2.5, 4.2), rnd.uniform(1.8, 3)), mix(P['moss_d'], P['moss_m'], rnd.random()), P['moss_d'], P['moss_l'], bevel=0.8)
        add_prop(f'plant_{v}', [r.finish()], (20, H - 3))
    # rubble
    for v in range(3):
        rnd = random.Random(80 + v)
        parts = []
        W, H = 56, 44
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        for i in range(5 + v):
            a = rnd.choice([5, 6, 7, 8])
            h = rnd.randint(3, 9)
            pr = prism(a, h, seed=200 + v * 7 + i, moss=0.4)
            x = 28 + rnd.randint(-16, 16)
            y = 30 + rnd.randint(-5, 5)
            im.alpha_composite(pr, (x - a, y - h - a // 2))
        add_prop(f'rubble_{v}', [im], (28, 30))


def gen_sign():
    W, H = 34, 52
    r = Rig(W, H, 4)
    wood, wood_d = (96, 70, 44), (50, 34, 20)
    r.part(rect(15, 8, 19, 48), wood, wood_d)
    r.part(poly([(5, 8), (26, 8), (31, 13), (26, 18), (5, 18)]), (118, 86, 54), wood_d)
    r.detail(line((8, 13), (24, 13), 1.0), (50, 34, 20), 200)
    r.part(ell(17, 48, 7, 2.6), P['stone_d'], (20, 18, 16))
    add_prop('signpost', [r.finish()], (17, 48), solid=0.18)


# ---------------------------------------------------------------- portao do chefe, veu, portal
def arch_flat(w_cells=4, open_cells=2, H=112):
    """Arco gotico plano (plano de parede), 32px por celula. Retorna imagem w x H."""
    W = w_cells * 32
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px = img.load()
    ox0 = (W - open_cells * 32) // 2
    ox1 = ox0 + open_cells * 32
    cx = W / 2
    spring = 44          # altura onde comeca a curva
    for x in range(W):
        for y in range(H):
            inside_open = False
            if ox0 <= x < ox1:
                # ogiva: duas circunferencias
                dxo = abs(x + 0.5 - cx)
                half = (ox1 - ox0) / 2
                top = H - spring - math.sqrt(max(0.0, (half * 1.25) ** 2 - (half * 1.25 - (half - dxo)) ** 2)) * 0.9
                inside_open = y >= top
            if inside_open:
                continue
            # moldura do arco
            dxo = abs(x + 0.5 - cx)
            half = (ox1 - ox0) / 2
            arch_ring = False
            if ox0 - 5 <= x < ox1 + 5:
                hd = half + 5
                t2 = H - spring - math.sqrt(max(0.0, (hd * 1.25) ** 2 - (hd * 1.25 - (hd - dxo)) ** 2)) * 0.9
                arch_ring = (dxo < hd) and y >= t2
            solid_area = (x < ox0 - 5 or x >= ox1 + 5) or arch_ring or y < 24
            if y < 6 and not (abs(x - cx) < 40):
                solid_area = x < ox0 + 6 or x >= ox1 - 6
            if not solid_area:
                continue
            c = ci = int(y // 14)
            off = 9 if ci % 2 else 0
            bi = int((x + off) // 18)
            hh = hnoise(bi + ci * 31, ci, 66)
            col = shade(P['stone_m'], (0.82 + 0.4 * hh) * 0.92)
            ft = y - ci * 14
            fb = (x + off) - bi * 18
            if ft < 1.5:
                col = shade(col, 1.15)
            if fb < 1.0 or ft < 0.6:
                col = shade(P['mortar'], 1.1)
            col = shade(col, 0.9 + 0.2 * hnoise(x, y, 8))
            if arch_ring:
                col = mix(col, P['stone_l'], 0.25)
                if hnoise(x * 3, y * 3, 12) > 0.93:
                    col = shade(col, 0.6)
            if fbm(x * 0.4, y * 0.2, 14, 2) > 0.62 and y < 60:
                col = mix(col, P['moss_m'], 0.6)
            # veios roxos de corrupcao junto do vao
            if (ox0 - 9 <= x < ox0 + 1 or ox1 - 1 <= x < ox1 + 9) and fbm(x * 0.5, y * 0.2, 31, 2) > 0.6:
                col = mix(col, P['purple'], 0.55)
            px[x, y] = (*col, 255)
    return img


def gen_gate():
    flat = arch_flat()
    sh = shear(flat, 0.5)
    W, H = sh.size
    pieces = []
    for i in range(4):
        sl = sh.crop((i * 32, 0, i * 32 + 32, H))
        pieces.append(sl)
        save(sl, f'{OUT_PROP}/gate_{i}.png')
    base_y = flat.size[1]
    for i in range(4):
        META[f'gate_{i}'] = dict(file=f'res://{OUT_PROP}/gate_{i}.png', frames=1, fps=0, fw=32, fh=H, ax=16, ay=base_y + 16 * i + 8, solid=0.0, tall=True)
    # veu (ocupa a abertura: 2 celulas = 64 px) animado
    frames = []
    for f in range(6):
        t = f / 6
        w, h = 64, 82
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        px = im.load()
        for x in range(w):
            for y in range(h):
                dxo = abs(x + 0.5 - w / 2)
                top = 22 + (dxo / (w / 2)) ** 2 * 26
                if y < top:
                    continue
                n = fbm(x * 0.06 + t * 2.0, y * 0.05 - t * 3.0, 3, 3)
                n2 = fbm(x * 0.12 - t * 1.5, y * 0.1 + t * 2.0, 8, 2)
                v = n * 0.7 + n2 * 0.5
                a = 0.30 + 0.5 * v
                edge = min(1.0, (w / 2 - dxo) / 8)
                a *= edge * min(1.0, (y - top) / 8 + 0.2)
                col = mix(P['purple_d'], P['purple_l'], max(0, min(1, v * 1.2 - 0.2)))
                if v > 0.78:
                    col = mix(col, (240, 220, 255), 0.5)
                px[x, y] = (*col, int(255 * min(0.92, a)))
        frames.append(shear(im, 0.5))
    h0 = 82
    add_prop('gate_veil', frames, (32, h0 + 16 - 8), fps=8, tall=True,
             light=dict(color=[0.62, 0.3, 1.0], energy=0.9, scale=2.6, dx=0, dy=-30))
    # barreira (mesma imagem, usada como parede de nevoa no corredor)
    # portal da arena: moldura gotica + redemoinho; 2 celulas de largura, plano 'L'
    frames = []
    for f in range(6):
        t = f / 6
        w, h = 60, 80
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        px = im.load()
        for x in range(w):
            for y in range(h):
                dxo = abs(x + 0.5 - w / 2)
                hw = 22
                top = 10 + (dxo / hw) ** 2 * 22
                in_open = dxo < hw and y > top
                ring = (dxo < hw + 6) and y > top - 6 and not in_open
                if in_open:
                    ang = math.atan2(y - 48, x - 30)
                    rr = math.hypot((x - 30) / 22, (y - 48) / 30)
                    sw = 0.5 + 0.5 * math.sin(ang * 3 + rr * 6 - t * math.tau)
                    n = fbm(x * 0.1 + t, y * 0.1 - t, 5, 2)
                    v = max(0.0, min(1.0, sw * 0.55 + n * 0.6 - rr * 0.25 + 0.2))
                    col = mix((24, 8, 36), P['purple_l'], v)
                    px[x, y] = (*col, 255)
                elif ring:
                    k = 0.8 + 0.4 * hnoise(x, y, 4)
                    px[x, y] = (*shade(P['stone_l'], k * 0.9), 255)
        frames.append(shear(im, 0.5))
    add_prop('portal_plane', frames, (30, 80 + 16 - 2), fps=8, tall=True,
             light=dict(color=[0.6, 0.28, 1.0], energy=1.1, scale=3.2, dx=0, dy=-30))


# ---------------------------------------------------------------- orbes, brilhos, fundo
def gen_misc():
    # brilho radial (para sprites aditivos)
    n = 64
    yy, xx = np.mgrid[0:n, 0:n]
    d = np.hypot(xx - n / 2 + 0.5, yy - n / 2 + 0.5) / (n / 2)
    a = np.clip(1 - d, 0, 1) ** 2
    img = np.zeros((n, n, 4), np.uint8)
    img[..., :3] = 255
    img[..., 3] = (a * 255).astype(np.uint8)
    save(Image.fromarray(img, 'RGBA'), f'{OUT_FX}/glow.png')
    # orbe de almas (animada)
    frames = []
    for f in range(6):
        t = f / 6
        W = 28
        r = Rig(W, W, 4)
        pulse = 1 + 0.12 * math.sin(t * math.tau)
        r.flat(ell(14, 14, 10 * pulse, 10 * pulse), P['blue_d'], 120)
        r.flat(ell(14, 14, 6.5 * pulse, 6.5 * pulse), P['blue'], 230)
        r.flat(ell(14, 14, 3.4, 3.4), (225, 245, 255))
        for k in range(3):
            a = t * math.tau + k * 2.1
            r.flat(ell(14 + math.cos(a) * 9, 14 + math.sin(a) * 4 - 2, 1.1, 1.1), P['blue_l'])
        frames.append(r.finish(outline=False))
    add_prop('soul_orb', frames, (14, 22), fps=8, light=dict(color=[0.4, 0.7, 1.0], energy=0.9, scale=1.8, dx=0, dy=-10))
    # fundo: silhuetas distantes na nevoa
    W, H = 1024, 512
    arr = np.zeros((H, W, 4), np.float32)
    rnd = random.Random(5)
    for layer, (col, alpha, cnt) in enumerate(((rgb('1a2236'), 0.55, 9), (rgb('141a2a'), 0.8, 7))):
        for _ in range(cnt):
            w = rnd.randint(44, 90)
            x0 = rnd.randint(0, W - w)
            top = rnd.randint(40, 260) + layer * 60
            for x in range(x0, x0 + w):
                for y in range(top, H):
                    # arcos escavados
                    a = alpha * (1 - (y - top) / (H - top)) ** 0.8
                    arr[y, x] = np.maximum(arr[y, x], [*col, a * 255])
            # janelas de luz distantes
            for _ in range(rnd.randint(0, 2)):
                wx, wy = rnd.randint(x0 + 6, x0 + w - 6), rnd.randint(top + 10, top + 110)
                arr[wy:wy + 3, wx:wx + 2] = [230, 150, 60, 200]
    img = Image.fromarray(arr.astype(np.uint8), 'RGBA').filter(ImageFilter.GaussianBlur(1.2))
    save(img, f'{OUT_ENV}/far_ruins.png')
    # textura de nevoa
    n = 256
    arr = np.zeros((n, n, 4), np.uint8)
    for y in range(n):
        for x in range(n):
            # ruido periodico via soma de senos + ruido de valor tileavel
            v = 0.0
            amp = 1.0
            tot = 0.0
            for o in range(4):
                f = 2 ** o * 3
                px_, py_ = x / n * f, y / n * f
                x0, y0 = int(px_), int(py_)
                fx, fy = px_ - x0, py_ - y0
                fx = fx * fx * (3 - 2 * fx)
                fy = fy * fy * (3 - 2 * fy)
                a = hnoise(x0 % f, y0 % f, o)
                b = hnoise((x0 + 1) % f, y0 % f, o)
                c = hnoise(x0 % f, (y0 + 1) % f, o)
                d_ = hnoise((x0 + 1) % f, (y0 + 1) % f, o)
                v += ((a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d_ * fx) * fy) * amp
                tot += amp
                amp *= 0.5
            v /= tot
            arr[y, x] = (150, 170, 210, min(255, int(max(0, v - 0.35) * 2.2 * 255)))
    save(Image.fromarray(arr, 'RGBA'), f'{OUT_ENV}/fog.png')


def main():
    gen_floors()
    gen_walls()
    gen_cliffs()
    gen_decals()
    gen_pillars()
    gen_statues()
    gen_fires()
    gen_crystals()
    gen_plants()
    gen_sign()
    gen_gate()
    gen_misc()
    with open('tools/data/props.json', 'w') as f:
        json.dump(META, f, indent=1)
    print('props:', len(META))


if __name__ == '__main__':
    main()
