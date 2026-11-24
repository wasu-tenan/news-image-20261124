#!/usr/bin/env python3
"""news-image-20261124 entry.

Draws a 1024x1024 PNG summing up Tuesday 24 November 2026 world news
and writes it to $MAKEFUN_OUTPUT_DIR/entry.png (default /output).

Pure Python 3 standard library only (zlib for PNG compression).
Fully deterministic: same bytes on every run, no timestamps, no randomness,
no network, no fonts or files read from disk.

Layout (top to bottom):
  masthead with the date, KPI strip, 3 hero story cards, 4 second-row
  cards, a world map with 10 story pins, an ALSO list of 22 more stories,
  and a sources footer. 39 stories across 10 regions in total.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font -----
# Hand-drawn 5x7 bitmap font, one row per string, '#' = pixel on.
FONT = {
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
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10001", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "00010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "00000", "11110", "10001", "10001", "11110", "10000"),
    "q": ("00000", "00000", "01111", "10001", "10001", "01111", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("01000", "01000", "11100", "01000", "01000", "01000", "00110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
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
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    ">": ("10000", "01000", "00100", "00010", "00100", "01000", "10000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
}

# -------------------------------------------------------------- colours ----
PAPER = (245, 240, 230)
NAVY = (15, 30, 51)
NAVY2 = (27, 44, 74)
INK = (20, 33, 61)
CREAM = (245, 240, 230)
RED = (180, 35, 24)
GREEN = (22, 120, 80)
GOLD = (201, 162, 39)
TEAL = (14, 124, 123)
WHITE = (255, 255, 255)
BORDER = (178, 168, 148)
MAP_OCEAN = (199, 217, 232)
MAP_LAND = (143, 174, 139)
MAP_LAND2 = (168, 190, 150)
DARKGREEN = (18, 77, 52)
CHIPGREEN = (34, 139, 92)


# -------------------------------------------------------------- canvas -----
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def hline(self, x, y, w, c, t=1):
        for dy in range(t):
            self.fill_rect(x, y + dy, w, 1, c)

    def vline(self, x, y, h, c, t=1):
        for dx in range(t):
            self.fill_rect(x + dx, y, 1, h, c)

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
            for a in range(t):
                for b in range(t):
                    self.set(x0 + a, y0 + b, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.hline(cx - dx, cy + dy, 2 * dx + 1, c)

    def circle_outline(self, cx, cy, r, c, t=1):
        steps = max(24, r * 6)
        prev = None
        for i in range(steps + 1):
            a = 2 * math.pi * i / steps
            p = (int(cx + r * math.cos(a)), int(cy + r * math.sin(a)))
            if prev is not None:
                self.line(prev[0], prev[1], p[0], p[1], c, t)
            prev = p

    def ellipse_outline(self, cx, cy, rx, ry, c, t=1):
        steps = max(32, (rx + ry) * 3)
        prev = None
        for i in range(steps + 1):
            a = 2 * math.pi * i / steps
            p = (int(cx + rx * math.cos(a)), int(cy + ry * math.sin(a)))
            if prev is not None:
                self.line(prev[0], prev[1], p[0], p[1], c, t)
            prev = p

    def polygon(self, pts, c):
        # Scanline fill for a simple polygon.
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.hline(int(xs[i]), y, int(xs[i + 1]) - int(xs[i]) + 1, c)

    def rounded_rect(self, x, y, w, h, r, c):
        self.fill_rect(x + r, y, w - 2 * r, h, c)
        self.fill_rect(x, y + r, w, h - 2 * r, c)
        for cx, cy in ((x + r, y + r), (x + w - r - 1, y + r),
                       (x + r, y + h - r - 1), (x + w - r - 1, y + h - r - 1)):
            self.circle(cx, cy, r, c)


# -------------------------------------------------------------- text -------
def text_w(s, scale):
    return len(s) * 6 * scale


def draw_text(cv, x, y, s, scale, color):
    for ch in s:
        glyph = FONT.get(ch)
        if glyph is None:
            x += 6 * scale
            continue
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    cv.fill_rect(x + col * scale, y + row * scale,
                                 scale, scale, color)
        x += 6 * scale
    return x


def wrap(text, max_w, scale):
    """Greedy word wrap; returns list of lines fitting max_w pixels."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(cv, x, y, text, max_w, scale, color, line_h=None):
    lh = line_h or (7 * scale + 1)
    for i, ln in enumerate(wrap(text, max_w, scale)):
        draw_text(cv, x, y + i * lh, ln, scale, color)
    return y + len(wrap(text, max_w, scale)) * lh


# -------------------------------------------------------------- png --------
def png_bytes(cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", comp) + chunk(b"IEND", b""))


# -------------------------------------------------------- illustrations ---
def illu_chip(cv, x, y, w, h):
    """Nvidia chip with a rising arrow."""
    cv.fill_rect(x, y, w, h, (232, 245, 233))
    cx, cy = x + w // 2 - 30, y + h // 2
    # pins
    for i in range(5):
        yy = cy - 28 + i * 14
        cv.fill_rect(cx - 12, yy, 10, 4, DARKGREEN)
        cv.fill_rect(cx + 62, yy, 10, 4, DARKGREEN)
    # chip body
    cv.fill_rect(cx, cy - 34, 62, 68, DARKGREEN)
    cv.fill_rect(cx + 10, cy - 24, 42, 48, CHIPGREEN)
    draw_text(cv, cx + 24, cy - 13, "$", 3, WHITE)
    # rising arrow, right side
    ax = x + w - 78
    cv.line(ax, y + h - 18, ax + 22, y + h - 44, GREEN, 4)
    cv.line(ax + 22, y + h - 44, ax + 46, y + h - 62, GREEN, 4)
    cv.line(ax + 46, y + h - 62, ax + 46, y + h - 44, GREEN, 4)
    cv.line(ax + 46, y + h - 62, ax + 30, y + h - 62, GREEN, 4)


def illu_globe_slash(cv, x, y, w, h):
    """Globe with a red slash: COP31 collapses."""
    cv.fill_rect(x, y, w, h, (253, 236, 234))
    cx, cy, r = x + w // 2, y + h // 2 + 2, 32
    cv.circle(cx, cy, r, (46, 110, 166))
    cv.circle_outline(cx, cy, r, NAVY, 2)
    # land blobs
    cv.polygon([(cx - 26, cy - 18), (cx - 6, cy - 24), (cx + 2, cy - 8),
                (cx - 12, cy + 2), (cx - 26, cy - 4)], (126, 190, 110))
    cv.polygon([(cx + 8, cy + 6), (cx + 26, cy + 2), (cx + 30, cy + 18),
                (cx + 14, cy + 26), (cx + 4, cy + 16)], (126, 190, 110))
    cv.polygon([(cx - 30, cy + 12), (cx - 14, cy + 10), (cx - 10, cy + 24),
                (cx - 24, cy + 28)], (126, 190, 110))
    # meridians
    cv.ellipse_outline(cx, cy, 18, r - 1, (255, 255, 255), 1)
    cv.hline(cx - r, cy, 2 * r, (255, 255, 255), 1)
    # red slash
    cv.line(cx - r - 4, cy + r + 4, cx + r + 4, cy - r - 4, RED, 5)


def illu_capitol(cv, x, y, w, h):
    """US Capitol dome."""
    cv.fill_rect(x, y, w, h, (232, 238, 247))
    cx = x + w // 2
    base_y = y + h - 12
    # dome
    for dy in range(0, 26):
        half = int(math.sqrt(max(0, 26 * 26 - dy * dy)) * 30 / 26)
        cv.hline(cx - half, base_y - 26 - dy, 2 * half, NAVY2)
    cv.fill_rect(cx - 30, base_y - 28, 60, 6, NAVY2)
    # flag pole + flag
    cv.vline(cx, base_y - 56, 30, NAVY2, 2)
    cv.polygon([(cx + 2, base_y - 56), (cx + 20, base_y - 51),
                (cx + 2, base_y - 46)], RED)
    # columns and base
    for i in range(-2, 3):
        cv.fill_rect(cx + i * 14 - 3, base_y - 24, 6, 24, WHITE)
    cv.fill_rect(cx - 44, base_y - 26, 88, 4, WHITE)
    cv.fill_rect(cx - 48, base_y - 4, 96, 6, NAVY2)


def illu_awacs(cv, x, y, w, h):
    """AWACS plane with radar dome."""
    cv.fill_rect(x, y, w, h, (232, 238, 247))
    cx, cy = x + w // 2, y + h // 2 + 10
    # radar arcs
    cv.circle_outline(cx - 6, cy - 14, 16, TEAL, 1)
    cv.circle_outline(cx - 6, cy - 14, 22, TEAL, 1)
    # fuselage
    cv.polygon([(cx - 78, cy), (cx - 60, cy - 8), (cx + 30, cy - 8),
                (cx + 66, cy), (cx + 30, cy + 8), (cx - 60, cy + 8)],
               NAVY2)
    # wings
    cv.polygon([(cx - 18, cy - 6), (cx + 6, cy - 30), (cx + 18, cy - 30),
                (cx + 2, cy - 6)], NAVY2)
    cv.polygon([(cx - 14, cy + 6), (cx + 2, cy + 26), (cx + 12, cy + 26),
                (cx + 0, cy + 6)], NAVY2)
    # tail
    cv.polygon([(cx - 78, cy - 2), (cx - 66, cy - 22), (cx - 56, cy - 22),
                (cx - 60, cy - 2)], NAVY2)
    # radar dome
    cv.circle(cx - 6, cy - 14, 8, WHITE)
    cv.circle_outline(cx - 6, cy - 14, 8, NAVY2, 2)
    # windows
    for i in range(4):
        cv.fill_rect(cx + 34 + i * 7, cy - 4, 4, 3, WHITE)


def illu_ship(cv, x, y, w, h):
    """Cargo ship on waves under a blockade warning."""
    cv.fill_rect(x, y, w, h, (253, 236, 234))
    cx, cy = x + w // 2, y + h // 2
    # containers
    cv.fill_rect(cx - 52, cy - 26, 24, 14, RED)
    cv.fill_rect(cx - 26, cy - 26, 24, 14, GOLD)
    cv.fill_rect(cx + 2, cy - 26, 24, 14, TEAL)
    cv.fill_rect(cx + 28, cy - 26, 24, 14, NAVY2)
    # hull
    cv.polygon([(cx - 66, cy - 12), (cx + 66, cy - 12), (cx + 52, cy + 10),
                (cx - 52, cy + 10)], NAVY)
    # bridge
    cv.fill_rect(cx + 52, cy - 30, 14, 18, WHITE)
    # waves
    for k, wy in enumerate((cy + 18, cy + 28)):
        for i in range(9):
            xx = x + 12 + i * 24
            cv.line(xx, wy, xx + 12, wy - 5 if k == 0 else wy + 5, TEAL, 2)
            cv.line(xx + 12, wy - 5 if k == 0 else wy + 5, xx + 24, wy,
                    TEAL, 2)


def illu_scales(cv, x, y, w, h):
    """Scales of justice (ICJ)."""
    cv.fill_rect(x, y, w, h, (245, 240, 230))
    cx = x + w // 2
    top_y, base_y = y + 12, y + h - 10
    cv.vline(cx, top_y, base_y - top_y, NAVY2, 3)
    cv.hline(cx - 62, top_y + 4, 124, NAVY2, 3)
    cv.circle(cx, top_y + 4, 4, GOLD)
    for sgn in (-1, 1):
        px = cx + sgn * 56
        cv.line(px, top_y + 4, px - 14, top_y + 26, NAVY2, 2)
        cv.line(px, top_y + 4, px + 14, top_y + 26, NAVY2, 2)
        cv.polygon([(px - 18, top_y + 26), (px + 18, top_y + 26),
                    (px, top_y + 38)], GOLD)
    cv.fill_rect(cx - 34, base_y - 4, 68, 6, NAVY2)


def illu_mercury(cv, x, y, w, h):
    """BepiColombo at Mercury: orange planet, small craft, orbit."""
    cv.fill_rect(x, y, w, h, (27, 42, 74))
    cx, cy = x + w // 2 - 18, y + h // 2
    cv.ellipse_outline(x + w // 2, y + h // 2, 84, 22, (120, 140, 170), 1)
    cv.circle(cx, cy, 30, (214, 138, 74))
    cv.circle(cx - 10, cy - 8, 5, (180, 108, 56))
    cv.circle(cx + 8, cy + 6, 7, (180, 108, 56))
    cv.circle(cx + 12, cy - 12, 3, (180, 108, 56))
    cv.circle(cx - 2, cy + 14, 4, (180, 108, 56))
    # spacecraft, upper right on the orbit
    sx, sy = x + w - 58, y + 16
    cv.fill_rect(sx, sy, 16, 12, WHITE)
    cv.fill_rect(sx - 16, sy + 2, 14, 8, (46, 110, 166))
    cv.fill_rect(sx + 18, sy + 2, 14, 8, (46, 110, 166))
    cv.line(sx + 8, sy + 12, sx + 8, sy + 20, WHITE, 2)


# -------------------------------------------------------------- cards ------
def draw_card(cv, x, y, w, h, tag, tag_color, headline, body, illu,
              head_scale=3, illu_h=72):
    cv.fill_rect(x, y, w, h, WHITE)
    cv.rect(x, y, w, h, BORDER, 1)
    cv.fill_rect(x, y, w, 5, tag_color)
    draw_text(cv, x + 10, y + 10, tag, 2, tag_color)
    illu(cv, x + 8, y + 30, w - 16, illu_h)
    ty = y + 30 + illu_h + 4
    ty = draw_wrapped(cv, x + 12, ty, headline, w - 24, head_scale, INK,
                      7 * head_scale + 4)
    draw_wrapped(cv, x + 12, ty + 3, body, w - 24, 2, (60, 68, 84), 16)


# -------------------------------------------------------------- layout -----
ALSO_LEFT = [
    "US shutdown looms; funding ends 11 Dec",
    "Trump hits Newsom over 548 commutations",
    "Rep. Gomez quits after ethics probe",
    "Palisades fire starter convicted",
    "450 German schools get bomb threats",
    "US sanctions Iran shadow banks, $15B",
    "Iran flogs singer Parastoo Ahmadi",
    "Settler arson is 'Jewish terrorism'",
    "Japan launches Asian oil reserve plan",
    "S. Korea minister quits in exam row",
    "China official gets death for leaks",
]
ALSO_RIGHT = [
    "Taiwan tracks 12 Chinese ships, 6 jets",
    "US blacklists Megaspeed in chip probe",
    "Kenya, DR Congo restore ambassadors",
    "Sudan peace talks open Wednesday",
    "Bukele seeks third term in El Salvador",
    "Swift and Cameron honoured in Mumbai",
    "SpaceX Dragon returns science to Earth",
    "Rocket test keeps space drugs stable",
    "Wall St soars: S&P +4.7%, Nasdaq +6.5%",
    "KC Current win first NWSL title, 2-1",
    "Golden Horse: 'We Are Born Good' wins",
]

CONTINENTS = [
    # North America
    [(70, 610), (150, 600), (230, 605), (270, 620), (250, 640), (210, 655),
     (190, 680), (150, 672), (110, 660), (75, 640), (60, 625)],
    # Greenland
    [(300, 598), (330, 596), (335, 608), (310, 612)],
    # South America
    [(250, 668), (300, 662), (320, 680), (310, 715), (285, 732), (265, 710),
     (248, 690)],
    # Europe
    [(480, 606), (540, 600), (560, 612), (545, 628), (510, 632), (485, 622)],
    # Africa
    [(480, 640), (545, 638), (565, 655), (560, 690), (540, 725), (515, 720),
     (495, 690), (478, 665)],
    # Asia
    [(565, 605), (700, 598), (850, 600), (950, 615), (960, 635), (900, 650),
     (830, 665), (760, 672), (680, 668), (620, 650), (585, 630), (565, 618)],
    # SE Asia islands
    [(800, 690), (830, 688), (835, 700), (805, 702)],
    [(860, 695), (880, 693), (885, 703), (862, 705)],
    # Australia
    [(830, 705), (900, 702), (915, 715), (890, 728), (845, 726), (828, 716)],
    # UK
    [(470, 600), (478, 598), (480, 608), (472, 610)],
    # Japan
    [(930, 612), (940, 610), (942, 622), (932, 624)],
]

# (number, pin x, pin y, label, label x, label y, leader start x, leader start y)
PINS = [
    (1, 540, 612, "KYIV STRIKES", 370, 600, 518, 609),
    (2, 520, 652, "WARSHIP SUNK", 350, 640, 498, 649),
    (3, 566, 648, "GAZA STRIKES", 600, 612, 600, 621),
    (4, 600, 640, "BAHRAIN HIT", 580, 676, 606, 676),
    (5, 815, 692, "FACTORY FIRE", 660, 648, 800, 657),
    (6, 880, 632, "TAIWAN TRACKS", 800, 600, 878, 618),
    (7, 500, 690, "NIGERIA +$7.5B", 514, 700, 514, 709),
    (8, 170, 655, "CARTEL ARREST", 184, 648, 184, 657),
    (9, 300, 700, "BOLSONARO ICU", 312, 710, 312, 719),
    (10, 870, 715, "COP BACKLASH", 690, 712, 830, 712),
]


def draw_masthead(cv):
    cv.fill_rect(0, 0, W, 104, NAVY)
    draw_text(cv, 28, 16, "THE WORLD IN ONE DAY", 2, GOLD)
    draw_text(cv, 28, 40, "TUESDAY 24 NOVEMBER 2026", 5, CREAM)
    draw_text(cv, 28, 84, "THE DAY'S NEWS, SUMMED UP IN ONE PICTURE",
              2, (200, 210, 225))
    # globe emblem, top right
    cx, cy, r = 920, 52, 36
    cv.circle(cx, cy, r, (46, 110, 166))
    cv.circle_outline(cx, cy, r, CREAM, 2)
    cv.polygon([(cx - 26, cy - 18), (cx - 6, cy - 24), (cx + 2, cy - 8),
                (cx - 12, cy + 2), (cx - 26, cy - 4)], (126, 190, 110))
    cv.polygon([(cx + 8, cy + 6), (cx + 26, cy + 2), (cx + 30, cy + 18),
                (cx + 14, cy + 26), (cx + 4, cy + 16)], (126, 190, 110))
    cv.ellipse_outline(cx, cy, 17, r - 1, CREAM, 1)
    cv.hline(cx - r, cy, 2 * r, CREAM, 1)
    cv.hline(0, 101, W, GOLD, 3)


def draw_kpi_strip(cv):
    cv.fill_rect(0, 104, W, 56, PAPER)
    kpis = [
        ("NVIDIA +31.5%", "HUANG BACK AS CEO", GREEN),
        ("COP31 NO DEAL", "NO DEAL IN ANTALYA", RED),
        ("258 SEATS", "BIGGEST SINCE 1992", NAVY),
        ("ICJ 9-6", "MYANMAR GENOCIDE", TEAL),
    ]
    for i, (value, label, color) in enumerate(kpis):
        x = 16 + i * 256
        draw_text(cv, x, 116, value, 3, color)
        draw_text(cv, x, 142, label, 2, INK)
        if i:
            cv.vline(i * 256, 112, 40, BORDER, 1)
    cv.hline(0, 159, W, BORDER, 1)


def draw_map(cv):
    draw_text(cv, 16, 578, "WHERE IT HAPPENED", 2, INK)
    draw_text(cv, 672, 578, "10 STORIES PINNED ON THE MAP", 2, (90, 96, 110))
    cv.fill_rect(16, 592, 992, 146, MAP_OCEAN)
    cv.rect(16, 592, 992, 146, BORDER, 1)
    # graticule
    for gy in (620, 660, 700):
        cv.hline(17, gy, 990, (225, 235, 242), 1)
    for gx in (250, 500, 750):
        cv.vline(gx, 593, 144, (225, 235, 242), 1)
    for poly in CONTINENTS:
        cv.polygon(poly, MAP_LAND)
    cv.polygon(CONTINENTS[6], MAP_LAND2)  # SE Asia islands, lighter
    cv.polygon(CONTINENTS[7], MAP_LAND2)
    cv.polygon(CONTINENTS[8], MAP_LAND2)  # Australia, lighter
    # leader lines first, then labels, then pins on top
    for num, px, py, label, lx, ly, sx, sy in PINS:
        cv.line(sx, sy, px, py, INK, 1)
    for num, px, py, label, lx, ly, sx, sy in PINS:
        lw = text_w(label, 2)
        cv.fill_rect(lx - 3, ly - 2, lw + 6, 18, PAPER)
        cv.rect(lx - 3, ly - 2, lw + 6, 18, BORDER, 1)
        draw_text(cv, lx, ly, label, 2, INK)
    for num, px, py, label, lx, ly, sx, sy in PINS:
        cv.circle(px, py, 11, RED)
        cv.circle_outline(px, py, 11, WHITE, 2)
        num_s = str(num)
        draw_text(cv, px - 5 if len(num_s) == 1 else px - 10, py - 7,
                  num_s, 2, WHITE)


def draw_also(cv):
    draw_text(cv, 16, 750, "ALSO ON TUESDAY 24 NOVEMBER", 2, INK)
    cv.hline(16, 766, 992, RED, 2)
    for col, items in ((16, ALSO_LEFT), (520, ALSO_RIGHT)):
        y = 774
        for item in items:
            cv.fill_rect(col, y + 3, 8, 8, RED)
            draw_text(cv, col + 14, y, item, 2, INK)
            y += 15


def draw_footer(cv):
    cv.fill_rect(0, 960, W, 64, NAVY)
    draw_text(cv, 16, 972,
              "SOURCES: REUTERS - AP - NASA - ESA - ICJ - AMNESTY "
              "INTERNATIONAL - MOTLEY FOOL", 2, CREAM)
    draw_text(cv, 16, 992,
              "ALL STORIES REPORTED 23-24 NOVEMBER 2026 - MAKE.FUN "
              "BOUNTY NEWS-IMAGE-20261124", 2, (200, 210, 225))


def build_image():
    cv = Canvas(W, H, PAPER)
    draw_masthead(cv)
    draw_kpi_strip(cv)
    # hero row: 3 big cards
    draw_card(cv, 16, 160, 324, 232, "NORTH AMERICA - BUSINESS", GREEN,
              "HUANG IS BACK AT NVIDIA",
              "Huang reinstated as CEO 11 days after quitting; shares "
              "surge 31.5%, adding nearly $1T.",
              illu_chip, head_scale=3, illu_h=70)
    draw_card(cv, 350, 160, 324, 232, "EUROPE - CLIMATE", RED,
              "COP31 COLLAPSES WITHOUT A DEAL",
              "UN climate talks in Antalya collapse as the EU rejects a "
              "draft with no fossil-fuel mention.",
              illu_globe_slash, head_scale=3, illu_h=70)
    draw_card(cv, 684, 160, 324, 232, "NORTH AMERICA - POLITICS", NAVY2,
              "DEMOCRATS WIN 258 HOUSE SEATS",
              "Hubbard beats Foxx after a recount - the biggest "
              "Democratic House majority since 1992.",
              illu_capitol, head_scale=3, illu_h=70)
    # second row: 4 cards
    draw_card(cv, 16, 392, 240, 184, "EUROPE - SECURITY", NAVY2,
              "NATO SENDS AWACS TO POLAND",
              "AWACS jets deploy after missiles hit Poland.",
              illu_awacs, head_scale=2, illu_h=56)
    draw_card(cv, 266, 392, 240, 184, "MIDDLE EAST", RED,
              "IRAN VOWS TO FIGHT US BLOCKADE",
              "Tehran vows 'all tools' against the US blockade.",
              illu_ship, head_scale=2, illu_h=56)
    draw_card(cv, 516, 392, 240, 184, "ASIA-PACIFIC - LAW", TEAL,
              "ICJ: MYANMAR GENOCIDE",
              "Court rules 9-6: Myanmar committed genocide in 2017.",
              illu_scales, head_scale=2, illu_h=56)
    draw_card(cv, 766, 392, 240, 184, "SCIENCE - SPACE", (150, 110, 10),
              "BEPICOLOMBO REACHES MERCURY",
              "ESA/JAXA craft ends an eight-year trip at Mercury.",
              illu_mercury, head_scale=2, illu_h=56)
    draw_map(cv)
    draw_also(cv)
    draw_footer(cv)
    return png_bytes(cv)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = build_image()
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
