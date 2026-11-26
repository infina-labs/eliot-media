import os, sys, math, random, json, subprocess
os.environ['REEL_CFG'] = '/home/claude/ep002/cfg.json'
sys.path.insert(0, '/home/claude/reel')
import render2 as R
from render2 import *
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

W_ = R.W_
R.KEY = {'LUMA', 'PLACAS', 'RED', 'CRÉDITOS', 'NOCHE', 'NADA', 'DIFERENCIA', 'FIJOS', '$8', 'PENSIONES', 'PEQUEÑO', 'SUBIR', 'ENTENDER', 'CONSUMO', 'PREGUNTÁNDOTE'}
R.CH = R.chunks()
BLUE = (34, 58, 104)

# ---------- house scene ----------
HO = (470, 900); HS = 118      # iso origin & scale
def house_img(glow=0.0, night=0.0, small=False):
    im = Image.new('RGBA', (W, 1100), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ox, oy, s = HO[0], 640, HS
    w, dp, h, r = 3.2, 2.6, 1.7, 1.15
    wall = tuple(int(lerp(c, c * 0.55, night)) for c in (205, 208, 216))
    # ground slab
    draw_box(d, -0.6, -0.6, w + 1.2, dp + 1.4, 0.18, (34, 37, 44), ox, oy, s)
    z0 = 0.18
    def P(x, y, z): return iso(x, y, z + z0, ox, oy, s)
    # walls
    lf = [P(0, dp, 0), P(w, dp, 0), P(w, dp, h), P(0, dp, h)]
    rf = [P(w, 0, 0), P(w, dp, 0), P(w, dp, h), P(w, 0, h)]
    d.polygon(lf, fill=shade(wall, 0.82)); d.polygon(rf, fill=shade(wall, 0.62))
    gable = [P(w, 0, h), P(w, dp, h), P(w, dp / 2, h + r)]
    d.polygon(gable, fill=shade(wall, 0.62))
    # windows / door (lit at night)
    win = (255, 196, 0) if night > 0.5 else (60, 74, 96)
    for x0 in (0.35, 2.1):
        d.polygon([P(x0, dp, 0.75), P(x0 + 0.7, dp, 0.75), P(x0 + 0.7, dp, 1.35), P(x0, dp, 1.35)], fill=win)
    d.polygon([P(1.25, dp, 0), P(1.85, dp, 0), P(1.85, dp, 1.25), P(1.25, dp, 1.25)], fill=(40, 30, 20))
    d.polygon([P(w, 0.9, 0.75), P(w, 1.7, 0.75), P(w, 1.7, 1.35), P(w, 0.9, 1.35)], fill=win)
    # roof: back face then front face (+y)
    rc = (58, 62, 72)
    back = [P(-0.15, -0.15, h - 0.08), P(w + 0.15, -0.15, h - 0.08), P(w + 0.15, dp / 2, h + r), P(-0.15, dp / 2, h + r)]
    front = [P(-0.15, dp + 0.15, h - 0.08), P(w + 0.15, dp + 0.15, h - 0.08), P(w + 0.15, dp / 2, h + r), P(-0.15, dp / 2, h + r)]
    d.polygon(back, fill=shade(rc, 0.7)); d.polygon(front, fill=rc)
    # panels on front roof
    cols = 2 if small else 5; rows = 1 if small else 2
    def RP(u, v):  # u along x (0..1), v from eave (0) to ridge (1)
        x = -0.15 + (w + 0.3) * u; y = (dp + 0.15) + (dp / 2 - dp - 0.15) * v; z = (h - 0.08) + (r + 0.08) * v
        return P(x, y, z + 0.03)
    pc = tuple(int(lerp(BLUE[i], 255 if i < 2 else 120, glow * 0.0)) for i in range(3))
    for rr in range(rows):
        for cc in range(cols):
            u0 = 0.08 + cc * (0.84 / cols); u1 = u0 + 0.84 / cols - 0.02
            v0 = 0.12 + rr * 0.40; v1 = v0 + 0.36
            q = [RP(u0, v0), RP(u1, v0), RP(u1, v1), RP(u0, v1)]
            d.polygon(q, fill=BLUE, outline=(120, 140, 180))
            for k in (1, 2):
                a = RP(lerp(u0, u1, k / 3), v0); b = RP(lerp(u0, u1, k / 3), v1); d.line([a, b], fill=(70, 95, 140), width=2)
            a = RP(u0, (v0 + v1) / 2); b = RP(u1, (v0 + v1) / 2); d.line([a, b], fill=(70, 95, 140), width=2)
            if glow > 0:
                gl = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(gl).polygon(q, fill=Y + (int(150 * glow),)); im.alpha_composite(gl); d = ImageDraw.Draw(im)
    return im
POLE_TOP = (930, 470)
def pole(d, a=255):
    x, y = POLE_TOP
    d.line([(x, y - 10), (x, y + 560)], fill=(110, 100, 90, a), width=12)
    d.line([(x - 60, y + 20), (x + 60, y + 20)], fill=(110, 100, 90, a), width=10)
    for dx in (-50, 50): d.ellipse([x + dx - 8, y + 4, x + dx + 8, y + 20], fill=(180, 180, 190, a))
EAVE = None
def wire_pts():
    ox, oy, s = HO[0], 640 + (900 - 550), HS
    a = iso(3.2, 0.3, 1.7 + 0.18, ox, oy - 350 + 0, s)
    return a
CACHE = {}
def house_cached(glow, night, small=False):
    k = (round(glow, 2), round(night, 2), small)
    if k not in CACHE:
        if len(CACHE) > 60: CACHE.clear()
        CACHE[k] = house_img(glow, night, small)
    return CACHE[k]

def sky(L, t, day):
    # sun / moon on top right
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    sx, sy = 820, 420
    if day > 0.02:
        a = int(255 * day)
        for k in range(12):
            ang = math.radians(k * 30 + t * 20); r0, r1 = 74, 104
            d.line([(sx + r0 * math.cos(ang), sy + r0 * math.sin(ang)), (sx + r1 * math.cos(ang), sy + r1 * math.sin(ang))], fill=Y + (a,), width=6)
        d.ellipse([sx - 56, sy - 56, sx + 56, sy + 56], fill=Y + (a,))
    if day < 0.98:
        a = int(255 * (1 - day))
        d.ellipse([sx - 48, sy - 48, sx + 48, sy + 48], fill=(225, 228, 236, a))
        d.ellipse([sx - 20, sy - 62, sx + 70, sy + 28], fill=(0, 0, 0, 0))
        mk = Image.new('L', (W, H), 0); ImageDraw.Draw(mk).ellipse([sx - 22, sy - 66, sx + 72, sy + 26], fill=255)
        lay.putalpha(Image.composite(Image.new('L', (W, H), 0), lay.getchannel('A'), mk))
        d = ImageDraw.Draw(lay)
        for (x, y) in ((180, 380), (300, 470), (640, 360), (960, 560), (120, 600)):
            d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 255, 255, int(200 * (1 - day))))
    L.alpha_composite(lay)

def house_scene(L, t, day=1.0, glow=0.0, flow=0, flow_a=1.0, small=False, sc=1.0, show_pole=True, dx=0):
    sky(L, t, day)
    hi = house_cached(glow, 1 - day, small)
    place(L, hi, W / 2 + dx, 900, sc)
    if show_pole:
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        # transform pole/wire with same scale about (540,900)
        def T_(p): return (W / 2 + dx + (p[0] - W / 2) * sc, 900 + (p[1] - 900) * sc)
        x, y = POLE_TOP
        d.line([T_((x, y - 10)), T_((x, y + 640))], fill=(120, 108, 92), width=int(12 * sc))
        d.line([T_((x - 60, y + 20)), T_((x + 60, y + 20))], fill=(120, 108, 92), width=int(10 * sc))
        # house attach point (gable top-ish right)
        hx, hy = iso(3.2, 1.3, 2.7 + 0.18, HO[0], 640, HS); hx += 0; hy += 900 - 550
        A_ = T_((hx, hy)); B_ = T_((x - 50, y + 14))
        pts = []
        for i in range(31):
            u = i / 30; px = lerp(A_[0], B_[0], u); py = lerp(A_[1], B_[1], u) + 60 * sc * math.sin(math.pi * u)
            pts.append((px, py))
        d.line(pts, fill=(170, 172, 180), width=3)
        if flow != 0:
            for k in range(4):
                u = ((t * 0.8 + k / 4) % 1); u = u if flow > 0 else 1 - u
                px, py = pts[int(u * 30)]
                d.ellipse([px - 9, py - 9, px + 9, py + 9], fill=(Y if flow > 0 else WH) + (int(255 * flow_a),))
        L.alpha_composite(lay)

def bill_card(amount='$???', title='FACTURA DE LUZ'):
    im = Image.new('RGBA', (330, 400), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 4, 326, 396], 18, fill=(236, 236, 230))
    d.text((30, 34), title, font=font('Black', 30), fill=K)
    for k in range(5): d.rectangle([30, 100 + k * 34, 300 - (k % 2) * 60, 110 + k * 34], fill=(190, 192, 196))
    d.rounded_rectangle([30, 290, 300, 366], 10, fill=Y)
    d.text((165, 328), amount, font=font('Black', 52), fill=K, anchor='mm')
    return im
BILL_Q = bill_card()

def hook_state(L, t, enter=1.0):
    house_scene(L, t, day=1, glow=0.5, flow=0)
    place(L, BILL_Q, 265, 610 + 40 * (1 - eo(enter)), 0.85 * (0.8 + 0.2 * eb(enter)), eo(enter), rot=8)

def b_hook(t, L):  # 0 -> W8
    hook_state(L, t, 1.0)
    q = pr(t, W_(3), 0.3)  # LUMA -> pulse bill
    if 0 < q < 1:
        place(L, glowed(BILL_Q, 28, 0.8 * (1 - q)), 265, 610, 0.85 * (1 + 0.06 * math.sin(q * math.pi)), 1, rot=8)

def b_connected(t, L):  # W8 -> W17
    p = eio(pr(t, W_(8), 0.6))
    house_scene(L, t, day=1, glow=0.5, flow=1 if t > W_(13) else 0, flow_a=eo(pr(t, W_(13), 0.4)))
    lb = pr(t, W_(15) - 0.3, 0.4)
    if lb > 0:
        pill = card(420, 64, outline=Y, r=32, fill=(20, 18, 8, 230))
        tt_ = txt('CONECTADO A LA RED', 'Bold', 24, Y, track=4); pill.alpha_composite(tt_, (210 - tt_.width // 2, 32 - tt_.height // 2))
        place(L, pill, 700, 1180, 0.9 + 0.1 * eb(lb), eo(lb))

CRED = None
def counter_card(label_, val, col):
    c = card(430, 170, outline=col if col == Y else LINE)
    lb = txt(label_, 'Bold', 20, col, track=4); c.alpha_composite(lb, (28, 26))
    v = txt(val, 'Black', 64, WH); c.alpha_composite(v, (28, 66))
    return c
def b_day(t, L):  # W17 -> W36
    house_scene(L, t, day=1, glow=0.6 + 0.3 * math.sin(t * 3) ** 2, flow=1 if t > W_(26) else 0, flow_a=eo(pr(t, W_(26), 0.4)))
    # production rays onto panels
    if t > W_(19):
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for k in range(5):
            ph = (t * 1.2 + k / 5) % 1
            x0, y0 = 790 - k * 30, 470; x1, y1 = 420 + k * 40, 760
            px, py = lerp(x0, x1, ph), lerp(y0, y1, ph)
            d.line([(px, py), (px - (x1 - x0) * 0.06, py - (y1 - y0) * 0.06)], fill=Y + (int(200 * (1 - ph)),), width=4)
        L.alpha_composite(lay)
    cp = pr(t, W_(32), 0.4)
    if cp > 0:
        kwh = int(lerp(0, 620, eo(pr(t, W_(33), 1.6))))
        place(L, counter_card('● CRÉDITOS', '+%d kWh' % kwh, Y), 300, 1170, 0.9 + 0.1 * eb(cp), eo(cp))

def b_night(t, L):  # W36 -> W51
    day = 1 - eio(pr(t, W_(36), 0.9))
    house_scene(L, t, day=day, glow=0.0, flow=-1 if t > W_(46) else 0, flow_a=eo(pr(t, W_(46), 0.4)))
    if t > W_(42) and t < W_(44) + 0.5:
        q = pr(t, W_(42), 0.3)
        place(L, txt('0 kWh', 'Black', 70, GR), 330, 600, eb(q), eo(q) * (1 - pr(t, W_(44), 0.4)))
    cp = pr(t, W_(48) - 0.2, 0.4)
    if cp > 0:
        kwh = int(lerp(0, 850, eo(pr(t, W_(48), 1.6))))
        place(L, counter_card('● CONSUMO DE LA RED', '%d kWh' % kwh, WH), 300, 1170, 0.9 + 0.1 * eb(cp), eo(cp))

def bar_row(L, y, label_, val, frac, col, a):
    place(L, txt(label_, 'Bold', 22, GR, track=4), 130 + txt(label_, 'Bold', 22, GR, track=4).width / 2, y - 48, 1, a)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([130, y - 22, 950, y + 22], 22, fill=(30, 33, 40, int(255 * a)))
    if frac > 0.01: d.rounded_rectangle([130, y - 22, 130 + 820 * frac, y + 22], 22, fill=col + (int(255 * a),))
    L.alpha_composite(lay)
    v = txt(val, 'Black', 34, WH); place(L, v, 950 - v.width / 2, y - 48, 1, a)
def b_meter(t, L):  # W51 -> W70
    p0 = eo(pr(t, W_(51) - 0.1, 0.45))
    place(L, txt('A FIN DE MES', 'Black', 46, WH), CX, 400, 1, p0)
    pill = card(430, 44, outline=YD, r=22, fill=(0, 0, 0, 0)); pl = txt('EJEMPLO ILUSTRATIVO', 'Bold', 19, YD, track=4)
    pill.alpha_composite(pl, (215 - pl.width // 2, 22 - pl.height // 2)); place(L, pill, CX, 460, 1, p0)
    place(L, card(940, 560), CX, 820, 1, p0)
    f1 = eo(pr(t, W_(59), 0.8)) * 620 / 850; f2 = eo(pr(t, W_(63), 0.8))
    bar_row(L, 680, '● ENERGÍA QUE DISTE', '%d kWh' % int(620 * f1 / (620 / 850) if f1 else 0), f1, Y, p0)
    bar_row(L, 820, '● ENERGÍA QUE TOMASTE', '%d kWh' % int(850 * f2), f2, (235, 236, 240), p0)
    dp = pr(t, W_(67), 0.45)
    if dp > 0:
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        x0 = 130 + 820 * 620 / 850
        d.rounded_rectangle([x0, 950, x0 + (950 - x0) * eo(dp), 994], 22, fill=RED + (230,)); L.alpha_composite(lay)
        place(L, txt('DIFERENCIA: 230 kWh → PAGAS', 'Black', 32, WH), CX, 1050, 0.9 + 0.1 * eb(dp), eo(dp))

def bill_detail(t, step):
    im = Image.new('RGBA', (720, 760), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 4, 716, 756], 22, fill=(236, 236, 230))
    d.text((40, 40), 'FACTURA DE LUZ', font=font('Black', 40), fill=K)
    d.text((40, 96), 'CLIENTE CON MEDICIÓN NETA', font=font('Bold', 22), fill=(110, 112, 118))
    d.line([(40, 140), (680, 140)], fill=(180, 182, 186), width=3)
    return im
def b_fixed(t, L):  # W70 -> W101
    p0 = eo(pr(t, W_(70), 0.5))
    base = bill_detail(t, 0)
    place(L, base, CX, 790 + 50 * (1 - p0), 1, p0, rot=0)
    ox, oy = CX - 360, 790 - 380 + 50 * (1 - p0)
    rows = [('CONSUMO NETO', '—', W_(72)), ('CARGO FIJO', None, W_(75)), ('PENSIONES', 'INCLUIDO', W_(97))]
    for k, (lab, val, ts) in enumerate(rows):
        q = pr(t, ts - 0.1, 0.35)
        if q <= 0: continue
        y = oy + 200 + k * 110
        place(L, txt(lab, 'Black', 36, K), ox + 40 + txt(lab, 'Black', 36, K).width / 2, y, 1, eo(q) * p0)
        if val is None:
            # $4 -> $8
            v4 = txt('$4.00', 'Black', 40, (120, 122, 128)); place(L, v4, ox + 440, y, 1, eo(q) * p0)
            sp = eo(pr(t, W_(89), 0.3))
            if sp > 0:
                lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(lay).line([(ox + 440 - 70, y), (ox + 440 - 70 + 140 * sp, y)], fill=RED, width=6); L.alpha_composite(lay)
            q8 = pr(t, W_(91) - 0.1, 0.3)
            if q8 > 0:
                b8 = card(150, 64, outline=Y, r=12, fill=Y + (255,)); v8 = txt('$8.00', 'Black', 40, K)
                b8.alpha_composite(v8, (75 - v8.width // 2, 32 - v8.height // 2)); place(L, b8, ox + 600, y, 0.8 + 0.2 * eb(q8), eo(q8) * p0)
        else:
            vv = txt(val, 'Black', 32, (90, 92, 98)); place(L, vv, ox + 680 - vv.width / 2 - 20, y, 1, eo(q) * p0)
    # stamp
    sq = pr(t, W_(80), 0.25)
    if sq > 0:
        st = R.stamp('APLICA A TODOS', color=(200, 140, 0), size=54)
        place(L, st, CX + 90, 790 + 230, 1.6 - 0.6 * eo(sq), cl(sq * 2) * p0, rot=-10)
    dq = pr(t, W_(82), 0.4)
    if dq > 0:
        pill = card(380, 54, outline=YD, r=27, fill=(0, 0, 0, 0)); pl = txt('DESDE JULIO 2026', 'Bold', 22, Y, track=4)
        pill.alpha_composite(pl, (190 - pl.width // 2, 27 - pl.height // 2)); place(L, pill, CX, 360, 1, eo(dq))

def ac_icon():
    im = Image.new('RGBA', (220, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 20, 210, 110], 16, outline=WH, width=8)
    for k in range(4): d.line([(40, 75 + k * 0), (180, 75)], fill=WH, width=5)
    for k in range(3): d.arc([50 + k * 45, 110, 90 + k * 45, 160], 200, 340, fill=Y, width=6)
    return im
def car_icon():
    im = Image.new('RGBA', (240, 150), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(20, 95), (40, 55), (80, 30), (160, 30), (200, 60), (225, 70), (225, 105), (20, 105)], outline=WH, width=8)
    for x in (65, 180): d.ellipse([x - 22, 88, x + 22, 132], fill=K, outline=WH, width=8)
    d.polygon(R.bolt_pts(120, 68, 22), fill=Y)
    return im
AC, CAR = ac_icon(), car_icon()
def b_small(t, L):  # W101 -> W125
    p0 = eo(pr(t, W_(101), 0.5))
    # small house on top
    hs = 0.62
    place(L, house_cached(0.6, 0, True), W / 2 - 40, 520, 0.55, p0)
    place(L, label('SISTEMA PEQUEÑO', GR), 540, 805, 1, eo(pr(t, W_(106), 0.4)))
    # bars
    prod = 0.45
    cons = 0.5 + 0.18 * eo(pr(t, W_(114), 0.5)) + 0.22 * eo(pr(t, W_(118), 0.5))
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    base = 1170; Hh = 320
    for k, (lab, v, col) in enumerate((('PRODUCCIÓN', prod, Y), ('CONSUMO', cons, (235, 236, 240)))):
        x = 420 + k * 240
        d.rounded_rectangle([x - 60, base - Hh, x + 60, base], 14, fill=(28, 31, 38, int(255 * p0)))
        d.rounded_rectangle([x - 60, base - Hh * v * p0, x + 60, base], 14, fill=col + (int(255 * p0),))
    gap = pr(t, W_(121), 0.4)
    if gap > 0:
        y1 = base - Hh * prod; y2 = base - Hh * cons
        d.rectangle([600, y2, 720, y1], fill=RED + (int(170 * eo(gap)),))
    L.alpha_composite(lay)
    for k, lab in enumerate(('PRODUCCIÓN', 'CONSUMO')):
        place(L, label(lab, GR), 420 + k * 240, base + 30, 1, p0)
    place(L, AC, 880, 860, 0.6 * eb(pr(t, W_(114), 0.35)), 1)
    place(L, CAR, 880, 1030, 0.6 * eb(pr(t, W_(118), 0.35)), 1)
    if gap > 0: place(L, txt('LA DIFERENCIA LA PAGAS', 'Black', 30, RED), 660, base - Hh * cons - 40, 1, eo(gap))

def b_understand(t, L):  # W125 -> W136
    p0 = pr(t, W_(125), 0.45)
    c = card(700, 520, outline=Y, ow=3, fill=(24, 21, 10, 240))
    c.alpha_composite(R.licon('bulb', 150), (275, 50))
    e = txt('ENTIENDE', 'Black', 70, Y); c.alpha_composite(e, (350 - e.width // 2, 230))
    e2 = txt('TU CONSUMO', 'Black', 70, WH); c.alpha_composite(e2, (350 - e2.width // 2, 320))
    l = txt('ANTES DE COMPRAR PLACAS', 'Bold', 24, GR, track=4); c.alpha_composite(l, (350 - l.width // 2, 435))
    em = eio(pr(t, W_(133), 0.5))
    im = c if em < 0.3 else glowed(c, 30, 0.5 * em)
    place(L, im, CX, 800, (0.85 + 0.15 * eb(p0)) * (1 + 0.04 * em), eo(p0))

def b_loop(t, L):  # W136 -> T : rebuild hook state
    enter = pr(t, W_(141), T - 0.15 - W_(141))
    house_scene(L, t, day=1, glow=0.5, flow=0)
    place(L, BILL_Q, 265, 610 + 40 * (1 - eo(enter)), 0.85 * (0.8 + 0.2 * eb(enter)), eo(enter), rot=8)

R.BEATS = [b_hook, b_connected, b_day, b_night, b_meter, b_fixed, b_small, b_understand, b_loop]
R.B = [0, W_(8), W_(17), W_(36), W_(51), W_(70), W_(101), W_(125), W_(136), R.T]

if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        for tt in map(float, sys.argv[2:]): R.frame(int(round(tt * 30))).save('/home/claude/ep002/s_%05.2f.jpg' % tt, quality=88)
    elif sys.argv[1] == 'sfx':
        c = json.load(open('/home/claude/ep002/cfg.json'))
        c['sfx'] = {'whoosh': R.B[1:-1], 'impact': [W_(3), W_(69), W_(91), W_(124), W_(133)], 'pop': [W_(32), W_(48), W_(75), W_(97), W_(114), W_(118)]}
        json.dump(c, open('/home/claude/ep002/cfg.json', 'w'), ensure_ascii=False)
    else:
        a, b, outp = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', '30', '-i', '-',
                              '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', outp], stdin=subprocess.PIPE)
        for i in range(a, b): p.stdin.write(R.frame(i).tobytes())
        p.stdin.close(); sys.exit(p.wait())
