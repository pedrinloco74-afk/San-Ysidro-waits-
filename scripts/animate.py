"""Step 4 - render the 'truck hovering away' shot.

Vehicle motion is driven by three numbers per keyframe:
    bottom  - where the wheels sit in the output frame
    s       - scale (the vehicle recedes into the distance)
    dx      - horizontal drift
`dy` is derived so the wheels land exactly on `bottom`.
"""
import json
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "assets")
F = os.path.join(ROOT, "frames")
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

FPS = 30
DUR = 7.5
OUT_W, OUT_H = 1440, 960
S = OUT_W / 1712.0

rng = np.random.default_rng(7)
PREVIEW = "--preview" in sys.argv
PLATE = os.path.join(A, "background_plate.png")


# ------------------------------------------------------------------ helpers
def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def lerp_keys(keys, t):
    if t <= keys[0][0]:
        return dict(keys[0][1])
    for i in range(len(keys) - 1):
        t0, v0 = keys[i]
        t1, v1 = keys[i + 1]
        if t0 <= t <= t1:
            u = smoothstep((t - t0) / (t1 - t0))
            return {k: v0[k] + (v1[k] - v0[k]) * u for k in v0}
    return dict(keys[-1][1])


def warp(img, M, size=(OUT_W, OUT_H)):
    return cv2.warpAffine(img, M, size, flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))


def make_M(pos, scale, angle_deg, pivot):
    th = math.radians(angle_deg)
    c, s = math.cos(th), math.sin(th)
    a, b = scale * c, -scale * s
    cc, d = scale * s, scale * c
    return np.array([[a, b, pos[0] - (a * pivot[0] + b * pivot[1])],
                     [cc, d, pos[1] - (cc * pivot[0] + d * pivot[1])]], np.float32)


def translate(dx, dy):
    return np.array([[1, 0, dx], [0, 1, dy], [0, 0, 1]], np.float32)


def translate2(dx, dy):
    return np.array([[1, 0, dx], [0, 1, dy]], np.float32)


def alpha_over(dst, src):
    sa = src[:, :, 3:4].astype(np.float32) / 255.0
    da = dst[:, :, 3:4].astype(np.float32) / 255.0
    oa = sa + da * (1 - sa)
    rgb = (src[:, :, :3].astype(np.float32) * sa
           + dst[:, :, :3].astype(np.float32) * da * (1 - sa))
    return np.dstack([rgb, oa * 255]).astype(np.uint8)


def additive(dst, src, gain):
    a = src[:, :, 3:4].astype(np.float32) / 255.0
    rgb = src[:, :, :3].astype(np.float32) * a * gain
    out = dst.copy()
    out[:, :, :3] = np.clip(out[:, :, :3].astype(np.float32) + rgb, 0, 255).astype(np.uint8)
    return out


def ramp(n, a, b):
    """1 before a, 0 after b (linear)."""
    r = np.ones(n, np.float32)
    if b > a:
        seg = np.linspace(1, 0, int(b - a) + 2, dtype=np.float32)[:-1]
        r[a:a + len(seg)] = seg
        r[b:] = 0
    return r


# ------------------------------------------------------------------- assets
plate = cv2.resize(np.array(Image.open(PLATE).convert("RGB")),
                    (OUT_W, OUT_H), interpolation=cv2.INTER_LANCZOS4)
plate = np.dstack([plate, np.full((OUT_H, OUT_W, 1), 255, np.uint8)])

truck_full = np.array(Image.open(os.path.join(A, "truck_rgba.png")))
fire_full = np.array(Image.open(os.path.join(A, "fire_rgba.png")))

bx0, by0, bx1, by1 = 62, 294, 1681, 738
ORIG = (bx0 * S, by0 * S)
truck = cv2.resize(truck_full[by0:by1, bx0:bx1],
                    (int((bx1 - bx0) * S), int((by1 - by0) * S)),
                    interpolation=cv2.INTER_LANCZOS4)
PIVOT = ((870 - bx0) * S, (470 - by0) * S)
PIVOT_OUT = (ORIG[0] + PIVOT[0], ORIG[1] + PIVOT[1])
WHEEL_LOCAL_Y = (738 - by0) * S

GROUND_Y = 705
NOZZLES = ((250, 690), (1285, 686))
IW, IH = fire_full.shape[1], fire_full.shape[0]


def crop(img, x0, y0, x1, y1):
    x0 = max(0, x0); y0 = max(0, y0)
    x1 = min(img.shape[1], x1); y1 = min(img.shape[0], y1)
    return img[y0:y1, x0:x1].copy(), x0, y0


cones, balls = [], []
for nx, ny in NOZZLES:
    # ---- cone : bright part attached to the nozzle
    cone, cx0, cy0 = crop(fire_full, nx - 270, ny - 135, nx + 270, GROUND_Y + 30)
    n = cone.shape[0]
    a = cone[:, :, 3].astype(np.float32) / 255.0
    tail = np.clip((GROUND_Y + 30 - np.arange(n)) / 45.0, 0, 1)
    a *= tail[:, None]
    a *= np.clip((np.arange(cone.shape[1]) - 6) / 30.0, 0, 1)[None, :]
    a *= np.clip((cone.shape[1] - 6 - np.arange(cone.shape[1])) / 30.0, 0, 1)[None, :]
    cone[:, :, 3] = (a * 255).astype(np.uint8)
    cone = cv2.resize(cone, (int(cone.shape[1] * S), int(cone.shape[0] * S)),
                      interpolation=cv2.INTER_LANCZOS4)
    noz = ((nx - cx0) * S, (ny - cy0) * S)
    cones.append((cone, noz, cx0, cy0))

    # ---- ball : the fire pooling on the ground
    ball, bx0s, by0s = crop(fire_full, nx - 340, GROUND_Y - 30, nx + 340, 990)
    n = ball.shape[0]
    a = ball[:, :, 3].astype(np.float32) / 255.0
    head = np.clip((np.arange(n) - 10) / 40.0, 0, 1)
    tail = np.clip((n - 10 - np.arange(n)) / 90.0, 0, 1)
    a *= (head * tail)[:, None]
    a *= np.clip((np.arange(ball.shape[1]) - 10) / 60.0, 0, 1)[None, :]
    a *= np.clip((ball.shape[1] - 10 - np.arange(ball.shape[1])) / 60.0, 0, 1)[None, :]
    ball[:, :, 3] = (a * 255).astype(np.uint8)
    ball = cv2.resize(ball, (int(ball.shape[1] * S), int(ball.shape[0] * S)),
                      interpolation=cv2.INTER_LANCZOS4)
    balls.append((ball, (bx0s, by0s)))


def puff_sprite(size=300, seed=0):
    r = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size]
    c = (size - 1) / 2
    d = np.sqrt(((x - c) / (size * 0.40)) ** 2 + ((y - c) / (size * 0.40)) ** 2)
    n = r.random((size // 6 + 2, size // 6 + 2))
    n = cv2.resize(n, (size, size), interpolation=cv2.INTER_CUBIC)
    n = cv2.GaussianBlur(n, (0, 0), size / 30)
    n = (n - n.min()) / (n.max() - n.min() + 1e-6)
    a = np.clip(1.0 - d, 0, 1) ** 1.5 * (0.18 + 1.25 * n)
    rgba = np.zeros((size, size, 4), np.uint8)
    rgba[:, :, 0] = 232
    rgba[:, :, 1] = 214
    rgba[:, :, 2] = 192
    rgba[:, :, 3] = (np.clip(a * 1.7, 0, 1) * 255).astype(np.uint8)
    return rgba


PUFFS = [puff_sprite(300, 11 + i) for i in range(8)]


def shadow_sprite(x0=110, x1=1640, h=280):
    """built in source pixels: a wide soft pool plus contact patches."""
    w = x1 - x0
    y, x = np.mgrid[0:h, 0:w]
    cx, cy = (870 - x0), (h * 0.55)
    d = ((x - cx) / (w / 2)) ** 2 + ((y - cy) / (h / 2)) ** 2
    a = np.clip(1.0 - d, 0, 1) ** 2.2 * 0.20
    for wx in (250, 1285):
        dx = (x - (wx - x0)) / 130.0
        dy = (y - (h * 0.58)) / 34.0
        a = np.maximum(a, np.clip(1.0 - (dx * dx + dy * dy), 0, 1) ** 1.5 * 0.72)
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[:, :, 3] = (a * 255).astype(np.uint8)
    rgba = cv2.resize(rgba, (int(w * S), int(h * S)), interpolation=cv2.INTER_LANCZOS4)
    return rgba, (x0 * S, h * S)


SHADOW, SHADOW_ORG = shadow_sprite()

KEYS = [
    (0.00, dict(bottom=620.8, s=1.000, dx=0,   ang=0.0,  cam=1.000, camdy=0,  dust=0.00, shadow=1.00, trail=0.0)),
    (0.45, dict(bottom=606.0, s=0.998, dx=0,   ang=0.0,  cam=1.000, camdy=0,  dust=0.35, shadow=1.00, trail=0.0)),
    (1.00, dict(bottom=556.0, s=0.994, dx=1,   ang=-0.7, cam=1.001, camdy=1,  dust=0.95, shadow=0.88, trail=0.2)),
    (1.70, dict(bottom=508.0, s=0.972, dx=8,   ang=-1.5, cam=1.003, camdy=3,  dust=1.00, shadow=0.66, trail=0.7)),
    (2.50, dict(bottom=456.0, s=0.928, dx=24,  ang=-2.5, cam=1.005, camdy=6,  dust=0.78, shadow=0.44, trail=1.0)),
    (3.40, dict(bottom=400.0, s=0.850, dx=50,  ang=-3.7, cam=1.008, camdy=10, dust=0.55, shadow=0.27, trail=1.0)),
    (4.40, dict(bottom=346.0, s=0.706, dx=96,  ang=-5.1, cam=1.010, camdy=15, dust=0.36, shadow=0.14, trail=1.0)),
    (5.40, dict(bottom=298.0, s=0.566, dx=162, ang=-6.5, cam=1.012, camdy=20, dust=0.23, shadow=0.06, trail=1.0)),
    (6.40, dict(bottom=261.0, s=0.444, dx=238, ang=-7.8, cam=1.014, camdy=25, dust=0.14, shadow=0.02, trail=1.0)),
    (7.50, dict(bottom=230.0, s=0.340, dx=318, ang=-8.6, cam=1.016, camdy=30, dust=0.08, shadow=0.00, trail=1.0)),
]

cam_c = (OUT_W / 2, OUT_H * 0.55)


def vehicle_state(t):
    """returns (tr_M, s, dx, dy, ang) for the given time"""
    k = lerp_keys(KEYS, t)
    s = k["s"]
    dy = k["bottom"] - PIVOT_OUT[1] - (WHEEL_LOCAL_Y - PIVOT[1]) * s
    pos = (PIVOT_OUT[0] + k["dx"] * S, PIVOT_OUT[1] + dy)
    return make_M(pos, s, k["ang"], PIVOT), k


def render(t):
    k = lerp_keys(KEYS, t)
    s = k["s"]
    dy = k["bottom"] - PIVOT_OUT[1] - (WHEEL_LOCAL_Y - PIVOT[1]) * s
    pos = (PIVOT_OUT[0] + k["dx"] * S, PIVOT_OUT[1] + dy)
    tr_M = make_M(pos, s, k["ang"], PIVOT)

    shake = (1 - t / 0.55) ** 2 if t < 0.55 else 0.0
    sx = rng.normal(0, 1) * 3.4 * shake
    sy = rng.normal(0, 1) * 2.8 * shake
    cam_M = make_M((cam_c[0] + sx, cam_c[1] + sy + k["camdy"]), k["cam"], 0.0, cam_c)

    # ---------------- world ------------------------------------------------
    world = plate.copy()

    ball_fade = max(0.0, 1.0 - max(0.0, 620.8 - k["bottom"]) / 85.0) ** 1.25
    if ball_fade > 0.01:
        for ball, (ox, oy) in balls:
            b = ball.copy()
            b[:, :, 3] = (b[:, :, 3].astype(np.float32) * ball_fade).astype(np.uint8)
            world = alpha_over(world, warp(b, translate2(ox * S, oy * S)))

    # ground shadow
    if k["shadow"] > 0.01:
        sh = SHADOW.copy()
        sh[:, :, 3] = (sh[:, :, 3].astype(np.float32) * k["shadow"]).astype(np.uint8)
        sc = 0.80 + 0.55 * (1 - k["shadow"])
        m = make_M(((870 + k["dx"]) * S, 700 * S), sc, 0.0,
                   (SHADOW.shape[1] / 2, SHADOW.shape[0] / 2))
        world = alpha_over(world, warp(sh, m))

    # dust kicked up at take-off
    if k["dust"] > 0.01:
        for j, (nx, ny) in enumerate(((250, 700), (1285, 700))):
            for p in range(4):
                si = j * 4 + p
                life = min(1.0, max(0.0, t - 0.10 * si) / 1.9)
                sc = (0.20 + 0.85 * life) * (0.8 + 0.12 * si)
                op = k["dust"] * (1 - life) ** 1.25 * 0.95
                if op < 0.01:
                    continue
                puff = PUFFS[(si * 3 + int(t * 7)) % len(PUFFS)].copy()
                puff[:, :, 3] = (puff[:, :, 3].astype(np.float32) * op).astype(np.uint8)
                px = (nx - 70 + math.sin(t * 0.6 + si * 1.7) * 80) * S
                py = (ny - 15 - life * 95) * S
                m = make_M((px, py), sc, 0.0, (puff.shape[1] / 2, puff.shape[0] / 2))
                world = alpha_over(world, warp(puff, m))

    # smoke trail left hanging in the air
    if k["trail"] > 0.01 and t > 0.8:
        for j, (nx, ny) in enumerate(NOZZLES):
            for step in range(7):
                tk = t - 0.16 * step
                if tk < 0.5:
                    continue
                trk, kk = vehicle_state(tk)
                h = np.array([(nx - bx0) * S, (ny - by0) * S, 1.0], np.float32)
                p = (trk @ h)[:2]
                age = (t - tk)
                op = k["trail"] * math.exp(-age * 1.45) * 0.85
                if op < 0.02:
                    continue
                sc = 0.13 + 0.46 * age
                puff = PUFFS[(j * 5 + step * 3) % len(PUFFS)].copy()
                puff[:, :, 3] = (puff[:, :, 3].astype(np.float32) * op).astype(np.uint8)
                m = make_M((p[0], p[1]), sc, 0.0, (puff.shape[1] / 2, puff.shape[0] / 2))
                world = alpha_over(world, warp(puff, m))

    world = warp(world, cam_M)

    # ---------------- air --------------------------------------------------
    frame = alpha_over(world, warp(truck, tr_M))

    stretch = 1.0 + 0.26 * smoothstep((t - 1.0) / 4.0) + 0.05 * math.sin(t * 29.0)
    flick = 0.80 + 0.24 * (0.5 + 0.5 * math.sin(t * 53.0)) + 0.07 * rng.normal()
    bloom = np.zeros((OUT_H, OUT_W, 4), np.uint8)
    for cone, noz, cx0s, cy0s in cones:
        c = cone.copy()
        c[:, :, 3] = np.clip(c[:, :, 3].astype(np.float32) * flick, 0, 255).astype(np.uint8)
        sxm = 1.0 + 0.025 * math.sin(t * 41.0 + noz[0])
        local = np.array([[1 / sxm, 0, noz[0] * (1 - 1 / sxm)],
                          [0, 1 / stretch, noz[1] * (1 - 1 / stretch)],
                          [0, 0, 1]], np.float32)
        full = tr_M @ translate((cx0s - bx0) * S, (cy0s - by0) * S) @ local
        wc = warp(c, full)
        frame = alpha_over(frame, wc)
        bloom = additive(bloom, cv2.GaussianBlur(wc, (0, 0), 20), 1.1 * flick)
    frame = additive(frame, bloom, 1.0)

    if t > 3.8:
        kern = np.zeros((3, 3), np.float32)
        kern[1, :] = 1 / 3
        frame = cv2.filter2D(frame, -1, kern)
    return frame


NFRAMES = int(DUR * FPS)
os.makedirs(os.path.join(F, "seq"), exist_ok=True)
frame_paths = []
idxs = list(range(NFRAMES))
if PREVIEW:
    idxs = [0, 15, 30, 48, 72, 99, 129, 165, 200, 224]

for i in idxs:
    frame = render(i / FPS)
    p = os.path.join(F, "seq", f"f{i:04d}.png")
    cv2.imwrite(p, cv2.cvtColor(frame, cv2.COLOR_RGBA2BGRA))
    frame_paths.append(p)
    if not PREVIEW and i % 30 == 0:
        print(f"  frame {i}/{NFRAMES}")

json.dump(frame_paths, open(os.path.join(OUT, "frames.json"), "w"))
print("rendered", len(frame_paths), "frames")
