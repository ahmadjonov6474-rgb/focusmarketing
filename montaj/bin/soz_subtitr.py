#!/usr/bin/env python3
"""Referens-2 uslubidagi subtitr: so'zma-so'z, katta harf, chapda.

Referensda to'liq gap emas, 1-2 ta SO'Z chiqadi: katta harfli, qalin,
pushti-oq rangda, kadrning chap-o'rta qismida (x=230, y=1238 @1080x1920).
Shuning uchun bu yerda qator emas, so'z guruhlari yasaladi.

Kirish: soz_vaqt.py bergan qatorlar (manba vaqtida).
Chiqish: ASS (hali ham manba vaqtida) — subs.py uni chiqish vaqtiga ko'chiradi.
"""
import argparse, importlib.util, json, os, sys


def _subs():
    """subs.py dagi EDL bo'yicha vaqt ko'chirish mantig'ini qayta ishlatamiz."""
    yol = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subs.py")
    spec = importlib.util.spec_from_file_location("subs", yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def guruhla(cues, max_belgi):
    """Qatorlarni 1-2 so'zli guruhlarga bo'ladi, vaqtni belgi bo'yicha taqsimlaydi."""
    out = []
    for c in cues:
        sozlar = c["text"].split()
        if not sozlar:
            continue
        guruh, cur = [], []
        for w in sozlar:
            cur.append(w)
            if len(" ".join(cur)) >= max_belgi or len(cur) >= 2:
                guruh.append(cur)
                cur = []
        if cur:
            if guruh and len(cur) == 1 and len(" ".join(guruh[-1] + cur)) <= max_belgi + 4:
                guruh[-1] += cur
            else:
                guruh.append(cur)

        uz = [len(" ".join(g)) + 1 for g in guruh]
        jami = sum(uz)
        t = c["start"]
        dur = c["end"] - c["start"]
        for g, u in zip(guruh, uz):
            d = dur * u / jami
            out.append({"start": round(t, 3), "end": round(t + d, 3),
                        "text": " ".join(g)})
            t += d
    return out


def ass(cues, W, H, kegl, x, y, rang):
    """Uslub maydonlari tartibi (chalkashish oson):
    ... BorderStyle=1, Outline=0, Shadow=4, Alignment=7 (tepa-chap),
    MarginL=x, MarginR=60, MarginV=y (tepadan masofa).
    Alignment 7 bo'lgani uchun MarginV TEPADAN o'lchanadi."""
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Soz,Inter,{kegl},{rang},{rang},&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,0,4,7,{x},60,{y},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    # har qator kichikroq va shaffofroq holatdan "pop" bo'lib chiqadi
    anim = (r"{\fscx86\fscy86\alpha&H60&"
            r"\t(0,110,\fscx100\fscy100\alpha&H00&)}")
    satrlar = [f"Dialogue: 0,{ts(c['start'])},{ts(c['end'])},Soz,,0,0,0,,"
               f"{anim}{c['text'].upper()}" for c in cues]
    return head + "\n".join(satrlar) + "\n"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cues", help="soz_vaqt.py chiqishi")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--max-belgi", type=int, default=14)
    p.add_argument("--kegl", type=int, default=51)
    p.add_argument("--x", type=int, default=230)
    p.add_argument("--y", type=int, default=1238)
    p.add_argument("--rang", default="&H00DADAF7")   # ASS = BGR: #F7DADA
    p.add_argument("--w", type=int, default=1080)
    p.add_argument("--h", type=int, default=1920)
    p.add_argument("--edl", help="edl.py chiqishi — vaqtlar chiqish vaqtiga ko'chiriladi")
    a = p.parse_args()

    cues = json.load(open(a.cues))
    g = guruhla(cues, a.max_belgi)
    if a.edl:
        sm = _subs()
        xar = sm.xarita(json.load(open(a.edl)))
        oldin = len(g)
        g = sm.qayta_vaqtla(g, xar)
        print(f"EDL bo'yicha ko'chirildi: {oldin} -> {len(g)} "
              f"(kesilgan qismga tushganlari olib tashlandi)")
    json.dump(g, open(a.out.replace(".ass", ".json"), "w"),
              ensure_ascii=False, indent=1)
    open(a.out, "w").write(ass(g, a.w, a.h, a.kegl, a.x, a.y, a.rang))
    qisqa = sum(1 for c in g if c["end"] - c["start"] < 0.25)
    print(f"{a.out}: {len(g)} so'z guruhi "
          f"({qisqa} tasi 0.25 s dan qisqa)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
