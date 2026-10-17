"""Step 5 - synthesise the rocket rumble that goes with the shot."""
import os

import numpy as np
from scipy import signal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

SR = 48000
DUR = 7.5
n = int(SR * DUR)
t = np.arange(n) / SR
rng = np.random.default_rng(3)


def norm(x, peak=0.9):
    m = np.max(np.abs(x))
    return x / m * peak if m > 0 else x


# ---------------------------------------------------------------- rumble ---
white = rng.normal(0, 1, n)
brown = np.cumsum(white)
brown = brown - np.mean(brown)
brown = signal.lfilter(*signal.butter(2, 260, "low", fs=SR), brown)
brown = norm(brown, 1.0)

# a slow swelling envelope: the engines spool up, hold, then die away
env = np.clip(t / 0.45, 0, 1) ** 1.2
env *= np.clip((DUR - t) / 0.9, 0, 1) ** 0.8
# small amplitude wobble so it never sounds static
env *= 1.0 + 0.10 * np.sin(2 * np.pi * 3.1 * t) + 0.06 * np.sin(2 * np.pi * 7.3 * t)
rumble = brown * env

# ------------------------------------------------------- low engine tone ---
f0 = 42.0 + 46.0 * np.clip(t / 2.2, 0, 1) - 12.0 * np.clip((t - 5.0) / 2.5, 0, 1)
phase = 2 * np.pi * np.cumsum(f0) / SR
tone = (np.sin(phase) + 0.45 * np.sin(2 * phase) + 0.22 * np.sin(3 * phase))
tone *= env * 0.30

# ------------------------------------------------------------------ hiss ---
hiss = rng.normal(0, 1, n)
hiss = signal.lfilter(*signal.butter(2, [900, 7000], "band", fs=SR), hiss)
hiss = norm(hiss, 1.0)
flick = 0.75 + 0.25 * np.sin(2 * np.pi * 23.0 * t) + 0.12 * np.sin(2 * np.pi * 61.0 * t)
hiss *= env * 0.085 * flick

# ------------------------------------------------------------- liftoff -----
def thump(at, dur, amp, f0, f1):
    i0 = int(at * SR)
    ln = int(dur * SR)
    idx = np.arange(ln)
    e = np.exp(-idx / (SR * dur * 0.22))
    sweep = f0 * np.exp(-idx / (SR * dur * 0.4)) + f1
    s = np.sin(2 * np.pi * np.cumsum(sweep) / SR) * e
    s += rng.normal(0, 1, ln) * e * 0.35
    out = np.zeros(n)
    out[i0:i0 + ln] += s * amp
    return out


thumps = thump(0.38, 0.9, 0.75, 120, 40) + thump(0.62, 0.7, 0.35, 90, 35)

# --------------------------------------------------------------- whoosh ----
i0 = int(3.1 * SR)
ln = int(2.4 * SR)
idx = np.arange(ln)
e = np.sin(np.pi * np.clip(idx / ln, 0, 1)) ** 1.6
sw = rng.normal(0, 1, ln)
sw = signal.lfilter(*signal.butter(2, [400, 4200], "band", fs=SR), sw)
sw = norm(sw, 1.0)
whoosh = np.zeros(n)
whoosh[i0:i0 + ln] += sw * e * 0.16

# ------------------------------------------------------------------ mix ----
mix = rumble * 0.55 + tone + hiss + thumps * 0.5 + whoosh
mix = signal.lfilter(*signal.butter(2, 9000, "low", fs=SR), mix)
mix = norm(mix, 0.89)

# gentle fade
fade = np.ones(n)
fade[: int(0.12 * SR)] = np.linspace(0, 1, int(0.12 * SR))
fade[- int(0.7 * SR):] = np.linspace(1, 0, int(0.7 * SR))
mix *= fade

stereo = np.stack([mix, mix * 0.97 + 0.012 * np.sin(2 * np.pi * 55 * t)], axis=1)
pcm = (stereo * 32767).astype(np.int16)

import wave
with wave.open(os.path.join(OUT, "rocket.wav"), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("wrote", os.path.join(OUT, "rocket.wav"), pcm.shape)
