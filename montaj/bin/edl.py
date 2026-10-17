#!/usr/bin/env python3
"""Kesim rejasini (EDL) quradi: pauzalarni olib tashlaydi va kamera almashinuvini belgilaydi.

Asosiy qoida — har safar pauza kesilganda kamera almashadi.
Shunda jump-cut ko'rinmaydi: sakrash rakurs o'zgarishi ostida yashirinadi.
"""
import argparse, json, sys


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
    target = params["shot_ortacha"]
    hook_until = params["hook_s"]
    hook_shot = params["hook_shot"]

    clips = []            # [manba_boshi, manba_oxiri, kamera]
    cam = 0               # 0 = A, 1 = B
    shot_len = 0.0        # joriy kadr uzunligi (chiqish vaqtida)
    out_t = 0.0

    for i, (s, e) in enumerate(speech):
        # oldingi bo'lakdan keyin pauza kesilgan bo'lsa — kamera almashtir
        if i > 0:
            # Bu yerda albatta pauza kesilgan (qisqalari allaqachon
            # birlashtirilgan), demak kamera ALBATTA almashishi shart —
            # aks holda sakrash ko'zga tashlanadi.
            cam ^= 1
            shot_len = 0.0

        seg_s, seg_e = s, e
        while seg_e - seg_s > 1e-3:
            limit = hook_shot if out_t < hook_until else max_shot
            room = max(min_shot, limit - shot_len)
            take = min(seg_e - seg_s, room)

            # juda qisqa quyruq qolmasin — qo'shib yubor
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
    p.add_argument("--offset-b", type=float, default=0.0,
                   help="B kameraning A ga nisbatan siljishi (sync.py)")
    p.add_argument("--pauza-qoldiq", type=float, default=0.18,
                   help="pauzadan qoldiriladigan nafas (s)")
    p.add_argument("--shot-min", type=float, default=0.7)
    p.add_argument("--shot-max", type=float, default=5.6)
    p.add_argument("--shot-ortacha", type=float, default=2.4)
    p.add_argument("--hook-s", type=float, default=3.0,
                   help="boshidagi tez montaj zonasi")
    p.add_argument("--hook-shot", type=float, default=1.6)
    a = p.parse_args()

    sp = json.load(open(a.speech_json))
    speech = sp["nutq"]
    if not speech:
        print("XATO: nutq topilmadi", file=sys.stderr)
        return 1

    params = {k: getattr(a, k.replace("-", "_")) for k in
              ("pauza_qoldiq", "shot_min", "shot_max", "shot_ortacha",
               "hook_s", "hook_shot")}
    clips, out_dur = plan(speech, params)
    clips = merge(clips)

    cuts = sum(1 for i in range(1, len(clips)) if clips[i][2] != clips[i - 1][2])
    edl = {
        "manba_davomiyligi": sp["davomiylik"],
        "chiqish_davomiyligi": round(out_dur, 2),
        "tejaldi_s": round(sp["davomiylik"] - out_dur, 2),
        "offset_b": a.offset_b,
        "kamera_almashinuvi": cuts,
        "ortacha_shot_s": round(out_dur / max(1, cuts + 1), 2),
        "kliplar": clips,
    }
    open(a.out, "w").write(json.dumps(edl, ensure_ascii=False, indent=2))
    print(f"{a.out}: {len(clips)} klip, {cuts} ta kamera almashinuvi, "
          f"{edl['chiqish_davomiyligi']}s "
          f"(manbadan {edl['tejaldi_s']}s kesildi), "
          f"o'rtacha kadr {edl['ortacha_shot_s']}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
