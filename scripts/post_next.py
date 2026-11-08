"""Đăng video tiếp theo trong videos.json lên TikTok (Content Posting API, FILE_UPLOAD)."""
import json
import os
import subprocess
import sys
import tempfile
import time

import requests

API = "https://open.tiktokapis.com"
QUEUE = os.path.join(os.path.dirname(__file__), "..", "videos.json")
CHUNK = 10 * 1024 * 1024  # 10 MB (TikTok cho phép 5-64 MB mỗi phần)


def die(msg):
    print(f"LỖI: {msg}")
    sys.exit(1)


def env(name, default=None):
    v = os.environ.get(name, default)
    if v is None or v == "":
        die(f"Thiếu biến môi trường / secret: {name}")
    return v


def refresh_access_token():
    old_rt = env("TIKTOK_REFRESH_TOKEN")
    r = requests.post(
        f"{API}/v2/oauth/token/",
        data={
            "client_key": env("TIKTOK_CLIENT_KEY"),
            "client_secret": env("TIKTOK_CLIENT_SECRET"),
            "grant_type": "refresh_token",
            "refresh_token": old_rt,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=60,
    )
    d = r.json()
    if "access_token" not in d:
        die(f"Không lấy được access token: {d.get('error')} - {d.get('error_description')}")
    new_rt = d.get("refresh_token")
    if new_rt and new_rt != old_rt:
        pat = os.environ.get("GH_PAT")
        repo = os.environ.get("GITHUB_REPOSITORY")
        if pat and repo:
            subprocess.run(
                ["gh", "secret", "set", "TIKTOK_REFRESH_TOKEN", "--repo", repo],
                input=new_rt, text=True, check=True, env={**os.environ, "GH_TOKEN": pat},
            )
            print("Đã cập nhật secret TIKTOK_REFRESH_TOKEN (token mới).")
        else:
            print("CẢNH BÁO: TikTok trả refresh token mới nhưng chưa có GH_PAT để tự lưu. "
                  "Nếu lần sau báo lỗi token, hãy chạy lại scripts/get_token.py.")
    return d["access_token"]


def pick_privacy(token):
    r = requests.post(
        f"{API}/v2/post/publish/creator_info/query/",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"},
        timeout=60,
    )
    d = r.json()
    if d.get("error", {}).get("code") != "ok":
        die(f"Không lấy được thông tin kênh: {d}")
    options = d["data"].get("privacy_level_options", [])
    want = os.environ.get("TIKTOK_PRIVACY", "SELF_ONLY")
    if want not in options:
        print(f"Chế độ {want} chưa dùng được (app chưa duyệt?). Chọn trong: {options}")
        want = "SELF_ONLY" if "SELF_ONLY" in options else options[0]
    print(f"Chế độ đăng: {want} | kênh: {d['data'].get('creator_username')}")
    return want


def download(url, path):
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for part in r.iter_content(1024 * 1024):
                f.write(part)
    return os.path.getsize(path)


def upload(token, path, size, caption, privacy):
    if size <= CHUNK:
        chunk_size, total = size, 1
    else:
        chunk_size, total = CHUNK, size // CHUNK  # phần cuối gồm cả phần dư
    body = {
        "post_info": {
            "title": caption[:2200],
            "privacy_level": privacy,
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": size,
            "chunk_size": chunk_size,
            "total_chunk_count": total,
        },
    }
    r = requests.post(
        f"{API}/v2/post/publish/video/init/",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"},
        json=body, timeout=60,
    )
    d = r.json()
    if d.get("error", {}).get("code") != "ok":
        die(f"Khởi tạo đăng thất bại: {d.get('error')}")
    publish_id = d["data"]["publish_id"]
    upload_url = d["data"]["upload_url"]

    with open(path, "rb") as f:
        for i in range(total):
            start = i * chunk_size
            end = size - 1 if i == total - 1 else start + chunk_size - 1
            data = f.read(end - start + 1)
            rr = requests.put(
                upload_url, data=data, timeout=300,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Length": str(len(data)),
                    "Content-Range": f"bytes {start}-{end}/{size}",
                },
            )
            if rr.status_code not in (200, 201, 206):
                die(f"Tải phần {i + 1}/{total} lỗi: {rr.status_code} {rr.text[:200]}")
    return publish_id


def wait_status(token, publish_id):
    for _ in range(40):
        r = requests.post(
            f"{API}/v2/post/publish/status/fetch/",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"},
            json={"publish_id": publish_id}, timeout=60,
        )
        data = r.json().get("data", {})
        status = data.get("status")
        print("Trạng thái:", status)
        if status == "PUBLISH_COMPLETE":
            return True
        if status == "FAILED":
            die(f"TikTok báo thất bại: {data.get('fail_reason')}")
        time.sleep(8)
    print("Hết thời gian chờ, video có thể vẫn đang được xử lý.")
    return True


def main():
    with open(QUEUE, encoding="utf-8") as f:
        queue = json.load(f)
    item = next((v for v in queue if not v.get("posted")), None)
    if item is None:
        print("Hết video trong videos.json. Hãy thêm link mới.")
        return
    print("Sẽ đăng:", item["url"])

    token = refresh_access_token()
    privacy = pick_privacy(token)
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "video.mp4")
        size = download(item["url"], path)
        print(f"Đã tải video {size / 1024 / 1024:.1f} MB")
        publish_id = upload(token, path, size, item.get("caption", ""), privacy)
    wait_status(token, publish_id)

    item["posted"] = True
    item["publish_id"] = publish_id
    with open(QUEUE, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("Xong.")


if __name__ == "__main__":
    main()
