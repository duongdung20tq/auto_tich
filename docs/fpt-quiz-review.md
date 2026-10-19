# Đọc đáp án đúng từ trang review bài thi FPT eLearning

Quiz daotao.fpt.com (type 6) rút một tập con NGẪU NHIÊN từ bank câu hỏi lớn mỗi lần làm (thứ tự + câu nào đều thay đổi), nhưng ID input đáp án (`a_N_0` → id số) ỔN ĐỊNH theo từng câu, qua các tài khoản/lần làm. Làm lại không giới hạn; đạt = 80%.

## Cách tìm đáp án đúng sau một lần làm trượt (chắc chắn, không đoán)

1. Sau submit, frame kết quả có URL `Examination/User_ViewTest/{ExamineeID}` — bảng lần thi có link `Xem kết quả` → `/QuestionFrame/QuestionResult?UserTestID={id}`.
2. Vào URL QuestionResult đó, bấm chữ `Kết quả chi tiết`.
3. Frame `/ViewTestDetails?UserTestID={id}` load. Mỗi khối câu hỏi là `Câu hỏi số N (Điểm: X/1)` (X=0 → sai). `<label>` của đáp án ĐÚNG có class CSS **`bg_answertrue`** (đáp án đã chọn mà sai thì chữ đỏ). Đọc text label của phần tử `bg_answertrue` mỗi câu = đáp án đúng.

## Rule engine theo text

Regex-đoạn-câu-hỏi → text-đáp-án-đúng xử lý được việc xáo trộn vì khớp trên câu hỏi đọc-live mỗi lần làm. Đây là cùng nguyên tắc với bank trong `fpt_solve.py` (daotao) và `sk_solve.py` (Skilljar).
