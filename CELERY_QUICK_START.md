# 🎯 Celery Worker - Quick Start

## 60-Second Setup

### 1. Install Dependencies
```bash
cd /home/abdelmoteleb/pdf-platform

# Install worker packages
pip install -r requirements.txt

# Install system dependencies
sudo apt-get update
sudo apt-get install -y libreoffice poppler-utils
```

### 2. Start Services
```bash
# Start Redis, PostgreSQL, MinIO, etc.
docker-compose up -d
```

### 3. Start Worker
```bash
cd /home/abdelmoteleb/pdf-platform
celery -A worker.main worker --loglevel=info --concurrency=2
```

**Expected Output:**
```
-------------- celery@worker_hostname v5.3.4 (emerald-rush)
--- ***** ----- 
-- ******* ----
- *** --- * ---
- ** ---------- [config]
- ** ---------- .broker: redis://localhost:6379/0
- ** ---------- .concurrency: 2 (prefork)
--- ******* ----
-- ******* ---- [queues]
-------------- celery@worker
  . worker.tasks.convert.convert_file
  . worker.tasks.convert.test_conversion_task

[2026-03-09 14:30:00,000: INFO/MainProcess] celery@worker ready.
```

### 4. Upload Test File
```bash
# Get token first
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# Upload file
JOB_ID=$(curl -X POST http://localhost:8000/upload/files \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample.pdf" \
  | grep -o '"job_id":"[^"]*' | cut -d'"' -f4)

echo "Job ID: $JOB_ID"
```

### 5. Monitor Progress
```bash
# Poll status
while true; do
  curl http://localhost:8000/upload/jobs/$JOB_ID/status \
    -H "Authorization: Bearer $TOKEN" \
    -s | jq .
  sleep 2
done
```

### 6. View Dashboard
```
http://localhost:5555  (Flower - Celery monitoring)
```

---

## 📂 What's Running

| Component | URL/Command | Status |
|-----------|-----------|--------|
| FastAPI | http://localhost:8000 | Running |
| Swagger UI | http://localhost:8000/docs | Running |
| PostgreSQL | localhost:5432 | Running |
| Redis | localhost:6379 | Running |
| MinIO | http://localhost:9000 | Running |
| Celery Worker | Terminal window | Running (if you started it) |
| Flower Dashboard | http://localhost:5555 | Running (if you started it) |

---

## 🔄 Task Lifecycle

```
1. User uploads file
   ↓
2. API queues task: convert_file.delay(job_id)
   ↓
3. CELERY WORKER picks up task
   ↓
4. Worker processes:
   - Downloads file from MinIO
   - Detects format
   - Acquires lock (if needed)
   - Runs conversion (120s timeout)
   - Applies watermark (if free tier)
   - Uploads result
   - Updates database
   ↓
5. User polls /jobs/{id}/status
   ↓
6. Gets presigned download URL
```

---

## 📊 8 Conversion Options

Worker supports these conversions:

```python
"pdf_to_word"    # PDF → DOCX (LibreOffice)
"pdf_to_excel"   # PDF → XLSX (LibreOffice)
"pdf_to_image"   # PDF → JPEG (pdf2image, DPI=200)
"word_to_pdf"    # DOCX → PDF (LibreOffice)
"pdf_merge"      # [PDF...] → merged.pdf (pypdf)
"pdf_split"      # PDF + pages → split.pdf (pypdf)
"pdf_annotate"   # PDF + notes → annotated.pdf (PyMuPDF)
"pdf_watermark"  # PDF + text → watermarked.pdf (auto for free tier)
```

---

## 🐛 Troubleshooting

### Worker Not Starting?
```bash
# Check Redis
redis-cli ping  # Should say PONG

# Check Python
python3 -c "from worker.main import app; print('OK')"

# Check imports
python3 -c "from worker.tasks.convert import convert_file; print('OK')"
```

### Task Not Processing?
```bash
# Check queue
redis-cli LLEN celery  # Should show pending count

# Check worker logs (in worker terminal)
# Look for: "Starting conversion task for job"

# Check Flower
# http://localhost:5555/tasks
```

### LibreOffice Hangs?
```bash
# Tasks may wait for lock
# Check active locks
redis-cli KEYS "lock:*"

# Force release lock
redis-cli DEL lock:libreoffice:execution
```

### Increase Timeout
```bash
# Edit: /worker/celery_config.py
task_soft_time_limit=300  # Up from 120
task_time_limit=330       # Up from 150

# Restart worker
```

---

## 📝 Example: Full Workflow

```bash
#!/bin/bash

# 1. Register user (if needed)
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'

# 2. Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"

# 3. Upload PDF
JOB=$(curl -s -X POST http://localhost:8000/upload/files \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample.pdf")

JOB_ID=$(echo $JOB | jq -r '.job_id')
echo "Job ID: $JOB_ID"

# 4. Check status (loop)
for i in {1..30}; do
  STATUS=$(curl -s http://localhost:8000/upload/jobs/$JOB_ID/status \
    -H "Authorization: Bearer $TOKEN" | jq '.')
  
  echo "[$i] Status: $(echo $STATUS | jq -r '.status') Progress: $(echo $STATUS | jq -r '.progress')%"
  
  # If complete, download
  if [ "$(echo $STATUS | jq -r '.status')" == "completed" ]; then
    DOWNLOAD_URL=$(echo $STATUS | jq -r '.download_url')
    echo "✅ Complete! Download: $DOWNLOAD_URL"
    break
  fi
  
  sleep 5
done
```

---

## 🎯 Key Files

| File | Purpose | Edit? |
|------|---------|-------|
| `/worker/celery_config.py` | Celery config | ⚙️ If timeout issues |
| `/worker/main.py` | Start command | ❌ Leave as-is |
| `/worker/tasks/convert.py` | Conversion logic | ❌ Leave as-is |
| `/worker/tasks/processors.py` | Conversion functions | ✅ Add new processors here |
| `/worker/tasks/redis_lock.py` | Locking | ❌ Leave as-is |

---

## 💡 Tips

✅ **Monitor in separate terminal:**
```bash
# Terminal 1: Worker
celery -A worker.main worker --loglevel=info

# Terminal 2: Flower
celery -A worker.main flower --port=5555

# Terminal 3: Tests/uploads
curl ... (your commands)
```

✅ **Increase logging if issues:**
```bash
celery -A worker.main worker --loglevel=debug
```

✅ **Single-threaded mode for debugging:**
```bash
celery -A worker.main worker --concurrency=1 --loglevel=debug
```

✅ **Watch logs in real-time:**
```bash
docker-compose logs -f celery_worker
```

---

## ✅ Validation

All files compiled and validated:
```
✅ celery_config.py compiled
✅ tasks/convert.py compiled
✅ tasks/processors.py compiled
✅ tasks/redis_lock.py compiled
✅ main.py compiled
✅ API integration verified
✅ Requirements updated
```

---

## 🚀 You're Ready!

```bash
celery -A worker.main worker --loglevel=info --concurrency=2
```

**The system is now processing files asynchronously!** 🎉

Need help? Check `CELERY_WORKER_GUIDE.md` for full documentation.
