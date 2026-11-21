#!/usr/bin/env python3
"""Draw the front page of THE WORLD TODAY for Saturday 21 November 2026.

Writes one 1024x1024 PNG to $MAKEFUN_OUTPUT_DIR/entry.png (``/output``
when the variable is unset). The page sums up six stories that happened
or were first reported on Saturday 21 November 2026:

  1. Russia launches a huge attack on Ukraine -- 400+ drones and 110
     missiles; two missiles and a suspected drone come down in Poland.
  2. The International Court of Justice finds Myanmar committed
     genocide against the Rohingya people.
  3. An AI stock sell-off pushes the S&P 500 into correction; the
     Nasdaq falls 5.3% in a day.
  4. The COP31 climate talks in Antalya run past their deadline,
     deadlocked over fossil fuels.
  5. A strong earthquake shakes the Peruvian Andes.
  6. The UK and the EU sign their biggest post-Brexit agreements in
     Brussels: three deals on food, carbon and youth mobility.

Everything is drawn in code: a plain RGB canvas, a bitmap font defined
below by hand (5x7 glyphs, no font file, no image file, no network),
simple geometric illustrations per story, and a hand-written PNG
encoder. Standard library only. No randomness, no timestamps, no
network: two runs produce byte-identical output.
"""

import hashlib
import os
import struct
import zlib

W, H = 1024, 1024
MAX_FILE_SIZE = 1024 * 1024  # 1 MiB

PAPER = (248, 244, 232)
INK = (26, 26, 26)
MUTED = (96, 90, 78)
RED = (163, 22, 33)
PANEL = (255, 255, 255)
EDGE = (198, 192, 176)
SKY = (205, 228, 240)
NAVY = (18, 30, 58)
SLATE = (70, 90, 120)
GOLD = (212, 175, 55)
EUBLUE = (0, 51, 153)
GREEN = (46, 125, 50)
TAN = (210, 180, 140)
DARK = (16, 24, 48)
ORANGE = (232, 120, 30)
YELLOW = (245, 200, 60)
LIGHTBLUE = (170, 205, 235)
BROWN = (120, 85, 50)
GREY = (140, 140, 140)


class Canvas:
    """A plain RGB canvas backed by one bytearray per row."""

    def __init__(self, width, height, bg):
        self.w = width
        self.h = height
        self.rows = [bytearray(bg * width) for _ in range(height)]
        self.cx0, self.cy0, self.cx1, self.cy1 = 0, 0, width, height

    def clip_to(self, x, y, w, h):
        self.cx0, self.cy0 = max(0, x), max(0, y)
        self.cx1, self.cy1 = min(self.w, x + w), min(self.h, y + h)

    def unclip(self):
        self.cx0, self.cy0, self.cx1, self.cy1 = 0, 0, self.w, self.h

    def set_pixel(self, x, y, color):
        if self.cx0 <= x < self.cx1 and self.cy0 <= y < self.cy1:
            row = self.rows[y]
            row[x * 3] = color[0]
            row[x * 3 + 1] = color[1]
            row[x * 3 + 2] = color[2]

    def fill_rect(self, x, y, w, h, color):
        x0 = max(self.cx0, x)
        y0 = max(self.cy0, y)
        x1 = min(self.cx1, x + w)
        y1 = min(self.cy1, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        fill = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            row = self.rows[yy]
            row[x0 * 3:x1 * 3] = fill

    def rect(self, x, y, w, h, color, thick=1):
        self.fill_rect(x, y, w, thick, color)
        self.fill_rect(x, y + h - thick, w, thick, color)
        self.fill_rect(x, y, thick, h, color)
        self.fill_rect(x + w - thick, y, thick, h, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        r = thick // 2
        while True:
            self.fill_rect(x0 - r, y0 - r, thick, thick, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            half = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - half, yy, half * 2 + 1, 1, color)

    def ring(self, cx, cy, r, color, thick=2):
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            outer = int((r * r - dy * dy) ** 0.5)
            inner2 = (r - thick) * (r - thick) - dy * dy
            inner = int(inner2 ** 0.5) if inner2 > 0 else 0
            self.fill_rect(cx - outer, yy, outer - inner, 1, color)
            self.fill_rect(cx + inner + 1, yy, outer - inner, 1, color)

    def triangle(self, p0, p1, p2, color):
        (x0, y0), (x1, y1), (x2, y2) = sorted(
            (p0, p1, p2), key=lambda p: p[1])
        if y2 == y0:
            return
        for yy in range(max(y0, self.cy0), min(y2 + 1, self.cy1)):
            if yy < y1:
                t = (yy - y0) / (y1 - y0) if y1 != y0 else 0.0
                xa = x0 + (x1 - x0) * t
                xb = x0 + (x2 - x0) * ((yy - y0) / (y2 - y0))
            else:
                t = (yy - y1) / (y2 - y1) if y2 != y1 else 0.0
                xa = x1 + (x2 - x1) * t
                xb = x0 + (x2 - x0) * ((yy - y0) / (y2 - y0))
            lo, hi = int(min(xa, xb)), int(max(xa, xb))
            self.fill_rect(lo, yy, hi - lo + 1, 1, color)


# ---------------------------------------------------------------------------
# Bitmap font: 5x7 glyphs defined by hand in this file. '#' is ink, '.' is
# blank. Only upper-case letters, digits and the punctuation the page uses.
# ---------------------------------------------------------------------------
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
}

CHAR_W = 5
CHAR_H = 7
CHAR_ADV = 6  # glyph width + 1px gap, before scaling


def text_width(text, scale):
    return len(text) * CHAR_ADV * scale - scale


def draw_text(canvas, x, y, text, scale, color):
    """Draw text with its top-left corner at (x, y). Text is upper-case."""
    cx = x
    for ch in text:
        glyph = FONT.get(ch)
        if glyph is None:
            cx += CHAR_ADV * scale
            continue
        for row_i, row in enumerate(glyph):
            for col_i, bit in enumerate(row):
                if bit == '1':
                    canvas.fill_rect(
                        cx + col_i * scale, y + row_i * scale,
                        scale, scale, color)
        cx += CHAR_ADV * scale


def wrap_text(text, max_width, scale):
    """Greedy word wrap; returns a list of lines fitting max_width."""
    words = text.split(' ')
    lines = []
    cur = ''
    for word in words:
        trial = word if not cur else cur + ' ' + word
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------------------
# Story pictograms. Each draws inside a box (x, y, w, h) with its own sky.
# ---------------------------------------------------------------------------

def pic_strike(c, x, y, w, h):
    """Night sky, explosion burst, missile streaks, city silhouettes."""
    c.fill_rect(x, y, w, h, NAVY)
    for sx, sy in ((18, 16), (70, 30), (150, 12), (230, 26), (285, 14),
                   (40, 48), (200, 44), (260, 55), (110, 20)):
        c.fill_rect(x + sx, y + sy, 3, 3, (255, 255, 255))
    cx, cy = x + w // 2 - 30, y + 58
    for k in range(12):
        ang = k * 30.0
        import math
        dx = math.cos(math.radians(ang))
        dy = math.sin(math.radians(ang))
        c.line(int(cx), int(cy), int(cx + dx * 52), int(cy + dy * 52),
               ORANGE if k % 2 == 0 else YELLOW, 5)
    c.disc(cx, cy, 20, YELLOW)
    c.disc(cx, cy, 11, ORANGE)
    c.line(x + 40, y + 30, x + 130, y + 78, (255, 255, 255), 3)
    c.line(x + 200, y + 22, x + 260, y + 60, (255, 255, 255), 3)
    for bx, bw, bh in ((0, 52, 46), (56, 44, 62), (104, 60, 40),
                       (168, 48, 56), (220, 56, 44), (280, 42, 60)):
        c.fill_rect(x + bx, y + h - bh, bw, bh, (10, 16, 34))
        for wy in range(y + h - bh + 8, y + h - 6, 14):
            for wx in range(x + bx + 8, x + bx + bw - 8, 16):
                c.fill_rect(wx, wy, 5, 6, YELLOW)


def pic_justice(c, x, y, w, h):
    """Scales of justice on a pale courtroom background."""
    c.fill_rect(x, y, w, h, (232, 226, 208))
    c.fill_rect(x, y + h - 14, w, 14, BROWN)
    cx = x + w // 2
    c.fill_rect(cx - 4, y + 22, 8, h - 40, GOLD)
    c.fill_rect(cx - 90, y + 30, 180, 7, GOLD)
    c.disc(cx, y + 26, 9, GOLD)
    for side in (-1, 1):
        px = cx + side * 78
        c.line(px, y + 37, px, y + 78, INK, 2)
        c.line(cx + side * 62, y + 37, px, y + 78, INK, 2)
        c.line(cx + side * 94, y + 37, px, y + 78, INK, 2)
        c.triangle((px - 42, y + 78), (px + 42, y + 78), (px, y + 108),
                   GOLD)
        c.fill_rect(px - 42, y + 76, 84, 4, INK)
    c.fill_rect(cx - 26, y + h - 26, 52, 10, GOLD)


def pic_markets(c, x, y, w, h):
    """Falling red chart line over grey bars."""
    c.fill_rect(x, y, w, h, PANEL)
    base = y + h - 22
    bars = (58, 74, 66, 88, 70, 96, 78, 104)
    bw = 26
    for i, bh in enumerate(bars):
        bx = x + 16 + i * 36
        c.fill_rect(bx, base - bh, bw, bh, (205, 205, 205))
    pts = [(x + 22, y + 26), (x + 66, y + 40), (x + 110, y + 34),
           (x + 154, y + 62), (x + 198, y + 78), (x + 242, y + 96),
           (x + 292, y + 122)]
    for a, b in zip(pts, pts[1:]):
        c.line(a[0], a[1], b[0], b[1], RED, 5)
    ex, ey = pts[-1]
    c.triangle((ex - 14, ey - 12), (ex + 12, ey + 2), (ex - 2, ey + 14),
               RED)
    c.fill_rect(x, base, w, 3, INK)


def pic_climate(c, x, y, w, h):
    """Globe with a hot sun, over a warming land strip."""
    c.fill_rect(x, y, w, h, SKY)
    cx, cy = x + w // 2 - 20, y + h // 2 + 4
    sx, sy = x + w - 52, y + 22
    c.disc(sx, sy, 22, ORANGE)
    for k in range(8):
        import math
        ang = k * 45.0
        dx = math.cos(math.radians(ang))
        dy = math.sin(math.radians(ang))
        c.line(int(sx + dx * 26), int(sy + dy * 26),
               int(sx + dx * 36), int(sy + dy * 36), ORANGE, 4)
    c.disc(cx, cy, 58, (58, 130, 200))
    c.ring(cx, cy, 58, (30, 90, 160), 3)
    c.disc(cx - 26, cy - 18, 16, GREEN)
    c.disc(cx + 22, cy + 12, 20, GREEN)
    c.disc(cx - 4, cy + 30, 12, GREEN)
    c.fill_rect(x, y + h - 18, w, 18, TAN)
    c.fill_rect(x, y + h - 18, w, 3, BROWN)


def pic_quake(c, x, y, w, h):
    """Andes mountains split by a jagged crack."""
    c.fill_rect(x, y, w, h, (238, 228, 205))
    c.disc(x + w - 46, y + 26, 20, YELLOW)
    c.triangle((x + 6, y + h - 16), (x + 110, y + 18), (x + 214, y + h - 16),
               (96, 110, 130))
    c.triangle((x + 120, y + h - 16), (x + 210, y + 34), (x + 316, y + h - 16),
               SLATE)
    c.triangle((x + 96, y + 32), (x + 110, y + 18), (x + 126, y + 34),
               (255, 255, 255))
    c.triangle((x + 196, y + 46), (x + 210, y + 34), (x + 226, y + 48),
               (255, 255, 255))
    cx = x + w // 2
    crack = [(cx - 6, y + 70), (cx + 8, y + 88), (cx - 8, y + 104),
             (cx + 6, y + 120), (cx - 4, y + h - 16)]
    for a, b in zip(crack, crack[1:]):
        c.line(a[0], a[1], b[0], b[1], INK, 4)
    for mx, my in ((x + 30, y + 30), (x + 280, y + 40), (x + 60, y + 60)):
        c.line(mx, my, mx + 16, my, INK, 3)
        c.line(mx + 4, my - 6, mx + 12, my + 6, INK, 2)
    c.fill_rect(x, y + h - 16, w, 16, BROWN)


def pic_flags(c, x, y, w, h):
    """EU flag and Union Jack side by side, joined by a green check."""
    c.fill_rect(x, y, w, h, (232, 226, 208))
    fx, fy, fw, fh = x + 18, y + 34, 122, 78
    c.fill_rect(fx, fy, fw, fh, EUBLUE)
    c.rect(fx, fy, fw, fh, INK, 2)
    import math
    ccx, ccy = fx + fw // 2, fy + fh // 2
    for k in range(12):
        ang = math.radians(k * 30 - 90)
        c.disc(int(ccx + 30 * math.cos(ang)),
               int(ccy + 24 * math.sin(ang)), 4, YELLOW)
    ux, uy, uw, uh = x + w - 140, y + 34, 122, 78
    c.fill_rect(ux, uy, uw, uh, (30, 60, 140))
    c.rect(ux, uy, uw, uh, INK, 2)
    c.line(ux, uy, ux + uw, uy + uh, (255, 255, 255), 10)
    c.line(ux + uw, uy, ux, uy + uh, (255, 255, 255), 10)
    c.line(ux, uy, ux + uw, uy + uh, RED, 4)
    c.line(ux + uw, uy, ux, uy + uh, RED, 4)
    c.fill_rect(ux + uw // 2 - 7, uy, 14, uh, (255, 255, 255))
    c.fill_rect(ux, uy + uh // 2 - 7, uw, 14, (255, 255, 255))
    c.fill_rect(ux + uw // 2 - 4, uy, 8, uh, RED)
    c.fill_rect(ux, uy + uh // 2 - 4, uw, 8, RED)
    hx, hy = x + w // 2, y + h - 22
    c.disc(hx, hy, 15, GREEN)
    c.line(hx - 7, hy, hx - 1, hy + 6, (255, 255, 255), 4)
    c.line(hx - 1, hy + 6, hx + 8, hy - 7, (255, 255, 255), 4)


# ---------------------------------------------------------------------------
# Panels and page layout
# ---------------------------------------------------------------------------

def draw_panel(canvas, x, y, w, h, kicker, kicker_color, title, caption,
               pic_fn):
    canvas.fill_rect(x, y, w, h, PANEL)
    canvas.rect(x, y, w, h, EDGE, 2)
    canvas.fill_rect(x, y, w, 34, kicker_color)
    draw_text(canvas, x + 12, y + 8, kicker.upper(), 2, (255, 255, 255))
    pic_fn(canvas, x + 2, y + 36, w - 4, 146)
    ty = y + 194
    # The bitmap font holds upper-case glyphs only: normalise here so a
    # mixed-case story line can never render as scattered fragments.
    for line in wrap_text(title.upper(), w - 24, 3):
        draw_text(canvas, x + 12, ty, line, 3, INK)
        ty += 26
    ty += 6
    for line in wrap_text(caption.upper(), w - 24, 2):
        draw_text(canvas, x + 12, ty, line, 2, (52, 52, 52))
        ty += 17


STORIES = [
    ("UKRAINE", NAVY,
     "RUSSIA STRIKES UKRAINE",
     "400+ drones and 110 missiles hit Kyiv, debris falls in Poland.",
     pic_strike),
    ("THE HAGUE", (90, 60, 30),
     "MYANMAR GUILTY OF GENOCIDE",
     "World Court rules Myanmar committed genocide against the Rohingya.",
     pic_justice),
    ("MARKETS", RED,
     "MARKETS TUMBLE ON AI SELL-OFF",
     "S&P 500 falls into correction, Nasdaq drops 5.3% in a day.",
     pic_markets),
    ("CLIMATE", (30, 110, 70),
     "COP31 TALKS DEADLOCKED",
     "Climate summit in Antalya runs past deadline over fossil fuels.",
     pic_climate),
    ("PERU", BROWN,
     "STRONG QUAKE HITS PERU",
     "Powerful earthquake shakes the Peruvian Andes, people flee outside.",
     pic_quake),
    ("EUROPE", EUBLUE,
     "UK AND EU SIGN POST-BREXIT DEAL",
     "Three agreements on food, carbon and youth mobility in Brussels.",
     pic_flags),
]


def draw_page():
    c = Canvas(W, H, PAPER)
    c.rect(0, 0, W, H, INK, 4)
    # Masthead
    title = "THE WORLD TODAY"
    tw = text_width(title, 7)
    draw_text(c, (W - tw) // 2, 26, title, 7, INK)
    c.fill_rect(28, 92, W - 56, 4, RED)
    date = "SATURDAY 21 NOVEMBER 2026"
    dw = text_width(date, 3)
    draw_text(c, (W - dw) // 2, 106, date, 3, RED)
    sub = "SIX STORIES FROM AROUND THE WORLD - THE DAY IN ONE PAGE"
    sw = text_width(sub, 2)
    draw_text(c, (W - sw) // 2, 138, sub, 2, MUTED)
    c.fill_rect(28, 162, W - 56, 2, EDGE)
    # Story grid: 3 columns x 2 rows
    margin, gap = 16, 12
    pw = (W - 2 * margin - 2 * gap) // 3
    ph = 404
    for i, story in enumerate(STORIES):
        col, row = i % 3, i // 3
        px = margin + col * (pw + gap)
        py = 176 + row * (ph + gap)
        draw_panel(c, px, py, pw, ph, *story)
    # Footer
    foot = "SOURCES: AP, REUTERS, BBC, FRANCE 24 - 21 NOVEMBER 2026"
    fw = text_width(foot, 1)
    draw_text(c, (W - fw) // 2, 1006, foot, 1, MUTED)
    return c


# ---------------------------------------------------------------------------
# PNG encoding (hand-written, standard library only) and entry point
# ---------------------------------------------------------------------------

def png_bytes(canvas):
    def chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data +
                struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes(row) for row in canvas.rows)
    comp = zlib.compress(raw, 6)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def validate_png(data):
    """Re-parse the PNG we just encoded; raise on any structural flaw."""
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "bad PNG signature"
    pos = 8
    seen = []
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        (crc,) = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])
        assert zlib.crc32(typ + body) & 0xFFFFFFFF == crc, "bad CRC: %r" % typ
        seen.append(typ)
        if typ == b"IHDR":
            (w, h, depth, ctype) = struct.unpack(">IIBB", body[:10])
            assert (w, h) == (W, H), "bad dimensions"
            assert depth == 8 and ctype == 2, "bad colour type"
        pos += 12 + length
    assert seen[0] == b"IHDR" and seen[-1] == b"IEND", "missing chunks"
    assert len(data) <= MAX_FILE_SIZE, "file over 1 MiB"


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    data = png_bytes(draw_page())
    validate_png(data)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes, sha256 %s)"
          % (path, len(data), hashlib.sha256(data).hexdigest()))


if __name__ == "__main__":
    main()
