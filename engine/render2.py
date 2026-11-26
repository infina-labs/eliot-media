import json, math, random, sys, subprocess, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
cfg = json.load(open(os.environ.get('REEL_CFG', '/home/claude/reel/cfg.json')))
T = cfg['T']; NF = int(round(T * FPS))
WD = json.load(open(cfg['words']))
WS = [w[1] for w in WD]
A = '/home/claude/assets/'
Y = (255, 196, 0); YD = (212, 155, 0); K = (8, 10, 13); WH = (255, 255, 255); G = (25, 29, 35)
GR = (150, 156, 168); DIM = (72, 76, 86); RED = (230, 57, 70); LINE = (46, 51, 60)
CX, CY = 540, 790   # visual center

# ---------- fonts / text ----------
_fc = {}
def font(kind, size):
    k = (kind, size)
    if k not in _fc:
        if kind == 'bebas': _fc[k] = ImageFont.truetype(A + 'BebasNeue-Regular.ttf', size)
        else: _fc[k] = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-%s.otf' % kind, size)
    return _fc[k]
_tc = {}
def txt(s, kind, size, color=WH, track=0):
    key = (s, kind, size, color, track)
    if key in _tc: return _tc[key]
    f = font(kind, size)
    l, t, r, b = f.getbbox('ÁÉÍgjQ¿')
    if track == 0:
        w = int(f.getlength(s)) + 8
        im = Image.new('RGBA', (w, b - t + 8), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((4, 4 - t), s, font=f, fill=color)
    else:
        ws = [f.getlength(c) for c in s]; w = int(sum(ws) + track * (len(s) - 1)) + 8
        im = Image.new('RGBA', (w, b - t + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 4
        for c, cw in zip(s, ws): d.text((x, 4 - t), c, font=f, fill=color); x += cw + track
    _tc[key] = im; return im

def glowed(im, r=22, strength=0.8, color=Y):
    pad = r * 2
    base = Image.new('RGBA', (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    a = Image.new('L', base.size, 0); a.paste(im.getchannel('A'), (pad, pad))
    a = a.filter(ImageFilter.GaussianBlur(r)).point(lambda v: min(255, int(v * strength)))
    g = Image.new('RGBA', base.size, color + (0,)); g.putalpha(a); g.alpha_composite(im, (pad, pad))
    return g

def place(fr, im, cx, cy, s=1.0, a=1.0, rot=0.0):
    if a <= 0.004 or s <= 0.01: return
    if abs(s - 1) > 0.003: im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
    if abs(rot) > 0.05: im = im.rotate(rot, Image.BICUBIC, expand=True)
    if a < 0.996: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    x, y = int(round(cx - im.width / 2)), int(round(cy - im.height / 2))
    x0, y0, x1, y1 = max(0, x), max(0, y), min(fr.width, x + im.width), min(fr.height, y + im.height)
    if x1 > x0 and y1 > y0: fr.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))

def cl(v, a=0.0, b=1.0): return max(a, min(b, v))
def eo(p): p = cl(p); return 1 - (1 - p) ** 3
def eio(p): p = cl(p); return 3 * p * p - 2 * p * p * p
def eb(p): p = cl(p); c1 = 1.6; c3 = c1 + 1; return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2
def pr(t, t0, d=0.4): return cl((t - t0) / d)
def lerp(a, b, p): return a + (b - a) * p

# ---------- background ----------
def make_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - 540) / 820) ** 2 + ((yy - 760) / 1050) ** 2)
    f = np.clip(1 - d, 0, 1) ** 1.8
    c0 = np.array(K, np.float32); c1 = np.array([34, 28, 8], np.float32)
    img = c0 + f[..., None] * (c1 - c0)
    v = np.clip(d - 0.7, 0, 1) * 0.8
    img = img * (1 - v[..., None])
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
BG = make_bg()
rng = np.random.default_rng(3)
GRAIN = []
for _ in range(4):
    g = Image.fromarray(rng.integers(0, 14, (H // 2, W // 2), dtype=np.uint8)).resize((W, H))
    gl = Image.new('RGBA', (W, H), (255, 255, 255, 0)); gl.putalpha(g); GRAIN.append(gl)

# ---------- header ----------
def make_header():
    im = Image.new('RGBA', (W, 140), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([60, 30, 104, 34], fill=Y)
    im.alpha_composite(txt('ELIOT ANGUEIRA', 'Bold', 24, (235, 236, 240), track=6), (56, 48))
    im.alpha_composite(txt('EL NEGOCIO DE LA ENERGÍA', 'SemiBold', 19, YD, track=5), (57, 86))
    ep = txt('EP. ' + cfg.get('ep', 'EP.001').split('.')[-1], 'SemiBold', 22, GR, track=4)
    im.alpha_composite(ep, (W - 60 - ep.width, 50))
    return im
HEADER = make_header()

# ---------- isometric ----------
C30, S30 = 0.866, 0.5
def iso(x, y, z, ox, oy, s): return (ox + (x - y) * C30 * s, oy + (x + y) * S30 * s - z * s)
def shade(c, f): return tuple(int(max(0, min(255, v * f))) for v in c)

def draw_box(d, x, y, w, dp, h, base, ox, oy, s, edge=None):
    top = [iso(x, y, h, ox, oy, s), iso(x + w, y, h, ox, oy, s), iso(x + w, y + dp, h, ox, oy, s), iso(x, y + dp, h, ox, oy, s)]
    lf = [iso(x, y + dp, 0, ox, oy, s), iso(x + w, y + dp, 0, ox, oy, s), iso(x + w, y + dp, h, ox, oy, s), iso(x, y + dp, h, ox, oy, s)]
    rf = [iso(x + w, y, 0, ox, oy, s), iso(x + w, y + dp, 0, ox, oy, s), iso(x + w, y + dp, h, ox, oy, s), iso(x + w, y, h, ox, oy, s)]
    d.polygon(lf, fill=shade(base, 0.78)); d.polygon(rf, fill=shade(base, 0.58)); d.polygon(top, fill=shade(base, 1.15))
    if edge:
        for poly in (top, lf, rf): d.line(poly + [poly[0]], fill=edge, width=2)
    return top, lf, rf

# ----- city -----
crng = random.Random(21)
CITY_S = 46
CITY_O = (540, 500)
BLD = []
for gx in range(5):
    for gy in range(5):
        if (gx, gy) in ((0, 4), (4, 0)): continue
        h = crng.choice([2.2, 3.0, 3.8, 4.6, 5.6, 6.8]) * (1.25 if (gx, gy) in ((2, 2), (1, 2), (2, 1)) else 1)
        BLD.append((gx * 1.9, gy * 1.9, 1.35, 1.35, h))
def render_city():
    size = (W, 1100)
    lit = Image.new('RGBA', size, (0, 0, 0, 0)); dark = Image.new('RGBA', size, (0, 0, 0, 0))
    field = Image.new('L', size, 0); glowsrc = Image.new('L', size, 0)
    dl, dd, df, dg = ImageDraw.Draw(lit), ImageDraw.Draw(dark), ImageDraw.Draw(field), ImageDraw.Draw(glowsrc)
    ox, oy, s = CITY_O[0], CITY_O[1] - 60, CITY_S
    # platform
    for D in (dl, dd):
        draw_box(D, -0.8, -0.8, 10.8, 10.8, 0.35, (30, 33, 40), ox, oy, s)
    # streets glow lines
    for k in range(6):
        p0 = iso(-0.5 + k * 1.9 - 0.27, -0.6, 0.36, ox, oy, s); p1 = iso(-0.5 + k * 1.9 - 0.27, 10.0, 0.36, ox, oy, s)
        dl.line([p0, p1], fill=(90, 70, 10), width=2); dd.line([p0, p1], fill=(40, 42, 48), width=2)
        q0 = iso(-0.6, -0.5 + k * 1.9 - 0.27, 0.36, ox, oy, s); q1 = iso(10.0, -0.5 + k * 1.9 - 0.27, 0.36, ox, oy, s)
        dl.line([q0, q1], fill=(90, 70, 10), width=2); dd.line([q0, q1], fill=(40, 42, 48), width=2)
    order = sorted(BLD, key=lambda b: b[0] + b[1])
    for (x, y, w, dp, h) in order:
        z0 = 0.35
        for D, base in ((dl, (40, 44, 54)), (dd, (32, 35, 43))):
            top, lf, rf = draw_box(D, x, y, w, dp, h + z0, base, ox, oy, s)
        xn = (iso(x, y, 0, ox, oy, s)[0]) / W
        # windows on +y face (along x) and +x face (along y)
        rows = int(h / 0.55)
        for face in (0, 1):
            for r in range(rows):
                for c in range(3):
                    if crng.random() < 0.35: continue
                    za = z0 + 0.35 + r * 0.55; zb = za + 0.3
                    ua = 0.15 + c * 0.42; ub = ua + 0.26
                    if face == 0:
                        q = [iso(x + ua, y + dp, za, ox, oy, s), iso(x + ub, y + dp, za, ox, oy, s), iso(x + ub, y + dp, zb, ox, oy, s), iso(x + ua, y + dp, zb, ox, oy, s)]
                    else:
                        q = [iso(x + w, y + ua, za, ox, oy, s), iso(x + w, y + ub, za, ox, oy, s), iso(x + w, y + ub, zb, ox, oy, s), iso(x + w, y + ua, zb, ox, oy, s)]
                    br = crng.uniform(0.75, 1.0) * (1 if face == 0 else 0.8)
                    dl.polygon(q, fill=shade(Y, br)); dd.polygon(q, fill=(26, 28, 34))
                    v = int(255 * cl(0.72 * xn + 0.28 * crng.random()))
                    df.polygon(q, fill=max(1, v)); dg.polygon(q, fill=255)
    glow = glowsrc.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(min(255, v * 0.55)))
    gl = Image.new('RGBA', size, Y + (0,)); gl.putalpha(glow)
    glow2 = glowsrc.filter(ImageFilter.GaussianBlur(80)).point(lambda v: int(min(255, v * 0.45)))
    gl2 = Image.new('RGBA', size, (255, 170, 0, 0)); gl2.putalpha(glow2)
    return lit, dark, field, gl, gl2
CITY_LIT, CITY_DARK, CITY_FIELD, CITY_GLOW, CITY_GLOW2 = render_city()

def city_frame(level, flick_seed):
    """level: 1=all lit, 0=all dark; windows switch by field threshold with flicker band."""
    thr = (1 - level) * 1.08 - 0.04
    band = 0.05
    fs = flick_seed % 2
    lut = []
    for v in range(256):
        if v == 0: lut.append(0); continue
        f = v / 255
        if f > thr + band: lut.append(255)
        elif f > thr - band: lut.append(255 if fs else 40)
        else: lut.append(0)
    m = CITY_FIELD.point(lut)
    im = CITY_DARK.copy()
    lw = CITY_LIT.copy(); lw.putalpha(Image.composite(CITY_LIT.getchannel('A'), Image.new('L', lw.size, 0), m))
    im.alpha_composite(lw)
    lay = Image.new('RGBA', im.size, (0, 0, 0, 0))
    g2 = CITY_GLOW2.copy(); g2.putalpha(g2.getchannel('A').point(lambda v: int(v * level))); lay.alpha_composite(g2)
    g = CITY_GLOW.copy(); g.putalpha(Image.composite(g.getchannel('A'), Image.new('L', g.size, 0), m.filter(ImageFilter.MaxFilter(9))));
    lay.alpha_composite(im)
    return lay

# ----- objects (beat B) -----
def obj_fridge():
    im = Image.new('RGBA', (600, 640), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ox, oy, s = 300, 470, 120
    draw_box(d, 0, 0, 1.6, 1.4, 3.2, (205, 210, 218), ox, oy, s)
    # door seam & handles on +y face
    a = iso(0, 1.4, 2.15, ox, oy, s); b = iso(1.6, 1.4, 2.15, ox, oy, s); d.line([a, b], fill=(120, 126, 136), width=5)
    d.line([iso(0.2, 1.4, 2.4, ox, oy, s), iso(0.2, 1.4, 2.95, ox, oy, s)], fill=Y, width=12)
    d.line([iso(0.2, 1.4, 1.2, ox, oy, s), iso(0.2, 1.4, 1.9, ox, oy, s)], fill=Y, width=12)
    # snowflake-ish dots fading (food spoiling)
    return im
def obj_store():
    im = Image.new('RGBA', (640, 620), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ox, oy, s = 330, 430, 110
    draw_box(d, 0, 0, 2.6, 1.8, 2.1, (58, 63, 74), ox, oy, s)
    # awning stripes on +y face
    for i in range(6):
        x0 = i * 2.6 / 6; x1 = x0 + 2.6 / 6
        q = [iso(x0, 1.8, 2.0, ox, oy, s), iso(x1, 1.8, 2.0, ox, oy, s), iso(x1, 2.3, 1.55, ox, oy, s), iso(x0, 2.3, 1.55, ox, oy, s)]
        d.polygon(q, fill=Y if i % 2 == 0 else (240, 240, 240))
    # door & window
    d.polygon([iso(0.3, 1.8, 0, ox, oy, s), iso(1.0, 1.8, 0, ox, oy, s), iso(1.0, 1.8, 1.3, ox, oy, s), iso(0.3, 1.8, 1.3, ox, oy, s)], fill=(20, 22, 27))
    d.polygon([iso(1.3, 1.8, 0.5, ox, oy, s), iso(2.35, 1.8, 0.5, ox, oy, s), iso(2.35, 1.8, 1.3, ox, oy, s), iso(1.3, 1.8, 1.3, ox, oy, s)], fill=(30, 34, 42))
    # CERRADO sign
    sg = Image.new('RGBA', (230, 70), (0, 0, 0, 0)); sd = ImageDraw.Draw(sg)
    sd.rounded_rectangle([0, 0, 229, 69], 10, fill=RED); sd.text((115, 36), 'CERRADO', font=font('Black', 36), fill=WH, anchor='mm')
    sg = sg.transform(sg.size, Image.AFFINE, (1, 0, 0, -0.5774 * 0, 1, 0))
    sk = sg.rotate(0, expand=True)
    p = iso(1.82, 1.8, 0.95, ox, oy, s)
    shear = sg.transform((230, 70 + 133), Image.AFFINE, (1, 0, 0, -0.5774, 1, 0), Image.BICUBIC)
    im.alpha_composite(shear, (int(p[0] - 115), int(p[1] - 100)))
    return im
def obj_calendar():
    im = Image.new('RGBA', (560, 560), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([60, 70, 500, 510], 28, fill=(232, 234, 238))
    d.rounded_rectangle([60, 70, 500, 170], 28, fill=Y); d.rectangle([60, 140, 500, 170], fill=Y)
    for x in (160, 400): d.rounded_rectangle([x - 14, 40, x + 14, 110], 10, fill=(60, 64, 74))
    d.text((280, 122), 'REUNIONES', font=font('Black', 40), fill=K, anchor='mm')
    for r in range(4):
        for c in range(5):
            x = 100 + c * 78; y = 205 + r * 72
            d.rounded_rectangle([x, y, x + 58, y + 50], 8, fill=(205, 208, 214))
    return im
def stamp(word, color=RED, size=110):
    f = font('Black', size); w = int(f.getlength(word)) + 60
    im = Image.new('RGBA', (w, size + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([6, 6, w - 6, size + 54], 14, outline=color, width=10)
    d.text((w // 2, (size + 60) // 2), word, font=f, fill=color, anchor='mm')
    a = np.asarray(im.getchannel('A')).astype(np.float32)
    nz = np.random.default_rng(5).random(a.shape)
    a = a * np.where(nz < 0.12, 0.25, 1.0)
    im.putalpha(Image.fromarray(a.astype(np.uint8)))
    return im
OBJ = [obj_fridge(), obj_calendar(), obj_store()]
ST_CANCEL = stamp('CANCELADO', size=72)
NEG = txt('−$', 'Black', 54, RED)

# ----- PR dotted map -----
PR = [(-67.27, 18.37), (-67.15, 18.50), (-66.9, 18.49), (-66.6, 18.48), (-66.3, 18.47), (-66.0, 18.45), (-65.75, 18.40),
      (-65.62, 18.30), (-65.65, 18.15), (-65.85, 18.0), (-66.15, 17.95), (-66.4, 17.96), (-66.7, 17.97), (-67.0, 17.97),
      (-67.2, 18.02), (-67.22, 18.15)]
def pr_dots():
    lon0, lon1, lat0, lat1 = -67.3, -65.6, 17.92, 18.53
    sx = 940 / (lon1 - lon0); sy = sx / math.cos(math.radians(18.2))
    poly = [((lo - lon0) * sx + 70, (lat1 - la) * sy) for lo, la in PR]
    m = Image.new('L', (1080, 600), 0); ImageDraw.Draw(m).polygon(poly, fill=255)
    ma = np.asarray(m)
    pts = []; r = random.Random(4)
    for y in range(4, ma.shape[0], 15):
        for x in range(4, 1080, 15):
            if ma[y, x]: pts.append((x, y, r.random()))
    return pts, int((lat1 - lat0) * sy)
PRD, PRH = pr_dots()

# ----- line icons -----
def bolt_pts(cx, cy, s):
    p = [(0.15, -1), (-0.55, 0.12), (-0.05, 0.12), (-0.25, 1), (0.55, -0.2), (0.05, -0.2), (0.3, -1)]
    return [(cx + x * s, cy + y * s) for x, y in p]
def licon(name, sz=96, col=WH):
    im = Image.new('RGBA', (220, 220), (0, 0, 0, 0)); d = ImageDraw.Draw(im); w = 10
    if name == 'gen':
        d.rounded_rectangle([30, 65, 190, 175], 14, outline=col, width=w); d.ellipse([52, 88, 116, 152], outline=col, width=8)
        d.polygon(bolt_pts(152, 120, 30), fill=Y)
    elif name == 'fuel':
        d.rounded_rectangle([50, 35, 140, 190], 12, outline=col, width=w); d.rectangle([68, 55, 122, 95], fill=Y)
        d.line([(140, 80), (175, 100), (175, 165), (160, 180)], fill=col, width=w)
    elif name == 'batt':
        d.rounded_rectangle([50, 50, 170, 190], 14, outline=col, width=w); d.rectangle([88, 28, 132, 50], fill=col)
        d.polygon(bolt_pts(110, 120, 44), fill=Y)
    elif name == 'wrench':
        d.line([(60, 165), (140, 85)], fill=col, width=20); d.ellipse([118, 38, 188, 108], outline=col, width=13)
        d.rectangle([150, 30, 200, 66], fill=(0, 0, 0, 0)); d.ellipse([42, 148, 78, 184], fill=Y)
    elif name == 'panel':
        d.polygon([(45, 70), (175, 70), (192, 155), (28, 155)], outline=col, width=8)
        for i in range(1, 4): d.line([(45 + i * 32.5, 70), (28 + i * 41, 155)], fill=col, width=5)
        d.line([(36, 112), (184, 112)], fill=col, width=5); d.line([(110, 155), (110, 190)], fill=col, width=w)
        d.ellipse([160, 18, 204, 62], fill=Y)
    elif name == 'siren':
        d.pieslice([55, 60, 165, 170], 180, 360, fill=Y); d.rectangle([55, 115, 165, 150], fill=Y); d.rectangle([40, 150, 180, 180], fill=col)
        for a in (-50, -90, -130):
            r = math.radians(a); d.line([(110 + 70 * math.cos(r), 108 + 70 * math.sin(r)), (110 + 95 * math.cos(r), 108 + 95 * math.sin(r))], fill=col, width=8)
    elif name == 'bulb':
        d.ellipse([55, 25, 165, 135], outline=Y, width=w); d.rectangle([85, 135, 135, 170], outline=Y, width=8)
        d.line([(92, 185), (128, 185)], fill=Y, width=8); d.line([(110, 60), (110, 105)], fill=Y, width=8)
    return im.resize((sz, sz), Image.LANCZOS)

def node_img(icon, label, r=74):
    im = Image.new('RGBA', (340, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([170 - r, 80 - r + 10, 170 + r, 80 + r + 10], fill=(16, 18, 22), outline=Y, width=4)
    im.alpha_composite(licon(icon, 92), (170 - 46, 90 - 46))
    lb = txt(label, 'Bold', 24, WH, track=3); im.alpha_composite(lb, (170 - lb.width // 2, 185))
    return im
NODES = [('gen', 'GENERADORES'), ('fuel', 'COMBUSTIBLE'), ('batt', 'BATERÍAS'), ('wrench', 'REPARACIONES'), ('panel', 'SISTEMAS SOLARES'), ('siren', 'EMERGENCIAS')]
NODE_IM = [node_img(i, l) for i, l in NODES]
def hub_img():
    im = Image.new('RGBA', (260, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([20, 20, 240, 240], fill=(255, 196, 0, 255))
    d.polygon(bolt_pts(130, 112, 62), fill=K)
    d.text((130, 200), 'APAGÓN', font=font('Black', 30), fill=K, anchor='mm')
    return glowed(im, 30, 0.7)
HUB = hub_img()

def card(w, h, outline=LINE, fill=(17, 19, 24, 235), r=26, ow=2):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ImageDraw.Draw(im).rounded_rectangle([1, 1, w - 2, h - 2], r, fill=fill, outline=outline, width=ow)
    return im
def label(s, col=GR): return txt(s, 'Bold', 21, col, track=4)

def person(col):
    im = Image.new('RGBA', (40, 52), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([12, 2, 28, 18], fill=col); d.rounded_rectangle([5, 21, 35, 50], 12, fill=col)
    return im
P_DIM, P_ON = person((96, 100, 112)), person((235, 236, 240))

# ---------- captions ----------
KEY = {'DINERO', 'LUZ', 'PIERDES', 'ECONOMÍA', 'APAGONES', 'OPORTUNIDAD', 'IMPORTANTE', 'IMPREDECIBLES', 'ENTENDER', 'NEGOCIO', 'PREGUNTARTE', 'PUERTO', 'RICO'}
def chunks():
    out = []; cur = []
    for i, w in enumerate(WD):
        if cur and (w[1] - WD[i - 1][2] > 0.35): out.append(cur); cur = []
        cur.append(i)
        if len(cur) >= 4 or w[0][-1] in ',.?:': out.append(cur); cur = []
    if cur: out.append(cur)
    res = []
    for k, c in enumerate(out):
        s = WD[c[0]][1]; e = WD[out[k + 1][0]][1] if k + 1 < len(out) else T
        e = min(e, WD[c[-1]][2] + 0.7)
        res.append((s, e, c))
    return res
CH = chunks()
def wtext(i): return WD[i][0].upper().strip(',.?:¿')
def draw_caps(fr, t):
    for s, e, c in CH:
        if not (s - 0.02 <= t < e): continue
        fa = eo(pr(t, s, 0.12)) * (1 - eo(pr(t, e - 0.1, 0.1)))
        items = []
        for i in c:
            wd = wtext(i); on = t >= WD[i][1]
            col = (Y if wd in KEY else WH) if on else DIM
            items.append(txt(wd, 'Black', 76, col))
        gap = 22
        widths = [im.width for im in items]
        lines = [list(range(len(items)))]
        if sum(widths) + gap * (len(items) - 1) > 940 and len(items) > 1:
            best = None
            for k in range(1, len(items)):
                a = sum(widths[:k]); b = sum(widths[k:]); d_ = abs(a - b)
                if best is None or d_ < best[0]: best = (d_, k)
            lines = [list(range(best[1])), list(range(best[1], len(items)))]
        y0 = 1350 if len(lines) == 1 else 1310
        for li, ln in enumerate(lines):
            tw = sum(widths[j] for j in ln) + gap * (len(ln) - 1)
            ls = min(1.0, 960 / tw); x = W / 2 - tw * ls / 2
            for j in ln:
                im = items[j]; on = t >= WD[c[j]][1]
                pop = 1 + 0.06 * (1 - eo(pr(t, WD[c[j]][1], 0.18))) if on else 1
                place(fr, im, x + im.width * ls / 2, y0 + li * 88 + 10 * (1 - fa), pop * ls, fa)
                x += (im.width + gap) * ls
        return

# ---------- beats ----------
def W_(i): return WS[i]
B = [0, W_(12), W_(28), W_(36), W_(45), W_(58), W_(64), W_(81), W_(96), T]

def beat_city_intro(t, L):  # 0 -> W12
    lvl = 1 - eio(pr(t, W_(11) + 0.05, 0.75))
    sc = 1.0 + 0.07 * eio(t / W_(11)) if t < W_(11) else 1.07 + 0.02 * eio(pr(t, W_(11), 0.9))
    shake = 4 * math.sin(t * 70) * (1 - pr(t, W_(11) + 0.05, 0.35)) if t > W_(11) else 0
    place(L, city_frame(lvl, int(t * 24)), CX + shake, 820, sc)

def beat_losses(t, L):  # W12 -> W28
    ts = [W_(12) + 0.25, W_(20), W_(24)]
    slots = [(230, 760), (540, 760), (850, 760)]
    for k, (im, t0) in enumerate(zip(OBJ, ts)):
        p = pr(t, t0 - 0.2, 0.45)
        if p <= 0: continue
        nxt = ts[k + 1] if k < 2 else W_(27) - 0.1
        q = eio(pr(t, nxt - 0.15, 0.5))
        x = lerp(CX, slots[k][0], q); y = lerp(800, slots[k][1], q); s = lerp(1.0, 0.5, q) * (0.88 + 0.12 * eb(p))
        place(L, im, x, y + 40 * (1 - eo(p)), s, eo(p))
        if k == 1:
            sp = pr(t, W_(21) + 0.1, 0.22)
            if sp > 0: place(L, ST_CANCEL, x, y + 40 * s, s * (1.7 - 0.7 * eo(sp)), cl(sp * 2), rot=-14)
        # money draining tags
        dt = t - (t0 + 0.4)
        if dt > 0:
            for j in range(3):
                ph = (dt * 0.8 + j / 3) % 1
                place(L, NEG, x + (j - 1) * 70 * s, y - 220 * s - ph * 160 * s, s * 0.9, (1 - ph) * cl(dt * 2) * 0.9)
    # title strip
    p = pr(t, W_(12) + 0.1, 0.5)
    place(L, label('LO QUE PIERDES DURANTE UN APAGÓN', GR), CX, 430, 1, eo(p))

def beat_economy(t, L):  # W28 -> W36
    ox, oy = 0, 820 - PRH // 2
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    reveal = eo(pr(t, W_(28) - 0.1, 0.8))
    for (x, y, r) in PRD:
        if (x / W) > reveal * 1.2: continue
        lit = r < 0.14
        tw = 0.6 + 0.4 * math.sin(t * 3 + r * 40)
        col = (Y + (int(255 * tw),)) if lit else (70, 74, 84, 255)
        rad = 4 if lit else 3
        d.ellipse([ox + x - rad, oy + y - rad, ox + x + rad, oy + y + rad], fill=col)
    L.alpha_composite(lay)
    place(L, label('PUERTO RICO', GR), CX, oy + PRH + 40, 1, reveal)
    # arcs to money targets
    arng = random.Random(9)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k in range(9):
        sx, sy, _ = PRD[arng.randrange(len(PRD))]; sx += ox; sy += oy
        tx = 140 + k * 100 + arng.uniform(-20, 20); ty = 420 + arng.uniform(-30, 40)
        t0 = W_(30) + k * 0.22
        p = eo(pr(t, t0, 0.7))
        if p <= 0: continue
        mx, my = (sx + tx) / 2, min(sy, ty) - 120
        pts = []
        for i in range(int(30 * p) + 1):
            u = i / 30; pts.append(((1 - u) ** 2 * sx + 2 * (1 - u) * u * mx + u * u * tx, (1 - u) ** 2 * sy + 2 * (1 - u) * u * my + u * u * ty))
        if len(pts) > 1: d.line(pts, fill=Y + (200,), width=3)
        hx, hy = pts[-1]; d.ellipse([hx - 7, hy - 7, hx + 7, hy + 7], fill=WH)
        if p >= 1:
            cp = eb(pr(t, t0 + 0.7, 0.3))
            r = 26 * cp; d.ellipse([tx - r, ty - r, tx + r, ty + r], fill=Y)
            if cp > 0.6: d.text((tx, ty), '$', font=font('Black', 30), fill=K, anchor='mm')
    L.alpha_composite(lay)
    # pulse ring at "apagones"
    rp = pr(t, W_(35), 0.9)
    if 0 < rp < 1:
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); R = 60 + 600 * eo(rp)
        d.ellipse([CX - R, 820 - R * 0.45, CX + R, 820 + R * 0.45], outline=Y + (int(200 * (1 - rp)),), width=4); L.alpha_composite(lay)

def beat_network(t, L):  # W36 -> W45
    hub = (CX, 790); R = (330, 300)
    angs = [-150, -30, 180, 0, 150, 30]
    pos = [(hub[0] + R[0] * math.cos(math.radians(a)), hub[1] + R[1] * math.sin(math.radians(a)) * 1.25) for a in angs]
    ts = [W_(36), W_(37), W_(38), W_(39), W_(40), W_(42)]
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for (px, py), t0 in zip(pos, ts):
        p = eo(pr(t, t0 - 0.15, 0.4))
        if p <= 0: continue
        ex, ey = lerp(hub[0], px, p), lerp(hub[1], py, p)
        d.line([hub, (ex, ey)], fill=Y + (150,), width=3)
        for j in range(2):
            u = ((t * 0.9) + j * 0.5 + t0) % 1
            qx, qy = lerp(hub[0], ex, u), lerp(hub[1], ey, u)
            d.ellipse([qx - 6, qy - 6, qx + 6, qy + 6], fill=WH + (230,))
    L.alpha_composite(lay)
    hp = eb(pr(t, W_(36) - 0.3, 0.45))
    place(L, HUB, hub[0], hub[1], hp * (1 + 0.03 * math.sin(t * 5)))
    for (px, py), t0, im in zip(pos, ts, NODE_IM):
        p = pr(t, t0 - 0.1, 0.4)
        if p > 0: place(L, im, px, py + 20, 0.6 + 0.4 * eb(p), cl(p * 2))

def beat_opportunity(t, L):  # W45 -> W58
    up = eio(pr(t, W_(51), 0.6))
    gy = lerp(600, 470, up); gs = lerp(1.0, 0.72, up)
    place(L, label('MILLONES DE PERSONAS', GR), CX, gy - 205 * gs, 1, eo(pr(t, W_(45), 0.4)) * (1 - up))
    cols, rows, sp = 13, 5, 62
    for r in range(rows):
        for c in range(cols):
            i = r * cols + c
            p = pr(t, W_(45) + 0.1 + i * 0.015, 0.25)
            if p <= 0: continue
            x = CX + (c - (cols - 1) / 2) * sp * gs; y = gy + (r - (rows - 1) / 2) * 66 * gs
            place(L, P_DIM, x, y, gs * (0.6 + 0.4 * eb(p)), cl(p * 2) * (1 - 0.4 * up))
    cp = pr(t, W_(52) - 0.1, 0.5)
    if cp > 0:
        cy = 1010 + 60 * (1 - eo(cp))
        place(L, card(880, 420, outline=YD, ow=2), CX, cy, 1, eo(cp))
        place(L, label('● OPORTUNIDAD COMERCIAL', Y), CX - 440 + 30 + label('● OPORTUNIDAD COMERCIAL', Y).width / 2, cy - 170, 1, eo(cp))
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        hs = [70, 95, 88, 130, 150, 185, 230]
        bp = pr(t, W_(53), 1.3)
        for i, h in enumerate(hs):
            pp = eo(cl(bp * 1.7 - i * 0.1)); x = CX - 300 + i * 100
            d.rounded_rectangle([x - 30, cy + 160 - h * pp, x + 30, cy + 160], 6, fill=(Y if i == 6 else (120, 92, 10)) + (int(255 * eo(cp)),))
        if bp > 0.5:
            lp = eo(pr(t, W_(53) + 0.6, 0.8)); pts = [(CX - 300 + i * 100, cy + 160 - hs[i] - 30) for i in range(7)]
            n = 1 + int(lp * 6); dd = pts[:n + 1]
            d.line(dd, fill=WH + (230,), width=4)
            d.ellipse([dd[-1][0] - 9, dd[-1][1] - 9, dd[-1][0] + 9, dd[-1][1] + 9], fill=WH)
        L.alpha_composite(lay)

def beat_focus(t, L):  # W58 -> W64
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k in range(4):
        ph = ((t - W_(58)) * 0.55 + k / 4) % 1
        R = 40 + 420 * ph
        d.ellipse([CX - R, CY - R, CX + R, CY + R], outline=Y + (int(150 * (1 - ph)),), width=3)
    L.alpha_composite(lay)
    p = eb(pr(t, W_(58), 0.4)); pulse = 1 + 0.15 * max(0, math.sin((t - W_(63)) * 8)) * (t > W_(63))
    dot = Image.new('RGBA', (120, 120), (0, 0, 0, 0)); ImageDraw.Draw(dot).ellipse([30, 30, 90, 90], fill=Y)
    place(L, glowed(dot, 26, 1.0), CX, CY, p * pulse)

BILL = [0.45, 0.52, 0.40, 0.70, 0.62, 0.88, 0.55, 0.95, 0.66, 0.80, 0.50, 1.0]
GAUGE = None
def gauge_img():
    im = Image.new('RGBA', (300, 170), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i in range(60):
        a0 = 180 + i * 3; f = i / 59
        col = (int(lerp(230, 255, min(1, f * 2))), int(lerp(57, 196, min(1, f * 2))), int(lerp(70, 0, min(1, f * 2)))) if f < 0.5 else (int(lerp(255, 46, (f - 0.5) * 2)), int(lerp(196, 190, (f - 0.5) * 2)), int(lerp(0, 120, (f - 0.5) * 2)))
        d.arc([20, 20, 280, 280], a0, a0 + 3.4, fill=col, width=22)
    return im
def beat_bill(t, L):  # W64 -> W81
    t0 = W_(64)
    p0 = eo(pr(t, t0 - 0.1, 0.45))
    place(L, txt('TU FACTURA DE LUZ', 'Black', 46, WH), CX, 380, 1, p0)
    pill = Image.new('RGBA', (430, 44), (0, 0, 0, 0)); ImageDraw.Draw(pill).rounded_rectangle([1, 1, 428, 42], 21, outline=YD, width=2)
    pl = txt('EJEMPLO ILUSTRATIVO', 'Bold', 19, YD, track=4); pill.alpha_composite(pl, (215 - pl.width // 2, 22 - pl.height // 2))
    place(L, pill, CX, 440, 1, p0)
    # main chart card
    c1 = pr(t, t0 + 0.2, 0.45)
    if c1 > 0:
        cy = 660 + 40 * (1 - eo(c1)); a = eo(c1)
        place(L, card(940, 330), CX, cy, 1, a)
        lb = label('● CONSUMO MENSUAL', Y); place(L, lb, 70 + 30 + lb.width / 2, cy - 130, 1, a)
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        x0, x1, yb, yt = 120, 960, cy + 130, cy - 90
        pts = [(x0 + (x1 - x0) * i / 11, yb - (yb - yt) * v) for i, v in enumerate(BILL)]
        lp = pr(t, t0 + 0.5, 3.6); n = lp * 11; k = int(n)
        dd = pts[:k + 1]
        if k < 11: f = n - k; dd = dd + [(lerp(pts[k][0], pts[k + 1][0], f), lerp(pts[k][1], pts[k + 1][1], f))]
        if len(dd) > 1:
            d.polygon(dd + [(dd[-1][0], yb), (dd[0][0], yb)], fill=Y + (int(38 * a),))
            d.line(dd, fill=Y + (int(255 * a),), width=6, joint='curve')
            for (x, y) in dd[:-1]: d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=WH + (int(255 * a),))
        L.alpha_composite(lay)
        for i in (3, 5, 7, 11):
            q = pr(t, W_(77) + i * 0.03, 0.3)
            if q > 0: place(L, txt('?', 'Black', 48, Y), pts[i][0], pts[i][1] - 42, eb(q), a)
    # amount card (scramble)
    c2 = pr(t, t0 + 0.9, 0.45)
    if c2 > 0:
        cy = 1010 + 40 * (1 - eo(c2)); a = eo(c2)
        place(L, card(455, 270), 300, cy, 1, a)
        lb = label('● MONTO A PAGAR', GR); place(L, lb, 300 - 227 + 28 + lb.width / 2, cy - 95, 1, a)
        if t < W_(77): s = '$' + str(random.Random(int(t * 12)).randint(95, 480))
        else: s = '$???'
        place(L, txt(s, 'Black', 92, WH if t < W_(77) else Y), 300, cy + 20, 1, a)
    c3 = pr(t, t0 + 1.2, 0.45)
    if c3 > 0:
        global GAUGE
        if GAUGE is None: GAUGE = gauge_img()
        cy = 1010 + 40 * (1 - eo(c3)); a = eo(c3)
        place(L, card(455, 270), 780, cy, 1, a)
        lb = label('● TU CONTROL', GR); place(L, lb, 780 - 227 + 28 + lb.width / 2, cy - 95, 1, a)
        place(L, GAUGE, 780, cy + 30, 0.95, a)
        ang = 200 + 18 * math.sin(t * 2.3) + 10 * math.sin(t * 7.1)
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        px, py = 780, cy + 72; r = math.radians(ang)
        d.line([(px, py), (px + 105 * math.cos(r), py + 105 * math.sin(r))], fill=WH + (int(255 * a),), width=6)
        d.ellipse([px - 11, py - 11, px + 11, py + 11], fill=WH + (int(255 * a),)); L.alpha_composite(lay)

def compare_card(kind):
    if kind == 0:
        im = card(430, 540, outline=Y, ow=3, fill=(24, 21, 10, 240))
        im.alpha_composite(licon('bulb', 150), (140, 70))
        e = txt('ENTENDER', 'Black', 58, Y); im.alpha_composite(e, (215 - e.width // 2, 270))
        for k, s in enumerate(['CÓMO FUNCIONA', 'LA ENERGÍA']):
            l = txt(s, 'Bold', 26, WH, track=3); im.alpha_composite(l, (215 - l.width // 2, 365 + k * 40))
    else:
        im = card(430, 540, outline=LINE, ow=2)
        im.alpha_composite(licon('panel', 150, GR), (140, 70))
        for k, s in enumerate(['COMPRAR', 'PLACAS']):
            e = txt(s, 'Black', 58, GR); im.alpha_composite(e, (215 - e.width // 2, 260 + k * 72))
    return im
CMP = [compare_card(0), compare_card(1)]
def beat_compare(t, L):  # W81 -> W96
    p0 = pr(t, W_(81) + 0.05, 0.45); p1 = pr(t, W_(93) - 0.15, 0.45); pb = pr(t, W_(88) - 0.1, 0.35)
    em = eio(pr(t, W_(95), 0.6))
    if p0 > 0:
        s = (0.85 + 0.15 * eb(p0)) * (1 + 0.08 * em)
        im = CMP[0] if em < 0.5 else glowed(CMP[0], 30, 0.45 * em)
        place(L, im, 290 + 20 * em, 800, s, eo(p0))
    if p1 > 0:
        place(L, CMP[1], 790 + 10 * em, 800, (0.85 + 0.15 * eb(p1)) * (1 - 0.1 * em), eo(p1) * (1 - 0.55 * em))
    if pb > 0:
        b = Image.new('RGBA', (110, 110), (0, 0, 0, 0)); bd = ImageDraw.Draw(b); bd.ellipse([2, 2, 108, 108], fill=Y)
        bd.text((55, 52), '>', font=font('Black', 70), fill=K, anchor='mm')
        place(L, b, 540, 800, eb(pb))

def beat_city_outro(t, L):  # W96 -> T  (relight -> identical to frame 0)
    lvl = eio(pr(t, W_(98), W_(104) + 0.4 - W_(98)))
    sc = lerp(1.14, 1.0, eio(pr(t, W_(96), T - W_(96))))
    place(L, city_frame(lvl, int(t * 24)), CX, 820, sc)
    # energy streams flowing into city while relighting
    if lvl < 1:
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for k in range(10):
            ph = ((t * 0.7) + k / 10) % 1
            x = 120 + k * 92; y0 = 330 + ph * 300
            d.line([(x, y0), (x, y0 + 60)], fill=Y + (int(180 * (1 - ph) * (1 - lvl)),), width=3)
        L.alpha_composite(lay)

BEATS = [beat_city_intro, beat_losses, beat_economy, beat_network, beat_opportunity, beat_focus, beat_bill, beat_compare, beat_city_outro]
TR = 0.22

def render_beat(k, t):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); BEATS[k](t, L); return L

def streaks(fr, t):
    d_ = (t - T) if t > T / 2 else t   # signed distance to loop point
    a = math.exp(-abs(d_ + 0.25) / 0.18)
    if a < 0.03: return
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); r = random.Random(17)
    for i in range(70):
        ang = r.uniform(0, 6.283); r0 = r.uniform(80, 700); ln = r.uniform(30, 120) * a
        sp = (r0 + 900 * (d_ + 0.3)) % 1000
        x0, y0 = CX + math.cos(ang) * sp, CY + math.sin(ang) * sp * 1.4
        d.line([(x0, y0), (x0 + math.cos(ang) * ln, y0 + math.sin(ang) * ln * 1.4)], fill=Y + (int(200 * a),), width=2)
    fr.alpha_composite(lay)

def frame(i):
    t = i / FPS
    fr = BG.copy()
    k = max(j for j in range(len(BEATS)) if B[j] <= t) if t < T else len(BEATS) - 1
    k = min(k, len(BEATS) - 1)
    # crossfade near boundaries (not at loop point)
    nb = B[k + 1] if k + 1 < len(BEATS) else None
    if nb is not None and t > nb - TR:          # leaving towards k+1
        p = eio((t - (nb - TR)) / (2 * TR))
        a = render_beat(k, t); b = render_beat(k + 1, t)
        place(fr, a, W / 2, H / 2, 1 + 0.05 * p, 1 - p); place(fr, b, W / 2, H / 2, 0.95 + 0.05 * p, p)
    elif k > 0 and t < B[k] + TR:               # arriving into k
        p = eio((t - (B[k] - TR)) / (2 * TR))
        a = render_beat(k - 1, t); b = render_beat(k, t)
        place(fr, a, W / 2, H / 2, 1 + 0.05 * p, 1 - p); place(fr, b, W / 2, H / 2, 0.95 + 0.05 * p, p)
    else:
        fr.alpha_composite(render_beat(k, t))
    streaks(fr, t)
    draw_caps(fr, t)
    fr.alpha_composite(HEADER, (0, 200))
    fr.alpha_composite(GRAIN[i % 4])
    return fr.convert('RGB')

if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        for tt in map(float, sys.argv[2:]): frame(int(round(tt * FPS))).save('/home/claude/reel/v2_%05.2f.jpg' % tt, quality=88)
    else:
        a, b, outp = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', outp], stdin=subprocess.PIPE)
        for i in range(a, b): p.stdin.write(frame(i).tobytes())
        p.stdin.close(); sys.exit(p.wait())
