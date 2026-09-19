# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Tôi yêu VinUni
**Biến thể:** K4-L3A — Truy xuất Dịch vụ / Quy chế Đại học  
**Thành viên:**
1. **Đào Thanh Trường** (MSSV: 2A202602683) — Trách nhiệm: *SentenceChunker* (Trưởng nhóm)
2. **Nguyễn Huy Hùng** (MSSV: 2A202602990) — Trách nhiệm: *FixedSizeChunker*
3. **Nguyễn Minh Hiển** (MSSV: 2A202602759) — Trách nhiệm: *RecursiveChunker*

**Ngày:** 19/09/2026  

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Quy chế, Quy định và Hướng dẫn Đăng ký học phần & Công tác Cố vấn học tập tại các trường Đại học (IUH, UIT, UEH, HUFLIT).

**Tại sao nhóm chọn chủ đề này?**
> Đăng ký học phần và tư vấn kế hoạch học tập là nghiệp vụ học vụ cốt lõi, diễn ra định kỳ mỗi học kỳ và có tính ràng buộc pháp lý cao đối với sinh viên và giảng viên. Nhóm chọn chủ đề này vì các văn bản quy định chứa đựng nhiều con số, điều kiện tiên quyết, hạn mức tín chỉ và quy trình xử lý ngoại lệ rõ ràng, là tập ngữ cảnh lý tưởng để xây dựng hệ thống hỏi đáp tự động RAG và kiểm thử độ chính xác của các chiến lược truy xuất.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Đăng ký học phần — UEH Phân hiệu Vĩnh Long | https://hotro.ueh.edu.vn/bai-viet/hoc-phan-1736 | 2026-09-19 / not-stated | 4,247 | `audience: student`, `department: academic-affairs`, `category: registration`, `language: vi` |
| 2 | Hướng dẫn đăng ký học phần — UIT | https://daa.uit.edu.vn/27-huong-dan-dang-ky-hoc-phan-cho-sinh-vien | 2026-09-19 / 2023-08 | 1,814 | `audience: student`, `department: academic-affairs`, `category: registration`, `language: vi` |
| 3 | Quy chế đào tạo tín chỉ IUH 2025 (Điều 6: Đăng ký học phần) | https://camnang.iuh.edu.vn/quy-che-dao-tao-theo-he-thong-tin-chi.php | 2026-09-19 / 2025 | 4,453 | `audience: student`, `department: academic-affairs`, `category: registration`, `language: vi` |
| 4 | Hướng dẫn đăng ký học phần — IUH (Cẩm nang người học) | https://camnang.iuh.edu.vn/huong-dan-dang-ky-hoc-phan.php | 2026-09-19 / not-stated | 2,071 | `audience: student`, `department: academic-affairs`, `category: registration`, `language: vi` |
| 5 | Cách đăng ký học phần — HUFLIT | https://huflit.edu.vn/vi/tin-tuc/cach-dang-ky-hoc-phan/ | 2026-09-19 / 2026-05-16 | 11,639 | `audience: student`, `department: academic-affairs`, `category: registration`, `language: vi` |
| 6 | Quy định công tác tư vấn học tập cho sinh viên ĐHCQ — UEH | https://daotao.ueh.edu.vn/quy-dinh-cong-tac-tu-van-hoc-tap-doi-voi-sinh-vien-he-dai-hoc-chinh-quy/ | 2026-09-19 / 2016-10-24 | 13,693 | `audience: faculty`, `department: student-affairs`, `category: academic-advising`, `language: vi` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.
- [x] Tập tài liệu có ít nhất 2 giá trị `audience` khác nhau (`student` và `faculty`) để phục vụ kiểm thử tính năng lọc metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | `str` | `iuh-regulation-course-registration` | Định danh duy nhất tài liệu, dùng để liên kết trích dẫn và hỗ trợ xóa tài liệu (`delete_document`). |
| `audience` | `str` | `student`, `faculty` | Cho phép lọc đối tượng người dùng (pre-filtering), ngăn sinh viên truy xuất nhầm vào quy định nội bộ của giảng viên/cố vấn học tập. |
| `department` | `str` | `academic-affairs`, `student-affairs` | Khoanh vùng phạm vi đơn vị phụ trách nghiệp vụ (Phòng Đào tạo vs Phòng Công tác sinh viên). |
| `category` | `str` | `registration`, `academic-advising` | Phân loại nghiệp vụ cụ thể giúp hệ thống lọc nhanh theo nhóm tác vụ cần tra cứu. |
| `source_url` | `str` | `https://daa.uit.edu.vn/...` | Cung cấp đường dẫn nguồn chính thức phục vụ tính minh bạch (provenance) và trích dẫn câu trả lời. |
| `document_version` | `str` | `2025`, `2023-08` | Xác định phiên bản hoặc ngày ban hành hiệu lực để đánh giá độ mới của quy định. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu thực tế của nhóm (`chunk_size=300`):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| **IUH — Điều 6 Quy chế tín chỉ** | FixedSizeChunker (`fixed_size`) | 16 | 297.1 ký tự | Kém; thường xuyên bị cắt ngang giữa điều khoản hoặc cắt cụt từ |
| | SentenceChunker (`by_sentences`) | 12 | 368.7 ký tự | Rất tốt; mỗi chunk gồm 3 câu quy định trọn vẹn nghĩa |
| | RecursiveChunker (`recursive`) | 19 | 232.5 ký tự | Tốt; giữ được ranh giới các tiểu mục `a)`, `b)`, `c)` |
| **UEH Phân hiệu Vĩnh Long** | FixedSizeChunker (`fixed_size`) | 16 | 284.2 ký tự | Kém; bảng biểu và danh sách bước đăng ký bị xé lẻ |
| | SentenceChunker (`by_sentences`) | 12 | 351.5 ký tự | Tốt; gom các bước thao tác thành khối câu mạch lạc |
| | RecursiveChunker (`recursive`) | 19 | 221.8 ký tự | Rất tốt; ưu tiên cắt theo ngắt dòng `\n\n` của từng bước |
| **UIT — Hướng dẫn đăng ký** | FixedSizeChunker (`fixed_size`) | 7 | 276.3 ký tự | Trung bình; văn bản ngắn nên ít bị đứt đoạn hơn |
| | SentenceChunker (`by_sentences`) | 14 | 127.9 ký tự | Tốt; các câu ngắn được gom nhóm rõ ràng |
| | RecursiveChunker (`recursive`) | 9 | 200.0 ký tự | Tốt; phân chia hài hòa theo các heading mục lớn |

### Chiến lược của từng thành viên

**Thành viên 1 — Đào Thanh Trường (SentenceChunker)**
- **Loại chiến lược:** SentenceChunker (`by_sentences`, `max_sentences_per_chunk=3`)
- **Mô tả & lý do chọn cho chủ đề này:** Các văn bản quy chế học vụ cấu thành từ các điều khoản pháp lý, trong đó mỗi câu văn diễn đạt trọn vẹn một điều kiện ràng buộc hoặc quyền lợi. Việc nhóm theo 3 câu bảo đảm không làm đứt đôi bất kỳ câu chữ hay mốc thời gian nào, giúp ngữ nghĩa của đoạn văn bản hoàn chỉnh khi nhúng vào vector store.
- **Code snippet:**
```python
class SentenceChunker:
    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        raw_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+|(?<=\.)\n+', text.strip()) if s.strip()]
        chunks = []
        for i in range(0, len(raw_sentences), self.max_sentences_per_chunk):
            group = raw_sentences[i : i + self.max_sentences_per_chunk]
            chunk_str = " ".join(group).strip()
            if chunk_str:
                chunks.append(chunk_str)
        return chunks
```

**Thành viên 2 — Nguyễn Huy Hùng (FixedSizeChunker)**
- **Loại chiến lược:** FixedSizeChunker (`fixed_size`, `chunk_size=300`, `overlap=50`)
- **Mô tả & lý do chọn:** Chiến lược kích thước cố định tạo ra các vector có độ dài đồng đều nhất, tối ưu hiệu quả tính toán tích vô hướng. Độ chồng lấn 50 ký tự nhằm cứu vãn các từ khóa hoặc câu bị đứt đoạn ở ranh giới cắt.
- **Code snippet:** Sử dụng lớp `FixedSizeChunker` chuẩn được cài đặt sẵn trong `src/chunking.py`.

**Thành viên 3 — Nguyễn Thế Hiển (RecursiveChunker)**
- **Loại chiến lược:** RecursiveChunker (`recursive`, `chunk_size=300`, bộ phân tách theo mục và tiêu đề)
- **Mô tả & lý do chọn:** Tận dụng cấu trúc phân tầng Markdown của quy chế (`\n\n` giữa các điều khoản, `\n` giữa các điểm, dấu chấm câu). Đây là chiến lược tự nhiên nhất cho văn bản có cấu trúc heading mục lục như quy chế đào tạo đại học.
- **Code snippet:** Sử dụng lớp `RecursiveChunker` với cơ chế đệ quy ưu tiên `["\n\n", "\n", ". ", " ", ""]` trong `src/chunking.py`.

### So Sánh Giữa Các Thành Viên (Thực nghiệm với OpenAI `text-embedding-3-small`)

Toàn bộ 6 văn bản quy chế đại học (corpus K4-L3A) được nạp và phân mảnh độc lập theo 3 chiến lược của 3 thành viên, sau đó đánh giá truy xuất trên cùng 5 câu hỏi benchmark:

| Tiêu chí so sánh | Thành viên 1: Đào Thanh Trường (`SentenceChunker`) | Thành viên 2: Nguyễn Huy Hùng (`FixedSizeChunker`) | Thành viên 3: Nguyễn Thế Hiển (`RecursiveChunker`) |
|---|:---:|:---:|:---:|
| **Cấu hình tham số** | `max_sentences=3` | `chunk_size=300, overlap=50` | `chunk_size=300, sep=['\n\n','\n','. ',' ']` |
| **Tổng số Chunks sinh ra** | **128 chunks** | **154 chunks** | **180 chunks** |
| **Độ dài chunk trung bình** | **294.0 ký tự** (Min: 31, Max: 1452) | **294.3 ký tự** (Min: 64, Max: 300) | **208.8 ký tự** (Min: 1, Max: 300) |
| **Độ chính xác Top-1** | **5 / 5 (100%)** | **4 / 5 (80%)** | **5 / 5 (100%)** |
| **Độ chính xác Top-3** | **5 / 5 (100%)** | **4 / 5 (80%)** | **5 / 5 (100%)** |
| **Điểm tương đồng TB (Score)** | **0.7001** | **0.7016** | **0.7055** |
| **Đánh giá chất lượng** | **Xuất sắc (9.5/10)** — Bảo toàn trọn vẹn ngữ pháp câu văn pháp lý. | **Khá (7.0/10)** — Cắt cụt câu văn; thất bại ở Câu 3 do xé lẻ bảng thao tác. | **Xuất sắc nhất (10/10)** — Phân tầng tự nhiên theo tiêu đề markdown, điểm score cao nhất. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **RecursiveChunker** và **SentenceChunker** vượt trội hoàn toàn so với FixedSizeChunker:
> 1. **FixedSizeChunker (Thành viên 2 — Nguyễn Huy Hùng) gặp lỗi nghiêm trọng ở Câu hỏi 3:** Do cắt cứng 300 ký tự bất chấp ranh giới câu, khối hướng dẫn menu "Xác nhận Đăng ký Học Phần" của UIT bị chẻ đôi, dẫn đến việc mô hình nhầm lẫn và trả về chunk của UEH Vĩnh Long (`ueh-vinh-long-course-registration_7`), làm mất tính chính xác (Top-1 và Top-3 đều SAI).
> 2. **SentenceChunker (Thành viên 1 — Đào Thanh Trường):** Đạt độ chính xác tuyệt đối 5/5 (100%) vì luôn giữ trọn vẹn từng câu quy định (không bao giờ chẻ đôi câu chữ hay mốc thời gian).
> 3. **RecursiveChunker (Thành viên 3 — Nguyễn Thế Hiển):** Đạt độ chính xác 5/5 (100%) và có điểm tương đồng trung bình cao nhất (0.7055) nhờ bám sát cấu trúc Markdown heading `#`, `##` và ngắt đoạn `\n\n`.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng từ corpus; **ít nhất 1 câu (Câu 5)** cần lọc metadata mới trả lời chuẩn xác.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Theo Quy chế đào tạo tín chỉ IUH năm 2025, khối lượng học tập tối thiểu và tối đa sinh viên phải đăng ký trong một học kỳ chính (trừ học kỳ cuối) là bao nhiêu tín chỉ? | Khối lượng học tập mỗi sinh viên phải đăng ký trong mỗi học kỳ chính (trừ học kỳ cuối) tối thiểu là 12 tín chỉ và tối đa là 30 tín chỉ. | `iuh-regulation-course-registration` (Điều 6, Khoản 1b) |
| 2 | Sinh viên UEH Phân hiệu Vĩnh Long có thể đăng nhập vào cổng portal sinh viên bằng những cách nào? | Có 2 cách: Cách 1 dùng Mã sinh viên và Mật khẩu; Cách 2 đăng nhập bằng Google với Email sinh viên tên miền @st.ueh.edu.vn và Mật khẩu. | `ueh-vinh-long-course-registration` (Mục Đăng nhập portal) |
| 3 | Để xác nhận lớp học phần được hỗ trợ đăng ký từ Phòng Đào tạo tại UIT, sinh viên cần thực hiện bước đầu tiên vào menu nào? | Sinh viên truy cập trang dkhp.uit.edu.vn và chọn menu "Xác nhận Đăng ký Học Phần". | `uit-course-registration` (Mục 2. Xác nhận lớp) |
| 4 | Tại IUH, sau khi học phần đã được triển khai giảng dạy, Nhà trường có giải quyết cho sinh viên rút bớt học phần và hoàn phí không? | Khi học phần đã được triển khai giảng dạy, Nhà trường không chấp thuận cho sinh viên rút bớt các học phần và không giải quyết hoàn phí, rút phí. | `iuh-regulation-course-registration` (Điều 6, Khoản 4d) |
| 5 *(Lọc audience="faculty")* | Theo quy định UEH, nhiệm vụ của Cố vấn học tập (giảng viên) trong công tác tư vấn kế hoạch học tập và đăng ký học phần cho sinh viên là gì? | Tư vấn cách thức xây dựng và điều chỉnh kế hoạch học tập phù hợp với năng lực, hoàn cảnh; hướng dẫn cách thức đăng ký học phần ở từng học kỳ để hoàn thành kế hoạch học tập. | `ueh-academic-advising-regulation` (Điều 4, Khoản 3) |

### Tổng hợp chất lượng truy xuất đối chiếu 3 thành viên

| # | Câu hỏi | `SentenceChunker` (Đào Thanh Trường) | `FixedSizeChunker` (Nguyễn Huy Hùng) | `RecursiveChunker` (Nguyễn Thế Hiển) | Chiến lược tối ưu |
|---|---------|:---:|:---:|:---:|---|
| 1 | Khối lượng tín chỉ tối thiểu/tối đa IUH | **ĐÚNG** (Score: 0.7654) | **ĐÚNG** (Score: 0.7570) | **ĐÚNG** (Score: 0.7589) | Cả 3 đều tốt (Điều 6.1b) |
| 2 | Các cách đăng nhập portal UEH Vĩnh Long | **ĐÚNG** (Score: 0.6470) | **ĐÚNG** (Score: 0.6826) | **ĐÚNG** (Score: 0.7192) | `RecursiveChunker` cao điểm nhất |
| 3 | Bước vào menu xác nhận đăng ký UIT | **ĐÚNG** (Score: 0.6755) | **SAI** (Nhầm sang UEH Vĩnh Long, 0.6585) | **ĐÚNG** (Score: 0.6752) | `SentenceChunker` & `RecursiveChunker` |
| 4 | Quy định rút học phần & hoàn phí IUH | **ĐÚNG** (Score: 0.6423) | **ĐÚNG** (Score: 0.6556) | **ĐÚNG** (Score: 0.6511) | Cả 3 đều đạt Top-1 Điều 6.4d |
| 5 | Nhiệm vụ tư vấn đăng ký học phần CVHT UEH | **ĐÚNG** (Score: 0.7702) | **ĐÚNG** (Score: 0.7544) | **ĐÚNG** (Score: 0.7232) | `SentenceChunker` đạt score cao nhất |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **Lọc bằng metadata cực kỳ hữu ích, thể hiện rõ nhất ở Câu hỏi số 5.** Nếu không áp dụng bộ lọc `metadata_filter={"audience": "faculty"}`, câu hỏi "nhiệm vụ tư vấn đăng ký học phần" sẽ dễ bị trả về các chunk hướng dẫn đăng ký học phần của sinh viên (do tần suất từ khóa "đăng ký học phần" ở tài liệu sinh viên cao hơn). Nhờ có bộ lọc `audience="faculty"`, không gian tìm kiếm được cô lập hoàn toàn vào văn bản quy định dành cho giảng viên/cố vấn học tập, đưa tài liệu `ueh-academic-advising-regulation` lên vị trí Top-1 chính xác tuyệt đối trên cả 3 chiến lược.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. **Tác động của chiến lược chunking đến ngữ nghĩa:** Cắt đoạn cứng theo số ký tự (`FixedSizeChunker`) thường xuyên làm cụt từ hoặc đứt gãy điều kiện pháp lý; trong khi `SentenceChunker` và `RecursiveChunker` bảo tồn trọn vẹn câu văn và phân cấp điều khoản.  
> 2. **Sức mạnh của Metadata Pre-filtering:** Trong môi trường đại học với nhiều đối tượng người dùng khác nhau (sinh viên, giảng viên, cán bộ học vụ), việc phân loại và lọc theo `audience` giúp loại bỏ hoàn toàn nhiễu và trả về câu trả lời chính xác cho từng vai trò.  
> 3. **Hạn chế của mô hình nhúng giả lập (Mock Embedder):** Mock embedder dựa trên hash MD5 không thể hiện được sự tương đồng ngữ nghĩa thực sự, khẳng định vai trò sống còn của các mô hình Neural Embedding đa ngôn ngữ trong thực tế.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một bộ văn bản nguồn nhưng ba thành viên sử dụng ba chiến lược chia đoạn khác nhau đã dẫn đến sự phân mảnh dữ liệu hoàn toàn khác biệt: `FixedSizeChunker` sinh ra nhiều đoạn bị mất ngữ cảnh; `SentenceChunker` đảm bảo tính hoàn chỉnh của ngữ pháp; còn `RecursiveChunker` giữ được cấu trúc phân đoạn tự nhiên của văn bản. Việc thử nghiệm song song giúp nhóm nhìn thấy rõ ràng ưu nhược điểm định lượng của từng giải pháp.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ thiết kế thêm trường metadata `school` hoặc `campus` để hỗ trợ lọc theo từng trường đại học cụ thể, tránh việc câu hỏi về IUH bị gợi ý nhầm sang quy định của HUFLIT hay UIT khi không kèm tên trường. Đồng thời, nhóm sẽ bổ sung cơ chế chunking kết hợp (Hybrid Chunking): trước tiên tách theo cấu trúc tiêu đề điều/khoản, sau đó chia nhỏ tiếp theo câu nếu điều khoản đó quá dài.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
