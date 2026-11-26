"""Anuncios — Campaña 001 «No compres a ciegas» (Eliot Angueira · Profit Solar Energy).
Uso: python ad.py ads/adNNN/spec.json stills t1 t2 ... | render | cover
"""
import os, sys, json, math, random, subprocess, unicodedata
SPEC_PATH = os.path.abspath(sys.argv[1]); SPEC = json.load(open(SPEC_PATH))
os.environ['REEL_CFG'] = SPEC_PATH
ENG = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ENG)
import render2 as R
from render2 import W, H, Y, YD, K, WH, GR, DIM, RED, LINE, txt, glowed, place, cl, eo, eio, eb, pr, lerp, card
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------- Montserrat ExtraBold ----------
_base_font = R.font; _mf = {}
MONT = '/usr/share/fonts/truetype/google-fonts/ofl/montserrat/Montserrat[wght].ttf'
def font(kind, size):
    if kind != 'mont': return _base_font(kind, size)
    if size not in _mf:
        f = ImageFont.truetype(MONT, size)
        try: f.set_variation_by_name('ExtraBold')
        except Exception:
            try: f.set_variation_by_axes([800])
            except Exception: pass
        _mf[size] = f
    return _mf[size]
R.font = font

WD = R.WD; T = R.T
NAVY = (30, 46, 80); NAVY2 = (48, 72, 118); PAPER = (238, 237, 231); INK = (24, 26, 30)
VY = 720  # centro visual (zona segura de anuncios)

def norm(s):
    s = unicodedata.normalize('NFD', s.lower()); s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.strip('¿?¡!.,:;')
def find(prefix, after=0):
    for i in range(after, len(WD)):
        if norm(WD[i][0]).startswith(prefix): return i
    raise SystemExit('word not found: ' + prefix)
def tw(i): return WD[max(0, min(len(WD) - 1, i))][1]
def ap(t, i, d=0.4, lead=0.1): return pr(t, tw(i) - lead, d)

iA = find('antes'); iCons1 = find('consum', iA); iPeq = find('pequeno', iA); iUn = iPeq - 3
iPag = find('pagando', iPeq); iGr = find('grande', iPeq); iInn = find('innecesar', iGr)
iPor = find('por', iInn); iCalc = find('calculadora', iPor); iPR = find('puerto', iCalc)
iSolo = find('solo', iPR); iCons2 = find('consumo', iSolo); iLuma = find('luma', iCons2)
iIng = find('ingresa', iLuma); iDat = find('datos', iIng); iDesc = find('descubre', iIng); iCuan = find('cuantas', iDesc); iHog = find('hogar', iDesc)
iSoy = find('soy', iHog); iPres = find('presiona', iSoy); iSin = find('sin', iPres)

# ---------- drawing helpers ----------
def mont(s, size, col=WH): return txt(s, 'mont', size, col)
def fitw(im, w):
    return im if im.width <= w else im.resize((w, max(1, int(im.height * w / im.width))), Image.LANCZOS)
def pill(text, col=Y, fill=(20, 18, 8, 235), size=24):
    tt = txt(text, 'Bold', size, col, track=4); w = tt.width + 60; h = size * 2 + 4
    c = card(w, h, outline=col, r=h // 2, fill=fill); c.alpha_composite(tt, (w // 2 - tt.width // 2, h // 2 - tt.height // 2)); return c

def panel_cell(cs):
    im = Image.new('RGBA', (cs, int(cs * 1.5)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); h = im.height
    d.rectangle([0, 0, cs - 1, h - 1], fill=NAVY, outline=(150, 166, 196), width=max(1, cs // 18))
    for k in (1, 2): d.line([(cs * k // 3, 2), (cs * k // 3, h - 3)], fill=NAVY2, width=1)
    for k in (1, 2, 3, 4, 5): d.line([(2, h * k // 6), (cs - 3, h * k // 6)], fill=NAVY2, width=1)
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).polygon([(0, 0), (cs * 0.55, 0), (0, h * 0.5)], fill=(255, 255, 255, 34))
    im.alpha_composite(sh); return im
_pc = {}
def cell(cs):
    if cs not in _pc: _pc[cs] = panel_cell(cs)
    return _pc[cs]
def panel_layout(n, per_row, cs, gap):
    rows = []; left = n
    while left > 0: rows.append(min(per_row, left)); left -= rows[-1]
    ch = int(cs * 1.5); pos = []
    tw_ = per_row * cs + (per_row - 1) * gap
    for r, m in enumerate(rows):
        x0 = (tw_ - (m * cs + (m - 1) * gap)) / 2
        for c in range(m): pos.append((x0 + c * (cs + gap), r * (ch + gap)))
    return pos, tw_, len(rows) * ch + (len(rows) - 1) * gap
def panels_img(n, per_row, cs, gap=6, prog=1.0):
    pos, w, h = panel_layout(n, per_row, cs, gap)
    im = Image.new('RGBA', (int(w) + 2, int(h) + 2), (0, 0, 0, 0)); c = cell(cs)
    for k, (x, y) in enumerate(pos):
        q = cl(prog * len(pos) - k)
        if q <= 0: continue
        if q < 1:
            cc = c.copy(); cc.putalpha(cc.getchannel('A').point(lambda v: int(v * q))); im.alpha_composite(cc, (int(x), int(y)))
        else: im.alpha_composite(c, (int(x), int(y)))
    return im

def house(w, npan, per_row, prog=1.0, lit=True, tint=None):
    """Casa frontal con techo trapezoidal y placas sobre el techo."""
    h = int(w * 0.78); im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rt = int(h * 0.46); body = (int(w * 0.10), rt, int(w * 0.90), h - 4)
    d.polygon([(int(w * 0.02), rt), (int(w * 0.20), 6), (int(w * 0.80), 6), (int(w * 0.98), rt)], fill=(26, 30, 37), outline=tint or (96, 102, 116))
    d.rectangle(body, fill=(36, 40, 49), outline=tint or (96, 102, 116), width=3)
    dw = int(w * 0.13); d.rectangle([w // 2 - dw // 2, h - 4 - int(h * 0.30), w // 2 + dw // 2, h - 4], fill=Y if lit else (60, 64, 74))
    for x in (int(w * 0.22), int(w * 0.64)):
        d.rectangle([x, rt + int(h * 0.12), x + int(w * 0.14), rt + int(h * 0.12) + int(h * 0.14)], fill=(255, 214, 90) if lit else (54, 58, 68))
    if npan:
        rows = math.ceil(npan / per_row); avail_w = int(w * 0.52); avail_h = rt - 22
        cs = int(min((avail_w - (per_row - 1) * 4) / per_row, (avail_h - (rows - 1) * 4) / rows / 1.5))
        p = panels_img(npan, per_row, max(6, cs), 4, prog)
        im.alpha_composite(p, (w // 2 - p.width // 2, 12 + (avail_h - p.height) // 2))
    return im

def xbadge(sz=86, col=RED, check=False):
    im = Image.new('RGBA', (sz, sz), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([2, 2, sz - 3, sz - 3], fill=col); m = sz * 0.3; lw = max(4, sz // 10)
    if check: d.line([(sz * 0.27, sz * 0.52), (sz * 0.44, sz * 0.68), (sz * 0.74, sz * 0.34)], fill=K, width=lw)
    else: d.line([(m, m), (sz - m, sz - m)], fill=WH, width=lw); d.line([(sz - m, m), (m, sz - m)], fill=WH, width=lw)
    return im

BARS = [0.62, 0.70, 0.55, 0.78, 0.92, 1.0, 0.95, 0.88, 0.74, 0.66, 0.60, 0.71, 0.84]
def bill_img(grow=1.0, hl=0.0):
    w, h = 620, 800; im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 26, fill=PAPER)
    d.text((44, 40), 'LUMA', font=font('Black', 58), fill=INK)
    d.text((w - 44, 52), 'FACTURA', font=font('Bold', 22), fill=(110, 112, 118), anchor='ra')
    d.text((w - 44, 82), 'ELECTRICIDAD', font=font('Bold', 22), fill=(110, 112, 118), anchor='ra')
    for k, ww in enumerate((300, 220, 260)): d.rounded_rectangle([44, 140 + k * 30, 44 + ww, 154 + k * 30], 7, fill=(205, 205, 200))
    d.line([(44, 250), (w - 44, 250)], fill=(190, 190, 186), width=3)
    d.text((44, 276), 'HISTORIAL DE CONSUMO', font=font('Bold', 24), fill=(90, 92, 98))
    cx0, cy1, cw, chh = 56, 590, w - 112, 270
    if hl > 0:
        a = int(255 * hl); d.rounded_rectangle([cx0 - 18, cy1 - chh - 26, cx0 + cw + 18, cy1 + 44], 18, outline=YD + (a,), width=6)
    bw = cw / len(BARS)
    for k, v in enumerate(BARS):
        g = eo(cl(grow * 1.6 - k * 0.05)); bh = chh * v * g
        on = hl > 0 and cl(hl * len(BARS) * 1.2 - k) > 0
        col = YD if on else (128, 132, 140)
        if k == len(BARS) - 1 and not on: col = (70, 74, 82)
        d.rectangle([cx0 + k * bw + 5, cy1 - bh, cx0 + (k + 1) * bw - 5, cy1], fill=col)
    d.text((cx0, cy1 + 12), 'kWh', font=font('Bold', 22), fill=(110, 112, 118))
    d.line([(44, 650), (w - 44, 650)], fill=(190, 190, 186), width=3)
    d.text((44, 688), 'CONSUMO DEL MES', font=font('Bold', 24), fill=(90, 92, 98))
    vt = '1,050 kWh'; f = font('Black', 44); tw_ = d.textlength(vt, font=f)
    if hl > 0: d.rounded_rectangle([w - 44 - tw_ - 20, 676, w - 30, 748], 14, fill=Y + (int(255 * hl),))
    d.text((w - 40, 712), vt, font=f, fill=INK, anchor='rm')
    return im

# ---------- header ----------
def make_header():
    im = Image.new('RGBA', (W, 220), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([60, 78, 104, 82], fill=Y)
    im.alpha_composite(txt('ELIOT ANGUEIRA', 'Bold', 24, (235, 236, 240), track=6), (56, 96))
    im.alpha_composite(txt('ENERGY ADVISOR', 'SemiBold', 19, YD, track=5), (57, 134))
    r = txt('PROFIT SOLAR ENERGY', 'SemiBold', 19, GR, track=4); im.alpha_composite(r, (W - 60 - r.width, 100))
    return im
R.HEADER = make_header()

# ---------- captions (zona segura de anuncios) ----------
KEY = {'PLACAS', 'SOLARES', 'CONSUME', 'PEQUEÑO', 'GRANDE', 'CALCULADORA', 'PUERTO', 'RICO', 'LUMA', 'CONSUMO', 'ELIOT', 'ANGUEIRA',
       'COMPROMISO', 'ERROR', 'CARO', 'PRIMERO', 'RESPUESTA', 'HOGARES', '10', '15', '25', 'ENLACE'}
CH = R.chunks()
def draw_caps(fr, t):
    for s, e, c in CH:
        if not (s - 0.02 <= t < e): continue
        fa = eo(pr(t, s, 0.12)) * (1 - eo(pr(t, e - 0.1, 0.1)))
        items = []
        for i in c:
            wd = WD[i][0].upper().strip(',.:'); key = wd.strip('¿?') in KEY; on = t >= WD[i][1]
            items.append(mont(wd, 68, (Y if key else WH) if on else DIM))
        gap = 20; widths = [im.width for im in items]; lines = [list(range(len(items)))]
        if sum(widths) + gap * (len(items) - 1) > 920 and len(items) > 1:
            best = min(range(1, len(items)), key=lambda k: abs(sum(widths[:k]) - sum(widths[k:])))
            lines = [list(range(best)), list(range(best, len(items)))]
        y0 = 1150 if len(lines) == 1 else 1108
        for li, ln in enumerate(lines):
            tw_ = sum(widths[j] for j in ln) + gap * (len(ln) - 1); ls = min(1.0, 940 / tw_); x = W / 2 - tw_ * ls / 2
            for j in ln:
                im = items[j]; on = t >= WD[c[j]][1]
                pop = 1 + 0.06 * (1 - eo(pr(t, WD[c[j]][1], 0.18))) if on else 1
                place(fr, im, x + im.width * ls / 2, y0 + li * 84 + 10 * (1 - fa), pop * ls, fa)
                x += (im.width + gap) * ls
        return
R.draw_caps = draw_caps
R.streaks = lambda fr, t: None

# ---------- hooks ----------
def hook_ad001(t, L):
    i10, i15 = 0, find('15'); i25 = find('25'); iNec = find('necesitas')
    for k, (num, idx, per, hl) in enumerate(((10, i10, 5, False), (15, i15, 8, True), (25, i25, 9, False))):
        p = 1.0 if k == 0 else ap(t, idx, 0.45)
        if p <= 0: continue
        y = 560 + k * 205; cd = card(900, 186, outline=Y if hl else LINE, ow=3 if hl else 2, fill=(24, 21, 10, 240) if hl else (17, 19, 24, 235))
        nm = mont(str(num), 120, Y if hl else WH); cd.alpha_composite(nm, (60, 93 - nm.height // 2 - 10))
        lb = txt('PLACAS', 'Bold', 20, GR, track=5); cd.alpha_composite(lb, (66 + nm.width // 2 - lb.width // 2, 140))
        pim = panels_img(num, per, 34 if num < 25 else 30, 5, 1.0 if k == 0 else eo(pr(t, tw(idx) + 0.05, 0.5)))
        pim = fitw(pim, 560)
        if pim.height > 160: pim = pim.resize((int(pim.width * 160 / pim.height), 160), Image.LANCZOS)
        cd.alpha_composite(pim, (590 - pim.width // 2 + 40, 93 - pim.height // 2))
        place(L, cd, 540 + 260 * (1 - eo(p)), y, 0.92 + 0.08 * eb(p), eo(p))
    q = ap(t, iNec, 0.4)
    if q > 0: place(L, pill('¿CUÁL NECESITA TU CASA?'), 540, 410, 0.9 + 0.1 * eb(q), eo(q))

def hook_ad002(t, L):
    iPl = find('placas'); iSinH = find('sin'); iPri = find('primero')
    place(L, mont('NO COMPRES', 112, WH), 540, 450, 1.08 - 0.08 * eo(pr(t, 0, 0.4)), 1)
    q = ap(t, iPl, 0.35)
    if q > 0: place(L, glowed(mont('PLACAS SOLARES', 92, Y), 24, 0.5), 540, 580, 1.2 - 0.2 * eo(q), cl(q * 2))
    pim = panels_img(8, 4, 64, 8, 1.0)
    place(L, pim, 540, 800, 1, 1)
    s = ap(t, iPri, 0.3)
    if s > 0:
        lay = Image.new('RGBA', (320, 320), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        d.ellipse([14, 14, 306, 306], outline=RED, width=22)
        a = math.radians(-45); d.line([(160 - 120 * math.cos(a), 160 - 120 * math.sin(a)), (160 + 120 * math.cos(a), 160 + 120 * math.sin(a))], fill=RED, width=22)
        place(L, lay, 540, 800, 1.5 - 0.5 * eo(s), cl(s * 2))

def hook_ad003(t, L):
    iCaro = find('caro'); iCom = find('comprar'); iPl = find('placas')
    place(L, mont('EL ERROR', 120, WH), 540, 450, 1.08 - 0.08 * eo(pr(t, 0, 0.4)), 1)
    q = ap(t, iCaro, 0.3)
    if q > 0: place(L, glowed(mont('MÁS CARO', 140, Y), 30, 0.6), 540, 610, 1.3 - 0.3 * eo(q), cl(q * 2))
    p = 1.0
    if p > 0:
        hs = house(420, 6, 3, 1.0)
        place(L, hs, 540, 880, 0.9 + 0.1 * eb(p), eo(p))
        r = random.Random(5)
        for k in range(9):
            st = tw(iCom) + k * 0.12; u = (t - st) % 1.4
            if t < st: continue
            x = 540 + r.uniform(-260, 260); y = 760 + u * 260
            place(L, txt('−$', 'Black', int(r.uniform(38, 60)), RED), x, y, 1, cl(1 - u / 1.4) * eo(p))

def hook_ad004(t, L):
    iEsc = find('esconde'); iRes = find('respuesta')
    b = bill_img(1.0, 0)
    place(L, b, 540, 740, 0.78, 1, rot=-5)
    p = ap(t, iEsc, 0.5)
    if p > 0:
        u = eio(pr(t, tw(iEsc), 1.0)); lx, ly = lerp(380, 690, u), 760 - 60 * math.sin(u * math.pi)
        r = 120; zoom = b.resize((int(b.width * 1.25), int(b.height * 1.25)), Image.LANCZOS)
        # lens: draw yellow-tinted magnified disk
        lens = Image.new('RGBA', (2 * r + 40, 2 * r + 120), (0, 0, 0, 0)); d = ImageDraw.Draw(lens)
        d.ellipse([20, 20, 20 + 2 * r, 20 + 2 * r], fill=(255, 196, 0, 60), outline=WH, width=12)
        d.line([(20 + r + int(r * 0.75), 20 + r + int(r * 0.75)), (20 + r + int(r * 1.25), 20 + r + int(r * 1.45))], fill=WH, width=22)
        place(L, lens, lx + 20, ly + 40, 0.8 + 0.2 * eb(p), eo(p))
    q = ap(t, iRes, 0.35)
    if q > 0: place(L, pill('LA RESPUESTA: TU CONSUMO'), 540, 410, 0.9 + 0.1 * eb(q), eo(q))

def hook_ad005(t, L):
    iHg = find('hogares'); iCant = find('cantidad'); iPl = find('placas')
    specs = [(260, 4, 2, 190), (320, 9, 3, 520), (380, 16, 4, 870)]
    for k, (w, n, per, x) in enumerate(specs):
        p = 1.0
        hs = house(w, n, per, 1.0)
        place(L, hs, x, 800 - w * 0.39, 1, 1)
        q = ap(t, iCant, 0.35, lead=0.1 - k * 0.15)
        if q > 0:
            lb = mont('%d PLACAS' % n, 40, Y if k == 1 else WH); place(L, lb, x, 870, 0.9 + 0.1 * eb(q), eo(q))
    q = ap(t, iPl, 0.4)
    if q > 0: place(L, pill('CADA CASA ES DIFERENTE'), 540, 410, 0.9 + 0.1 * eb(q), eo(q))

# ---------- body ----------
def body_bill(t, L):
    t0 = tw(iA); p = eo(pr(t, t0 - 0.2, 0.5)); grow = pr(t, t0, 1.2); hl = eio(pr(t, tw(iCons1) - 0.1, 0.9))
    b = bill_img(grow, hl); z = lerp(0.74, 0.86, eio(pr(t, tw(iCons1) - 0.2, 1.2)))
    fl = math.sin(t * 1.6) * 8
    place(L, b, 540, 760 + 60 * (1 - p) + fl - 40 * hl, z, p, rot=lerp(-4, 0, eio(pr(t, t0, 1.0))))
    q = ap(t, iCons1, 0.35)
    if q > 0: place(L, pill('TODO COMIENZA AQUÍ'), 540, 410, 0.9 + 0.1 * eb(q), eo(q))

def meter(frac, a, over=False):
    w, h = 400, 120; im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    mk = 240
    d.text((0, 0), 'PRODUCCIÓN', font=font('Bold', 18), fill=GR)
    d.rounded_rectangle([0, 40, w - 1, 70], 15, fill=(30, 33, 40))
    fw = min(w - 1, mk * frac * a)
    if fw > 4:
        d.rounded_rectangle([0, 40, fw, 70], 15, fill=YD if not over else Y)
        if over and fw > mk: d.rounded_rectangle([mk, 40, fw, 70], 15, fill=RED); d.rectangle([mk, 40, mk + 14, 70], fill=RED)
    d.line([(mk, 30), (mk, 80)], fill=WH, width=4)
    lb = 'TU CONSUMO'; d.text((mk, 86), lb, font=font('Bold', 18), fill=WH, anchor='ma')
    return im

def body_houses(t, L):
    t0 = tw(iUn)
    for side, (x, npan, per, iK, iV, frac, title, verdict, over) in enumerate(
            ((290, 3, 3, iPeq, iPag, 0.45, 'MUY PEQUEÑO', 'SIGUES PAGANDO LUZ', False),
             (790, 18, 6, iGr, iInn, 1.55, 'MUY GRANDE', 'GASTAS DE MÁS', True))):
        p = eo(pr(t, t0 - 0.2 + side * 0.15, 0.5))
        pp = eo(pr(t, tw(iK) - 0.1, 0.6))
        hs = house(400, npan, per, pp)
        place(L, hs, x, 600, 0.9 + 0.1 * eb(p), p)
        q = ap(t, iK, 0.35)
        if q > 0: place(L, mont(title, 40, Y), x, 790, 0.9 + 0.1 * eb(q), eo(q))
        m = eo(pr(t, tw(iK) + 0.3, 0.9))
        if m > 0: place(L, meter(frac, m, over), x, 900, 1, cl(m * 3))
        v = ap(t, iV, 0.3)
        if v > 0:
            place(L, xbadge(80), x + 160, 470, 1.5 - 0.5 * eo(v), cl(v * 2))
            place(L, txt(verdict, 'Black', 30, RED if over else (255, 120, 120)), x, 1010, 1, eo(v))

def phone(t):
    pw, ph = 380, 740; im = Image.new('RGBA', (pw, ph), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, pw - 1, ph - 1], 56, fill=(14, 15, 18), outline=(70, 74, 84), width=4)
    sx, sy, sw, sh = 14, 14, pw - 28, ph - 28
    sc = Image.new('RGBA', (sw, sh), (15, 18, 22, 255)); s = ImageDraw.Draw(sc)
    s.rounded_rectangle([sw // 2 - 50, 10, sw // 2 + 50, 34], 12, fill=(0, 0, 0))
    s.text((26, 14), '9:41', font=font('Bold', 16), fill=WH)
    s.polygon(R.bolt_pts(34, 62, 9), fill=Y); s.text((50, 52), 'CALCULADORA SOLAR', font=font('Bold', 15), fill=Y)
    y = 86
    for parts in ((('¿Cuántas ', WH), ('placas', Y)), (('solares', Y), (' necesita', WH)), (('tu hogar?', WH),)):
        x = 26
        for tx, col in parts: s.text((x, y), tx, font=font('Black', 31), fill=col); x += s.textlength(tx, font=font('Black', 31))
        y += 38
    s.text((26, y + 8), 'Empieza con tu consumo.', font=font('Medium', 16), fill=GR)
    # toggle
    sel13 = t >= tw(iCons2) - 0.1
    ty = 236; s.rounded_rectangle([20, ty, sw - 20, ty + 46], 23, fill=(30, 33, 40))
    half = (sw - 40) // 2; xs = 20 if not sel13 else 20 + half
    s.rounded_rectangle([xs + 3, ty + 3, xs + half - 3, ty + 43], 20, fill=Y)
    s.text((20 + half // 2, ty + 23), 'Solo sé 1 mes', font=font('Bold', 14), fill=K if not sel13 else GR, anchor='mm')
    s.text((20 + half + half // 2, ty + 23), 'Ingresar mis 13 meses', font=font('Bold', 13), fill=K if sel13 else GR, anchor='mm')
    # fields
    vals = ['1,050', '980', '1,120', '890']; labs = ['Mes 1 (más reciente)', 'Mes 2', 'Mes 3', 'Mes 4']
    ts = tw(iCons2) + 0.2; te = tw(iDesc) - 0.4; per = (te - ts) / 4
    for k in range(4):
        fy = 300 + k * 64
        s.text((24, fy), labs[k], font=font('SemiBold', 13), fill=GR)
        act = ts + k * per <= t < ts + (k + 1) * per
        s.rounded_rectangle([20, fy + 18, sw - 20, fy + 56], 10, fill=(24, 27, 33), outline=Y if act else (52, 56, 66), width=2)
        n = len(vals[k]); typed = int(cl((t - (ts + k * per)) / (per * 0.7)) * n)
        tx = vals[k][:typed]
        s.text((34, fy + 37), tx + (' kWh' if typed == n else ''), font=font('Bold', 18), fill=WH, anchor='lm')
        if act and int(t * 3) % 2 == 0 and typed < n:
            cxp = 34 + s.textlength(tx, font=font('Bold', 18)); s.line([(cxp + 2, fy + 26), (cxp + 2, fy + 48)], fill=Y, width=2)
    s.text((24, 556), '… Mes 13 (más antiguo)', font=font('SemiBold', 13), fill=(90, 94, 104))
    # button
    by = 590; press = pr(t, tw(iDesc) - 0.1, 0.25); pressed = 0 < press < 1
    s.rounded_rectangle([20 + (4 if pressed else 0), by + (2 if pressed else 0), sw - 20 - (4 if pressed else 0), by + 58 - (2 if pressed else 0)], 16, fill=Y)
    s.text((sw // 2, by + 29), 'Calcular mis placas solares', font=font('Black', 17), fill=K, anchor='mm')
    # result sheet
    rq = eo(pr(t, tw(iDesc) + 0.25, 0.5))
    if rq > 0:
        ry = int(lerp(sh, 300, rq))
        sheet = Image.new('RGBA', (sw, sh - 300), (0, 0, 0, 0)); sd = ImageDraw.Draw(sheet)
        sd.rounded_rectangle([0, 0, sw - 1, sh - 300 + 30], 30, fill=(22, 25, 31), outline=YD, width=3)
        sd.text((sw // 2, 34), 'TU RESULTADO', font=font('Bold', 15), fill=YD, anchor='mm')
        cnt = int(round(18 * eo(pr(t, tw(iCuan) - 0.1, 1.0))))
        sd.text((sw // 2, 112), str(cnt), font=font('Black', 96), fill=Y, anchor='mm')
        sd.text((sw // 2, 182), 'placas', font=font('Bold', 24), fill=WH, anchor='mm')
        sd.line([(30, 220), (sw - 30, 220)], fill=(52, 56, 66), width=2)
        sd.text((30, 246), 'Potencia aproximada (kW)', font=font('SemiBold', 14), fill=GR)
        sd.text((sw - 30, 246), '8.3', font=font('Black', 16), fill=WH, anchor='ra')
        sd.text((30, 280), 'Consumo anual estimado (kWh)', font=font('SemiBold', 14), fill=GR)
        sd.text((sw - 30, 280), '12,480', font=font('Black', 16), fill=WH, anchor='ra')
        sd.text((sw // 2, 330), 'EJEMPLO ILUSTRATIVO', font=font('Bold', 12), fill=(110, 114, 124), anchor='mm')
        sc.alpha_composite(sheet, (0, ry))
    m = Image.new('L', (sw, sh), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, sw - 1, sh - 1], 44, fill=255)
    sc.putalpha(Image.composite(sc.getchannel('A'), Image.new('L', (sw, sh), 0), m))
    im.alpha_composite(sc, (sx, sy))
    return im

def callout(l1, l2, align='l'):
    a = txt(l1, 'Bold', 22, GR, track=3); b = mont(l2, 36, WH)
    w = max(a.width, b.width) + 10; im = Image.new('RGBA', (max(w, 60), 110), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x = 0 if align == 'l' else im.width - 50
    d.rectangle([x, 0, x + 50, 6], fill=Y)
    im.alpha_composite(a, (0 if align == 'l' else im.width - a.width, 22)); im.alpha_composite(b, (0 if align == 'l' else im.width - b.width, 56))
    return fitw(im, 320)

def tap(L, x, y, t, t0):
    u = pr(t, t0, 0.6)
    if 0 < u < 1:
        lay = Image.new('RGBA', (200, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); r = 20 + 70 * eo(u)
        d.ellipse([100 - r, 100 - r, 100 + r, 100 + r], outline=(255, 255, 255, int(220 * (1 - u))), width=5)
        d.ellipse([86, 86, 114, 114], fill=(255, 255, 255, int(200 * (1 - u))))
        place(L, lay, x, y, 1, 1)

def body_phone(t, L):
    t0 = tw(iPor); p = eo(pr(t, t0 - 0.2, 0.6))
    ph = phone(t); gl = eio(pr(t, tw(iCalc) - 0.1, 0.5)) * (1 - eio(pr(t, tw(iCalc) + 0.9, 0.6)))
    if gl > 0.02: ph = glowed(ph, 30, 0.5 * gl)
    PX, PY = 540, 742; SC = 0.93
    place(L, ph, PX, PY + 300 * (1 - p), SC * (0.9 + 0.1 * p), p)
    ox, oy = PX - 190 * SC + 14 * SC, PY - 370 * SC + 14 * SC
    tap(L, ox + (20 + 3 * 88 + 44) * SC, oy + (236 + 23) * SC, t, tw(iCons2) - 0.1)
    tap(L, PX, oy + (590 + 29) * SC, t, tw(iDesc) - 0.1)
    for (l1, l2, al, x, y, idx) in (('DISEÑADA PARA', 'PUERTO RICO', 'l', 190, 520, iPR), ('1 MES O', '13 MESES', 'r', 900, 700, iSolo),
                                    ('SOLO TU', 'FACTURA', 'l', 190, 880, iLuma)):
        q = ap(t, idx, 0.4)
        if q > 0:
            c = callout(l1, l2, al); place(L, c, x + (-40 if al == 'l' else 40) * (1 - eo(q)), y, 1, eo(q))

LOGO = Image.open(os.path.join(ENG, 'assets', 'logo_icon.png')).convert('RGBA')
def body_end(t, L):
    t0 = tw(iSoy); p = eo(pr(t, t0 - 0.15, 0.5))
    lg = glowed(LOGO.resize((150, 173), Image.LANCZOS), 26, 0.55)
    place(L, lg, 540, 440, 0.7 + 0.3 * eb(p), p)
    e = mont('ELIOT', 100, WH); a = glowed(mont('ANGUEIRA', 100, Y), 24, 0.45)
    place(L, e, 540, 590, 1, eo(pr(t, t0, 0.4))); place(L, a, 540, 690, 1, eo(pr(t, t0 + 0.15, 0.4)))
    place(L, txt('ENERGY ADVISOR', 'SemiBold', 28, WH, track=10), 540, 772, 1, eo(pr(t, t0 + 0.3, 0.4)))
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ln = eo(pr(t, t0 + 0.35, 0.5))
    ImageDraw.Draw(lay).line([(540 - 360 * ln, 812), (540 + 360 * ln, 812)], fill=YD, width=3); L.alpha_composite(lay)
    place(L, txt('PROFIT SOLAR ENERGY', 'Bold', 24, Y, track=6), 540, 846, 1, eo(pr(t, t0 + 0.45, 0.4)))
    q = ap(t, iPres, 0.4)
    if q > 0:
        bt = card(800, 112, outline=Y, r=56, fill=Y + (255,)); tt = mont('CALCULA TUS PLACAS SOLARES', 40, K); tt = fitw(tt, 740)
        bt.alpha_composite(tt, (400 - tt.width // 2, 56 - tt.height // 2))
        pulse = 1 + 0.03 * math.sin((t - tw(iPres)) * 6) if q >= 1 else 1
        place(L, glowed(bt, 26, 0.5), 540, 950, (0.8 + 0.2 * eb(q)) * pulse, eo(q))
        tap(L, 760, 960, t, tw(iPres) + 1.0)
    s = ap(t, iSin, 0.4)
    if s > 0: place(L, txt('SIN COMPROMISO · CALCULATUCONSUMO.NETLIFY.APP', 'Bold', 20, (200, 204, 214), track=3), 540, 1040, 1, eo(s))

HOOK = {'ad001': hook_ad001, 'ad002': hook_ad002, 'ad003': hook_ad003, 'ad004': hook_ad004, 'ad005': hook_ad005}[SPEC['ad']]
R.BEATS = [HOOK, body_bill, body_houses, body_phone, body_end]
R.B = [0, tw(iA), tw(iUn), tw(iPor), tw(iSoy), T]

# ---------- cover ----------
COVER = {
    'ad001': [('¿10, 15 O 25', WH), ('PLACAS', Y), ('SOLARES?', WH)],
    'ad002': [('NO COMPRES', WH), ('PLACAS SOLARES', Y), ('SIN HACER ESTO.', WH)],
    'ad003': [('EL ERROR', WH), ('MÁS CARO', Y), ('AL COMPRAR PLACAS', WH)],
    'ad004': [('TU FACTURA', WH), ('DE LUMA', Y), ('ESCONDE LA RESPUESTA', WH)],
    'ad005': [('NO TODOS', WH), ('LOS HOGARES', Y), ('NECESITAN LO MISMO', WH)],
}
def make_cover(path):
    fr = R.BG.copy(); d = ImageDraw.Draw(fr)
    # subtle grid
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    for x in range(0, W, 60): gd.line([(x, 0), (x, H)], fill=(255, 255, 255, 8))
    for y in range(0, H, 60): gd.line([(0, y), (W, y)], fill=(255, 255, 255, 8))
    fr.alpha_composite(g)
    d.rectangle([90, 300, 190, 310], fill=Y)
    fr.alpha_composite(txt('ENERGÍA INTELIGENTE', 'Bold', 28, Y, track=7), (88, 334))
    y = 420
    for s, col in COVER[SPEC['ad']]:
        im = fitw(mont(s, 120, col), 900)
        if col == Y: gim = glowed(im, 24, 0.45); fr.alpha_composite(gim, (90 - (gim.width - im.width) // 2, y - (gim.height - im.height) // 2))
        else: fr.alpha_composite(im, (90, y))
        y += im.height + 4
    b = bill_img(1.0, 1.0); b = b.resize((int(b.width * 0.42), int(b.height * 0.42)), Image.LANCZOS)
    place(fr, b, 270, y + 230, 1, 1, rot=6)
    arr = Image.new('RGBA', (140, 60), (0, 0, 0, 0)); ad_ = ImageDraw.Draw(arr); ad_.line([(5, 30), (120, 30)], fill=Y, width=8); ad_.polygon([(105, 10), (135, 30), (105, 50)], fill=Y)
    place(fr, arr, 500, y + 230, 1, 1)
    pn = panels_img(12, 4, 64, 6); place(fr, pn, 760, y + 230, 1, 1)
    sun = Image.new('RGBA', (120, 120), (0, 0, 0, 0)); ImageDraw.Draw(sun).ellipse([10, 10, 110, 110], fill=Y); place(fr, glowed(sun, 20, 0.6), 930, y + 70, 1, 1)
    d.line([(90, 1450), (990, 1450)], fill=YD, width=3)
    e = mont('ELIOT ', 80, WH); a = mont('ANGUEIRA', 80, Y)
    fr.alpha_composite(e, (86, 1480)); fr.alpha_composite(a, (86 + e.width, 1480))
    fr.alpha_composite(txt('ENERGY ADVISOR', 'SemiBold', 30, WH, track=10), (90, 1590))
    ps = txt('PROFIT SOLAR ENERGY', 'Bold', 26, Y, track=6); fr.alpha_composite(ps, (990 - ps.width, 1594))
    fr.convert('RGB').save(path, quality=92)

def render_all(outdir):
    n = int(round(T * 30)); parts = 4; step = math.ceil(n / parts); procs = []
    for k in range(parts):
        a, bb = k * step, min(n, (k + 1) * step)
        procs.append(subprocess.Popen([sys.executable, __file__, SPEC_PATH, 'chunk', str(a), str(bb), os.path.join(outdir, 'p%d.mp4' % k)]))
    for p in procs:
        if p.wait() != 0: raise SystemExit('chunk failed')
    lst = os.path.join(outdir, 'list.txt'); open(lst, 'w').write(''.join("file 'p%d.mp4'\n" % k for k in range(parts)))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', os.path.join(outdir, 'v.mp4')], check=True)
    hook_imp = {'ad001': ['15', '25'], 'ad002': ['primero'], 'ad003': ['caro'], 'ad004': ['respuesta'], 'ad005': ['cantidad']}[SPEC['ad']]
    sfx = {'whoosh': R.B[1:-1], 'impact': [0.02] + [tw(find(w)) for w in hook_imp] + [tw(iPres)],
           'pop': [tw(i) for i in (iPeq, iGr, iPag, iInn, iPR, iSolo, iLuma, iCuan, iSin)]}
    cfg = dict(SPEC); cfg['sfx'] = sfx; cfg['mix'] = os.path.join(outdir, 'mix.f32')
    cpath = os.path.join(outdir, 'audio_cfg.json'); json.dump(cfg, open(cpath, 'w'), ensure_ascii=False)
    subprocess.run([sys.executable, os.path.join(ENG, 'audio2.py')], env=dict(os.environ, REEL_CFG=cpath), check=True)
    final = os.path.join(outdir, 'video.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(outdir, 'v.mp4'), '-f', 'f32le', '-ar', '48000', '-ac', '2', '-i', cfg['mix'],
                    '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-maxrate', '8M', '-bufsize', '16M', '-pix_fmt', 'yuv420p',
                    '-profile:v', 'high', '-level', '4.1', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', final], check=True)
    make_cover(os.path.join(outdir, 'cover.jpg'))
    for f in ['v.mp4', 'mix.f32', 'list.txt', 'audio_cfg.json'] + ['p%d.mp4' % k for k in range(parts)]:
        try: os.remove(os.path.join(outdir, f))
        except OSError: pass
    print('OK', final)

if __name__ == '__main__':
    cmd = sys.argv[2]; od = os.path.dirname(SPEC_PATH)
    if cmd == 'stills':
        sd = os.path.join(od, 'stills'); os.makedirs(sd, exist_ok=True)
        for tt in sys.argv[3:]:
            tt = float(tt); R.frame(int(round(tt * 30))).save(os.path.join(sd, 's_%05.2f.jpg' % tt), quality=85)
        print('beats', [round(b, 2) for b in R.B])
    elif cmd == 'chunk':
        a, bb, outp = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', '30', '-i', '-',
                              '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', outp + '.tmp.mp4'], stdin=subprocess.PIPE)
        for i in range(a, bb): p.stdin.write(R.frame(i).tobytes())
        p.stdin.close(); rc = p.wait()
        if rc == 0: os.replace(outp + '.tmp.mp4', outp)
        sys.exit(rc)
    elif cmd == 'cover': make_cover(os.path.join(od, 'cover.jpg'))
    elif cmd == 'render': render_all(od)
