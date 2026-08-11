# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100 (baseline ban đầu 30/100 trước khi hoàn thiện middleware/PII/log enrichment)
- Tổng số traces: 19
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard: https://cloud.langfuse.com/project/cmsod0gjn02ctad0dqtnilg3g/dashboards

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

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: HỢP LỆ: 6/6 panel có trong dashboard contract.
- Evidence dashboard: submission/evidence/dashboard.png
- SLO đã chọn và lý do (chi tiết trong `config/slo.yaml`):
  - `latency_p95_ms` ≤ 3000ms — baseline thực đo ~1214ms, biên độ ~2.5x để chịu tải cao và incident `rag_slow` (+~2500ms/request) mà không báo động liên tục.
  - `error_rate_pct` ≤ 2% — baseline 0% lỗi; 2% phản ánh mức chấp nhận được cho API demo dùng fake LLM/RAG.
  - `daily_cost_usd` ≤ 2.5 USD/cửa sổ 60 phút — baseline ~0.002 USD/request; đủ chặt để bắt được `cost_spike` (×4 output token).
  - `quality_score_avg` ≥ 0.75 — baseline đo được 0.88; cho phép một phần câu trả lời bị redact PII hoặc thiếu tài liệu RAG vẫn nằm trong ngưỡng.
  - Cả 4 giá trị khớp đúng threshold tương ứng trong `config/dashboard.yaml` (đối chiếu tự động bằng `scripts/validate_alerts.py`).
- Alert rules và runbook (`config/alert_rules.yaml` + `docs/alerts.md`):
  - `HighLatencyP95` (critical) — `latency_p95_ms > 3000 for 5m`, runbook `docs/alerts.md#alert-1`.
  - `ElevatedErrorRate` (critical) — `error_rate_pct > 2 for 5m`, runbook `docs/alerts.md#alert-2`. Đã kiểm chứng field `error_rate_pct` (từ `app/metrics.py::calculate_error_rate_pct`) phản ánh đúng khi trigger incident `tool_fail` (100% khi 1/1 request lỗi, `error_breakdown={"RuntimeError": 1}`).
  - `QualityScoreDegraded` (warning) — `quality_score_avg < 0.75 for 15m`, runbook `docs/alerts.md#alert-3`.
  - Cả 3 alert đều symptom-based (dựa trên SLI/SLO), không tham chiếu tên incident nội bộ (`rag_slow`, `tool_fail`, `cost_spike`) — kiểm tra tự động bằng `scripts/validate_alerts.py`.
  - Bonus: `scripts/validate_alerts.py` tự động đối chiếu SLO ↔ dashboard threshold và kiểm tra runbook anchor tồn tại, chạy: `python scripts/validate_alerts.py` → `HOP LE`.

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
| Nguyễn Trung Hiếu | Thành viên B (Security Engineer) |  | Đã chạy baseline score |
