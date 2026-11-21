#!/usr/bin/env python3
"""AURELLE - the island that floats above the clouds.

A travel poster for a place that does not exist. Pure stdlib (zlib,
struct, math, os). Deterministic: no randomness, no clock. Writes
/output/entry.png, 1024x1024, as a hand-encoded PNG.
"""
import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- canvas
buf = bytearray(W * H * 3)


def lerp(a, b, t):
    return a + (b - a) * t


def lerp3(c1, c2, t):
    return (int(lerp(c1[0], c2[0], t)),
            int(lerp(c1[1], c2[1], t)),
            int(lerp(c1[2], c2[2], t)))


def fill_span(y, x0, x1, rgb):
    """Opaque horizontal run on row y (clamped)."""
    if y < 0 or y >= H:
        return
    if x0 < 0:
        x0 = 0
    if x1 > W:
        x1 = W
    if x1 <= x0:
        return
    n = x1 - x0
    row = y * W * 3 + x0 * 3
    buf[row:row + n * 3] = bytes(rgb) * n


def blend_span(y, x0, x1, rgb, alpha):
    """Alpha-blend a horizontal run (alpha 0..255)."""
    if y < 0 or y >= H or alpha <= 0:
        return
    if alpha >= 255:
        fill_span(y, x0, x1, rgb)
        return
    if x0 < 0:
        x0 = 0
    if x1 > W:
        x1 = W
    if x1 <= x0:
        return
    r, g, b = rgb
    inv = 255 - alpha
    base = y * W * 3
    for x in range(x0, x1):
        i = base + x * 3
        buf[i] = (r * alpha + buf[i] * inv) >> 8
        buf[i + 1] = (g * alpha + buf[i + 1] * inv) >> 8
        buf[i + 2] = (b * alpha + buf[i + 2] * inv) >> 8


def fill_circle(cx, cy, r, rgb, alpha=255):
    r2 = r * r
    for y in range(cy - r, cy + r + 1):
        dy = y - cy
        rem = r2 - dy * dy
        if rem < 0:
            continue
        dx = int(math.sqrt(rem))
        if alpha >= 255:
            fill_span(y, cx - dx, cx + dx + 1, rgb)
        else:
            blend_span(y, cx - dx, cx + dx + 1, rgb, alpha)


def fill_ellipse(cx, cy, rx, ry, rgb, alpha=255):
    for y in range(cy - ry, cy + ry + 1):
        dy = (y - cy) / ry
        rem = 1.0 - dy * dy
        if rem < 0:
            continue
        dx = int(rx * math.sqrt(rem))
        if alpha >= 255:
            fill_span(y, cx - dx, cx + dx + 1, rgb)
        else:
            blend_span(y, cx - dx, cx + dx + 1, rgb, alpha)


def fill_rect(x0, y0, x1, y1, rgb, alpha=255):
    for y in range(y0, y1):
        if alpha >= 255:
            fill_span(y, x0, x1, rgb)
        else:
            blend_span(y, x0, x1, rgb, alpha)


# Deterministic pseudo-random (fixed-seed LCG).
_seed = [123456789]


def rnd():
    _seed[0] = (_seed[0] * 1103515245 + 12345) & 0x7FFFFFFF
    return _seed[0] / 0x7FFFFFFF


# ---------------------------------------------------------------- sky
SKY_STOPS = [
    (0.00, (46, 26, 88)),     # deep violet
    (0.30, (104, 52, 132)),   # violet
    (0.48, (178, 84, 118)),   # rose
    (0.60, (226, 128, 84)),   # amber-orange
    (0.70, (248, 184, 96)),   # amber gold
    (0.78, (252, 216, 142)),  # gold horizon
]
for y in range(0, 720):
    t = y / 1024.0
    for i in range(len(SKY_STOPS) - 1):
        t0, c0 = SKY_STOPS[i]
        t1, c1 = SKY_STOPS[i + 1]
        if t0 <= t <= t1:
            f = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
            fill_span(y, 0, W, lerp3(c0, c1, f))
            break
    else:
        fill_span(y, 0, W, SKY_STOPS[-1][1])

# ---------------------------------------------------------------- sun
SUN_X, SUN_Y, SUN_R = 716, 396, 74
for _i in range(30):  # smooth glow ramp, largest faintest first
    _r = 262 - _i * 6
    _a = 4 + _i * 4
    fill_circle(SUN_X, SUN_Y, _r, (255, 208, 128), _a)
fill_circle(SUN_X, SUN_Y, SUN_R, (255, 232, 165))
fill_circle(SUN_X, SUN_Y, SUN_R - 12, (255, 240, 190))

# faint high clouds (thin warm streaks)
for i in range(14):
    cx = int(rnd() * 1024)
    cy = int(120 + rnd() * 260)
    rx = int(60 + rnd() * 130)
    ry = int(5 + rnd() * 9)
    tone = 250 if i % 3 else 244
    fill_ellipse(cx, cy, rx, ry, (tone, 214, 178), 60)

# ---------------------------------------------------------------- cloud sea
for y in range(700, H):
    f = (y - 700) / 324.0
    fill_span(y, 0, W, lerp3((252, 238, 214), (228, 200, 178), f))

# puffy cloud tops along the sea's upper edge
for i in range(46):
    cx = int(rnd() * 1024)
    cy = int(648 + rnd() * 120)
    rx = int(46 + rnd() * 110)
    ry = int(16 + rnd() * 30)
    k = rnd()
    col = lerp3((255, 250, 240), (240, 214, 182), k)
    fill_ellipse(cx, cy, rx, ry, col)
# a second, lower layer of puffs for depth
for i in range(30):
    cx = int(rnd() * 1024)
    cy = int(800 + rnd() * 180)
    rx = int(60 + rnd() * 130)
    ry = int(18 + rnd() * 34)
    k = rnd()
    col = lerp3((250, 238, 222), (226, 196, 168), k)
    fill_ellipse(cx, cy, rx, ry, col)

# soft shadow of the island on the cloud sea
fill_ellipse(512, 872, 250, 34, (178, 140, 128), 70)

# ---------------------------------------------------------------- island
# Green-topped floating rock, centred slightly below middle.
# Rock body: rows 520..800, tapering to a point.
for y in range(520, 802):
    f = (y - 520) / 282.0
    half = 184 * (1.0 - f ** 1.55) + 6
    if half < 2:
        half = 2
    cx = 512
    x0 = int(cx - half)
    x1 = int(cx + half)
    col = lerp3((128, 88, 66), (58, 40, 50), f)
    fill_span(y, x0, x1, col)
    # sunlit right edge
    fill_span(y, int(cx + half * 0.55), x1, lerp3((158, 108, 78), (84, 56, 62), f))
    # dark left edge
    fill_span(y, x0, int(cx - half * 0.55), lerp3((104, 70, 54), (44, 30, 40), f))

# green plateau cap (domed top)
for y in range(496, 546):
    f = (y - 496) / 50.0
    half = 186 * math.sqrt(max(0.0, 1.0 - ((y - 522) / 30.0) ** 2 * 0.55)) \
        if y < 522 else 186 * (1.0 - (y - 522) / 24.0 * 0.12)
    if half < 10:
        half = 10
    col = lerp3((96, 158, 92), (52, 112, 70), min(1.0, f))
    fill_span(y, int(512 - half), int(512 + half), col)
# darker green tree blobs on the plateau
for i in range(12):
    cx = int(360 + rnd() * 300)
    cy = int(500 + rnd() * 26)
    rx = int(12 + rnd() * 22)
    ry = int(6 + rnd() * 10)
    fill_ellipse(cx, cy, rx, ry, (38, 92, 58))

# ---------------------------------------------------------------- town
# Small white houses with terracotta roofs along the plateau.
HOUSES = [(352, 492, 26, 16), (392, 496, 22, 13), (428, 490, 30, 18),
          (470, 496, 22, 13), (560, 494, 24, 14), (596, 490, 28, 17),
          (638, 496, 22, 13), (668, 492, 24, 15)]
for (hx, hy, hw, hh) in HOUSES:
    fill_rect(hx, hy, hx + hw, hy + hh, (248, 242, 228))
    # terracotta pitched roof (triangle via spans)
    for ry in range(hh // 2 + 4):
        wdt = (hw // 2 + 3) - ry
        fill_span(hy - ry, hx + hw // 2 - wdt, hx + hw // 2 + wdt + 1,
                  (196, 96, 56))

# ---------------------------------------------------------------- tower
# One tall slender lighthouse-observatory: the single landmark.
fill_rect(500, 330, 526, 512, (246, 238, 220))
fill_rect(500, 330, 508, 512, (214, 200, 176))   # shaded side
fill_rect(518, 330, 526, 512, (255, 248, 232))   # sunlit side
# balcony ring
fill_rect(494, 352, 532, 360, (176, 128, 72))
# gallery windows
for wy in (392, 424, 456):
    fill_rect(508, wy, 518, wy + 12, (52, 64, 92))
# golden dome + spire
fill_circle(513, 330, 20, (216, 164, 72))
fill_rect(511, 296, 515, 312, (216, 164, 72))
fill_circle(513, 296, 4, (250, 220, 130))
# warm glow from the lamp room
fill_circle(513, 330, 34, (255, 214, 130), 70)
fill_circle(513, 330, 22, (255, 232, 170), 110)

# ---------------------------------------------------------------- waterfalls
# Three falls pouring off the island's edge into the cloud sea.
for (fx, fw, top, bot) in [(392, 12, 690, 862), (512, 16, 760, 884),
                           (618, 11, 700, 856)]:
    for y in range(top, bot):
        wob = int(4 * math.sin(y / 38.0))
        fade = 1.0 - max(0.0, (y - (bot - 40)) / 40.0) * 0.55
        col = lerp3((228, 242, 250), (250, 250, 244), 0.5)
        fill_span(y, fx + wob, fx + wob + fw, col)
        fill_span(y, fx + wob + fw // 3, fx + wob + fw // 3 + 2,
                  (255, 255, 255))

# small cloud puffs where the falls meet the sea
for (fx, fy) in [(398, 858), (520, 880), (624, 852)]:
    fill_ellipse(fx, fy, 34, 12, (255, 250, 240))
    fill_ellipse(fx + 18, fy + 6, 24, 10, (246, 232, 214))

# ---------------------------------------------------------------- birds
def bird(bx, by, s):
    for k in range(s):
        fill_span(by + k, bx - s + k, bx - k, (58, 40, 66))
        fill_span(by + k, bx + k, bx + s - k, (58, 40, 66))


bird(300, 250, 9)
bird(340, 282, 7)
bird(262, 300, 6)
bird(760, 220, 8)
bird(806, 258, 6)

# ---------------------------------------------------------------- name
# 5x7 bitmap font, scaled 13x -> letters ~65x91 px. Cream with shadow.
GLYPHS = {
    'A': ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    'U': ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    'R': ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    'E': ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    'L': ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
}
NAME = "AURELLE"
S = 13
GW, GH = 5 * S, 7 * S
SP = S
total_w = len(NAME) * GW + (len(NAME) - 1) * SP
TX = (W - total_w) // 2
TY = 66
SHADOW = (74, 40, 96)
CREAM = (255, 244, 214)


def draw_text(ox, oy, rgb, alpha=255):
    for li, ch in enumerate(NAME):
        gx = ox + li * (GW + SP)
        glyph = GLYPHS[ch]
        for r in range(7):
            for c in range(5):
                if glyph[r][c] == '1':
                    x0 = gx + c * S
                    y0 = oy + r * S
                    if alpha >= 255:
                        fill_rect(x0, y0, x0 + S, y0 + S, rgb)
                    else:
                        for yy in range(y0, y0 + S):
                            blend_span(yy, x0, x0 + S, rgb, alpha)


draw_text(TX + 5, TY + 6, SHADOW, 150)
draw_text(TX, TY, CREAM)

# ---------------------------------------------------------------- PNG out
def write_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += buf[y * W * 3:(y + 1) * W * 3]
    comp = zlib.compress(bytes(raw), 6)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        c += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        return c

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


if __name__ == "__main__":
    out = os.environ.get("AURELLE_OUT", "/output/entry.png")
    n = write_png(out)
    print("wrote %s (%d bytes, %dx%d)" % (out, n, W, H))
