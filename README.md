# OCR Image Text Extraction API

A production-ready serverless OCR API deployed on Google Cloud Run. Extract text from images with intelligent caching and structured logging.

**Live API**: `https://ocr-api-663394155406.asia-southeast1.run.app`

---

## Quick Start

### Test the API

```bash
# Extract text from invoice
curl -X POST -F "image=@testimages/invoice.jpg" \
  https://ocr-api-663394155406.asia-southeast1.run.app/extract-text

# Extract from handwritten note
curl -X POST -F "image=@testimages/note.png" \
  https://ocr-api-663394155406.asia-southeast1.run.app/extract-text

# Check health
curl https://ocr-api-663394155406.asia-southeast1.run.app/health
```

### Interactive Docs

**Swagger UI**: https://ocr-api-663394155406.asia-southeast1.run.app/docs

---

## Features

- **OCR**: Extract text from JPG, PNG, GIF, WebP, BMP images
- **Batch Processing**: Process up to 10 images at once
- **Smart Caching**: LRU cache with 1000 entries, 1-hour TTL (~50% cost savings)
- **Multi-Language**: Auto-detects 50+ languages
- **Production-Ready**: Serverless, auto-scales, structured logging

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/extract-text` | POST | Extract text from single image |
| `/batch-extract` | POST | Extract text from multiple images |
| `/health` | GET | Health check |

**Example**:
```bash
curl -X POST -F "image=@testimages/invoice.jpg" \
  https://ocr-api-663394155406.asia-southeast1.run.app/extract-text
```

**Response**:
```json
{
  "success": true,
  "text": "INVOICE\nTotal: $125.00",
  "confidence": 0.98,
  "processing_time_ms": 45,
  "metadata": {
    "cached": true,
    "language": "en"
  }
}
```

---

## Local Development

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Authenticate
gcloud auth application-default login

# Run
uvicorn main:app --reload --port 8080
```

Visit: http://localhost:8080/docs

---

## Deployment

**Runs on Python 3.12** in Google Cloud Run Docker container:

```bash
# Deploy to Google Cloud Run
bash scripts/deploy.sh

# Test deployment (23 automated tests)
bash scripts/comprehensive_test.sh
```

---

## Documentation

### For API Users
- **Swagger UI**: https://ocr-api-663394155406.asia-southeast1.run.app/docs (Interactive API documentation)
- **[README.md](README.md)** - Quick start and examples

### For Developers
- **[PROJECT.md](PROJECT.md)** - Complete technical documentation (architecture, deployment, costs, testing)
- **Code**: Clean, well-structured Python modules with clear comments

---

## Architecture

```
Client → Cloud Run → Validators → OCR Service → Google Vision API
                         ↓             ↓
                    Middleware    LRU Cache (1000 entries, 1hr TTL)
                         ↓             
                    Rate Limiter  
                         ↓             
                    Logger (Cloud Logging)
```

**Tech Stack**: FastAPI, Google Cloud Vision API, Cloud Run, Python 3.12

---

## Configuration

Key environment variables:
```bash
GOOGLE_CLOUD_PROJECT=your-project-id
MAX_FILE_SIZE_MB=10
MAX_CACHE_SIZE=1000
CACHE_TTL_SECONDS=3600
RATE_LIMIT_ENABLED=false
```

See [PROJECT.md](PROJECT.md#configuration) for complete configuration guide.

---

## Performance & Costs

**Response Times**:
- Cache hit: <50ms
- Cache miss: 200-500ms

**Costs** (with 50% cache hit rate):
- 1,000 requests/month: **$0** (free tier)
- 5,000 requests/month: **~$2.75**
- 20,000 requests/month: **~$12.50**

See [PROJECT.md](PROJECT.md#costs) for detailed cost analysis.

---

## Testing

```bash
# Run test suite (23 automated tests)
bash scripts/comprehensive_test.sh
```

---

## Support

- **Issues**: Check PROJECT.md for technical details and implementation information
- **API Docs**: [Swagger UI](https://ocr-api-663394155406.asia-southeast1.run.app/docs) (Interactive documentation)
- **Project Details**: [PROJECT.md](PROJECT.md) (Complete technical guide)

---

**Status**: Production Ready | **Version**: 1.0.0 | **Updated**: 2025-01-20
