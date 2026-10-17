#!/usr/bin/env python3
"""Grafika kartalarini HTML/CSS dan PNG qilib render qiladi (headless Chromium).

Referens-2 da kesim o'rnida grafika ishlaydi: hikoyaning kalit nuqtasida
to'liq ekran karta chiqadi. Bu yerda ikki tur:

  karta  — to'liq ekran: kichik ustki izoh + katta kalit so'z
  hook   — shaffof fonli ustki sarlavha (video ustiga qo'yiladi)

Ranglar `style/tokens.json` dan (bizning kechki, sovuq ko'k materialga mos).

Ishlatish:
  bin/karta.py work/kartalar.json -o work/kartalar
  # kartalar.json: [{"tur":"karta","ust":"...","asos":"...","tag":"natija"}]
"""
import argparse, html, json, os, shutil, subprocess, sys, tempfile

CHROME = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"
CHROME_ALT = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"


def chrome():
    for c in (CHROME, CHROME_ALT, shutil.which("chromium"), shutil.which("google-chrome")):
        if c and os.path.exists(c):
            return c
    raise SystemExit("XATO: Chromium topilmadi")


SAHIFA = """<!doctype html><meta charset="utf-8">
<style>
  :root {{
    --fon:   {fon};
    --panel: {panel};
    --akcent:{akcent};
    --amber: {amber};
    --matn:  {matn};
    --kul:   {kul};
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html,body {{ width:{w}px; height:{h}px; }}
  body {{
    font-family:'Inter',sans-serif; color:var(--matn);
    background:{bg};
    display:flex; align-items:center; justify-content:center;
    padding:0 96px; text-align:center;
  }}
  .ust {{
    font-size:46px; font-weight:500; color:var(--amber);
    letter-spacing:.02em; margin-bottom:34px; line-height:1.35;
  }}
  .asos {{
    font-size:{kegl}px; font-weight:800; line-height:1.06;
    letter-spacing:-.01em; text-transform:uppercase;
  }}
  .tag {{
    display:inline-block; margin-bottom:46px; padding:14px 30px;
    border:2px solid var(--akcent); border-radius:999px;
    font-size:34px; font-weight:600; letter-spacing:.18em;
    text-transform:uppercase; color:var(--amber);
  }}
  .hook {{
    position:absolute; top:150px; left:0; right:0; padding:0 70px;
    font-size:84px; font-weight:800; line-height:1.08;
    text-transform:uppercase; letter-spacing:-.01em;
    text-shadow:0 6px 28px rgba(0,0,0,.85), 0 2px 6px rgba(0,0,0,.9);
  }}
  .hook .kichik {{ display:block; font-size:54px; font-weight:600; color:var(--amber); }}
</style>
<body>{tana}</body>
"""


def tana(k):
    if k["tur"] == "hook":
        kichik = (f'<span class="kichik">{html.escape(k["ust"])}</span>'
                  if k.get("ust") else "")
        return f'<div class="hook">{kichik}{html.escape(k["asos"])}</div>'
    tag = f'<div class="tag">{html.escape(k["tag"])}</div>' if k.get("tag") else ""
    ust = f'<div class="ust">{html.escape(k["ust"])}</div>' if k.get("ust") else ""
    return f'<div>{tag}{ust}<div class="asos">{html.escape(k["asos"])}</div></div>'


def render(k, tok, w, h, out, bin_chrome):
    c = tok["rang"]
    bg = ("transparent" if k["tur"] == "hook" else
          f'radial-gradient(120% 90% at 50% 18%, {c["panel"]} 0%, {c["fon_eng_toq"]} 72%)')
    n = len(k["asos"])
    kegl = 150 if n <= 14 else 122 if n <= 26 else 96 if n <= 44 else 78
    doc = SAHIFA.format(w=w, h=h, bg=bg, kegl=kegl, tana=tana(k),
                        fon=c["fon_eng_toq"], panel=c["panel"], akcent=c["akcent"],
                        amber=c["amber"], matn=c["matn"], kul=c["matn_kulrang"])
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(doc)
        src = f.name
    cmd = [bin_chrome, "--headless", "--disable-gpu", "--no-sandbox",
           "--hide-scrollbars", "--force-device-scale-factor=1",
           f"--window-size={w},{h}", f"--screenshot={out}"]
    if k["tur"] == "hook":
        cmd.append("--default-background-color=00000000")
    cmd.append("file://" + src)
    subprocess.run(cmd, check=True, capture_output=True)
    os.unlink(src)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kartalar", help="JSON: [{tur,ust,asos,tag}]")
    p.add_argument("-o", "--out", required=True, help="chiqish papkasi")
    p.add_argument("--tokens", default="style/tokens.json")
    p.add_argument("--w", type=int, default=1080)
    p.add_argument("--h", type=int, default=1920)
    a = p.parse_args()

    tok = json.load(open(a.tokens))
    ks = json.load(open(a.kartalar))
    os.makedirs(a.out, exist_ok=True)
    bc = chrome()
    for i, k in enumerate(ks, 1):
        f = os.path.join(a.out, f"{i:02d}_{k['tur']}.png")
        render(k, tok, a.w, a.h, f, bc)
        print(f"{f}  <- {k['asos'][:48]}")
    print(f"\n{len(ks)} karta -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
