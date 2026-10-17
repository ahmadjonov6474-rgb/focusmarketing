#!/usr/bin/env python3
"""EDL bo'yicha yakuniy montajni yig'adi.

Video — kliplarga ko'ra ikki kameradan, ovoz — doim bitta eng yaxshi manbadan.

Nega bir o'tishli `trim+concat` emas: bitta fayldan 17 ta trim olinsa, ffmpeg
har shox uchun manbani boshidan dekodlab bufferlaydi va xotira o'nlab GB ga
chiqadi (sinovda 13.9 GB da OOM bo'ldi). Shuning uchun:

  1) har klip alohida kesiladi (`-ss` bilan — faqat kerakli joy dekodlanadi)
  2) concat demuxer bilan ulanadi (qayta kodlashsiz)
  3) ovoz alohida yig'iladi (PCM buferi kichik) va oxirida muxlanadi
"""
import argparse, json, os, shutil, subprocess, sys, tempfile


def framing(cam, W, H, fps):
    """Kadrni 9:16 ga keltiradi.

    `burilish` — kamera yonboshlatib olingan bo'lsa (Sony XAVC rotatsiya
    metadatasini yozmaydi): 1 = soat yo'nalishi, 2 = teskari. Burilish ENG
    BIRINCHI qo'llanadi, aks holda kesish noto'g'ri o'qqa tushadi.
    `y` — vertikal markaz (0 tepa, 1 past).
    """
    zoom = cam.get("zoom", 1.0)
    xf, yf = cam.get("x", 0.5), cam.get("y", 0.5)
    rot = int(cam.get("burilish", 0))
    h = int(H * zoom)
    h += h % 2
    pre = f"transpose={rot}," if rot else ""
    return (f"{pre}scale=-2:{h}:flags=lanczos,"
            f"crop={W}:{H}:(iw-{W})*{xf}:(ih-{H})*{yf},setsar=1,"
            f"fps={fps},format=yuv420p")


def vcodec(preview):
    if preview:
        return ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "30"]
    return ["-c:v", "libx264", "-preset", "slow", "-crf", "18",
            "-pix_fmt", "yuv420p", "-profile:v", "high"]


def push_in(W, H, fps, dur, zoom, orqaga=False):
    """Kadr harakati: yaqinlashuv yoki orqaga chekinish, easing bilan.

    Chiziqli zoom ko'zga "o'lik" ko'rinadi, shuning uchun ease-out egri
    chizig'i ishlatiladi: boshida tezroq, oxirida sekinlashadi. Planlar
    navbatma-navbat yaqinlashadi va chekinadi — bir xillik yo'qoladi.

    Jitterni kamaytirish uchun avval 1.6x ga kattalashtiriladi, keyin
    zoompan 1080x1920 ga qaytaradi: siljish subpiksel bo'ladi.
    """
    nf = max(2, int(round(dur * fps)))
    p = f"(on/{nf})"
    egri = (f"pow(1-{p},3)" if orqaga else f"(1-pow(1-{p},3))")
    return (f",scale=iw*1.6:-2:flags=bicubic,"
            f"zoompan=z='1+{zoom:.4f}*{egri}':d=1:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"s={W}x{H}:fps={fps}")


def kes_klip(cam, s, e, W, H, fps, preview, out, zoom=0.0, orqaga=False):
    """Bitta klipni manbadan kesib, kadrlab, kodlaydi (video only)."""
    ss = s + cam.get("offset", 0.0)
    vf = framing(cam, W, H, fps)
    if zoom > 0:
        vf += push_in(W, H, fps, e - s, zoom, orqaga)
    cmd = (["ffmpeg", "-y", "-v", "error", "-ss", f"{ss:.3f}",
            "-i", cam["fayl"], "-t", f"{e - s:.3f}", "-an",
            "-vf", vf]
           + vcodec(preview)
           + ["-video_track_timescale", "90000", out])
    subprocess.run(cmd, check=True)


def ovoz(cams, edl, audio_src, out):
    """Ovozni bitta manbadan EDL bo'yicha yig'adi (atrim + concat)."""
    off = cams[audio_src].get("offset", 0.0)
    parts, labs = [], []
    for i, (s, e, _c) in enumerate(edl["kliplar"]):
        parts.append(f"[0:a]atrim=start={s + off:.3f}:end={e + off:.3f},"
                     f"asetpts=PTS-STARTPTS[a{i}]")
        labs.append(f"[a{i}]")
    n = len(edl["kliplar"])
    parts.append("".join(labs) + f"concat=n={n}:v=0:a=1[aout]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", cams[audio_src]["fayl"],
                    "-filter_complex", ";".join(parts), "-map", "[aout]",
                    "-c:a", "pcm_s16le", "-ar", "48000", out], check=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("config", help="kameralar config JSON")
    p.add_argument("edl", help="edl.py chiqishi")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--preview", action="store_true",
                   help="tez, past sifatli ko'rik")
    p.add_argument("--ish", help="vaqtinchalik papka (standart: temp)")
    p.add_argument("--zoom", type=float, default=0.0,
                   help="har klipda sekin yaqinlashuv (masalan 0.05 = 5%%)")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    cfg = json.load(open(args.config))
    edl = json.load(open(args.edl))
    cams = cfg["kameralar"]
    W, H = cfg.get("w", 1080), cfg.get("h", 1920)
    fps = cfg.get("fps", 30)
    if args.preview:
        W, H = W // 2, H // 2
    klips = edl["kliplar"]

    if args.dry_run:
        print(f"kliplar: {len(klips)}, "
              f"{sum(e - s for s, e, _ in klips):.2f}s -> {args.out}")
        return 0

    ish = args.ish or tempfile.mkdtemp(prefix="montaj_")
    os.makedirs(ish, exist_ok=True)
    try:
        segs = []
        for i, (s, e, c) in enumerate(klips):
            f = os.path.join(ish, f"seg{i:03d}.mp4")
            # toq klip yaqinlashadi, juft klip chekinadi
            kes_klip(cams[c], s, e, W, H, fps, args.preview, f,
                     args.zoom, orqaga=(i % 2 == 1))
            segs.append(f)
            print(f"  [{i + 1:3d}/{len(klips)}] kamera {c}  "
                  f"{s:7.2f}-{e:7.2f}  ({e - s:5.2f}s)", flush=True)

        lst = os.path.join(ish, "segs.txt")
        with open(lst, "w") as fh:
            for f in segs:
                fh.write(f"file '{os.path.abspath(f)}'\n")
        vid = os.path.join(ish, "video.mp4")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat",
                        "-safe", "0", "-i", lst, "-c", "copy", vid], check=True)

        aud = os.path.join(ish, "ovoz.wav")
        ovoz(cams, edl, cfg.get("ovoz_manbai", 0), aud)

        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", aud,
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                        "-shortest", args.out], check=True)
        print(f"\n{args.out}: {len(klips)} klip yig'ildi")
    finally:
        if not args.ish:
            shutil.rmtree(ish, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
