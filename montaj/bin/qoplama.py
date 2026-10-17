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

# Referensdan o'lchangan o'tish (11.40-11.60 s):
#   2 kadr kadr qorayadi -> 1-2 kadr oq chaqnash -> karta 0.2 s da normal
#   yorqinlikka tushadi. Pop kadrlari karta2.py da tayyorlanadi.
QORAYISH = 0.08   # kartadan oldin kadr qorayadi
CHAQNASH = 0.22   # oq chaqnash so'nishi


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--subs", help="ASS fayl (chiqish vaqtida)")
    p.add_argument("--reja", help="karta2.py bergan reja.json")
    p.add_argument("--qora", default="work/grafika_qora.png")
    p.add_argument("--oq", default="work/grafika_oq.png")
    p.add_argument("--chaqnashsiz", action="store_true",
                   help="kartalarga chaqnash o'tishini qo'shmaslik")
    p.add_argument("--crf", type=int, default=18)
    p.add_argument("--preset", default="medium")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    reja = json.load(open(a.reja)) if a.reja else []

    # --- kartaga chaqnash bilan o'tish ---
    flash = []
    if reja and not a.chaqnashsiz:
        kartalar = {}
        for e in reja:
            if e["tur"] == "karta":
                k = os.path.basename(e["png"])[:2]
                kartalar.setdefault(k, e["start"])
        for t0 in sorted(kartalar.values()):
            flash.append({"png": a.qora, "tur": "oq",
                          "start": round(t0 - QORAYISH, 3), "end": round(t0, 3),
                          "animatsiya": "tinch"})
            flash.append({"png": a.oq, "tur": "oq", "sonish": True,
                          "start": round(t0, 3),
                          "end": round(t0 + CHAQNASH, 3),
                          "animatsiya": "tinch"})
    reja = reja + flash

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning", "-stats",
           "-i", a.video]
    for e in reja:
        cmd += ["-loop", "1", "-i", e["png"]]

    # har PNG oqimini o'z vaqtiga suramiz va kirishda fade beramiz,
    # shunda element "paydo bo'lib" chiqadi, birdan tushib qolmaydi
    tayyor = []
    for i, e in enumerate(reja, 1):
        if e.get("sonish"):      # oq chaqnash: to'liq oqdan nolga so'nadi
            f = f"fade=t=out:st={e['start']:.3f}:d={CHAQNASH}:alpha=1"
        else:
            f = "null"
        tayyor.append(
            f"[{i}:v]format=rgba,setpts=PTS+{e['start']:.3f}/TB,{f}[ov{i}]")

    zanjir, oqim = list(tayyor), "0:v"
    if a.subs:
        zanjir.append(f"[{oqim}]subtitles={a.subs}[vs]")
        oqim = "vs"

    for i, e in enumerate(reja, 1):
        yangi = f"v{i}"
        s, t = e["start"], e["end"]
        zanjir.append(
            f"[{oqim}][ov{i}]overlay=x=0:y=0:"
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
