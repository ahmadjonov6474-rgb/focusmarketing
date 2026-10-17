#!/usr/bin/env python3
"""Kadrma-kadr grafika qatlamini videoga qo'yadi, motion blur bilan.

Grafika 50 fps da render qilingan. Video ham 50 fps ga ko'tariladi,
qatlamlar qo'shiladi, keyin `tmix` bilan juft kadrlar o'rtachalanib
25 fps ga tushiriladi — tez harakatlanayotgan element tabiiy xiralashadi
(motion blur). Alpha bu bosqichda yo'q, shuning uchun o'rtachalash xavfsiz.

Bo'sh kadrlar (grafika ko'rinmaydigan joylar) shaffof PNG bilan
to'ldiriladi, chunki ffmpeg image2 ketma-ketligi uzluksiz raqam talab qiladi.
"""
import argparse, json, os, shutil, subprocess, sys


def toldir(papka, oxirgi, shaffof):
    """Yetishmayotgan kadrlarni shaffof PNG bilan to'ldiradi."""
    qoshildi = 0
    for i in range(0, oxirgi + 1):
        f = os.path.join(papka, f"g{i:06d}.png")
        if not os.path.exists(f):
            os.link(shaffof, f) if hasattr(os, "link") else shutil.copy(shaffof, f)
            qoshildi += 1
    return qoshildi


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("png_papka")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--subs")
    p.add_argument("--crf", type=int, default=18)
    p.add_argument("--preset", default="medium")
    a = p.parse_args()

    meta = json.load(open(os.path.join(a.png_papka, "meta.json")))
    fps, fps_eff = meta["fps"], meta["fps_eff"]

    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", a.video], capture_output=True, check=True,
        text=True).stdout.strip())
    oxirgi = int(dur * fps_eff)

    shaffof = os.path.join(a.png_papka, "_shaffof.png")
    if not os.path.exists(shaffof):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                        "color=c=black@0.0:s=1080x1920,format=rgba",
                        "-frames:v", "1", shaffof], check=True)
    n = toldir(a.png_papka, oxirgi, shaffof)
    print(f"{n} ta bo'sh kadr shaffof bilan to'ldirildi (jami {oxirgi+1})")

    v = f"[0:v]fps={fps_eff}"
    if a.subs:
        v += f",subtitles={a.subs}"
    v += "[vb]"
    fc = (f"{v};"
          f"[vb][1:v]overlay=0:0:format=auto[ov];"
          f"[ov]tmix=frames={meta['blur']}:weights='1 1',fps={fps}[vout]")

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning", "-stats",
           "-i", a.video,
           "-framerate", str(fps_eff), "-start_number", "0",
           "-i", os.path.join(a.png_papka, "g%06d.png"),
           "-filter_complex", fc, "-map", "[vout]", "-map", "0:a",
           "-c:v", "libx264", "-preset", a.preset, "-crf", str(a.crf),
           "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-c:a", "copy", "-shortest", a.out]
    print(f"Motion blur: {meta['blur']}x ({fps_eff} -> {fps} fps)")
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    sys.exit(main())
