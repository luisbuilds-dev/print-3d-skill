"""Animated 16:9 banner for the README (LuisBuilds palette). Usage: uv run --with pillow,numpy assets/banner.py assets/banner.gif  (Windows fonts: Bahnschrift, Consolas)
import math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, SS = 1280, 720, 2            # output size, supersampling
BG, LIME, TEAL, TXT = (8, 8, 8), (200, 240, 80), (80, 240, 200), (245, 242, 235)
DIM = (34, 40, 22)
FONT = "C:/Windows/Fonts/bahnschrift.ttf"
MONO = "C:/Windows/Fonts/consola.ttf"
N, PRINT_FRAMES, L = 84, 66, 40     # frames, frames spent printing, layers

def font(path, size, bold=False):
    f = ImageFont.truetype(path, size * SS)
    if bold:
        try:
            f.set_variation_by_name("Bold")
        except Exception:
            pass
    return f

F_TITLE, F_SUB, F_TAG, F_SIG = font(FONT, 112, True), font(MONO, 28), font(MONO, 21), font(FONT, 30, True)

def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

# twisted hexagonal vase, z in [0,1]
def layer_pts(z, yaw, n=6, seg=10):
    r = 1.0 + 0.18 * math.sin(z * math.pi * 1.6) - 0.12 * z
    tw = z * math.pi * 0.55
    pts = []
    for k in range(n * seg + 1):
        a = 2 * math.pi * k / (n * seg)
        # hexagon with rounded corners
        corner = math.cos(math.pi / n) / math.cos(((a + tw) % (2 * math.pi / n)) - math.pi / n)
        rr = r * (0.86 * corner + 0.14)
        pts.append((rr * math.cos(a), rr * math.sin(a), z * 2.2))
    return project(np.array(pts), yaw)

def project(p, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    x = p[:, 0] * c - p[:, 1] * s
    y = p[:, 0] * s + p[:, 1] * c
    tilt = 0.42
    sx = 940 + x * 150
    sy = 520 - p[:, 2] * 150 + y * 150 * tilt
    return np.stack([sx, sy], 1) * SS

def background(d, f):
    step = 40 * SS
    off = 0
    for x in range(-step, W * SS + step, step):
        d.line([(x + off, 0), (x + off, H * SS)], fill=(16, 18, 12), width=SS)
    for y in range(0, H * SS + step, step):
        d.line([(0, y + off), (W * SS, y + off)], fill=(16, 18, 12), width=SS)

def frame(f):
    im = Image.new("RGB", (W * SS, H * SS), BG)
    d = ImageDraw.Draw(im)
    background(d, f)
    # scanlines
    for y in range(0, H * SS, 6 * SS):
        d.line([(0, y), (W * SS, y)], fill=(5, 5, 5), width=1)
    yaw = f / N * 2 * math.pi / 3              # 120° per loop: hexagon symmetry -> seamless
    prog = min(f / PRINT_FRAMES, 1.0) * L
    done = int(prog)
    # bed
    bed = project(np.array([[-1.7, -1.7, 0], [1.7, -1.7, 0], [1.7, 1.7, 0], [-1.7, 1.7, 0], [-1.7, -1.7, 0]]), yaw)
    d.line([tuple(p) for p in bed], fill=(40, 46, 30), width=2 * SS)
    # ghost of the full part
    for i in range(0, L, 4):
        d.line([tuple(p) for p in layer_pts(i / (L - 1), yaw)], fill=DIM, width=SS)
    # printed layers
    for i in range(done):
        t = i / (L - 1)
        d.line([tuple(p) for p in layer_pts(t, yaw)], fill=mix(TEAL, LIME, t), width=3 * SS)
    nozzle = None
    if done < L:
        t = done / (L - 1)
        pts = layer_pts(t, yaw)
        k = max(2, int((prog - done) * len(pts)))
        d.line([tuple(p) for p in pts[:k]], fill=TXT, width=3 * SS)
        nozzle = pts[k - 1]
    if nozzle is not None:
        nx, ny = nozzle
        d.line([(nx - 230 * SS, ny - 70 * SS), (nx + 230 * SS, ny - 70 * SS)], fill=(60, 66, 50), width=3 * SS)  # gantry
        d.polygon([(nx - 16 * SS, ny - 62 * SS), (nx + 16 * SS, ny - 62 * SS), (nx + 5 * SS, ny - 10 * SS),
                   (nx, ny - 2 * SS), (nx - 5 * SS, ny - 10 * SS)], fill=LIME)
        d.ellipse([nx - 6 * SS, ny - 6 * SS, nx + 6 * SS, ny + 6 * SS], fill=(255, 255, 230))
    else:
        # validated badge pulses while holding
        a = 0.5 + 0.5 * math.sin((f - PRINT_FRAMES) / (N - PRINT_FRAMES) * math.pi * 2)
        col = mix(BG, LIME, 0.55 + 0.45 * a)
        msg = "OK  watertight · fits bed"
        bw = d.textlength(msg, font=F_TAG) + 36 * SS
        bx, by = 1230 * SS - bw, 70 * SS
        d.rounded_rectangle([bx, by, bx + bw, by + 44 * SS], 10 * SS, outline=col, width=2 * SS)
        d.text((bx + 18 * SS, by + 9 * SS), msg, font=F_TAG, fill=col)
    # text block
    x0 = 88 * SS
    d.text((x0, 168 * SS), "print-", font=F_TITLE, fill=TXT)
    tw = d.textlength("print-", font=F_TITLE)
    d.text((x0 + tw, 168 * SS), "3d", font=F_TITLE, fill=LIME)
    d.rectangle([x0, 312 * SS, x0 + 120 * SS, 318 * SS], fill=TEAL)
    sub = "A Claude skill: idea → validated STL"
    typed = sub[: max(0, min(len(sub), int((f - 4) * 1.2)))] if f < 40 else sub
    d.text((x0, 345 * SS), typed, font=F_SUB, fill=TXT)
    if (f // 6) % 2 == 0:
        cx = x0 + d.textlength(typed, font=F_SUB) + 4 * SS
        d.rectangle([cx, 349 * SS, cx + 14 * SS, 377 * SS], fill=LIME)
    tags = ["36 printers", "build123d", "STL · 3MF · STEP", "EN / ES"]
    tx = x0
    for j, tg in enumerate(tags):
        if f >= 10 + j * 5:
            w = d.textlength(tg, font=F_TAG) + 28 * SS
            d.rounded_rectangle([tx, 410 * SS, tx + w, 448 * SS], 19 * SS, outline=TEAL if j % 2 else LIME, width=2 * SS)
            d.text((tx + 14 * SS, 418 * SS), tg, font=F_TAG, fill=TXT)
            tx += w + 12 * SS
    d.text((x0, 600 * SS), "by ", font=F_SIG, fill=(150, 150, 140))
    d.text((x0 + d.textlength("by ", font=F_SIG), 600 * SS), "LuisBuilds_", font=F_SIG, fill=LIME)
    return im.resize((W, H), Image.LANCZOS)

frames = [frame(f) for f in range(N)]
pal = frames[PRINT_FRAMES // 2].quantize(colors=64, method=Image.Quantize.MEDIANCUT)
q = [fr.quantize(palette=pal, dither=Image.Dither.NONE) for fr in frames]
durs = [70] * N
durs[-1] = 600
q[0].save(sys.argv[1], save_all=True, append_images=q[1:], duration=durs, loop=0, optimize=True, disposal=1)

print("ok", sys.argv[1])
