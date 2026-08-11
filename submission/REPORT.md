# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: G28
- Repository URL: https://github.com/PakerPP/Day13-K4-Observability-G28
- Commit SHA cuối: sẽ cập nhật sau commit/push cuối cùng của `submission/REPORT.md` và evidence.
- Thành viên và vai trò:
  - Trần Trung Kiên - Thành viên A (API & Middleware)
  - Nguyễn Trung Hiếu - Thành viên B (Security Engineer)
  - Nguyễn Quang Sơn - Thành viên C (Metrics & Dashboard)
  - Đặng Ngọc Anh - Thành viên D (SRE & Alerts Engineer)
  - Bùi Xuân Tùng - Thành viên E (QA & Chief Investigator)

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100 (baseline ban đầu 30/100 trước khi hoàn thiện middleware/PII/log enrichment)
- Tổng số traces: tối thiểu 20 root traces trong Langfuse, cộng thêm các trace challenge/prompt mới trong quá trình QA.
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard: `dashboard.html` (chạy local tại `http://127.0.0.1:8501/dashboard.html`)

## 3. Logging và tracing

### QA baseline (2026-08-11, before team fixes)

- Test suite: `22 passed`; FastAPI emitted 2 deprecation warnings for `on_event`.
- Load test: 10/10 requests returned HTTP 200, but every response reported `x-request-id` as `MISSING`.
- `validate_logs.py`: 21 records analysed; 20 missing required fields; 20 missing context enrichment; 0 unique correlation IDs; 0 potential PII leaks; estimated score `30/100`.
- Follow-up owner: member A needs correlation-ID propagation and API log enrichment. Member B should rerun PII verification with explicit PII test input after the logging fix.

### Langfuse connection check (2026-08-11)

- Langfuse authentication check succeeded (`auth_check() = True`).
- Langfuse Tracing showed 20 root `run` observations after filtering `isRootObservation:true`; this exceeds the required minimum of 10 traces.
- Trace `5c44be51621241b6cc964785b9787f64` showed a waterfall with a `run` span and nested generation. Evidence included 1.03 s latency, $0.002754 cost, session `s10`, hashed user ID, environment `default`, and tags `lab`, `qa`, and `claude-sonnet-4-5`.
- Evidence: `submission/evidence/10 traces.png`, `submission/evidence/trace waterfall.png`, `submission/evidence/langfuse_load_test.txt`.

### CP1 post-pull verification (2026-08-11)

- Commit `0f6af13` implemented correlation-ID middleware and API log context enrichment.
- Test suite sau pull cuối: `25 passed, 2 warnings` (`submission/evidence/qa_pytest_pass.png`).
- A new 10-request load test returned HTTP 200 with a distinct `req-...` ID on every response.
- The newest batch contained 20 API logs; all 20 contained `correlation_id`, `user_id_hash`, `session_id`, `feature`, `model`, and `env`, with 10 unique correlation IDs.
- Fresh validator sau khi archive/clear log baseline: `100/100` (`submission/evidence/qa_validate_logs_100.png`). Dashboard validator: `HỢP LỆ: 6/6 panel` (`submission/evidence/qa_validate_dashboard_pass.png`).

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

- Prompt name: `day13-chat` (text prompt, giữ 3 biến `{{feature}}`, `{{docs}}`, `{{message}}`)
- Version/label baseline: version 1, labels `baseline` + `production` — nội dung `Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}`
- Version/label candidate: version 2, label `candidate` — thêm câu chỉ dẫn "Answer concisely in at most 3 sentences." vào cuối template
- Evidence UI: `submission/evidence/prompt_versions.png`, `submission/evidence/prompt_trace_baseline.png`, `submission/evidence/prompt_trace_candidate.png`.
- Trace ID của mỗi version:
  - `LANGFUSE_PROMPT_LABEL=baseline` (version 1) → trace `8d7578b5f23376661318a351047fa6c6`, metadata `prompt_label=baseline`, `prompt_version=1`, `prompt_source=langfuse`
  - `LANGFUSE_PROMPT_LABEL=candidate` (version 2) → trace `97d73126cd8bb61833166559fb531acb`, metadata `prompt_label=candidate`, `prompt_version=2`, `prompt_source=langfuse`
- Bằng chứng đổi label hoặc rollback (xác nhận qua Langfuse API, không chỉ log local):
  1. Đổi `production` từ version 1 sang version 2: trace `4f856cc895f981d1023d89c1a72a4be5` (`LANGFUSE_PROMPT_LABEL=production`) có metadata `prompt_version=2`.
  2. Rollback `production` từ version 2 về version 1: trace `1bf1b9e125e8958b8d63812a214282ab` (`LANGFUSE_PROMPT_LABEL=production`) có metadata `prompt_version=1`.
  3. Trạng thái label cuối cùng: `production` → version 1 (labels `['baseline', 'production']`), `candidate` vẫn trỏ version 2, xác nhận bằng `client.get_prompt('day13-chat', label='production').version == 1`.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: HỢP LỆ: 6/6 panel có trong dashboard contract. (chi tiết: `submission/evidence/validate_dashboard_result.txt`)
- Evidence dashboard:
  - `submission/evidence/dashboard-baseline.png`: dashboard baseline có đủ 6 nhóm chỉ số.
  - `submission/evidence/dashboard-rag-slow.png`: incident `rag_slow` làm P95 tăng lên 3,763 ms, vượt threshold 3,000 ms.
  - `submission/evidence/dashboard-tool-fail.png`: incident `tool_fail` cho error rate 25.00% và breakdown `RuntimeError: 10`.
- SLO đã chọn và lý do (chi tiết trong `config/slo.yaml`):
  - `latency_p95_ms` ≤ 3000ms — baseline thực đo ~1214ms, biên độ ~2.5x để chịu tải cao và incident `rag_slow` (+~2500ms/request) mà không báo động liên tục. Khớp với evidence `dashboard-rag-slow.png` (P95 thực tế vượt lên 3,763ms khi incident bật).
  - `error_rate_pct` ≤ 2% — baseline 0% lỗi; 2% phản ánh mức chấp nhận được cho API demo dùng fake LLM/RAG. Khớp với evidence `dashboard-tool-fail.png` (error rate thực tế 25% khi incident bật).
  - `daily_cost_usd` ≤ 2.5 USD/cửa sổ 60 phút — baseline ~0.002 USD/request; đủ chặt để bắt được `cost_spike` (×4 output token).
  - `quality_score_avg` ≥ 0.75 — baseline đo được 0.88; cho phép một phần câu trả lời bị redact PII hoặc thiếu tài liệu RAG vẫn nằm trong ngưỡng.
  - Cả 4 giá trị khớp đúng threshold tương ứng trong `config/dashboard.yaml` (đối chiếu tự động bằng `scripts/validate_alerts.py`).
- Alert rules và runbook (`config/alert_rules.yaml` + `docs/alerts.md`):
  - `HighLatencyP95` (critical) — `latency_p95_ms > 3000 for 5m`, runbook `docs/alerts.md#alert-1`.
  - `ElevatedErrorRate` (critical) — `error_rate_pct > 2 for 5m`, runbook `docs/alerts.md#alert-2`. Đã kiểm chứng field `error_rate_pct` (từ `app/metrics.py::calculate_error_rate_pct`) phản ánh đúng khi trigger incident `tool_fail` (100% khi 1/1 request lỗi, `error_breakdown={"RuntimeError": 1}`); evidence runtime `dashboard-tool-fail.png` cho thấy 25% error rate khi tải 10 request lỗi.
  - `QualityScoreDegraded` (warning) — `quality_score_avg < 0.75 for 15m`, runbook `docs/alerts.md#alert-3`.
  - Cả 3 alert đều symptom-based (dựa trên SLI/SLO), không tham chiếu tên incident nội bộ (`rag_slow`, `tool_fail`, `cost_spike`) — kiểm tra tự động bằng `scripts/validate_alerts.py`.
  - Bonus: `scripts/validate_alerts.py` tự động đối chiếu SLO ↔ dashboard threshold và kiểm tra runbook anchor tồn tại, chạy: `python scripts/validate_alerts.py` → `HOP LE`.

## 6. Điều tra challenge

- Challenge ID: `day13-k4-observability-v1` (cohort K4, incident chính thức `rag_slow`, seed 1304, `affected_feature=monitoring`, `latency_threshold_ms=2000`)
- Triệu chứng từ metrics/logs: Chạy `POST /incidents/rag_slow/enable` rồi gửi 5 query chính thức từ `config/challenge.json` với `--challenge --concurrency 5`. Output load test cho thấy 5 request `monitoring` đều HTTP 200 nhưng latency khoảng `14215ms` (`submission/evidence/challenge_load_test.png`). Log local sau đó cho thấy các request `monitoring` có `latency_ms` vượt ngưỡng challenge `2000ms`, ví dụ `req-3952654c` đạt `3585ms` (`submission/evidence/challenge_slow_log.png`).
- Trace ID liên quan: Langfuse trace `cadcfe5c5a3963b33a92c5421a5d8453` (session `k4-challenge-s01`), latency hiển thị 2.65s, tag `monitoring`, model `claude-sonnet-4-5`, waterfall `run -> generation` (`submission/evidence/challenge_trace_waterfall.png`).
- Log line/correlation ID liên quan: `correlation_id=req-025ef959` trong `data/logs.jsonl` cho session `k4-challenge-s01`:
  ```json
  {"service": "api", "latency_ms": 2650, "tokens_in": 45, "tokens_out": 116, "cost_usd": 0.001875, "quality_score": 0.8, "event": "response_sent", "session_id": "k4-challenge-s01", "feature": "monitoring", "correlation_id": "req-025ef959", "user_id_hash": "f00ba60b3772", "ts": "2026-08-11T03:25:32.061331Z"}
  ```
  Evidence log bổ sung: `req-3952654c` (session `k4-challenge-s02`) có `latency_ms=3585`, feature `monitoring`, khớp ảnh `challenge_slow_log.png`.
- Root cause: `app/mock_rag.py:18` — hàm `retrieve()` gọi `time.sleep(2.5)` khi `STATE["rag_slow"]` bật, mô phỏng bước truy vấn vector store bị chậm. Vì `LabAgent.run()` gọi `retrieve()` trước khi gọi LLM, toàn bộ 2.5s này cộng dồn vào latency tổng của request và được ghi nhận nguyên vẹn trong `response_sent.latency_ms` cũng như trong latency của Langfuse generation span.
- Fix action: Tắt incident bằng `POST /incidents/rag_slow/disable` (đã xác nhận qua log `incident_disabled`, `metrics.latency_p95` trở lại ~0 ngay sau đó vì server restart). Ở production, hướng fix tương ứng là thêm timeout ngắn cho bước retrieval (ví dụ 1s) kèm circuit breaker, để một vector store chậm không kéo toàn bộ request vượt SLO — đúng như mitigation đã ghi trong `docs/alerts.md#alert-1`.
- Preventive measure:
  1. Alert `HighLatencyP95` (`config/alert_rules.yaml`) sẽ bắt được triệu chứng này trong thực tế (`latency_p95_ms > 3000 for 5m`); với `rag_slow` chạy liên tục trên tải thật, P95 vượt xa ngưỡng này.
  2. Bổ sung timeout/circuit breaker cho `retrieve()` để giới hạn phần đóng góp tối đa của bước RAG vào latency tổng.
  3. Phát hiện phụ trong lúc điều tra: khi chạy 5 request đồng thời qua `ThreadPoolExecutor`, `correlation_id` trong metadata trace Langfuse (lấy từ `structlog.contextvars` tại `app/agent.py:39`) không khớp với `correlation_id` thật trong log JSONL của cùng session (ví dụ trace metadata ghi `req-025ef959` nhưng log ghi `req-ac645aff` cho session `k4-challenge-s01`) — dấu hiệu context bị chia sẻ giữa các thread khi nhiều request async chạy song song. Không ảnh hưởng tới kết luận root cause của challenge này (vẫn đối chiếu đúng bằng `session_id` và giá trị `latency_ms`), nhưng nên được nhóm sửa (ví dụ đọc `correlation_id` từ `request.state` truyền tường minh qua thay vì qua contextvars) trước khi dùng correlation_id trong trace metadata làm bằng chứng chính cho các điều tra sau này.

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Trần Trung Kiên | Thành viên A (API & Middleware) | https://github.com/PakerPP/Day13-K4-Observability-G28/commit/0f6af13dfae720f2ee14c802cdeeea621fc6b7b9 | Cấu hình CorrelationIdMiddleware, xử lý PII Scrubbing, Log Enrichment |
| Nguyễn Trung Hiếu | Thành viên B (Security Engineer) |  | Đã chạy baseline score |
| Nguyễn Quang Sơn | Thành viên C (Metrics & Dashboard): triển khai `error_rate_pct`, bổ sung unit test, thiết kế dashboard HTML 6 nhóm chỉ số và thu thập evidence baseline/`rag_slow`/`tool_fail`. | [63c2977](https://github.com/PakerPP/Day13-K4-Observability-G28/commit/63c2977) · [18c8bbb](https://github.com/PakerPP/Day13-K4-Observability-G28/commit/18c8bbb) | Cách tính error rate từ request thành công/lỗi, thiết kế dashboard theo log contract, và dùng metrics để xác nhận latency/error khi xảy ra incident. |
| Đặng Ngọc Anh | Thành viên D (SRE & Alerts Engineer) | https://github.com/PakerPP/Day13-K4-Observability-G28/commit/a542151, https://github.com/PakerPP/Day13-K4-Observability-G28/commit/8238930 | Thiết kế SLO (`config/slo.yaml`) đối chiếu số với threshold dashboard; viết 3 alert symptom-based + runbook 8 trường (`config/alert_rules.yaml`, `docs/alerts.md`); tự viết validator `scripts/validate_alerts.py` để tự động phát hiện lệch số SLO↔dashboard và alert dựa tên incident nội bộ. |
| Bùi Xuân Tùng | Thành viên E (QA & Chief Investigator): chạy QA cuối, kiểm tra evidence Langfuse, chạy challenge chính thức, nối Metrics/Logs/Trace để kết luận root cause và hoàn thiện báo cáo nhóm. | Evidence local trong `submission/evidence/qa_*.png`, `submission/evidence/challenge_*.png`, `submission/evidence/prompt_*.png`; commit/push cuối sẽ cập nhật sau. | Biết cách xác minh end-to-end bằng `pytest`, `validate_logs.py`, `validate_dashboard.py`; dùng load test để tạo dữ liệu điều tra; đối chiếu latency từ log JSONL với trace waterfall Langfuse và báo cáo root cause theo luồng Metrics → Traces → Logs. |

