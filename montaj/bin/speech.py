#!/usr/bin/env python3
"""Audiodan nutq va pauza segmentlarini ajratadi.

Chiqish: JSON — {"davomiylik":s, "nutq":[[boshi,oxiri],...], "pauza":[...]}
Matn kerak emas: faqat energiya konturi bo'yicha ishlaydi.
"""
import argparse, json, subprocess, sys
import numpy as np

SR = 16000
HOP = 0.02          # 20 ms


def audio(path, sr=SR):
    cmd = ["ffmpeg", "-v", "error", "-i", path,
           "-map", "a:0", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def rms_db(x, sr=SR, hop=HOP):
    w = int(sr * hop)
    n = (len(x) // w) * w
    f = x[:n].reshape(-1, w)
    r = np.sqrt((f ** 2).mean(axis=1) + 1e-12)
    return 20 * np.log10(r)


def segments(db, hop, margin, min_speech, min_sil):
    """Gisterezis bilan nutq oraliqlarini yig'adi."""
    floor = np.percentile(db, 10)
    peak = np.percentile(db, 95)
    thr = max(floor + margin, peak - 25)

    on = db > thr
    segs, start = [], None
    sil_run = 0
    sil_frames = int(min_sil / hop)

    for i, v in enumerate(on):
        if v:
            if start is None:
                start = i
            sil_run = 0
        elif start is not None:
            sil_run += 1
            if sil_run >= sil_frames:
                end = i - sil_run + 1
                if (end - start) * hop >= min_speech:
                    segs.append([start * hop, end * hop])
                start, sil_run = None, 0
    if start is not None and (len(on) - start) * hop >= min_speech:
        segs.append([start * hop, len(on) * hop])
    return segs, float(thr), float(floor)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("media")
    p.add_argument("--margin", type=float, default=11.0,
                   help="shovqin polidan necha dB yuqorisi nutq hisoblanadi")
    p.add_argument("--min-speech", type=float, default=0.30)
    p.add_argument("--min-sil", type=float, default=0.35,
                   help="shu uzunlikdan katta jimlik — pauza")
    p.add_argument("--pad", type=float, default=0.10,
                   help="har segment chetiga qo'shiladigan nafas (s)")
    p.add_argument("-o", "--out")
    a = p.parse_args()

    x = audio(a.media)
    db = rms_db(x)
    segs, thr, floor = segments(db, HOP, a.margin, a.min_speech, a.min_sil)
    dur = len(x) / SR

    # nafas qo'shish va ustma-ust tushganlarini birlashtirish
    padded = []
    for s, e in segs:
        s, e = max(0.0, s - a.pad), min(dur, e + a.pad)
        if padded and s <= padded[-1][1]:
            padded[-1][1] = e
        else:
            padded.append([s, e])

    gaps, prev = [], 0.0
    for s, e in padded:
        if s - prev > 0.01:
            gaps.append([round(prev, 3), round(s, 3)])
        prev = e
    if dur - prev > 0.01:
        gaps.append([round(prev, 3), round(dur, 3)])

    out = {
        "davomiylik": round(dur, 3),
        "shovqin_poli_dB": round(floor, 1),
        "chegara_dB": round(thr, 1),
        "nutq": [[round(s, 3), round(e, 3)] for s, e in padded],
        "pauza": gaps,
        "nutq_jami_s": round(sum(e - s for s, e in padded), 2),
    }
    js = json.dumps(out, ensure_ascii=False, indent=2)
    if a.out:
        open(a.out, "w").write(js)
        print(f"{a.out}: {len(padded)} nutq bo'lagi, "
              f"{out['nutq_jami_s']}s / {out['davomiylik']}s")
    else:
        print(js)
    return 0


if __name__ == "__main__":
    sys.exit(main())
