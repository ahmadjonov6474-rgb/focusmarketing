#!/usr/bin/env python3
"""Nutqni matnga aylantiradi (sherpa-onnx + Whisper turbo), manba vaqtida.

Nega segment bo'yicha: sherpa-onnx Whisper so'z vaqtlarini bermaydi, shuning
uchun matn `speech.py` topgan nutq bo'laklariga bog'lanadi — vaqtlar o'sha
bo'laklardan olinadi, ya'ni aniq. Uzun bo'laklar ichki jimliklar bo'yicha
mayda bo'laklarga bo'linadi (subtitr uchun).

Chiqish: [{"start":s,"end":s,"text":"..."}] — manba video vaqtida.
"""
import argparse, json, os, subprocess, sys
import numpy as np

SR = 16000


def audio(path, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-map", "a:0",
                          "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def bol(x, s, e, max_s, sr=SR):
    """Bo'lakni ichki eng jim nuqtalardan max_s dan qisqa qismlarga bo'ladi."""
    if e - s <= max_s:
        return [(s, e)]
    seg = x[int(s * sr):int(e * sr)]
    hop = int(0.02 * sr)
    n = (len(seg) // hop) * hop
    r = np.sqrt((seg[:n].reshape(-1, hop) ** 2).mean(axis=1) + 1e-12)
    parts, cur = [], s
    while e - cur > max_s:
        lo = int((cur + max_s * 0.55 - s) / 0.02)
        hi = int((cur + max_s - s) / 0.02)
        hi = min(hi, len(r) - 1)
        if hi <= lo:
            break
        k = lo + int(np.argmin(r[lo:hi]))
        t = s + k * 0.02
        parts.append((cur, t))
        cur = t
    parts.append((cur, e))
    return parts


def main():
    p = argparse.ArgumentParser()
    p.add_argument("media")
    p.add_argument("speech_json", help="speech.py chiqishi")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--model", default="/home/user/models/sherpa-onnx-whisper-turbo")
    p.add_argument("--til", default="uz")
    p.add_argument("--max-bolak", type=float, default=6.0,
                   help="subtitr uchun bitta bo'lakning maksimal uzunligi (s)")
    a = p.parse_args()

    import sherpa_onnx
    pre = os.path.join(a.model, "turbo")
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=pre + "-encoder.int8.onnx",
        decoder=pre + "-decoder.int8.onnx",
        tokens=pre + "-tokens.txt",
        language=a.til, task="transcribe",
        num_threads=os.cpu_count() or 4)

    x = audio(a.media)
    sp = json.load(open(a.speech_json))["nutq"]

    bolaklar = []
    for s, e in sp:
        bolaklar += bol(x, s, e, a.max_bolak)

    out = []
    for i, (s, e) in enumerate(bolaklar, 1):
        chunk = x[int(s * SR):int(e * SR)]
        st = rec.create_stream()
        st.accept_waveform(SR, chunk)
        rec.decode_stream(st)
        txt = st.result.text.strip()
        if txt:
            out.append({"start": round(s, 3), "end": round(e, 3), "text": txt})
        print(f"[{i:3d}/{len(bolaklar)}] {s:7.2f}-{e:7.2f}  {txt}", flush=True)

    json.dump(out, open(a.out, "w"), ensure_ascii=False, indent=2)
    print(f"\n{a.out}: {len(out)} bo'lak / {len(bolaklar)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
