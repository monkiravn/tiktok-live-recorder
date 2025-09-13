# TikTok Live Recorder — Frontend Dashboard (Next.js + React + TypeScript)

> **Mục tiêu**: Xây dựng **dashboard nội bộ** để quản trị watchers, khởi chạy ghi hình, theo dõi trạng thái job, duyệt file recordings và quan sát sức khỏe hệ thống, dựa trên Backend API (FastAPI + Celery + Redis).

---

## Mục lục
- [1. Phạm vi & Mục tiêu](#1-phạm-vi--mục-tiêu)
- [2. Không nằm trong phạm vi (Non-goals)](#2-không-nằm-trong-phạm-vi-non-goals)
- [3. Kiến trúc tổng quan (BFF)](#3-kiến-trúc-tổng-quan-bff)
- [4. Thành phần Frontend](#4-thành-phần-frontend)
- [5. IA (Information Architecture) & Flow](#5-ia-information-architecture--flow)
- [6. Hợp đồng API & BFF Proxy](#6-hợp-đồng-api--bff-proxy)
- [7. Trạng thái ứng dụng & Dữ liệu](#7-trạng-thái-ứng-dụng--dữ-liệu)
- [8. Bảo mật Frontend](#8-bảo-mật-frontend)
- [9. Quan sát & Telemetry](#9-quan-sát--telemetry)
- [10. Xử lý lỗi & Trạng thái UI](#10-xử-lý-lỗi--trạng-thái-ui)
- [11. Hiệu năng & Khả dụng](#11-hiệu-năng--khả-dụng)
- [12. A11y & i18n](#12-a11y--i18n)
- [13. Kiểm thử & Chất lượng](#13-kiểm-thử--chất-lượng)
- [14. Triển khai & Vận hành](#14-triển-khai--vận-hành)
- [15. Roadmap & Task Breakdown](#15-roadmap--task-breakdown)
- [16. Acceptance Criteria](#16-acceptance-criteria)
- [17. Phụ lục A — Sơ đồ route & layout](#17-phụ-lục-a--sơ-đồ-route--layout)
- [18. Phụ lục B — Biến môi trường & scripts](#18-phụ-lục-b--biến-môi-trường--scripts)
- [19. Handover Checklist](#19-handover-checklist)

---

## 1. Phạm vi & Mục tiêu
- Cung cấp **UI quản trị** các chức năng Backend: tạo/xóa watcher, khởi chạy record, xem job/status/result, duyệt recordings.
- Đảm bảo **không lộ API key**; mọi request đi qua **BFF proxy** ở Next.js server.
- Tối ưu **trải nghiệm thao tác** cho vận hành nội bộ: nhanh, rõ trạng thái, dễ tra cứu.

## 2. Không nằm trong phạm vi (Non-goals)
- Không xây dựng public site hay multi-tenant portal.
- Không streaming realtime logs phức tạp (sử dụng polling trạng thái đơn giản).
- Không lưu trữ hay hiển thị secret nhạy cảm (proxy/cookies).

---

## 3. Kiến trúc tổng quan (BFF)
```
Browser → Next.js (App Router, React 18, TS)
           ├─ UI (pages/components, Tailwind + shadcn/ui)
           ├─ TanStack Query (fetch, cache, polling)
           └─ Route Handlers /api/*  →  Backend FastAPI
                                 (chèn X-API-Key từ server env)
```

**Lợi ích BFF**: tách API key khỏi client, gom logic xử lý lỗi/mapping response, có thể thêm caching/transform.

---

## 4. Thành phần Frontend
- **Framework**: Next.js 14 (App Router) + React 18 + TypeScript
- **UI Kit**: Tailwind CSS + shadcn/ui + Radix + lucide-react (icons)
- **Data**: TanStack Query (server-state), Zustand (UI ephemeral state)
- **Form/Validation**: React Hook Form + Zod
- **Table**: TanStack Table (sort, filter, column visibility)
- **Charts**: Recharts (xu hướng jobs/metrics)
- **Test**: Vitest + React Testing Library; Playwright (E2E)
- **Lint/Format**: eslint + prettier + stylelint
- **Lỗi/Telemetry (optional)**: Sentry

---

## 5. IA (Information Architecture) & Flow
### Trang chính
1. **Dashboard**: thẻ số liệu (Active Watchers, Running Jobs, Success/Failure 24h, Queue Depth), biểu đồ jobs theo giờ, health chips.
2. **Watchers**: bảng danh sách; Create (modal), Delete, (optional Pause/Resume); xem lần chạy gần nhất.
3. **Record Now**: form gửi record (room_id/url, duration, options); điều hướng tới Job Detail.
4. **Jobs**: bảng jobs (task_id, status, started/ended, lỗi); trang chi tiết job (files/S3, metadata).
5. **Files**: danh sách recordings; filter theo room_id/url/date; pagination; hành động copy path/S3 key.
6. **Settings**: theme, timezone & định dạng thời gian, ngôn ngữ (vi/en — optional).

### Luồng tiêu biểu
- Tạo watcher → toast thành công → về danh sách (poll cập nhật).
- Record nhanh → nhận task_id → sang chi tiết job, auto-poll 2–5s cho tới SUCCESS/FAILURE.
- Duyệt Files → lọc & copy path/S3 key.

---

## 6. Hợp đồng API & BFF Proxy
**BFF Route Handlers** (server only) che chắn API key và gọi Backend:
- `GET /api/healthz` → proxy `GET /healthz`
- `GET /api/ready` → proxy `GET /ready`
- `POST /api/recordings` → proxy `POST /recordings`
- `POST /api/watchers` → proxy `POST /watchers`
- `DELETE /api/watchers/[key]` → proxy `DELETE /watchers/{key}`
- `GET /api/jobs/[task_id]` → proxy `GET /jobs/{task_id}`
- `GET /api/files` → proxy `GET /files`

**Quy ước lỗi BFF**:
- Chuẩn hóa response lỗi dạng:
  ```json
  { "error_code": "string", "error_message": "string", "correlation_id": "uuid" }
  ```
- Mapping status code giữ nguyên của Backend; thêm `x-correlation-id` nếu có.

**Kiểu dữ liệu**: sinh types từ OpenAPI (openapi-typescript) **hoặc** định nghĩa thủ công (Zod + infer).

---

## 7. Trạng thái ứng dụng & Dữ liệu
- **TanStack Query**: quản lý cache server-state; `refetchInterval` 2–5s cho Jobs, 10–30s cho Watchers/Files.
- **Zustand**: trạng thái UI (modals, table layout, theme).
- **Invalidation**: sau khi Create/Delete watcher, invalidate keys tương ứng.
- **Prefetching**: chuyển trang Jobs/Files thì prefetch trang đầu.

---

## 8. Bảo mật Frontend
- **Không bao giờ** đặt `API_KEY` ở client; chỉ ở server env và được BFF thêm vào header khi gọi Backend.
- Xử lý dữ liệu đầu vào (forms) bằng validation Zod; escape khi render.
- Tắt indexing/public access (đây là dashboard nội bộ).

---

## 9. Quan sát & Telemetry
- (Optional) **Sentry**: log lỗi theo release; bỏ qua ở dev.
- Sự kiện thao tác chính (create watcher, submit record, delete watcher) chỉ để **audit nhẹ** nếu cần; không gửi PII.

---

## 10. Xử lý lỗi & Trạng thái UI
- **Loading**: skeletons cho bảng & biểu đồ.
- **Error**: banner + retry; hiển thị `correlation_id` để tra log Backend.
- **Empty**: nội dung hướng dẫn (CTA *Create Watcher* / *Record Now*).
- **Toasts**: cho create/delete/success/failure.

---

## 11. Hiệu năng & Khả dụng
- Bảng > 500 hàng: virtualization.
- Bundle trang đầu < 300KB gzipped; code-splitting theo route.
- FCP < 1.5s trong mạng nội bộ.
- Polling thích ứng: giảm tần suất khi tab không focus.

---

## 12. A11y & i18n
- Keyboard navigation & focus ring rõ ràng.
- Modal có focus trap, đóng bằng ESC.
- i18n (vi/en) qua `next-intl` (optional).

---

## 13. Kiểm thử & Chất lượng
- **Unit**: components (Form, Table cell, Badges), helpers (format bytes/time).
- **Integration**: hooks gọi BFF; mutation create/delete watcher (mock fetch).
- **E2E**: Playwright các flow chính (create watcher → list; record → job success; filter files).
- Threshold: ≥ 70% lines/functions ở phần cốt lõi UI; CI chạy lint + unit + e2e headless.

---

## 14. Triển khai & Vận hành
- **Env (server-only)**: `API_BASE_URL`, `API_KEY`, `NODE_ENV`.
- Deploy dạng container hoặc Vercel (khuyến nghị container cùng cluster với Backend để giảm độ trễ).
- Tắt cache edge; đây là dashboard nội bộ, **không bật public cache**.
- Giám sát lỗi trên Sentry (nếu bật).

---

## 15. Roadmap & Task Breakdown
> Định dạng: **ID — Title — Owner — Estimate — Dependencies — Deliverables — AC — Notes**

### Sprint 1 — Skeleton & BFF (Tuần 1)
- **F1-T01 — Bootstrap Next.js + TS + Tailwind + shadcn** (0.5d)  
  *AC*: `pnpm dev` chạy; eslint/prettier pass.
- **F1-T02 — Layout + Navbar/Sidebar** (0.5d)  
  *AC*: responsive; active route; breadcrumbs.
- **F1-T03 — BFF proxy `/api/*` + env** (0.5d)  
  *AC*: proxy `GET /healthz` & `GET /ready` OK; lỗi được map chuẩn.
- **F1-T04 — Dashboard skeleton** (0.5d)  
  *AC*: 4 cards (dummy), health chips, chart placeholder.

### Sprint 2 — Watchers & Record (Tuần 2)
- **F2-T01 — Watchers Table + Filters** (1d)  
  *AC*: list + sort + search; empty/loading states.
- **F2-T02 — Create Watcher Modal** (0.5d)  
  *AC*: Zod validate (room_id xor url, poll_interval ≥ 10); toast success/error.
- **F2-T03 — Delete Watcher + Optimistic** (0.5d)  
  *AC*: confirm dialog; bảng cập nhật ngay.
- **F2-T04 — Record Form & Submit Flow** (0.5d)  
  *AC*: submit → nhận `task_id` → điều hướng Job Detail.

### Sprint 3 — Jobs & Files (Tuần 3)
- **F3-T01 — Jobs List + Filters** (0.5d)  
  *AC*: badge trạng thái; filter theo status/date; link detail.
- **F3-T02 — Job Detail + Polling** (0.5d)  
  *AC*: auto refresh 2–5s; dừng khi `SUCCESS/FAILURE`; hiển thị files/S3.
- **F3-T03 — Files Browser + Pagination** (1d)  
  *AC*: filter room_id/url/date; copy path/S3 key; paging.
- **F3-T04 — Dashboard metrics & chart** (0.5d)  
  *AC*: dùng counters thật nếu `/metrics` có; fallback mock.

### Sprint 4 — Polish & Quality (Tuần 4)
- **F4-T01 — i18n vi/en (optional)** (0.5d)  
  *AC*: chuyển ngôn ngữ runtime; persisted preference.
- **F4-T02 — A11y & Keyboard nav** (0.5d)  
  *AC*: focus trap, tab order, aria roles.
- **F4-T03 — Sentry + Telemetry nhẹ** (0.5d)  
  *AC*: lỗi gửi kèm release; tắt ở dev.
- **F4-T04 — E2E tests 6–8 flows** (1d)  
  *AC*: Playwright xanh trên CI; artifact báo cáo.
- **F4-T05 — Docs & Handover** (0.5d)  
  *AC*: README-frontend, hướng dẫn env/deploy, ảnh chụp màn hình.

---

## 16. Acceptance Criteria
- **BFF**: tất cả request đi qua `/api/*`; **không lộ API key** ở network tab.
- **Watchers**: tạo/xóa thành công; validation rõ ràng; cập nhật optimistic + reconcile từ polling.
- **Record**: submit thành công → tới Job Detail; dừng polling khi job kết thúc.
- **Jobs**: danh sách và chi tiết phản ánh chính xác status/result; copy task_id dễ dàng.
- **Files**: filter & paging hoạt động mượt; copy path/S3 chính xác.
- **Dashboard**: health hiển thị đúng; cards/charts cập nhật.
- **Hiệu năng**: FCP < 1.5s nội bộ; bundle trang đầu < 300KB gz.
- **A11y**: modal có focus trap; hỗ trợ phím tắt cơ bản.

---

## 17. Phụ lục A — Sơ đồ route & layout
```
/ (Dashboard)
├─ /watchers
│   ├─ (list)
│   └─ (create modal)
├─ /record
├─ /jobs
│   └─ /jobs/[task_id] (detail)
├─ /files
└─ /settings
```
**Layout**: App Shell (Navbar + Sidebar) → nội dung trang. Component thư mục: `components/ui/*`, `modules/*` (feature scoped).

---

## 18. Phụ lục B — Biến môi trường & scripts
**.env.local (server-only)**
```
API_BASE_URL=http://backend:8000
API_KEY=***
NODE_ENV=production
```
**Scripts (pnpm)**
```
pnpm dev         # chạy dev
pnpm build       # build production
pnpm start       # chạy production
pnpm test        # unit/integration
pnpm test:e2e    # e2e playwright
pnpm lint        # eslint
```

---

## 19. Handover Checklist
- [ ] CI pass: lint + unit + e2e
- [ ] ENV production cấu hình đúng (API_BASE_URL, API_KEY)
- [ ] BFF kiểm chứng: API key **không** xuất hiện ở client
- [ ] Tài liệu cập nhật; ảnh chụp các flow chính
- [ ] Quy trình rollback FE (deploy phiên bản trước)