"""Chạy MỘT LẦN trên máy bạn để lấy refresh token của kênh TikTok ATS FISHING.

Cách chạy:  python scripts/get_token.py
Cần:        pip install requests
"""
import getpass
import secrets
import urllib.parse
import webbrowser

import requests

client_key = input("Client key: ").strip()
client_secret = getpass.getpass("Client secret (gõ không hiện): ").strip()
redirect_uri = input("Redirect URI (đúng như đã khai trong app TikTok): ").strip()

state = secrets.token_urlsafe(12)
url = "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode({
    "client_key": client_key,
    "scope": "user.info.basic,video.publish",
    "response_type": "code",
    "redirect_uri": redirect_uri,
    "state": state,
})
print("\nĐang mở trình duyệt. Hãy đăng nhập đúng kênh ATS FISHING rồi bấm cho phép.")
print("Nếu trình duyệt không tự mở, mở link này:\n" + url + "\n")
webbrowser.open(url)

print("Sau khi cho phép, trình duyệt chuyển sang một trang (có thể báo lỗi, không sao).")
back = input("Dán TOÀN BỘ địa chỉ trang đó vào đây: ").strip()
params = urllib.parse.parse_qs(urllib.parse.urlparse(back).query)
if params.get("state", [""])[0] != state:
    raise SystemExit("State không khớp, hủy để an toàn. Chạy lại script.")
code = params.get("code", [""])[0]
if not code:
    raise SystemExit("Không thấy 'code' trong địa chỉ. Chạy lại script.")

r = requests.post(
    "https://open.tiktokapis.com/v2/oauth/token/",
    data={
        "client_key": client_key,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=60,
).json()

if "refresh_token" not in r:
    raise SystemExit(f"Lỗi: {r.get('error')} - {r.get('error_description')}")

print("\nThành công. Lưu giá trị dưới đây vào GitHub Secrets (TIKTOK_REFRESH_TOKEN).")
print("KHÔNG gửi qua chat hay dán vào code.\n")
print("TIKTOK_REFRESH_TOKEN =", r["refresh_token"])
print("open_id =", r.get("open_id"))
