"""Step 3 - cut the vehicle and the thruster flames out of the source photo.

The silhouette is seeded from a hand measured outline; GrabCut then snaps the
alpha to the real edges.  The dark bodywork (rocker, bumpers, wheel arches) is
seeded explicitly, otherwise GrabCut mistakes it for the ground shadow.
"""
import json
import os

import cv2
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "assets")
F = os.path.join(ROOT, "frames")

src = Image.open(os.path.join(A, "source_truck.jpeg")).convert("RGB")
W, H = src.size
rgb = np.array(src)

OUTLINE = [
    (58, 528), (72, 505), (100, 494), (140, 489), (185, 484), (240, 479),
    (275, 462), (310, 440), (350, 418), (395, 398), (440, 380), (490, 362),
    (540, 348), (590, 332), (640, 315), (690, 300), (740, 291), (800, 285),
    (860, 288), (920, 296), (980, 307), (1040, 320), (1100, 333), (1160, 347),
    (1220, 361), (1280, 374), (1340, 387), (1400, 399), (1460, 409), (1520, 418),
    (1580, 428), (1630, 436), (1666, 442),
    (1666, 500), (1666, 560), (1666, 600), (1668, 626), (1682, 640), (1627, 675),
    (1560, 668), (1500, 662), (1460, 690), (1400, 702), (1300, 704), (1210, 700),
    (1170, 682), (1120, 676), (900, 676), (700, 676), (500, 674), (430, 668),
    (400, 660), (370, 692), (300, 704), (230, 706), (185, 698), (168, 700),
    (150, 722), (110, 738), (68, 720), (62, 655), (58, 600), (56, 560),
]

# dark bodywork that GrabCut would otherwise drop
DARK_PARTS = [
    [(420, 596), (1120, 596), (1130, 672), (420, 670)],                 # rocker
    [(62, 600), (168, 600), (172, 700), (150, 724), (110, 740), (66, 722)],  # front bumper
    [(1420, 596), (1668, 604), (1684, 640), (1627, 678), (1500, 664), (1430, 640)],  # rear bumper
    [(140, 470), (215, 470), (215, 700), (140, 700)],                   # front flare
    [(1425, 520), (1495, 520), (1495, 690), (1425, 690)],               # rear flare
]
WHEELS = [((278, 596), (100, 92)), ((1282, 592), (108, 96))]

# regions that must stay background: the ground shadow + the smoke
FORCE_BG = [
    [(410, 700), (1140, 700), (1140, 860), (410, 860)],
    [(0, 745), (200, 745), (200, 900), (0, 900)],
    [(1380, 700), (1712, 700), (1712, 900), (1380, 900)],
]

poly = np.array(OUTLINE, np.int32)
seed = np.zeros((H, W), np.uint8)
cv2.fillPoly(seed, [poly], 255)

k13 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (27, 27))
k9 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (19, 19))

sure_fg = cv2.erode(seed, k13)
for d in DARK_PARTS:
    m = np.zeros((H, W), np.uint8)
    cv2.fillPoly(m, [np.array(d, np.int32)], 255)
    sure_fg = cv2.bitwise_or(sure_fg, cv2.erode(m, k9))
for (c, r) in WHEELS:
    m = np.zeros((H, W), np.uint8)
    cv2.ellipse(m, c, r, 0, 0, 360, 255, -1)
    sure_fg = cv2.bitwise_or(sure_fg, cv2.erode(m, k9))

sure_bg = cv2.bitwise_not(cv2.dilate(seed, k13))
for d in FORCE_BG:
    m = np.zeros((H, W), np.uint8)
    cv2.fillPoly(m, [np.array(d, np.int32)], 255)
    sure_bg = cv2.bitwise_or(sure_bg, m)

gmask = np.full((H, W), cv2.GC_PR_BGD, np.uint8)
gmask[sure_bg > 0] = cv2.GC_BGD
gmask[seed > 0] = cv2.GC_PR_FGD
gmask[sure_fg > 0] = cv2.GC_FGD

bgd = np.zeros((1, 65), np.float64)
fgd = np.zeros((1, 65), np.float64)
cv2.grabCut(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), gmask, None, bgd, fgd,
            7, cv2.GC_INIT_WITH_MASK)
mask = np.where((gmask == cv2.GC_FGD) | (gmask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
mask = cv2.bitwise_and(mask, seed)
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k9, iterations=2)
n, lab, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
if n > 1:
    idx = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    mask = np.where(lab == idx, 255, 0).astype(np.uint8)
ff = mask.copy()
h2 = np.zeros((H + 2, W + 2), np.uint8)
cv2.floodFill(ff, h2, (0, 0), 255)
mask = cv2.bitwise_or(mask, cv2.bitwise_not(ff))
print("truck mask area:", int((mask > 0).sum()))

alpha = cv2.GaussianBlur(mask.astype(np.float32) / 255.0, (0, 0), 1.0) * 255
alpha[alpha < 14] = 0
truck = np.dstack([rgb, alpha.astype(np.uint8)])
ys, xs = np.where(mask > 0)
bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
print("truck bbox:", bbox)
Image.fromarray(truck, "RGBA").save(os.path.join(A, "truck_rgba.png"))

vis = rgb.copy()
vis[mask > 0] = (0.5 * vis[mask > 0] + 0.5 * np.array([0, 255, 255])).astype(np.uint8)
Image.fromarray(vis).save(os.path.join(F, "truck_mask_check.png"))

# --------------------------------------------------------------- flames ----
R = rgb[:, :, 0].astype(np.int16)
G = rgb[:, :, 1].astype(np.int16)
B = rgb[:, :, 2].astype(np.int16)
mx = rgb.max(axis=2).astype(np.int16)
mn = rgb.min(axis=2).astype(np.int16)
sat = ((mx - mn) / np.maximum(mx, 1)).astype(np.float32)
warm = (R > 140) & (G > 65) & (R > B + 40) & (sat > 0.28)
cool = (B > 130) & (B > R + 20) & (G > 85) & (sat > 0.18)
hot = (mx > 225) & (sat > 0.12) & (sat < 0.75)
flame = (warm | cool | hot).astype(np.uint8) * 255
flame = cv2.morphologyEx(flame, cv2.MORPH_CLOSE, k9, iterations=2)

win = np.zeros((H, W), np.uint8)
cv2.ellipse(win, (240, 730), (215, 190), 0, 0, 360, 255, -1)
cv2.ellipse(win, (1285, 730), (215, 190), 0, 0, 360, 255, -1)
flame = cv2.bitwise_and(flame, win)
flame = cv2.bitwise_and(flame, 255 - mask)      # don't double up on the vehicle
n, lab, stats, _ = cv2.connectedComponentsWithStats(flame, 8)
keep = np.zeros_like(flame)
for i in range(1, n):
    if stats[i, cv2.CC_STAT_AREA] > 250:
        keep[lab == i] = 255
flame = keep
fal = cv2.GaussianBlur(flame.astype(np.float32) / 255.0, (0, 0), 1.2) * 255
fal[fal < 8] = 0
print("flame area:", int((fal > 0).sum()))
Image.fromarray(np.dstack([rgb, fal.astype(np.uint8)]), "RGBA").save(os.path.join(A, "fire_rgba.png"))

fvis = rgb.copy()
fvis[fal > 40] = (0.4 * fvis[fal > 40] + 0.6 * np.array([255, 120, 0])).astype(np.uint8)
Image.fromarray(fvis).save(os.path.join(F, "fire_mask_check.png"))

json.dump({"size": [W, H], "truck_bbox": bbox,
           "nozzles": [{"x": 250, "y": 690}, {"x": 1285, "y": 686}],
           "ground_y": 700},
          open(os.path.join(A, "sprites.json"), "w"), indent=2)
print("done")
