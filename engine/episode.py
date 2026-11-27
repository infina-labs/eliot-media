"""Motor genérico de episodios — EL NEGOCIO DE LA ENERGÍA (Eliot Angueira).
Uso:
  python episode.py SPEC.json stills 1.0 5.0 ...   -> imágenes de control
  python episode.py SPEC.json render                -> video final + portada (todo)
El SPEC define T, words (whisper), audio, ep, keys, beats (escenas por índice de palabra), cover, impacts.
"""
import os, sys, json, math, random, subprocess
SPEC_PATH = os.path.abspath(sys.argv[1])
SPEC = json.load(open(SPEC_PATH))
os.environ['REEL_CFG'] = SPEC_PATH
ENG = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ENG)
import render2 as R
from render2 import *
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

WS = R.WS
def WT(i): return WS[max(0, min(len(WS) - 1, int(i)))]
R.KEY = set(k.upper() for k in SPEC.get('keys', []))
R.CH = R.chunks()
COL = {'y': Y, 'w': (235, 236, 240), 'r': RED, 'g': GR}

# ---------------- extra line icons ----------------
_base_licon = R.licon
def licon(name, sz=96, col=WH):
    if name in ('gen', 'fuel', 'batt', 'wrench', 'panel', 'siren', 'bulb'): return _base_licon(name, sz, col)
    im = Image.new('RGBA', (220, 220), (0, 0, 0, 0)); d = ImageDraw.Draw(im); w = 10
    if name == 'house':
        d.polygon([(30, 105), (110, 35), (190, 105)], outline=col, width=w); d.rectangle([50, 105, 170, 190], outline=col, width=w)
        d.rectangle([95, 135, 125, 190], fill=Y)
    elif name == 'doc':
        d.rounded_rectangle([50, 25, 170, 195], 12, outline=col, width=w)
        for k in range(4): d.line([(75, 65 + k * 30), (145, 65 + k * 30)], fill=col, width=7)
        d.line([(75, 170), (120, 170)], fill=Y, width=9)
    elif name == 'dollar':
        d.ellipse([30, 30, 190, 190], outline=Y, width=w); d.text((110, 112), '$', font=font('Black', 100), fill=col, anchor='mm')
    elif name == 'plant':
        d.rectangle([40, 110, 180, 190], outline=col, width=w)
        for x in (60, 100): d.rectangle([x, 50, x + 22, 110], outline=col, width=8)
        d.ellipse([125, 20, 175, 60], outline=GR, width=6); d.polygon(R.bolt_pts(150, 150, 26), fill=Y)
    elif name == 'tower':
        d.line([(70, 200), (110, 25), (150, 200)], fill=col, width=w); d.line([(55, 70), (165, 70)], fill=col, width=w)
        d.line([(70, 115), (150, 115)], fill=col, width=8); d.line([(84, 150), (150, 200)], fill=col, width=6); d.line([(136, 150), (70, 200)], fill=col, width=6)
    elif name == 'meter':
        d.rounded_rectangle([40, 30, 180, 190], 18, outline=col, width=w); d.rectangle([62, 55, 158, 95], fill=Y)
        d.ellipse([85, 115, 135, 165], outline=col, width=8)
    elif name == 'warning':
        d.polygon([(110, 25), (200, 190), (20, 190)], outline=Y, width=w); d.line([(110, 80), (110, 140)], fill=col, width=12); d.ellipse([102, 155, 118, 171], fill=col)
    elif name == 'people':
        for cx in (75, 145):
            d.ellipse([cx - 22, 45, cx + 22, 89], outline=col, width=8); d.rounded_rectangle([cx - 38, 100, cx + 38, 185], 30, outline=col, width=8)
    elif name == 'key':
        d.ellipse([25, 70, 105, 150], outline=Y, width=w); d.line([(105, 110), (195, 110)], fill=col, width=w)
        d.line([(160, 110), (160, 145)], fill=col, width=w); d.line([(185, 110), (185, 135)], fill=col, width=w)
    elif name == 'bank':
        d.polygon([(25, 80), (110, 30), (195, 80)], outline=col, width=w)
        for x in (50, 90, 130, 170): d.line([(x, 95), (x, 170)], fill=col, width=10)
        d.line([(25, 185), (195, 185)], fill=Y, width=w)
    elif name == 'calendar':
        d.rounded_rectangle([30, 45, 190, 195], 14, outline=col, width=w); d.rectangle([34, 49, 186, 85], fill=Y)
        for x in (70, 150): d.line([(x, 25), (x, 60)], fill=col, width=w)
    elif name == 'sun':
        d.ellipse([70, 70, 150, 150], fill=Y)
        for k in range(8):
            a = math.radians(k * 45); d.line([(110 + 55 * math.cos(a), 110 + 55 * math.sin(a)), (110 + 85 * math.cos(a), 110 + 85 * math.sin(a))], fill=Y, width=8)
    elif name == 'moon':
        d.ellipse([45, 40, 175, 170], fill=(225, 228, 236)); d.ellipse([85, 20, 205, 140], fill=(0, 0, 0, 0))
        m = Image.new('L', (220, 220), 0); ImageDraw.Draw(m).ellipse([85, 20, 205, 140], fill=255)
        im.putalpha(Image.composite(Image.new('L', (220, 220), 0), im.getchannel('A'), m))
    elif name == 'check':
        d.ellipse([25, 25, 195, 195], outline=Y, width=w); d.line([(65, 112), (98, 145), (158, 80)], fill=col, width=14)
    elif name == 'x':
        d.ellipse([25, 25, 195, 195], outline=RED, width=w); d.line([(75, 75), (145, 145)], fill=col, width=14); d.line([(145, 75), (75, 145)], fill=col, width=14)
    elif name == 'fridge':
        d.rounded_rectangle([60, 20, 160, 200], 14, outline=col, width=w); d.line([(60, 85), (160, 85)], fill=col, width=w)
        d.line([(80, 40), (80, 65)], fill=Y, width=9); d.line([(80, 105), (80, 145)], fill=Y, width=9)
    elif name == 'car':
        d.polygon([(20, 135), (45, 90), (85, 65), (150, 65), (185, 95), (205, 105), (205, 145), (20, 145)], outline=col, width=8)
        for x in (65, 165): d.ellipse([x - 20, 128, x + 20, 168], fill=K, outline=col, width=8)
        d.polygon(R.bolt_pts(118, 103, 20), fill=Y)
    elif name == 'ac':
        d.rounded_rectangle([15, 50, 205, 135], 16, outline=col, width=8); d.line([(45, 105), (175, 105)], fill=col, width=5)
        for k in range(3): d.arc([45 + k * 45, 135, 85 + k * 45, 185], 200, 340, fill=Y, width=6)
    elif name == 'shield':
        d.polygon([(110, 20), (185, 50), (175, 140), (110, 200), (45, 140), (35, 50)], outline=col, width=w); d.line([(80, 110), (105, 135), (145, 85)], fill=Y, width=12)
    elif name == 'fan':
        d.ellipse([95, 95, 125, 125], fill=Y)
        for k in range(3):
            a = math.radians(k * 120 - 90); cx, cy = 110 + 50 * math.cos(a), 110 + 50 * math.sin(a)
            d.ellipse([cx - 32, cy - 32, cx + 32, cy + 32], outline=col, width=8)
        d.line([(110, 125), (110, 200)], fill=col, width=8); d.line([(75, 200), (145, 200)], fill=col, width=8)
    elif name == 'question':
        d.ellipse([25, 25, 195, 195], outline=Y, width=w); d.text((110, 112), '?', font=font('Black', 110), fill=col, anchor='mm')
    elif name == 'chart':
        d.line([(30, 190), (195, 190)], fill=col, width=8)
        for k, h in enumerate((50, 90, 70, 130)): d.rectangle([45 + k * 38, 185 - h, 70 + k * 38, 185], fill=Y if k == 3 else col)
    elif name == 'gov':
        d.polygon([(30, 85), (110, 30), (190, 85)], fill=None, outline=col, width=w); d.ellipse([90, 45, 130, 85], outline=Y, width=6)
        for x in (55, 95, 135, 175): d.line([(x, 95), (x, 170)], fill=col, width=10)
        d.line([(30, 185), (190, 185)], fill=col, width=w)
    else:
        d.ellipse([40, 40, 180, 180], outline=col, width=w)
    return im.resize((sz, sz), Image.LANCZOS)
R.licon = licon

# ---------------- appearance logic ----------------
class Ctx:
    def __init__(self, b, mode, t):
        self.b, self.mode, self.t = b, mode, t
        self.dur = b['_end'] - b['_start']
    def ap(self, at, order=0, n=1, d=0.4):
        if self.mode == 'hook': return 1.0
        if self.mode == 'loop':
            span = max(0.3, self.dur - 0.8)
            return pr(self.t, self.b['_start'] + 0.15 + span * (order / max(1, n)), d)
        if at is None: at = self.b['start']
        return pr(self.t, WT(at) - 0.15, d)
    def at_t(self, at):
        return WT(at) if at is not None else self.b['_start']

def pill_img(text, col=YD, fill=(0, 0, 0, 0)):
    tt = txt(text, 'Bold', 21, col, track=4); w = tt.width + 56
    c = card(w, 48, outline=col, r=24, fill=fill); c.alpha_composite(tt, (w // 2 - tt.width // 2, 24 - tt.height // 2)); return c

def title_block(L, c, title, pill, y=380):
    if title:
        p = c.ap(c.b['start'], 0, 6)
        place(L, txt(title, 'Black', 46, WH), CX, y, 1, eo(p))
    if pill:
        p = c.ap(c.b['start'], 0, 6)
        place(L, pill_img(pill), CX, y + 62, 1, eo(p))

# ---------------- scenes ----------------
def sc_statement(L, c, b):
    lines = b['lines']; n = len(lines)
    ys = [CY - (n - 1) * 70 + k * 140 for k in range(n)]
    for k, ln in enumerate(lines):
        p = c.ap(ln.get('at'), k, n)
        if p <= 0: continue
        size = ln.get('size', 150); col = COL.get(ln.get('color', 'w'), WH)
        im = txt(ln['text'], 'bebas', size, col)
        if ln.get('color') == 'y': im = glowed(im, 24, 0.5)
        place(L, im, CX, ln.get('y', ys[k]), 1.25 - 0.25 * eo(p), cl(p * 2))

def sc_icons(L, c, b):
    items = b['items']; n = len(items)
    title_block(L, c, b.get('title'), b.get('pill'))
    cols = 3 if n >= 3 and n != 4 else (2 if n >= 2 else 1)
    rows = math.ceil(n / cols); cw, ch = (300, 330) if cols == 3 else (400, 380) if cols == 2 else (520, 460)
    y0 = CY + 30 - (rows - 1) * (ch + 30) / 2
    for k, it in enumerate(items):
        r_, c_ = divmod(k, cols); m = min(cols, n - r_ * cols)
        x = CX + (c_ - (m - 1) / 2) * (cw + 30); y = y0 + r_ * (ch + 30)
        p = c.ap(it.get('at'), k, n)
        if p <= 0: continue
        hl = it.get('hl', False)
        cd = card(cw, ch, outline=Y if hl else LINE, ow=3 if hl else 2, fill=(24, 21, 10, 240) if hl else (17, 19, 24, 235))
        isz = int(cw * 0.42); cd.alpha_composite(licon(it['icon'], isz), (cw // 2 - isz // 2, int(ch * 0.14)))
        lab = txt(it['label'], 'Black', 38 if cols == 3 else 46, Y if hl else WH)
        if lab.width > cw - 30: lab = lab.resize((cw - 30, int(lab.height * (cw - 30) / lab.width)))
        cd.alpha_composite(lab, (cw // 2 - lab.width // 2, int(ch * 0.66)))
        if it.get('sub'):
            sb = txt(it['sub'], 'Bold', 20, GR, track=3)
            if sb.width > cw - 24: sb = sb.resize((cw - 24, int(sb.height * (cw - 24) / sb.width)))
            cd.alpha_composite(sb, (cw // 2 - sb.width // 2, int(ch * 0.66) + lab.height + 6))
        place(L, cd, x, y + 40 * (1 - eo(p)), 0.85 + 0.15 * eb(p), eo(p))
        if it.get('stamp'):
            sp = c.ap(it.get('stamp_at', it.get('at')), k, n, 0.25) if c.mode != 'normal' else pr(c.t, c.at_t(it.get('stamp_at', it.get('at'))) + 0.3, 0.25)
            if sp > 0: place(L, R.stamp(it['stamp'], size=48), x, y + 20, 1.6 - 0.6 * eo(sp), cl(sp * 2), rot=-12)

def sc_network(L, c, b):
    hub = (CX, 790); Rr = (330, 300); nodes = b['nodes']; n = len(nodes)
    angs = [-150, -30, 180, 0, 150, 30][:n] if n > 4 else [-135, -45, 135, 45][:n]
    pos = [(hub[0] + Rr[0] * math.cos(math.radians(a)), hub[1] + Rr[1] * math.sin(math.radians(a)) * 1.25) for a in angs]
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k, ((px, py), nd) in enumerate(zip(pos, nodes)):
        p = eo(c.ap(nd.get('at'), k + 1, n + 1))
        if p <= 0: continue
        ex, ey = lerp(hub[0], px, p), lerp(hub[1], py, p)
        d.line([hub, (ex, ey)], fill=Y + (150,), width=3)
        for j in range(2):
            u = ((c.t * 0.9) + j * 0.5 + k * 0.17) % 1; qx, qy = lerp(hub[0], ex, u), lerp(hub[1], ey, u)
            d.ellipse([qx - 6, qy - 6, qx + 6, qy + 6], fill=WH + (230,))
    L.alpha_composite(lay)
    hb = Image.new('RGBA', (260, 260), (0, 0, 0, 0)); hd = ImageDraw.Draw(hb)
    hd.ellipse([20, 20, 240, 240], fill=Y)
    if b.get('hub_icon'):
        ic = licon(b['hub_icon'], 110, K); hb.alpha_composite(ic, (75, 45))
    else:
        hd.polygon(R.bolt_pts(130, 112, 62), fill=K)
    lab = b.get('hub', 'APAGÓN'); f = 30 if len(lab) < 10 else 24
    hd.text((130, 200), lab, font=font('Black', f), fill=K, anchor='mm')
    hp = eb(c.ap(b['start'], 0, n + 1))
    place(L, glowed(hb, 30, 0.7), hub[0], hub[1], hp * (1 + 0.03 * math.sin(c.t * 5)))
    for k, ((px, py), nd) in enumerate(zip(pos, nodes)):
        p = c.ap(nd.get('at'), k + 1, n + 1)
        if p > 0: place(L, R.node_img(nd['icon'], nd['label']) if nd['icon'] in ('gen', 'fuel', 'batt', 'wrench', 'panel', 'siren') else node2(nd['icon'], nd['label']), px, py + 20, 0.6 + 0.4 * eb(p), cl(p * 2))

def node2(icon, label, r=74):
    im = Image.new('RGBA', (340, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([170 - r, 80 - r + 10, 170 + r, 80 + r + 10], fill=(16, 18, 22), outline=Y, width=4)
    im.alpha_composite(licon(icon, 92), (170 - 46, 90 - 46))
    lb = txt(label, 'Bold', 24, WH, track=3); im.alpha_composite(lb, (170 - lb.width // 2, 185)); return im

def sc_bars(L, c, b):
    title_block(L, c, b.get('title'), b.get('pill', 'EJEMPLO ILUSTRATIVO'))
    rows = b['rows']; n = len(rows)
    top = 600; gap = 140 if n <= 3 else 115
    place(L, card(940, 120 + gap * n), CX, top - 70 + (120 + gap * n) / 2 - 60, 1, eo(c.ap(b['start'], 0, n + 1)))
    for k, rw in enumerate(rows):
        y = top + k * gap; p = c.ap(rw.get('at'), k + 1, n + 1, 0.9)
        a = eo(c.ap(rw.get('at'), k + 1, n + 1, 0.3))
        if a <= 0: continue
        lb = txt('● ' + rw['label'], 'Bold', 22, GR, track=4); place(L, lb, 130 + lb.width / 2, y - 46, 1, a)
        v = txt(rw.get('value', ''), 'Black', 34, WH); place(L, v, 950 - v.width / 2, y - 46, 1, a)
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        d.rounded_rectangle([130, y - 20, 950, y + 20], 20, fill=(30, 33, 40, int(255 * a)))
        f = rw.get('frac', 0.5) * eo(p)
        if f > 0.01: d.rounded_rectangle([130, y - 20, 130 + 820 * f, y + 20], 20, fill=COL.get(rw.get('color', 'y'), Y) + (int(255 * a),))
        L.alpha_composite(lay)
    if b.get('note'):
        p = c.ap(b.get('note_at'), n + 1, n + 2)
        if p > 0: place(L, txt(b['note'], 'Black', 34, COL.get(b.get('note_color', 'y'), Y)), CX, top + gap * n + 20, 0.9 + 0.1 * eb(p), eo(p))

def sc_bill(L, c, b):
    p0 = eo(c.ap(b['start'], 0, 6))
    rows = b['rows']; n = len(rows)
    hgt = 240 + 110 * n + (120 if b.get('stamp') else 0)
    im = Image.new('RGBA', (720, hgt), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 4, 716, hgt - 4], 22, fill=(236, 236, 230))
    d.text((40, 40), b.get('title', 'FACTURA DE LUZ'), font=font('Black', 40), fill=K)
    if b.get('subtitle'): d.text((40, 96), b['subtitle'], font=font('Bold', 22), fill=(110, 112, 118))
    d.line([(40, 140), (680, 140)], fill=(180, 182, 186), width=3)
    cy = 790; place(L, im, CX, cy + 50 * (1 - p0), 1, p0)
    ox, oy = CX - 360, cy - hgt / 2 + 50 * (1 - p0)
    for k, rw in enumerate(rows):
        q = c.ap(rw.get('at'), k + 1, n + 2)
        if q <= 0: continue
        y = oy + 200 + k * 110
        lt = txt(rw['label'], 'Black', 34, K); place(L, lt, ox + 40 + lt.width / 2, y, 1, eo(q) * p0)
        if rw.get('old'):
            v4 = txt(rw['old'], 'Black', 38, (120, 122, 128)); place(L, v4, ox + 450, y, 1, eo(q) * p0)
            sp = eo(c.ap(rw.get('new_at', rw.get('at')), k + 1, n + 2, 0.3) if c.mode != 'normal' else pr(c.t, c.at_t(rw.get('new_at', rw.get('at'))), 0.3))
            if sp > 0:
                lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(lay).line([(ox + 450 - v4.width / 2, y), (ox + 450 - v4.width / 2 + v4.width * sp, y)], fill=RED, width=6); L.alpha_composite(lay)
                vv = txt(rw['value'], 'Black', 38, K); bx = card(vv.width + 30, 62, outline=Y, r=12, fill=Y + (255,)); bx.alpha_composite(vv, (15, 31 - vv.height // 2))
                place(L, bx, ox + 620, y, 0.8 + 0.2 * eb(sp), sp * p0)
        else:
            vv = txt(rw.get('value', ''), 'Black', 34, (60, 62, 68)); place(L, vv, ox + 680 - vv.width / 2 - 10, y, 1, eo(q) * p0)
    if b.get('stamp'):
        sq = c.ap(b.get('stamp_at'), n + 1, n + 2, 0.25)
        if sq > 0: place(L, R.stamp(b['stamp'], color=(200, 140, 0), size=50), CX + 80, oy + hgt - 100, 1.6 - 0.6 * eo(sq), cl(sq * 2) * p0, rot=-10)
    if b.get('pill'):
        pq = c.ap(b.get('pill_at'), 0, 6)
        if pq > 0: place(L, pill_img(b['pill'], Y), CX, oy - 50, 1, eo(pq))

def sc_compare(L, c, b):
    def mk(side, hl):
        im = card(430, 540, outline=Y if hl else LINE, ow=3 if hl else 2, fill=(24, 21, 10, 240) if hl else (17, 19, 24, 235))
        im.alpha_composite(licon(side['icon'], 150, WH if hl else GR), (140, 60))
        for k, s in enumerate(side['title'] if isinstance(side['title'], list) else [side['title']]):
            e = txt(s, 'Black', 54, Y if hl else GR)
            if e.width > 400: e = e.resize((400, int(e.height * 400 / e.width)))
            im.alpha_composite(e, (215 - e.width // 2, 250 + k * 66))
        for k, s in enumerate(side.get('lines', [])):
            l = txt(s, 'Bold', 24, WH if hl else GR, track=3)
            if l.width > 400: l = l.resize((400, int(l.height * 400 / l.width)))
            im.alpha_composite(l, (215 - l.width // 2, 400 + k * 38))
        return im
    win = b.get('winner', 'left')
    title_block(L, c, b.get('title'), b.get('pill'))
    pl = c.ap(b['left'].get('at'), 0, 3); pr_ = c.ap(b['right'].get('at'), 2, 3); pm = c.ap(b.get('mid_at'), 1, 3, 0.35)
    em = eio(c.ap(b.get('emph_at'), 2, 3, 0.6)) if b.get('emph_at') is not None or c.mode != 'normal' else 0
    for side, x, p, key in ((b['left'], 290, pl, 'left'), (b['right'], 790, pr_, 'right')):
        if p <= 0: continue
        hl = (key == win)
        im = mk(side, hl)
        if hl and em > 0.3: im = glowed(im, 30, 0.45 * em)
        s = (0.85 + 0.15 * eb(p)) * ((1 + 0.08 * em) if hl else (1 - 0.1 * em))
        place(L, im, x, 800, s, eo(p) * (1 if hl else (1 - 0.5 * em)))
    if pm > 0:
        bb = Image.new('RGBA', (110, 110), (0, 0, 0, 0)); bd = ImageDraw.Draw(bb); bd.ellipse([2, 2, 108, 108], fill=Y)
        bd.text((55, 52), b.get('mid', 'VS'), font=font('Black', 44 if len(b.get('mid', 'VS')) > 1 else 70), fill=K, anchor='mm')
        place(L, bb, 540, 800, eb(pm))

def sc_bignum(L, c, b):
    title_block(L, c, b.get('title'), b.get('pill'))
    p = c.ap(b.get('at'), 0, 2, 0.5)
    if p <= 0: return
    val = b['value']
    if b.get('count') and c.mode == 'normal':
        q = eo(pr(c.t, c.at_t(b.get('at')), b.get('count_dur', 1.4)))
        num = b['count']; s = b.get('prefix', '') + format(int(num * q), ',') + b.get('suffix', '')
    else: s = val
    im = glowed(txt(s, 'Black', b.get('size', 150), Y), 30, 0.55)
    place(L, im, CX, 760, 0.85 + 0.15 * eb(p), eo(p))
    if b.get('label'): place(L, txt(b['label'], 'Bold', 26, GR, track=5), CX, 620, 1, eo(p))
    if b.get('sub'):
        q = c.ap(b.get('sub_at'), 1, 2)
        if q > 0: place(L, txt(b['sub'], 'Black', 40, WH), CX, 920, 1, eo(q))

def sc_battery(L, c, b):
    title_block(L, c, b.get('title'), b.get('pill'))
    p = eo(c.ap(b['start'], 0, 2))
    f0, f1 = b.get('from', 1.0), b.get('to', 0.1)
    if c.mode == 'normal': q = eio(pr(c.t, c.at_t(b.get('drain_at')), b.get('drain_dur', 2.5)))
    else: q = 0
    lvl = lerp(f0, f1, q)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    x0, y0, x1, y1 = 380, 520, 700, 1140; a = int(255 * p)
    d.rounded_rectangle([x0, y0, x1, y1], 40, outline=(235, 236, 240, a), width=14)
    d.rounded_rectangle([480, 470, 600, 520], 14, fill=(235, 236, 240, a))
    col = Y if lvl > 0.35 else ((255, 140, 0) if lvl > 0.18 else RED)
    top = y1 - 24 - (y1 - y0 - 48) * lvl
    d.rounded_rectangle([x0 + 24, top, x1 - 24, y1 - 24], 24, fill=col + (a,))
    L.alpha_composite(lay)
    place(L, txt('%d%%' % round(lvl * 100), 'Black', 70, K if lvl > 0.25 else WH), CX, max(top + 60, 840) if lvl > 0.25 else 830, 1, p)
    if b.get('label'):
        ql = c.ap(b.get('label_at'), 1, 2)
        if ql > 0: place(L, pill_img(b['label'], Y), CX, 1200, 1, eo(ql))

def sc_chart(L, c, b):
    title_block(L, c, b.get('title'), b.get('pill', 'EJEMPLO ILUSTRATIVO'))
    p0 = eo(c.ap(b['start'], 0, 3)); cy = 790
    place(L, card(940, 520), CX, cy, 1, p0)
    if b.get('label'):
        lb = txt('● ' + b['label'], 'Bold', 22, Y, track=4); place(L, lb, 100 + lb.width / 2, cy - 220, 1, p0)
    vals = b['values']; n = len(vals)
    x0, x1, yb, yt = 120, 960, cy + 200, cy - 170
    pts = [(x0 + (x1 - x0) * i / (n - 1), yb - (yb - yt) * v) for i, v in enumerate(vals)]
    if c.mode == 'normal': lp = pr(c.t, c.at_t(b.get('draw_at')), b.get('draw_dur', 3.0))
    else: lp = 1.0 if c.mode == 'hook' else pr(c.t, b['_start'], c.dur * 0.7)
    m = lp * (n - 1); k = int(m); dd = pts[:k + 1]
    if k < n - 1: f = m - k; dd = dd + [(lerp(pts[k][0], pts[k + 1][0], f), lerp(pts[k][1], pts[k + 1][1], f))]
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    if len(dd) > 1:
        d.polygon(dd + [(dd[-1][0], yb), (dd[0][0], yb)], fill=COL.get(b.get('color', 'y'), Y) + (int(38 * p0),))
        d.line(dd, fill=COL.get(b.get('color', 'y'), Y) + (int(255 * p0),), width=6, joint='curve')
        for (x, y) in dd[:-1]: d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=WH + (int(255 * p0),))
    L.alpha_composite(lay)
    if b.get('end_label') and lp >= 1:
        place(L, txt(b['end_label'], 'Black', 40, WH), pts[-1][0] - 60, pts[-1][1] - 50, 1, p0)

def sc_focus(L, c, b):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k in range(4):
        ph = ((c.t - b['_start']) * 0.55 + k / 4) % 1; Rr = 40 + 420 * ph
        d.ellipse([CX - Rr, CY - Rr, CX + Rr, CY + Rr], outline=Y + (int(150 * (1 - ph)),), width=3)
    L.alpha_composite(lay)
    dot = Image.new('RGBA', (120, 120), (0, 0, 0, 0)); ImageDraw.Draw(dot).ellipse([30, 30, 90, 90], fill=Y)
    place(L, glowed(dot, 26, 1.0), CX, CY, eb(c.ap(b['start'], 0, 1)))

def sc_city(L, c, b):
    mode = b.get('mode', 'lit')
    if c.mode == 'hook' or mode == 'lit': lvl = 1.0
    elif mode == 'blackout': lvl = 1 - eio(pr(c.t, c.at_t(b.get('at')), 0.8))
    elif mode == 'dark': lvl = 0.0
    else: lvl = eio(pr(c.t, c.at_t(b.get('at')), b.get('dur', 2.5)))
    if c.mode == 'loop': lvl = eio(pr(c.t, b['_start'] + 0.3, max(0.5, c.dur - 1.0)))
    place(L, R.city_frame(lvl, int(c.t * 24)), CX, 820, 1.0)

import importlib.util as _ilu
_HOUSE = None
def house_mod():
    global _HOUSE
    if _HOUSE is None:
        sp = _ilu.spec_from_file_location('ep002h', os.path.join(ENG, 'ep002.py'))
        # ep002 module needs its own cfg; we only borrow drawing helpers
        src = open(os.path.join(ENG, 'ep002.py')).read().split('# ---------- house scene ----------')[1].split('def b_hook')[0]
        g = dict(R.__dict__); g.update(globals()); g['R'] = R; g['BLUE'] = (34, 58, 104)
        exec(src, g); _HOUSE = g
    return _HOUSE
def sc_house(L, c, b):
    h = house_mod()
    day = b.get('day', 1.0)
    if b.get('night_at') is not None and c.mode == 'normal': day = 1 - eio(pr(c.t, c.at_t(b['night_at']), 0.9))
    flow = b.get('flow', 0); fa = 1.0
    if b.get('flow_at') is not None and c.mode == 'normal':
        fa = eo(pr(c.t, c.at_t(b['flow_at']), 0.4)); flow = flow if fa > 0 else 0
    h['house_scene'](L, c.t, day=day, glow=b.get('glow', 0.5) * day, flow=flow, flow_a=fa, small=b.get('small', False))
    if b.get('bill'):
        p = c.ap(b.get('bill_at'), 0, 2)
        place(L, h['bill_card'](b.get('bill_amount', '$???')), 265, 610 + 40 * (1 - eo(p)), 0.85 * (0.8 + 0.2 * eb(p)), eo(p), rot=8)
    if b.get('pill'):
        p = c.ap(b.get('pill_at'), 1, 2)
        if p > 0: place(L, pill_img(b['pill'], Y, (20, 18, 8, 230)), 700, 1180, 0.9 + 0.1 * eb(p), eo(p))

def sc_map(L, c, b):
    ox, oy = 0, 820 - R.PRH // 2
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    reveal = 1.0 if c.mode == 'hook' else eo(pr(c.t, b['_start'] - 0.1, 0.8))
    lit_frac = b.get('lit', 0.14)
    if b.get('relight_at') is not None and c.mode == 'normal': lit_frac = lerp(lit_frac, 0.9, eo(pr(c.t, c.at_t(b['relight_at']), 2.0)))
    for (x, y, r) in R.PRD:
        if (x / W) > reveal * 1.2: continue
        lit = r < lit_frac; tw = 0.6 + 0.4 * math.sin(c.t * 3 + r * 40)
        col = (Y + (int(255 * tw),)) if lit else (70, 74, 84, 255); rad = 4 if lit else 3
        d.ellipse([ox + x - rad, oy + y - rad, ox + x + rad, oy + y + rad], fill=col)
    L.alpha_composite(lay)
    place(L, label(b.get('label', 'PUERTO RICO'), GR), CX, oy + R.PRH + 40, 1, reveal)
    if b.get('pins'):
        for k, pin in enumerate(b['pins']):
            p = c.ap(pin.get('at'), k, len(b['pins']))
            if p <= 0: continue
            x, y = pin['x'] * W, oy + pin['y'] * R.PRH
            dd = Image.new('RGBA', (60, 60), (0, 0, 0, 0)); ImageDraw.Draw(dd).ellipse([10, 10, 50, 50], fill=Y)
            place(L, glowed(dd, 16, 0.8), x, y, eb(p))
            place(L, txt(pin['label'], 'Bold', 24, WH, track=3), x, y - 52, 1, eo(p))

SCENES = {'statement': sc_statement, 'icons': sc_icons, 'network': sc_network, 'bars': sc_bars, 'bill': sc_bill, 'compare': sc_compare,
          'bignum': sc_bignum, 'battery': sc_battery, 'chart': sc_chart, 'focus': sc_focus, 'city': sc_city, 'house': sc_house, 'map': sc_map}

BEATS = SPEC['beats']
for k, b in enumerate(BEATS):
    b['_start'] = 0.0 if k == 0 else WT(b['start'])
    b['_end'] = WT(BEATS[k + 1]['start']) if k + 1 < len(BEATS) else R.T
LOOPB = {'_start': WT(SPEC['loop_start']), '_end': R.T, 'start': SPEC['loop_start']}
LOOPB.update({kk: vv for kk, vv in BEATS[0].items() if not kk.startswith('_') and kk != 'start'})

def make_fn(k):
    b = BEATS[k]
    def fn(t, L):
        mode = 'hook' if k == 0 else 'normal'
        SCENES[b['type']](L, Ctx(b, mode, t), b)
    return fn
def loop_fn(t, L):
    SCENES[LOOPB['type']](L, Ctx(LOOPB, 'loop', t), LOOPB)
R.BEATS = [make_fn(k) for k in range(len(BEATS))] + [loop_fn]
R.B = [b['_start'] for b in BEATS] + [LOOPB['_start'], R.T]

# ---------------- cover ----------------
def make_cover(path):
    sys.path.insert(0, ENG)
    fr = R.BG.copy(); d = ImageDraw.Draw(fr)
    d.rectangle([90, 250, 190, 262], fill=Y)
    fr.alpha_composite(txt('EL NEGOCIO DE LA ENERGÍA', 'Bold', 30, Y, track=7), (86, 286))
    ep = txt(('EP. ' + SPEC['ep'].split('.')[-1]) if '.' in SPEC['ep'] else SPEC['ep'], 'SemiBold', 30, WH); fr.alpha_composite(ep, (W - 90 - ep.width, 286))
    y = 400
    for ln in SPEC['cover']['lines']:
        col = Y if ln.get('color') == 'y' else WH; sz = ln.get('size', 210)
        base = txt(ln['text'], 'bebas', sz, col)
        if base.width > 900: base = base.resize((900, int(base.height * 900 / base.width)));
        im = glowed(base, 26, 0.45) if col == Y else base
        fr.alpha_composite(im, (90 - (im.width - base.width) // 2, y - (im.height - base.height) // 2)); y += base.height + 6
    if SPEC['cover'].get('sub'): fr.alpha_composite(txt(SPEC['cover']['sub'], 'SemiBold', 30, (200, 205, 215), track=4), (92, y + 30))
    d.line([(90, 1470), (990, 1470)], fill=YD, width=3)
    e = txt('ELIOT ', 'Black', 76, WH); a = txt('ANGUEIRA', 'Black', 76, Y)
    fr.alpha_composite(e, (86, 1500)); fr.alpha_composite(a, (86 + e.width - 10, 1500))
    fr.alpha_composite(txt('ENERGY ADVISOR', 'SemiBold', 30, WH, track=10), (90, 1610))
    fr.convert('RGB').save(path, quality=92)

def render_all(outdir):
    os.makedirs(outdir, exist_ok=True)
    n = int(round(R.T * 30)); parts = 4; step = math.ceil(n / parts); procs = []
    for k in range(parts):
        a, bb = k * step, min(n, (k + 1) * step)
        procs.append(subprocess.Popen([sys.executable, __file__, SPEC_PATH, 'chunk', str(a), str(bb), os.path.join(outdir, 'p%d.mp4' % k)]))
    for p in procs:
        if p.wait() != 0: raise SystemExit('chunk failed')
    lst = os.path.join(outdir, 'list.txt'); open(lst, 'w').write(''.join("file 'p%d.mp4'\n" % k for k in range(parts)))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', os.path.join(outdir, 'v.mp4')], check=True)
    # sfx + mix
    sfx = {'whoosh': R.B[1:-1], 'impact': [WT(i) for i in SPEC.get('impacts', [])], 'pop': []}
    for b in BEATS:
        for key in ('items', 'nodes', 'rows'):
            for it in b.get(key, []):
                if it.get('at') is not None: sfx['pop'].append(WT(it['at']))
    cfg = dict(SPEC); cfg['sfx'] = sfx; cfg['mix'] = os.path.join(outdir, 'mix.f32')
    cpath = os.path.join(outdir, 'audio_cfg.json'); json.dump(cfg, open(cpath, 'w'), ensure_ascii=False)
    subprocess.run([sys.executable, os.path.join(ENG, 'audio2.py')], env=dict(os.environ, REEL_CFG=cpath), check=True)
    final = os.path.join(outdir, 'video.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(outdir, 'v.mp4'), '-f', 'f32le', '-ar', '48000', '-ac', '2', '-i', cfg['mix'],
                    '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '23', '-maxrate', '6M', '-bufsize', '12M', '-pix_fmt', 'yuv420p',
                    '-profile:v', 'high', '-level', '4.1', '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', '-shortest', final], check=True)
    make_cover(os.path.join(outdir, 'cover.jpg'))
    for f in ['v.mp4', 'mix.f32', 'list.txt'] + ['p%d.mp4' % k for k in range(parts)]:
        try: os.remove(os.path.join(outdir, f))
        except OSError: pass
    print('OK', final)

if __name__ == '__main__':
    cmd = sys.argv[2]
    if cmd == 'stills':
        od = os.path.join(os.path.dirname(SPEC_PATH), 'stills'); os.makedirs(od, exist_ok=True)
        for tt in map(float, sys.argv[3:]): R.frame(int(round(tt * 30))).save(os.path.join(od, 's_%05.2f.jpg' % tt), quality=85)
    elif cmd == 'chunk':
        a, bb, outp = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', '30', '-i', '-',
                              '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', outp], stdin=subprocess.PIPE)
        for i in range(a, bb): p.stdin.write(R.frame(i).tobytes())
        p.stdin.close(); sys.exit(p.wait())
    elif cmd == 'cover':
        make_cover(os.path.join(os.path.dirname(SPEC_PATH), 'cover.jpg'))
    elif cmd == 'render':
        render_all(os.path.dirname(SPEC_PATH))
