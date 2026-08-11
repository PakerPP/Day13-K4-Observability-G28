# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: G28
- Repository URL: https://github.com/PakerPP/Day13-K4-Observability-G28
- Commit SHA cuối:
- Thành viên và vai trò:
  - Trần Trung Kiên - Thành viên A (API & Middleware)
  - Nguyễn Trung Hiếu - Thành viên B (Security Engineer)
  - Nguyễn Quang Sơn - Thành viên C (Metrics & Dashboard)
  - Đặng Ngọc Anh - Thành viên D (SRE & Alerts Engineer)
  - Bùi Xuân Tùng - Thành viên E (QA & Chief Investigator)

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100
- Tổng số traces: 19
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard: `dashboard.html` (chạy local tại `http://127.0.0.1:8501/dashboard.html`)

## 3. Logging và tracing

- Evidence correlation ID:
```json
{"service": "api", "payload": {"message_preview": "Summarize the monitoring policy for production logging"}, "event": "request_received", "user_id_hash": "97ce842ec69d", "session_id": "s03", "feature": "summary", "correlation_id": "req-fce754ea", "model": "claude-sonnet-4-5", "env": "dev", "level": "info", "ts": "2026-08-11T08:31:16.208541Z"}
```
- Evidence PII redaction:
```json
{"service": "api", "payload": {"message_preview": "Here is my phone [REDACTED_PHONE_VN], what should be logged?"}, "event": "request_received", "feature": "qa", "model": "claude-sonnet-4-5", "correlation_id": "req-7a4cdd93", "user_id_hash": "64f6ec689229", "session_id": "s05", "env": "dev", "level": "info", "ts": "2026-08-11T08:31:26.648811Z"}
```
- Evidence trace waterfall: `submission/evidence/trace waterfall.png`
- Giải thích một span đáng chú ý: Span `generation` (trong trace ID `req-7a4cdd93`) chiếm hơn 90% latency của toàn bộ request (~1029ms). Span này chịu trách nhiệm xử lý Prompt và sinh văn bản đầu ra thông qua mô hình `claude-sonnet-4-5` với 33 input tokens và 179 output tokens.  
```json
{"service": "api", "latency_ms": 1029, "tokens_in": 33, "tokens_out": 179, "cost_usd": 0.002784, "quality_score": 0.9, "payload": {"answer_preview": "..."}, "event": "response_sent", "feature": "qa", "model": "claude-sonnet-4-5", "correlation_id": "req-7a4cdd93", "user_id_hash": "64f6ec689229", "session_id": "s05", "env": "dev", "level": "info", "ts": "2026-08-11T08:31:27.681504Z"}
```
## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: HỢP LỆ: 6/6 panel có trong dashboard contract.
- Evidence dashboard:
  - `submission/evidence/dashboard-baseline.png`: dashboard baseline có đủ 6 nhóm chỉ số.
  - `submission/evidence/dashboard-rag-slow.png`: incident `rag_slow` làm P95 tăng lên 3,763 ms, vượt threshold 3,000 ms.
  - `submission/evidence/dashboard-tool-fail.png`: incident `tool_fail` cho error rate 25.00% và breakdown `RuntimeError: 10`.
- SLO đã chọn và lý do:
- Alert rules và runbook:

## 6. Điều tra challenge

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Trần Trung Kiên | Thành viên A (API & Middleware) | https://github.com/PakerPP/Day13-K4-Observability-G28/commit/0f6af13dfae720f2ee14c802cdeeea621fc6b7b9 | Cấu hình CorrelationIdMiddleware, xử lý PII Scrubbing, Log Enrichment |
| Nguyễn Trung Hiếu | Thành viên B (Security Engineer) |  | Đã chạy baseline score |


