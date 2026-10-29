"""Sintetiza efeitos sonoros e musica ambiente (numpy). Uso: python3 tools/gen_audio.py"""
import os, subprocess, wave
import numpy as np

SR = 22050
OUT = 'assets/audio'
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)


def t_(d):
    return np.arange(int(SR * d)) / SR


def env(n, a=0.005, r=0.2, curve=2.0):
    e = np.ones(n)
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] = np.minimum(e[-nr:], np.linspace(1, 0, nr) ** curve)
    return e


def decay(n, tau):
    return np.exp(-np.arange(n) / SR / tau)


def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.zeros_like(x)
    p = 0.0
    for i in range(len(x)):
        p = (1 - a) * x[i] + a * p
        y[i] = p
    return y


def lp_fast(x, fc):
    # filtro por FFT (rapido)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / fc) ** 4)
    return np.fft.irfft(X, len(x))


def hp_fast(x, fc):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= (f / fc) ** 4 / (1 + (f / fc) ** 4)
    return np.fft.irfft(X, len(x))


def bp(x, lo, hi):
    return lp_fast(hp_fast(x, lo), hi)


def noise(n):
    return rng.standard_normal(n)


def sine(f, d, ph=0.0):
    t = t_(d)
    return np.sin(2 * np.pi * f * t + ph)


def sine_n(f, n):
    return np.sin(2 * np.pi * f * np.arange(n) / SR)


def sweep(f0, f1, d):
    t = t_(d)
    f = f0 * (f1 / f0) ** (t / d)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def norm(x, peak=0.8):
    m = np.max(np.abs(x)) or 1.0
    return x / m * peak


def reverb(x, wet=0.25, size=1.0):
    out = x.copy()
    for d, g in ((0.029, 0.5), (0.043, 0.4), (0.067, 0.33), (0.101, 0.25), (0.157, 0.18)):
        n = int(d * SR * size)
        out[n:] += x[:-n] * g * wet * 2
    return out


def save_wav(name, x, peak=0.85):
    x = norm(x, peak)
    a = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(f'{OUT}/{name}.wav', 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(a.tobytes())


def pad(x, d):
    n = int(SR * d)
    return np.pad(x, (0, max(0, n - len(x))))[:n]


# ---------------------------------------------------------------- efeitos
def swing(var):
    d = 0.28
    n = int(SR * d)
    x = noise(n)
    f0, f1 = (500, 3000) if var == 0 else (400, 2400)
    # varredura de filtro: soma de bandas
    y = np.zeros(n)
    for i, (lo, hi) in enumerate(((300, 900), (900, 2200), (2200, 5000))):
        band = bp(x, lo, hi)
        c = (i + 1) / 3
        e = np.exp(-((t_(d) - 0.07 - 0.05 * c) ** 2) / (2 * 0.04 ** 2))
        y += band * e * (0.6 + 0.4 * c)
    return y * env(n, 0.01, 0.15)


def hit(heavy=False):
    d = 0.35 if heavy else 0.22
    n = int(SR * d)
    thump = sweep(160 if heavy else 220, 55, d) * decay(n, 0.09 if heavy else 0.05)
    crack = bp(noise(n), 800, 5000) * decay(n, 0.025)
    clang = (sine(1480, d) + 0.6 * sine(2210, d)) * decay(n, 0.04) * 0.25
    return thump * 1.2 + crack * 0.9 + clang


def dodge():
    d = 0.3
    n = int(SR * d)
    x = bp(noise(n), 200, 1800)
    e = np.exp(-((t_(d) - 0.12) ** 2) / (2 * 0.06 ** 2))
    return x * e * 0.9 + sweep(180, 90, d) * 0.15 * decay(n, 0.1)


def hurt():
    d = 0.4
    n = int(SR * d)
    thump = sweep(120, 45, d) * decay(n, 0.1)
    grit = bp(noise(n), 300, 2500) * decay(n, 0.05)
    voice = sweep(300, 170, d) * decay(n, 0.12) * 0.5
    return thump + grit * 0.8 + voice


def heal():
    d = 1.1
    n = int(SR * d)
    y = np.zeros(n)
    for i, f in enumerate((523, 659, 784, 988, 1175)):
        s = int(i * 0.09 * SR)
        seg = sine_n(f, n - s) * decay(n - s, 0.35)
        y[s:] += seg[:n - s] * (0.5 - i * 0.05)
    gl = bp(noise(n), 400, 1200) * decay(n, 0.15) * 0.18        # gole
    return reverb(y + gl, 0.5)


def enemy_die():
    d = 0.9
    n = int(SR * d)
    x = sweep(260, 50, d) * decay(n, 0.25)
    x += lp_fast(noise(n), 900) * decay(n, 0.2) * 0.6
    x += sine(140, d) * decay(n, 0.3) * 0.3
    return reverb(x, 0.3)


def wraith_die():
    d = 1.3
    n = int(SR * d)
    x = (sweep(900, 220, d) + 0.6 * sweep(1350, 330, d)) * decay(n, 0.35) * 0.5
    x += hp_fast(noise(n), 1500) * decay(n, 0.3) * 0.2
    return reverb(x, 0.6)


def boss_telegraph():
    d = 0.9
    n = int(SR * d)
    x = (sweep(70, 140, d) + 0.5 * sweep(105, 210, d)) * np.linspace(0.2, 1, n) ** 1.5
    x += lp_fast(noise(n), 400) * np.linspace(0.1, 0.7, n)
    return x * env(n, 0.05, 0.1)


def boss_slam():
    d = 1.2
    n = int(SR * d)
    x = sweep(110, 32, d) * decay(n, 0.28) * 1.4
    x += lp_fast(noise(n), 1200) * decay(n, 0.2) * 0.9
    x += bp(noise(n), 1500, 6000) * decay(n, 0.04)
    return reverb(x, 0.4)


def boss_charge():
    d = 0.7
    n = int(SR * d)
    x = lp_fast(noise(n), 900) * np.linspace(0.3, 1, n)
    x += sweep(90, 60, d) * 0.6
    return x * env(n, 0.03, 0.2)


def boss_roar():
    d = 2.0
    n = int(SR * d)
    t = t_(d)
    x = np.sin(2 * np.pi * (55 + 12 * np.sin(2 * np.pi * 5 * t)) * t) * 0.8
    x += lp_fast(noise(n), 500) * 0.8
    x += np.sin(2 * np.pi * 110 * t + np.sin(2 * np.pi * 7 * t) * 2) * 0.4
    e = np.minimum(1, t / 0.5) * np.exp(-np.maximum(0, t - 0.9) * 1.8)
    return reverb(x * e, 0.5)


def boss_die():
    d = 3.2
    n = int(SR * d)
    t = t_(d)
    x = sweep(140, 28, d) * decay(n, 0.9) * 1.1
    x += lp_fast(noise(n), 700) * decay(n, 0.7) * 0.7
    x += (np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 466 * t)) * 0.12 * np.exp(-t * 0.9)
    return reverb(x, 0.7, 1.6)


def victory():
    d = 3.8
    n = int(SR * d)
    y = np.zeros(n)
    notes = ((0.0, (220, 330, 440)), (0.9, (247, 370, 494)), (1.8, (262, 392, 523, 659)))
    for st, fs in notes:
        s = int(st * SR)
        for f in fs:
            seg = (sine_n(f, n - s) + 0.3 * sine_n(f * 2, n - s)) * decay(n - s, 1.1)
            y[s:] += seg[:n - s] * 0.2
    return reverb(y, 0.7, 1.8)


def defeat():
    d = 3.0
    n = int(SR * d)
    t = t_(d)
    y = (np.sin(2 * np.pi * 98 * t) + np.sin(2 * np.pi * 103.8 * t) + 0.6 * np.sin(2 * np.pi * 49 * t)) * np.exp(-t * 0.7) * 0.4
    y += lp_fast(noise(n), 300) * np.exp(-t * 1.2) * 0.3
    return reverb(y, 0.8, 1.8)


def pickup():
    d = 0.7
    n = int(SR * d)
    y = (sine(880, d) + sine(1318, d) * 0.6 + sine(1760, d) * 0.3) * decay(n, 0.25) * env(n, 0.005, 0.1)
    return reverb(y, 0.4)


def click():
    d = 0.08
    n = int(SR * d)
    return (sine(600, d) * 0.5 + bp(noise(n), 1000, 4000) * 0.4) * decay(n, 0.02)


def wraith_cast():
    d = 0.7
    n = int(SR * d)
    y = sweep(300, 900, d) * np.linspace(0.2, 1, n) * 0.5 + sweep(450, 1350, d) * np.linspace(0.1, 0.8, n) * 0.3
    return reverb(y * env(n, 0.02, 0.2), 0.5)


def wraith_bolt():
    d = 0.35
    n = int(SR * d)
    return (sweep(900, 400, d) * 0.5 + bp(noise(n), 1500, 5000) * 0.3) * decay(n, 0.12)


def fog_seal():
    d = 1.4
    n = int(SR * d)
    t = t_(d)
    y = lp_fast(noise(n), 700) * np.minimum(1, t / 0.4) * np.exp(-np.maximum(0, t - 0.5) * 2)
    y += sweep(60, 120, d) * 0.5 * decay(n, 0.6)
    return reverb(y, 0.6)


# ---------------------------------------------------------------- musica
def music(name, dur, root, minor_chords, tension=0.0, bell_every=6.0):
    n = int(SR * dur)
    t = t_(dur)
    y = np.zeros(n)
    nch = len(minor_chords)
    seg = dur / nch
    for i, ch in enumerate(minor_chords):
        s0, s1 = int(i * seg * SR), int((i + 1) * seg * SR)
        tt = t[s0:s1] - t[s0]
        e = np.minimum(1, tt / 3.0) * np.minimum(1, (seg - tt) / 3.0)
        # xfade circular: permite loop
        for k, semi in enumerate(ch):
            f = root * 2 ** (semi / 12)
            det = 1 + 0.002 * (k - 1)
            w = np.sin(2 * np.pi * f * det * tt + np.sin(2 * np.pi * 0.1 * tt + k) * 0.8)
            w += 0.5 * np.sin(2 * np.pi * f * 2 * det * tt + 0.5 * np.sin(2 * np.pi * 0.07 * tt))
            w += 0.25 * np.sin(2 * np.pi * f * 3 * det * tt)
            y[s0:s1] += w * e * 0.12
    # pedal grave
    y += np.sin(2 * np.pi * root / 2 * t) * 0.18 * (1 + 0.3 * np.sin(2 * np.pi * 0.05 * t))
    # vento
    wind = lp_fast(noise(n), 500) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t + 1)) * 0.07
    y += wind
    # sinos esparsos
    for b in np.arange(2.0, dur - 3.0, bell_every):
        f = root * 2 ** (rng.choice([12, 15, 19, 24, 22]) / 12)
        s = int(b * SR)
        d = 3.0
        seg_ = (np.sin(2 * np.pi * f * t_(d)) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t_(d))) * decay(int(SR * d), 0.7) * 0.08
        end = min(n, s + len(seg_))
        y[s:end] += seg_[:end - s]
    if tension > 0:
        # pulso de tambor grave
        step = 60 / (70 + 30 * tension)
        for b in np.arange(0, dur - 1, step * 2):
            s = int(b * SR)
            d = 0.5
            k = sweep(90, 38, d) * decay(int(SR * d), 0.12) * 0.55 * tension
            end = min(n, s + len(k))
            y[s:end] += k[:end - s]
    y = reverb(y, 0.35, 1.6)
    # costura de loop: crossfade final -> inicio
    xf = int(SR * 2.5)
    fade = np.linspace(0, 1, xf)
    y[:xf] = y[:xf] * fade + y[-xf:] * (1 - fade)
    y = y[:-xf]
    y = norm(y, 0.55)
    raw = f'{OUT}/_{name}.wav'
    a = (np.clip(y, -1, 1) * 32767).astype(np.int16)
    with wave.open(raw, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(a.tobytes())
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-c:a', 'libvorbis', '-q:a', '2', f'{OUT}/{name}.ogg'], check=True)
    os.remove(raw)


def main():
    sfx = dict(swing_0=swing(0), swing_1=swing(1), hit=hit(False), hit_heavy=hit(True), dodge=dodge(), hurt=hurt(), heal=heal(),
               enemy_die=enemy_die(), wraith_die=wraith_die(), boss_telegraph=boss_telegraph(), boss_slam=boss_slam(),
               boss_charge=boss_charge(), boss_roar=boss_roar(), boss_die=boss_die(), victory=victory(), defeat=defeat(),
               pickup=pickup(), click=click(), wraith_cast=wraith_cast(), wraith_bolt=wraith_bolt(), fog_seal=fog_seal())
    for k, v in sfx.items():
        save_wav(k, v)
    music('ambient', 56, 55.0, [(0, 7, 12), (-2, 5, 10), (-4, 3, 8), (-2, 5, 10)], 0.0, 7.0)
    music('boss', 48, 49.0, [(0, 3, 7, 12), (-4, 3, 8), (-5, 2, 7), (-7, 0, 5)], 0.9, 5.0)
    print('audio ok:', len(sfx), 'sfx + 2 musicas')


if __name__ == '__main__':
    main()
