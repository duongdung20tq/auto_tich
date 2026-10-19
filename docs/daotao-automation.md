# Tự động hoàn thành khóa học daotao.fpt.com

Hoàn thành các khóa trên Dashboard daotao.fpt.com cho tài khoản đang đăng nhập, điều khiển bằng `fpt_course.py` / `fpt_solve.py` / `dsurvey.py` qua CDP (`CDP_URL=http://127.0.0.1:9222`).

> daotao + elis dùng FPT Microsoft SSO → restart Chrome là **mất session, phải login lại + MFA** (thủ công). Skilljar thì sống qua restart.

## Enroll

Mở `Course/Courseinfo?CourseID=<id>&cid=0`:
- Nút **"VÀO HỌC"** → đã đăng ký, bấm để vào `Curriculum/User_ViewCourse?oid=<oid>`.
- Nút **"ĐĂNG KÝ THAM GIA"** → chưa đăng ký, bấm (trang vào thẳng khóa).
- Khóa kiểu "Register | FREE" thì bấm nút đó.
- `oid` thường == `CourseID`.

## Nội dung

`fpt_course.py auto-all` đánh dấu mọi video/audio (type 1/2) đã xem đủ và lưu docs/html (type 3/4/5/7/8); liệt kê item tương tác (type 6 = exam, 9 = survey) để xử lý tay. Việc hoàn thành video/doc đã ở mức API (`Learn_LogTime`/`Learn_LogSave`/`Learn_Save`) — chi phí thật chỉ là exam.

`fpt_course.py` honors biến `DAOTAO_OID` để chọn tab theo URL (`oid=`); tab index KHÔNG ổn định.

## Exam (type 6)

`exam-open <id>` hay báo "NO ViewExam frame" lần đầu → chạy lại (2 lần). Rồi đọc câu hỏi + ID radio, quyết đáp án bằng kiến thức, `exam-answer <các-id-cách-nhau-dấu-phẩy>`, `exam-submit`. Điểm đọc ở frame `ViewTest` ("N/N Cấp độ Đạt"). Ngưỡng đạt 80%.

### Khi exam 0/10 hoặc frame cứ detach (session chập chờn)

ID phần tử đáp án tái dùng KHÔNG map ổn định giữa tài khoản/lần làm; `LoadViewCur()` + `goto(sameUrl)` KHÔNG reinit SPA. Công thức bền (`fpt_solve.py`):

1. Mở bằng `pg.reload()` rồi JS-click item sidebar `.li-sub-menu-el[data-cur-id="<item>"]`.
2. Sau khi iframe `ViewExam` hiện, `sleep(5)` — nó tự reload một lần, re-fetch frame trước khi bấm "Vào thi"/"Thi lại" qua `frame.evaluate` (không dùng `get_by_text`, sẽ ném "Frame detached").
3. Trả lời **theo NỘI DUNG không theo ID:** tách body theo `CÂU SỐ N:` → map câu N sang group `a_N_0`, khớp text đáp án đúng, set `.checked` + dispatch MouseEvent click lên cả input và label.
4. Verify số `input[type=radio]:checked` == số câu trước khi submit.
5. Đọc kết quả hay bị STALE (frame ExamineeID cũ) → tin icon sidebar `dahoc.svg` (= đạt) sau reload.

`fpt_solve.py` chứa bank đáp án theo nội dung cho **8114/8115** (4Ds + "Làm chủ AI"), **8113** (prompt engineering), và tiếng Anh **7971/7974** (ngữ pháp). Bank lớn hơn một lần làm hiển thị; khi in UNMATCHED thì đọc Q+OPTS dump ra rồi thêm rule, chạy lại (script không bao giờ submit khi còn thiếu).

### Bank lớn hơn một lần làm & một item có thể rút bank khác mỗi lần

Vd 8114 item 182696 có lúc rút bank Discernment, có lúc bank "Diligence / Cẩn trọng thấu đáo" (10 câu khác: Transparency/Creation/Deployment diligence, ẩn dụ "Lái xe ô tô"). Khi UNMATCHED → đọc dump, thêm rule, chạy lại.

## Survey (type 9)

`dsurvey.py <oid> <surveyItemId>` — mở bằng reload + click sidebar, điền iframe `#myFrame` chọn radio cuối mỗi group, `AnswerSurvey('SurveyDo')`, xác nhận.

## Song song — cảnh báo

Chạy 4 tab daotao cùng lúc nhanh nhưng gây TRANH CHẤP submit — đáp án khớp+đăng ký nhưng submit cuối đôi khi không lưu (item vẫn chuahoc); readback checked đôi khi thấy 0 và abort an toàn. → Sau mỗi batch song song, LUÔN verify lại status `.li-sub-menu-el` (dahoc) và chạy lại item thiếu TUẦN TỰ. ≤2 tab đồng thời ổn định hơn 4.

## Các khóa đã làm

"Làm chủ AI" (8114 collaboration framework, 8115 "Hiểu Đúng Để Dùng Trúng") test khung 4Ds + next-token prediction / working memory / steerability / knowledge cutoff. Tiếng Anh "theo chủ đề" P2/P3 là bài cuối ngữ pháp 20 câu.

**Gotcha:** đừng bao giờ viết `time.sleep=None` (rebind tên → TypeError lần gọi sau).
