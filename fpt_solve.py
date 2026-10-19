"""Content-matched daotao exam solver (FPT shows all Qs on one page).
Answers by matching the correct-answer TEXT substring within each question group,
immune to shuffled option order and per-attempt element IDs.
Usage: python fpt_solve.py <oid> <item>   (selects the daotao tab whose URL has oid)
"""
import sys, time, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from playwright.sync_api import sync_playwright

oid, item = sys.argv[1], sys.argv[2]
TAB = int(sys.argv[3]) if len(sys.argv) > 3 else 0

RULES = [
 # ---- 8114 Quiz 2 ----
 (r"Thẩm định đầu ra.*Discernment.*yêu cầu người dùng", r"Đánh giá và kiểm chứng khách quan"),
 (r"dịch chuyển tư duy.*vai trò của AI", r"đối tác đáng tin cậy để giải quyết"),
 (r"Sự thông thạo AI.*định nghĩa chính xác", r"hiệu quả, tối ưu, có đạo đức và an toàn"),
 (r"Kỹ năng bề nổi.*không mang tính bền vững", r"nhanh chóng trở nên lỗi thời"),
 (r"Trọng tâm cốt lõi của khái niệm .Sự thông thạo AI", r"Con người và cách con người tương tác"),
 # ---- 8114 Quiz 3 ----
 (r"Cộng tác đồng hành.*Augmentation.*phù hợp nhất khi", r"không gian đối thoại để thử nghiệm"),
 (r"Tự động hóa.*Automation.*vai trò của con người và AI", r"Con người đưa ra chỉ dẫn trực tiếp"),
 (r"ví dụ thực tế về chế độ Cộng tác đồng hành", r"kiến trúc phần mềm phức tạp"),
 (r"dấu hiệu rõ nét của .khoảng cách năng lực", r"bối rối khi nhận phản hồi không mong muốn"),
 (r"Ủy quyền hành động.*Agency.*vai trò của con người", r"Người viết kịch bản.*Đạo diễn"),
 # ---- 8114 Quiz 5 ----
 (r"Thấu hiểu vấn đề.*Problem awareness.*trước khi đưa AI", r"Định nghĩa rõ ràng mục tiêu"),
 (r"phân biệt giữa hệ thống AI mạnh về sáng tạo", r"Thấu hiểu nền tảng"),
 (r"Ủy quyền công việc.*Delegation.*trong bối cảnh cộng tác.*là gì", r"phân rã công việc và (chọn|lựa chọn)"),
 (r"bản chất cốt lõi của năng lực .Ủy quyền công việc.*được định nghĩa như thế nào", r"phân rã công việc và lựa chọn chế độ tương tác"),
 (r"ví dụ về dự án nghiên cứu.*ủy quyền", r"đọc hiểu nhanh và tóm tắt"),
 (r"nền tảng quan trọng nhất để thực hiện ủy quyền", r"Chuyên môn nghiệp vụ"),
 (r"khu vực mơ hồ cần đối tác tư duy", r"Thấu hiểu vấn đề"),
 (r"chuyên môn nghiệp vụ.*nền tảng cốt lõi", r"không hiểu rõ mục tiêu và bối cảnh"),
 (r"phần lớn trường hợp.*thẩm định phát hiện ra lỗi", r"Mô tả lại yêu cầu một cách rõ ràng"),
 (r"phán đoán chuyên môn cốt lõi và thẩm định đạo đức", r"Giữ lại tuyệt đối cho con người"),
 (r"Thấu hiểu nền tảng.*Platform awareness.*khuyến nghị", r"thử nghiệm trực tiếp trên nhiều công cụ"),
 # ---- 8114 Quiz 6 ----
 (r"hướng dẫn AI thực hiện phân tích dữ liệu theo đúng 3 bước", r"Mô tả quy trình"),
 (r"Mô tả yêu cầu.*Description.*được hiểu như thế nào là đúng", r"truyền thông và giao tiếp sâu sắc"),
 (r"đóng vai một gia sư", r"Mô tả tương tác"),
 (r"chỉ cung cấp một câu lệnh ngắn gọn.*thất bại", r"không thể đọc được suy nghĩ"),
 (r"đối tượng độc giả.*định dạng kết quả", r"Mô tả thành phẩm"),
 (r"Cây cầu.*The Bridge", r"ý đồ của con người và khả năng thực thi"),
 (r"ví dụ minh họa trực quan.*demonstration", r"Mô tả thành phẩm, vì ví dụ"),
 (r"bước chuẩn bị không thể thiếu cho.*Thẩm định", r"không có mô tả chi tiết"),
 (r"giải thích lý do đằng sau mỗi bước", r"Mô tả tương tác"),
 (r"câu lệnh ăn sẵn.*clever prompts.*sang.*Mô tả", r"kỹ năng bề nổi sang xây dựng môi trường"),
 # ---- 8114 Quiz 7/8 ----
 (r"vai trò cốt lõi của .Thẩm định đầu ra.*ví như", r"Hệ thống kiểm soát chất lượng"),
 (r"lệch pha. về quy trình", r"lén lút đưa các ý tưởng đã bị bác bỏ"),
 (r"Cấu trúc trình bày này đã mạch lạc", r"Thẩm định thành phẩm"),
 (r"lỗi lặp lại liên tục do giới hạn hệ thống", r"Tái định hình việc Ủy quyền"),
 (r"KHÔNG thuộc bộ 4 yếu tố cấu thành một phản hồi", r"tự tìm ra lỗi sai mà không giải thích"),
 (r"Thẩm định kết hợp với năng lực nào", r"^Mô tả yêu cầu$"),
 (r"quan trọng nhất khi giải thích lỗi sai", r"Cung cấp bối cảnh và tiêu chuẩn"),
 (r"khi sự thẩm định phát hiện ra lỗi, giải pháp tốt nhất", r"Mô tả lại yêu cầu một cách rõ ràng"),
 (r"phản hồi chất lượng để AI điều chỉnh", r"Màu sắc đang chưa phù hợp"),
 (r"câu hỏi xã giao rườm rà", r"Thẩm định tương tác"),
 # ---- 8114 Quiz 9 Diligence (Cẩn trọng thấu đáo) ----
 (r"Cẩn trọng trong minh bạch.*Transparency diligence.*nền tảng để duy trì lòng tin", r"mọi người có quyền được biết khi AI đóng vai trò quan trọng"),
 (r"thể hiện đúng nhất trụ cột .Cẩn trọng khi khởi tạo.*Creation diligence", r"Chủ động tìm hiểu về chính sách bảo mật và quyền sở hữu dữ liệu"),
 (r"điểm khác biệt cốt lõi.*Sự cẩn trọng thấu đáo.*Diligence.*phân biệt với ba năng lực", r"Tập trung chủ yếu vào khía cạnh đạo đức và an toàn"),
 (r"Cẩn trọng khi triển khai.*Deployment diligence.*trước khi chia sẻ kết quả", r"Tự chịu trách nhiệm hoàn toàn bằng cách xác thực sự thật"),
 (r"tư duy phê phán và chủ động lựa chọn hệ thống AI an toàn", r"Cẩn trọng khi khởi tạo.*Creation diligence"),
 (r"Sự minh bạch.*Transparency.*một phần của năng lực cẩn trọng", r"duy trì lòng tin và sự tôn trọng trong các mối quan hệ chuyên nghiệp"),
 (r"sự khác biệt căn bản giữa .Sự cẩn trọng thấu đáo.*so với ba năng lực", r"khía cạnh đạo đức và an toàn thay vì chỉ là hiệu suất"),
 (r"vi phạm trụ cột .Cẩn trọng khi khởi tạo.*Creation diligence", r"công cụ AI miễn phí.*dữ liệu khách hàng nhạy cảm"),
 (r"Cẩn trọng khi triển khai.*Deployment diligence.*trách nhiệm xác thực.*thuộc về ai", r"Chính cá nhân người sử dụng và chia sẻ kết quả"),
 (r"Lái xe ô tô.*nhấn mạnh điều gì", r"Mọi hành động tương tác với AI đều có thể gây ra hệ quả"),
 # ================= 8113 Prompt engineering =================
 (r"Thuật ngữ 'Shot'|'Shot' trong kỹ nghệ câu lệnh", r"Ví dụ mẫu cung cấp cho AI bắt chước"),
 (r"Cơ chế hoạt động cốt lõi.*Mô hình Ngôn ngữ Lớn.*LLM", r"Dự đoán từ tiếp theo có xác suất xuất hiện cao nhất"),
 (r"Thành phần quan trọng nào nên đặt ở đầu câu lệnh", r"Một động từ hành động rõ ràng"),
 (r"hiện tượng 'Ảo tưởng'.*Hallucination.*định nghĩa", r"tự tin đưa ra thông tin hoàn toàn sai lệch hoặc bịa đặt"),
 (r"hành vi nào sau đây là TUYỆT ĐỐI BỊ CẤM", r"Nhập mã nguồn dự án"),
 (r"câu hỏi tự vấn nào là quan trọng nhất để đối phó.*Ảo tưởng", r"chính xác về mặt sự thật không và có số liệu kiểm chứng"),
 (r"AI bắt đầu đưa ra câu trả lời bị rối, không nhất quán", r"Chủ động mở một cuộc hội thoại mới"),
 (r"phân chia 100 phản hồi của khách hàng thành các nhóm", r"Phân loại"),
 (r"Tìm quán chay ăn trưa.*kém hiệu quả", r"không có khả năng tự ngầm hiểu bối cảnh"),
 (r"cung cấp đúng 1 ví dụ mẫu duy nhất cho AI bắt chước", r"One-shot Prompting"),
 (r"gắn nhãn 'Quản trị dự án PM' cho nam giới", r"Định kiến.*Bias.*dữ liệu huấn luyện"),
 (r"cung cấp quá nhiều ví dụ.*quá nhiều 'Shot'.*phản tác dụng", r"rập khuôn máy móc, giảm bớt sự linh hoạt"),
 (r"trích xuất tên dự án, quản trị dự án.*thời hạn hoàn thành.*tối ưu nhất", r"trình bày dưới dạng một bảng biểu gọn gàng"),
 (r"thứ tự đúng của quy trình lặp tinh chỉnh câu lệnh", r"Viết phiên bản câu lệnh đầu tiên -> Đánh giá kết quả đầu ra"),
 (r"Khóa cửa thông minh FPT.*Few-shot đúng chuẩn nhất", r"liệt kê ít nhất 2 ví dụ mẫu hoàn chỉnh về sản phẩm khác"),
 # ================= 8115 "Làm chủ AI" =================
 (r"Hai mặt của một đồng xu", r"cùng một thuộc tính kỹ thuật duy nhất"),
 (r"Dải liên tục.*Continuum.*Vùng năng lực", r"Mật độ dữ liệu khuôn mẫu cực kỳ dày đặc"),
 (r"Niềm tin hiệu chuẩn.*Calibrated Trust", r"Tự vấn nhanh để định vị tác vụ"),
 (r"AI truyền thống.*AI tạo sinh.*Generative", r"sắp xếp, phân loại dựa trên dữ liệu có sẵn"),
 (r"Bộ khung 4 thuộc tính cốt lõi", r"Dự đoán từ tiếp theo, Tri thức, Bộ nhớ tạm thời"),
 (r"Xu hướng đồng thuận thái quá", r"tự động nhận sai và thay đổi đáp án chính xác"),
 (r"Huấn luyện sơ bộ.*Pre-training.*thô sơ", r"Máy hoàn thiện văn bản"),
 (r"Sự quá thận trọng.*Overcaution.*bộc lộ", r"cảnh báo rườm rà hoặc từ chối các yêu cầu công việc lành mạnh"),
 (r"từ chối thực hiện một tác vụ phân tích tài liệu", r"chủ động viết lại câu lệnh để làm rõ bối cảnh"),
 (r"tổng thống đầu tiên của Hoa Kỳ là Abraham Lincoln", r"Sycophancy.*Đánh giá.*Discernment"),
 (r"Xu hướng dông dài.*Verbosity.*mặc định", r"dài dòng, chi tiết thường được con người chấm điểm cao hơn"),
 (r"Huấn luyện tinh chỉnh.*Fine-tuning.*uốn nắn mô hình thành", r"ví dụ mẫu về hành vi tốt và chấm điểm thưởng"),
 (r"Độ hiệu chuẩn tự tin kém.*Loose Confidence Calibration", r"tự tin của ngôn từ, hoàn toàn độc lập với tính chính xác"),
 (r"tự tin đưa ra một nguồn trích dẫn.*giả mạo", r"khớp với khuôn mẫu chữ nghĩa của động cơ dự đoán"),
 (r"Con đường mòn quen thuộc.*Well-worn", r"Tóm tắt báo cáo dài, định dạng lại"),
 (r"minh chứng cho một tác vụ thành công rực rỡ", r"tóm tắt các lập luận chính trong một cuốn sách"),
 (r"Nhiệm vụ cốt lõi và cơ chế vận hành gốc rễ", r"Dự đoán mảnh nhỏ tiếp theo của từ"),
 (r"Lối đi thưa thớt.*Thin path", r"lắp ghép các mảnh chữ ngẫu nhiên"),
 (r"mô tả trực quan cơ chế hoạt động của động cơ", r"tự động điền từ.*autocomplete"),
 (r"kiểm chứng nguồn gốc.*source verification", r"không thể tự phân biệt một cách đáng tin cậy"),
 (r"Bộ Quy tắc Vàng.*dễ tập trung lỗi bịa đặt", r"Tên riêng, ngày tháng, số liệu thống kê"),
 (r"Sự trôi chảy.*Tính chính xác thực tế.*hiểu đúng", r"hai biến số hoàn toàn độc lập"),
 (r"thấu hiểu sâu sắc về thuộc tính .Dự đoán từ tiếp theo", r"Thẩm định đầu ra.*không bị đánh lừa"),
 (r"Điểm dừng tri thức.*Knowledge Cutoff", r"cột mốc thời gian trong quá khứ khi quá trình huấn luyện kết thúc"),
 (r"kết nối AI với các kho dữ liệu đóng nội bộ", r"MCP.*Model Context Protocol.*kết nối kho dữ liệu"),
 (r"lưu trữ và liên kết dưới dạng biểu diễn nội bộ", r"Embeddings ánh xạ"),
 (r"mối liên kết tri thức liên ngành", r"xếp tụ lại gần nhau trong không gian toán học Embeddings"),
 (r"thuộc .Vùng năng lực.*dải liên tục tri thức", r"khoa học đại chúng, lịch sử kinh điển"),
 (r"Chứng mất trí nhớ nguồn.*Source amnesia", r"không nhớ chính xác thông tin nó lấy ra nằm ở tài liệu"),
 (r"AI xuất sắc ở một lĩnh vực này. không đảm bảo", r"mật độ bao phủ dữ liệu huấn luyện phân bổ không hề đồng đều"),
 (r"tổng hợp báo cáo tài chính ngách", r"tự đính kèm tài liệu nguồn uy tín"),
 (r"tắt tính năng tìm kiếm web.*khoảng trống tri thức", r"hoạt động cô lập, dựa hoàn toàn vào tri thức tĩnh"),
 (r"Định kiến thừa hưởng.*Inherited bias", r"để mặc cho mô hình tự suy luận"),
 (r"Cửa sổ ngữ cảnh.*Context Window.*vai trò", r"Bộ nhớ tạm thời.*chứa toàn bộ lịch sử chat"),
 (r"lưu giữ các sự thật cốt lõi qua nhiều phiên", r"Lưu nhớ chọn lọc.*Memory"),
 (r"Hiệu ứng Vách đá.*Cliff", r"chạm giới hạn bộ nhớ và lập tức sụp đổ"),
 (r"Mất tập trung ở giữa.*Lost-in-the-middle", r"ghi nhớ rất tốt thông tin ở đầu và cuối"),
 (r"mặc định.*bộ nhớ tạm thời.*giữa các phiên", r"hoàn toàn trống rỗng và AI bắt đầu lại"),
 (r"vượt quá giới hạn cứng của Cửa sổ ngữ cảnh", r"cũ nhất ở đầu cuộc hội thoại sẽ bị đẩy ra ngoài"),
 (r"Bộ nhớ tạm thời va chạm với Khả năng điều hướng.*lỗi hệ thống", r"bị đẩy ra ngoài hoособ loãng đi"),
 (r"AI bắt đầu phớt lờ các ràng buộc ban đầu do tràn bộ nhớ", r"Mở một phiên chat mới hoàn toàn"),
 (r"phòng chống.*Mất tập trung ở giữa.*kỹ thuật viết câu lệnh", r"Ưu tiên vị trí vàng"),
 (r"thấu hiểu thuộc tính bộ nhớ tạm thời.*Mô tả.*Description", r"phải nằm vừa vặn trong cửa sổ ngữ cảnh"),
 (r"chỉ thị cụ thể, dễ kiểm chứng", r"nằm vững trong vùng năng lực và rất dễ khớp khuôn mẫu"),
 (r"Chấp hành câu chữ nhưng sai tinh thần.*Letter over spirit", r"đúng tuyệt đối các ràng buộc định dạng theo nghĩa đen"),
 (r"Prompt hệ thống.*System Prompt", r"mỏ neo. giúp AI giữ vững phong cách"),
 (r"Khả năng điều hướng.*Steerability.*giai đoạn huấn luyện", r"Tinh chỉnh.*Fine-tuning.*đánh giá và sở thích"),
 (r"Tác vụ nào.*Vùng năng lực.*thuộc tính Điều hướng", r"Duy trì vai trò xuyên suốt"),
 (r"bản chất của Khả năng điều hướng.*Steerability", r"khớp khuôn mẫu thống kê chứ không phải thực sự thấu hiểu"),
 (r"Trôi dạt lập luận.*chuỗi lập luận logic dài.*kỹ thuật", r"mốc kiểm soát trung gian"),
 (r"Trôi dạt lập luận.*Reasoning drift.*giải thích", r"sai sót cực kỳ nhỏ ở bước lập luận trung gian"),
 (r"Khả năng điều hướng.*nâng cao năng lực .Mô tả yêu cầu", r"thu hẹp tối đa khoảng trống ý đồ"),
 (r"chuỗi lập luận phức tạp.*Ủy quyền.*Delegation.*khôn ngoan", r"thiết lập chốt kiểm duyệt nghiêm ngặt"),
 (r"nguyên nhân gốc rễ.*lỗi kép 2 giữa Bộ nhớ tạm thời", r"đẩy các chỉ dẫn quan trọng ban đầu ra ngoài"),
 (r"dệt nên các nguồn trích dẫn học thuật giả mạo có hình dáng hoàn hảo", r"khớp với khuôn mẫu nhịp điệu ngôn từ"),
 (r"hầu hết các lỗi sai sót kỳ lạ.*xuất phát từ nguyên nhân cốt lõi", r"giao thoa và va chạm của hai giới hạn"),
 (r"Bộ nhớ tạm thời va chạm với Khả năng điều hướng, AI sẽ hành xử", r"âm thầm ghi đè, lấn át"),
 (r"tư duy Chẩn đoán lỗi hệ thống.*công sở", r"thất vọng mơ hồ.*thành hành động điều chỉnh có mục tiêu"),
 (r"Lỗi kép 1.*Dự đoán từ tiếp theo gặp gỡ Tri thức", r"tự bịa đặt ra các bài báo nghiên cứu"),
 (r"chẩn đoán và phát hiện các khuôn mẫu lỗi.*giá trị dài hạn", r"tối ưu hóa, tái cấu trúc và phân chia việc giao phó"),
 (r"liên tục chỉnh sửa câu từ của câu lệnh.*vô định", r"phỏng đoán may rủi và không giải quyết được gốc rễ"),
 (r"lỗi kép .Dự đoán từ tiếp theo x Khoảng trống tri thức", r"Mở một phiên làm việc mới sạch sẽ, cung cấp trực tiếp"),
 (r"không thể tự nhận biết và cảnh báo.*đang bịa đặt", r"không thể tự phân biệt một cách đáng tin cậy giữa tri thức có sẵn"),
 # ================= English (7971 / 7974) =================
 (r"\byou like to join us for lunch", r"^Would$"),
 (r"missed the bus,\s*_+\s*she took a taxi", r"^so$"),
 (r"Tokyo is one of\s*_+\s*cities", r"^the most expensive$"),
 (r"This bridge\s*_+\s*built 100 years ago", r"^was$"),
 (r"They\s*_+\s*in this company since 2018", r"^have worked$"),
 (r"movie was boring,\s*_+\s*we left early", r"^so$"),
 (r"Visitors\s*_+\s*show their ID", r"^must$"),
 (r"smartphones\s*_+\s*in China every year", r"^are produced$"),
 (r"dark clouds!? It\s*_+\s*rain soon", r"^is going to$"),
 (r"She\s*_+\s*to book a flight to Singapore", r"^would like$"),
 (r"mentioned that she\s*_+\s*to discuss the proposal", r"^would like$"),
 (r"I\s*_+\s*it if you could review my report", r"^would appreciate$"),
 (r"new regulations\s*_+\s*into effect", r"^will be put$"),
 (r"most challenging project we\s*_+\s*ever\s*_+\s*on", r"^have / worked$"),
 (r"_+\s*disclose this information.*strictly confidential", r"^mustn't$"),
 (r"suspect is believed\s*_+\s*fled the country", r"^to have$"),
 (r"The more effort you put in,\s*_+\s*results", r"^the better$"),
 (r"_+\s*the complexity of the project, we need to extend", r"^Because of$"),
 (r"presentation was\s*_+\s*complicated\s*_+\s*many participants", r"^so / that$"),
 (r"by far\s*_+\s*qualified", r"^the most$"),
 (r"I've decided\. I\s*_+\s*apply for that job", r"^am going to$"),
 (r"Students\s*_+\s*use their phones during exams", r"^shouldn't$"),
 (r"This restaurant serves\s*_+\s*food than", r"^better$"),
 (r"couldn't attend the meeting\s*_+\s*he was sick", r"^because$"),
 (r"Tomorrow is Sunday\. I\s*_+\s*go to work", r"^don't have to$"),
 (r"Watch out!? That ladder\s*_+\s*fall", r"^is going to$"),
 (r"She\s*_+\s*have left already", r"^must$"),
 (r"This solution is\s*_+\s*practical of all", r"^the least$"),
 (r"saved money regularly\s*_+\s*he could buy", r"^so that$"),
 (r"company went bankrupt\s*_+\s*poor financial management", r"^because of$"),
 (r"You\s*_+\s*have submitted the report earlier", r"^should$"),
 (r"The girl\s*_+\s*bicycle was stolen", r"^whose$"),
 (r"The man\s*_+\s*is standing over there", r"^who$"),
 (r"He\s*_+\s*have been at home\. The lights were on", r"^must$"),
 (r"She\s*_+\s*her keys yesterday", r"^lost$"),
 (r"If she\s*_+\s*earlier, she wouldn't have missed", r"^had left$"),
 (r"She\s*_+\s*have finished by now", r"^must$"),
 (r"The city\s*_+\s*I was born", r"^where$"),
 (r"If it\s*_+\s*tomorrow, we will cancel", r"^rains$"),
 (r"Tom said.*I have finished my homework.*he\s*_+\s*his homework", r"^had finished$"),
 (r"We\s*_+\s*the movie last night", r"^watched$"),
 (r"He is the only person\s*_+\s*understands me", r"^that$"),
 (r"It's been ages since we last\s*_+\s*each other", r"^saw$"),
 (r"Let's go to the cinema.*Mary\s*_+\s*going to the cinema", r"^suggested$"),
 (r"_+\s*I known about the meeting, I would have attended", r"^Had$"),
 (r"She didn't come to the party\. She\s*_+\s*have forgotten", r"^must$"),
 (r"You\s*_+\s*have parked here\. It's a no-parking", r"^shouldn't$"),
 (r"Don't touch that wire.*He\s*_+\s*me not to touch", r"^warned$"),
 (r"The ground is wet\. It\s*_+\s*have rained last night", r"^must$"),
 (r"Up to now, the teacher\s*_+\s*our class four tests", r"^has given$"),
 (r"The reason\s*_+\s*she was absent is still unknown", r"^why$"),
 (r"This is the first time I\s*_+\s*such a delicious meal", r"^have eaten$"),
 (r"If he\s*_+\s*the money, he would have bought", r"^had had$"),
 (r"All\s*_+\s*is needed is a little patience", r"^that$"),
 (r"Would you like to come to my party.*She\s*_+\s*me to her party", r"^invited$"),
 (r"He\s*_+\s*for this company for 20 years before he retired", r"^had worked$"),
 (r"If she\s*_+\s*so hard, she wouldn't be so tired now", r"^didn't work$"),
 (r"I\s*_+\s*never\s*_+\s*to Australia before", r"^have / been$"),
 (r"_+\s*you need any clarification, please contact", r"^Should$"),
 (r"I\s*_+\s*to Paris three times so far", r"^have been$"),
 (r"If you heat water to 100.C, it\s*_+", r"^boils$"),
 (r"This is the book\s*_+\s*I bought yesterday", r"^which$"),
 (r"They\s*_+\s*here since 2010", r"^have lived$"),
 (r"They said,?\s*.We are studying.*they\s*_+\s*studying", r"^were$"),
 (r"You\s*_+\s*have told me earlier\. I was waiting", r"^should$"),
 (r"He said,?\s*.I will help you.*he\s*_+\s*help me", r"^would$"),
 (r"He\s*_+\s*have stolen the money; he was with me all day", r"^couldn't$"),
 (r"I didn't break the vase.*The boy\s*_+\s*breaking the vase", r"^denied$"),
 (r"If I\s*_+\s*you, I would study harder", r"^were$"),
 (r"But for your help, I\s*_+\s*the exam", r"^would have failed$"),
 (r"flight was delayed\s*_+\s*the heavy fog", r"^because of$"),
 (r"That was\s*_+\s*movie I have ever watched", r"^the worst$"),
 (r"This time next week, I\s*_+\s*on the beach", r"^will be lying$"),
 (r"By the time she arrives, we\s*_+\s*already\s*_+\s*the meeting", r"^will have / started$"),
 (r"They\s*_+\s*have taken my umbrella by mistake", r"^might$"),
 (r"You look tired\. You\s*_+\s*get some rest", r"^should$"),
 (r"My brother,?\s*_+\s*wife is a doctor", r"^whose$"),
]

def qframe(pg):
    for f in pg.frames:
        if "questiontest" in (f.url or ""):
            return f
    return None

def open_exam(pg):
    if f"oid={oid}" not in (pg.url or ""):
        pg.goto(f"https://daotao.fpt.com/Curriculum/User_ViewCourse?oid={oid}&mlid=1", wait_until="domcontentloaded")
        time.sleep(6)
    for attempt in range(8):
        try:
            pg.reload(wait_until="domcontentloaded"); time.sleep(7)
            pg.wait_for_selector(f'.li-sub-menu-el[data-cur-id="{item}"]', timeout=10000)
            ok = pg.evaluate("(id)=>{const el=[...document.querySelectorAll('.li-sub-menu-el')].find(e=>(e.getAttribute('data-cur-id')||'')===id);if(el){el.click();return true;}return false;}", str(item))
            if not ok:
                print(f"  attempt {attempt+1}: no sidebar el"); continue
            time.sleep(7)
        except Exception as e:
            print("open nav err", str(e)[:40]); continue
        seen = False
        for _ in range(15):
            if any("ViewExam" in (f.url or "") for f in pg.frames):
                seen = True; break
            time.sleep(1)
        if seen:
            time.sleep(5)
            for _try in range(4):
                vf = next((f for f in pg.frames if "ViewExam" in (f.url or "")), None)
                if not vf: time.sleep(2); continue
                try:
                    clicked = vf.evaluate("""()=>{const els=[...document.querySelectorAll('button,a,input[type=button],input[type=submit]')];for(const nm of ['Vào thi','Thi lại','Tiếp tục thi']){const e=els.find(x=>((x.innerText||x.value||'').trim())===nm);if(e){e.click();return nm;}}return null;}""")
                    if clicked: break
                except Exception:
                    time.sleep(2)
            time.sleep(2.5)
            for scope in pg.frames + [pg]:
                try:
                    okb = scope.get_by_role("button", name="OK")
                    if okb.count(): okb.first.click(); break
                except Exception: pass
        for _ in range(20):
            qf = qframe(pg)
            if qf:
                try:
                    if len(set(qf.evaluate("()=>[...document.querySelectorAll('input[type=radio]')].filter(i=>i.name&&i.name.startsWith('a_')).map(i=>i.name)"))) > 0:
                        return qf
                except Exception: pass
            time.sleep(1)
        print(f"  attempt {attempt+1}: no qframe")
    return None

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    dts = [q for c in b.contexts for q in c.pages if "daotao" in q.url]
    pg = next((q for q in dts if f"oid={oid}" in (q.url or "")), None) or (dts[TAB] if TAB < len(dts) else dts[0])
    pg.on("dialog", lambda d: d.accept())
    qf = open_exam(pg)
    if not qf:
        print(f"{item}: FAILED open"); sys.exit(1)
    res = qf.evaluate(
        """(rules)=>{
        const body=(document.body.innerText||'');
        const parts=body.split(/C[ÂA]U\\s*S[ỐO]\\s*(\\d+)\\s*:/);
        const blocks={};
        for(let i=1;i<parts.length;i+=2){ blocks[parseInt(parts[i])]=(parts[i+1]||'').replace(/\\s+/g,' '); }
        const groups={};
        document.querySelectorAll('input[type=radio]').forEach(i=>{ if(i.name&&i.name.startsWith('a_')) (groups[i.name]=groups[i.name]||[]).push(i); });
        let matched=0, total=0; const unmatched=[];
        for(const name of Object.keys(groups)){
          total++;
          const qn=parseInt(name.split('_')[1]);
          const qtext=blocks[qn]||'';
          const radios=groups[name];
          let done=false;
          for(const [qp,ap] of rules){
            if(new RegExp(qp,'i').test(qtext)){
              const are=new RegExp(ap,'i');
              for(const r of radios){
                const l=r.closest('label')||document.querySelector("label[for='"+r.id+"']");
                const t=((l?l.innerText:'')||'').replace(/\\s+/g,' ').trim();
                if(are.test(t)){ r.checked=true; try{if(typeof r.onclick==='function')r.onclick();}catch(e){} r.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window})); r.dispatchEvent(new Event('change',{bubbles:true})); if(l){l.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window}));} matched++; done=true; break; }
              }
              if(done) break;
            }
          }
          if(!done){ const opts=radios.map(r=>{const l=r.closest('label')||document.querySelector("label[for='"+r.id+"']");return ((l?l.innerText:'')||'').replace(/\\s+/g,' ').trim();}); unmatched.push('Q'+qn+': '+qtext.slice(0,140)+' || OPTS: '+opts.join(' ~~ ')); }
        }
        return {total, matched, unmatched};
    }""", [[qp, ap] for qp, ap in RULES])
    print("answer:", {"total": res["total"], "matched": res["matched"]})
    if res["matched"] < res["total"]:
        print("UNMATCHED:", res["unmatched"]); print("Not submitting."); sys.exit(2)
    time.sleep(1.5)
    reg = qf.evaluate("()=>new Set([...document.querySelectorAll('input[type=radio]:checked')].filter(i=>i.name&&i.name.startsWith('a_')).map(i=>i.name)).size")
    print("registered checked:", reg, "/", res["total"])
    if reg < res["total"]:
        print("Answers not registered; not submitting."); sys.exit(3)
    qf.get_by_text("Kết thúc bài thi").first.click()
    time.sleep(1.5)
    for scope in pg.frames + [pg]:
        try:
            okb = scope.get_by_role("button", name="OK")
            if okb.count(): okb.first.click(); break
        except Exception: pass
    time.sleep(4)
    score = "?"
    for _ in range(25):
        for fr in pg.frames:
            if "ViewTest" in (fr.url or ""):
                try:
                    m = re.search(r"(\d+/\d+)\s*(Cấp độ )?(Đạt|Không đạt)", " ".join(fr.locator("body").inner_text().split()))
                    if m: score = m.group(0); break
                except Exception: pass
        if score != "?": break
        time.sleep(1)
    print(f"{item}: {score}")
