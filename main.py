#!/usr/bin/env python3
"""Draw one newspaper front page summing up the world's news of
Wednesday 18 November 2026, as a 1024x1024 PNG.

Standard library only. No network, no randomness, no clock: two runs
write byte-identical files. Usage:
    MAKEFUN_OUTPUT_DIR=out python3 main.py   # writes out/entry.png
"""

import binascii
import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 242, 231)   # newsprint cream
INK = (22, 22, 22)        # headline black
RED = (176, 32, 32)       # kicker / date red
BLUE = (38, 84, 124)      # sea and sky blue
SKY = (176, 205, 224)     # pale sky
SAND = (214, 196, 160)    # land tan
GREY = (110, 110, 108)    # secondary grey
LGREY = (226, 220, 208)   # panel tint
WHITE = (255, 255, 255)
GREEN = (46, 110, 62)
GOLD = (212, 160, 40)
DARKBLUE = (30, 58, 95)

# ------------------------------------------------------- 5x7 bitmap font
# Each glyph is 7 rows of 5 pixels; "#" is on, "." is off. Only the
# characters this page needs are defined; anything else draws blank.
_G = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "00000", "01100"),
    ",": ("00000", "00000", "00000", "00000", "00100", "00100", "01000"),
    ":": ("00000", "01100", "00000", "00000", "00000", "01100", "00000"),
    ";": ("00000", "01100", "00000", "00000", "01100", "01100", "01000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "•": ("00000", "00000", "01100", "01100", "01100", "00000", "00000"),
    "~": ("00000", "00000", "01001", "10110", "00000", "00000", "00000"),
}
BLANK = ("00000",) * 7


def glyph(ch):
    return _G.get(ch.upper(), BLANK)


# ------------------------------------------------------------ the canvas
class Page:
    """A flat RGB canvas with small vector-drawing helpers."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bytes(bg)) * (w * h)

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def hline(self, x, y, w, c, t=1):
        self.fill(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill(x, y, t, h, c)

    def rect(self, x, y, w, h, c, t=1):
        self.hline(x, y, w, c, t)
        self.hline(x, y + h - t, w, c, t)
        self.vline(x, y, h, c, t)
        self.vline(x + w - t, y, h, c, t)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.fill(x0 - t // 2, y0 - t // 2, t, t, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.put(xx, yy, c)

    def ring(self, cx, cy, r, c, t=2):
        for yy in range(cy - r - 1, cy + r + 2):
            for xx in range(cx - r - 1, cx + r + 2):
                d = math.hypot(xx - cx, yy - cy)
                if r - t < d <= r:
                    self.put(xx, yy, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for yy in range(cy - ry, cy + ry + 1):
            for xx in range(cx - rx, cx + rx + 1):
                if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1:
                    self.put(xx, yy, c)

    def poly(self, pts, c):
        """Scanline fill of a simple polygon."""
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.fill(int(math.ceil(xs[j])), y,
                          int(math.floor(xs[j + 1])) - int(math.ceil(xs[j])) + 1,
                          1, c)

    def star(self, cx, cy, r, c):
        pts = []
        for k in range(10):
            ang = -math.pi / 2 + k * math.pi / 5
            rr = r if k % 2 == 0 else r * 0.42
            pts.append((cx + int(rr * math.cos(ang)),
                        cy + int(rr * math.sin(ang))))
        self.poly(pts, c)

    def arc(self, cx, cy, r, a0, a1, c, t=3, step=4):
        a = a0
        while a <= a1:
            rad = math.radians(a)
            self.disc(cx + int(r * math.cos(rad)),
                      cy + int(r * math.sin(rad)), t, c)
            a += step


# ------------------------------------------------------------------ text
def text_w(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(pg, x, y, s, scale, c):
    """Draw s at (x, y); y is the top of the 7-pixel cap height."""
    cx = x
    for ch in s:
        g = glyph(ch)
        for row in range(7):
            bits = g[row]
            for col in range(5):
                if bits[col] == "1":
                    pg.fill(cx + col * scale, y + row * scale,
                            scale, scale, c)
        cx += 6 * scale
    return cx


def draw_center(pg, cx, y, s, scale, c):
    return draw_text(pg, cx - text_w(s, scale) // 2, y, s, scale, c)


def wrap(s, scale, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_block(pg, x, y, lines, scale, c, lead=4):
    for ln in lines:
        draw_text(pg, x, y, ln, scale, c)
        y += 7 * scale + lead
    return y


# ------------------------------------------------------------------- PNG
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    return out + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)


def write_png(pg, path):
    raw = bytearray()
    stride = pg.w * 3
    for y in range(pg.h):
        raw.append(0)  # filter: none
        raw += pg.px[y * stride:(y + 1) * stride]
    data = b"\x89PNG\r\n\x1a\n"
    data += _chunk(b"IHDR", struct.pack(">IIBBBBB", pg.w, pg.h, 8, 2, 0, 0, 0))
    data += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    data += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


# ----------------------------------------------------------- illustrations
def draw_flag_us(pg, x, y, w, h):
    stripe = max(1, h // 7)
    for i in range(7):
        pg.fill(x, y + i * stripe, w, stripe,
                RED if i % 2 == 0 else WHITE)
    pg.fill(x, y, w * 2 // 5, stripe * 4, DARKBLUE)
    for r in range(4):
        for c in range(5):
            pg.put(x + 3 + c * 5, y + 3 + r * 4, WHITE)


def draw_flag_cn(pg, x, y, w, h):
    pg.fill(x, y, w, h, RED)
    pg.star(x + w // 4, y + h // 2, h // 4, GOLD)
    for dx, dy in ((w * 3 // 5, h // 4), (w * 3 // 4, h // 3),
                   (w * 3 // 4, h * 3 // 5), (w * 3 // 5, h * 3 // 4)):
        pg.disc(x + dx, y + dy, 2, GOLD)


def draw_flag_ru(pg, x, y, w, h):
    third = h // 3
    pg.fill(x, y, w, third, WHITE)
    pg.fill(x, y + third, w, third, BLUE)
    pg.fill(x, y + 2 * third, w, h - 2 * third, RED)


def draw_lead_art(pg, x, y, w, h):
    """Airplane descending over a Shenzhen skyline, three summit flags."""
    pg.fill(x, y, w, h, SKY)
    # sun and clouds
    pg.disc(x + w - 30, y + 22, 14, GOLD)
    pg.ellipse(x + 70, y + 34, 34, 9, WHITE)
    pg.ellipse(x + 96, y + 34, 26, 8, WHITE)
    pg.ellipse(x + w - 150, y + 78, 30, 8, WHITE)
    # skyline silhouettes
    base = y + h - 58
    towers = [(0, 96), (34, 130), (74, 84), (108, 150), (150, 108),
              (188, 138), (224, 92), (258, 128), (292, 104)]
    for tx, th in towers:
        pg.fill(x + tx, base - th, 30, th, DARKBLUE)
        for wy in range(base - th + 10, base - 8, 16):
            for wx in range(x + tx + 6, x + tx + 26, 10):
                pg.put(wx, wy, GOLD)
    # ground band
    pg.fill(x, base, w, h - (base - y), (52, 84, 60))
    # airplane, nose pointing right-down toward the city
    ax, ay = x + 66, y + 96
    pg.poly([(ax, ay), (ax + 118, ay + 12), (ax + 128, ay + 20),
             (ax + 118, ay + 26), (ax, ay + 16)], WHITE)
    pg.poly([(ax + 52, ay + 6), (ax + 88, ay - 26), (ax + 100, ay - 24),
             (ax + 76, ay + 10)], (200, 208, 216))
    pg.poly([(ax + 104, ay + 10), (ax + 126, ay - 12), (ax + 132, ay - 10),
             (ax + 122, ay + 14)], (200, 208, 216))
    pg.line(ax + 8, ay + 14, ax + 108, ay + 24, RED, 3)
    for wx in range(ax + 22, ax + 96, 12):
        pg.disc(wx, ay + 8 + (wx - ax) // 12, 2, DARKBLUE)
    # dashed flight path behind the plane
    for i in range(0, 46, 8):
        pg.fill(x + 8 + i, y + 82 - i // 3, 5, 2, INK)
    # three flags on poles above the skyline, labels on open sky
    fx, fy = x + 14, base - 200
    for i, fn in enumerate((draw_flag_us, draw_flag_cn, draw_flag_ru)):
        px = fx + i * 108
        pg.vline(px, fy, 58, INK, 3)
        fn(pg, px + 3, fy, 62, 34)
        draw_text(pg, px + 3, fy + 40, ("USA", "CHN", "RUS")[i], 1, INK)


def draw_gulf_art(pg, x, y, w, h):
    """Drone above a tanker on a troubled strait."""
    pg.fill(x, y, w, h, SKY)
    pg.disc(x + w - 26, y + 22, 12, GOLD)
    pg.fill(x, y + h - 52, w, 52, BLUE)
    for wy in (y + h - 44, y + h - 30, y + h - 16):
        for wx in range(x + 6, x + w - 10, 26):
            pg.line(wx, wy, wx + 12, wy, WHITE, 2)
    # tanker
    tx, ty = x + 18, y + h - 74
    pg.poly([(tx, ty + 22), (tx + 116, ty + 22), (tx + 106, ty + 40),
             (tx + 8, ty + 40)], INK)
    pg.fill(tx + 8, ty, 12, 22, WHITE)
    pg.fill(tx + 24, ty + 4, 22, 18, RED)
    pg.fill(tx + 50, ty + 4, 22, 18, GOLD)
    pg.fill(tx + 76, ty + 4, 22, 18, (90, 140, 90))
    # drone with a dashed strike path down to the tanker
    dx, dy = x + w - 46, y + 26
    pg.fill(dx - 12, dy - 4, 24, 8, INK)
    pg.line(dx - 18, dy - 8, dx - 6, dy - 4, INK, 2)
    pg.line(dx + 6, dy - 4, dx + 18, dy - 8, INK, 2)
    pg.line(dx - 20, dy - 10, dx - 2, dy - 10, INK, 2)
    pg.line(dx + 2, dy - 10, dx + 20, dy - 10, INK, 2)
    for i in range(0, 56, 10):
        pg.fill(dx - 4 + (i % 14), dy + 8 + i, 4, 3, RED)
    # blast star at the tanker deck
    pg.star(tx + 62, ty + 14, 12, GOLD)


def draw_bridge_art(pg, x, y, w, h):
    """Kerch bridge with a span dropped into the strait."""
    pg.fill(x, y, w, h, SKY)
    pg.disc(x + 24, y + 20, 11, GOLD)
    pg.fill(x, y + h - 34, w, 34, BLUE)
    for wy in (y + h - 26, y + h - 12):
        for wx in range(x + 6, x + w - 10, 24):
            pg.line(wx, wy, wx + 11, wy, WHITE, 2)
    deck = y + h - 62
    # left deck and right deck, gap in the middle
    pg.fill(x + 4, deck, 52, 6, INK)
    pg.fill(x + w - 56, deck, 52, 6, INK)
    pg.vline(x + 14, deck + 6, 24, INK, 4)
    pg.vline(x + w - 18, deck + 6, 24, INK, 4)
    # fallen span, tilted down into the water
    pg.line(x + 58, deck, x + w - 60, deck + 26, INK, 5)
    pg.line(x + 58, deck, x + 76, deck + 30, RED, 3)
    # splash where the span hit
    for a in range(200, 341, 24):
        rad = math.radians(a)
        pg.line(x + w // 2, y + h - 34,
                x + w // 2 + int(26 * math.cos(rad)),
                y + h - 34 + int(14 * math.sin(rad)), WHITE, 2)
    # crack marks on the standing decks
    pg.line(x + 30, deck, x + 36, deck - 12, RED, 2)
    pg.line(x + w - 34, deck, x + w - 28, deck - 12, RED, 2)


def draw_gaza_art(pg, x, y, w, h):
    """Stylised Gaza map: sea, land, three operation markers."""
    pg.fill(x, y, w, h, BLUE)
    pg.poly([(x + 34, y), (x + w, y), (x + w, y + h), (x + 58, y + h),
             (x + 40, y + h // 2)], SAND)
    pg.line(x + 34, y, x + 58, y + h, WHITE, 2)
    for i, (mx, my) in enumerate(((x + 96, y + 30), (x + 112, y + 78),
                                  (x + 92, y + 122))):
        pg.disc(mx, my, 11, RED)
        pg.ring(mx, my, 16, RED, 2)
        draw_text(pg, mx - 3, my - 5, str(i + 1), 1, WHITE)
    draw_text(pg, x + 8, y + h - 16, "GAZA", 2, WHITE)


def draw_cyclone_art(pg, x, y, w, h):
    """Spiral cyclone over the Bay of Bengal coast."""
    pg.fill(x, y, w, h, SKY)
    pg.fill(x, y + h - 30, w, 30, SAND)
    pg.line(x, y + h - 30, x + w, y + h - 30, GREEN, 2)
    # tiny shelters along the coast
    for sx in range(x + 12, x + w - 20, 34):
        pg.poly([(sx, y + h - 30), (sx + 8, y + h - 42),
                 (sx + 16, y + h - 30)], RED)
    cx, cy = x + w // 2, y + h // 2 - 6
    pg.disc(cx, cy, 8, RED)
    for arm in range(3):
        a0 = arm * 120
        for r in range(12, 62, 4):
            a = a0 + r * 3.4
            rad = math.radians(a)
            pg.disc(cx + int(r * math.cos(rad)),
                    cy + int(r * math.sin(rad) * 0.8), 5, WHITE)
    pg.ring(cx, cy, 62, WHITE, 2)


# ------------------------------------------------------------ the layout
def draw_panel(pg, x, y, w, h, kicker, headline, caption, art):
    pg.rect(x, y, w, h, INK, 1)
    art(pg, x + 10, y + 10, 150, h - 20)
    tx = x + 172
    tw = w - 182
    draw_text(pg, tx, y + 12, kicker, 2, RED)
    hy = y + 36
    for ln in wrap(headline, 3, tw):
        draw_text(pg, tx, hy, ln, 3, INK)
        hy += 7 * 3 + 4
    hy += 6
    draw_block(pg, tx, hy, wrap(caption, 2, tw), 2, INK)


def build_page():
    pg = Page(W, H, PAPER)
    # double outer border
    pg.rect(16, 16, 992, 992, INK, 2)
    pg.rect(22, 22, 980, 980, INK, 1)

    # ---- masthead
    draw_center(pg, 512, 40, "WEDNESDAY - THE WORLD'S NEWS IN ONE PICTURE",
                2, GREY)
    draw_center(pg, 512, 64, "THE WORLD IN ONE DAY", 6, INK)
    draw_center(pg, 512, 112, "18 NOVEMBER 2026", 5, RED)
    pg.hline(28, 158, 968, INK, 4)
    pg.hline(28, 164, 968, INK, 1)

    # ---- lead story: Trump lands in Shenzhen
    draw_text(pg, 28, 184, "LEAD - SHENZHEN, CHINA", 2, RED)
    draw_text(pg, 28, 208, "TRUMP LANDS IN", 5, INK)
    draw_text(pg, 28, 248, "SHENZHEN", 5, INK)
    draw_block(pg, 28, 296, wrap(
        "FIRST TRILATERAL WITH XI AND PUTIN SET FOR THURSDAY "
        "AT THE APEC SIDELINES", 2, 600), 2, INK)
    draw_block(pg, 28, 340, wrap(
        "PUTIN ARRIVED ABOUT 02:00 LOCAL TIME. AGENDA: UKRAINE, "
        "IRAN, NUCLEAR ARMS, TRADE AND AI.", 2, 600), 2, INK)
    draw_block(pg, 28, 392, wrap(
        "ARRIVALS ON WEDNESDAY; THE TALKS THEMSELVES ARE THURSDAY.",
        2, 600), 2, RED)
    draw_lead_art(pg, 656, 180, 340, 268)
    pg.hline(28, 458, 968, INK, 3)
    pg.hline(28, 463, 968, INK, 1)

    # ---- four story panels
    draw_panel(pg, 28, 472, 472, 184, "THE GULF",
               "IRAN DRONES HIT U.S. BASE",
               "U.S. SINKS FIVE IRANIAN TANKERS; ADNOC SHIP HIT, ONE "
               "CREW MISSING; HORMUZ SHIPPING DISRUPTED.",
               draw_gulf_art)
    draw_panel(pg, 524, 472, 472, 184, "UKRAINE",
               "KERCH BRIDGE SPAN COLLAPSES",
               "RUSSIA VOWS TO REBUILD AFTER THE SECOND NIGHT STRIKE; "
               "MOSCOW HITS A KYIV BRIDGE.",
               draw_bridge_art)
    draw_panel(pg, 28, 668, 472, 184, "GAZA",
               "ISRAEL MOVES INTO CENTRAL GAZA",
               "CONCENTRATED OPERATION IN THREE AREAS OF CENTRAL GAZA.",
               draw_gaza_art)
    draw_panel(pg, 524, 668, 472, 184, "INDIA - CYCLONE",
               "CYCLONE AKVAN HEADS FOR INDIA",
               "SEVERE STORM DUE ABOUT 20 NOV; RESIDENTS MOVED TO "
               "SHELTERS ON THE ODISHA AND ANDHRA COASTS.",
               draw_cyclone_art)

    # ---- footer strip: tech outage wave, then the rest of the day
    pg.hline(28, 860, 968, INK, 3)
    draw_text(pg, 28, 874, "TECH OUTAGE WAVE: T-MOBILE, SPECTRUM, EA DOWN",
              3, INK)
    draw_block(pg, 28, 906, wrap(
        "SIXTH MAJOR OUTAGE THIS MONTH, AFTER MICROSOFT, FAA, "
        "JPMORGAN, AWS, OPENAI AND A SECRET NSA NETWORK.",
        2, 968), 2, INK)
    pg.hline(28, 946, 968, INK, 1)
    draw_block(pg, 28, 956, wrap(
        "ALSO: RUSSIAN MILITARY PLANE CRASHES IN SIBERIA, 19 DEAD - "
        "U.S. LOSES MEASLES-FREE STATUS - JEFFRIES NOMINATED FOR "
        "HOUSE SPEAKER.",
        2, 968), 2, INK)
    return pg


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    pg = build_page()
    path = os.path.join(out_dir, "entry.png")
    n = write_png(pg, path)
    print(f"wrote {path} ({n} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
