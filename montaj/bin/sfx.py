#!/usr/bin/env python3
"""SFX kutubxonasini sintez qiladi va montaj vaqtiga mos trek yig'adi.

Tayyor sempllar ishlatilmaydi (litsenziya), hammasi shu yerda hisoblab
chiqariladi: shovqin filtri bilan "whoosh", sinus + konvert bilan "pop",
past chastotali "impact", qisqa "tick".

Ishlatish:
  bin/sfx.py work/sfx_reja.json -o work/sfx.wav --davomiylik 68.1
  # reja: [{"t":7.4,"ovoz":"whoosh","gain":0.8}, ...]
"""
import argparse, json, sys
import numpy as np

SR = 48000


def _env(n, atak, susayish, kuch=3.0):
    """Tez ko'tarilib, eksponensial susayadigan konvert."""
    a = int(atak * SR)
    d = max(1, n - a)
    e = np.concatenate([np.linspace(0, 1, max(1, a)),
                        np.exp(-np.linspace(0, kuch, d))])
    return e[:n]


def _bandpass(x, lo, hi):
    """FFT orqali oddiy polosali filtr (lo, hi — massiv bo'lsa sweep)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = (f >= lo) & (f <= hi)
    X[~m] *= 0.04
    return np.fft.irfft(X, len(x))


def whoosh(dur=0.38, lo=250, hi=5200):
    """Shovqin + yuqoriga siljiydigan filtr — element uchib kirgandek."""
    n = int(dur * SR)
    x = np.random.default_rng(7).standard_normal(n)
    bloklar, chiqish = 24, np.zeros(n)
    for i in range(bloklar):
        a, b = i * n // bloklar, (i + 1) * n // bloklar
        p = i / (bloklar - 1)
        seg = _bandpass(x[a:b], lo * (1 - p) + 900 * p, hi * (0.25 + 0.75 * p))
        chiqish[a:b] = seg
    chiqish *= _env(n, 0.02, dur, kuch=2.6)
    return chiqish / (np.abs(chiqish).max() + 1e-9)


def pop(dur=0.09, f0=760):
    """Qisqa "pop" — matn paydo bo'lganda."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f0 * t) * 0.8
         + np.sin(2 * np.pi * f0 * 2.02 * t) * 0.25)
    x += np.random.default_rng(3).standard_normal(n) * 0.06
    x *= _env(n, 0.002, dur, kuch=7.0)
    return x / (np.abs(x).max() + 1e-9)


def impact(dur=0.55, f0=72):
    """Past "impact" — to'liq ekran karta chiqqanda."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 * np.exp(-t * 3.2)          # chastota tushib boradi
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    sh = np.random.default_rng(11).standard_normal(n)
    x = x * 0.9 + _bandpass(sh, 120, 1800) * 0.18
    x *= _env(n, 0.003, dur, kuch=5.0)
    return x / (np.abs(x).max() + 1e-9)


def tick(dur=0.035, f0=2200):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f0 * t) * _env(n, 0.001, dur, kuch=10.0)
    return x / (np.abs(x).max() + 1e-9)


KUTUBXONA = {"whoosh": whoosh, "pop": pop, "impact": impact, "tick": tick}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("reja", help="JSON: [{t, ovoz, gain}]")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--davomiylik", type=float, required=True)
    a = p.parse_args()

    reja = json.load(open(a.reja))
    n = int(a.davomiylik * SR) + SR
    mix = np.zeros(n)
    keshlar = {}
    for e in reja:
        nom = e["ovoz"]
        if nom not in KUTUBXONA:
            raise SystemExit(f"XATO: '{nom}' ovozi yo'q")
        if nom not in keshlar:
            keshlar[nom] = KUTUBXONA[nom]()
        s = keshlar[nom] * e.get("gain", 1.0)
        i = int(e["t"] * SR)
        j = min(i + len(s), n)
        mix[i:j] += s[:j - i]
        print(f"  {e['t']:6.2f}s  {nom:7s} gain {e.get('gain',1.0):.2f}")

    cho = np.abs(mix).max()
    if cho > 0.95:
        mix *= 0.95 / cho
    pcm = (mix * 32767).astype(np.int16)

    import wave
    with wave.open(a.out, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"\n{a.out}: {len(reja)} ta effekt, {n/SR:.1f}s, cho'qqi {cho:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
