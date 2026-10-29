"""Gera texturas da HUD medieval e efeitos de combate.
Uso: python3 tools/gen_ui.py"""
import math, os, sys, json
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from px import *

UI = 'assets/ui'
FX = 'assets/effects'
os.makedirs(UI, exist_ok=True)
os.makedirs(FX, exist_ok=True)
META = {}

BR_D, BR, BR_L = (58, 40, 20), (128, 92, 44), (196, 156, 78)
DARK = (14, 12, 14)


def new(w, h):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def border(d, w, h, col_out=BR_D, col_mid=BR, col_hi=BR_L, inset=0):
    d.rectangle([inset, inset, w - 1 - inset, h - 1 - inset], outline=(*col_out, 255))
    d.rectangle([inset + 1, inset + 1, w - 2 - inset, h - 2 - inset], outline=(*col_mid, 255))
    d.line([(inset + 1, inset + 1), (w - 2 - inset, inset + 1)], fill=(*col_hi, 255))
    d.line([(inset + 1, inset + 1), (inset + 1, h - 2 - inset)], fill=(*col_hi, 255))


def diamond(d, cx, cy, r, col=BR_L, out=BR_D):
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=(*col, 255), outline=(*out, 255))


def bar_frame(w, h, name, cap=10):
    im, d = new(w, h)
    border(d, w, h)
    # pontas ornamentais
    for x in (3, w - 4):
        diamond(d, x, h // 2, min(4, h // 2 - 1))
    d.line([(cap, 0), (w - 1 - cap, 0)], fill=(*BR_L, 255))
    save(im, f'{UI}/{name}.png')


def gradient_bar(name, top, mid, bot, w=12, h=8):
    im, d = new(w, h)
    for y in range(h):
        t = y / (h - 1)
        c = mix(top, mid, t * 2) if t < 0.5 else mix(mid, bot, (t - 0.5) * 2)
        d.line([(0, y), (w - 1, y)], fill=(*c, 255))
    # brilho fino em cima
    d.line([(0, 1), (w - 1, 1)], fill=(*mix(top, (255, 255, 255), 0.25), 255))
    for x in range(0, w, 3):
        d.point((x, h - 2), fill=(*shade(bot, 0.8), 255))
    save(im, f'{UI}/{name}.png')


def orb():
    S = 60
    im, d = new(S, S)
    c = S // 2
    # aneis de bronze
    d.ellipse([2, 2, S - 3, S - 3], fill=(*BR_D, 255))
    d.ellipse([5, 5, S - 6, S - 6], fill=(*BR, 255))
    d.ellipse([8, 8, S - 9, S - 9], fill=(*DARK, 255))
    d.ellipse([10, 10, S - 11, S - 11], outline=(*BR_L, 255))
    # espinhos
    for i in range(12):
        a = i / 12 * math.tau
        x0, y0 = c + math.cos(a) * (c - 4), c + math.sin(a) * (c - 4)
        x1, y1 = c + math.cos(a) * (c + 0.0), c + math.sin(a) * (c + 0.0)
        pa = a + math.pi / 2
        d.polygon([(x0 + math.cos(pa) * 3, y0 + math.sin(pa) * 3), (x1, y1), (x0 - math.cos(pa) * 3, y0 - math.sin(pa) * 3)], fill=(*BR_L, 255), outline=(*BR_D, 255))
    save(im, f'{UI}/orb_frame.png')
    # gema azul
    G = 36
    gm = np.zeros((G, G, 4), np.uint8)
    for y in range(G):
        for x in range(G):
            dx, dy = (x + 0.5 - G / 2) / (G / 2), (y + 0.5 - G / 2) / (G / 2)
            r = math.hypot(dx, dy)
            if r > 1:
                continue
            k = 1 - r
            col = mix(P['blue_d'], P['blue'], min(1, k * 1.6))
            hl = max(0, 1 - math.hypot(dx + 0.38, dy + 0.4) * 2.2)
            col = mix(col, (225, 245, 255), min(1, hl))
            gm[y, x] = (*col, 255)
    gim = Image.fromarray(gm, 'RGBA')
    d = ImageDraw.Draw(gim)
    # escaravelho / lagrima
    for dx, dy in ((0, -6), (-5, 0), (5, 0), (0, 6)):
        d.point((G // 2 + dx, G // 2 + dy), fill=(*P['blue_l'], 255))
    d.polygon([(G // 2, G // 2 - 8), (G // 2 + 5, G // 2 + 2), (G // 2, G // 2 + 9), (G // 2 - 5, G // 2 + 2)], outline=(*P['blue_d'], 255))
    save(gim, f'{UI}/orb_gem.png')


def slots():
    S = 38
    im, d = new(S, S)
    d.rectangle([0, 0, S - 1, S - 1], fill=(14, 12, 14, 230))
    border(d, S, S)
    for x, y in ((3, 3), (S - 4, 3), (3, S - 4), (S - 4, S - 4)):
        diamond(d, x, y, 2)
    save(im, f'{UI}/slot.png')
    im, d = new(S, S)
    border(d, S, S, (120, 84, 28), BR_L, (255, 232, 150))
    d.rectangle([2, 2, S - 3, S - 3], outline=(*mix(BR_L, (255, 255, 255), 0.2), 255))
    for x, y in ((3, 3), (S - 4, 3), (3, S - 4), (S - 4, S - 4)):
        diamond(d, x, y, 3, (255, 232, 150), BR)
    save(im, f'{UI}/slot_sel.png')


def icon_sword():
    im, d = new(28, 28)
    d.polygon([(23, 3), (25, 5), (10, 20), (8, 18)], fill=(*P['steel_l'], 255), outline=(*P['steel_d'], 255))
    d.line([(22, 5), (10, 18)], fill=(255, 255, 255, 220))
    d.polygon([(5, 14), (14, 23), (12, 25), (3, 16)], fill=(*BR_L, 255), outline=(*BR_D, 255))
    d.line([(4, 24), (8, 20)], fill=(*P['leather'], 255), width=3)
    d.ellipse([2, 23, 5, 26], fill=(*BR_L, 255))
    save(im, f'{UI}/icon_sword.png')


def icon_oil():
    im, d = new(28, 28)
    d.rectangle([9, 5, 19, 24], fill=(70, 46, 24, 255), outline=(*BR_D, 255))
    d.rectangle([10, 9, 18, 22], fill=(*P['fire'], 255))
    d.rectangle([10, 9, 13, 22], fill=(*P['fire_l'], 255))
    d.rectangle([11, 2, 17, 6], fill=(*BR, 255), outline=(*BR_D, 255))
    d.rectangle([8, 12, 20, 14], fill=(*BR_L, 255))
    d.line([(10, 20), (18, 20)], fill=(*P['fire_d'], 255))
    save(im, f'{UI}/icon_oil.png')


def icon_flask():
    im, d = new(28, 28)
    d.ellipse([5, 8, 23, 26], fill=(20, 40, 80, 255), outline=(*BR, 255))
    d.ellipse([7, 10, 21, 24], fill=(*P['blue'], 255))
    d.ellipse([9, 12, 14, 17], fill=(*P['blue_l'], 255))
    d.rectangle([11, 3, 17, 9], fill=(*BR, 255), outline=(*BR_D, 255))
    d.line([(10, 3), (18, 3)], fill=(*BR_L, 255))
    d.line([(9, 21), (19, 21)], fill=(*P['blue_d'], 255))
    save(im, f'{UI}/icon_flask.png')


def icon_cloak():
    im, d = new(28, 28)
    d.polygon([(8, 4), (20, 4), (25, 24), (20, 26), (14, 23), (8, 26), (3, 24)], fill=(*P['cloak'], 255), outline=(*P['cloak_d'], 255))
    d.polygon([(8, 4), (14, 8), (20, 4), (17, 3), (11, 3)], fill=(*P['cloak_l'], 255), outline=(*P['cloak_d'], 255))
    for a in range(0, 360, 45):
        d.point((int(14 + math.cos(math.radians(a)) * 4), int(15 + math.sin(math.radians(a)) * 4)), fill=(*BR_L, 255))
    d.point((14, 15), fill=(*BR_L, 255))
    save(im, f'{UI}/icon_cloak.png')


def drops():
    for name, full in (('drop_full', True), ('drop_empty', False)):
        im, d = new(11, 14)
        col = P['blue'] if full else (30, 34, 44)
        d.polygon([(5, 1), (9, 8), (8, 11), (5, 12), (2, 11), (1, 8)], fill=(*col, 255), outline=(*(BR if full else BR_D), 255))
        if full:
            d.point((4, 7), fill=(*P['blue_l'], 255))
            d.point((4, 8), fill=(*P['blue_l'], 255))
        save(im, f'{UI}/{name}.png')


def soul_frame():
    w, h = 96, 26
    im, d = new(w, h)
    d.rectangle([0, 0, w - 1, h - 1], fill=(10, 8, 10, 215))
    border(d, w, h)
    diamond(d, 4, h // 2, 3)
    diamond(d, w - 5, h // 2, 3)
    save(im, f'{UI}/soul_frame.png')
    im, d = new(16, 16)
    d.polygon([(8, 1), (14, 8), (8, 15), (2, 8)], fill=(*BR, 255), outline=(*BR_D, 255))
    d.polygon([(8, 4), (11, 8), (8, 12), (5, 8)], fill=(*P['blue'], 255))
    d.point((7, 7), fill=(*P['blue_l'], 255))
    save(im, f'{UI}/soul_icon.png')


def compass():
    w, h = 260, 14
    im, d = new(w, h)
    d.rectangle([4, 4, w - 5, h - 5], fill=(10, 8, 10, 190), outline=(*BR_D, 255))
    d.line([(6, 4), (w - 7, 4)], fill=(*BR, 255))
    for i in range(11):
        x = 22 + i * (w - 44) / 10
        diamond(d, int(x), h // 2, 2 if i % 5 else 3, BR if i % 5 else BR_L)
    diamond(d, 6, h // 2, 5)
    diamond(d, w - 7, h // 2, 5)
    save(im, f'{UI}/compass.png')
    im, d = new(13, 13)
    d.polygon([(6, 0), (12, 6), (6, 12), (0, 6)], fill=(*P['blue'], 255), outline=(*BR_L, 255))
    d.polygon([(6, 3), (9, 6), (6, 9), (3, 6)], fill=(*P['blue_l'], 255))
    save(im, f'{UI}/compass_marker.png')


def panels():
    w = h = 52
    im, d = new(w, h)
    d.rectangle([0, 0, w - 1, h - 1], fill=(10, 8, 12, 235))
    border(d, w, h)
    border(d, w, h, BR_D, BR_D, BR, inset=4)
    for x, y in ((3, 3), (w - 4, 3), (3, h - 4), (w - 4, h - 4)):
        diamond(d, x, y, 3)
    save(im, f'{UI}/panel.png')
    for name, hov in (('button', False), ('button_hover', True)):
        w, h = 56, 20
        im, d = new(w, h)
        d.rectangle([0, 0, w - 1, h - 1], fill=((40, 28, 16, 240) if hov else (16, 12, 14, 235)))
        border(d, w, h, BR_D, BR_L if hov else BR, (255, 232, 150) if hov else BR_L)
        diamond(d, 3, h // 2, 2)
        diamond(d, w - 4, h // 2, 2)
        save(im, f'{UI}/{name}.png')
    im, d = new(220, 9)
    d.line([(8, 4), (96, 4)], fill=(*BR, 255))
    d.line([(124, 4), (212, 4)], fill=(*BR, 255))
    diamond(d, 110, 4, 4)
    diamond(d, 100, 4, 2)
    diamond(d, 120, 4, 2)
    save(im, f'{UI}/divider.png')
    # vinheta
    w, h = 320, 180
    yy, xx = np.mgrid[0:h, 0:w]
    dx, dy = (xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)
    r = np.hypot(dx * 0.95, dy * 1.05)
    a = np.clip((r - 0.55) / 0.75, 0, 1) ** 1.6 * 0.85
    img = np.zeros((h, w, 4), np.uint8)
    img[..., 0] = 4
    img[..., 1] = 4
    img[..., 2] = 8
    img[..., 3] = (a * 255).astype(np.uint8)
    save(Image.fromarray(img, 'RGBA'), f'{UI}/vignette.png')


# ---------------------------------------------------------------- efeitos de combate
def slash_frames():
    """Arco de corte voltado para +X (direita), desenhado em espaco de chao (quadrado), 5 quadros."""
    S = 96
    frames = []
    for f in range(5):
        t = f / 4
        big = Image.new('RGBA', (S * 4, S * 4), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        c = S * 2
        R = S * 4 * 0.42
        sweep0 = -75 + 150 * min(1, t * 1.6)
        start = -75
        thick = (1 - t) * 0.9 + 0.1
        steps = 40
        pts_out, pts_in = [], []
        for i in range(steps + 1):
            a = math.radians(start + (sweep0 - start) * i / steps)
            w = math.sin(math.pi * i / steps) * thick * S * 4 * 0.12
            pts_out.append((c + math.cos(a) * (R + w * 0.55), c + math.sin(a) * (R + w * 0.55)))
            pts_in.append((c + math.cos(a) * (R - w * 0.45), c + math.sin(a) * (R - w * 0.45)))
        poly_pts = pts_out + pts_in[::-1]
        alpha = int(255 * (1 - t * 0.7))
        d.polygon(poly_pts, fill=(255, 245, 215, alpha))
        # nucleo mais claro
        inner = [(c + (x - c) * 0.97, c + (y - c) * 0.97) for x, y in pts_out]
        d.line(inner, fill=(255, 255, 255, alpha), width=int(S * 0.05))
        frames.append(big.resize((S, S), Image.LANCZOS))
    sheet = Image.new('RGBA', (S * 5, S), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        sheet.paste(fr, (i * S, 0))
    save(sheet, f'{FX}/slash.png')
    META['slash'] = dict(file='res://assets/effects/slash.png', fw=S, fh=S, frames=5, fps=30)


def spark_frames():
    S = 32
    sheet = Image.new('RGBA', (S * 4, S), (0, 0, 0, 0))
    for f in range(4):
        big = Image.new('RGBA', (S * 4, S * 4), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        c = S * 2
        t = f / 3
        n = 8
        for i in range(n):
            a = i / n * math.tau + 0.2
            r0 = (0.1 + t * 0.35) * S * 4
            r1 = (0.28 + t * 0.4) * S * 4 * (1.0 if i % 2 else 0.6)
            w = max(2, int((1 - t) * 9))
            d.line([c + math.cos(a) * r0, c + math.sin(a) * r0, c + math.cos(a) * r1, c + math.sin(a) * r1], fill=(255, 235, 190, int(255 * (1 - t * 0.6))), width=w)
        if f < 2:
            d.ellipse([c - 14 + f * 5, c - 14 + f * 5, c + 14 - f * 5, c + 14 - f * 5], fill=(255, 250, 235, 255))
        sheet.paste(big.resize((S, S), Image.LANCZOS), (f * S, 0))
    save(sheet, f'{FX}/spark.png')
    META['spark'] = dict(file='res://assets/effects/spark.png', fw=S, fh=S, frames=4, fps=24)


def crack():
    W, H = 160, 80
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    import random
    rnd = random.Random(4)
    cx, cy = W // 2, H // 2
    for i in range(11):
        a = i / 11 * math.tau + rnd.uniform(-0.2, 0.2)
        x, y = cx, cy
        for s in range(rnd.randint(4, 7)):
            a += rnd.uniform(-0.5, 0.5)
            L = rnd.uniform(6, 13)
            nx, ny = x + math.cos(a) * L, y + math.sin(a) * L * 0.5
            d.line([(x, y), (nx, ny)], fill=(*P['purple_l'], 255), width=1)
            x, y = nx, ny
    save(im, f'{FX}/crack.png')


def build_sheet_meta():
    json.dump(META, open('tools/data/fx.json', 'w'), indent=1)


def main():
    bar_frame(64, 14, 'bar_frame')
    bar_frame(80, 18, 'boss_frame', 16)
    gradient_bar('bar_red', (214, 70, 60), (150, 24, 28), (86, 10, 16))
    gradient_bar('bar_green', (150, 190, 90), (84, 120, 52), (44, 72, 34))
    gradient_bar('bar_gold', (240, 200, 110), (190, 140, 60), (110, 76, 30))
    gradient_bar('bar_trail', (255, 236, 190), (230, 190, 120), (170, 120, 60))
    gradient_bar('bar_bg', (24, 18, 18), (14, 10, 12), (8, 6, 8))
    orb()
    slots()
    icon_sword(); icon_oil(); icon_flask(); icon_cloak()
    drops()
    soul_frame()
    compass()
    panels()
    slash_frames()
    spark_frames()
    crack()
    build_sheet_meta()
    print('ui ok')


if __name__ == '__main__':
    main()
