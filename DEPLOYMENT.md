# Thông Tin Deploy — Checkpoint 5

> Điền file này sau khi deploy xong. `pytest tests/test_cp5.py` đọc file này
> để tìm địa chỉ service của bạn và gọi thử.
>
> **Chỉ ghi TÊN biến môi trường, tuyệt đối không dán giá trị API key vào đây.**
> Repo này công khai — dán khóa vào là mất khóa.

## Thông Tin Học Viên

| Mục | Nội dung |
|-----|----------|
| Họ và tên | Nguyễn Quốc Tuấn |
| Mã học viên | 2A202602910 |
| Repo | https://github.com/quoctuan2005/K4-L3A-DAY12-NguyenQuocTuan-2A202602910-CloudServicesAndDeployment |

## Service

| Mục | Nội dung |
|-----|----------|
| Public URL | https://day12-agent-342629476877.asia-southeast1.run.app |
| Platform | Cloud Run (Google Cloud Platform) |
| Ngày deploy | 2026-09-28 |

## Biến Môi Trường Đã Set Trên Cloud

Ghi tên biến và **nguồn giá trị**, không ghi giá trị:

| Biến | Đã set | Ghi chú |
|------|--------|---------|
| `PORT` | ✅ | platform tự gán |
| `AGENT_API_KEY` | ✅ | đặt trong Google Cloud Run environment variables (bảo mật, không commit repo) |
| `REDIS_URL` | ✅ | Upstash Redis (Singapore region / TLS) |
| `RATE_LIMIT_PER_MINUTE` | ✅ | 10 |
| `MONTHLY_BUDGET_USD` | ✅ | 10.0 |
| `LOG_LEVEL` | ✅ | INFO |
| `GEMINI_API_KEY` | ✅ | Google AI Studio API Key (cho Music Mood Agent) |

## Lệnh Kiểm Tra

Thay `<URL>` bằng Public URL ở trên:

```bash
# 1. Liveness — mong đợi 200 {"status":"ok"}
curl -i https://day12-agent-342629476877.asia-southeast1.run.app/health

# 2. Readiness — mong đợi 200 {"status":"ready"} (đã nối được Redis)
curl -i https://day12-agent-342629476877.asia-southeast1.run.app/ready

# 3. Không có API key — mong đợi 401
curl -i -X POST https://day12-agent-342629476877.asia-southeast1.run.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello"}'

# 4. Có API key — mong đợi 200 kèm câu trả lời
curl -i -X POST https://day12-agent-342629476877.asia-southeast1.run.app/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $AGENT_API_KEY" \
  -H "X-User-Id: sv-test" \
  -d '{"question":"Deploy là gì?"}'

# 5. Rate limit — gọi 15 lần, những lần cuối phải trả 429
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "%{http_code} " -X POST https://day12-agent-342629476877.asia-southeast1.run.app/ask \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $AGENT_API_KEY" \
    -H "X-User-Id: sv-test" \
    -d '{"question":"test"}'
done; echo
```

## Kết Quả Chạy Thật

Dán output của các lệnh trên vào đây:

```
# 1. Liveness probe:
HTTP/2 200 
content-type: application/json
x-cloud-trace-context: 8dd45e7a3c31b0d7d71fdd2bc9ecaea1;o=1
date: Mon, 28 Sep 2026 09:12:46 GMT
server: Google Frontend
content-length: 57
alt-svc: h3=":443"; ma=2592000,h3-29=":443"; ma=2592000

{"status":"ok","service":"day12-agent","version":"1.0.0"}

# 2. Readiness probe:
HTTP/2 200 
content-type: application/json
x-cloud-trace-context: bd9ad12e7debcb15bb9ea6506006783f
date: Mon, 28 Sep 2026 09:12:53 GMT
server: Google Frontend
content-length: 31
alt-svc: h3=":443"; ma=2592000,h3-29=":443"; ma=2592000

{"status":"ready","redis":true}

# 3. Authentication required (không có API key):
HTTP/2 401 
content-type: application/json
x-cloud-trace-context: dcfe2e73b2b2c25162c9dd8290bfce2c;o=1
date: Mon, 28 Sep 2026 09:13:06 GMT
server: Google Frontend
content-length: 39
alt-svc: h3=":443"; ma=2592000,h3-29=":443"; ma=2592000

{"detail":"invalid or missing API key"}

# 4. Có API key hợp lệ:
HTTP/2 200 
content-type: application/json
x-cloud-trace-context: 7213d275832fb7122261d4ec54de71ca;o=1
date: Mon, 28 Sep 2026 09:13:29 GMT
server: Google Frontend
content-length: 279
alt-svc: h3=":443"; ma=2592000,h3-29=":443"; ma=2592000

{"answer":"Câu hỏi hay. Deploy là gì thường được giải quyết bằng cách chuẩn hóa môi trường chạy: cùng một image chạy giống nhau ở laptop và trên cloud.","user_id":"sv-test","history_length":0,"cost_usd":2.145e-05,"tokens":{"in":3,"out":35}}

# 5. Rate limit (gọi 15 lần liên tiếp):
200 200 200 200 200 200 200 200 200 429 429 429 429 429 429
```

## Ảnh Chụp Màn Hình

Đặt ảnh trong thư mục `screenshots/`:

- `screenshots/dashboard.png` — trang quản lý service trên Cloud Run dashboard
- `screenshots/health.png` — kết quả gọi `/health` và `/ready` thành công từ terminal
