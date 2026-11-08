# Tự động đăng TikTok – kênh ATS FISHING

Mỗi ngày lúc **19:00 (giờ Việt Nam)** GitHub tự đăng 1 video trong `videos.json` lên TikTok.

## Thêm video
Mở `videos.json` trên GitHub, bấm biểu tượng bút chì, thêm một mục mới ở cuối:

```json
{ "url": "https://link-tai-truc-tiep/video.mp4", "caption": "Tiêu đề #hashtag", "posted": false }
```

- `url` dùng được các loại link sau:
  - **Google Drive**: chuột phải file → Chia sẻ → đặt "Bất kỳ ai có đường liên kết" → Sao chép đường liên kết, dán thẳng vào.
  - **Dropbox**: Chia sẻ → Tạo liên kết, dán thẳng vào.
  - Link tải trực tiếp file .mp4 từ nơi khác.
  - Không dùng link YouTube, TikTok hay Facebook (không tải được).
- Video nên là .mp4 (H.264), dọc 9:16, dưới khoảng 500 MB.
- Video được đăng theo thứ tự, mục nào `"posted": false` đầu tiên sẽ được đăng.

## Cài đặt một lần
1. Tạo app trên developers.tiktok.com, thêm **Content Posting API**, khai **Redirect URI**, lấy Client key và Client secret.
2. Chạy `python scripts/get_token.py` trên máy bạn, đăng nhập kênh ATS FISHING, lấy `TIKTOK_REFRESH_TOKEN`.
3. Trong repo: Settings → Secrets and variables → Actions → New repository secret. Tạo 3 secret:
   - `TIKTOK_CLIENT_KEY`
   - `TIKTOK_CLIENT_SECRET`
   - `TIKTOK_REFRESH_TOKEN`
4. Tab Actions → "Dang TikTok ATS FISHING" → Run workflow để thử.

## Lưu ý
- Khi app **chưa được TikTok duyệt**, video chỉ đăng ở chế độ riêng tư (`SELF_ONLY`). Sau khi duyệt, đổi `TIKTOK_PRIVACY` trong `.github/workflows/post.yml` thành `PUBLIC_TO_EVERYONE`.
- Đổi giờ đăng: sửa dòng `cron` trong `post.yml` (giờ UTC, Việt Nam = UTC+7).
- Không bao giờ dán Client secret hay token vào code hoặc chat.
