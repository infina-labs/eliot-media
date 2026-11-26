"""Especial Acción de Gracias — LA ENERGÍA QUE REALMENTE IMPORTA. Uso: python tg.py DIR [stills t..|render|cover]"""
import os, sys, json, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
D = os.path.abspath(sys.argv[1]); ENG = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(ENG, 'assets') + '/'
W, H, FPS = 1080, 1920, 30
Y = (255, 196, 0); GOLD = (198, 154, 84); WH = (255, 255, 255); K = (8, 10, 13)
WD = json.load(open(os.path.join(D, 'a.words.json')))
FIX = {85: 'Eliot', 86: 'Angueira', 92: 'Día', 94: 'Acción', 96: 'Gracias.'}
for i, s in FIX.items(): WD[i][0] = s
def tw(i): return WD[i][1]
SEG = [('c1.mp4', 0, 7.2, 1.0, 0), ('c2.mp4', 0, 7.6, 1.0, 0), ('c3.mp4', 0, 8.0, 1.0, 0), ('c4.mp4', 0, 1.3, 0.45, 0), ('c3.mp4', 0, 8.0, 0.42, 1)]
XF = 0.6
T = sum(s[2] / s[3] if s[3] != 1 else s[2] for s in SEG) - XF * (len(SEG) - 1)
T = round(T, 3)

_fc = {}
def font(kind, size):
    k = (kind, size)
    if k not in _fc:
        if kind.startswith('mont'):
            f = ImageFont.truetype('/usr/share/fonts/truetype/google-fonts/ofl/montserrat/Montserrat[wght].ttf', size)
            try: f.set_variation_by_name({'mont': 'ExtraBold', 'montsb': 'SemiBold', 'montl': 'Light', 'montm': 'Medium'}[kind])
            except Exception: pass
            _fc[k] = f
        else: _fc[k] = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-%s.otf' % kind, size)
    return _fc[k]
def txt(s, kind, size, col=WH, track=0, shadow=True):
    f = font(kind, size); asc, desc = f.getmetrics()
    w = int(f.getlength(s) + track * len(s)) + 40; h = asc + desc + 40
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 20
    if track:
        for ch in s: d.text((x, 20), ch, font=f, fill=col); x += f.getlength(ch) + track
    else: d.text((20, 20), s, font=f, fill=col)
    if shadow:
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel('A').filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.75)))
        out = Image.new('RGBA', im.size, (0, 0, 0, 0)); out.alpha_composite(sh, (0, 3)); out.alpha_composite(im); return out
    return im
def glow(im, r=24, s=0.6, col=Y):
    a = im.getchannel('A').filter(ImageFilter.GaussianBlur(r)).point(lambda v: int(min(255, v * s)))
    g = Image.new('RGBA', im.size, col + (0,)); g.putalpha(a); o = Image.new('RGBA', im.size, (0, 0, 0, 0)); o.alpha_composite(g); o.alpha_composite(im); return o
def place(fr, im, cx, cy, s=1.0, a=1.0):
    if a <= 0.003: return
    if s != 1.0: im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    if a < 1: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    fr.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
def cl(v, a=0, b=1): return max(a, min(b, v))
def pr(t, t0, d): return cl((t - t0) / d)
def eo(p): return 1 - (1 - cl(p)) ** 3
def eio(p): p = cl(p); return 3 * p * p - 2 * p ** 3

# ---------- captions: phrase chunks, word-by-word soft reveal ----------
def chunks():
    out, cur = [], []
    for i, w in enumerate(WD):
        if cur and (w[1] - WD[i - 1][2] > 0.45 or len(cur) >= 6): out.append(cur); cur = []
        cur.append(i)
        if w[0][-1] in ',.': out.append(cur); cur = []
    if cur: out.append(cur)
    res = []
    for k, c in enumerate(out):
        s = WD[c[0]][1] - 0.08; e = (WD[out[k + 1][0]][1] - 0.08) if k + 1 < len(out) else T
        res.append((s, min(e, WD[c[-1]][2] + 0.9), c))
    return res
CH = chunks()
HIDE = [(26.15, 29.45), (29.45, 33.45)]
GOLDW = {'energía', 'energía,', 'hijos,', 'familia,', 'amamos,', 'personas', 'gracias', 'importa.', 'Eliot', 'Angueira'}
def captions(fr, t):
    if any(a <= t < b for a, b in HIDE): return
    for s, e, c in CH:
        if not (s <= t < e): continue
        fa = eo(pr(t, s, 0.25)) * (1 - eo(pr(t, e - 0.25, 0.25)))
        ims = [txt(WD[i][0].strip(','), 'montsb', 56, GOLD if WD[i][0] in GOLDW else WH) for i in c]
        sp = -22; widths = [im.width + sp for im in ims]
        lines = [list(range(len(ims)))]
        if sum(widths) > 900:
            k = min(range(1, len(ims)), key=lambda k: abs(sum(widths[:k]) - sum(widths[k:]))); lines = [list(range(k)), list(range(k, len(ims)))]
        y0 = 1480 - (len(lines) - 1) * 38
        for li, ln in enumerate(lines):
            tw_ = sum(widths[j] for j in ln); x = W / 2 - tw_ / 2
            for j in ln:
                wa = eo(pr(t, WD[c[j]][1] - 0.12, 0.3))
                place(fr, ims[j], x + ims[j].width / 2, y0 + li * 76 + 8 * (1 - wa), 1, fa * (0.25 + 0.75 * wa))
                x += widths[j]
        return

# ---------- overlays ----------
LOGO = Image.open(A + 'logo_full.png').convert('RGBA')
WORDS = [('PRODUCIR', 9), ('ALMACENAR', 10), ('APROVECHAR', 12)]
rng = random.Random(4); DUST = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(2, 7), rng.uniform(0.2, 0.7), rng.uniform(0, 6)) for _ in range(70)]
def dust(fr, t, a):
    if a <= 0: return
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for x, y, r, sp, ph in DUST:
        yy = (y - t * 40 * sp) % H; xx = x + 20 * math.sin(t * 0.5 + ph); al = int(150 * a * (0.5 + 0.5 * math.sin(t * 1.3 + ph)))
        d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(255, 210, 130, al))
    fr.alpha_composite(lay.filter(ImageFilter.GaussianBlur(2)))
def overlay(fr, t):
    # S0 words
    out0 = 1 - eo(pr(t, 6.5, 0.6))
    for k, (wtxt, wi) in enumerate(WORDS):
        p = eo(pr(t, tw(wi) - 0.1, 0.6)) * out0
        if p <= 0: continue
        y = 700 + k * 150
        im = txt(wtxt, 'montsb', 58, WH, track=14); place(fr, im, 540, y + 20 * (1 - p), 1, p)
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ln = 90 * eo(pr(t, tw(wi), 0.7))
        ImageDraw.Draw(lay).line([(540 - ln, y + 52), (540 + ln, y + 52)], fill=Y + (int(255 * p),), width=3); fr.alpha_composite(lay)
    # message on house
    m = eio(pr(t, tw(67) - 0.2, 1.2)) * (1 - eio(pr(t, 29.1, 0.5)))
    if m > 0:
        place(fr, txt('LA VERDADERA ENERGÍA', 'mont', 64, WH, track=3), 540, 520 + 15 * (1 - m), 1, m)
        place(fr, glow(txt('ESTÁ EN LAS PERSONAS', 'mont', 64, GOLD, track=3), 22, 0.5, GOLD), 540, 610 + 15 * (1 - m), 1, eio(pr(t, tw(69), 1.0)) * (1 - eio(pr(t, 29.1, 0.5))))
    # title
    q = eio(pr(t, 29.9, 1.2)) * (1 - eio(pr(t, 33.0, 0.5)))
    if q > 0:
        place(fr, txt('LA ENERGÍA QUE', 'mont', 92, WH, track=int(4 + 6 * q)), 540, 840, 1, q)
        place(fr, glow(txt('REALMENTE IMPORTA', 'mont', 92, Y, track=int(4 + 6 * q)), 30, 0.55), 540, 950, 1, eio(pr(t, tw(82) - 0.1, 1.0)) * (1 - eio(pr(t, 33.0, 0.5))))
    dust(fr, t, eo(pr(t, 29.4, 1.0)))
    # end card
    e = 33.4
    if t >= e:
        place(fr, txt('FELIZ DÍA DE', 'mont', 72, WH, track=4), 540, 440, 1, eo(pr(t, e, 0.9)))
        place(fr, glow(txt('ACCIÓN DE GRACIAS', 'mont', 72, GOLD, track=4), 22, 0.5, GOLD), 540, 530, 1, eo(pr(t, e + 0.3, 0.9)))
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ln = 260 * eo(pr(t, e + 0.6, 1.0))
        ImageDraw.Draw(lay).line([(540 - ln, 615), (540 + ln, 615)], fill=GOLD + (220,), width=2); fr.alpha_composite(lay)
        a1 = txt('ELIOT ', 'mont', 70, WH); a2 = txt('ANGUEIRA', 'mont', 70, Y)
        nm = Image.new('RGBA', (a1.width + a2.width - 40, a1.height), (0, 0, 0, 0)); nm.alpha_composite(a1, (0, 0)); nm.alpha_composite(a2, (a1.width - 40, 0))
        place(fr, nm, 540, 700, 1, eo(pr(t, e + 0.9, 0.9)))
        place(fr, txt('ENERGY ADVISOR', 'Medium', 26, (230, 230, 230), track=10), 540, 772, 1, eo(pr(t, e + 1.1, 0.9)))
        lp = eo(pr(t, e + 1.6, 1.2)); lg = LOGO.resize((500, int(LOGO.height * 500 / LOGO.width)), Image.LANCZOS)
        place(fr, glow(lg, 26, 0.35), 540, 1010, 0.94 + 0.06 * lp, lp)

def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); d = np.sqrt(((xx - 540) / 700) ** 2 + ((yy - 900) / 1150) ** 2)
    a = (np.clip(d - 0.55, 0, 1) * 1.1).clip(0, 0.85)
    im = Image.new('RGBA', (W, H), K + (0,)); im.putalpha(Image.fromarray((a * 255).astype(np.uint8))); return im
VIG = vignette()
def lowgrad():
    a = np.zeros((H, W), np.float32); yy = np.arange(H)[:, None]
    a[:] = np.clip((yy - 1150) / 600, 0, 1) * 0.65
    im = Image.new('RGBA', (W, H), K + (0,)); im.putalpha(Image.fromarray((a * 255).astype(np.uint8))); return im
LOW = lowgrad()
g_rng = np.random.default_rng(2)
GRAIN = [Image.fromarray(g_rng.integers(0, 16, (H // 2, W // 2), dtype=np.uint8)).resize((W, H)) for _ in range(4)]

def compose(base, i):
    t = i / FPS; fr = base.convert('RGBA')
    fr.alpha_composite(VIG); fr.alpha_composite(LOW)
    # darken backdrop for end card
    dk = eo(pr(t, 29.4, 1.0)) * 0.35
    if dk > 0: fr.alpha_composite(Image.new('RGBA', (W, H), K + (int(255 * dk),)))
    overlay(fr, t); captions(fr, t)
    g = Image.new('RGBA', (W, H), (255, 255, 255, 0)); g.putalpha(GRAIN[i % 4]); fr.alpha_composite(g)
    return fr.convert('RGB')

def build_base(out):
    ins, fl = [], []
    for k, (f, ss, dur, sp, blur) in enumerate(SEG):
        ins += ['-ss', str(ss), '-t', str(dur), '-i', os.path.join(D, f)]
        chain = '[%d:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30' % k
        if sp != 1.0: chain += ',setpts=PTS/%s' % sp
        chain += ',eq=saturation=1.06:contrast=1.03,colorbalance=rs=0.03:gs=0.01:bs=-0.03'
        if blur: chain += ',gblur=sigma=28,eq=brightness=-0.05'
        chain += ',format=yuv420p,settb=AVTB[v%d]' % k
        fl.append(chain)
    cur = 'v0'; acc = SEG[0][2] / SEG[0][3]
    for k in range(1, len(SEG)):
        off = acc - XF; nm = 'x%d' % k
        fl.append('[%s][v%d]xfade=transition=fade:duration=%s:offset=%.3f[%s]' % (cur, k, XF, off, nm))
        acc = off + SEG[k][2] / SEG[k][3]; cur = nm
    subprocess.run(['ffmpeg', '-v', 'error', '-y'] + ins + ['-filter_complex', ';'.join(fl), '-map', '[%s]' % cur, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-pix_fmt', 'yuv420p', out], check=True)
    print('base', acc)

def frames(base_path):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', base_path, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    i = 0
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        yield i, Image.frombytes('RGB', (W, H), b); i += 1

def mix(out):
    SR = 48000; N = int(T * SR)
    v = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(D, 'a.mp3'), '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout, np.float32)
    voice = np.zeros(N, np.float32); off = int(0.25 * SR); m = min(N - off, len(v)); voice[off:off + m] = v[:m]
    subprocess.run([sys.executable, os.path.join(ENG, 'music_piano.py'), os.path.join(D, 'music.f32'), str(T)], check=True)
    mus = np.fromfile(os.path.join(D, 'music.f32'), np.float32).reshape(-1, 2)[:N]
    env = np.convolve(np.abs(voice), np.ones(int(0.2 * SR)) / int(0.2 * SR), 'same'); duck = 1 - 0.35 * np.clip(env / (env.max() * 0.3), 0, 1)
    y = mus * 0.42 * duck[:, None] + np.stack([voice, voice], 1) * 1.0
    y = np.tanh(y * 1.05) / np.tanh(1.05); y /= np.abs(y).max() / 0.93
    y.astype(np.float32).tofile(out)

def cover(path):
    # frame from hug clip
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', '5.5', '-i', os.path.join(D, 'c2.mp4'), '-frames:v', '1', '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    fr = Image.frombytes('RGB', (W, H), raw).convert('RGBA'); fr.alpha_composite(VIG)
    a = np.clip((np.arange(H)[:, None] - 700) / 700, 0, 1) * 0.85 + np.zeros((H, W)); a = np.maximum(a, np.clip((420 - np.arange(H)[:, None]) / 420, 0, 1) * 0.5)
    gr = Image.new('RGBA', (W, H), K + (0,)); gr.putalpha(Image.fromarray((a * 255).astype(np.uint8))); fr.alpha_composite(gr)
    d = ImageDraw.Draw(fr); d.rectangle([90, 1040, 190, 1048], fill=Y)
    fr.alpha_composite(txt('FELIZ DÍA DE ACCIÓN DE GRACIAS', 'Bold', 28, GOLD, track=6, shadow=False), (70, 1060))
    y = 1120
    for s, col in (('LA ENERGÍA', WH), ('QUE REALMENTE', WH), ('IMPORTA', Y)):
        im = txt(s, 'mont', 112, col)
        if im.width > 960: im = im.resize((960, int(im.height * 960 / im.width)), Image.LANCZOS)
        if col == Y: im = glow(im, 28, 0.55)
        fr.alpha_composite(im, (70 - (14 if col == Y else 0), y)); y += 122
    d.line([(90, 1560), (990, 1560)], fill=GOLD, width=2)
    a1 = txt('ELIOT ', 'mont', 60, WH, shadow=False); a2 = txt('ANGUEIRA', 'mont', 60, Y, shadow=False)
    fr.alpha_composite(a1, (70, 1580)); fr.alpha_composite(a2, (70 + a1.width - 40, 1580))
    lg = LOGO.resize((260, int(LOGO.height * 260 / LOGO.width)), Image.LANCZOS); fr.alpha_composite(lg, (990 - 260, 1585))
    fr.convert('RGB').save(path, quality=93)

if __name__ == '__main__':
    cmd = sys.argv[2]; base = os.path.join(D, 'base.mp4')
    if cmd == 'base': build_base(base)
    elif cmd == 'stills':
        want = {int(round(float(x) * FPS)) for x in sys.argv[3:]}
        os.makedirs(os.path.join(D, 'stills'), exist_ok=True)
        for i, b in frames(base):
            if i in want: compose(b, i).save(os.path.join(D, 'stills', 's_%05.2f.jpg' % (i / FPS)), quality=85)
            if i > max(want): break
    elif cmd == 'cover': cover(os.path.join(D, 'cover.jpg'))
    elif cmd == 'render':
        mix(os.path.join(D, 'mix.f32'))
        enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', '30', '-i', '-',
                                '-f', 'f32le', '-ar', '48000', '-ac', '2', '-i', os.path.join(D, 'mix.f32'),
                                '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-maxrate', '10M', '-bufsize', '20M', '-pix_fmt', 'yuv420p',
                                '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', os.path.join(D, 'video.tmp.mp4')], stdin=subprocess.PIPE)
        for i, b in frames(base): enc.stdin.write(compose(b, i).tobytes())
        enc.stdin.close()
        if enc.wait() == 0: os.replace(os.path.join(D, 'video.tmp.mp4'), os.path.join(D, 'video.mp4'))
        cover(os.path.join(D, 'cover.jpg')); print('OK', T)
