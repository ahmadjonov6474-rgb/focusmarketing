#!/usr/bin/env python3
"""Grafika qatlamini KADRMA-KADR render qiladi (haqiqiy motion grafika).

Oldingi yondashuv — bir nechta tayyor PNG ni almashtirish — animatsiya
emas edi. Bu yerda har kadr uchun `style/grafika.html?t=<sekund>` ochiladi
va u o'sha lahzadagi holatni JS da hisoblab chizadi: spring easing,
stagger, maska bilan ochiluvchi band, chaqnash o'tishi.

Motion blur: kadrlar ikki barobar tez (50 fps) render qilinib, keyin
juft-juft o'rtachalanadi — tez harakat tabiiy xiralashadi.
"""
import argparse, json, os, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

CHROME = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"
W, H = 1080, 1920


def oraliq(sen, fps, blur_x, chet=0.4):
    """Grafika ko'rinadigan kadrlar ro'yxati (bo'sh joylar render qilinmaydi)."""
    kadrlar = set()
    for e in sen:
        a = max(0.0, e["start"] - chet)
        b = e["end"] + chet
        for i in range(int(a * fps * blur_x), int(b * fps * blur_x) + 1):
            kadrlar.add(i)
    return sorted(kadrlar)


def render(args):
    html, i, fps_eff, papka = args
    t = i / fps_eff
    out = os.path.join(papka, f"g{i:06d}.png")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    "--hide-scrollbars", "--force-device-scale-factor=1",
                    "--default-background-color=00000000",
                    f"--window-size={W},{H}", "--virtual-time-budget=220",
                    f"--screenshot={out}", f"file://{html}?t={t:.4f}"],
                   check=True, capture_output=True)
    return i


def main():
    p = argparse.ArgumentParser()
    p.add_argument("senariy")
    p.add_argument("-o", "--out", required=True, help="PNG papkasi")
    p.add_argument("--html", default="style/grafika.html")
    p.add_argument("--tokens", default="style/tokens-ref2-dizayn.json")
    p.add_argument("--fps", type=int, default=25)
    p.add_argument("--blur", type=int, default=2,
                   help="motion blur uchun necha barobar tez render qilish")
    p.add_argument("--ishchi", type=int, default=4)
    a = p.parse_args()

    sen = json.load(open(a.senariy))
    tok = json.load(open(a.tokens))["rang"]
    shablon = open(a.html).read()

    # senariy va ranglarni sahifaga joylaymiz
    css = (f":root{{--brend-yorqin:{tok['brend_yorqin']};--brend:{tok['brend']};"
           f"--brend-toq:{tok['brend_toq']};--tog1:{tok['tog_1']};"
           f"--tog2:{tok['tog_2']}}}")
    doc = shablon.replace("<style>", f"<style>{css}", 1).replace(
        "window.__SENARIY__", json.dumps(sen, ensure_ascii=False))
    f = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False)
    f.write(doc); f.close()

    os.makedirs(a.out, exist_ok=True)
    fps_eff = a.fps * a.blur
    kadrlar = oraliq(sen, a.fps, a.blur)
    print(f"{len(kadrlar)} kadr ({fps_eff} fps), {a.ishchi} ishchi...")

    done = 0
    with ThreadPoolExecutor(max_workers=a.ishchi) as ex:
        for _ in ex.map(render, [(f.name, i, fps_eff, a.out) for i in kadrlar]):
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(kadrlar)}", flush=True)
    os.unlink(f.name)

    meta = {"fps": a.fps, "blur": a.blur, "fps_eff": fps_eff,
            "birinchi": kadrlar[0], "oxirgi": kadrlar[-1], "soni": len(kadrlar)}
    json.dump(meta, open(os.path.join(a.out, "meta.json"), "w"), indent=1)
    print(f"\n{len(kadrlar)} kadr -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
