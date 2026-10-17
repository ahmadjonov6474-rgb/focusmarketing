#!/usr/bin/env python3
"""EDL bo'yicha yakuniy montajni yig'adi (ffmpeg filter_complex).

Video — kliplarga ko'ra ikki kameradan, ovoz — doim bitta eng yaxshi manbadan.
"""
import argparse, json, subprocess, sys


def framing(idx, cam, W, H):
    """Kadrni 9:16 ga kesadi: balandlik bo'yicha o'lchab, x bo'yicha qirqadi."""
    zoom = cam.get("zoom", 1.0)
    xf = cam.get("x", 0.5)
    h = int(H * zoom)
    h += h % 2
    return (f"scale=-2:{h}:flags=lanczos,"
            f"crop={W}:{H}:(iw-{W})*{xf}:(ih-{H})/2,setsar=1")


def build_filter(edl, cams, W, H, fps, audio_src):
    v, a, parts = [], [], []
    off = [c.get("offset", 0.0) for c in cams]

    for i, (s, e, c) in enumerate(edl["kliplar"]):
        ss, ee = s + off[c], e + off[c]
        parts.append(
            f"[{c}:v]trim=start={ss:.3f}:end={ee:.3f},setpts=PTS-STARTPTS,"
            f"{framing(i, cams[c], W, H)},fps={fps},"
            f"format=yuv420p[v{i}]")
        v.append(f"[v{i}]")
        # ovoz har doim bitta manbadan — tembr sakramaydi
        sa, ea = s + off[audio_src], e + off[audio_src]
        parts.append(
            f"[{audio_src}:a]atrim=start={sa:.3f}:end={ea:.3f},"
            f"asetpts=PTS-STARTPTS[a{i}]")
        a.append(f"[a{i}]")

    n = len(edl["kliplar"])
    inter = "".join(x + y for x, y in zip(v, a))
    parts.append(f"{inter}concat=n={n}:v=1:a=1[vout][aout]")
    return ";".join(parts)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("config", help="kameralar config JSON")
    p.add_argument("edl", help="edl.py chiqishi")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--preview", action="store_true",
                   help="tez, past sifatli ko'rik")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    cfg = json.load(open(args.config))
    edl = json.load(open(args.edl))
    cams = cfg["kameralar"]
    W, H = cfg.get("w", 1080), cfg.get("h", 1920)
    fps = cfg.get("fps", 30)
    if args.preview:
        W, H = W // 2, H // 2

    fc = build_filter(edl, cams, W, H, fps, cfg.get("ovoz_manbai", 0))

    cmd = ["ffmpeg", "-y", "-hide_banner"]
    for c in cams:
        cmd += ["-i", c["fayl"]]
    cmd += ["-filter_complex", fc, "-map", "[vout]", "-map", "[aout]"]
    if args.preview:
        cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "30"]
    else:
        cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "18",
                "-pix_fmt", "yuv420p", "-profile:v", "high"]
    cmd += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", args.out]

    if args.dry_run:
        print(f"kliplar: {len(edl['kliplar'])}, filtr uzunligi: {len(fc)} belgi")
        print(" ".join(cmd[:8]), "... [filter_complex] ...", args.out)
        return 0

    print(f"Yig'ilmoqda: {len(edl['kliplar'])} klip -> {args.out}")
    r = subprocess.run(cmd)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
