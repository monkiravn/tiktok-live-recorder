# TikTok Live Recorder – API Service (FastAPI + Celery + Redis)

> **Mục tiêu**: Biến dự án CLI `tiktok-live-recorder` thành **dịch vụ API** có khả năng theo dõi (watch) và ghi (record) livestream TikTok ở quy mô production, có thể mở rộng, quan sát được, và dễ vận hành.

---

## Mục lục
- [1. Phạm vi & Mục tiêu](#1-phạm-vi--mục-tiêu)
- [2. Không nằm trong phạm vi (Non-goals)](#2-không-nằm-trong-phạm-vi-non-goals)
- [3. Tổng quan kiến trúc](#3-tổng-quan-kiến-trúc)
- [4. Thành phần hệ thống](#4-thành-phần-hệ-thống)
- [5. Thiết kế API (v1)](#5-thiết-kế-api-v1)
- [6. Mô hình dữ liệu & lưu trữ](#6-mô-hình-dữ-liệu--lưu-trữ)
- [7. Thiết kế Celery task](#7-thiết-kế-celery-task)
- [8. Cấu hình & bí mật (Config & Secrets)](#8-cấu-hình--bí-mật-config--secrets)
- [9. Bảo mật, quyền truy cập & Rate limit](#9-bảo-mật-quyền-truy-cập--rate-limit)
- [10. Quan sát (Observability)](#10-quan-sát-observability)
- [11. Xử lý lỗi & Mã lỗi](#11-xử-lý-lỗi--mã-lỗi)
- [12. Hiệu năng & mở rộng](#12-hiệu-năng--mở-rộng)
- [13. Kiểm thử & Chất lượng](#13-kiểm-thử--chất-lượng)
- [14. Triển khai & Vận hành](#14-triển-khai--vận-hành)
- [15. Kế hoạch phát triển & Giao việc](#15-kế-hoạch-phát-triển--giao-việc)
- [16. Tiêu chí chấp nhận (Acceptance Criteria) chi tiết](#16-tiêu-chí-chấp-nhận-acceptance-criteria-chi-tiết)
- [17. Phụ lục A — Ví dụ sử dụng API](#17-phụ-lục-a--ví-dụ-sử-dụng-api)
- [18. Phụ lục B — Checklist bàn giao](#18-phụ-lục-b--checklist-bàn-giao)
- [19. Thuật ngữ](#19-thuật-ngữ)

---

## 1. Phạm vi & Mục tiêu
- Cung cấp **REST API** để:
  - Đăng ký **watcher** theo dõi `room_id` hoặc `url` TikTok Live và **tự động** ghi khi có live.
  - **Khởi chạy** phiên ghi thủ công theo yêu cầu.
  - **Theo dõi trạng thái** job, truy vấn log (ở mức tóm tắt), xem danh sách file xuất.
- Đảm bảo có thể **scale ngang** qua Celery workers, **đóng gói** bằng Docker, và có **quan sát** (logs/metrics).
- Tùy chọn **đẩy file lên S3/MinIO** sau khi ghi xong.

## 2. Không nằm trong phạm vi (Non-goals)
- Không sửa đổi sâu logic của **repo CLI gốc**; ta chỉ **bọc** (wrap) và **điều phối**.
- Không cung cấp UI frontend; chỉ REST API và công cụ quan sát (Flower/metrics).
- Không đảm bảo vượt qua mọi chính sách/ToS của nền tảng; trách nhiệm vận hành thuộc môi trường triển khai.

---

## 3. Tổng quan kiến trúc
```
Client → FastAPI (REST, Auth, Rate Limit)
          │
          ├─ Celery (broker: Redis, backend: Redis)
          │     └─ Workers (thực thi subprocess → CLI tiktok-live-recorder)
          │
          ├─ Storage: recordings (Local Volume / NFS / PVC)
          ├─ (Optional) S3/MinIO upload
          └─ Observability: Flower, Logging JSON, Prometheus metrics
```

**Luồng chính**:
1. Client gọi API (tạo watcher hoặc record ngay).
2. API đẩy task vào Celery queue.
3. Worker nhận task, chạy CLI recorder bằng `subprocess`.
4. File ghi xong lưu vào `RECORDINGS_DIR`; tuỳ chọn push S3.
5. Client truy vấn `/jobs/{task_id}` để lấy trạng thái & kết quả.

---

## 4. Thành phần hệ thống
- **FastAPI**: xác thực, giới hạn tần suất, định nghĩa endpoints, chuyển công việc sang Celery.
- **Celery**: điều phối job nền; queues: `default` (nhẹ) & `recording` (nặng I/O).
- **Redis**: làm **broker** và **result backend**.
- **Worker**: chạy tiến trình CLI gốc, quản lý vòng đời tiến trình, gom kết quả.
- **Flower**: quan sát queue, task, retries.
- **Storage**: thư mục recordings (local/PVC) + (tuỳ chọn) đẩy lên S3/MinIO.
- **Config/Secrets**: từ biến môi trường; không hard-code.

**Tech stack**: Python 3.11, FastAPI, Celery, Redis 7, pydantic v2, boto3, slowapi, pytest/httpx, logging JSON, Prometheus client, Docker.

---

## 5. Thiết kế API (v1)
> Tất cả endpoints (trừ `/healthz`, `/ready`, `/docs`, `/openapi.json`) yêu cầu header `X-API-Key` hợp lệ.

### 5.1. Health & Readiness
- `GET /healthz` → `200 OK` (liveness)
- `GET /ready` → `200 OK` khi kết nối Redis & cấu hình hợp lệ

### 5.2. Ghi thủ công (Record-on-demand)
- `POST /recordings`
  - Body:
    ```json
    {
      "room_id": "string | null",
      "url": "string | null",
      "duration": 3600,
      "output_template": "string | null",
      "options": {
        "upload_s3": false,
        "proxy": "http://user:pass@host:port",
        "cookies": "/secrets/cookies.txt"
      }
    }
    ```
  - Response: `202 Accepted`
    ```json
    { "task_id": "uuid", "status": "PENDING" }
    ```
  - Lỗi: `400` thiếu `room_id|url`; `422` sai kiểu; `500` lỗi nội bộ.

### 5.3. Tạo watcher (theo dõi & auto-record)
- `POST /watchers`
  - Body:
    ```json
    {
      "room_id": "string | null",
      "url": "string | null",
      "poll_interval": 60,
      "options": {
        "upload_s3": false,
        "proxy": "http://...",
        "cookies": "/secrets/cookies.txt"
      }
    }
    ```
  - Response:
    ```json
    { "task_id": "uuid", "status": "PENDING" }
    ```

- `DELETE /watchers/{key}`
  - `key` = `room_id` **hoặc** URL đã đăng ký.
  - Response:
    ```json
    { "ok": true }
    ```
  - Lỗi: `404` nếu không tồn tại watcher; `409` nếu task không thể hủy an toàn.

### 5.4. Trạng thái job
- `GET /jobs/{task_id}`
  - Response:
    ```json
    {
      "task_id": "uuid",
      "status": "PENDING|STARTED|RETRY|SUCCESS|FAILURE",
      "result": {
        "returncode": 0,
        "files": ["..."],
        "s3": [{"bucket": "...", "key": "..."}],
        "started_at": "ISO8601",
        "ended_at": "ISO8601"
      }
    }
    ```

### 5.5. Danh sách file
- `GET /files?room_id=&url=&from=&to=&page=1&page_size=50`
  - Trả danh sách `{name,size,mtime,path}` + phân trang.

**Versioning**: Tiền tố `v1` có thể được thêm vào route (ví dụ `/v1/recordings`) khi nâng cấp breaking changes.

---

## 6. Mô hình dữ liệu & lưu trữ
### 6.1. Watcher (SQLite)
```json
{
  "key": "<room_id|url>",
  "room_id": "string|null",
  "url": "string|null",
  "poll_interval": 60,
  "status": "active|paused|deleted",
  "created_at": "ISO8601",
  "last_run_at": "ISO8601|null",
  "options": {
    "upload_s3": true,
    "proxy": "http://...",
    "cookies": "/secrets/cookies.txt"
  }
}
```

### 6.2. File index
- Quét thư mục `RECORDINGS_DIR`, có cache 30–60s trong Redis để trả `/files` nhanh hơn.
- Tên file/đường dẫn chuẩn hóa theo template (ví dụ: `{room_id}/{YYYY}/{MM}/{DD}/{timestamp}_{title}.mp4`).

---

## 7. Thiết kế Celery task
- **Queues**: `default` (nhẹ như watcher/poll), `recording` (record nặng I/O).
- **Retries**: backoff theo lũy thừa (exponential) tối đa 5 lần cho lỗi mạng/tạm thời.
- **Giới hạn thời gian**: `hard_time_limit` hoặc watchdog để kill tiến trình treo.
- **Hủy job**: qua Celery `revoke(terminate=True)`; đảm bảo cleanup tiến trình con.
- **Kết quả**: ghi nhận `returncode`, danh sách `files`, thông tin upload S3 (nếu bật).

> **Lưu ý về CLI upstream**: ánh xạ chính xác cờ (flags) `room_id/url/output/duration/proxy/cookies` theo README của dự án gốc. Pin theo **commit SHA** ổn định để tránh thay đổi breaking.

---

## 8. Cấu hình & bí mật (Config & Secrets)
Các biến môi trường chính:
- `CELERY_BROKER_URL` (ví dụ `redis://redis:6379/0`)
- `CELERY_RESULT_BACKEND` (ví dụ `redis://redis:6379/1`)
- `RECORDINGS_DIR` (ví dụ `/recordings`)
- `TLR_ROOT` (đường tới repo gốc trong container, ví dụ `/opt/tlr/src`)
- `API_KEYS="key1,key2,..."` (danh sách key cho auth)
- `RATE_LIMIT_PER_MIN=60`
- (Tuỳ chọn S3) `S3_BUCKET`, `S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
- (Tuỳ chọn) proxy/cookies thông qua `options` ở body request hoặc mount vào container (secrets).

**Nguyên tắc**: không in ra log các secrets; dùng mount volume/secret store khi triển khai thực tế.

---

## 9. Bảo mật, quyền truy cập & Rate limit
- **Auth**: Header `X-API-Key`. Từ chối 401/403 nếu thiếu/sai.
- **CORS**: chỉ whitelist domain cần thiết.
- **Rate limit**: 60 req/phút/API key (mặc định), tuỳ chỉnh qua env.
- **Validation**: kiểm tra chặt chẽ `room_id/url`, `duration`, đường dẫn `cookies`/`proxy` để tránh command injection.
- **Sandbox**: ưu tiên chạy worker trong cgroup hạn chế CPU/RAM/IO; đặt `ulimit` hợp lý.

---

## 10. Quan sát (Observability)
- **Logging JSON**: `ts, level, msg, task_id, room_id|url, duration, returncode`.
- **Flower**: theo dõi queue, task, retries trên cổng 5555.
- **Prometheus metrics** (`/metrics`):
  - `celery_tasks_total{status=...}`
  - `recordings_success_total`, `recordings_failed_total`
  - `watchers_active`
  - `disk_bytes_free` (tuỳ chọn đo dung lượng)
- **Tracing** (tuỳ chọn): OpenTelemetry exporter.

---

## 11. Xử lý lỗi & Mã lỗi
- **4xx**: `400` (thiếu trường), `401/403` (auth), `422` (validation), `429` (rate limit).
- **5xx**: `500` (lỗi nội bộ), `502/504` (quá hạn từ tiến trình, tùy cấu hình reverse proxy).
- **Mapping recorder**:
  - `returncode != 0` → map sang `error_code`: `RECORDER_EXIT_NONZERO`, `FFMPEG_MISSING`, `LIVE_OFFLINE`, `NETWORK_TIMEOUT`, …
- **Phản hồi lỗi chuẩn**:
  ```json
  {
    "error_code": "string",
    "error_message": "mô tả",
    "correlation_id": "uuid"
  }
  ```

---

## 12. Hiệu năng & mở rộng
- **Scale workers** theo độ sâu hàng đợi; tách queue `recording` để không chặn tác vụ nhẹ.
- **I/O disk**: bảo đảm thông lượng ghi đủ lớn; cân nhắc SSD/NVMe.
- **Băng thông mạng**: theo dõi & hạn mức để tránh nghẽn.
- **TTL lưu trữ**: chính sách tự động dọn file cũ hoặc quota per channel.
- **Proxy pool**: giảm nguy cơ bị chặn/rate-limit từ nền tảng.

---

## 13. Kiểm thử & Chất lượng
- **Unit**: adapter build command, path utils, upload S3 (mock), pagination `/files`.
- **Integration**: API ↔ Celery (eager mode), mock `subprocess.Popen`.
- **E2E dev**: chạy docker-compose, test thực tế 1 URL demo (khi có thể).
- **Coverage mục tiêu**: ≥ 70% modules cốt lõi.
- **CI**: lint (ruff/black/mypy) + test (pytest) + build image + scan (Trivy).

---

## 14. Triển khai & Vận hành
- **Dev**: `docker compose up` (services: api, worker, beat, flower, redis).
- **Prod**:
  - K8s: tách deployment `api` & `worker`; Redis managed; PVC cho recordings.
  - Autoscale: HPA/KEDA theo queue depth / CPU.
  - Ingress: TLS, optional mTLS; áp hạn mức tại edge.
- **Runbook**:
  1. Xem job: Flower hoặc `GET /jobs/{id}`.
  2. Hủy job: `DELETE /watchers/{key}` hoặc Celery revoke.
  3. S3 sự cố: chuyển sang lưu local-only, retry sau.
  4. Disk đầy: bật cleanup theo TTL/quota; cảnh báo trước ngưỡng.
  5. TikTok rate-limit: tăng `poll_interval`, dùng proxy pool.

---

## 15. Kế hoạch phát triển & Giao việc
> Chia theo sprint, mỗi ticket có **Owner, Estimate, Deliverables, AC, Dependencies**.

### Sprint 1 — Nền tảng E2E
- **S1-T01 — FastAPI bootstrap & healthcheck** (0.5d)  
  *AC*: `/healthz` 200; `/ready` kiểm tra Redis OK.
- **S1-T02 — Celery wiring (queues, broker/backend)** (1d)  
  *AC*: gửi/nhận task demo OK.
- **S1-T03 — CLI adapter (build flags)** (0.5d)  
  *AC*: ánh xạ đúng flags (room_id/url/output/duration).
- **S1-T04 — record_once subprocess & cleanup** (1d)  
  *AC*: không zombie; trả `{returncode, files}`.
- **S1-T05 — Endpoints /recordings & /jobs/{id}** (0.5d)  
  *AC*: trả `task_id`, truy vấn trạng thái.
- **S1-T06 — Compose & quickstart** (0.5d)  
  *AC*: compose up lần đầu thành công.

### Sprint 2 — Watcher & Files
- **S2-T01 — task_watch_and_record + backoff** (1d)  
  *AC*: offline → sleep; khi live → tạo file.
- **S2-T02 — Watchers API (in-memory)** (0.5d)  
  *AC*: tạo/hủy watcher; lưu `task_id` theo `key`.
- **S2-T03 — /files list + pagination** (1d)  
  *AC*: lọc, phân trang, độ trễ < 500ms (cache).
- **S2-T04 — Logging JSON + correlation id** (0.5d)  
  *AC*: mọi request/task có `correlation_id`.
- **S2-T05 — Flower integration** (0.25d)  
  *AC*: Flower hoạt động ở :5555.

### Sprint 3 — Bảo mật & Persistence
- **S3-T01 — API key middleware + CORS** (0.5d)  
  *AC*: thiếu/sai key → 401; CORS whitelist.
- **S3-T02 — Rate limit (slowapi)** (0.5d)  
  *AC*: vượt quota → 429; counters theo API key.
- **S3-T03 — Persist watchers (Redis/SQLite)** (1d)  
  *AC*: restart dịch vụ, watchers tự nạp & reschedule.
- **S3-T04 — Proxy & cookies options** (0.5d)  
  *AC*: truyền proxy/cookies xuống CLI an toàn.

### Sprint 4 — Cloud storage & Quality
- **S4-T01 — S3/MinIO upload hook** (1d)  
  *AC*: upload OK, retry 3x, expose URL/key.
- **S4-T02 — Metrics `/metrics`** (0.5d)  
  *AC*: counters/gauges như mục 10.
- **S4-T03 — Tests ≥70% + CI pipeline** (1.5d)  
  *AC*: badge coverage; pipeline PR xanh.
- **S4-T04 — Docs hoàn chỉnh + runbook** (0.5d)  
  *AC*: README/How-to, Postman collection.

---

## 16. Tiêu chí chấp nhận (Acceptance Criteria) chi tiết
**API chung**
- [ ] Mọi endpoint (trừ health/docs) yêu cầu `X-API-Key` hợp lệ.
- [ ] Rate limit mặc định 60 req/phút/API key (config được).
- [ ] OpenAPI `/openapi.json` chuẩn; `/docs` hiển thị đầy đủ.

**/recordings**
- [ ] Body hợp lệ khi có **ít nhất** `room_id` **hoặc** `url`.
- [ ] Trả `task_id` ngay (202); trạng thái tiến độ theo `/jobs/{id}`.
- [ ] Khi thành công, `result.files` liệt kê đầy đủ file tạo ra.

**/watchers**
- [ ] Có thể tạo watcher với `poll_interval` (>=10s).
- [ ] Xóa watcher dừng job an toàn; không để lại tiến trình treo.

**/jobs/{id}**
- [ ] Trả `status` chính xác; `result` khi `SUCCESS`.
- [ ] Thất bại có `error_code`, `error_message`, `correlation_id`.

**/files**
- [ ] Phân trang chuẩn; filter theo `room_id/url/from/to`.
- [ ] Độ trễ danh sách < 500ms (có cache).

**Bảo mật & vận hành**
- [ ] Không log secrets.
- [ ] Flower hoạt động; metrics có sẵn.
- [ ] Chính sách TTL/quota lưu trữ được cấu hình (nếu bật).

---

## 17. Phụ lục A — Ví dụ sử dụng API
> Ví dụ minh họa (dev). Thay `API_KEY` và giá trị thực tế trước khi dùng.

**Record ngay một room URL**
```bash
curl -X POST http://localhost:8000/recordings  -H "Content-Type: application/json"  -H "X-API-Key: $API_KEY"  -d '{"url":"https://www.tiktok.com/@user/live","duration":1800}'
```

**Tạo watcher**
```bash
curl -X POST http://localhost:8000/watchers  -H "Content-Type: application/json"  -H "X-API-Key: $API_KEY"  -d '{"room_id":"123456789","poll_interval":60}'
```

**Xem trạng thái job**
```bash
curl -H "X-API-Key: $API_KEY" http://localhost:8000/jobs/<task_id>
```

**Liệt kê recordings**
```bash
curl -H "X-API-Key: $API_KEY" "http://localhost:8000/files?page=1&page_size=50"
```

---

## 18. Phụ lục B — Checklist bàn giao
- [ ] Code + tests + tài liệu cập nhật.
- [ ] `make test` pass; coverage báo cáo ≥ 70%.
- [ ] Compose up chạy OK; README hướng dẫn rõ ràng.
- [ ] Secrets không lộ; config tách bạch môi trường.
- [ ] Runbook có ví dụ và quy trình sự cố.
- [ ] Rủi ro & rollback đã được ghi nhận.

---

## 19. Thuật ngữ
- **Watcher**: đăng ký theo dõi một `room_id`/`url` để tự động ghi khi live.
- **Recording session**: một phiên ghi do người dùng khởi tạo.
- **Worker**: tiến trình Celery thực thi công việc nền.
- **Broker**/**Backend**: phần Redis dùng để xếp hàng và lưu kết quả task.

> **Ghi chú**: Để phù hợp với thay đổi upstream, cần **pin** phiên bản/commit của `tiktok-live-recorder` và xác thực lại mapping flags ở môi trường staging trước khi đưa vào production.