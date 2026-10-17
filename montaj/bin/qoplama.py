#!/usr/bin/env python3
"""Subtitr va grafika kartalarini videoga qo'yadi (yoqib yozadi).

Referens-2 mantig'i: kadr uzun, kesim kam, lekin hikoyaning kalit
nuqtalarida TO'LIQ EKRAN karta chiqadi — shunda video zerikarli bo'lmaydi.
Hook kartasi esa shaffof: video ustida, tepada turadi.

Kartalar vaqti CHIQISH (montajdan keyingi) vaqtida beriladi.
"""
import argparse, json, os, subprocess, sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--subs", help="ASS fayl")
    p.add_argument("--kartalar", help="kartalar JSON (start/end chiqish vaqtida)")
    p.add_argument("--png", default="work/kartalar", help="PNG papkasi")
    p.add_argument("--crf", type=int, default=18)
    p.add_argument("--preset", default="slow")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    kartalar = json.load(open(a.kartalar)) if a.kartalar else []
    fayllar = sorted(os.listdir(a.png)) if kartalar else []
    if kartalar and len(fayllar) != len(kartalar):
        raise SystemExit(f"XATO: {len(kartalar)} karta, {len(fayllar)} PNG")

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning", "-stats",
           "-i", a.video]
    for f in fayllar:
        cmd += ["-loop", "1", "-i", os.path.join(a.png, f)]

    zanjir, oqim = [], "0:v"
    if a.subs:
        # ASS ichidagi vaqtlar allaqachon chiqish vaqtida (subs.py ko'chirgan)
        zanjir.append(f"[{oqim}]subtitles={a.subs}[vs]")
        oqim = "vs"
    for i, k in enumerate(kartalar, 1):
        yangi = f"v{i}"
        zanjir.append(
            f"[{oqim}][{i}:v]overlay=0:0:"
            f"enable='between(t,{k['start']:.3f},{k['end']:.3f})'[{yangi}]")
        oqim = yangi

    fc = ";".join(zanjir) if zanjir else None
    if fc:
        cmd += ["-filter_complex", fc, "-map", f"[{oqim}]"]
    else:
        cmd += ["-map", "0:v"]
    cmd += ["-map", "0:a", "-c:v", "libx264", "-preset", a.preset,
            "-crf", str(a.crf), "-pix_fmt", "yuv420p", "-profile:v", "high",
            "-c:a", "copy", "-shortest", a.out]

    print(f"Subtitr: {'ha' if a.subs else 'yo\'q'}, kartalar: {len(kartalar)}")
    for k in kartalar:
        print(f"  {k['start']:6.2f}-{k['end']:6.2f}  {k['tur']:5s}  {k['asos']}")
    if a.dry_run:
        print("\n" + " ".join(cmd[:6]) + " ... " + a.out)
        return 0
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    sys.exit(main())
