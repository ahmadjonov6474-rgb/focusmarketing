#!/usr/bin/env python3
"""Subtitrlarni manba vaqtidan chiqish vaqtiga ko'chiradi va ASS fayl yasaydi.

Muhim: transkript manba videodagi vaqtlarda bo'ladi. Montajdan keyin
vaqtlar siljiydi, shuning uchun EDL orqali qayta hisoblanadi.
Uslub referensdan olingan: to'yingan ko'k pill, oq qalin matn.
"""
import argparse, json, sys

# Ikki uslub bor:
#   pill — referens-1 (kurs sotuvi): to'yingan ko'k pill ostida oq matn
#   soya — referens-2 (storytelling): qalin oq matn + qattiq soya, fonsiz.
#          To'q, kechki kadrda tinchroq ko'rinadi va yuzni yopmaydi.
USLUBLAR = {
    "pill": {"kegl": 58, "fon": "&H00A43904", "border": 3, "outline": 14,
             "shadow": 0},
    "soya": {"kegl": 66, "fon": "&H00000000", "border": 1, "outline": 5,
             "shadow": 3},
}
STYLE = {
    "matn": "&H00FFFFFF",
    "pastdan": 420,            # 1920 balandlikda pastdan masofa (UI zonasidan tepada)
}


def xarita(edl):
    """[(manba_boshi, manba_oxiri, chiqish_boshi)] ro'yxatini quradi."""
    out, t = [], 0.0
    for s, e, _cam in edl["kliplar"]:
        out.append((s, e, t))
        t += e - s
    return out


def kochir(t, xar):
    """Manba vaqtini chiqish vaqtiga aylantiradi (kesilgan bo'lsa None)."""
    for s, e, o in xar:
        if s - 1e-6 <= t <= e + 1e-6:
            return o + (t - s)
    return None


def qayta_vaqtla(cues, xar):
    """Kesim chegarasidan o'tib ketgan subtitrni bo'lib yuboradi."""
    res = []
    for c in cues:
        for s, e, o in xar:
            a, b = max(c["start"], s), min(c["end"], e)
            if b - a < 0.08:
                continue
            res.append({"start": o + (a - s), "end": o + (b - s),
                        "text": c["text"]})
    res.sort(key=lambda x: x["start"])
    # bir xil matn qo'shni bo'laklarga bo'lingan bo'lsa — birlashtir
    merged = []
    for c in res:
        if (merged and merged[-1]["text"] == c["text"]
                and c["start"] - merged[-1]["end"] < 0.12):
            merged[-1]["end"] = c["end"]
        else:
            merged.append(c)
    # ustma-ust tushgan subtitrlar ekranda bir-birining ustiga chiqmasin
    for i in range(len(merged) - 1):
        if merged[i]["end"] > merged[i + 1]["start"]:
            merged[i]["end"] = merged[i + 1]["start"] - 0.02
    return [c for c in merged if c["end"] - c["start"] > 0.08]


def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60)
    s = t % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def ass(cues, W, H, uslub="soya", pastdan=None):
    u = USLUBLAR[uslub]
    y = pastdan if pastdan is not None else STYLE["pastdan"]
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Pill,Inter,{u['kegl']},{STYLE['matn']},{STYLE['matn']},{u['fon']},{u['fon']},-1,0,0,0,100,100,0,0,{u['border']},{u['outline']},{u['shadow']},2,90,90,{y},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [f"Dialogue: 0,{ts(c['start'])},{ts(c['end'])},Pill,,0,0,0,,"
             f"{c['text'].strip()}" for c in cues]
    return head + "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("transcript", help="JSON: [{start,end,text}] manba vaqtida")
    p.add_argument("edl")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--w", type=int, default=1080)
    p.add_argument("--h", type=int, default=1920)
    p.add_argument("--uslub", choices=sorted(USLUBLAR), default="soya")
    p.add_argument("--pastdan", type=int)
    a = p.parse_args()

    cues = json.load(open(a.transcript))
    edl = json.load(open(a.edl))
    xar = xarita(edl)
    out = qayta_vaqtla(cues, xar)
    open(a.out, "w").write(ass(out, a.w, a.h, a.uslub, a.pastdan))
    yoq = len(cues) - len({c["text"] for c in out})
    print(f"{a.out}: {len(out)} subtitr "
          f"({yoq} ta kesilgan qismga tushib qoldi)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
