# File Upload Pipeline - Quick Reference

## Endpoints

| Method | URL | Auth | Status | Response |
|--------|-----|------|--------|----------|
| POST | `/upload/files` | ✅ | 202 | job_id, status |
| GET | `/upload/jobs/{job_id}/status` | ✅ | 200 | status, progress, download_url |

---

## Upload File

### Request
```bash
curl -X POST "http://localhost:8000/upload/files" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "file=@document.pdf"
```

### Response
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "File uploaded successfully and queued for processing"
}
```

### Errors
- `202` - Success (file queued)
- `400` - Bad request
- `401` - Unauthorized (no token)
- `403` - Forbidden (no subscription or limit reached)
- `413` - File too large
- `422` - Invalid MIME type or virus detected
- `500` - Server error (MinIO/DB)

---

## Check Job Status

### Request
```bash
curl -X GET "http://localhost:8000/upload/jobs/550e8400-e29b-41d4-a716-446655440000/status" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Response (Processing)
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 50,
  "created_at": "2025-03-09T10:30:00Z",
  "started_at": "2025-03-09T10:31:00Z"
}
```

### Response (Completed)
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "output_file_path": "jobs/123/550e8400.../output.pdf",
  "download_url": "https://minio:9000/...",
  "completed_at": "2025-03-09T10:35:00Z"
}
```

### Status Values
- `queued` - Waiting (progress: 0%)
- `processing` - Running (progress: 50%)
- `completed` - Done (progress: 100%)
- `failed` - Error (check error_message)

---

## Validation Pipeline

1. **JWT Token** - Must be valid access token
2. **Active Subscription** - Must have non-expired plan
3. **File Size** - Must be < plan.file_size_limit_mb MB
4. **Session Files** - Count < plan.max_files_per_session
5. **Magic Bytes** - Must be allowed MIME type
6. **ClamAV Scan** - Must pass virus scan

---

## Allowed File Types

| Type | MIME | Extension |
|------|------|-----------|
| PDF | application/pdf | .pdf |
| Word (old) | application/msword | .doc |
| Word (new) | application/vnd.openxmlformats-officedocument.wordprocessingml.document | .docx |
| Excel (old) | application/vnd.ms-excel | .xls |
| Excel (new) | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet | .xlsx |
| JPEG | image/jpeg | .jpg, .jpeg |
| PNG | image/png | .png |

---

## Plan Limits

See `/auth/me` response for current plan:

```json
{
  "subscriptions": [
    {
      "plan": {
        "name": "free",
        "max_files_per_month": 1,
        "file_size_limit_mb": 2,
        "rate_limit_per_hour": null
      }
    }
  ]
}
```

---

## JavaScript Example

```javascript
// Get access token (from login)
const token = localStorage.getItem('access_token');

// Upload file
const file = document.getElementById('fileInput').files[0];
const formData = new FormData();
formData.append('file', file);

const uploadResponse = await fetch('/upload/files', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
}).then(r => r.json());

const jobId = uploadResponse.job_id;

// Poll for status
setInterval(async () => {
  const status = await fetch(`/upload/jobs/${jobId}/status`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }).then(r => r.json());

  console.log(`Status: ${status.status}, Progress: ${status.progress}%`);

  if (status.status === 'completed') {
    // Download file or show success
    window.open(status.download_url, '_blank');
  }
}, 2000);  // Poll every 2 seconds
```

---

## Python Example

```python
import requests
import time

token = "your_access_token"
headers = {"Authorization": f"Bearer {token}"}

# Upload file
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:8000/upload/files',
        headers=headers,
        files=files
    )

job_id = response.json()['job_id']
print(f"Job ID: {job_id}")

# Poll for status
while True:
    status = requests.get(
        f'http://localhost:8000/upload/jobs/{job_id}/status',
        headers=headers
    ).json()
    
    print(f"Status: {status['status']}, Progress: {status['progress']}%")
    
    if status['status'] == 'completed':
        print(f"Download: {status['download_url']}")
        break
    elif status['status'] == 'failed':
        print(f"Error: {status['error_message']}")
        break
    
    time.sleep(2)  # Poll every 2 seconds
```

---

## Configuration

### Environment Variables
```bash
# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false

# ClamAV
CLAMAV_HOST=localhost
CLAMAV_PORT=3310

# Database
POSTGRES_DSN=postgresql+asyncpg://postgres:password@localhost:5432/db
```

### Plan Limits (From Database)
```
Free Plan:
  - max_files_per_month: 1
  - file_size_limit_mb: 2
  - rate_limit_per_hour: null

Hourly Plan:
  - max_files_per_month: 3
  - file_size_limit_mb: 5
  - rate_limit_per_hour: 60

Monthly Plan:
  - max_files_per_month: unlimited (-1)
  - file_size_limit_mb: 5
  - rate_limit_per_hour: null
```

---

## MinIO Buckets

```
input-files/
├── jobs/
│   ├── {user_id}/
│   │   ├── {job_id}/
│   │   │   └── original_filename.pdf

output-files/
├── jobs/
│   ├── {user_id}/
│   │   ├── {job_id}/
│   │   │   └── converted_file.pdf
```

---

## Error Handling

| Error | Code | Solution |
|-------|------|----------|
| "File size exceeds limit" | 413 | Upload smaller file or upgrade plan |
| "File limit reached" | 403 | Wait 24h or upgrade to unlimited |
| "File type not allowed" | 422 | Use PDF, Word, Excel, PNG, or JPEG |
| "Malware detected" | 422 | File is infected, use different file |
| "No active subscription" | 403 | Subscribe to a plan first |
| "Invalid token" | 401 | Login and get new access token |

---

## Testing Checklist

- [ ] Login and get access_token
- [ ] Upload small PDF file (should succeed)
- [ ] Check job status (should show progress)
- [ ] Upload large file (should fail with 413)
- [ ] Upload unsupported file type (should fail with 422)
- [ ] Check download URL after completion
- [ ] Verify file in MinIO bucket
- [ ] Verify job record in PostgreSQL

---

## API Documentation

Interactive testing: **http://localhost:8000/docs**

---

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `/api/services/storage.py` | MinIO operations | 220 |
| `/api/routers/upload.py` | Upload endpoints | 380 |
| `config.py` | Upload settings | Added 25 lines |
| `main.py` | Include upload router | Updated |
| `requirements.txt` | Add pyclamd | Updated |
| `schemas/__init__.py` | Upload schemas | Added 40 lines |

---

## Status Diagram

```
Upload file
   ↓
Validation (JWT, Sub, Size, Count)
   ↓
Magic Bytes check
   ↓
ClamAV scan
   ↓
MinIO upload → 202 Accepted
   ↓              ↓
Job created    Return job_id
   ↓
Celery task pushed
   ↓
Client polls GET /status
   ↓
Status progresses: queued → processing → completed
   ↓
Download URL available when done
```

---

**Ready to use! Upload files now with** `/upload/files` 🚀
