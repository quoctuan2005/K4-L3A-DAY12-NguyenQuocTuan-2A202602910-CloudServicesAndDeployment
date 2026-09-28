# Phiếu Phản Ánh — K4 Level 3A, Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: thay dòng placeholder bằng câu trả lời.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Nguyễn Quốc Tuấn  Mã học viên: 2A202602910

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

Tình huống cụ thể: Khi deploy service lên môi trường mới (staging hoặc production trên Cloud), kỹ sư cấu hình quên khai báo biến `AGENT_API_KEY` trong dashboard.
- Nếu để mặc định là `"changeme"`: Service vẫn khởi động thành công (200 OK) và báo healthy. Tuy nhiên, khóa bảo mật lúc này là `"changeme"` — một giá trị công khai ai cũng đoán được. Kẻ xấu có thể quét và dùng key này gọi API ồ ạt, làm rò rỉ dữ liệu hoặc đốt sạch hạn mức tài chính của mô hình AI mà đội ngũ phát triển không hề hay biết cho đến khi nhận hóa đơn cuối tháng.
- Nếu không có mặc định (Fail Fast): Pydantic ném `ValidationError` ngay ở giây đầu tiên khi nạp cấu hình. Container lập tức dừng (crash) với exit code khác 0. Hệ thống điều phối Cloud phát hiện container failed và từ chối rollout phiên bản lỗi này, giữ nguyên bản cũ đang chạy ổn định, đồng thời bắn cảnh báo đỏ cho kỹ sư vào sửa biến môi trường ngay lập tức trước khi bất kỳ request nào từ bên ngoài chạm vào hệ thống.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

- Dòng log JSON thực tế thu được từ stdout:
`{"event": "ask_completed", "level": "info", "timestamp": "2026-09-28T08:40:39.123456+00:00", "user_id": "sv-test", "tokens_in": 12, "tokens_out": 24, "cost_usd": 0.00036}`

- Hai việc làm được với dòng log JSON này mà `print("đã trả lời xong")` không thể làm được:
  1. **Lọc, truy vấn và tạo dashboard tự động (Structured Querying & Aggregation):** Các hệ thống thu thập log tập trung (như Datadog, Grafana Loki, CloudWatch, GCP Cloud Logging) có thể tự động parse các trường JSON để lọc theo user cụ thể (`jsonPayload.user_id = "sv-test"`), lọc request tốn kém (`jsonPayload.cost_usd > 0.01`), hoặc tổng hợp biểu đồ tổng số token tiêu thụ theo thời gian thực mà không cần viết regex bóc tách chuỗi text thô phức tạp.
  2. **Thiết lập cảnh báo tự động theo ngưỡng (Automated Threshold Alerting):** Dễ dàng gắn cảnh báo (Alert Rule) khi chi phí của một request vượt ngưỡng bất thường (`cost_usd > threshold`), hoặc khi phát hiện một user có lượng token tiêu thụ tăng vọt, giúp phát hiện sớm các cuộc tấn công DDoS tài chính hoặc lỗi lặp vô hạn ở phía client.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t agent:single .
docker build -t agent:multi .
docker images | grep agent
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu: `python:3.11` đầy đủ) | ~1020 MB |
| Multi-stage (`python:3.11-slim`, non-root) | ~297 MB (content size thực tế chỉ ~64 MB) |

Giải thích: phần dung lượng chênh lệch đó là những gì?

Phần dung lượng chênh lệch (~700 MB) bao gồm:
1. **Base image tối giản:** `python:3.11` đầy đủ được xây dựng trên bản Debian hoàn chỉnh có sẵn toàn bộ công cụ biên dịch (gcc, g++, make, libc-dev, build headers, git, curl...). Trong khi đó, `python:3.11-slim` đã lược bỏ hầu hết các package phát triển đó, chỉ giữ lại những gì tối thiểu nhất để thông dịch Python.
2. **Loại bỏ build cache trong Multi-stage:** Ở stage `builder`, quá trình tải bánh xe wheel, index cache của pip (`/root/.cache/pip`) và các file trung gian phát sinh đều bị bỏ lại ở stage đầu. Stage runtime cuối cùng chỉ copy đúng thư mục gói thư viện hoàn chỉnh (`/install` sang `/usr/local`), không mang theo bất kỳ file rác nào của quá trình build.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

- Khi sửa 1 ký tự trong `app/main.py`:
  + Các layer được dùng lại từ cache (`CACHED`):
    * Layer tải base image `python:3.11-slim`
    * Layer `WORKDIR /app`
    * Layer `COPY requirements.txt .`
    * Layer `RUN pip install --no-cache-dir ...` (toàn bộ stage builder)
    * Layer `COPY --from=builder /install /usr/local`
    * Layer `RUN useradd -m ...`
  + Layer phải chạy lại: Chỉ từ layer `COPY . .` trở về sau trong stage runtime (thời gian build lại chỉ mất ~0.5 giây).
- Nếu đặt `COPY . .` lên trước `RUN pip install`:
  + Mỗi khi sửa file code `app/main.py`, layer `COPY . .` sẽ bị mất hiệu lực cache (cache bust).
  + Theo nguyên lý của Docker layer caching, một khi một layer bị chạy lại thì toàn bộ các layer tiếp theo phía sau nó đều bị vô hiệu hóa cache.
  + Kết quả: Docker sẽ buộc phải chạy lại lệnh `RUN pip install` từ đầu, tải và cài lại toàn bộ danh sách thư viện mỗi lần sửa code, biến thời gian build từ 0.5s thành 1-2 phút, cực kỳ lãng phí thời gian phát triển và băng thông CI/CD.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

- Chuỗi sự kiện leo thang:
  1. Ứng dụng Python xuất hiện lỗ hổng Remote Code Execution (RCE) — ví dụ qua deserialization không an toàn, command injection, hoặc lỗ hổng trong thư viện C extension.
  2. Kẻ tấn công gửi payload kích hoạt thành công lỗ hổng và giành được quyền thực thi mã shell bên trong container.
  3. Mặc định container chạy bằng `root` (UID 0), nên kẻ tấn công sở hữu toàn quyền root bên trong container.
  4. Nếu máy host tồn tại lỗ hổng container breakout (như lỗ hổng của Linux kernel, runc, hoặc container bị cấu hình ẩu mount volume nhạy cảm / socket docker `/var/run/docker.sock`), kẻ tấn công thực hiện kỹ thuật escape ra ngoài namespace của host.
  5. Vì UID 0 trong container map tương ứng với UID 0 trên kernel host (nếu host không bật user namespace remapping), kẻ tấn công lập tức trở thành root của máy host vật lý và kiểm soát toàn bộ hạ tầng.
- Lệnh `USER appuser` cắt đứt chuỗi ở bước 3 và bước 5:
  Lệnh `USER` chuyển tiến trình sang user không đặc quyền (UID 1000). Kẻ tấn công nếu khai thác RCE thành công cũng chỉ có quyền của user thường, không thể sửa đổi file hệ thống bên trong container (`/etc`, `/usr/bin`), không thể tải kernel module, và nếu có tìm cách breakout ra host thì kernel host vẫn chỉ nhận diện đó là tiến trình không có quyền quản trị, bảo vệ máy host an toàn.

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

- Con số tối đa: **20 request** trong 2 giây liên tiếp.
- Cách đạt được con số đó:
  + Giả sử người dùng gửi 10 request dồn dập vào giây cuối cùng của phút thứ nhất: lúc `10:00:59`. Hệ thống đếm theo phút đồng hồ ghi nhận 10 request trong phút 10:00 (hợp lệ, đúng hạn mức 10/phút).
  + Ngay khi đồng hồ chuyển sang giây `10:01:00`, bộ đếm của phút cũ được reset về 0.
  + Người dùng lập tức gửi tiếp 10 request nữa vào giây `10:01:01`. Hệ thống lại ghi nhận 10 request trong phút 10:01 (vẫn hợp lệ theo phút đồng hồ mới).
  + Kết quả: Trong khoảng thời gian chỉ vỏn vẹn **2 giây** (từ 10:00:59 đến 10:01:01), server phải xử lý tới **20 request liên tiếp** (gấp đôi năng lực dự tính).
  + Với thuật toán Sliding Window 60s của chúng ta: Tại thời điểm 10:01:01, hệ thống tính lùi 60 giây (từ 10:00:01 đến 10:01:01). Cả 10 request trước vẫn nằm trọn trong cửa sổ trượt, do đó request thứ 11 sẽ bị chặn đứng ngay lập tức với mã lỗi 429.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

- Điểm khác biệt:
  + **Rate Limit:** Kiểm soát **tần suất / số lượng request trong một khoảng thời gian ngắn** (ví dụ 10 request/phút) nhằm bảo vệ hạ tầng máy chủ khỏi bị nghẽn mạng, cạn kiệt CPU/RAM do request dồn dập.
  + **Cost Guard:** Kiểm soát **ngân sách tài chính tích lũy trong chu kỳ dài** (ví dụ 10.0 USD/tháng) dựa trên lượng token LLM thực tế tiêu thụ, nhằm bảo vệ ví tiền của nhà phát triển khỏi hóa đơn API khổng lồ.
- Tình huống Rate Limit cho qua nhưng Cost Guard phải chặn:
  Cả tháng người dùng mới gửi request đầu tiên (tần suất 1 req/phút, hoàn toàn không vi phạm rate limit). Tuy nhiên câu hỏi kèm tài liệu đầu vào cực lớn (khoảng 100,000 token) khiến chi phí ước tính vượt quá ngân sách tháng còn lại của người dùng. Cost Guard phát hiện và ném lỗi 402 Payment Required chặn lại ngay trước khi gọi LLM.
- Tình huống Cost Guard cho qua nhưng Rate Limit phải chặn:
  Một người dùng mới đăng ký có nguyên ngân sách $10.0 chưa tiêu một cent nào. Người dùng viết bot gửi liên tục 25 request chỉ trong vòng 3 giây (mỗi request chỉ gửi "Hello", chi phí chỉ tốn $0.00001 mỗi lượt). Tổng chi phí chỉ vài phần nghìn cent nên Cost Guard thấy ngân sách vẫn còn thừa, nhưng Rate Limiter lập tức chặn ở request thứ 11 với mã 429 vì tần suất gọi quá dồn dập vượt quá 10 req/phút.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

Thứ tự sự kiện xảy ra thảm họa (Cascading Failure):
1. Redis gặp sự cố mạng hoặc khởi động lại, tạm thời mất kết nối trong 30 giây.
2. Trình điều phối cụm (Orchestrator) gửi định kỳ probe kiểm tra container.
3. Vì endpoint gộp chung có gọi kiểm tra Redis, nó phát hiện Redis mất kết nối và trả về lỗi 503 / timeout.
4. Orchestrator coi đây là Liveness Probe thất bại -> kết luận rằng toàn bộ 3 container agent đều "đã chết tiến trình hoặc bị treo vĩnh viễn".
5. Orchestrator lập tức ra lệnh kill và restart lại đồng loạt cả 3 container agent.
6. Trong suốt 30 giây Redis chưa phục hồi, cả 3 container agent bị rơi vào vòng xoáy khởi động lại liên tục (CrashLoopBackOff). Mọi kết nối hiện tại của khách hàng bị đứt đột ngột, tài nguyên CPU/RAM của server bị tiêu tốn tối đa cho việc khởi động lại ứng dụng.
7. Khi Redis phục hồi sau 30s, cụm container vẫn chưa thể phục vụ ngay vì còn đang lúng túng trong tiến trình reboot, làm kéo dài thời gian sập hệ thống (downtime).
*Trái lại, khi tách riêng:* `/health` vẫn trả 200 (container không bị restart), chỉ có `/ready` trả 503 (load balancer tạm dừng đẩy request mới vào cho đến khi Redis sẵn sàng lại).

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

- Khi lưu bằng Redis (Stateless - hệ thống hiện tại):
  Do toàn bộ dữ liệu lịch sử nằm tập trung tại Redis, dù Load Balancer có điều phối request lần lượt sang Container 1, Container 2 hay Container 3 thì tất cả container đều đọc chung một nguồn sự thật. Do đó `history_length` tăng đều đặn và tuyến tính: 0 -> 2 -> 4 -> 6 -> 8...
- Nếu lưu trong dict Python (Stateful - lưu trong RAM cục bộ):
  Mỗi container là một process riêng với không gian bộ nhớ RAM độc lập. Khi gọi `/ask` liên tiếp:
  + Request 1 rơi vào Container A: `history_length` = 0 (Container A lưu câu hỏi 1 vào dict của mình).
  + Request 2 rơi vào Container B: `history_length` lại là 0 (vì dict của Container B hoàn toàn trống rỗng).
  + Request 3 rơi vào Container C: `history_length` tiếp tục là 0 (dict của Container C chưa có gì).
  + Request 4 tình cờ quay lại Container A: `history_length` lúc này mới nhảy lên 2.
  + Request 5 rơi vào Container B: `history_length` nhảy lên 2.
  Hậu quả: Con số `history_length` sẽ nhảy lộn xộn, gián đoạn. Người dùng sẽ thấy AI Agent có triệu chứng "mất trí nhớ từng chặp", hoàn toàn không duy trì được mạch hội thoại khi hệ thống scale ngang.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

- **Lỗi gặp phải:** Container không lắng nghe đúng cổng do nền tảng Cloud cung cấp qua biến môi trường `$PORT` (Port Binding Mismatch).
- **Thông báo lỗi trên Cloud logs:**
  `"Cloud Run error: The user-provided container failed to start and listen on the port defined by the PORT environment variable (PORT=8080). Container terminated with exit code 1."`
- **Cách tìm ra nguyên nhân:**
  Mở xem log chi tiết của service trên Cloud Console, tôi nhận thấy Uvicorn trong container khởi động và bind cứng vào cổng mặc định `8000` (do lệnh cũ trong Dockerfile là `CMD ["uvicorn", "app.main:app", "--port", "8000"]`). Tuy nhiên, cơ chế của Cloud Serverless tự động gán một cổng ngẫu nhiên thông qua biến môi trường `$PORT` (thường là 8080 trên Cloud Run). Vì container không lắng nghe trên cổng 8080 mà router cloud chuyển tiếp vào, health probe của cloud bị timeout và đánh dấu container khởi động thất bại.
- **Cách sửa chữa:**
  Điều chỉnh lệnh `CMD` trong Dockerfile để đọc động giá trị từ biến `$PORT` (và fallback về 8000 nếu chạy local):
  `CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]`
  Đồng thời trong `app/config.py`, lớp `Settings` của Pydantic cũng tự động đọc biến `PORT` từ môi trường. Sau khi rebuild và redeploy, service lập tức bắt đúng cổng 8080 và chuyển sang trạng thái Ready.
