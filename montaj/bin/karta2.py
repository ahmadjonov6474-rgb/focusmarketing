#!/usr/bin/env python3
"""Referens-2 dizaynidagi grafikalar: to'liq ekran karta, chip va hook sarlavha.

Referensdan o'lchangan (style/tokens-ref2-dizayn.json): qizil radial fon,
yupqa setka, pastda tog' siluetlari, qalin KURSIV bosh harfli matn, oq band,
dumaloq ikonkali chip.

Har element BOSQICHMA-BOSQICH chiqadi (referensda ham shunday): bitta
element uchun bir nechta PNG holati render qilinadi, qoplama ularni
ketma-ket ko'rsatadi — shunda matn "yozilib borayotgandek" bo'ladi.

Ishlatish:
  bin/karta2.py work/senariy.json -o work/grafika
"""
import argparse, html, json, os, shutil, subprocess, sys, tempfile

CHROME = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"
CHROME_ALT = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
W, H = 1080, 1920


def chrome():
    for c in (CHROME, CHROME_ALT, shutil.which("chromium")):
        if c and os.path.exists(c):
            return c
    raise SystemExit("XATO: Chromium topilmadi")


BOSH = """<!doctype html><meta charset="utf-8">
<style>
  @font-face {{ font-family:'InterI'; src:local('Inter'); }}
  :root {{
    --brend-yorqin:{brend_yorqin}; --brend:{brend}; --brend-toq:{brend_toq};
    --tog1:{tog_1}; --tog2:{tog_2}; --oq:{oq}; --ikkilamchi:{ikkilamchi};
    --amber:{amber};
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html,body {{ width:{W}px; height:{H}px; overflow:hidden; }}
  body {{ font-family:'Inter',sans-serif; color:var(--oq); background:{fon}; }}

  /* --- brend rangidagi karta foni --- */
  .karta {{ position:absolute; inset:0;
    background:
      radial-gradient(ellipse 72% 46% at 50% 32%,
        var(--brend-yorqin) 0%, var(--brend) 46%, var(--brend-toq) 100%);
  }}
  .setka {{ position:absolute; inset:0;
    background-image:
      repeating-linear-gradient(0deg, {setka} 0 1px, transparent 1px 135px),
      repeating-linear-gradient(90deg, {setka} 0 1px, transparent 1px 135px);
  }}
  .tog {{ position:absolute; left:0; right:0; bottom:0; }}
  .tog svg {{ display:block; width:100%; }}

  /* --- karta matnlari --- */
  .ust {{ position:absolute; left:0; right:0; top:{karta_ust_y}px;
    text-align:center; font-size:{karta_ust}px; font-weight:500;
    font-style:italic; letter-spacing:.01em;
    text-shadow:0 3px 14px rgba(0,0,0,.45); }}
  .band {{ position:absolute; left:0; top:{karta_band_y}px; height:138px;
    background:var(--oq); display:flex; align-items:center;
    justify-content:center; overflow:hidden;
    box-shadow:0 14px 44px rgba(0,0,0,.42); }}
  .band span {{ color:var(--brend); font-size:{karta_band}px; font-weight:900;
    font-style:italic; text-transform:uppercase; letter-spacing:-.01em;
    white-space:nowrap; padding:0 46px; }}
  .chiplar {{ position:absolute; left:0; right:0; top:{chiplar_y}px;
    display:flex; flex-direction:column; align-items:center; gap:18px; }}
  .kchip {{ background:rgba(0,0,0,.26); border:2px solid rgba(255,255,255,.3);
    border-radius:999px; padding:12px 30px; font-size:34px; font-weight:500;
    font-style:italic; }}
  .quote {{ position:absolute; left:60px; right:60px; top:{quote_y}px;
    text-align:center; font-size:{karta_quote}px; font-weight:900;
    font-style:italic; line-height:1.08;
    text-shadow:0 5px 20px rgba(0,0,0,.5); }}

  /* --- video ustidagi chip --- */
  .chip {{ position:absolute; left:{chip_chet}px; right:{chip_chet}px;
    top:{chip_y}px; min-height:{chip_balandlik}px;
    border-radius:{chip_radius}px; display:flex; align-items:center;
    gap:34px; padding:26px 38px;
    background:linear-gradient(152deg, var(--brend-yorqin), var(--brend) 72%);
    border:3px solid rgba(255,255,255,.85);
    box-shadow:0 20px 56px rgba(0,0,0,.55); }}
  .ikon {{ flex:0 0 120px; height:120px; border-radius:999px;
    background:rgba(255,255,255,.18); display:flex; align-items:center;
    justify-content:center; }}
  .ikon svg {{ width:62px; height:62px; fill:#fff; }}
  .chip .matn {{ flex:1; min-width:0; }}
  .chip .katta {{ font-size:{chip_katta}px; font-weight:900; font-style:italic;
    text-transform:uppercase; line-height:1.0; letter-spacing:-.01em; }}
  .chip .kichik {{ font-size:{chip_kichik}px; font-weight:500;
    font-style:italic; color:rgba(255,255,255,.93); margin-top:10px; }}

  /* --- hook sarlavha --- */
  .hook {{ position:absolute; left:{hook_x}px; top:{hook_y}px; right:80px;
    font-size:{hook_kegl}px; font-weight:900; font-style:italic;
    text-transform:uppercase; line-height:1.12; letter-spacing:-.005em;
    text-shadow:0 6px 26px rgba(0,0,0,.8), 0 2px 6px rgba(0,0,0,.9); }}
</style>
<body>{tana}</body>
"""

TOG = """<div class="tog"><svg viewBox="0 0 1080 300" preserveAspectRatio="none" height="300">
  <path d="M0,300 L0,210 L150,110 L260,215 L390,120 L520,230 L650,130 L790,225 L920,125 L1080,235 L1080,300 Z" fill="{tog1}"/>
  <path d="M0,300 L0,255 L120,195 L250,265 L380,205 L520,275 L660,210 L800,268 L940,200 L1080,262 L1080,300 Z" fill="{tog2}"/>
</svg></div>"""

IKONLAR = {
    "odam": '<svg viewBox="0 0 24 24"><path d="M12 12a5 5 0 100-10 5 5 0 000 10zm0 2c-5 0-9 2.5-9 5.5V22h18v-2.5c0-3-4-5.5-9-5.5z"/></svg>',
    "kalendar": '<svg viewBox="0 0 24 24"><path d="M7 2v2H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V6a2 2 0 00-2-2h-2V2h-2v2H9V2H7zm12 8v10H5V10h14z"/></svg>',
    "yurak": '<svg viewBox="0 0 24 24"><path d="M12 21s-7.5-4.9-9.5-9A5.5 5.5 0 0112 5.6 5.5 5.5 0 0121.5 12c-2 4.1-9.5 9-9.5 9z"/></svg>',
    "ogoh": '<svg viewBox="0 0 24 24"><path d="M12 2L1 21h22L12 2zm1 14h-2v2h2v-2zm0-7h-2v5h2V9z"/></svg>',
    "plus": '<svg viewBox="0 0 24 24"><path d="M19 11h-6V5h-2v6H5v2h6v6h2v-6h6z"/></svg>',
}


def tana_karta(e, holat, r_tog1="#04301E", r_tog2="#021B11"):
    """holat: 0 = faqat fon+ust, 1 = band ochilmoqda, 2 = to'liq"""
    t = [f'<div class="karta"></div><div class="setka"></div>',
         TOG.format(tog1=r_tog1, tog2=r_tog2)]
    if e.get("ust"):
        t.append(f'<div class="ust">{html.escape(e["ust"])}</div>')
    if holat >= 1 and e.get("band"):
        kengligi = "56%" if holat == 1 else "100%"
        t.append(f'<div class="band" style="width:{kengligi}">'
                 f'<span>{html.escape(e["band"])}</span></div>')
    if holat >= 2:
        for c in e.get("chiplar", []):
            pass
        if e.get("chiplar"):
            ch = "".join(f'<div class="kchip">{html.escape(c)}</div>'
                         for c in e["chiplar"])
            t.append(f'<div class="chiplar">{ch}</div>')
        if e.get("quote"):
            t.append(f'<div class="quote">{html.escape(e["quote"])}</div>')
    return "".join(t)


def tana_chip(e, holat):
    """holat: 0 = faqat katta matn, 1 = kichik matn ham"""
    ik = IKONLAR.get(e.get("ikon", "odam"), IKONLAR["odam"])
    kichik = (f'<div class="kichik">{html.escape(e["kichik"])}</div>'
              if holat >= 1 and e.get("kichik") else "")
    return (f'<div class="chip"><div class="ikon">{ik}</div>'
            f'<div class="matn"><div class="katta">'
            f'{html.escape(e["katta"])}</div>{kichik}</div></div>')


def tana_hook(e, holat):
    sozlar = e["matn"].split()
    n = len(sozlar) if holat >= 1 else max(1, len(sozlar) // 2)
    bosh = " ".join(sozlar[:n])
    return f'<div class="hook">{html.escape(bosh)}</div>'


def render(doc, out, shaffof, bc):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(doc)
        src = f.name
    cmd = [bc, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
           "--force-device-scale-factor=1", f"--window-size={W},{H}",
           f"--screenshot={out}"]
    if shaffof:
        cmd.append("--default-background-color=00000000")
    cmd.append("file://" + src)
    subprocess.run(cmd, check=True, capture_output=True)
    os.unlink(src)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("senariy")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--tokens", default="style/tokens-ref2-dizayn.json")
    a = p.parse_args()

    tok = json.load(open(a.tokens))
    r, o, j = tok["rang"], tok["olcham_1080"], tok["joylashuv_1080"]
    sen = json.load(open(a.senariy))
    os.makedirs(a.out, exist_ok=True)
    bc = chrome()

    reja = []
    for i, e in enumerate(sen, 1):
        tur = e["tur"]
        shaffof = tur in ("chip", "hook")
        if tur == "karta":
            holatlar, f = [0, 1, 2], tana_karta
        elif tur == "chip":
            holatlar, f = ([0, 1] if e.get("kichik") else [0]), tana_chip
        else:
            holatlar, f = ([0, 1] if len(e["matn"].split()) > 1 else [0]), tana_hook

        n = len(holatlar)
        uz = (e["end"] - e["start"]) / n
        for k, hol in enumerate(holatlar):
            fayl = os.path.join(a.out, f"{i:02d}{chr(97+k)}_{tur}.png")
            doc = BOSH.format(
                W=W, H=H, tana=f(e, hol),
                fon="transparent" if shaffof else r["brend_toq"],
                **{k2: v for k2, v in r.items() if not k2.startswith("_")},
                chiplar_y=j["karta_band_y"] + 180,
                quote_y=j["karta_band_y"] + 420, **o, **j)
            render(doc, fayl, shaffof, bc)
            reja.append({"png": fayl, "tur": tur,
                         "start": round(e["start"] + k * uz, 2),
                         "end": round(e["end"] if k == n - 1
                                      else e["start"] + (k + 1) * uz, 2),
                         "animatsiya": e.get("animatsiya", "")})
            print(f"  {fayl}  {reja[-1]['start']:6.2f}-{reja[-1]['end']:6.2f}")

    json.dump(reja, open(os.path.join(a.out, "reja.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"\n{len(reja)} holat -> {a.out}/reja.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
