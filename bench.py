from __future__ import annotations

import math
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

from src import Document, EmbeddingStore, RecursiveChunker


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data" / "course-registration"
OUTPUT_FILE = PROJECT_DIR / "ket_qua_benchmark.txt"

# Chiến lược cá nhân: chỉ thay dòng này khi muốn thử chunker khác.
CHUNKER = RecursiveChunker(
    chunk_size=300,
    separators=["\n\n", "\n", ". ", " "],
)

TOKEN_PATTERN = re.compile(r"\w+", flags=re.UNICODE)
STOP_WORDS = {
    "bi", "cac", "can", "cho", "co", "cong", "cua", "dinh", "duoc", "gi",
    "giang", "hoc", "khong", "la", "lam", "mot", "nhiem", "nhung", "o", "phai",
    "quy", "sau", "sinh", "tai", "theo", "thi", "trong", "truoc", "tu", "va",
    "van", "ve", "vien", "voi", "vu",
}

# Cùng 5 câu hỏi và đáp án chuẩn trong report/REPORT_NHOM.md.
BENCHMARK_CASES = [
    {
        "query": (
            "Theo Quy chế đào tạo tín chỉ IUH năm 2025, khối lượng học tập tối thiểu "
            "và tối đa sinh viên phải đăng ký trong một học kỳ chính (trừ học kỳ cuối) "
            "là bao nhiêu tín chỉ?"
        ),
        "expected_doc_id": "iuh-regulation-course-registration",
        "metadata_filter": None,
        "answer_markers": ("tối thiểu là 12 tín chỉ", "tối đa là 30 tín chỉ"),
        "gold_answer": "Tối thiểu 12 tín chỉ và tối đa 30 tín chỉ.",
    },
    {
        "query": (
            "Sinh viên UEH Phân hiệu Vĩnh Long có thể đăng nhập vào cổng portal sinh viên "
            "bằng những cách nào?"
        ),
        "expected_doc_id": "ueh-vinh-long-course-registration",
        "metadata_filter": None,
        "answer_markers": ("mã sinh viên và mật khẩu", "@st.ueh.edu.vn"),
        "gold_answer": (
            "Dùng Mã sinh viên và Mật khẩu; hoặc đăng nhập Google bằng email sinh viên "
            "@st.ueh.edu.vn và mật khẩu."
        ),
    },
    {
        "query": (
            "Để xác nhận lớp học phần được hỗ trợ đăng ký từ Phòng Đào tạo tại UIT, "
            "sinh viên cần thực hiện bước đầu tiên vào menu nào?"
        ),
        "expected_doc_id": "uit-course-registration",
        "metadata_filter": None,
        "answer_markers": ("xác nhận đăng ký học phần",),
        "gold_answer": (
            "Truy cập dkhp.uit.edu.vn và chọn menu “Xác nhận Đăng ký Học Phần”."
        ),
    },
    {
        "query": (
            "Tại IUH, sau khi học phần đã được triển khai giảng dạy, Nhà trường có giải quyết "
            "cho sinh viên rút bớt học phần và hoàn phí không?"
        ),
        "expected_doc_id": "iuh-regulation-course-registration",
        "metadata_filter": None,
        "answer_markers": ("không chấp thuận", "không giải quyết hoàn phí"),
        "gold_answer": (
            "Không; Nhà trường không chấp thuận rút bớt học phần và không giải quyết hoàn phí, "
            "rút phí."
        ),
    },
    {
        "query": (
            "Theo quy định UEH, nhiệm vụ của Cố vấn học tập (giảng viên) trong công tác tư vấn "
            "kế hoạch học tập và đăng ký học phần cho sinh viên là gì?"
        ),
        "expected_doc_id": "ueh-academic-advising-regulation",
        "metadata_filter": {"audience": "faculty"},
        "answer_markers": (
            "điều chỉnh kế hoạch học tập",
            "đăng ký học phần ở từng học kỳ",
        ),
        "gold_answer": (
            "Tư vấn xây dựng và điều chỉnh kế hoạch học tập phù hợp; hướng dẫn đăng ký học phần "
            "từng học kỳ để hoàn thành kế hoạch."
        ),
    },
]


def tokenize(text: str) -> list[str]:
    """Chuẩn hóa tiếng Việt và tách token cho TF-IDF cục bộ."""
    normalized = unicodedata.normalize("NFD", text.lower()).replace("đ", "d")
    normalized = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return [token for token in TOKEN_PATTERN.findall(normalized) if token not in STOP_WORDS]


class TfidfEmbedder:
    """Embedding TF-IDF gọn nhẹ, chạy offline và cho kết quả tái lập được."""

    def __init__(self, texts: list[str]) -> None:
        token_sets = [set(tokenize(text)) for text in texts]
        vocabulary = sorted(set().union(*token_sets)) if token_sets else []
        self.index = {token: index for index, token in enumerate(vocabulary)}
        document_count = max(1, len(texts))
        document_frequency = Counter(token for token_set in token_sets for token in token_set)
        self.idf = {
            token: math.log((1 + document_count) / (1 + document_frequency[token])) + 1
            for token in vocabulary
        }

    def __call__(self, text: str) -> list[float]:
        counts = Counter(tokenize(text))
        vector = [0.0] * len(self.index)
        for token, count in counts.items():
            if token in self.index:
                vector[self.index[token]] = (1 + math.log(count)) * self.idf[token]
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


def parse_document(path: Path) -> tuple[dict[str, str], str]:
    """Tách YAML frontmatter đơn giản khỏi nội dung Markdown."""
    raw = path.read_text(encoding="utf-8")
    metadata: dict[str, str] = {}
    content = raw
    if raw.startswith("---\n"):
        _, frontmatter, content = raw.split("---", 2)
        for line in frontmatter.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            clean_value = re.sub(r"\s+#.*$", "", value).strip().strip('"')
            metadata[key.strip()] = clean_value
    return metadata, content.strip()


def build_chunks() -> tuple[list[Document], int]:
    """Đọc corpus và truyền metadata của tài liệu xuống từng chunk."""
    paths = sorted(DATA_DIR.glob("*.md"))
    chunks: list[Document] = []
    for path in paths:
        metadata, content = parse_document(path)
        doc_id = metadata.get("doc_id", path.stem)
        for index, chunk in enumerate(CHUNKER.chunk(content)):
            chunk_metadata = {**metadata, "doc_id": doc_id, "chunk_index": index}
            chunks.append(
                Document(
                    id=f"{doc_id}#{index}",
                    content=chunk,
                    metadata=chunk_metadata,
                )
            )
    return chunks, len(paths)


def run_benchmark() -> str:
    """Chạy 5 truy vấn và trả về báo cáo văn bản."""
    chunks, document_count = build_chunks()
    if not chunks:
        raise RuntimeError(f"Không tìm thấy tài liệu .md trong {DATA_DIR}")

    embedder = TfidfEmbedder([chunk.content for chunk in chunks])
    store = EmbeddingStore("nguyen-the-hien-benchmark", embedding_fn=embedder)
    store.add_documents(chunks)

    lines = [
        "KẾT QUẢ BENCHMARK CÁ NHÂN — NGUYỄN THẾ HIỂN",
        "Chiến lược: RecursiveChunker(chunk_size=300)",
        "Embedding: local TF-IDF (offline, deterministic)",
        f"Corpus: {document_count} tài liệu, {len(chunks)} chunks",
        "",
    ]
    relevant_count = 0

    for number, case in enumerate(BENCHMARK_CASES, start=1):
        results = store.search_with_filter(
            case["query"],
            top_k=3,
            metadata_filter=case["metadata_filter"],
        )
        combined_context = " ".join(result["content"].lower() for result in results)
        correct_document_found = any(
            result["metadata"].get("doc_id") == case["expected_doc_id"]
            for result in results
        )
        answer_found = all(marker in combined_context for marker in case["answer_markers"])
        relevant = correct_document_found and answer_found
        relevant_count += int(relevant)

        lines.extend(
            [
                f"Câu {number}: {case['query']}",
                f"Filter: {case['metadata_filter']}",
                f"Gold answer: {case['gold_answer']}",
                f"Relevant in top-3: {'Có' if relevant else 'Không'}",
                "Top-3:",
            ]
        )
        for rank, result in enumerate(results, start=1):
            metadata = result["metadata"]
            preview = " ".join(result["content"].split())[:180]
            lines.append(
                f"  {rank}. {metadata.get('doc_id')}#{metadata.get('chunk_index')} "
                f"| score={result['score']:.4f} | {preview}"
            )
        lines.append("")

    lines.append(f"TỔNG KẾT: {relevant_count}/5 câu có chunk trả lời được trong top-3.")
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    report = run_benchmark()
    OUTPUT_FILE.write_text(report, encoding="utf-8")
    print(report, end="")
    print(f"Đã lưu kết quả: {OUTPUT_FILE.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
