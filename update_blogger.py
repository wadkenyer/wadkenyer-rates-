import json, re, os, sys
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

AR_MONTHS = ["يناير","فبراير","مارس","أبريل","مايو","يونيو",
             "يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"]

def to_arabic(iso):  # "2026-09-24" -> "24 سبتمبر 2026"
    y, m, d = iso.split("-")
    return f"{int(d)} {AR_MONTHS[int(m)-1]} {y}"

# 1) قراءة البيانات الجديدة
with open("data.json", encoding="utf-8") as f:
    data = json.load(f)
rate     = data["usd_to_sdg"]
date_iso = data["last_updated"]          # "2026-09-24"
date_ar  = to_arabic(date_iso)

# 2) المصادقة مع Google
creds = Credentials(
    token=None,
    refresh_token=os.environ["BLOGGER_REFRESH_TOKEN"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.environ["BLOGGER_CLIENT_ID"],
    client_secret=os.environ["BLOGGER_CLIENT_SECRET"],
)
creds.refresh(Request())
service = build("blogger", "v3", credentials=creds)
blog_id = os.environ["BLOGGER_BLOG_ID"]
page_id = os.environ["BLOGGER_PAGE_ID"]

# 3) سحب HTML الصفحة الحالي
page = service.pages().get(blogId=blog_id, pageId=page_id).execute()
html = page["content"]

# 4) الاستبدالات الأربعة (مع فشل صريح إن لم تجد النمط)
subs = [
    (r"FALLBACK_RATE\s*=\s*[\d.]+",        f"FALLBACK_RATE = {rate}"),
    (r'FALLBACK_DATE\s*=\s*"[^"]+"',       f'FALLBACK_DATE = "{date_ar}"'),
    (r'(<span id="update">)[^<]*(</span>)', rf"\g<1>{date_ar}\g<2>"),
    (r'"dateModified":\s*"[^"]+"',         f'"dateModified": "{date_iso}"'),
]
for pattern, repl in subs:
    new_html, n = re.subn(pattern, repl, html)
    if n == 0:
        sys.exit(f"❌ لم أجد النمط: {pattern} — هل عدّلت الكود يدويًا؟")
    html = new_html

# 5) الرفع
service.pages().update(blogId=blog_id, pageId=page_id, body={"content": html}).execute()
print(f"✅ تم مزامنة Blogger: السعر {rate} بتاريخ {date_ar}")
