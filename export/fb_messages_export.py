#!/usr/bin/env python3
"""Facebook Page / Instagram xabarlarini Graph API orqali JSON faylga yuklab olish.

Faqat standart kutubxonalar ishlatiladi - `pip install` kerak emas.

Misollar:
    # 1-qadam: qaysi sahifalar bor va ularning tokenlarini ko'rish
    python3 fb_messages_export.py --list-pages --token "USER_TOKEN"

    # 2-qadam: sahifa xabarlarini yuklab olish (oxirgi 6 oy)
    python3 fb_messages_export.py --page-id 137827949416647 --token "PAGE_TOKEN"
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

DEFAULT_API_VERSION = "v26.0"
GRAPH = "https://graph.facebook.com"


# Sahifa tokenini aniqlashga urinayotganda xatolar ekranga chiqmasligi kerak
_quiet = False


def die(msg):
    if not _quiet:
        print(f"\nXATO: {msg}", file=sys.stderr)
    sys.exit(1)


def get(url, params=None, retries=4):
    """Graph API GET so'rovi. Rate limit va vaqtinchalik xatolarda qayta uriniladi."""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    delay = 2
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            try:
                err = json.loads(raw).get("error", {})
            except json.JSONDecodeError:
                err = {"message": raw[:500]}
            code = err.get("code")
            # 4 = app rate limit, 17 = user rate limit, 613 = calls exceeded, 1/2 = temporary
            if code in (1, 2, 4, 17, 613) and attempt < retries:
                print(f"  ... limitga yetildi, {delay}s kutilmoqda", flush=True)
                time.sleep(delay)
                delay *= 2
                continue
            die(
                f"Graph API rad etdi (HTTP {e.code}, code={code}):\n"
                f"  {err.get('message', raw[:500])}\n\n"
                "Ko'p uchraydigan sabablar:\n"
                "  - Token muddati tugagan -> Graph API Explorer'dan yangisini oling\n"
                "  - pages_messaging ruxsati yo'q\n"
                "  - Page token emas, User token ishlatilgan (--list-pages bilan tekshiring)"
            )
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < retries:
                time.sleep(delay)
                delay *= 2
                continue
            die(f"Tarmoqqa ulanib bo'lmadi: {e}")


def paginate(url, params, token, limit_pages=None):
    """Graph API sahifalanishini oxirigacha aylanib chiqadi."""
    params = dict(params, access_token=token)
    page = 0
    while url:
        data = get(url, params)
        params = None  # keyingi URL'da parametrlar allaqachon bor
        for item in data.get("data", []):
            yield item
        page += 1
        if limit_pages and page >= limit_pages:
            return
        url = data.get("paging", {}).get("next")


def fetch_pages(token, api_version, required=True):
    """User token orqali boshqariladigan sahifalarni (id, nom, token) qaytaradi."""
    global _quiet
    url = f"{GRAPH}/{api_version}/me/accounts"
    _quiet = not required
    try:
        rows = list(paginate(url, {"fields": "id,name,access_token", "limit": 100}, token))
    except SystemExit:
        if required:
            raise
        return []  # Page token berilgan - sahifalar ro'yxatini olib bo'lmaydi, muammo emas
    finally:
        _quiet = False
    if not rows and required:
        die("Hech qanday sahifa topilmadi. User token va pages_show_list ruxsatini tekshiring.")
    return rows


def list_pages(token, api_version):
    """Sahifalar va ularning tokenlarini ekranga chiqaradi."""
    rows = fetch_pages(token, api_version)
    print(f"\n{len(rows)} ta sahifa topildi:\n")
    for p in rows:
        print(f"  Nomi:  {p.get('name')}")
        print(f"  ID:    {p.get('id')}")
        print(f"  Token: {p.get('access_token', '(yo_q)')}")
        print()
    print("Kerakli sahifaning ID va Token'ini olib, keyingi buyruqda ishlating.")


def fetch_messages(conv_id, token, api_version, cutoff, max_messages):
    """Bitta suhbatning xabarlarini yig'adi. Xabarlar yangidan eskiga qarab keladi."""
    url = f"{GRAPH}/{api_version}/{conv_id}/messages"
    fields = "id,created_time,from,to,message,attachments{mime_type,name}"
    out = []
    for msg in paginate(url, {"fields": fields, "limit": 100}, token):
        created = msg.get("created_time")
        if created:
            try:
                ts = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except ValueError:
                ts = None
            if ts and ts < cutoff:
                # Eski xabarlarga yetdik - bu suhbatni to'xtatamiz
                break
        out.append(msg)
        if len(out) >= max_messages:
            break
    out.reverse()  # eskidan yangiga - o'qishga qulay
    return out


def export_page(page_id, token, args, cutoff, out_path, page_name=None):
    """Bitta sahifaning suhbatlarini yig'ib, JSON faylga yozadi."""
    if page_name is None:
        print(f"Sahifa:   {page_id}")
    print(f"Inbox:    {args.platform}")
    print(f"Davr:     {cutoff.date()} dan bugungacha ({args.months} oy)")

    conv_url = f"{GRAPH}/{args.api_version}/{page_id}/conversations"
    conv_params = {
        "platform": args.platform,
        "fields": "id,updated_time,message_count,participants,unread_count",
        "limit": 50,
    }

    conversations = []
    total_messages = 0

    for i, conv in enumerate(paginate(conv_url, conv_params, token), 1):
        updated = conv.get("updated_time")
        if updated:
            try:
                ts = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            except ValueError:
                ts = None
            if ts and ts < cutoff:
                # Suhbatlar yangilanish vaqti bo'yicha tartiblangan - keyingilari ham eski
                break

        msgs = fetch_messages(conv["id"], token, args.api_version,
                              cutoff, args.max_messages)
        if not msgs:
            continue

        conversations.append({
            "conversation_id": conv["id"],
            "updated_time": updated,
            "message_count_total": conv.get("message_count"),
            "unread_count": conv.get("unread_count"),
            "participants": conv.get("participants", {}).get("data", []),
            "messages": msgs,
        })
        total_messages += len(msgs)
        print(f"  [{i}] {len(msgs)} xabar (jami {total_messages})", flush=True)

    result = {
        "page_id": page_id,
        "page_name": page_name,
        "platform": args.platform,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "period_from": cutoff.isoformat(),
        "conversation_count": len(conversations),
        "message_count": total_messages,
        "conversations": conversations,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    print(f"  -> {len(conversations)} suhbat, {total_messages} xabar | {out_path}")
    return result


def main():
    ap = argparse.ArgumentParser(
        description="Facebook Page / Instagram xabarlarini JSON faylga yuklab oladi.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--token", default=os.environ.get("FB_TOKEN"),
                    help="Access token. Yoki FB_TOKEN muhit o'zgaruvchisiga yozing.")
    ap.add_argument("--list-pages", action="store_true",
                    help="User token orqali sahifalar ro'yxati va ularning tokenlarini chiqarish.")
    ap.add_argument("--page-id",
                    help="Sahifa ID. Bir nechtasini vergul bilan ajrating: ID1,ID2,ID3")
    ap.add_argument("--all-pages", action="store_true",
                    help="Barcha sahifalarni ketma-ket yuklaydi (User token kerak).")
    ap.add_argument("--platform", default="messenger", choices=["messenger", "instagram"],
                    help="Qaysi inbox. Default: messenger.")
    ap.add_argument("--months", type=int, default=6, help="Necha oylik tarix. Default: 6.")
    ap.add_argument("--max-messages", type=int, default=2000,
                    help="Bitta suhbatdan maksimal xabar soni. Default: 2000.")
    ap.add_argument("--api-version", default=DEFAULT_API_VERSION,
                    help=f"Graph API versiyasi. Default: {DEFAULT_API_VERSION}.")
    ap.add_argument("--out", help="Natija fayli. Default: messages_<page-id>_<platform>.json")
    args = ap.parse_args()

    if not args.token:
        die("Token berilmagan. --token \"...\" yoki FB_TOKEN muhit o'zgaruvchisini ishlating.")

    if args.list_pages:
        list_pages(args.token, args.api_version)
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=30 * args.months)

    if args.all_pages:
        pages = fetch_pages(args.token, args.api_version)
        print(f"\n{len(pages)} ta sahifa topildi. Hammasi ketma-ket yuklanadi.\n")
        done = []
        for n, page in enumerate(pages, 1):
            name = page.get("name", "?")
            page_token = page.get("access_token")
            print(f"\n{'=' * 60}\n[{n}/{len(pages)}] {name}  (ID {page['id']})")
            if not page_token:
                print("  Tashlab ketildi: bu sahifa uchun token berilmadi")
                continue
            out_path = f"messages_{page['id']}_{args.platform}.json"
            res = export_page(page["id"], page_token, args, cutoff, out_path, name)
            done.append((name, res["conversation_count"], res["message_count"], out_path))

        print(f"\n{'=' * 60}\nYAKUNIY NATIJA\n")
        for name, convs, msgs, path in done:
            print(f"  {name}: {convs} suhbat, {msgs} xabar -> {path}")
        total = sum(m for _, _, m, _ in done)
        print(f"\nJami {len(done)} sahifa, {total} xabar.")
        if total == 0:
            print("\nHech qayerda xabar topilmadi. pages_messaging ruxsatini tekshiring.")
        return

    if not args.page_id:
        die("--page-id yoki --all-pages kerak. Avval --list-pages bilan ro'yxatni ko'ring.")

    ids = [x.strip() for x in args.page_id.split(",") if x.strip()]

    # User token berilgan bo'lsa, har sahifaning o'z tokenini topib olamiz
    known = {p["id"]: p for p in fetch_pages(args.token, args.api_version, required=False)}

    results = []
    for n, pid in enumerate(ids, 1):
        page = known.get(pid)
        name = page.get("name") if page else None
        token = page.get("access_token") if page else args.token
        if len(ids) > 1:
            print(f"\n{'=' * 60}\n[{n}/{len(ids)}] {name or pid}  (ID {pid})")
        elif name:
            print(f"Sahifa:   {name} (ID {pid})")
        out_path = args.out if (args.out and len(ids) == 1) \
            else f"messages_{pid}_{args.platform}.json"
        results.append(export_page(pid, token, args, cutoff, out_path, name))

    if len(ids) > 1:
        print(f"\n{'=' * 60}\nYAKUNIY NATIJA\n")
        for r in results:
            print(f"  {r['page_name'] or r['page_id']}: "
                  f"{r['conversation_count']} suhbat, {r['message_count']} xabar")

    if sum(r["message_count"] for r in results) == 0:
        print("\nOgohlantirish: hech qanday xabar topilmadi. Sabablari:")
        print("  - Bu sahifalarda Messenger yozishmalari yo'q")
        print("  - Token'da pages_messaging ruxsati yo'q")
        print("  - --platform instagram ni sinab ko'ring")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTo'xtatildi.", file=sys.stderr)
        sys.exit(130)
