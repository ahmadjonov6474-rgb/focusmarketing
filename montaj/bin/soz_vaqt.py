#!/usr/bin/env python3
"""Bo'lak darajasidagi matnni subtitr uchun mayda, vaqtlangan qatorlarga bo'ladi.

Muammo: matn qo'lda nutq bo'laklariga bog'langanda chegaralar biroz siljiydi —
bir bo'lakka 28 belgi/s, qo'shnisiga 6 belgi/s tushib qoladi va subtitr
gapdan oldin yoki keyin chiqadi.

Yechim ikki bosqich:
  1. TEKISLASH — bitta blok (masalan savol, keyin javob) ichidagi matn
     qayta taqsimlanadi: har bo'lakka o'z NUTQ VAQTIga mutanosib miqdorda
     matn tushadi. Shunda tezlik hamma joyda bir xil bo'ladi.
  2. BO'LISH — har bo'lak matni 3-5 so'zli qatorlarga bo'linadi va vaqt
     bo'lak ichidagi nutq energiyasiga qarab (jimliklarni hisobga olmay)
     taqsimlanadi.

Kirish: [{"start","end","text","blok"(ixtiyoriy)}]
Chiqish: [{"start","end","text"}] — mayda qatorlar, manba vaqtida.
"""
import argparse, json, re, subprocess, sys
import numpy as np

SR = 16000
HOP = 0.02


def ovoz_konturi(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-map", "a:0",
                          "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    w = int(SR * HOP)
    n = (len(x) // w) * w
    r = np.sqrt((x[:n].reshape(-1, w) ** 2).mean(axis=1) + 1e-12)
    return 20 * np.log10(r)


def nutq_vazni(db, s, e, chegara):
    """Bo'lak ichidagi kadrlar uchun 'gapirilgan' vaznlar (jim kadr ~0)."""
    i0, i1 = int(s / HOP), max(int(e / HOP), int(s / HOP) + 1)
    seg = db[i0:i1]
    w = np.clip((seg - chegara) / 12.0, 0.05, 1.0)   # jim kadr ham 0.05
    return w


def tekisla(bolaklar, db, chegara):
    """Blok ichidagi matnni nutq vaqtiga mutanosib qayta taqsimlaydi."""
    out = []
    for blok in sorted({b.get("blok", 1) for b in bolaklar}):
        bs = [b for b in bolaklar if b.get("blok", 1) == blok]
        sozlar = []
        for b in bs:
            sozlar += b["text"].split()
        vaqtlar = [float(nutq_vazni(db, b["start"], b["end"], chegara).sum() * HOP)
                   for b in bs]
        jami_vaqt = sum(vaqtlar)
        jami_belgi = sum(len(s) + 1 for s in sozlar)

        k = 0
        for b, t in zip(bs, vaqtlar):
            ulush = jami_belgi * t / jami_vaqt
            olingan, n = 0, 0
            while k + n < len(sozlar) and olingan < ulush:
                olingan += len(sozlar[k + n]) + 1
                n += 1
            # oxirgi bo'lakka qolgan hamma so'z
            if b is bs[-1]:
                n = len(sozlar) - k
            out.append({**b, "text": " ".join(sozlar[k:k + n])})
            k += n
    out.sort(key=lambda x: x["start"])
    return out


def bol(bolak, db, chegara, max_soz, max_belgi):
    """Bo'lak matnini qatorlarga bo'lib, nutq vazniga qarab vaqtlaydi."""
    sozlar = bolak["text"].split()
    if not sozlar:
        return []
    qatorlar, cur = [], []
    for s in sozlar:
        cur.append(s)
        uz = len(" ".join(cur))
        oxirgi = s.endswith((".", "!", "?", ":"))
        if len(cur) >= max_soz or uz >= max_belgi or (oxirgi and len(cur) >= 2):
            qatorlar.append(cur)
            cur = []
    if cur:
        if qatorlar and len(cur) == 1:
            qatorlar[-1] += cur
        else:
            qatorlar.append(cur)

    s, e = bolak["start"], bolak["end"]
    w = nutq_vazni(db, s, e, chegara)
    cw = np.concatenate(([0.0], np.cumsum(w)))
    jami = cw[-1] if cw[-1] > 0 else 1.0
    belgilar = [len(" ".join(q)) + 1 for q in qatorlar]
    toplam = sum(belgilar)

    res, acc = [], 0
    for q, b in zip(qatorlar, belgilar):
        p0, p1 = acc / toplam, (acc + b) / toplam
        acc += b
        i0 = int(np.searchsorted(cw, p0 * jami))
        i1 = int(np.searchsorted(cw, p1 * jami))
        t0 = s + i0 * HOP
        t1 = s + max(i1, i0 + 1) * HOP
        res.append({"start": round(min(t0, e), 3),
                    "end": round(min(t1, e), 3),
                    "text": " ".join(q)})
    return res


def main():
    p = argparse.ArgumentParser()
    p.add_argument("media")
    p.add_argument("transcript", help="bo'lak darajasidagi JSON")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--max-soz", type=int, default=5)
    p.add_argument("--max-belgi", type=int, default=38)
    p.add_argument("--min-s", type=float, default=0.6,
                   help="shundan qisqa qator qo'shnisiga qo'shiladi")
    p.add_argument("--tekisla", action="store_true",
                   help="blok ichida matnni nutq vaqtiga mutanosib qayta taqsimlash")
    a = p.parse_args()

    db = ovoz_konturi(a.media)
    chegara = float(np.percentile(db, 10)) + 11.0   # speech.py bilan bir xil
    bolaklar = json.load(open(a.transcript))

    if a.tekisla:
        bolaklar = tekisla(bolaklar, db, chegara)
        print("Tekislangandan keyin (belgi/s):")
        for b in bolaklar:
            d = b["end"] - b["start"]
            print(f"  {b['start']:6.2f}-{b['end']:6.2f} {len(b['text'])/d:5.1f}  "
                  f"{b['text'][:46]}")

    cues = []
    for b in bolaklar:
        qs = bol(b, db, chegara, a.max_soz, a.max_belgi)
        # juda qisqa qatorlarni qo'shnisiga qo'shib yuborish — ko'z ulgurmaydi
        birlashgan = []
        for q in qs:
            if birlashgan and q["end"] - q["start"] < a.min_s:
                birlashgan[-1]["text"] += " " + q["text"]
                birlashgan[-1]["end"] = q["end"]
            else:
                birlashgan.append(q)
        if len(birlashgan) > 1 and \
                birlashgan[0]["end"] - birlashgan[0]["start"] < a.min_s:
            birlashgan[1]["text"] = birlashgan[0]["text"] + " " + birlashgan[1]["text"]
            birlashgan[1]["start"] = birlashgan[0]["start"]
            birlashgan.pop(0)
        cues += birlashgan
    json.dump(cues, open(a.out, "w"), ensure_ascii=False, indent=2)
    print(f"\n{a.out}: {len(cues)} subtitr qatori")
    return 0


if __name__ == "__main__":
    sys.exit(main())
