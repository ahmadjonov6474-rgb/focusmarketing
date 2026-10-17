#!/usr/bin/env python3
"""Ikki kamerani audio bo'yicha sinxronlaydi.

Chiqish: B kamerasining A ga nisbatan siljishi (sekundda).
Musbat qiymat = B kechikkan, ya'ni B ni oldinga surish kerak.
"""
import argparse, subprocess, sys, tempfile, os
import numpy as np

SR = 8000          # tahlil uchun yetarli
ENV_HZ = 200       # envelope diskretizatsiyasi


def audio(path, sr=SR):
    """Faylni mono float32 massiv qilib o'qiydi."""
    cmd = ["ffmpeg", "-v", "error", "-i", path,
           "-map", "a:0", "-ac", "1", "-ar", str(sr),
           "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def envelope(x, sr=SR, hz=ENV_HZ):
    """Amplituda konturi — nutq ritmini ushlaydi, tembr farqiga bog'liq emas."""
    win = max(1, sr // hz)
    n = (len(x) // win) * win
    e = np.abs(x[:n]).reshape(-1, win).mean(axis=1)
    e = e - e.mean()
    return e


def offset(a, b, hz=ENV_HZ, max_shift_s=None):
    """FFT kross-korrelyatsiya orqali siljishni topadi."""
    n = len(a) + len(b)
    nfft = 1 << (n - 1).bit_length()
    A = np.fft.rfft(a, nfft)
    B = np.fft.rfft(b, nfft)
    cc = np.fft.irfft(A * np.conj(B), nfft)
    cc = np.concatenate((cc[-(len(b) - 1):], cc[:len(a)]))
    lags = np.arange(-(len(b) - 1), len(a))
    if max_shift_s:
        m = np.abs(lags) <= int(max_shift_s * hz)
        cc, lags = cc[m], lags[m]
    k = int(np.argmax(cc))
    peak = cc[k]
    # ishonch: cho'qqi qolgan fonga nisbatan necha barobar
    noise = np.sqrt(np.mean(np.delete(cc, slice(max(0, k - 5), k + 6)) ** 2))
    return lags[k] / hz, float(peak / noise) if noise > 0 else 0.0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cam_a"); p.add_argument("cam_b")
    p.add_argument("--max-shift", type=float, default=120.0,
                   help="izlanadigan maksimal siljish (s)")
    a = p.parse_args()

    ea = envelope(audio(a.cam_a))
    eb = envelope(audio(a.cam_b))
    off, conf = offset(ea, eb, max_shift_s=a.max_shift)

    # build.py uchun to'g'ridan-to'g'ri ishlatiladigan qiymat:
    # B kameraning manba vaqti = A manba vaqti + offset_b
    print(f"offset_b={-off:.3f}")
    print(f"ishonch={conf:.1f}")
    if conf < 6:
        print("OGOHLANTIRISH: ishonch past — ovozlar bir sahnadan emasmi?",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
