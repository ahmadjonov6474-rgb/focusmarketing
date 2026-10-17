#!/usr/bin/env python3
"""Nutqni Gemini orqali matnga aylantiradi (o'zbek tili uchun).

Nega: Whisper (turbo ham, large-v3 ham) o'zbekchani eplamaydi — matn
o'qib bo'lmaydigan darajada buziladi. Gemini o'zbek tilini ancha yaxshi
biladi, shuning uchun transkript shundan olinadi.

Kalit: GEMINI_API_KEY muhit o'zgaruvchisidan o'qiladi (chatga yozilmaydi).

Vaqtlar `speech.py` topgan nutq bo'laklaridan olinadi — ya'ni aniq qoladi,
modeldan faqat MATN so'raladi. Shunda vaqt xatosi bo'lmaydi.

Chiqish: [{"start":s,"end":s,"text":"..."}] — manba video vaqtida.
"""
import argparse, base64, json, os, subprocess, sys, time, urllib.error, urllib.request

BASE = "https://generativelanguage.googleapis.com/v1beta"


def api(path, key, payload=None, tries=4):
    url = f"{BASE}/{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    for i in range(tries):
        req = urllib.request.Request(
            url, data=data,
            headers={"x-goog-api-key": key, "Content-Type": "application/json"},
            method="POST" if data else "GET")
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:400]
            if e.code in (429, 500, 503) and i < tries - 1:
                time.sleep(2 ** (i + 1))
                continue
            raise SystemExit(f"XATO {e.code}: {body}")
        except urllib.error.URLError as e:
            if i < tries - 1:
                time.sleep(2 ** (i + 1))
                continue
            raise SystemExit(f"XATO: {e}")


def modellar(key):
    ms = api("models", key).get("models", [])
    return [m["name"].split("/")[-1] for m in ms
            if "generateContent" in m.get("supportedGenerationMethods", [])]


def wav(media, s, e, out):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{s:.3f}",
                    "-i", media, "-t", f"{e - s:.3f}", "-map", "a:0",
                    "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", out],
                   check=True)
    return out


KORSATMA = """Bu o'zbek tilidagi intervyu audiosi (shifokor gapiryapti).

Audioni SO'ZMA-SO'Z yozib ber. Qoidalar:
- Faqat o'zbek lotin alifbosida yoz (turkcha yoki boshqa imlo ishlatma).
- Faqat eshitilgan so'zlarni yoz, hech narsa qo'shma va tushirib qoldirma.
- Tinish belgilarini qo'y.
- Agar biror joy tushunarsiz bo'lsa, o'sha joyga [?] qo'y.
- Javobda faqat matnning o'zi bo'lsin, boshqa hech narsa yozma."""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("media")
    p.add_argument("speech_json", help="speech.py chiqishi")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--model", default="gemini-2.5-pro")
    p.add_argument("--kontekst", default="",
                   help="mavzu bo'yicha qo'shimcha izoh (atamalar aniqroq chiqadi)")
    p.add_argument("--modellar", action="store_true",
                   help="mavjud modellarni ko'rsatib chiqish")
    a = p.parse_args()

    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise SystemExit("XATO: GEMINI_API_KEY muhit o'zgaruvchisi yo'q")

    if a.modellar:
        for m in modellar(key):
            print(m)
        return 0

    sp = json.load(open(a.speech_json))["nutq"]
    korsatma = KORSATMA + (f"\n\nMavzu bo'yicha izoh: {a.kontekst}"
                           if a.kontekst else "")
    tmp = "/tmp/_gem_chunk.wav"
    out = []
    for i, (s, e) in enumerate(sp, 1):
        wav(a.media, s, e, tmp)
        b64 = base64.b64encode(open(tmp, "rb").read()).decode()
        r = api(f"models/{a.model}:generateContent", key, {
            "contents": [{"parts": [
                {"text": korsatma},
                {"inline_data": {"mime_type": "audio/wav", "data": b64}}]}],
            "generationConfig": {"temperature": 0.0}})
        try:
            txt = r["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError):
            txt = ""
        if txt:
            out.append({"start": s, "end": e, "text": txt})
        print(f"[{i:3d}/{len(sp)}] {s:7.2f}-{e:7.2f}  {txt}", flush=True)

    json.dump(out, open(a.out, "w"), ensure_ascii=False, indent=2)
    print(f"\n{a.out}: {len(out)} bo'lak / {len(sp)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
