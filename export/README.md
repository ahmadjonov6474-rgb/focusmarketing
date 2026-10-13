# Facebook sahifa xabarlarini yuklab olish

Facebook sahifa (Page) inbox'ida "Скачать информацию" tugmasi yo'q. Xabarlarni
faqat Graph API orqali olish mumkin. Shu skript aynan shuni qiladi.

Instagram'dan farqli: bu yerda **App Review ham, Business Verification ham kerak
emas** — o'z sahifangiz bo'lgani uchun app'ni Development rejimida ishlatish yetarli.

## Kerakli narsalar

- Python 3.8+ (macOS'da oldindan bor; Windows uchun https://python.org dan o'rnatiladi)
- Sahifaga **admin** huquqi bo'lgan Facebook akkaunti
- Internet

Qo'shimcha kutubxona kerak emas — `pip install` qilinmaydi.

## Qadamlar

### 1. Meta app yaratish (bir marta, ~5 daqiqa)

1. https://developers.facebook.com/apps → **Create App**
2. Use case: **Other** → Type: **Business** → nom bering (masalan `Chat Export`)
3. App yaratilgach, boshqa hech narsa sozlash shart emas — Development rejimida qoladi

### 2. Token olish

1. https://developers.facebook.com/tools/explorer ga kiring
2. O'ng yuqorida yangi yaratgan app'ingizni tanlang
3. **User or Page** → `User Token`
4. **Add a Permission** dan quyidagilarni belgilang:
   - `pages_show_list`
   - `pages_messaging`
   - `pages_read_engagement`
5. **Generate Access Token** → ruxsat bering
6. Chiqqan uzun matnni (token) nusxalang

> Bu token ~1-2 soat amal qiladi. Eksport uchun yetarli. Muddati tugasa,
> shu qadamni takrorlab yangisini oling.

### 3. Sahifa tokenini olish

```bash
python3 fb_messages_export.py --list-pages --token "YUQORIDAGI_USER_TOKEN"
```

Sahifalar ro'yxati chiqadi. Kerakligining **ID** va **Token** ini oling.

### 4. Xabarlarni yuklab olish

```bash
python3 fb_messages_export.py --page-id SAHIFA_ID --token "SAHIFA_TOKENI"
```

Natija: `messages_<id>_messenger.json` fayli shu papkada paydo bo'ladi.

## Qo'shimcha imkoniyatlar

```bash
# 12 oylik tarix
python3 fb_messages_export.py --page-id ID --token "..." --months 12

# Instagram inbox (instagram_manage_messages ruxsati kerak)
python3 fb_messages_export.py --page-id ID --token "..." --platform instagram

# Fayl nomini o'zgartirish
python3 fb_messages_export.py --page-id ID --token "..." --out ilyos_fb.json
```

## Tez-tez uchraydigan xatolar

| Xato | Sabab |
|---|---|
| `Token muddati tugagan` | 2-qadamni takrorlab yangi token oling |
| `pages_messaging ruxsati yo'q` | 2-qadamda ruxsatni belgilashni unutgansiz |
| `Hech qanday suhbat topilmadi` | Sahifada Messenger yozishmasi yo'q, yoki Page token emas User token ishlatilgan |
| `(#200)` | Sahifaga admin huquqingiz yo'q |

## Maxfiylik

Chiqadigan fayl **bemorlarning shaxsiy yozishmalarini** o'z ichiga oladi — ismlar,
telefon raqamlari, sog'liq haqidagi ma'lumotlar.

- Faylni ochiq joyga (umumiy papka, Telegram kanali) qo'ymang
- Kerakmas bo'lgach o'chiring
- Tahlilga berishdan oldin ism/telefonni olib tashlash mumkin — so'rang
