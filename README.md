# 🛡️ IssueSpotter AI Guardian

> **Lightweight AI-powered content moderation microservice** for images, videos, and text

## Overview

IssueSpotter AI Guardian is a specialized microservice that analyzes user-generated content (posts, images, videos) and provides intelligent moderation decisions using state-of-the-art AI models.

**Core Mission:** Act as a guardian layer between user submissions and the main backend, automatically filtering spam, NSFW content, duplicates, and toxic posts while letting genuine civic issues through.

## Key Features

### Three-Tier Decision System

- **GREEN** (score < 0.3): Auto-approve safe content
- **YELLOW** (score 0.3-0.8): Escalate to human moderator
- **RED** (score > 0.8): Auto-reject violating content

### AI Models

- **Text Embeddings**: `all-MiniLM-L6-v2` (384-dimensional)
- **Image Embeddings**: `CLIP ViT-B/32` (512-dimensional)
- **NSFW Detection**: `NudeNet`
- **Video Analysis**: Frame-by-frame (1 frame/2 seconds)

### Capabilities

- NSFW image detection
- Video frame analysis
- Duplicate detection via vector similarity
- Learning from past moderator decisions (RAG)
- Webhook notifications with retry logic
- Human-in-the-loop (HITL) dashboard

## Quick Start

### Installation

```bash
uv sync

cp .env.example .env

uv run uvicorn app.main:app --reload --port 8000

uv run python scripts/demo_guardian.py
```

### Configuration

```env
ENVIRONMENT=development
QDRANT_HOST=localhost
QDRANT_PORT=6333
AI_THRESHOLD_GREEN=0.3
AI_THRESHOLD_RED=0.8
MAIN_BACKEND_WEBHOOK_URL=http://your-backend/webhook
```

## API Endpoints

### Classify Content

```http
POST /api/v1/moderation/classify
{
  "issue_id": "post-123",
  "title": "Pothole on Main St",
  "description": "Large pothole...",
  "image_paths": ["https://..."],
  "video_paths": []
}
```

### HITL Dashboard

```http
GET  /api/v1/dashboard/pending
POST /api/v1/dashboard/review
GET  /api/v1/dashboard/stats
```

### Health Check

```http
GET /health
```

## Testing

```bash
uv run pytest

uv run pytest --cov=app

uv run pytest tests/unit/
```

## Project Structure

```
app/
├── ai/                  # AI models
│   ├── text_embedder.py
│   ├── image_embedder.py
│   ├── image_analyser.py
│   └── video_analyzer.py
├── api/v1/              # REST API
│   ├── moderation.py
│   └── dashboard.py
├── pipelines/           # Decision pipeline
│   └── moderation/
│       └── classifier.py
├── services/            # Core services
│   ├── vector_service.py
│   ├── webhook_service.py
│   └── moderation_service.py
└── config/
    └── settings.py
```

## Tech Stack

- **FastAPI** - Async web framework
- **Transformers** - HuggingFace models
- **Qdrant** - Vector database
- **NudeNet** - NSFW detection
- **OpenCV** - Video processing

## Performance

- Text analysis: ~50ms
- Image analysis: ~200ms
- Video (60s): ~2s
- Vector search: ~30ms

## Docker

```bash
docker-compose up -d
```

---
