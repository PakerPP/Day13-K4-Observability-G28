# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: HighLatencyP95
- Severity: Critical
- SLI/SLO liên quan: `latency_p95_ms` (`config/slo.yaml`), objective ≤ 3000ms
- Điều kiện và thời gian duy trì: `latency_p95_ms > 3000` liên tục trong 5 phút (đo trên panel `latency` của `config/dashboard.yaml`, cửa sổ trượt 60 phút)
- Ảnh hưởng tới người dùng: Câu trả lời chat chậm rõ rệt, trải nghiệm hỏi-đáp bị treo, có nguy cơ client/API gateway timeout nếu kéo dài
- Ba bước kiểm tra đầu tiên:
  1. Mở panel `latency` trên dashboard, xác nhận khoảng thời gian P95 vượt ngưỡng và so sánh với panel `traffic` để loại trừ do tăng tải đột biến
  2. Mở một trace rơi vào khoảng thời gian đó trên Langfuse, so sánh thời lượng từng span (`retrieve` vs `generate`) để xác định span nào phình to bất thường
  3. Lấy `correlation_id` của request đó, tìm log `request_received`/`response_sent` tương ứng trong `data/logs.jsonl` để đối chiếu `latency_ms` và context (`feature`, `session_id`)
- Mitigation tạm thời: Bật circuit breaker/timeout ngắn hơn cho bước retrieval nếu span RAG là nguyên nhân; thông báo người dùng về độ trễ tạm thời qua status page
- Owner: SRE on-call (Thành viên D)

## Alert 2

- Tên: ElevatedErrorRate
- Severity: Critical
- SLI/SLO liên quan: `error_rate_pct` (`config/slo.yaml`), objective ≤ 2%
- Điều kiện và thời gian duy trì: `error_rate_pct > 2%` liên tục trong 5 phút, tính theo `count(request_failed) / count(request_received) * 100` trên panel `errors`
- Ảnh hưởng tới người dùng: Một phần request nhận HTTP 500 thay vì câu trả lời, mất niềm tin vào tính sẵn sàng của API
- Ba bước kiểm tra đầu tiên:
  1. Mở panel `errors`, xem breakdown `error_type` để biết lỗi tập trung ở loại nào (ví dụ `RuntimeError` từ vector store timeout)
  2. Mở trace của một request lỗi gần nhất, xác định span nào raise exception (RAG retrieval hay LLM generation)
  3. Tìm log `request_failed` cùng `correlation_id` trong `data/logs.jsonl`, đọc `payload.detail` để lấy thông điệp lỗi cụ thể làm bằng chứng root cause
- Mitigation tạm thời: Bật fallback trả lời chung khi retrieval lỗi (không raise ra người dùng); tạm giảm tải bằng cách giới hạn concurrency của load test/production traffic
- Owner: API on-call (Thành viên A)

## Alert 3

- Tên: QualityScoreDegraded
- Severity: Warning
- SLI/SLO liên quan: `quality_score_avg` (`config/slo.yaml`), objective ≥ 0.75
- Điều kiện và thời gian duy trì: `quality_score_avg < 0.75` liên tục trong 15 phút (đo trên panel `quality`, trung bình cửa sổ 60 phút)
- Ảnh hưởng tới người dùng: Câu trả lời ngắn hơn, không bám sát tài liệu RAG, hoặc chứa nội dung bị redact PII — chất lượng trả lời giảm dù request vẫn thành công (không phải lỗi cứng)
- Ba bước kiểm tra đầu tiên:
  1. Mở panel `quality`, xác nhận xu hướng giảm và đối chiếu với panel `tokens`/`errors` để loại trừ nguyên nhân do `cost_spike` (tăng output token bất thường) hoặc do rate PII-redaction cao
  2. Mở vài trace có `quality_score` thấp trong khoảng thời gian đó, kiểm tra `doc_count` trong generation metadata — quality thấp thường đi kèm `doc_count = 0` (RAG không match tài liệu)
  3. Đối chiếu `payload.answer_preview` trong log `response_sent` xem có chứa `[REDACTED_...]` không — nếu có, quality giảm do PII bị scrub làm câu trả lời mất ý nghĩa
- Mitigation tạm thời: Tạm thời nới `_heuristic_quality` không trừ điểm khi PII bị redact hợp lệ (đây là hành vi đúng, không phải lỗi); mở rộng `CORPUS` trong `app/mock_rag.py` nếu nhiều câu hỏi không match tài liệu nào
- Owner: SRE on-call (Thành viên D)
