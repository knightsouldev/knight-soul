"""Gera spritesheets animados: protagonista, inimigos e chefe (rig procedural com IK).
Uso: python3 tools/gen_chars.py [player|soldier|guardian|boss|wraith ...]"""
import json, math, os, random, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from px import *

ACTORS = {}

BASE = dict(bob=0.0, crouch=0.0, lean=0.0, px=0.0, lfx=0.0, lfy=0.0, rfx=0.0, rfy=0.0,
            lhx=None, lhy=None, rhx=None, rhy=None, wa=60.0, two=False, hx=0.0, hy=0.0,
            cape=0.0, rot=0.0, rotc=(0.0, 0.0), shx=0.0, shy=0.0, flask=False, aura=0.0, t=0.0,
            shield=0.0, eyes=1.0, mouth=0.0)


def mk(**kw):
    return kw


# ---------------------------------------------------------------- especificacoes
SPECS = {
    'player': dict(W=48, H=56, CX=24, FY=52, leg=(8.2, 8.4), leg_w=4.4, hip_w=2.8, torso_h=11.5, sw=11.5, ww=8.5,
                   head_r=5.1, arm=(6.8, 6.6), arm_w=3.6, boot_w=4.6, head='hair', weapon='sword', cape='cloak',
                   pauld=3.6, wlen=17,
                   col=dict(cloth=(44, 44, 52), armor=(86, 88, 98), trim=P['gold'], boots=(40, 30, 26), cape=P['cloak'],
                            hair=(20, 18, 26), skin=P['skin'], belt=P['leather'], glove=(70, 58, 50))),
    'soldier': dict(W=48, H=56, CX=24, FY=52, leg=(8.0, 8.4), leg_w=4.4, hip_w=2.9, torso_h=11.5, sw=11.8, ww=9.4,
                    head_r=5.0, arm=(6.8, 6.6), arm_w=3.8, boot_w=4.6, head='kettle', weapon='sword_shield', cape='tatters',
                    pauld=3.2, wlen=16,
                    col=dict(cloth=(86, 72, 56), armor=(96, 88, 78), trim=(110, 84, 46), boots=(48, 38, 30), cape=(70, 44, 52),
                             hair=(30, 26, 30), skin=(150, 128, 130), belt=(52, 38, 28), glove=(70, 60, 54),
                             rust=(112, 74, 48), corrupt=P['purple_l'])),
    'guardian': dict(W=68, H=76, CX=34, FY=71, leg=(11.0, 11.0), leg_w=7.0, hip_w=4.6, torso_h=17, sw=21, ww=15,
                     head_r=7.2, arm=(9.5, 9.0), arm_w=5.8, boot_w=7.2, head='great_helm', weapon='mace', cape='tabard',
                     pauld=6.6, wlen=34,
                     col=dict(cloth=(70, 54, 52), armor=(84, 82, 88), trim=(130, 96, 50), boots=(40, 34, 32), cape=(92, 40, 40),
                              hair=(30, 26, 30), skin=(110, 100, 100), belt=(48, 36, 28), glove=(60, 56, 56),
                              rust=(118, 76, 46), corrupt=P['purple_l'])),
    'boss': dict(W=150, H=152, CX=66, FY=146, leg=(19, 19.5), leg_w=10.5, hip_w=6.8, torso_h=27, sw=31, ww=21,
                 head_r=9.6, arm=(15, 14), arm_w=8.4, boot_w=11, head='boss_helm', weapon='halberd', cape='boss',
                 pauld=10, wlen=80,
                 col=dict(cloth=(44, 38, 56), armor=(66, 66, 78), trim=(150, 112, 58), boots=(34, 30, 38), cape=(64, 26, 62),
                          hair=(30, 26, 30), skin=(110, 100, 100), belt=(46, 34, 30), glove=(50, 48, 58),
                          rust=(112, 74, 48), corrupt=P['purple_l'])),
    'wraith': dict(W=60, H=66, CX=30, FY=60, head='wraith', col=dict(body=(52, 58, 92), glow=P['blue_l'], eye=(190, 240, 255))),
}


# ---------------------------------------------------------------- armas
def draw_weapon(r, S, kind, hand, wa, p, view):
    d = dirv(wa)
    n = (-d[1], d[0])
    hx, hy = hand
    c = S['col']
    steel, steel_d = P['steel'], P['steel_d']
    if kind in ('sword', 'sword_shield'):
        L = S['wlen']
        b0 = (hx + d[0] * 1.5, hy + d[1] * 1.5)
        tip = (hx + d[0] * (L + 2), hy + d[1] * (L + 2))
        wd = 2.6
        if kind == 'sword_shield':
            steel, steel_d = c['rust'], shade(c['rust'], 0.5)
            wd = 3.0
        r.part(poly([(b0[0] + n[0] * wd / 2, b0[1] + n[1] * wd / 2), (tip[0] + n[0] * 0.3, tip[1] + n[1] * 0.3),
                     (tip[0] - n[0] * 0.3, tip[1] - n[1] * 0.3), (b0[0] - n[0] * wd / 2, b0[1] - n[1] * wd / 2)]),
               steel, steel_d, P['steel_l'], bevel=0.6)
        gd = (hx + d[0] * 1.6, hy + d[1] * 1.6)
        r.part(limb((gd[0] - n[0] * 3, gd[1] - n[1] * 3), (gd[0] + n[0] * 3, gd[1] + n[1] * 3), 1.5), c['trim'], shade(c['trim'], 0.5))
        r.part(limb((hx - d[0] * 3.2, hy - d[1] * 3.2), (hx + d[0] * 1.0, hy + d[1] * 1.0), 1.8), P['leather'], P['leather_d'])
        if kind == 'sword' and S is SPECS['player']:
            r.glow(line((b0[0] + d[0] * 2, b0[1] + d[1] * 2), (tip[0] - d[0] * 1, tip[1] - d[1] * 1), 0.5), (230, 240, 255), 130)
    elif kind == 'mace':
        L = S['wlen']
        b0 = (hx - d[0] * L * 0.28, hy - d[1] * L * 0.28)
        e = (hx + d[0] * L * 0.72, hy + d[1] * L * 0.72)
        r.part(limb(b0, e, 3.0), P['leather'], P['leather_d'], bevel=0.6)
        hc = (e[0] + d[0] * 5, e[1] + d[1] * 5)
        r.part(poly([(hc[0] + n[0] * 8 + d[0] * 6, hc[1] + n[1] * 8 + d[1] * 6), (hc[0] - n[0] * 8 + d[0] * 6, hc[1] - n[1] * 8 + d[1] * 6),
                     (hc[0] - n[0] * 8 - d[0] * 6, hc[1] - n[1] * 8 - d[1] * 6), (hc[0] + n[0] * 8 - d[0] * 6, hc[1] + n[1] * 8 - d[1] * 6)]),
               (78, 76, 84), (36, 34, 40), (150, 150, 160), bevel=0.8)
        for sgn in (-1, 1):
            r.part(poly([(hc[0] + n[0] * sgn * 8 + d[0] * 3, hc[1] + n[1] * sgn * 8 + d[1] * 3),
                         (hc[0] + n[0] * sgn * 12.5, hc[1] + n[1] * sgn * 12.5),
                         (hc[0] + n[0] * sgn * 8 - d[0] * 3, hc[1] + n[1] * sgn * 8 - d[1] * 3)]), (110, 106, 112), (40, 38, 44), bevel=0.5)
        r.part(poly([(hc[0] + d[0] * 6, hc[1] + d[1] * 6), (hc[0] + d[0] * 13, hc[1] + d[1] * 13), (hc[0] + d[0] * 6 + n[0] * 3, hc[1] + d[1] * 6 + n[1] * 3)]), (120, 116, 122), bevel=0.5)
        r.glow(ell(hc[0], hc[1], 4, 4), P['purple'], 90 if p['aura'] > 0.2 else 0)
        r.part(limb((hx - d[0] * L * 0.28, hy - d[1] * L * 0.28), (hx - d[0] * L * 0.28 - d[0] * 2, hy - d[1] * L * 0.28 - d[1] * 2), 4), c['trim'])
    elif kind == 'halberd':
        L = S['wlen']
        b0 = (hx - d[0] * L * 0.30, hy - d[1] * L * 0.30)
        e = (hx + d[0] * L * 0.70, hy + d[1] * L * 0.70)
        r.part(limb(b0, e, 3.4), (62, 48, 40), (28, 22, 20), (110, 90, 70), bevel=0.6)
        # reforcos de bronze no cabo
        for t in (0.15, 0.45):
            q = (hx - d[0] * L * 0.3 + d[0] * L * t, hy - d[1] * L * 0.3 + d[1] * L * t)
            r.part(limb((q[0] - n[0] * 2.4, q[1] - n[1] * 2.4), (q[0] + n[0] * 2.4, q[1] + n[1] * 2.4), 2), c['trim'], shade(c['trim'], 0.5))
        # cabeca: lamina de machado de um lado + espigao + gancho
        a = e
        blade = [(a[0] - d[0] * 12 + n[0] * 2, a[1] - d[1] * 12 + n[1] * 2), (a[0] - d[0] * 14 + n[0] * 17, a[1] - d[1] * 14 + n[1] * 17),
                 (a[0] + d[0] * 3 + n[0] * 20, a[1] + d[1] * 3 + n[1] * 20), (a[0] + d[0] * 8 + n[0] * 9, a[1] + d[1] * 8 + n[1] * 9),
                 (a[0] + d[0] * 6 + n[0] * 2, a[1] + d[1] * 6 + n[1] * 2)]
        r.part(poly(blade), (112, 112, 126), (44, 42, 56), (200, 204, 218), bevel=0.9)
        r.glow(line(blade[1], blade[2], 0.9), P['purple_l'], 190)
        spike = [(a[0] + n[0] * 2.4, a[1] + n[1] * 2.4), (a[0] - n[0] * 2.4, a[1] - n[1] * 2.4), (a[0] + d[0] * 17, a[1] + d[1] * 17)]
        r.part(poly(spike), (150, 152, 166), (50, 48, 62), (225, 228, 240), bevel=0.6)
        hook = [(a[0] - d[0] * 8 - n[0] * 2, a[1] - d[1] * 8 - n[1] * 2), (a[0] - d[0] * 12 - n[0] * 11, a[1] - d[1] * 12 - n[1] * 11), (a[0] - d[0] * 2 - n[0] * 2, a[1] - d[1] * 2 - n[1] * 2)]
        r.part(poly(hook), (96, 96, 110), (40, 38, 50), bevel=0.6)
        # runas no ferro
        r.glow(ell(a[0] - d[0] * 6 + n[0] * 8, a[1] - d[1] * 6 + n[1] * 8, 1.5, 1.5), P['purple_l'], 230)
        # ponta traseira
        r.part(poly([(b0[0] + n[0] * 1.6, b0[1] + n[1] * 1.6), (b0[0] - n[0] * 1.6, b0[1] - n[1] * 1.6), (b0[0] - d[0] * 6, b0[1] - d[1] * 6)]), (120, 120, 134), bevel=0.5)
        if p['aura'] > 0:
            for k in range(5):
                ph = (p['t'] + k * 0.21) % 1.0
                q = (a[0] + d[0] * (4 + ph * 14) + n[0] * math.sin(ph * 6 + k) * 6, a[1] + d[1] * (4 + ph * 14) + n[1] * math.sin(ph * 6 + k) * 6)
                r.glow(ell(q[0], q[1], 1.6, 1.6), P['purple_l'], int(150 * p['aura'] * (1 - ph)))


# ---------------------------------------------------------------- cabecas
def draw_head(r, S, hc, p, view):
    c = S['col']
    R = S['head_r']
    kind = S['head']
    front = view == 'front'
    hx, hy = hc
    sh = 0.9 if front else -0.9
    if kind == 'hair':
        r.part(limb((hx, hy + R * 0.8), (hx, hy + R * 1.3), R * 0.8), c['skin'], c['skin'] and P['skin_d'])
        r.part(ell(hx + sh * 0.4, hy, R, R * 1.04), c['skin'], P['skin_d'])
        if front:
            # franja e espetos de cabelo
            r.part(poly([(hx - R * 1.05, hy - R * 0.1), (hx - R * 0.7, hy - R * 1.05), (hx - R * 0.2, hy - R * 1.5), (hx + R * 0.4, hy - R * 1.2),
                         (hx + R * 1.0, hy - R * 1.3), (hx + R * 1.05, hy - R * 0.2), (hx + R * 0.7, hy - R * 0.45), (hx + R * 0.1, hy - R * 0.62),
                         (hx - R * 0.5, hy - R * 0.4)]), c['hair'], shade(c['hair'], 0.6), (60, 56, 78), bevel=0.7)
            for sx, sy, ex, ey in ((-1.0, -0.6, -1.5, 0.2), (-0.6, -1.2, -1.2, -1.7), (0.5, -1.2, 0.9, -1.8), (1.0, -0.6, 1.5, -0.1)):
                r.part(poly([(hx + sx * R, hy + sy * R), (hx + ex * R, hy + ey * R), (hx + sx * R * 0.5, hy + sy * R * 0.4)]), c['hair'], shade(c['hair'], 0.6), bevel=0.4)
            ex = hx + sh
            r.flat(rect(ex - 2.6, hy + 0.3, ex - 1.4, hy + 1.6), (20, 18, 22))
            r.flat(rect(ex + 1.4, hy + 0.3, ex + 2.6, hy + 1.6), (20, 18, 22))
            r.flat(rect(ex - 0.5, hy + 3.0, ex + 0.9, hy + 3.4), P['skin_d'])
        else:
            r.part(ell(hx + sh * 0.3, hy - R * 0.1, R * 1.06, R * 1.12), c['hair'], shade(c['hair'], 0.6), (60, 56, 78), bevel=0.8)
            for sx, ex, ey in ((-0.9, -1.4, -1.7), (-0.2, -0.4, -2.0), (0.6, 1.0, -1.9), (1.0, 1.6, -0.9)):
                r.part(poly([(hx + sx * R, hy - R * 0.6), (hx + ex * R, hy + ey * R), (hx + (sx + 0.5) * R, hy - R * 0.9)]), c['hair'], shade(c['hair'], 0.6), bevel=0.4)
    elif kind == 'kettle':
        r.part(limb((hx, hy + R * 0.8), (hx, hy + R * 1.3), R * 0.8), c['skin'], P['skin_d'])
        r.part(ell(hx + sh * 0.4, hy + 0.5, R * 0.95, R), c['skin'], shade(c['skin'], 0.55))
        if front:
            r.flat(ell(hx + sh * 0.4, hy + 1.0, R * 0.78, R * 0.6), (24, 18, 30))
            ex = hx + sh
            e = p['eyes']
            r.glow(rect(ex - 2.8, hy + 0.6, ex - 1.2, hy + 1.7), c['corrupt'], int(255 * e))
            r.glow(rect(ex + 1.2, hy + 0.6, ex + 2.8, hy + 1.7), c['corrupt'], int(255 * e))
        # elmo cuba enferrujado
        r.part(poly([(hx - R * 1.1, hy + 0.2), (hx - R * 0.95, hy - R * 0.9), (hx, hy - R * 1.45), (hx + R * 0.95, hy - R * 0.9), (hx + R * 1.1, hy + 0.2),
                     (hx + R * 0.6, hy - R * 0.2), (hx - R * 0.6, hy - R * 0.2)]), c['armor'], shade(c['armor'], 0.5), bevel=0.9)
        r.part(ell(hx, hy - 0.4, R * 1.28, R * 0.38), shade(c['armor'], 0.9), shade(c['armor'], 0.45), bevel=0.7)
        r.detail(ell(hx - R * 0.4, hy - R * 0.9, 1.6, 1.0), c['rust'], 200)
        r.detail(ell(hx + R * 0.5, hy - R * 0.5, 1.2, 1.5), c['rust'], 200)
        if not front:
            r.part(ell(hx, hy + 0.5, R, R * 0.9), c['armor'], shade(c['armor'], 0.5))
    elif kind == 'great_helm':
        r.part(limb((hx, hy + R * 0.8), (hx, hy + R * 1.5), R * 1.1), (60, 58, 66), (26, 24, 30))
        r.part(poly([(hx - R * 0.95, hy - R * 1.2), (hx + R * 0.95, hy - R * 1.2), (hx + R * 1.05, hy + R * 1.1), (hx - R * 1.05, hy + R * 1.1)]),
               c['armor'], shade(c['armor'], 0.5), (150, 150, 160), bevel=0.8)
        r.part(ell(hx, hy - R * 1.2, R * 0.95, R * 0.45), shade(c['armor'], 1.1), shade(c['armor'], 0.5), bevel=0.7)
        if front:
            sx = hx + sh * 0.6
            r.flat(rect(sx - R * 0.8, hy - R * 0.25, sx + R * 0.8, hy + R * 0.18), (14, 10, 16))
            r.glow(rect(sx - R * 0.55, hy - R * 0.12, sx + R * 0.55, hy + R * 0.08), (200, 90, 60), int(210 * p['eyes']))
            for k in range(-2, 3):
                r.flat(rect(sx + k * 1.6, hy + R * 0.45, sx + k * 1.6 + 0.7, hy + R * 0.8), (20, 18, 24))
            r.detail(rect(hx - 0.7, hy - R * 1.2, hx + 0.7, hy + R * 1.0), shade(c['armor'], 0.55), 200)
        # crina rasgada
        r.part(poly([(hx - 1.5, hy - R * 1.5), (hx + 2, hy - R * 1.5), (hx + 7, hy - R * 0.2), (hx + 9, hy + R * 0.8), (hx + 5, hy + R * 0.3), (hx + 2, hy + R * 1.0), (hx - 1, hy - R * 0.2)]),
               c['cape'], shade(c['cape'], 0.5), bevel=0.6)
        r.detail(ell(hx - R * 0.5, hy + R * 0.2, 1.8, 1.2), c['rust'], 190)
    elif kind == 'boss_helm':
        # gorjal / malha
        r.part(limb((hx, hy + R * 0.7), (hx, hy + R * 1.5), R * 1.25), (50, 48, 58), (22, 20, 28))
        # cristas traseiras (coroa de espinhos)
        for i, (ax, ay, bx, by) in enumerate(((-1.0, -0.9, -1.9, -2.0), (-0.45, -1.2, -0.9, -2.5), (0.15, -1.3, 0.2, -2.8), (0.75, -1.2, 1.3, -2.5), (1.15, -0.8, 2.0, -1.8))):
            r.part(poly([(hx + ax * R, hy + ay * R), (hx + bx * R, hy + by * R), (hx + (ax + 0.42) * R, hy + (ay + 0.1) * R)]), (96, 96, 110), (36, 34, 46), (190, 192, 206), bevel=0.7)
        # chifres curvos
        for sgn in (-1, 1):
            r.part(poly([(hx + sgn * R * 0.85, hy - R * 0.4), (hx + sgn * R * 1.9, hy - R * 0.9), (hx + sgn * R * 2.3, hy - R * 2.0),
                         (hx + sgn * R * 1.5, hy - R * 1.3), (hx + sgn * R * 0.6, hy - R * 0.7)]), (112, 108, 100), (44, 40, 38), (200, 196, 180), bevel=0.8)
        r.part(poly([(hx - R * 1.1, hy - R * 1.0), (hx + R * 1.1, hy - R * 1.0), (hx + R * 1.2, hy + R * 1.1), (hx + R * 0.6, hy + R * 1.35),
                     (hx - R * 0.6, hy + R * 1.35), (hx - R * 1.2, hy + R * 1.1)]), c['armor'], shade(c['armor'], 0.5), (150, 152, 170), bevel=0.9)
        r.part(ell(hx, hy - R * 1.0, R * 1.1, R * 0.5), shade(c['armor'], 1.1), shade(c['armor'], 0.5), bevel=0.8)
        r.detail(rect(hx - 1.0, hy - R * 1.2, hx + 1.0, hy + R * 1.3), c['trim'], 190)
        if front:
            sx = hx + sh * 0.5
            r.flat(rect(sx - R * 0.8, hy - R * 0.1, sx + R * 0.8, hy + R * 0.28), (10, 6, 14))
            r.glow(rect(sx - R * 0.7, hy - R * 0.0, sx - R * 0.15, hy + R * 0.18), c['corrupt'], int(255 * p['eyes']))
            r.glow(rect(sx + R * 0.15, hy - R * 0.0, sx + R * 0.7, hy + R * 0.18), c['corrupt'], int(255 * p['eyes']))
            r.flat(rect(sx - 0.6, hy + R * 0.28, sx + 0.6, hy + R * 0.9), (10, 6, 14))
            for k in (-1, 1):
                r.flat(rect(sx + k * 2.4 - 0.4, hy + R * 0.45, sx + k * 2.4 + 0.4, hy + R * 0.95), (16, 12, 22))
        r.detail(ell(hx - R * 0.5, hy - R * 0.3, 1.8, 1.1), c['rust'], 150)


# ---------------------------------------------------------------- humanoide
def render_humanoid(name, pose, view):
    S = SPECS[name]
    p = {**BASE, **pose}
    c = S['col']
    W, H, CX, FY = S['W'], S['H'], S['CX'], S['FY']
    r = Rig(W, H, 4)
    th, shn = S['leg']
    leg_total = th + shn
    front = view == 'front'
    pelvis = (CX + p['px'], FY - leg_total * 0.94 + p['bob'] + p['crouch'])
    hw = S['hip_w']
    hl, hr = (pelvis[0] - hw, pelvis[1]), (pelvis[0] + hw, pelvis[1])
    lf = (hl[0] + p['lfx'], FY - p['lfy'])
    rf = (hr[0] + p['rfx'], FY - p['rfy'])
    lk, lfoot = ik2(hl, lf, th, shn, bend=-1)
    rk, rfoot = ik2(hr, rf, th, shn, bend=-1)
    neck = (pelvis[0] + p['lean'] * 1.15, pelvis[1] - S['torso_h'])
    sw = S['sw']
    sl = (neck[0] - sw / 2, neck[1] + 1.6)
    sr = (neck[0] + sw / 2, neck[1] + 1.6)
    hc = (neck[0] + p['hx'], neck[1] - S['head_r'] * 0.78 + p['hy'])
    ua, fa = S['arm']
    arm_total = ua + fa
    lhx = -1.0 if p['lhx'] is None else p['lhx']
    lhy = arm_total * 0.86 if p['lhy'] is None else p['lhy']
    rhx = 1.5 if p['rhx'] is None else p['rhx']
    rhy = arm_total * 0.86 if p['rhy'] is None else p['rhy']
    rh = (sr[0] + rhx, sr[1] + rhy)
    d_w = dirv(p['wa'])
    if p['two']:
        gap = S['wlen'] * 0.30 if S['weapon'] != 'mace' else S['wlen'] * 0.22
        lh = (rh[0] - d_w[0] * gap, rh[1] - d_w[1] * gap)
    else:
        lh = (sl[0] + lhx, sl[1] + lhy)
    le, lhand = ik2(sl, lh, ua, fa, bend=1)
    re_, rhand = ik2(sr, rh, ua, fa, bend=-1)
    aw = S['arm_w']
    lw = S['leg_w']
    cloth, armor, trim = c['cloth'], c['armor'], c['trim']
    big = S['W'] > 100
    heavy = S['W'] > 60

    def cape_poly(len_mult=1.0):
        top_l = (sl[0] - 1.5, sl[1] - 0.5)
        top_r = (sr[0] + 1.5, sr[1] - 0.5)
        hem_y = pelvis[1] + (S['leg'][0] * 1.15) * len_mult
        sway = p['cape']
        pts = [top_l, top_r]
        spread = sw / 2 + (4 if S['cape'] == 'cloak' else 6 if S['cape'] == 'boss' else 2)
        n = 7
        for i in range(n + 1):
            t = i / n
            x = (neck[0] + spread) - t * 2 * spread + sway * (1 - 0.3 * abs(t - 0.5))
            jag = (1 if i % 2 else -1) * (2.2 if S['cape'] != 'boss' else 3.6) * hnoise(i, int(hem_y), 3)
            pts.append((x, hem_y + jag))
        return pts

    # ---------- capa (atras do corpo em vista frontal)
    cape_kind = S['cape']
    if cape_kind in ('cloak', 'tatters', 'boss') and front:
        k = 0.55 if cape_kind == 'tatters' else 1.0
        r.part(poly(cape_poly(k)), c['cape'], shade(c['cape'], 0.55), shade(c['cape'], 1.3), bevel=1.0)
        r.detail(line((neck[0] - 3, sl[1] + 3), (neck[0] - 5 + p['cape'] * 0.5, pelvis[1] + 8), 0.8), shade(c['cape'], 0.5), 190)
        r.detail(line((neck[0] + 3, sl[1] + 3), (neck[0] + 5 + p['cape'] * 0.5, pelvis[1] + 8), 0.8), shade(c['cape'], 0.5), 190)

    # ---------- braco esquerdo (atras)
    def arm(shoulder, elbow, hand, glove=True):
        r.part(limb(shoulder, elbow, aw, aw * 0.92), cloth if not heavy else armor, shade(cloth, 0.55) if not heavy else shade(armor, 0.5), bevel=0.9)
        r.part(limb(elbow, hand, aw * 0.95, aw * 0.85), armor if S['head'] != 'kettle' else cloth, shade(armor, 0.5), bevel=0.9)
        r.part(ell(hand[0], hand[1], aw * 0.62, aw * 0.62), c['glove'], shade(c['glove'], 0.5), bevel=0.6)
        if heavy:
            r.detail(ell(elbow[0], elbow[1], aw * 0.55, aw * 0.55), trim, 220)
    shield_left = S['weapon'] == 'sword_shield'
    two = p['two']
    if front and not two:
        arm(sl, le, lhand)
    # ---------- pernas
    for hip, knee, foot, tw in ((hl, lk, lfoot, 0.0), (hr, rk, rfoot, 1.0)):
        r.part(limb(hip, knee, lw * 1.02, lw * 0.92), cloth if S['head'] in ('hair', 'kettle') else armor, shade(cloth, 0.55) if S['head'] in ('hair', 'kettle') else shade(armor, 0.5), bevel=0.9)
        r.part(limb(knee, (foot[0], foot[1] - 1.0), lw * 0.92, lw * 0.8), armor if S['head'] != 'kettle' else c['boots'], shade(armor, 0.5), bevel=0.9)
        toe = (foot[0] + (S['boot_w'] * 0.45 if front else 0.5), foot[1] + 0.2)
        r.part(limb((foot[0], foot[1] - 1.2), toe, S['boot_w'] * 0.62, S['boot_w'] * 0.5), c['boots'], shade(c['boots'], 0.5), bevel=0.8)
        r.detail(ell(knee[0], knee[1], lw * 0.5, lw * 0.5), trim if heavy else armor, 200)
    # ---------- tronco
    ww = S['ww']
    waist = pelvis[1] - 0.5
    torso = [(sl[0] - 0.5, sl[1] - 0.5), (sr[0] + 0.5, sr[1] - 0.5), (pelvis[0] + p['lean'] * 0.4 + ww / 2 + 0.6, waist), (pelvis[0] + p['lean'] * 0.4 - ww / 2 - 0.6, waist)]
    body_col = cloth
    if S['head'] in ('great_helm', 'boss_helm'):
        body_col = armor
    r.part(poly(torso), body_col, shade(body_col, 0.52), bevel=1.0)
    r.part(ell(pelvis[0], waist, ww / 2 + 1.2, 2.6), cloth, shade(cloth, 0.5), bevel=0.8)
    # peitoral
    if front:
        if S['head'] == 'hair':
            r.part(poly([(sl[0] + 1.5, sl[1] + 0.5), (sr[0] - 1.5, sr[1] + 0.5), (pelvis[0] + 3.3, waist - 3.5), (pelvis[0] - 3.3, waist - 3.5)]), armor, shade(armor, 0.5), (140, 144, 158), bevel=0.8)
            r.detail(line((neck[0], neck[1] + 3), (neck[0], waist - 4), 0.6), shade(armor, 0.45), 200)
        elif S['head'] == 'kettle':
            for k in range(3):
                y = sl[1] + 2.5 + k * 2.6
                r.detail(line((sl[0] + 2, y), (sr[0] - 2, y + 0.4), 0.5), shade(cloth, 0.55), 220)
            r.detail(ell(neck[0] + 2, neck[1] + 6, 2.2, 1.6), P['purple'], 170)
            r.detail(line((neck[0] - 4, neck[1] + 4), (neck[0] - 2, neck[1] + 9), 0.7), c['corrupt'], 180)
        elif S['head'] == 'great_helm':
            r.part(poly([(sl[0] + 1, sl[1] + 0.5), (sr[0] - 1, sr[1] + 0.5), (pelvis[0] + 5.5, waist - 3), (pelvis[0] - 5.5, waist - 3)]), (92, 90, 98), (36, 34, 42), (170, 170, 180), bevel=1.0)
            r.part(poly([(neck[0] - 3.5, neck[1] + 4), (neck[0] + 3.5, neck[1] + 4), (neck[0] + 5, waist + 5), (neck[0] - 5, waist + 5)]), c['cape'], shade(c['cape'], 0.5), bevel=0.8)
            r.detail(line((neck[0] - 8, neck[1] + 5), (neck[0] + 8, neck[1] + 5), 1.0), trim, 220)
        else:
            r.part(poly([(sl[0] + 1.5, sl[1] + 1), (sr[0] - 1.5, sr[1] + 1), (pelvis[0] + 7, waist - 4), (pelvis[0] - 7, waist - 4)]), (82, 82, 96), (30, 28, 40), (170, 172, 190), bevel=1.2)
            r.detail(line((neck[0], neck[1] + 4), (neck[0], waist - 4), 1.0), trim, 230)
            r.detail(line((sl[0] + 4, sl[1] + 7), (sr[0] - 4, sr[1] + 7), 0.9), trim, 200)
            r.glow(ell(neck[0], neck[1] + 11, 2.1, 2.1), P['purple_l'], 235)
            r.detail(ell(neck[0] - 7, neck[1] + 11, 1.0, 1.0), trim, 220)
            r.detail(ell(neck[0] + 7, neck[1] + 11, 1.0, 1.0), trim, 220)
    # cinto + fivela
    r.part(poly([(pelvis[0] - ww / 2 - 0.4, waist - 1.7), (pelvis[0] + ww / 2 + 0.4, waist - 1.7), (pelvis[0] + ww / 2 + 0.4, waist + 0.7), (pelvis[0] - ww / 2 - 0.4, waist + 0.7)]), c['belt'], shade(c['belt'], 0.5), bevel=0.6)
    if front:
        r.detail(rect(pelvis[0] - 0.8, waist - 1.6, pelvis[0] + 0.8, waist + 0.5), trim, 255)
    # frasco azul no quadril (jogador)
    if S['head'] == 'hair' and front:
        fx, fy = pelvis[0] + ww / 2 + 1.5, waist + 1.5
        r.part(ell(fx, fy, 2.0, 2.4), (30, 50, 90), (12, 22, 46), bevel=0.5)
        r.glow(ell(fx, fy + 0.3, 1.2, 1.5), P['blue'], 255)
    # ombreiras
    pr = S['pauld']
    if S['head'] in ('hair',):
        r.part(ell(sl[0] - 0.3, sl[1] + 0.2, pr, pr * 0.85), armor, shade(armor, 0.5), (150, 154, 170), bevel=0.9)
        r.part(ell(sr[0] + 0.3, sr[1] + 0.2, pr, pr * 0.85), armor, shade(armor, 0.5), (150, 154, 170), bevel=0.9)
    elif S['head'] == 'kettle':
        r.part(ell(sl[0] - 0.3, sl[1] + 0.2, pr, pr * 0.8), c['rust'], shade(c['rust'], 0.5), bevel=0.8)
        r.part(ell(sr[0] + 0.3, sr[1] + 0.2, pr * 0.8, pr * 0.7), armor, shade(armor, 0.5), bevel=0.8)
    else:
        for sx, sgn in ((sl[0] - 1, -1), (sr[0] + 1, 1)):
            r.part(ell(sx, sl[1] + 0.5, pr, pr * 0.82), armor, shade(armor, 0.5), (170, 172, 188) if big else (150, 150, 160), bevel=1.1)
            r.detail(ell(sx, sl[1] + 0.5, pr * 0.8, pr * 0.62), trim, 130)
            sp = pr * (1.1 if big else 0.9)
            r.part(poly([(sx + sgn * pr * 0.2, sl[1] - pr * 0.4), (sx + sgn * pr * 0.9, sl[1] - pr * 0.7 - sp), (sx + sgn * pr * 0.9 + sgn * 1.0, sl[1] - pr * 0.1)]), (120, 120, 134), (40, 38, 50), bevel=0.6)
    # ---------- cabeca
    draw_head(r, S, hc, p, view)
    # ---------- capa em vista traseira (sobre o corpo)
    if cape_kind in ('cloak', 'tatters', 'boss', 'tabard') and not front:
        if cape_kind == 'tabard':
            r.part(poly([(neck[0] - 5, neck[1] + 3), (neck[0] + 5, neck[1] + 3), (neck[0] + 8, pelvis[1] + 12), (neck[0] - 8, pelvis[1] + 12)]), c['cape'], shade(c['cape'], 0.5), bevel=1.0)
        else:
            k = 0.55 if cape_kind == 'tatters' else 1.0
            r.part(poly(cape_poly(k)), c['cape'], shade(c['cape'], 0.55), shade(c['cape'], 1.3), bevel=1.0)
            for i in range(-2, 3):
                r.detail(line((neck[0] + i * 3.6, sl[1] + 3), (neck[0] + i * 4.8 + p['cape'] * 0.4, pelvis[1] + 9), 0.8), shade(c['cape'], 0.5), 180)
            if cape_kind == 'cloak':
                for ang in range(0, 360, 60):
                    dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
                    r.detail(line((neck[0], neck[1] + 9), (neck[0] + dx * 4, neck[1] + 9 + dy * 4), 0.7), P['gold'], 200)
            if cape_kind == 'boss':
                r.glow(ell(neck[0], neck[1] + 17, 3, 3), P['purple_l'], 190)
                for ang in range(0, 360, 45):
                    dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
                    r.detail(line((neck[0], neck[1] + 17), (neck[0] + dx * 8, neck[1] + 17 + dy * 8), 0.8), c['trim'], 210)
    # gola / capuz de capa na frente
    if front and cape_kind in ('cloak', 'boss'):
        r.part(poly([(sl[0] - 1.5, sl[1] - 0.3), (neck[0] - 3.5, neck[1] + 0.5), (neck[0] + 3.5, neck[1] + 0.5), (sr[0] + 1.5, sr[1] - 0.3), (sr[0] + 0.5, sr[1] + 2.8), (neck[0], neck[1] + 4), (sl[0] - 0.5, sl[1] + 2.8)]),
               c['cape'], shade(c['cape'], 0.55), shade(c['cape'], 1.3), bevel=0.8)
    # ---------- escudo (soldado)
    if shield_left and p['shield'] >= 0:
        sc = (lhand[0] - 1.5, lhand[1] - 1.0 - p['shield'])
        rad = 6.8
        r.part(ell(sc[0], sc[1], rad, rad * 1.08), (84, 62, 42), (40, 28, 18), (130, 100, 70), bevel=1.0)
        r.detail(line((sc[0], sc[1] - rad), (sc[0], sc[1] + rad), 0.7), (40, 28, 18), 230)
        r.detail(line((sc[0] - rad, sc[1]), (sc[0] + rad, sc[1]), 0.7), (40, 28, 18), 230)
        r.part(ell(sc[0], sc[1], 2.0, 2.0), c['trim'], shade(c['trim'], 0.5), bevel=0.5)
        r.detail(line((sc[0] - 4, sc[1] - 3), (sc[0] - 1, sc[1] + 1), 0.8), c['corrupt'], 210)
    # ---------- braco direito + arma
    if two:
        arm(sl, le, lhand)
    wp = S['weapon']
    if wp in ('halberd', 'mace'):
        draw_weapon(r, S, wp, rhand, p['wa'], p, view)
        arm(sr, re_, rhand)
        if not front:
            pass
    else:
        arm(sr, re_, rhand)
        draw_weapon(r, S, wp, rhand, p['wa'], p, view)
        if not front:
            pass
    # frasco na mao esquerda (cura)
    if p['flask'] and S['head'] == 'hair':
        fx, fy = lhand
        r.part(ell(fx - 0.3, fy - 0.8, 2.0, 2.6), (30, 50, 90), (12, 22, 46), bevel=0.5)
        r.part(rect(fx - 0.9, fy - 4.3, fx + 0.3, fy - 2.6), (110, 84, 52), bevel=0.4)
        r.glow(ell(fx - 0.3, fy - 0.6, 1.3, 1.7), (150, 215, 255), 255)
        r.glow(ell(fx - 0.3, fy - 0.6, 4.2, 4.6), P['blue'], 70)
    # ---------- aura / brilho de corrupcao
    if p['aura'] > 0 and S['W'] > 100:
        for k in range(7):
            ph = (p['t'] * 1.0 + k / 7.0) % 1.0
            x = CX + (hnoise(k, 4, 9) - 0.5) * 42 + p['px']
            y = FY - 6 - ph * 100
            r.glow(ell(x, y, 1.5, 1.5), P['purple_l'], int(150 * p['aura'] * (1 - ph)))
    # ---------- transformacoes globais
    if p['rot'] != 0:
        rc = p['rotc']
        r.rotate(p['rot'], CX + rc[0], pelvis[1] + rc[1] if rc[1] != -999 else FY)
    if p['shx'] or p['shy']:
        r.shift(p['shx'], p['shy'])
    return r.finish()


# ---------------------------------------------------------------- espectro
def render_wraith(pose, view):
    S = SPECS['wraith']
    p = {**BASE, **pose}
    W, H, CX, FY = S['W'], S['H'], S['CX'], S['FY']
    r = Rig(W, H, 4)
    c = S['col']
    t = p['t']
    bob = p['bob']
    cx = CX + p['px']
    top = 14 + bob
    # fios esgarcados da barra (atras)
    for i in range(7):
        x0 = cx - 13 + i * 4.4
        sway = math.sin(t * math.tau + i * 0.9) * 2.4
        ln = 18 + 10 * hnoise(i, 3, 5) + math.sin(t * math.tau * 2 + i) * 2
        r.part(poly([(x0 - 2.6, top + 30), (x0 + 2.6, top + 30), (x0 + sway, top + 30 + ln)]), shade(c['body'], 0.7), shade(c['body'], 0.35), bevel=0.6)
    # manto
    r.part(poly([(cx - 8, top + 8), (cx + 8, top + 8), (cx + 15, top + 34), (cx + 6, top + 38), (cx - 6, top + 38), (cx - 15, top + 34)]), c['body'], shade(c['body'], 0.5), (110, 126, 190), bevel=1.0)
    # capuz
    r.part(poly([(cx - 8.5, top + 12), (cx - 6, top + 2), (cx, top - 3), (cx + 6, top + 2), (cx + 8.5, top + 12), (cx + 5, top + 16), (cx - 5, top + 16)]), shade(c['body'], 1.05), shade(c['body'], 0.45), (120, 138, 205), bevel=1.0)
    if view == 'front':
        r.flat(ell(cx, top + 9, 5.2, 5.8), (6, 8, 16))
        e = p['eyes']
        r.glow(ell(cx - 2.2, top + 8.5, 1.5, 1.2), c['eye'], int(255 * e))
        r.glow(ell(cx + 2.2, top + 8.5, 1.5, 1.2), c['eye'], int(255 * e))
        r.glow(ell(cx - 2.2, top + 8.5, 3.8, 3.2), c['glow'], int(60 * e))
        r.glow(ell(cx + 2.2, top + 8.5, 3.8, 3.2), c['glow'], int(60 * e))
    # bracos espectrais
    up = p['lhy'] if p['lhy'] is not None else 0.0
    for sgn in (-1, 1):
        sh = (cx + sgn * 7, top + 17)
        hd = (cx + sgn * (11 - up * 0.2), top + 27 - up)
        el = (cx + sgn * 12, top + 22 - up * 0.5)
        r.part(limb(sh, el, 3.2, 2.6), shade(c['body'], 1.1), shade(c['body'], 0.5), bevel=0.7)
        r.part(limb(el, hd, 2.6, 2.0), shade(c['body'], 1.1), shade(c['body'], 0.5), bevel=0.7)
        for k in (-1, 0, 1):
            r.flat(line(hd, (hd[0] + sgn * 3 + k * 1.2, hd[1] + 3.5 - up * 0.1 + abs(k)), 0.8), (170, 190, 230))
    # orbe de energia (ataque)
    if p['aura'] > 0:
        oy = top + 20 - up
        rad = 3.5 + 5.5 * p['aura']
        r.glow(ell(cx, oy, rad * 1.6, rad * 1.6), P['purple'], int(70 * p['aura']))
        r.glow(ell(cx, oy, rad, rad), P['purple_l'], int(220 * min(1, p['aura'] * 1.4)))
        r.glow(ell(cx, oy, rad * 0.45, rad * 0.45), (245, 235, 255), 255)
    # brilho interno
    r.glow(ell(cx, top + 24, 5, 6), P['blue'], 40)
    if p['rot'] != 0:
        r.rotate(p['rot'], cx, FY)
    if p['shx'] or p['shy']:
        r.shift(p['shx'], p['shy'])
    # espectro: um pouco translucido nas bordas (via alpha geral)
    img = r.finish()
    return img


# ---------------------------------------------------------------- animacoes
def lerp(a, b, t):
    return a + (b - a) * t


def blend(p0, p1, t):
    out = {}
    for k in set(p0) | set(p1):
        a, b = p0.get(k, BASE[k]), p1.get(k, BASE[k])
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
            out[k] = lerp(a, b, t)
        elif a is None and b is None:
            out[k] = None
        elif a is None or b is None:
            out[k] = b if t > 0.5 else a
        else:
            out[k] = b if t > 0.5 else a
    return out


def sample(keys, n, loop=True):
    """keys: lista de poses-chave igualmente espacadas; devolve n poses interpoladas."""
    out = []
    K = len(keys)
    for i in range(n):
        t = i / n if loop else (i / max(1, n - 1))
        if loop:
            f = t * K
            a = int(f) % K
            b = (a + 1) % K
        else:
            f = t * (K - 1)
            a = min(K - 2, int(f)) if K > 1 else 0
            b = min(K - 1, a + 1)
        out.append(blend(keys[a], keys[b], f - int(f) if loop else f - a))
    return out


def walk_poses(S, n=6, speed=1.0, stride=5.0, lift=3.4, bounce=0.8, lean=0.8):
    out = []
    for i in range(n):
        ph = i / n * math.tau
        l, rr = math.sin(ph), math.sin(ph + math.pi)
        out.append(mk(lfx=l * stride, rfx=rr * stride, lfy=max(0, math.cos(ph)) * lift, rfy=max(0, math.cos(ph + math.pi)) * lift,
                      bob=-abs(math.sin(ph)) * bounce, lean=lean, lhx=-1 - l * 2.0, rhx=1.5 - rr * 2.0,
                      cape=-math.sin(ph) * 1.2, t=i / n, wa=70 + rr * 8))
    return out


def idle_poses(n=4, aura=0.0, wa=60, breathe=0.7):
    out = []
    for i in range(n):
        ph = i / n * math.tau
        out.append(mk(bob=math.sin(ph) * breathe * 0.5, crouch=(1 - math.cos(ph)) * 0.25, cape=math.sin(ph) * 0.9, hy=-math.sin(ph) * 0.2, wa=wa + math.sin(ph) * 2, t=i / n, aura=aura,
                      lhy=None, rhy=None))
    return out


def rep(pose, **kw):
    q = dict(pose)
    q.update(kw)
    return q


def anim_player():
    A = {}
    A['idle'] = (idle_poses(4, wa=62), 5, True)
    A['walk'] = (walk_poses(SPECS['player']), 11, True)
    # ataque 1: corte descendente diagonal (wind 2 / act 2 / rec 2)
    a1 = [mk(rhx=2, rhy=-9, wa=205, lean=-1.2, crouch=0.3, rfx=-1, lfx=1.5, cape=-1.5),
          mk(rhx=0, rhy=-11, wa=232, lean=-2.2, crouch=0.8, rfx=-1.5, lfx=2.0, cape=-2.5, hy=0.3),
          mk(rhx=9, rhy=-4, wa=150, lean=1.2, crouch=0.6, rfx=3, lfx=-2, cape=1.5),
          mk(rhx=13.5, rhy=3.0, wa=96, lean=2.6, crouch=1.0, rfx=5, lfx=-3.4, cape=2.8, lhx=-4),
          mk(rhx=11.5, rhy=6, wa=72, lean=2.2, crouch=0.8, rfx=4.4, lfx=-3, cape=2.0, lhx=-3),
          mk(rhx=6, rhy=10, wa=62, lean=0.8, crouch=0.2, rfx=2, lfx=-1, cape=0.8)]
    A['attack1'] = (a1, 12, False, dict(wind=2, act=2, rec=2))
    a2 = [mk(rhx=-1, rhy=12, wa=22, lean=-1.0, crouch=0.5, rfx=-2, lfx=2),
          mk(rhx=-3, rhy=14, wa=12, lean=-2.0, crouch=1.0, rfx=-2.5, lfx=2.5, cape=-2),
          mk(rhx=8, rhy=7, wa=70, lean=1.0, crouch=0.6, rfx=3, lfx=-2),
          mk(rhx=13, rhy=-5, wa=135, lean=2.4, crouch=1.0, rfx=5, lfx=-3.2, cape=2.5, lhx=-4, hy=-0.3),
          mk(rhx=10, rhy=-7, wa=160, lean=2.0, crouch=0.8, rfx=4, lfx=-3, cape=2.0),
          mk(rhx=6, rhy=4, wa=90, lean=0.8, crouch=0.2, rfx=2, lfx=-1)]
    A['attack2'] = (a2, 12, False, dict(wind=2, act=2, rec=2))
    # esquiva (rolamento)
    dg = []
    for i, rot in enumerate((0, -75, -165, -255, -335)):
        tuck = (0.0, 1.0, 1.0, 1.0, 0.4)[i]
        dg.append(mk(crouch=7.5 * tuck, lfy=5 * tuck, rfy=5 * tuck, lfx=2 * tuck, rfx=2 * tuck, lean=2.5 * tuck, rot=rot, rotc=(0, -9), shy=-4.5 * tuck, wa=130,
                     rhx=3, rhy=5 - 4 * tuck, lhx=3, lhy=5 - 4 * tuck, cape=-3 * tuck, hy=1.5 * tuck))
    A['dodge'] = (dg, 12, False)
    A['hurt'] = ([mk(lean=-3, hy=-0.8, crouch=0.6, rhx=-3, rhy=6, lhx=-5, lhy=8, wa=20, cape=2.5, eyes=0.5),
                  mk(lean=-2.2, hy=-0.4, crouch=1.0, rhx=-1, rhy=8, lhx=-3, lhy=10, wa=40, cape=1.5, eyes=0.5)], 8, False)
    A['death'] = ([mk(lean=-3, hy=-0.8, crouch=1, rhx=-2, rhy=8, wa=30),
                   mk(lean=-3.5, crouch=6, lfy=1, rfy=3, rfx=2, lhx=-6, lhy=6, rhx=-4, rhy=10, wa=10, hy=1.5),
                   mk(lean=-5, crouch=8, lfy=3, rfy=5, rot=28, rotc=(0, 4), lhx=-6, lhy=4, rhx=-6, rhy=8, wa=10, shx=-1),
                   mk(lean=-5, crouch=8, lfy=4, rfy=6, rot=62, rotc=(0, 6), lhx=-6, lhy=2, rhx=-8, rhy=6, wa=20, shx=-2),
                   mk(lean=-3, crouch=3, lfy=2, rfy=2, rot=84, rotc=(0, 8), lhx=-7, lhy=-2, rhx=-8, rhy=4, wa=30, shx=-3, shy=-1),
                   mk(lean=-3, crouch=2, lfy=1, rfy=1, rot=88, rotc=(0, 8), lhx=-7, lhy=-3, rhx=-8, rhy=4, wa=30, shx=-3, shy=-1, eyes=0)], 8, False)
    A['heal'] = ([mk(lhx=-2, lhy=9, lean=0.2, flask=True, crouch=0.5, rhy=12, wa=60),
                  mk(lhx=2, lhy=-0.5, lean=0.4, flask=True, crouch=0.5, rhy=12, wa=60),
                  mk(lhx=4, lhy=-5, lean=-0.4, flask=True, hy=-1.2, crouch=0.3, rhy=12, wa=60),
                  mk(lhx=4, lhy=-5, lean=-0.4, flask=True, hy=-1.2, crouch=0.3, rhy=12, wa=60, eyes=1),
                  mk(lhx=-1, lhy=6, lean=0.1, flask=True, rhy=12, wa=60)], 8, False)
    return A


def anim_soldier():
    S = SPECS['soldier']
    A = {}
    A['idle'] = ([rep(q, lhx=-3, lhy=10, shield=0.5) for q in idle_poses(4, wa=75, breathe=0.9)], 4, True)
    w = walk_poses(S, stride=4.4, lean=1.0)
    A['walk'] = ([rep(q, lhx=-3, lhy=10, shield=0.5) for q in w], 8, True)
    a = [mk(rhx=2, rhy=-8, wa=200, lean=-1.5, crouch=0.3, lhx=-2, lhy=7, shield=0.5, rfx=-1),
         mk(rhx=1, rhy=-10, wa=222, lean=-2.5, crouch=0.8, lhx=-2, lhy=7, shield=0.5, rfx=-1.5, lfx=2),
         mk(rhx=2, rhy=-11, wa=232, lean=-3, crouch=1.0, lhx=-2, lhy=6, shield=0.5, rfx=-1.5, lfx=2.4, eyes=1),
         mk(rhx=9, rhy=-3, wa=140, lean=1.4, crouch=0.8, lhx=-3, lhy=9, shield=0.5, rfx=3, lfx=-2),
         mk(rhx=13, rhy=4, wa=92, lean=3.0, crouch=1.2, lhx=-4, lhy=10, shield=0.5, rfx=5.4, lfx=-3.6),
         mk(rhx=11, rhy=7, wa=70, lean=2.6, crouch=1.0, lhx=-3, lhy=10, shield=0.5, rfx=4.5, lfx=-3),
         mk(rhx=8, rhy=9, wa=66, lean=1.8, crouch=0.6, lhx=-3, lhy=10, shield=0.5, rfx=3, lfx=-2),
         mk(rhx=5, rhy=11, wa=64, lean=0.6, crouch=0.2, lhx=-3, lhy=10, shield=0.5, rfx=1.5, lfx=-0.5)]
    A['attack'] = (a, 10, False, dict(wind=3, act=2, rec=3))
    A['hurt'] = ([mk(lean=-3.2, hy=-0.8, crouch=0.8, rhx=-3, rhy=6, lhx=-5, lhy=8, wa=20, eyes=0.3, shield=0.5),
                  mk(lean=-2.2, hy=-0.4, crouch=1.2, rhx=-1, rhy=8, lhx=-3, lhy=10, wa=40, eyes=0.5, shield=0.5)], 8, False)
    A['death'] = ([mk(lean=-3, crouch=1.2, wa=30, shield=0.5, lhx=-4, lhy=8),
                   mk(lean=-3.5, crouch=6, rfy=3, rfx=2, wa=10, shield=0.5, lhx=-5, lhy=6),
                   mk(lean=-5, crouch=8, lfy=3, rfy=5, rot=30, rotc=(0, 4), wa=10, shield=0.5, lhx=-6, lhy=4, shx=-1, eyes=0.5),
                   mk(lean=-5, crouch=8, lfy=4, rfy=6, rot=64, rotc=(0, 6), wa=20, shield=0.5, lhx=-6, lhy=2, shx=-2, eyes=0.2),
                   mk(lean=-3, crouch=3, lfy=2, rfy=2, rot=84, rotc=(0, 8), wa=30, shield=0.5, lhx=-7, lhy=-2, shx=-3, shy=-1, eyes=0),
                   mk(lean=-3, crouch=2, lfy=1, rfy=1, rot=88, rotc=(0, 8), wa=30, shield=0.5, lhx=-7, lhy=-3, shx=-3, shy=-1, eyes=0)], 8, False)
    return A


def anim_guardian():
    S = SPECS['guardian']
    A = {}
    base = dict(two=True, wa=135, rhx=7, rhy=14)
    A['idle'] = ([rep(q, **base) for q in idle_poses(4, wa=135, breathe=1.0)], 3, True)
    A['walk'] = ([rep(q, **base) for q in walk_poses(S, stride=5.6, lift=3.0, bounce=1.2, lean=1.2)], 6, True)
    a = [mk(two=True, rhx=6, rhy=2, wa=165, lean=-1.5, crouch=1.0),
         mk(two=True, rhx=4, rhy=-6, wa=190, lean=-2.5, crouch=1.4, rfx=-2, lfx=3),
         mk(two=True, rhx=3, rhy=-12, wa=205, lean=-3.5, crouch=1.8, rfx=-2.5, lfx=3.5),
         mk(two=True, rhx=3, rhy=-15, wa=214, lean=-4.2, crouch=2.0, rfx=-3, lfx=4, eyes=1),
         mk(two=True, rhx=3, rhy=-15, wa=216, lean=-4.5, crouch=2.0, rfx=-3, lfx=4, aura=1),
         mk(two=True, rhx=10, rhy=2, wa=112, lean=2.6, crouch=2.4, rfx=5, lfx=-3.5, aura=1),
         mk(two=True, rhx=14, rhy=14, wa=48, lean=4.4, crouch=3.6, rfx=7, lfx=-4.5, aura=1),
         mk(two=True, rhx=13, rhy=16, wa=36, lean=4.4, crouch=3.6, rfx=7, lfx=-4.5, aura=0.6),
         mk(two=True, rhx=12, rhy=15, wa=40, lean=4.0, crouch=3.2, rfx=6.5, lfx=-4),
         mk(two=True, rhx=10, rhy=13, wa=60, lean=2.8, crouch=2.2, rfx=5, lfx=-3),
         mk(two=True, rhx=8, rhy=14, wa=100, lean=1.2, crouch=1.0, rfx=2.5, lfx=-1)]
    A['attack'] = (a, 9, False, dict(wind=5, act=2, rec=4))
    A['hurt'] = ([rep(base, lean=-2, crouch=1.2, hy=-0.6, eyes=0.4), rep(base, lean=-1.2, crouch=1.6, eyes=0.5)], 6, False)
    A['death'] = ([rep(base, lean=-2.5, crouch=2, wa=120),
                   rep(base, lean=-3.5, crouch=8, lfy=2, rfy=5, wa=90, rhy=10),
                   rep(base, lean=-4, crouch=11, lfy=3, rfy=6, rot=24, rotc=(0, 6), wa=80, shx=-2, eyes=0.4),
                   rep(base, lean=-4, crouch=11, lfy=4, rfy=7, rot=58, rotc=(0, 8), wa=70, shx=-3, eyes=0.2),
                   rep(base, lean=-3, crouch=4, lfy=2, rfy=2, rot=84, rotc=(0, 10), wa=60, shx=-5, shy=-1, eyes=0),
                   rep(base, lean=-3, crouch=3, rot=88, rotc=(0, 10), wa=60, shx=-5, shy=-1, eyes=0)], 7, False)
    return A


def anim_boss():
    S = SPECS['boss']
    A = {}
    base = dict(two=True, wa=150, rhx=10, rhy=26, aura=0.7)
    A['idle'] = ([rep(q, **base) for q in idle_poses(4, wa=150, breathe=1.3)], 3, True)
    A['walk'] = ([rep(q, **base) for q in walk_poses(S, stride=8.5, lift=4.5, bounce=1.6, lean=1.8)], 6, True)
    # golpe pesado: levanta a alabarda atras, desfere diagonal com o corpo
    hs = [mk(two=True, aura=0.8, rhx=8, rhy=6, wa=170, lean=-2.5, crouch=1.5, cape=-3),
          mk(two=True, aura=0.9, rhx=6, rhy=-10, wa=198, lean=-4.5, crouch=2.5, rfx=-3, lfx=4, cape=-5),
          mk(two=True, aura=1.0, rhx=5, rhy=-24, wa=214, lean=-6, crouch=3.5, rfx=-4, lfx=6, cape=-7, hy=-0.6),
          mk(two=True, aura=1.0, rhx=5, rhy=-27, wa=220, lean=-6.4, crouch=3.8, rfx=-4.4, lfx=6.4, cape=-8),
          mk(two=True, aura=1.0, rhx=17, rhy=12, wa=100, lean=5, crouch=5, rfx=9, lfx=-6, cape=6),
          mk(two=True, aura=1.0, rhx=26, rhy=26, wa=58, lean=8, crouch=7, rfx=12, lfx=-8, cape=9),
          mk(two=True, aura=0.8, rhx=25, rhy=28, wa=46, lean=7.5, crouch=7.4, rfx=12, lfx=-8, cape=8),
          mk(two=True, aura=0.7, rhx=22, rhy=26, wa=52, lean=6.0, crouch=6, rfx=10, lfx=-6, cape=5),
          mk(two=True, aura=0.7, rhx=14, rhy=26, wa=96, lean=3, crouch=3, rfx=5, lfx=-3, cape=2)]
    A['strike'] = (hs, 9, False, dict(wind=4, act=2, rec=3))
    # investida: agacha, impulso, corrida, derrapagem
    ch = [mk(two=True, aura=0.9, rhx=14, rhy=22, wa=118, lean=-3, crouch=5, rfx=-2, lfx=5, cape=-3),
          mk(two=True, aura=1.0, rhx=18, rhy=22, wa=108, lean=-5, crouch=8, rfx=-4, lfx=7, cape=-6),
          mk(two=True, aura=1.0, rhx=20, rhy=20, wa=104, lean=-6.5, crouch=10, rfx=-5, lfx=8, cape=-8),
          mk(two=True, aura=1.0, rhx=28, rhy=18, wa=92, lean=10, crouch=8, lfx=-10, rfx=10, lfy=0, rfy=3, cape=10),
          mk(two=True, aura=1.0, rhx=28, rhy=18, wa=92, lean=10, crouch=8, lfx=10, rfx=-9, lfy=3, rfy=0, cape=12),
          mk(two=True, aura=0.8, rhx=24, rhy=22, wa=96, lean=7, crouch=6, lfx=-4, rfx=9, cape=6),
          mk(two=True, aura=0.7, rhx=18, rhy=24, wa=110, lean=3, crouch=4, lfx=-2, rfx=6, cape=2),
          mk(two=True, aura=0.7, rhx=12, rhy=26, wa=140, lean=1, crouch=1.5, cape=0)]
    A['charge'] = (ch, 9, False, dict(wind=3, dash=2, rec=3))
    # golpe de area: ergue a alabarda sobre a cabeca e crava no chao
    sl = [mk(two=True, aura=0.8, rhx=8, rhy=-6, wa=175, lean=-1, crouch=1, cape=-2),
          mk(two=True, aura=0.9, rhx=6, rhy=-22, wa=181, lean=-2.5, crouch=0, cape=-3, hy=-1.0),
          mk(two=True, aura=1.0, rhx=4, rhy=-34, wa=183, lean=-3.5, crouch=-1.0, lfy=0, cape=-4, hy=-1.4),
          mk(two=True, aura=1.0, rhx=4, rhy=-37, wa=184, lean=-3.8, crouch=-1.6, cape=-5, hy=-1.6),
          mk(two=True, aura=1.0, rhx=16, rhy=6, wa=120, lean=4.0, crouch=5, rfx=5, lfx=-4, cape=6),
          mk(two=True, aura=1.0, rhx=24, rhy=34, wa=22, lean=7.5, crouch=9, rfx=10, lfx=-7, cape=9),
          mk(two=True, aura=0.8, rhx=24, rhy=35, wa=18, lean=7.5, crouch=9, rfx=10, lfx=-7, cape=8),
          mk(two=True, aura=0.7, rhx=22, rhy=32, wa=24, lean=6, crouch=7, rfx=8, lfx=-6, cape=5),
          mk(two=True, aura=0.7, rhx=16, rhy=28, wa=60, lean=3, crouch=3, rfx=4, lfx=-3, cape=2)]
    A['slam'] = (sl, 9, False, dict(wind=4, act=2, rec=3))
    A['hurt'] = ([rep(base, lean=-3, crouch=2.5, hy=-0.8, eyes=0.5)], 6, False)
    A['death'] = ([rep(base, lean=-2, crouch=2, wa=130, eyes=0.7),
                   rep(base, lean=-3, crouch=7, lfy=2, rfy=4, wa=110, eyes=0.6),
                   rep(base, lean=-3, crouch=13, lfy=4, rfy=7, wa=95, rhy=18, eyes=0.5, aura=0.8),
                   rep(base, lean=-3, crouch=16, lfy=5, rfy=8, rot=14, rotc=(0, 10), wa=85, rhy=14, eyes=0.4, aura=0.6, shx=-1),
                   rep(base, lean=-4, crouch=16, lfy=6, rfy=9, rot=40, rotc=(0, 12), wa=70, eyes=0.3, aura=0.5, shx=-2),
                   rep(base, lean=-4, crouch=12, lfy=4, rfy=6, rot=70, rotc=(0, 12), wa=60, eyes=0.2, aura=0.4, shx=-4),
                   rep(base, lean=-3, crouch=5, rot=86, rotc=(0, 12), wa=50, eyes=0.1, aura=0.3, shx=-6, shy=-1),
                   rep(base, lean=-3, crouch=3, rot=90, rotc=(0, 12), wa=50, eyes=0.0, aura=0.0, shx=-6, shy=-1)], 7, False)
    return A


def anim_wraith():
    A = {}
    idle = []
    for i in range(6):
        ph = i / 6 * math.tau
        idle.append(mk(bob=math.sin(ph) * 2.2, t=i / 6, cape=0))
    A['idle'] = (idle, 6, True)
    cast = [mk(bob=0, lhy=2, aura=0.0, t=0.0), mk(bob=-1, lhy=8, aura=0.3, t=0.1), mk(bob=-2, lhy=12, aura=0.7, t=0.2),
            mk(bob=-2.5, lhy=14, aura=1.0, t=0.3), mk(bob=-1, lhy=6, aura=0.0, t=0.4), mk(bob=0, lhy=2, aura=0.0, t=0.5), mk(bob=1, lhy=0, aura=0.0, t=0.6)]
    A['cast'] = (cast, 10, False, dict(wind=4, act=1, rec=2))
    A['hurt'] = ([mk(bob=1, px=-2, eyes=0.3, t=0.1), mk(bob=0, px=-1, eyes=0.5, t=0.2)], 8, False)
    A['death'] = ([mk(bob=0, eyes=0.6, t=0.1), mk(bob=2, eyes=0.4, t=0.2, shy=2), mk(bob=4, eyes=0.2, t=0.3, shy=4), mk(bob=6, eyes=0.1, t=0.4, shy=6),
                   mk(bob=8, eyes=0.0, t=0.5, shy=8), mk(bob=10, eyes=0.0, t=0.6, shy=10)], 8, False)
    return A


BUILDERS = {'player': ('characters', anim_player), 'soldier': ('enemies', anim_soldier), 'guardian': ('enemies', anim_guardian),
            'boss': ('bosses', anim_boss), 'wraith': ('enemies', anim_wraith)}


def fade_death(frames, name):
    """Esmaece os ultimos quadros do espectro (dissipa)."""
    out = []
    n = len(frames)
    for i, f in enumerate(frames):
        a = np.array(f)
        k = max(0.0, 1.0 - max(0, i - 1) / (n - 1))
        a[..., 3] = (a[..., 3] * k).astype(np.uint8)
        out.append(Image.fromarray(a, 'RGBA'))
    return out


def build(name, only_anim=None):
    folder, fn = BUILDERS[name]
    S = SPECS[name]
    anims = fn()
    meta = dict(fw=S['W'], fh=S['H'], foot=S['H'] - S['FY'], anims={})
    views = ('front',) if name == 'wraith' else ('front', 'back')
    if name == 'wraith':
        views = ('front', 'back')
    for an, spec in anims.items():
        if only_anim and an not in only_anim:
            continue
        poses, fps, loop = spec[0], spec[1], spec[2]
        phases = spec[3] if len(spec) > 3 else None
        for view in views:
            frames = []
            for ps in poses:
                if name == 'wraith':
                    frames.append(render_wraith(ps, view))
                else:
                    frames.append(render_humanoid(name, ps, view))
            if name == 'wraith' and an == 'death':
                frames = fade_death(frames, name)
            sheet = Image.new('RGBA', (S['W'] * len(frames), S['H']), (0, 0, 0, 0))
            for i, f in enumerate(frames):
                sheet.paste(f, (i * S['W'], 0))
            path = f'assets/{folder}/{name}_{an}_{view}.png'
            sheet.save(path, optimize=True)
        info = dict(frames=len(poses), fps=fps, loop=loop)
        if phases:
            info['phases'] = phases
        meta['anims'][an] = info
    return meta, folder


def main():
    names = [a for a in sys.argv[1:] if a in BUILDERS] or list(BUILDERS)
    path = 'tools/data/actors.json'
    allmeta = json.load(open(path)) if os.path.exists(path) else {}
    for n in names:
        meta, folder = build(n)
        meta['folder'] = folder
        allmeta[n] = meta
        print('ok', n, sum(m['frames'] for m in meta['anims'].values()), 'frames/view')
    json.dump(allmeta, open(path, 'w'), indent=1)


if __name__ == '__main__':
    main()
