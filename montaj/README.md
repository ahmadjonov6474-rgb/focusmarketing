# Montaj pipeline

Ikki kamerada olingan storytelling videoni avtomatik montaj qiladi:
sinxronlash → pauzalarni kesish → kamera almashinuvi → subtitr → ovoz masteringi.

Uslub `ba3d9f80-referende.mp4` referensidan o'lchab olingan (`style/tokens.json`).

## Asosiy g'oya

Har safar pauza kesilganda kamera **albatta** almashadi. Shunda jump-cut
ko'rinmaydi — sakrash rakurs o'zgarishi ostida yashirinadi. Ovoz esa doim
bitta manbadan olinadi, shuning uchun tembr sakramaydi.

## Ishlatish

```bash
cd montaj

# 0. Kamera burilishi va mezzanine (bir marta)
#    Sony XAVC rotatsiya metadatasini yozmaydi: material yonboshlatib
#    olingan bo'lsa kadr 90° burilgan chiqadi. `burilish` shuni to'g'rilaydi.
#    Mezzanine = burilgan + 1080x1920 ga keltirilgan nusxa; keyingi barcha
#    kesimlar 4K o'rniga shundan yig'iladi, ya'ni ancha tez.
ffmpeg -i work/camA.mp4 -vf "transpose=2,scale=-2:1920,crop=1080:1920,setsar=1,fps=25" \
       -c:v libx264 -preset veryfast -crf 14 -c:a pcm_s16le work/mezA.mp4

# 1. Ikki kamerani sinxronlash
bin/sync.py work/camA.mp4 work/camB.mp4
# -> offset_b=4.868  ishonch=10.4   (ishonch < 6 bo'lsa natija shubhali)

# 2. Nutq va pauzalarni ajratish (ovozi yaxshi kameradan)
bin/speech.py work/camA.mp4 -o work/speech.json

# 3. Nutqni matnga aylantirish (hikoyani tanlash uchun)
bin/transkript.py work/camA.mp4 work/speech.json -o work/transcript.json --til uz

# 4. Kesim rejasi — storytelling presetida (referens-2 ritmi)
bin/edl.py work/speech.json -o work/edl.json --offset-b 4.868 \
           --tanlov work/tanlov.json --maqsad 60 \
           --pauza-qoldiq 0.50 --shot-min 2.0 --shot-max 9.0 --hook-s 0

# 5. Yig'ish
bin/build.py work/cams.json work/edl.json -o work/cut.mp4 --preview   # tez ko'rik
bin/build.py work/cams.json work/edl.json -o work/cut.mp4             # to'liq sifat

# 6. Subtitr (transkript manba vaqtida bo'lishi kerak)
bin/subs.py work/transcript.json work/edl.json -o work/subs.ass

# 7. Ovoz masteringi
bin/master.sh work/cut.mp4 work/final.mp4 work/music.mp3
```

### `cams.json`

```json
{
  "kameralar": [
    {"fayl": "work/camA.mp4", "burilish": 2, "x": 0.5, "y": 0.5, "zoom": 1.00, "offset": 0.000},
    {"fayl": "work/camB.mp4", "burilish": 2, "x": 0.5, "y": 0.5, "zoom": 1.00, "offset": 4.868}
  ],
  "ovoz_manbai": 0,
  "w": 1080, "h": 1920, "fps": 25
}
```

- `burilish` — 0 kerak emas, 1 soat yo'nalishi, 2 teskari. Kesishdan OLDIN
  qo'llanadi. Mezzanine ishlatilsa 0 beriladi (burilish allaqachon bajarilgan)
- `x` — 9:16 ga kesishda gorizontal markaz (0 chap, 1 o'ng)
- `y` — vertikal markaz (0 tepa, 1 past); tepada ortiqcha bo'sh joy bo'lsa oshiriladi
- `zoom` — qo'shimcha yaqinlashtirish; ikkinchi kameraga biroz ko'proq
  bersangiz rakurslar farqi kuchayadi
- `offset` — `sync.py` bergan qiymat

### `transcript.json`

```json
[{"start": 0.2, "end": 1.8, "text": "eng og'ir bemor"}]
```

Vaqtlar **manba** videoda. `subs.py` ularni montajdan keyingi vaqtga ko'chiradi
va kesilgan joylarga tushganini tashlab yuboradi.

## Sozlash

`edl.py` kalitlari ritmni boshqaradi (standart qiymatlar referensdan):

| Kalit | Standart | Nima qiladi |
|---|---|---|
| `--pauza-qoldiq` | 0.18 | shu uzunlikdagi pauza saqlanadi (nafas) |
| `--shot-min` | 0.7 | eng qisqa kadr |
| `--shot-max` | 5.6 | shundan uzun kadr majburan bo'linadi |
| `--hook-s` | 3.0 | boshidagi tez montaj zonasi |
| `--hook-shot` | 1.6 | hook zonasida kadr uzunligi |
| `--tanlov` | — | qoladigan bo'laklar (muharrir qarori) |
| `--maqsad` | — | maksimal davomiylik; oshsa past muhimlikdan kesiladi |

### `tanlov.json`

```json
[{"start": 0.0, "end": 4.2, "muhimlik": 5, "izoh": "HOOK"},
 {"start": 4.6, "end": 12.0, "muhimlik": 4, "izoh": "kontekst"}]
```

`muhimlik` 1–5. `--maqsad` ga sig'masa eng pastidan boshlab tashlanadi.
Tuzilma va darajalar izohi — `hikoya-tuzilma.md`.

## Holat

| Bosqich | Holat |
|---|---|
| Sinxronlash | ✅ sinaldi (3.700 s, ishonch 17.8) |
| Nutq/pauza ajratish | ✅ sinaldi (9/9 bo'lak aniq) |
| Kesim + kamera almashinuvi | ✅ sinaldi (A B A B A B A B) |
| Yig'ish | ✅ sinaldi (vaqtlar aniq mos) |
| Subtitr ko'chirish | ✅ sinaldi (kesilganlari tushib qoldi) |
| Ovoz masteringi | ✅ −14.1 LUFS, LRA 1.1 (referens: −14.1 / 1.3) |
| Transkripsiya | ⛔ model yuklab olinmaydi — `huggingface.co` ochilishi kerak |
| Grafikalar (HTML → Playwright) | ⬜ hali qurilmagan |

Pipeline sun'iy ikki-kamera materialida uchdan-uchgacha sinaldi.
