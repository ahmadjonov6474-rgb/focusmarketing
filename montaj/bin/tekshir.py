#!/usr/bin/env python3
"""Montaj sifatini tekshiradi: kesim so'z o'rtasiga tushmaganmi?

Har klip chegarasida ovoz energiyasini o'lchaydi. Agar kesim nuqtasida
ovoz baland bo'lsa — demak so'z yarmidan kesilgan va eshituvchi buni
sezadi. Boshi va oxiri alohida tekshiriladi.
"""
import argparse, json, subprocess, sys
import numpy as np

SR = 16000
HOP = 0.02


def db_contour(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-map", "a:0",
                          "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    w = int(SR * HOP)
    n = (len(x) // w) * w
    r = np.sqrt((x[:n].reshape(-1, w) ** 2).mean(axis=1) + 1e-12)
    return 20 * np.log10(r)


def dbat(db, t):
    i = int(t / HOP)
    return db[min(max(i, 0), len(db) - 1)]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("edl")
    p.add_argument("media", help="ovoz manbai (odatda camA)")
    p.add_argument("--jim", type=float, default=-22.0,
                   help="shu dB dan past bo'lsa kesim xavfsiz")
    a = p.parse_args()

    db = db_contour(a.media)
    edl = json.load(open(a.edl))
    kl = edl["kliplar"]
    ogoh = 0

    print("Kesim nuqtalari (manba vaqtida):\n")
    for i, (s, e, c) in enumerate(kl):
        # klip boshi: undan OLDINGI 60 ms jim bo'lishi kerak
        oldin = max(dbat(db, s - 0.06), dbat(db, s - 0.03))
        ichi = dbat(db, s + 0.08)
        bosh_ok = oldin <= a.jim or i == 0 and False
        # klip oxiri: undan KEYINGI 60 ms jim bo'lishi kerak
        keyin = max(dbat(db, e + 0.03), dbat(db, e + 0.06))
        oxir_ok = keyin <= a.jim

        if i == 0:
            bayroq = "" if oldin <= a.jim else "  <-- BOSHI SO'Z O'RTASIDA"
            if bayroq:
                ogoh += 1
            print(f"  BOSH  {s:7.2f}  oldin {oldin:6.1f} dB  "
                  f"ichi {ichi:6.1f} dB{bayroq}")
        if i + 1 < len(kl):
            s2 = kl[i + 1][0]
            if abs(s2 - e) < 1e-3:
                continue   # uzluksiz — kesim yo'q, faqat rakurs o'zgarishi
            kirish = dbat(db, s2 + 0.08)
            oldin2 = max(dbat(db, s2 - 0.06), dbat(db, s2 - 0.03))
            yomon = (keyin > a.jim) or (oldin2 > a.jim)
            if yomon:
                ogoh += 1
            print(f"  {i+1:2d}->{i+2:<2d} {e:7.2f} -> {s2:7.2f}  "
                  f"oxiridan keyin {keyin:6.1f} dB   "
                  f"boshidan oldin {oldin2:6.1f} dB"
                  + ("  <-- SO'Z O'RTASI" if yomon else ""))
        else:
            bayroq = "" if keyin <= a.jim else "  <-- OXIRI SO'Z O'RTASIDA"
            if bayroq:
                ogoh += 1
            print(f"  OXIR  {e:7.2f}  keyin {keyin:6.1f} dB{bayroq}")

    print(f"\n{len(kl)} klip, {ogoh} ta ogohlantirish")
    return 1 if ogoh else 0


if __name__ == "__main__":
    sys.exit(main())
