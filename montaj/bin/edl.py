#!/usr/bin/env python3
"""Kesim rejasini (EDL) quradi.

Uch bosqich:
  1. tanlov  — hikoyaning qaysi bo'laklari qoladi (muharrir qarori, tanlov.json)
  2. siqish  — maqsadli davomiylikka sig'dirish (eng past muhimlikdan kesiladi)
  3. ritm    — pauzalarni olib tashlash va kamera almashinuvini belgilash

Asosiy qoida: pauza kesilgan har bir nuqtada kamera ALBATTA almashadi —
shunda jump-cut rakurs o'zgarishi ostida yashirinadi.
"""
import argparse, json, sys


# --- 1. tanlov -------------------------------------------------------------

def tanla(speech, tanlov):
    """Nutq bo'laklarini tanlangan oraliqlar bilan kesishtiradi."""
    out = []
    for t in tanlov:
        ts, te = t["start"], t["end"]
        muh = t.get("muhimlik", 3)
        izoh = t.get("izoh", "")
        for s, e in speech:
            a, b = max(s, ts), min(e, te)
            if b - a > 0.15:
                out.append({"s": a, "e": b, "muhimlik": muh, "izoh": izoh})
    out.sort(key=lambda x: x["s"])
    return out


# --- 2. siqish -------------------------------------------------------------

def sigdir(bolaklar, maqsad, keep):
    """Maqsadli davomiylikka sig'maguncha eng past muhimlikdagini tashlaydi."""
    def jami(bs):
        if not bs:
            return 0.0
        t = sum(b["e"] - b["s"] for b in bs)
        # qoladigan nafaslar ham vaqt oladi
        return t + keep * max(0, len(bs) - 1)

    tashlandi = []
    while bolaklar and jami(bolaklar) > maqsad:
        # eng past muhimlik, ular ichida eng uzuni (ko'proq vaqt bo'shatadi)
        n = min(bolaklar, key=lambda b: (b["muhimlik"], -(b["e"] - b["s"])))
        bolaklar = [b for b in bolaklar if b is not n]
        tashlandi.append(n)
    return bolaklar, tashlandi, jami(bolaklar)


# --- 3. ritm ---------------------------------------------------------------

def birlashtir(speech, keep):
    """Qisqa pauzalarni (<= keep) bo'lak ichiga qo'shib yuboradi.

    Shunda chiqishda ular saqlanadi — tabiiy nafas bo'lib qoladi,
    va har qolgan chegara haqiqiy kesim bo'ladi.
    """
    out = []
    for s, e in speech:
        if out and s - out[-1][1] <= keep:
            out[-1][1] = e
        else:
            out.append([s, e])
    return out


def plan(speech, params):
    """Nutq bo'laklaridan kesim rejasini yig'adi."""
    keep = params["pauza_qoldiq"]
    speech = birlashtir(speech, keep)
    min_shot = params["shot_min"]
    max_shot = params["shot_max"]
    hook_until = params["hook_s"]
    hook_shot = params["hook_shot"]

    clips, cam, shot_len, out_t = [], 0, 0.0, 0.0

    for i, (s, e) in enumerate(speech):
        if i > 0:
            # Bu yerda albatta pauza kesilgan (qisqalari birlashtirilgan),
            # demak kamera ALBATTA almashishi shart.
            cam ^= 1
            shot_len = 0.0

        seg_s, seg_e = s, e
        while seg_e - seg_s > 1e-3:
            limit = hook_shot if out_t < hook_until else max_shot
            room = max(min_shot, limit - shot_len)
            take = min(seg_e - seg_s, room)
            if (seg_e - seg_s) - take < min_shot:
                take = seg_e - seg_s

            clips.append([round(seg_s, 3), round(seg_s + take, 3), cam])
            seg_s += take
            out_t += take
            shot_len += take

            if shot_len >= limit - 1e-3 and seg_e - seg_s > 1e-3:
                cam ^= 1
                shot_len = 0.0

    return clips, out_t


def merge(clips):
    """Qo'shni, bir kameradagi, uzluksiz bo'laklarni birlashtiradi."""
    out = []
    for s, e, c in clips:
        if out and out[-1][2] == c and abs(out[-1][1] - s) < 1e-3:
            out[-1][1] = e
        else:
            out.append([s, e, c])
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("speech_json", help="speech.py chiqishi (asosiy kamera)")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--tanlov", help="JSON: [{start,end,muhimlik,izoh}] — "
                                    "hikoyaning qoladigan bo'laklari")
    p.add_argument("--maqsad", type=float,
                   help="maksimal davomiylik (s); oshsa past muhimlik kesiladi")
    p.add_argument("--offset-b", type=float, default=0.0)
    p.add_argument("--pauza-qoldiq", type=float, default=0.18)
    p.add_argument("--shot-min", type=float, default=0.7)
    p.add_argument("--shot-max", type=float, default=5.6)
    p.add_argument("--hook-s", type=float, default=3.0)
    p.add_argument("--hook-shot", type=float, default=1.6)
    a = p.parse_args()

    sp = json.load(open(a.speech_json))
    speech = sp["nutq"]
    if not speech:
        print("XATO: nutq topilmadi", file=sys.stderr)
        return 1

    tashlandi = []
    if a.tanlov:
        bolaklar = tanla(speech, json.load(open(a.tanlov)))
        if not bolaklar:
            print("XATO: tanlov hech qaysi nutq bo'lagiga tushmadi",
                  file=sys.stderr)
            return 1
        if a.maqsad:
            bolaklar, tashlandi, _ = sigdir(bolaklar, a.maqsad, a.pauza_qoldiq)
        speech = [[b["s"], b["e"]] for b in bolaklar]

    params = {k: getattr(a, k) for k in
              ("pauza_qoldiq", "shot_min", "shot_max", "hook_s", "hook_shot")}
    clips, out_dur = plan(speech, params)
    clips = merge(clips)

    if a.maqsad and out_dur > a.maqsad + 0.5:
        print(f"OGOHLANTIRISH: {out_dur:.1f}s — maqsaddan "
              f"{out_dur - a.maqsad:.1f}s ortiq", file=sys.stderr)

    cuts = sum(1 for i in range(1, len(clips)) if clips[i][2] != clips[i - 1][2])
    edl = {
        "manba_davomiyligi": sp["davomiylik"],
        "chiqish_davomiyligi": round(out_dur, 2),
        "maqsad": a.maqsad,
        "offset_b": a.offset_b,
        "kamera_almashinuvi": cuts,
        "ortacha_shot_s": round(out_dur / max(1, cuts + 1), 2),
        "tashlangan_bolaklar": [
            {"start": round(t["s"], 2), "end": round(t["e"], 2),
             "muhimlik": t["muhimlik"], "izoh": t["izoh"]} for t in tashlandi],
        "kliplar": clips,
    }
    open(a.out, "w").write(json.dumps(edl, ensure_ascii=False, indent=2))

    print(f"{a.out}: {len(clips)} klip, {cuts} ta kamera almashinuvi, "
          f"{edl['chiqish_davomiyligi']}s, o'rtacha kadr "
          f"{edl['ortacha_shot_s']}s")
    if tashlandi:
        print(f"  sig'dirish uchun {len(tashlandi)} bo'lak tashlandi:")
        for t in tashlandi:
            print(f"    {t['s']:6.2f}-{t['e']:6.2f}  "
                  f"muhimlik {t['muhimlik']}  {t['izoh']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
