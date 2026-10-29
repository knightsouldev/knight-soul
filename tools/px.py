"""Biblioteca minima de pixel art procedural do Knight Souls (apenas ferramenta de assets)."""
import math
import numpy as np
from PIL import Image, ImageDraw


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def hnoise(x, y, seed=0):
    n = (int(x) * 374761393 + int(y) * 668265263 + int(seed) * 1442695041) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    n ^= n >> 16
    return (n & 0xFFFF) / 65536.0


def vnoise(x, y, seed=0):
    x0, y0 = math.floor(x), math.floor(y)
    fx, fy = x - x0, y - y0
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    a = hnoise(x0, y0, seed)
    b = hnoise(x0 + 1, y0, seed)
    c = hnoise(x0, y0 + 1, seed)
    d = hnoise(x0 + 1, y0 + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(x, y, seed=0, octaves=3):
    v, amp, tot = 0.0, 1.0, 0.0
    for o in range(octaves):
        v += vnoise(x, y, seed + o * 17) * amp
        tot += amp
        x *= 2
        y *= 2
        amp *= 0.5
    return v / tot


# Paleta do jogo
P = dict(
    ink=rgb('0b090c'),
    stone_d=rgb('2a2623'), stone_m=rgb('474039'), stone_l=rgb('6d6354'), stone_w=rgb('8c7a58'),
    mortar=rgb('171413'),
    moss_d=rgb('252d17'), moss_m=rgb('3f4a21'), moss_l=rgb('5f6830'),
    bronze_d=rgb('4a3418'), bronze=rgb('8a6430'), gold=rgb('c49a48'), gold_l=rgb('ecd088'),
    blue_d=rgb('1b3f78'), blue=rgb('4f9bff'), blue_l=rgb('b9e4ff'),
    purple_d=rgb('2f1146'), purple=rgb('7a35b0'), purple_l=rgb('c07cf0'),
    fire_d=rgb('a02a0a'), fire=rgb('f08a1c'), fire_l=rgb('ffd36a'),
    red=rgb('9a1c1c'), red_d=rgb('4a0c10'),
    cloak=rgb('3a4a2a'), cloak_d=rgb('222d19'), cloak_l=rgb('5b6e3c'),
    steel=rgb('8d939c'), steel_d=rgb('4a4f58'), steel_l=rgb('d3d9e0'),
    skin=rgb('d8a888'), skin_d=rgb('a8745a'),
    leather=rgb('4c3322'), leather_d=rgb('2a1c13'),
)


def save(img, path):
    img.save(path, optimize=True)


def iso_uv(x, y, w=64, h=32):
    """Coordenadas locais (u,v) de um pixel dentro do losango w x h; None se fora."""
    dx = (x + 0.5 - w / 2) / (w / 2)
    dy = (y + 0.5 - h / 2) / (h / 2)
    if abs(dx) + abs(dy) > 1.0:
        return None
    return (dx + dy) / 2 + 0.5, (dy - dx) / 2 + 0.5


def shear(img, slope):
    """Cisalha verticalmente: y' = y + slope*x. slope<0 sobe para a direita."""
    w, h = img.size
    extra = int(math.ceil(abs(slope) * w)) + 1
    src = np.array(img)
    dst = np.zeros((h + extra, w, 4), np.uint8)
    for x in range(w):
        off = int(round(slope * x)) if slope >= 0 else int(round(extra + slope * x))
        dst[off:off + h, x] = src[:, x]
    return Image.fromarray(dst, 'RGBA')


class Rig:
    """Tela em alta resolucao (supersample) com partes em cel-shading.
    O resultado e reduzido para pixel art e recebe contorno."""

    def __init__(self, w, h, s=4):
        self.w, self.h, self.s = w, h, s
        self.c = np.zeros((h * s, w * s, 4), np.float32)

    def _mask(self, fn):
        m = Image.new('L', (self.w * self.s, self.h * self.s), 0)
        fn(ImageDraw.Draw(m), self.s)
        return np.array(m) > 127

    def part(self, fn, base, dark=None, light=None, bevel=1.1):
        m = self._mask(fn)
        if not m.any():
            return
        dark = dark or shade(base, 0.58)
        light = light or tuple(min(255, int(v * 1.35 + 14)) for v in base)
        d = max(1, int(round(self.s * bevel)))
        dn = np.zeros_like(m)
        dn[:-d, :-d] = m[d:, d:]
        up = np.zeros_like(m)
        up[d:, d:] = m[:-d, :-d]
        is_dark = m & ~dn
        is_light = m & ~up & ~is_dark
        for mask, col in ((m, base), (is_dark, dark), (is_light, light)):
            self.c[mask] = (*col, 255)

    def flat(self, fn, col, alpha=255):
        m = self._mask(fn)
        self.c[m] = (*col, alpha)

    def detail(self, fn, col, alpha=255):
        m = self._mask(fn) & (self.c[..., 3] > 0)
        a = alpha / 255.0
        for i in range(3):
            self.c[..., i][m] = self.c[..., i][m] * (1 - a) + col[i] * a

    def glow(self, fn, col, alpha=255):
        m = self._mask(fn)
        a = alpha / 255.0
        for i in range(3):
            self.c[..., i][m] = self.c[..., i][m] * (1 - a) + col[i] * a
        self.c[..., 3][m] = np.maximum(self.c[..., 3][m], alpha)

    def rotate(self, deg, cx, cy):
        img = Image.fromarray(self.c.astype(np.uint8), 'RGBA')
        img = img.rotate(deg, resample=Image.BICUBIC, center=(cx * self.s, cy * self.s))
        self.c = np.array(img).astype(np.float32)

    def shift(self, dx, dy):
        img = Image.fromarray(self.c.astype(np.uint8), 'RGBA')
        out = Image.new('RGBA', img.size, (0, 0, 0, 0))
        out.paste(img, (int(dx * self.s), int(dy * self.s)))
        self.c = np.array(out).astype(np.float32)

    def finish(self, outline=True):
        im = Image.fromarray(self.c.astype(np.uint8), 'RGBA')
        im = im.resize((self.w, self.h), Image.BOX)
        a = np.array(im)
        alpha = a[..., 3] > 110
        al = np.maximum(a[..., 3:4].astype(np.float32) / 255.0, 1e-3)
        rgbv = np.clip(a[..., :3].astype(np.float32) / al, 0, 255)
        out = np.zeros((self.h, self.w, 4), np.uint8)
        out[alpha, :3] = rgbv[alpha].astype(np.uint8)
        out[alpha, 3] = 255
        if outline:
            pad = np.pad(alpha, 1)
            nb = pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]
            edge = nb & ~alpha
            padc = np.pad(out[..., :3].astype(np.float32), ((1, 1), (1, 1), (0, 0)))
            neigh = np.maximum.reduce([padc[:-2, 1:-1], padc[2:, 1:-1], padc[1:-1, :-2], padc[1:-1, 2:]])
            col = np.clip(neigh * 0.22 + 6, 0, 255).astype(np.uint8)
            out[edge, :3] = col[edge]
            out[edge, 3] = 255
        return Image.fromarray(out, 'RGBA')


def ell(cx, cy, rx, ry):
    return lambda d, s: d.ellipse([(cx - rx) * s, (cy - ry) * s, (cx + rx) * s, (cy + ry) * s], fill=255)


def poly(pts):
    return lambda d, s: d.polygon([(x * s, y * s) for x, y in pts], fill=255)


def rect(x0, y0, x1, y1):
    return lambda d, s: d.rectangle([x0 * s, y0 * s, x1 * s, y1 * s], fill=255)


def limb(p0, p1, w0, w1=None):
    w1 = w0 if w1 is None else w1

    def fn(d, s):
        x0, y0 = p0
        x1, y1 = p1
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        pts = [((x0 + nx * w0 / 2) * s, (y0 + ny * w0 / 2) * s), ((x1 + nx * w1 / 2) * s, (y1 + ny * w1 / 2) * s),
               ((x1 - nx * w1 / 2) * s, (y1 - ny * w1 / 2) * s), ((x0 - nx * w0 / 2) * s, (y0 - ny * w0 / 2) * s)]
        d.polygon(pts, fill=255)
        d.ellipse([(x0 - w0 / 2) * s, (y0 - w0 / 2) * s, (x0 + w0 / 2) * s, (y0 + w0 / 2) * s], fill=255)
        d.ellipse([(x1 - w1 / 2) * s, (y1 - w1 / 2) * s, (x1 + w1 / 2) * s, (y1 + w1 / 2) * s], fill=255)
    return fn


def line(p0, p1, w):
    return lambda d, s: d.line([(p0[0] * s, p0[1] * s), (p1[0] * s, p1[1] * s)], fill=255, width=max(1, int(w * s)))


def union(*fns):
    def fn(d, s):
        for f in fns:
            f(d, s)
    return fn


def dirv(a):
    """Angulo 'baseado em baixo': 0=baixo, 90=direita, 180=cima."""
    r = math.radians(a)
    return (math.sin(r), math.cos(r))


def ik2(a, target, l1, l2, bend=1):
    """IK de 2 ossos: retorna (articulacao, ponta)."""
    ax, ay = a
    tx, ty = target
    dx, dy = tx - ax, ty - ay
    full = math.hypot(dx, dy)
    d = max(0.001, min(full, l1 + l2 - 0.01))
    base = math.atan2(dy, dx)
    cosang = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    ang = math.acos(max(-1, min(1, cosang)))
    ka = base + bend * ang
    knee = (ax + math.cos(ka) * l1, ay + math.sin(ka) * l1)
    k = d / max(full, 0.001)
    end = (ax + dx * k, ay + dy * k)
    return knee, end
