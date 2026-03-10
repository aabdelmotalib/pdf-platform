# ⚡ Celery Worker - Quick Reference

## 🚀 Start Worker

```bash
cd /home/abdelmoteleb/pdf-platform
celery -A worker.main worker --loglevel=info --concurrency=2
```

## 📊 Monitor Tasks

```bash
# Dashboard
celery -A worker.main flower --port=5555
# Access: http://localhost:5555

# Logs
docker-compose logs -f celery_worker

# Active tasks
redis-cli LRANGE celery 0 -1
```

## 📁 File Structure

```
/worker/
├── celery_config.py      ← Celery app (Redis broker/backend)
├── main.py               ← Entry point (start here)
├── __init__.py
└── tasks/
    ├── convert.py        ← Main task: convert_file(job_id)
    ├── processors.py     ← 8 conversion functions
    ├── redis_lock.py     ← Distributed lock for LibreOffice
    └── __init__.py
```

## 🔄 Conversion Processors (8)

| Processor | Input | Output | Lock | Time |
|-----------|-------|--------|------|------|
| `pdf_to_word` | PDF | DOCX | ✅ | 120s |
| `pdf_to_excel` | PDF | XLSX | ✅ | 120s |
| `pdf_to_image` | PDF | JPEG | ❌ | 30s |
| `word_to_pdf` | DOCX | PDF | ✅ | 120s |
| `pdf_merge` | [PDF...] | PDF | ❌ | 60s |
| `pdf_split` | PDF,[pages] | PDF | ❌ | 30s |
| `pdf_annotate` | PDF,annot[] | PDF | ❌ | 30s |
| `pdf_watermark` | PDF,text | PDF | ❌ | 30s |

## ⚙️ Configuration

File: `/worker/celery_config.py`

```python
BROKER = redis://localhost:6379/0
BACKEND = redis://localhost:6379/0
SERIALIZER = json
TASK_TIMEOUT = 120s (warning), 150s (kill)
MAX_RETRIES = 3
RETRY_DELAY = 60s
CONCURRENCY = 2 tasks
```

## 🔒 Distributed Locking

LibreOffice operations use Redis-backed distributed lock:

```python
# Automatic - used internally
lock = get_libreoffice_lock()
with lock:
    pdf_to_word(input_path)  # Only 1 runs at a time
```

## 💾 Database Updates

Job status progression:
```
queued (0%)
  → processing (10-85%)
    → completed (100%) ✅
    → failed (0%) ❌
```

## 🎯 Watermarking

Applied automatically for free tier:
```
- Diagonal text: "WATERMARK - Free Tier"
- Angle: 45 degrees
- Color: Light gray
- Applied before upload
```

## 📝 Task Retry Logic

```python
# Max retries: 3
# Delay: 60 seconds
# Exponential: Increases on each retry

Try 1 → Fail → Wait 60s
Try 2 → Fail → Wait 120s (2x)
Try 3 → Fail → Wait 180s (3x)
Try 4 → Fail → Error (give up)
```

## 🧪 Test

```bash
# 1. Ensure services running
docker-compose up -d

# 2. Start worker
celery -A worker.main worker --loglevel=info

# 3. Upload file
curl -X POST http://localhost:8000/upload/files \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@sample.pdf"

# 4. Check status
curl http://localhost:8000/upload/jobs/{job_id}/status \
  -H "Authorization: Bearer TOKEN"

# 5. Watch worker logs
docker-compose logs -f celery_worker
```

## 🐛 Debug Mode

```bash
# Verbose logging
celery -A worker.main worker --loglevel=debug

# Single threaded (easier debugging)
celery -A worker.main worker --loglevel=debug --concurrency=1 --without-gossip --without-mingle --without-heartbeat
```

## 🔧 Common Issues

| Issue | Fix |
|-------|-----|
| Worker not starting | Check Redis: `redis-cli ping` |
| Tasks stuck | Check locks: `redis-cli KEYS "lock:*"` |
| LibreOffice hangs | Increase timeout in config |
| Memory leak | Restart worker regularly |
| MinIO upload fails | Check credentials in config |
| Database connection error | Verify DATABASE_URL |

## 🚨 Kill Stuck Tasks

```bash
# Find task ID
celery -A worker.main inspect active

# Revoke task
celery -A worker.main revoke TASK_ID --terminate

# Clear queue
redis-cli DEL celery
```

## 📊 Stats

```bash
# Active workers
celery -A worker.main inspect active

# Queue length
redis-cli LLEN celery

# Task stats
celery -A worker.main inspect stats
```

## 🔐 Environment Variables

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
DATABASE_URL=postgresql+asyncpg://...
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

## 📦 Required System Packages

```bash
# LibreOffice (PDF↔Word/Excel)
sudo apt-get install libreoffice

# Poppler (PDF→Image)
sudo apt-get install poppler-utils

# Optional
sudo apt-get install imagemagick  # Future use
```

## 🎯 Performance Tips

- **Concurrency=2:** Safe for most servers
- **Concurrency=4:** Needs 4+ CPU cores, 2GB RAM
- **Timeout=120s:** Good for files < 100MB
- **Timeout=300s:** For large files (slow servers)

---

**Ready to process files!** 🚀

```bash
celery -A worker.main worker --loglevel=info --concurrency=2
```
