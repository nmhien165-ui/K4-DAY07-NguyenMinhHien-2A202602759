# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Minh Hiển
**Nhóm:** Tôi yêu VinUni
**Ngày:** 2026-09-19

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector văn bản có hướng gần giống nhau trong không gian embedding, thường thể hiện hai đoạn có nội dung hoặc ý định gần nhau dù cách dùng từ có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: Sinh viên có thể gia hạn sách trực tuyến.
- Câu B: Người học được phép kéo dài thời gian mượn sách qua mạng.
- Tại sao tương đồng: Hai câu cùng nói về đối tượng người học, hành động gia hạn sách và hình thức trực tuyến.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Thư viện mở cửa lúc chín giờ.
- Câu B: Python là một ngôn ngữ lập trình.
- Tại sao khác: Hai câu thuộc hai chủ đề khác nhau và không có cùng ý định ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine tập trung vào hướng vector nên ít bị ảnh hưởng bởi độ lớn vector hoặc độ dài văn bản. Khoảng cách Euclid phụ thuộc cả hướng và độ lớn, nên hai câu cùng ý nhưng có norm khác nhau có thể bị đánh giá xa nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* `ceil((10.000 - 50) / (500 - 50)) = ceil(9.950 / 450) = ceil(22,11)`.
> *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số chunk tăng thành `ceil((10.000 - 100) / (500 - 100)) = 25`. Overlap lớn hơn giúp giữ ngữ cảnh ở ranh giới giữa các chunk, nhưng làm tăng dung lượng lưu trữ và chi phí embedding.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Fixed-Size Chunking của Nguyễn Huy Hùng là baseline dễ triển khai và có kích thước dự đoán được, nhưng có thể cắt ngang phần giải thích. Sentence-Based Chunking của Đào Thanh Trường dùng ranh giới câu tự nhiên nên dễ đọc hơn, nhưng kích thước chunk kém đồng đều và có thể dài khi nhiều câu dài được ghép lại.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Recursive Chunking với `chunk_size=300` là chiến lược cá nhân của tôi vì phù hợp với cấu trúc phân tầng Markdown của các quy chế. Thuật toán ưu tiên `\n\n`, `\n`, `. `, khoảng trắng rồi ký tự; base case là đoạn không vượt 300 ký tự, còn khi hết separator thì cắt cứng theo số ký tự.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi tài liệu được sao chép metadata, bổ sung `doc_id`, tạo ID duy nhất và embedding một lần khi thêm. Khi tìm kiếm, query được embed, tính dot product với các embedding đã lưu, sắp xếp điểm giảm dần rồi lấy tối đa `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Tôi lọc metadata trước khi tính điểm để tài liệu sai đối tượng không chiếm vị trí top-k. Khi xóa, store tìm và loại toàn bộ record có cùng `metadata["doc_id"]`, rồi trả về `True` nếu thực sự có dữ liệu bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Agent lấy top-k chunk, đánh số từng nguồn rồi chèn vào phần `NGỮ CẢNH`, tách rõ với `CÂU HỎI`. Prompt yêu cầu chỉ trả lời bằng dữ liệu trong ngữ cảnh và nói rõ khi thiếu thông tin, sau đó gọi `llm_fn` được truyền vào.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
> python -m pytest tests -v
============================= test session starts =============================
platform win32 -- Python 3.11.7, pytest-9.1.1, pluggy-1.6.0
collected 42 items

tests/test_solution.py ..........................................         [100%]

============================= 42 passed in 0.16s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | IUH yêu cầu đăng ký tối thiểu 12 tín chỉ. | Khối lượng học tập tối thiểu tại IUH là 12 tín chỉ. | cao | -0,1166 | Không |
| 2 | Sinh viên UIT phải xác nhận lớp được hỗ trợ. | Không xác nhận tại UIT sẽ bị xóa đăng ký học phần. | cao | -0,1650 | Không |
| 3 | Sinh viên đăng ký học phần bổ sung. | Trời hôm nay có mưa lớn. | thấp | -0,0393 | Đúng |
| 4 | Cố vấn hướng dẫn sinh viên đăng ký học phần. | CVHT hỗ trợ cách đăng ký môn học từng học kỳ. | cao | -0,0133 | Không |
| 5 | HUFLIT cho phép chuyển nhóm lớp. | Python là ngôn ngữ lập trình. | thấp | -0,0635 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 1 và cặp 2 có nội dung gần nhau nhưng vẫn nhận điểm âm. Nguyên nhân là `MockEmbedder` sinh vector từ hash để kiểm tra luồng code chứ không học quan hệ ngữ nghĩa, nên phù hợp cho unit test nhưng không phù hợp để đánh giá chất lượng retrieval thực tế.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Theo Quy chế đào tạo tín chỉ IUH năm 2025, khối lượng học tập tối thiểu và tối đa sinh viên phải đăng ký trong một học kỳ chính (trừ học kỳ cuối) là bao nhiêu tín chỉ? | Điều 6, Khoản 1b quy định giới hạn tín chỉ IUH | 0,7589 | Có | Tối thiểu 12 tín chỉ và tối đa 30 tín chỉ. |
| 2 | Sinh viên UEH Phân hiệu Vĩnh Long có thể đăng nhập vào cổng portal sinh viên bằng những cách nào? | Mục Đăng nhập portal UEH Vĩnh Long | 0,7192 | Có | Có hai cách: dùng Mã sinh viên và Mật khẩu; hoặc đăng nhập Google bằng email sinh viên `@st.ueh.edu.vn` và mật khẩu. |
| 3 | Để xác nhận lớp học phần được hỗ trợ đăng ký từ Phòng Đào tạo tại UIT, sinh viên cần thực hiện bước đầu tiên vào menu nào? | Mục 2 — Xác nhận lớp được hỗ trợ của UIT | 0,6752 | Có | Truy cập `dkhp.uit.edu.vn` và vào menu “Xác nhận Đăng ký Học Phần”. |
| 4 | Tại IUH, sau khi học phần đã được triển khai giảng dạy, Nhà trường có giải quyết cho sinh viên rút bớt học phần và hoàn phí không? | Điều 6, Khoản 4d về rút học phần IUH | 0,6511 | Có | Không; Nhà trường không chấp thuận rút bớt học phần và không giải quyết hoàn phí hoặc rút phí. |
| 5 | Theo quy định UEH, nhiệm vụ của Cố vấn học tập (giảng viên) trong công tác tư vấn kế hoạch học tập và đăng ký học phần cho sinh viên là gì? | Điều 4, Khoản 3 của quy định tư vấn học tập UEH | 0,7232 | Có | Tư vấn xây dựng và điều chỉnh kế hoạch học tập phù hợp với năng lực, hoàn cảnh; hướng dẫn đăng ký học phần từng học kỳ để hoàn thành kế hoạch. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> SentenceChunker của Đào Thanh Trường cho thấy việc giữ trọn câu pháp lý giúp đạt 5/5 câu chính xác, còn FixedSizeChunker của Nguyễn Huy Hùng cho thấy overlap không hoàn toàn khắc phục được việc cắt cứng giữa quy trình. So sánh này giúp tôi xác nhận RecursiveChunker phù hợp nhất với corpus có heading và điều khoản: đạt 5/5, đồng thời có điểm tương đồng trung bình cao nhất là 0,7055.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
