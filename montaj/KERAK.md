# Nima kerak — har safar qaytarmaslik uchun

Bu ro'yxat 2026-10-17 dagi montaj ishidan chiqdi: nima meni to'xtatgan
bo'lsa, o'sha yozildi. Tartib — ta'siri bo'yicha.

| # | Kerak | Qanday beriladi | Nimani ochadi |
|---|---|---|---|
| 1 | **Gemini kaliti** | `aistudio.google.com` → kalit → environment → `GEMINI_API_KEY` | Transkript avtomatik. Whisper o'zbekchani eplamaydi (turbo ham, large-v3 ham sinaldi) |
| 2 | **Musiqa kutubxonasi** | Drive papkasi: 10-15 litsenziyali trek | Musiqa + ducking + beat sync (`master.sh` da tayyor) |
| 3 | **B-roll banki** | Har mijoz uchun Drive papkasi: 20-30 klip | Tez montajda kadrlarning yarmi B-roll bo'ladi |
| 4 | **Shriftlar** | `fonts.gstatic.com`, `fonts.googleapis.com` ochilsin, yoki fayllar repoga | Kondensli qalin shrift (Oswald/Anton/Bebas) |
| 5 | **Zaxira ASR domenlari** | `us.aws.cdn.hf.co`, `cas-server.xethub.hf.co` | HF modellari (Gemini ishlamay qolsa) |
| 6 | **Referens kutubxonasi** | Yoqqan 5-10 video bitta papkada | Bitta uslub tizimi quriladi, har safar taxmin qilinmaydi |
| 7 | **Brend kit** | Logo, aniq ranglar, shriftlar, shablonlar | Hozir rang Instagram skrinshotidan o'lchab olindi (#0E9550) |
| 8 | **Qaysi referens asosiy** | Bitta javob | Ritm, grafika zichligi, uslub — hammasi shundan |

## Nega 8-band eng muhim

Bitta ishda uchta referens berildi va ritmi keskin farq qildi:

| Referens | Kadrlar | O'rtacha kadr |
|---|---|---|
| referens-1 (kurs sotuvi) | — | 2.4 s |
| referens-2 (storytelling) | 5 / 43 s | **8.6 s** |
| referens-3 (podcast) | 23 / 32.4 s | **1.41 s** |

Birinchi montaj referens-2 ga qurildi (7.6 s kadr) va "jonsiz" chiqdi,
chunki kutilgani referens-3 ning ritmi edi — 5 barobar tez. Uslub
oldindan qotirilmasa, har safar shu takrorlanadi.

## Hech qanday sharoit tuzatmaydigani

Men videoni real vaqtda ko'rmayman va eshitmayman — kadrlarni va
ovoz to'lqinini o'lchayman. Shuning uchun eng tez sikl:

1. Men o'lchab quraman (referensni ham o'lchayman, taxmin qilmayman)
2. Siz ko'rib **aniq** aytasiz: "kesim tezroq", "chaqnash yumshoq"
3. Men uni raqamga aylantirib tuzataman

Shu yo'l bilan "dabdala" dan "kesim 7.6 s emas, 1.6 s bo'lishi kerak"
ga yetib kelindi.
