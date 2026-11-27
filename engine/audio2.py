import numpy as np, subprocess, json, os
cfg = json.load(open(os.environ['REEL_CFG']))
SR = 48000; T = cfg['T']; N = int(round(T * SR)); beat = T / round(T / (60 / 90))
rng = np.random.default_rng(1)
out = np.zeros((N, 2), np.float32); tt = np.arange(N) / SR
def add(sig, t0, gain=1.0, pan=0.0):
    idx = (np.arange(len(sig)) + int(t0 * SR)) % N
    np.add.at(out[:, 0], idx, sig * gain * np.sqrt(0.5 * (1 - pan))); np.add.at(out[:, 1], idx, sig * gain * np.sqrt(0.5 * (1 + pan)))
def env(n, a, d):
    e = np.ones(n); na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na); return e * np.exp(-np.arange(n) / (d * SR))
drone = np.zeros(N)
for f, g in ((36.71, 0.5), (73.42, 0.35), (110.0, 0.18), (174.61, 0.10), (220.0, 0.06)):
    drone += g * np.sin(2 * np.pi * (round(f * T) / T) * tt + rng.uniform(0, 6))
drone *= 0.75 + 0.25 * np.sin(2 * np.pi * 4 / T * tt)
def kick():
    n = int(0.45 * SR); t = np.arange(n) / SR; f = 42 + 90 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
def hat():
    n = int(0.06 * SR); x = np.diff(np.concatenate([[0], rng.standard_normal(n)])); return x * np.exp(-np.arange(n) / (0.012 * SR)) * 0.5
def bass_note(f, d):
    n = int(d * SR); t = np.arange(n) / SR; s = np.sign(np.sin(2 * np.pi * f * t)) * 0.4 + np.sin(2 * np.pi * f * t)
    return np.convolve(s, np.ones(60) / 60, 'same') * env(n, 0.005, 0.12)
quiet = cfg.get('quiet', [])
def q(t): return any(a <= t < b for a, b in quiet)
K, HH = kick(), hat(); nb = int(round(T / beat))
for b in range(nb):
    t = b * beat
    if q(t): continue
    if b % 2 == 0: add(K, t, 0.55)
    add(HH, t + beat / 2, 0.10, 0.3)
    if b % 4 == 3: add(HH, t + beat * 0.75, 0.06, -0.3)
prog = [73.42, 73.42, 58.27, 65.41]
for b in range(nb * 2):
    t = b * beat / 2
    if not q(t): add(bass_note(prog[(b // 16) % 4], beat / 2), t, 0.10)
def lp_noise(n, c0, c1):
    x = rng.standard_normal(n); y = np.zeros(n); a = 0.0; c = np.linspace(c0, c1, n)
    for i in range(n): a += c[i] * (x[i] - a); y[i] = a
    return y
def whoosh(d=0.6):
    n = int(d * SR); return lp_noise(n, 0.02, 0.35) * np.sin(np.linspace(0, np.pi, n)) ** 2
def impact():
    n = int(1.6 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(35 + 70 * np.exp(-t * 10)) / SR) * np.exp(-t * 2.6) + rng.standard_normal(n) * np.exp(-t * 18) * 0.25
def pop():
    n = int(0.12 * SR); t = np.arange(n) / SR; return np.sin(2 * np.pi * (600 + 900 * np.exp(-t * 40)) * t) * np.exp(-t * 35)
def riser(d):
    n = int(d * SR); t = np.arange(n) / SR
    return (lp_noise(n, 0.01, 0.5) + np.sin(2 * np.pi * np.cumsum(200 + 600 * (t / d) ** 2) / SR) * 0.3) * (t / d) ** 2
W1 = whoosh()
sfx = cfg['sfx']
G = dict({'whoosh': 0.35, 'impact': 0.4, 'pop': 0.22, 'riser': 0.30, 'end_impact': 0.55}, **cfg.get('sfx_gain', {}))
for tc in sfx.get('whoosh', []): add(W1, tc - 0.3, G['whoosh'], rng.uniform(-0.4, 0.4))
for tc in sfx.get('impact', []): add(impact(), tc, G['impact'])
for tc in sfx.get('pop', []): add(pop(), tc, G['pop'], rng.uniform(-0.5, 0.5))
add(riser(1.6), T - 1.7, G['riser']); add(impact(), T - 0.1, G['end_impact'])
voice = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', cfg['audio'], '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout, np.float32)
v = np.zeros(N, np.float32); m = min(N, len(voice)); v[:m] = voice[:m]
fl = int(0.03 * SR); v[N - fl:] *= np.linspace(1, 0, fl)
venv = np.convolve(np.abs(v), np.ones(int(0.15 * SR)) / int(0.15 * SR), 'same')
duck = 1 - 0.45 * np.clip(venv / (venv.max() * 0.35), 0, 1)
music = out.copy(); music[:, 0] += drone * 0.10; music[:, 1] += drone * 0.10; music *= duck[:, None]
mix = music * 0.9 + np.stack([v, v], 1)
mix = np.tanh(mix * 1.1) / np.tanh(1.1); mix /= np.abs(mix).max() / 0.95
mix.astype(np.float32).tofile(cfg['mix']); print('audio ok', T)
