"""Música original (sin licencias de terceros): piano + cuerdas, cálida y emotiva.
Uso: python music_piano.py OUT.f32 DURACION  -> estéreo 48k float32"""
import sys, numpy as np
SR = 48000; out_path = sys.argv[1]; T = float(sys.argv[2]); N = int(T * SR)
rng = np.random.default_rng(7)
L = np.zeros(N); Rr = np.zeros(N)
def add(sig, t0, g=1.0, pan=0.0):
    i0 = int(t0 * SR)
    if i0 >= N: return
    s = sig[:N - i0] * g
    L[i0:i0 + len(s)] += s * np.sqrt(0.5 * (1 - pan)); Rr[i0:i0 + len(s)] += s * np.sqrt(0.5 * (1 + pan))
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def piano(m, d=3.5, vel=0.6):
    n = int(d * SR); t = np.arange(n) / SR; f = hz(m); s = np.zeros(n)
    for k, a in enumerate((1, 0.45, 0.22, 0.12, 0.06, 0.03), 1):
        s += a * np.sin(2 * np.pi * f * k * (1 + 0.0004 * k * k) * t) * np.exp(-t * (0.9 + 0.7 * k) * (f / 400) ** 0.3)
    att = np.minimum(1, t / 0.004); s *= att * vel
    s += rng.standard_normal(n) * np.exp(-t * 90) * 0.02 * vel
    return s
def strings(ms, d, att=1.5, rel=1.8):
    n = int(d * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for m in ms:
        for det in (-0.12, 0.0, 0.11):
            f = hz(m) * 2 ** (det / 12); ph = rng.uniform(0, 6)
            vib = 1 + 0.003 * np.sin(2 * np.pi * 5.2 * t + ph)
            x = 2 * ((f * np.cumsum(vib) / SR + ph) % 1) - 1
            s += x
    k = 220; s = np.convolve(s, np.ones(k) / k, 'same')  # dark low-pass
    env = np.minimum(1, t / att) * np.minimum(1, (d - t) / rel).clip(0, 1)
    return s * env / (len(ms) * 3)
# F - C/E - Dm - Bb (x) ; 2 s por acorde a ~60 bpm
prog = [([41, 53], [65, 69, 72]), ([40, 52], [64, 67, 72]), ([38, 50], [62, 65, 69]), ([34, 46], [62, 65, 70])]
bar = 2.6
t = 0.0; k = 0
while t < T - 1:
    bass, ch = prog[k % 4]
    lvl = 0.55 if t < 7 else 0.7
    add(piano(bass[0], 5, 0.5 * lvl), t, 1, -0.2); add(piano(bass[1], 5, 0.35 * lvl), t + 0.01, 1, -0.1)
    arp = ch + [ch[1] + 12, ch[2] + 12] if t > 6.5 else ch
    for j, m in enumerate(arp):
        add(piano(m, 4, 0.33 * lvl), t + 0.35 + j * (bar - 0.4) / len(arp), 1, 0.25 * ((j % 2) * 2 - 1))
    if t > 6.0:   # cuerdas entran con "una energía diferente"
        g = 0.22 if t < 20 else 0.34
        add(strings([bass[1]] + ch, bar + 1.2), t - 0.2, g, 0.0)
        if t > 20: add(strings([c + 12 for c in ch[1:]], bar + 1.2), t - 0.2, 0.12, 0.3)
    t += bar; k += 1
# final: acorde de F sostenido
add(piano(41, 6, 0.4), T - 5.5); [add(piano(m, 6, 0.28), T - 5.4 + i * 0.12) for i, m in enumerate((65, 69, 72, 77))]
x = np.stack([L, Rr], 1)
# reverb: IR de ruido con caída exponencial
ir_n = int(2.8 * SR); ir = rng.standard_normal((ir_n, 2)) * np.exp(-np.arange(ir_n) / (0.75 * SR))[:, None]
ir[:int(0.02 * SR)] = 0
from numpy.fft import rfft, irfft
nfft = 1 << int(np.ceil(np.log2(N + ir_n)))
wet = np.stack([irfft(rfft(x[:, c], nfft) * rfft(ir[:, c], nfft), nfft)[:N] for c in range(2)], 1)
wet /= np.abs(wet).max() + 1e-9
y = x / (np.abs(x).max() + 1e-9) * 0.7 + wet * 0.45
fade = int(2.5 * SR); y[-fade:] *= np.linspace(1, 0, fade)[:, None]; y[:int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))[:, None]
y = y / np.abs(y).max() * 0.9
y.astype(np.float32).tofile(out_path); print('music ok', T)
