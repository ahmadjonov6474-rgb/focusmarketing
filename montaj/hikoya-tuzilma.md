# 1 daqiqalik bemor keysi — tuzilma

Storytelling: shifokor o'zi ko'rgan eng og'ir holatni so'zlab beradi.
Maqsadli davomiylik — **maksimum 60 s**.

Referens ritmi shu janrga moslandi. Referensning *grafikalari* ko'chirilmaydi
(u kurs sotuvi edi — Inson/AI ustunlari, agentlar diagrammasi, $250 narx
stikeri bu yerga to'g'ri kelmaydi). Ko'chiriladigani — **dizayn tizimi**
(ranglar, shrift, pill subtitr, karta uslubi) va **kesim ritmi**.

## Beat tuzilmasi

| # | Beat | Vaqt | Kadr uzunligi | Vazifasi |
|---|---|---|---|---|
| 1 | **Hook** | 0–4 s | 1.4–1.8 s | Eng shok detal: bemor qanday holatda kelgani. Bitta jumla, hech qanday kirish so'zisiz |
| 2 | **Kontekst** | 4–12 s | 2.5–3 s | Kim, qachon, qanday kelgan |
| 3 | **Og'irlashuv** | 12–28 s | 3–4 s | Qanchalik jiddiy edi, nima xavf ostida edi |
| 4 | **Burilish** | 28–42 s | 3–4 s | Qanday qaror qabul qilindi, nima qilindi |
| 5 | **Natija** | 42–54 s | 4–5 s | Oqibat — eng kuchli emotsional nuqta, sekinroq ritm |
| 6 | **Xulosa** | 54–60 s | 2–3 s | Tomoshabin uchun xulosa yoki murojaat |

Ritm mantig'i: boshi tez (diqqatni ushlash), o'rtasi barqaror,
natija sekin (gap singib ulgursin), yakuni qisqa.

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
