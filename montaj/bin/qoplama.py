#!/usr/bin/env python3
"""Subtitr va grafikalarni videoga yoqib yozadi, animatsiya bilan.

Grafikalar `karta2.py` bergan rejadan olinadi: har element bir nechta
HOLAT (PNG) dan iborat bo'ladi va ular ketma-ket chiqadi — shunda matn
bosqichma-bosqich "yozilib borgandek" ko'rinadi (referens-2 dagidek).

Animatsiya turlari:
  pastdan  — element pastdan sirg'alib chiqadi (0.25 s)
  yo'q     — darhol paydo bo'ladi (kartalar uchun; referensda ham shunday)
"""
import argparse, json, os, subprocess, sys

SLIDE = 0.25     # sirg'alish davomiyligi
SILJISH = 260    # necha piksel pastdan ko'tariladi


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--subs", help="ASS fayl (chiqish vaqtida)")
    p.add_argument("--reja", help="karta2.py bergan reja.json")
    p.add_argument("--crf", type=int, default=18)
    p.add_argument("--preset", default="medium")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    reja = json.load(open(a.reja)) if a.reja else []

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning", "-stats",
           "-i", a.video]
    for e in reja:
        cmd += ["-loop", "1", "-i", e["png"]]

    zanjir, oqim = [], "0:v"
    if a.subs:
        zanjir.append(f"[{oqim}]subtitles={a.subs}[vs]")
        oqim = "vs"

    # bir element ichidagi birinchi holatgina sirg'aladi
    birinchi = {}
    for e in reja:
        kalit = os.path.basename(e["png"])[:2]
        birinchi.setdefault(kalit, e["start"])

    for i, e in enumerate(reja, 1):
        yangi = f"v{i}"
        s, t = e["start"], e["end"]
        kalit = os.path.basename(e["png"])[:2]
        if e.get("animatsiya") == "pastdan" and abs(birinchi[kalit] - s) < 1e-6:
            y = (f"if(lt(t-{s:.3f},{SLIDE}),"
                 f"{SILJISH}*(1-(t-{s:.3f})/{SLIDE}),0)")
        else:
            y = "0"
        zanjir.append(
            f"[{oqim}][{i}:v]overlay=x=0:y='{y}':"
            f"enable='between(t,{s:.3f},{t:.3f})'[{yangi}]")
        oqim = yangi

    fc = ";".join(zanjir) if zanjir else None
    if fc:
        cmd += ["-filter_complex", fc, "-map", f"[{oqim}]"]
    else:
        cmd += ["-map", "0:v"]
    cmd += ["-map", "0:a", "-c:v", "libx264", "-preset", a.preset,
            "-crf", str(a.crf), "-pix_fmt", "yuv420p", "-profile:v", "high",
            "-c:a", "copy", "-shortest", a.out]

    print(f"Subtitr: {'ha' if a.subs else 'yo\'q'}, grafika holatlari: {len(reja)}")
    if a.dry_run:
        print(" ".join(cmd[:6]) + " ... " + a.out)
        return 0
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    sys.exit(main())
