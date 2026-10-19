# Tự động hoàn thành khóa học Anthropic Academy (anthropic.skilljar.com)

Hoàn thành toàn bộ khóa AI (enroll → học bài → quiz có chấm điểm → chứng chỉ) cho một tài khoản, điều khiển Chrome thật qua DevTools Protocol (CDP).

## Kết nối CDP

Chrome phải chạy với cổng debug + profile riêng (Chrome 136+ chặn cổng debug trên profile mặc định):

```
chrome.exe --remote-debugging-port=9222 --user-data-dir=D:\Du_an_mini\auto_tich\chrome_debug_profile
```

Trên máy này `localhost` phân giải ra IPv6 → **bắt buộc dùng `http://127.0.0.1:9222`** trong Playwright `connect_over_cdp`. Mọi script đọc biến môi trường `CDP_URL` (mặc định `http://127.0.0.1:9222`). Chạy 2 tài khoản song song: Chrome thứ hai cổng `9223`, profile `chrome_debug_profile2`, truyền `CDP_URL=http://127.0.0.1:9223`. Hai trình duyệt độc lập nên chạy solver trên cả hai cùng lúc không bị tranh chấp.

## Đăng nhập

Form email/mật khẩu (không phải SSO): field `#id_login`, `#id_password`, nút `#button-sign-in` (vào qua nút "Sign In" trên anthropic.skilljar.com). Xác nhận đúng tài khoản qua `/accounts/profile/` (các input `first_name`/`last_name`/`email`) **trước khi** chụp chứng chỉ — chứng chỉ mang tên chủ tài khoản đó. Đăng nhập Skilljar sống qua các lần restart Chrome (khác với FPT SSO của elis/daotao cần login lại + MFA).

## Cấu trúc khóa học

- Trang landing `/<slug>`; bấm "Enroll in Course" (hoặc "Register | FREE") → các bài tại `/<slug>/<id-số>`.
- Bài nội dung **tự đánh dấu hoàn thành khi `page.goto`** — chỉ cần ghé qua.
- Dòng tiến độ: `X of Y lessons completed (Z%)`.
- Link bài: quét `a[href^="/<slug>/<digit>"]` (site không còn dùng class `a.lesson`).

## Danh mục (16 khóa trong bộ elis)

14 khóa lõi + `introduction-to-agent-skills` (6 bài) + `introduction-to-subagents` (4 bài) — **hai khóa mới chỉ có nội dung, KHÔNG có quiz**, chạy `sk_worker.py` là đạt 100%. Trang danh mục thêm tiền tố "Complete " vào tên khóa đã học xong — dùng để biết khóa nào đã hoàn thành. Các slug `ai-fluency-for-builders/creative-work/nonprofits/small-businesses/students` và `deploying-claude-enterprise-with-confidence` là khóa tự chọn theo đối tượng, **không** thuộc bộ elis bắt buộc.

## Quiz có chấm điểm (phần khó)

Mỗi khóa có ≥1 quiz; ba khóa dev (api/bedrock/vertex) có ~7-8 quiz module **cộng** một "Final Assessment" (20-25 câu) chốt 100%.

- Một câu / một trang, trong MAIN frame (không phải iframe).
- **Đáp án xáo trộn mỗi lần làm** → khớp theo NỘI DUNG text, không theo vị trí. Rule engine: regex-đoạn-câu-hỏi → đoạn-text-đáp-án-đúng.
- Kết quả: `Your score: N of M Correct (P%)`; "you have passed" / "did not pass". Làm lại không giới hạn. Thường cần 80% (final assessment thấp hơn, ~73-80%).
- **Không có nút "Show Answers"** — phải trả lời đúng bằng kiến thức.
- Khung 4D (Delegation, Description, Discernment, Diligence) là nền của mọi quiz AI-Fluency. api/bedrock/vertex cùng khái niệm nhưng **chữ của từng câu/đáp án khác nhau** → mỗi khóa cần bank riêng.

### Các "gotcha" đã học

1. **Câu cuối là satisfaction/feedback không chấm điểm:** satisfaction → "very satisfied", recommend → "very likely"; feedback là textarea + nút Submit (không có radio) → điền textarea + bấm Submit/Complete, nếu không quiz không kết thúc.
2. **Làm lại:** phải bấm "Take this again" RỒI nút "Start" xuất hiện sau đó (retry vài lần kèm chờ). Quiz bỏ dở sẽ resume ở câu đang kẹt với đáp án SAI cũ và trượt mãi cho tới khi restart sạch → `sk_solve.py` có vòng FLUSH đẩy bài dở về trang kết quả trước khi restart.
3. **Câu satisfaction cần `.check()` thật của Playwright** (click tổng hợp bằng JS bị báo "You must provide an answer").
4. **Vertex:** câu hỏi cùng khái niệm api/bedrock nhưng **text đáp án ngắn/khác** (vd "Response streaming" vs "enabling response streaming") → dùng bank bedrock chỉ được ~20-30%; đã có bank vertex riêng đầy đủ trong `sk_solve.py`.
5. **"Certificate of completion" / "Course Quiz" là quiz có chấm điểm** (vd ai-fluency-for-educators, ai-capabilities-and-limitations) — ghé qua chỉ để lại 4/5 hay 13/14; chạy `sk_solve.py` để qua và đạt 100%.

## Survey (ungraded, chốt ~2% cuối của khóa dev)

Bài "Course satisfaction survey" không chấm điểm nhưng chặn 100%. ID: api `297284`, vertex `297285`, intro-mcp `297281`, mcp-advanced `297276` (bedrock không có). Chạy `sk_solve.py <slug> <url-survey>` — vòng FLUSH chọn radio cuối + submit, đạt 100% (in RESULT rỗng là bình thường; kiểm chứng bằng % khóa).

## ID quiz (để chạy lại nhanh)

- **Bedrock module:** 289293, 289297, 289298, 289296, 289295, 289300, 289299 + Final `290881`.
- **Vertex module:** 289281, 289278, 289280, 289277, 289275, 289276, 289274, 289279 + Final `290880`.
- **Platform-101 quiz:** `486268`. Cowork `452288`. Code-101 `469849`. Capabilities `456462`.

(ID bài giống nhau giữa các tài khoản vì chung cấu trúc khóa.)

## Song song & bộ nhớ thấp

RAM thấp → ưu tiên mở nhiều TAB trong MỘT Chrome debug thay vì nhiều Chrome. Hai tài khoản thì mới cần Chrome thứ hai (9223).
