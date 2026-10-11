#!/usr/bin/env python3
"""Build the 9:16 animated short: 'From the Front Lines to the Networks Back Home'.

Inputs : images/scene*.jpg (768x1376), audio/narration.mp3 (voice-01, English w/ Mexican voice)
Output : output/From_Front_Lines_to_Networks_Back_Home_9x16.mp4
"""
import math
import os
import random
import struct
import subprocess
import sys
import wave
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "output")
IMG_DIR = os.path.join(ROOT, "images")
AUD_DIR = os.path.join(ROOT, "audio")
CAP_DIR = os.path.join(ROOT, "captions")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(CAP_DIR, exist_ok=True)

FFMPEG = subprocess.check_output(
    [sys.executable, "-c", "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"],
    text=True,
).strip()

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
W, H, FPS = 1080, 1920, 30
LEAD, TAIL = 3.0, 5.0          # title lead-in / end-card tail
XFADE = 0.5                    # crossfade seconds

# ---------------------------------------------------------------- narration beats
BEATS = [
    "For years, Mexican cartels used commercial drones for surveillance, watching routes, rivals, and targets.",
    "Then came reports that some were hunting something more advanced.",
    "By joining Ukraine's International Legion under the cover of volunteers, individuals linked to groups like CJNG and the Sinaloa Cartel could access drone training built under real combat pressure.",
    "One documented case involved a Mexican traveling on forged documents, who completed the courses, and displayed pre-existing expertise that raised suspicion.",
    "Mexican and Ukrainian intelligence both looked into the pattern.",
    "The larger question remains unresolved: how much of the hard-won knowledge from one war would end up reshaping networks operating thousands of miles away.",
]

SCENES = [  # display order: hook, drones, Ukraine Legion, forged docs, intel, closing arc
    ("scene1_hook.jpg", "title"),
    ("scene2_commercial_drones.jpg", "top"),
    ("scene4_ukraine_front.jpg", "top"),
    ("scene3_forged_documents.jpg", "top"),
    ("scene5_intelligence.jpg", "top"),
    ("scene6_global_arc.jpg", "center"),
]

CAPTIONS = [
    dict(main=[("FROM THE FRONT LINES", 78, (255, 255, 255)),
               ("TO THE NETWORKS BACK HOME", 78, (255, 176, 32))],
         sub=[("ANIMATED BRIEFING · BASED ON PUBLISHED REPORTS", 34, (215, 215, 215))],
         box=False),
    dict(main=[("COMMERCIAL DRONES,", 62, (255, 255, 255)),
               ("FOR YEARS", 62, (255, 255, 255))],
         sub=[("SURVEILLANCE INSIDE MEXICO", 36, (255, 176, 32))],
         box=True),
    dict(main=[("UNDER THE COVER", 62, (255, 255, 255)),
               ("OF VOLUNTEERS", 62, (255, 255, 255))],
         sub=[("UKRAINE'S INTERNATIONAL LEGION", 35, (255, 176, 32)),
              ("CJNG · SINALOA CARTEL (REPORTED)", 35, (255, 176, 32))],
         box=True),
    dict(main=[("ONE DOCUMENTED CASE:", 58, (255, 255, 255)),
               ("FORGED DOCUMENTS", 58, (255, 255, 255))],
         sub=[("PRE-EXISTING EXPERTISE RAISED SUSPICION", 33, (255, 176, 32))],
         box=True),
    dict(main=[("BOTH INTELLIGENCE SERVICES", 55, (255, 255, 255)),
               ("LOOK INTO THE PATTERN", 55, (255, 255, 255))],
         sub=[("MEXICO AND UKRAINE INVESTIGATE", 35, (255, 176, 32))],
         box=True),
    dict(main=[("HOW MUCH OF IT", 76, (255, 255, 255)),
               ("WOULD TRAVEL HOME?", 76, (255, 176, 32))],
         sub=[("THE QUESTION THAT REMAINS UNANSWERED", 34, (225, 225, 225))],
         box=False),
]


def narration_duration():
    wav = os.path.join(AUD_DIR, "narration.wav")
    if not os.path.exists(wav):
        subprocess.run([FFMPEG, "-y", "-v", "error",
                        "-i", os.path.join(AUD_DIR, "narration.mp3"), wav], check=True)
    with wave.open(wav) as w:
        return w.getnframes() / w.getframerate()


# ---------------------------------------------------------------- captions (Pillow)
def render_caption(idx, spec, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad_x, pad_y, gap_main, gap_sub = 40, 30, 16, 12
    fonts_main = [ImageFont.truetype(FONT_BOLD, s) for _, s, _ in spec["main"]]
    fonts_sub = [ImageFont.truetype(FONT_BOLD, s) for _, s, _ in spec["sub"]]

    def block_h():
        h = sum(f.size + gap_main for f in fonts_main)
        if spec["sub"]:
            h += 14 + sum(f.size + gap_sub for f in fonts_sub)
        return h - gap_main - gap_sub

    widths = [d.textbbox((0, 0), t, font=f)[2] for (t, _, _), f in zip(spec["main"], fonts_main)]
    widths += [d.textbbox((0, 0), t, font=f)[2] for (t, _, _), f in zip(spec["sub"], fonts_sub)]
    # shrink-to-fit: never let text run past the 1080px frame
    max_text_w = W - 40 - (pad_x * 2 if spec["box"] else 0)
    if max(widths) > max_text_w:
        factor = max_text_w / max(widths)
        fonts_main = [ImageFont.truetype(FONT_BOLD, max(int(f.size * factor), 20)) for f in fonts_main]
        fonts_sub = [ImageFont.truetype(FONT_BOLD, max(int(f.size * factor), 18)) for f in fonts_sub]
        widths = [d.textbbox((0, 0), t, font=f)[2] for (t, _, _), f in zip(spec["main"], fonts_main)]
        widths += [d.textbbox((0, 0), t, font=f)[2] for (t, _, _), f in zip(spec["sub"], fonts_sub)]
    bw = max(widths) + pad_x * 2
    bh = block_h() + pad_y * 2

    if spec["mode"] == "top":
        bx, by = (W - bw) / 2, 170
    elif spec["mode"] == "title":
        bx, by = (W - bw) / 2, 760 - bh / 2
    else:  # center (end card)
        bx, by = (W - bw) / 2, 830 - bh / 2

    if spec["box"]:
        d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=22,
                            fill=(6, 8, 12, 170), outline=(255, 176, 32, 110), width=3)

    y = by + pad_y
    for (t, s, col), f in zip(spec["main"], fonts_main):
        stroke = max(6, s // 8)
        d.text((W / 2, y), t, font=f, fill=col, anchor="mt",
               stroke_width=stroke, stroke_fill=(0, 0, 0, 235))
        y += s + gap_main
    if spec["sub"]:
        y += 14 - gap_sub
    for (t, s, col), f in zip(spec["sub"], fonts_sub):
        stroke = max(5, s // 8)
        d.text((W / 2, y), t, font=f, fill=col, anchor="mt",
               stroke_width=stroke, stroke_fill=(0, 0, 0, 235))
        y += s + gap_sub

    if spec["mode"] == "center":
        note = "BASED ON PUBLIC REPORTS · FOR EDUCATION & COMMENTARY"
        f = ImageFont.truetype(FONT_BOLD, 30)
        d.text((W / 2, 1790), note, font=f, fill=(200, 200, 200, 205), anchor="mm",
               stroke_width=4, stroke_fill=(0, 0, 0, 235))
    img.save(path)


# ---------------------------------------------------------------- ambient bed
def synth_ambient(path, dur, sr=44100):
    n = int(dur * sr) + sr // 10
    rnd = random.Random(7)
    # one-pole lowpass coefficient for ~260 Hz wind/rumble noise
    alpha = 1 - math.exp(-2 * math.pi * 260 / sr)
    peak = 0.0
    chans = []
    for ch in range(2):
        y = 0.0
        buf = [0.0] * n
        ph1, ph2, ph3 = 0.0, 0.0, 0.0
        step1 = 2 * math.pi * 55.0 / sr
        step2 = 2 * math.pi * 82.5 / sr
        step3 = 2 * math.pi * 110.0 / sr
        for i in range(n):
            t = i / sr
            ph1 += step1; ph2 += step2; ph3 += step3
            drone = (math.sin(ph1) + 0.45 * math.sin(ph2) + 0.25 * math.sin(ph3))
            lfo = 0.72 + 0.28 * math.sin(2 * math.pi * 0.07 * t + ch * 1.3)
            x = rnd.uniform(-1, 1)
            y += alpha * (x - y)
            wind = y * (0.55 + 0.45 * math.sin(2 * math.pi * 0.05 * t + ch * 0.9))
            v = drone * lfo * 0.147 + wind * 0.045
            buf[i] = v
            a = abs(v)
            if a > peak:
                peak = a
        chans.append(buf)
    gain = 0.22 / peak
    fade_in, fade_out = int(1.5 * sr), int(2.5 * sr)
    total = int(dur * sr)
    frames = bytearray()
    for i in range(total):
        env = 1.0
        if i < fade_in:
            env = i / fade_in
        elif i > total - fade_out:
            env = max(0.0, (total - i) / fade_out)
        for c in range(2):
            frames += struct.pack("<h", int(max(-1.0, min(1.0, chans[c][i] * gain * env)) * 32767))
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(bytes(frames))


# ---------------------------------------------------------------- timeline
def main():
    T = narration_duration()
    total_beats = sum(len(b) for b in BEATS)
    fr = [len(b) / total_beats for b in BEATS]

    b = [0.0]
    for f in fr:
        b.append(b[-1] + f)
    # stream length targets: scene k fully visible when beat k starts
    Lt = [LEAD]
    Lt.append(LEAD + b[1] * T)                     # Ukraine scene in  (beat B)
    Lt.append(LEAD + (b[1] + b[2]) * T)            # forged-docs scene in (beat C->D... use b[3])
    Lt[2] = LEAD + b[3] * T
    Lt.append(LEAD + b[4] * T)                     # intel scene in (beat E)
    Lt.append(LEAD + b[5] * T)                     # closing scene in (beat F)
    Lt.append(LEAD + T + TAIL)                     # end of video

    d = [Lt[0],
         Lt[1] - Lt[0] + XFADE,
         Lt[2] - Lt[1] + XFADE,
         Lt[3] - Lt[2] + XFADE,
         Lt[4] - Lt[3] + XFADE,
         Lt[5] - Lt[4] + XFADE]
    N = [max(round(x * FPS), 45) for x in d]
    L = [N[0] / FPS]
    for k in range(1, 6):
        L.append(L[-1] + N[k] / FPS - XFADE)
    total = L[5]
    print(f"narration T={T:.2f}s  scene frames={N}  total={total:.2f}s")

    # captions
    cap_paths = []
    for i, spec in enumerate(CAPTIONS):
        spec = dict(spec, mode=SCENES[i][1])
        p = os.path.join(CAP_DIR, f"cap{i}.png")
        render_caption(i, spec, p)
        cap_paths.append(p)
    amb_path = os.path.join(AUD_DIR, "ambient.wav")
    synth_ambient(amb_path, total)

    # caption visibility windows (stream time)
    wins = [(0.08, L[0] - XFADE - 0.08)]
    for k in range(1, 5):
        wins.append((L[k - 1] + 0.08, L[k] - XFADE - 0.08))
    wins.append((L[4] + 0.08, total - 0.15))

    # filtergraph
    vf = []
    for i in range(6):
        n = N[i]
        step = 0.10 / max(n - 1, 1)
        if i % 2 == 0:
            z = f"1+{step:.6f}*on"
        else:
            z = f"1.10-{step:.6f}*on"
        vf.append(
            f"[{i}:v]scale=2160:3870:flags=lanczos,crop=2160:3840:0:15,"
            f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={n}:s=1080x1920:fps={FPS},setsar=1,format=yuv420p[v{i}]"
        )
    cur = "v0"
    for k in range(1, 6):
        off = L[k - 1] - XFADE
        out = f"x{k}"
        vf.append(f"[{cur}][v{k}]xfade=transition=fade:duration={XFADE}:offset={off:.3f}[{out}]")
        cur = out
    for k, p in enumerate(cap_paths):
        ci = 6 + 2 + k  # images 0-5, narration 6, ambient 7, caps 8+
        a, bnd = wins[k]
        out = f"o{k}"
        vf.append(f"[{cur}][{ci}:v]overlay=0:0:enable='between(t,{a:.3f},{bnd:.3f})'[{out}]")
        cur = out
    vf.append(f"[{cur}]fade=t=in:st=0:d=0.4,fade=t=out:st={total - 0.6:.3f}:d=0.6,format=yuv420p[vout]")
    lead_ms = int(LEAD * 1000)
    vf.append(f"[6:a]adelay={lead_ms}:all=1,volume=1.0[na]")
    vf.append(f"[7:a]atrim=0:{total:.3f},afade=t=in:st=0:d=1.5,afade=t=out:st={total - 2.5:.3f}:d=2.5[am]")
    vf.append("[na][am]amix=inputs=2:duration=longest:normalize=0,volume=-1.5dB,alimiter=limit=0.87:level=disabled[aout]")

    out_path = os.path.join(OUT_DIR, "From_Front_Lines_to_Networks_Back_Home_9x16.mp4")
    cmd = [FFMPEG, "-y", "-v", "warning"]
    for i in range(6):
        cmd += ["-i", os.path.join(IMG_DIR, SCENES[i][0])]
    cmd += ["-i", os.path.join(AUD_DIR, "narration.mp3"), "-i", amb_path]
    for p in cap_paths:
        cmd += ["-i", p]
    cmd += [
        "-filter_complex", ";".join(vf),
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "19",
        "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "160k",
        "-movflags", "+faststart",
        "-t", f"{total:.3f}",
        out_path,
    ]
    print("running ffmpeg ...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-6000:])
        sys.exit(1)
    tail = [ln for ln in r.stderr.splitlines() if "warning" not in ln.lower()][-4:]
    print("\n".join(tail))
    size = os.path.getsize(out_path) / 1e6
    print(f"OK -> {out_path}  ({size:.1f} MB, {total:.1f}s)")


if __name__ == "__main__":
    main()
