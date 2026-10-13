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

DEFAULT_API_VERSION = "v22.0"
GRAPH = "https://graph.facebook.com"


def die(msg):
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


def list_pages(token, api_version):
    """User token orqali boshqariladigan sahifalar va ularning tokenlarini chiqaradi."""
    url = f"{GRAPH}/{api_version}/me/accounts"
    rows = list(paginate(url, {"fields": "id,name,access_token", "limit": 100}, token))
    if not rows:
        die("Hech qanday sahifa topilmadi. User token va pages_show_list ruxsatini tekshiring.")
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
    ap.add_argument("--page-id", help="Sahifa ID (masalan 137827949416647).")
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

    if not args.page_id:
        die("--page-id kerak. Avval --list-pages bilan ro'yxatni ko'ring.")

    cutoff = datetime.now(timezone.utc) - timedelta(days=30 * args.months)
    out_path = args.out or f"messages_{args.page_id}_{args.platform}.json"

    print(f"Sahifa:   {args.page_id}")
    print(f"Inbox:    {args.platform}")
    print(f"Davr:     {cutoff.date()} dan bugungacha ({args.months} oy)")
    print(f"Natija:   {out_path}\n")

    conv_url = f"{GRAPH}/{args.api_version}/{args.page_id}/conversations"
    conv_params = {
        "platform": args.platform,
        "fields": "id,updated_time,message_count,participants,unread_count",
        "limit": 50,
    }

    conversations = []
    total_messages = 0

    for i, conv in enumerate(paginate(conv_url, conv_params, args.token), 1):
        updated = conv.get("updated_time")
        if updated:
            try:
                ts = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            except ValueError:
                ts = None
            if ts and ts < cutoff:
                # Suhbatlar yangilanish vaqti bo'yicha tartiblangan - keyingilari ham eski
                break

        msgs = fetch_messages(conv["id"], args.token, args.api_version,
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
        print(f"  [{i}] {conv['id'][:24]}... -> {len(msgs)} xabar "
              f"(jami {total_messages})", flush=True)

    result = {
        "page_id": args.page_id,
        "platform": args.platform,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "period_from": cutoff.isoformat(),
        "conversation_count": len(conversations),
        "message_count": total_messages,
        "conversations": conversations,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    print(f"\nTayyor: {len(conversations)} suhbat, {total_messages} xabar")
    print(f"Fayl:   {os.path.abspath(out_path)}")
    if not conversations:
        print("\nOgohlantirish: hech qanday suhbat topilmadi. Sabablari:")
        print("  - Bu sahifada Messenger yozishmalari yo'q")
        print("  - Token'da pages_messaging ruxsati yo'q")
        print("  - --platform instagram ni sinab ko'ring")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTo'xtatildi.", file=sys.stderr)
        sys.exit(130)
