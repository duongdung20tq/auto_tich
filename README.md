# auto_tich — Tự động hoàn thành khóa học & nộp chứng chỉ

Bộ script điều khiển **Chrome thật** qua DevTools Protocol (CDP) để tự động hoàn thành khóa học trên **Anthropic Academy (anthropic.skilljar.com)** và **daotao.fpt.com**, chụp chứng chỉ, phục vụ nộp lên elis.fpt.com.

Không chụp màn hình để đọc đề — đọc DOM trực tiếp. Giải quiz bằng cách **khớp nội dung đáp án** (chống xáo trộn), không theo vị trí.

---

## 1. Yêu cầu

- Windows + Python 3 (đã có sẵn trên máy).
- `pip install playwright` — **KHÔNG** cần `playwright install` (nối vào Chrome thật đang chạy, không dùng browser của Playwright).
- Google Chrome.

## 2. Mở Chrome debug

Chrome 136+ chặn cổng debug trên profile mặc định → **bắt buộc dùng profile riêng**.

**Tài khoản 1 (cổng 9222)** — chạy `start_debug_chrome.bat`, hoặc:

```
chrome.exe --remote-debugging-port=9222 --user-data-dir=D:\Du_an_mini\auto_tich\chrome_debug_profile --no-first-run --no-default-browser-check https://anthropic.skilljar.com/
```

**Tài khoản 2 song song (cổng 9223)** — profile khác:

```
chrome.exe --remote-debugging-port=9223 --user-data-dir=D:\Du_an_mini\auto_tich\chrome_debug_profile2 --no-first-run --no-default-browser-check https://anthropic.skilljar.com/
```

Kiểm tra CDP sống: mở `http://127.0.0.1:9222/json/version`. **Luôn dùng `127.0.0.1`, không dùng `localhost`** (máy này phân giải localhost ra IPv6, Playwright nối hỏng).

> Mọi script đọc biến `CDP_URL` (mặc định `http://127.0.0.1:9222`). Chạy cho tài khoản 2: đặt `CDP_URL=http://127.0.0.1:9223` trước lệnh.

Đăng nhập Skilljar (email/mật khẩu, không SSO) **một lần** trong cửa sổ debug — session sống qua các lần restart. elis/daotao dùng SSO FPT → phải login lại + **MFA thủ công** mỗi lần.

## 3. Các script

| File | Nhiệm vụ |
|---|---|
| `sk_worker.py` | Skilljar: enroll + ghé qua mọi bài (bài nội dung tự hoàn thành). |
| `sk_solve.py` | Skilljar: giải quiz có chấm điểm (bank rule theo nội dung) + hoàn thành survey. **File chính.** |
| `sk_dump.py` | Skilljar: in toàn bộ câu hỏi + đáp án của một quiz (để soạn bank). |
| `cert_shot.py` | Skilljar: chụp chứng chỉ (full-page) vào thư mục theo tài khoản. |
| `lessons.py` | Liệt kê `id \| tiêu đề` mọi bài của một khóa (lọc quiz/survey). |
| `sweep.py` | In % hoàn thành của danh sách khóa. |
| `fpt_course.py` | daotao: enroll, `auto-all` (video/doc), mở exam/survey. |
| `fpt_solve.py` | daotao: giải exam theo nội dung (bank 8113/8114/8115, tiếng Anh 7971/7974). |
| `dsurvey.py` | daotao: hoàn thành survey (type 9). |

## 4. Quy trình Skilljar (một tài khoản → 100% + chứng chỉ)

```bash
cd D:/Du_an_mini/auto_tich

# 0) Xác nhận đúng tài khoản đang đăng nhập (chứng chỉ mang tên chủ tài khoản):
#    mở https://anthropic.skilljar.com/accounts/profile/ trong cửa sổ debug.

# 1) Enroll + học bài cho một hoặc nhiều khóa (phẩy ngăn cách, KHÔNG dấu cách):
CDP_URL=http://127.0.0.1:9222 python sk_worker.py W1 ai-fluency-framework-foundations,claude-101

# 2) Xem khóa nào còn dưới 100% (survey/quiz chưa qua sẽ hiện "<<<"):
CDP_URL=http://127.0.0.1:9222 python sweep.py claude-101,claude-platform-101

# 3) Tìm id bài quiz/survey của một khóa:
CDP_URL=http://127.0.0.1:9222 python lessons.py claude-platform-101 | grep -iE "quiz|survey"

# 4) Giải quiz (hoặc hoàn thành survey) — truyền URL bài đầy đủ:
CDP_URL=http://127.0.0.1:9222 python sk_solve.py claude-platform-101 https://anthropic.skilljar.com/claude-platform-101/486268
#   -> RESULT: Your score: 5 of 6 Correct (83%) You have passed

# 5) Chụp toàn bộ chứng chỉ vào thư mục của tài khoản:
CDP_URL=http://127.0.0.1:9222 python cert_shot.py certificates_<user> slug1,slug2,...
```

**Soạn bank cho quiz mới:** nếu `sk_solve.py` điểm thấp, dump đề rồi thêm rule vào `RULES["<slug>"]` trong `sk_solve.py`:

```bash
CDP_URL=http://127.0.0.1:9222 python sk_dump.py <slug> https://anthropic.skilljar.com/<slug>/<lessonId>
```

Rule là cặp `(regex-đoạn-câu-hỏi, [đoạn-text-đáp-án-đúng])`; khớp không phân biệt hoa/thường, chống xáo trộn đáp án. `GENERIC` áp cho mọi khóa; `RULES[slug]` ưu tiên trước.

## 5. Quy trình daotao

```bash
# Enroll + hoàn thành nội dung:
DAOTAO_OID=<oid> python fpt_course.py auto-all
# Giải exam (sau khi auto-all liệt kê item type 6):
python fpt_solve.py <oid> <itemId>
# Survey (type 9):
python dsurvey.py <oid> <surveyItemId>
```

Chi tiết + cách xử lý frame detach: xem [docs/daotao-automation.md](docs/daotao-automation.md).

## 6. Nộp chứng chỉ lên elis

elis dùng SSO FPT (MFA) → **người dùng tự đăng nhập** trong cửa sổ debug, rồi báo để nộp. Thao tác trực tiếp trên trang đang mở, **không reload** trang danh sách đã lọc (reload làm mất filter).

## 7. Tài liệu kiến thức (trước đây nằm trong memory ổ C)

- [docs/skilljar-automation.md](docs/skilljar-automation.md) — chi tiết CDP, cấu trúc khóa, 16 khóa, các gotcha của quiz, id quiz.
- [docs/daotao-automation.md](docs/daotao-automation.md) — enroll/exam/survey daotao, công thức xử lý session chập chờn.
- [docs/fpt-quiz-review.md](docs/fpt-quiz-review.md) — đọc đáp án đúng từ trang `bg_answertrue` của bài review.

## 8. Thư mục dữ liệu

- `certificates_<user>/` — ảnh chứng chỉ theo tài khoản (một `.png` mỗi khóa).
- `chrome_debug_profile/` (9222), `chrome_debug_profile2/` (9223) — profile Chrome debug (giữ session đăng nhập — **không xóa**).

## 9. Lỗi hay gặp

| Triệu chứng | Xử lý |
|---|---|
| Playwright nối CDP hỏng | Dùng `http://127.0.0.1` thay `localhost`. |
| "No skilljar tab found" | Mở khóa trong cửa sổ Chrome debug đúng cổng. |
| Quiz cứ trượt / resume câu kẹt | `sk_solve.py` tự FLUSH về trang kết quả rồi "Take this again" → "Start". |
| Survey không đạt 100% | Chạy `sk_solve.py` lên URL survey (RESULT rỗng vẫn đúng; kiểm bằng `sweep.py`). |
| daotao exam 0/10, frame detach | Xem công thức trong docs/daotao-automation.md. |
| Chứng chỉ sai tên | Kiểm `/accounts/profile/` đúng tài khoản trước khi chụp. |
