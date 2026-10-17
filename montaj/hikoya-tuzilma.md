# 1 daqiqalik bemor keysi — tuzilma

Storytelling: shifokor o'zi ko'rgan eng og'ir holatni so'zlab beradi.
Maqsadli davomiylik — **maksimum 60 s**.

**Ikkita referens bor va ular bir xil emas:**

| | Referens-1 (kurs sotuvi) | Referens-2 (storytelling) |
|---|---|---|
| Kadr o'rtacha | 2.4 s | **8.6 s** |
| Kesim | ko'p, tez | kam, nafas oladi |
| Grafika | sotuv blokiari, narx stikeri | hikoyani ko'rsatadigan kartalar |

Bizning janr — **storytelling**, shuning uchun ritm **referens-2** dan olinadi
(`style/tokens-ref2.json`). Referens-1 dan faqat **dizayn tokenlari** qoladi
(`style/tokens.json`: to'q ko'k palitra, pill subtitr) — ular bizning kechki,
sovuq ko'k materialimizga mos tushadi. Referens-2 ning issiq jigarrang
interyer ranglari esa ko'chirilmaydi.

**Hech qaysi referens nusxa ko'chirilmaydi.** Ulardan faqat o'lchov olinadi,
montaj esa shu videodagi hikoyaga qarab quriladi.

## Beat tuzilmasi

| # | Beat | Vaqt | Kadr uzunligi | Vazifasi |
|---|---|---|---|---|
| 1 | **Hook** | 0–6 s | 5–7 s | Eng kuchli jumla, kirish so'zisiz. Bitta uzun kadr — gap bo'linmaydi |
| 2 | **Kontekst** | 6–18 s | 5–7 s | Kim, qachon, qanday kelgan |
| 3 | **Og'irlashuv** | 18–34 s | 6–8 s | Qanchalik jiddiy edi, nima xavf ostida edi |
| 4 | **Burilish** | 34–46 s | 6–8 s | Qanday qaror qabul qilindi |
| 5 | **Natija** | 46–56 s | 6–9 s | Oqibat — eng kuchli nuqta, eng sekin ritm |
| 6 | **Xulosa** | 56–60 s | 4 s | Tomoshabin uchun xulosa |

Ritm mantig'i (referens-2 dan): kadr uzun, kesim faqat **kerak bo'lganda** —
ya'ni uzun pauza yoki tashlangan bo'lak joyida. Har kesimda kamera almashadi,
shuning uchun sakrash ko'rinmaydi.

### `edl.py` uchun storytelling presetlari

```bash
--pauza-qoldiq 0.50   # 0.5 s gacha pauza SAQLANADI (nafas) -> kesim kam
--shot-min     2.00
--shot-max     9.00   # uzun kadrga ruxsat (referens-2: 11.4 s gacha)
--hook-s       0      # boshida tez montaj zonasi YO'Q
```

Eski (referens-1) tez presetlari: `--pauza-qoldiq 0.18 --shot-max 5.6
--hook-s 3 --hook-shot 1.6` — sotuv/reklama kreativi uchun qoladi.

## Muhimlik darajalari (`tanlov.json` uchun)

| Daraja | Nima |
|---|---|
| 5 | Hook, burilish nuqtasi, natija — **hech qachon kesilmaydi** |
| 4 | Keysni tushunish uchun zarur kontekst |
| 3 | Tafsilot — joy bo'lsa qoladi |
| 2 | Takror yoki qo'shimcha izoh |
| 1 | Chekinish, "eee", mavzudan chetga chiqish — birinchi bo'lib ketadi |

`edl.py --maqsad 60` berilganda eng past darajadan boshlab tashlanadi,
60 soniyaga sig'maguncha.

## Grafikalar rejasi

Referens dizayn tizimida (`style/tokens.json`), lekin janrga mos:

| Beat | Grafika |
|---|---|
| Hook | Faqat subtitr pill — e'tibor gapda bo'lsin |
| Kontekst | Vaqt chizig'i chipi ("1-kun", "2-hafta") |
| Og'irlashuv | Holat kartasi yoki raqam callout (ko'rsatkich, muddat) |
| Burilish | Qaror kartasi — qisqa matn, to'q panel |
| Natija | "Oldin → Keyin" holat kartasi (matn bilan, fotosiz) |
| Xulosa | Murojaat chipi |

Barcha grafikalar HTML/CSS da yasaladi va Playwright orqali kadrma-kadr
render qilinib, ffmpeg bilan videoga qo'shiladi. `Inter` shrifti o'rnatilgan.

## Tibbiy kontent bo'yicha ehtiyot

- Bemor ismi, aniq sanasi, tanib olinadigan tafsiloti chiqmaydi.
- Natija va'da sifatida emas, aniq keys sifatida beriladi.
- Agar matnda bemorni tanitadigan detal bo'lsa — o'sha bo'lak kesiladi yoki
  subtitrda yumshatiladi; har qanday bunday holat alohida aytiladi.
