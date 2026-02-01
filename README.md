# IssueSpotter – AI‑Powered Civic Issue Discovery & Moderation Platform

## 1. Project Overview

IssueSpotter is a large‑scale civic engagement platform designed to allow citizens to report, discover, discuss, and escalate real‑world issues ranging from hyper‑local infrastructure problems (potholes, garbage, water leakage) to city‑wide, state‑level, or national concerns (health outbreaks, governance failures, environmental risks).

The platform intentionally blends interaction paradigms from **community discussion platforms (Reddit‑like)** and **professional issue visibility networks (LinkedIn‑like)**, while grounding every post in **geographic and administrative reality**. The core differentiator of IssueSpotter is **signal over noise**: ensuring that genuine, actionable issues surface while spam, duplicates, misinformation, rage‑bait, and low‑quality content are systematically filtered out using AI‑driven pipelines.

This repository represents the **AI/ML, moderation, ranking, and intelligence layer** of the IssueSpotter system, designed to integrate with an Android application and backend services built independently.

---

## 2. Problem Statement

Modern civic platforms fail in three major ways:

1. **Noise Dominance** – Genuine issues get buried under reposts, emotionally charged but low‑value content, memes, or irrelevant discussions.
2. **Lack of Geographic Grounding** – Many platforms lack structured location hierarchies, making it difficult to understand scope, severity, and jurisdiction.
3. **No Trust Gradient** – Posts from credible users and first‑hand reporters are treated the same as spam accounts or opportunistic engagement farmers.

IssueSpotter addresses these gaps by combining:

- Hierarchical geo‑structuring
- AI‑based content understanding
- Trust, credibility, and engagement modeling
- Automated issue deduplication and escalation

---

## 3. Core Design Philosophy

The platform is designed around the following principles:

- **Geography First** – Every issue is tied to a well‑defined administrative hierarchy.
- **AI as Infrastructure, Not Feature** – Machine learning operates continuously in the background to clean, rank, and contextualize content.
- **Human‑Centric Escalation** – AI assists moderators and authorities rather than replacing accountability.
- **Explainability & Control** – Every automated decision can be inspected, overridden, or tuned.
- **Scalability from Day One** – Designed to handle millions of posts across regions.

---

## 4. Geographic & Administrative Hierarchy Model

All issues are indexed using a strict multi‑level hierarchy:

```
Country
 └── State
     └── City
         └── District
             └── Locality
```

### Purpose of Hierarchy

- Enables **localized feeds** (what matters near me)
- Enables **jurisdiction mapping** (who is responsible)
- Enables **escalation logic** (local → district → city → state)
- Enables **duplicate detection** within geographic bounds

Each issue is stored with:

- Primary location (mandatory)
- Optional secondary affected regions
- Geo‑coordinates (when available)

---

## 5. High‑Level System Architecture

### 5.1 Client Layer (Android App)

- Issue creation & media upload
- Feed browsing (location‑aware)
- Voting, commenting, sharing
- User profile & reputation view

### 5.2 Backend Services (Non‑AI)

- Authentication & authorization
- User management
- Post storage & retrieval
- Media storage (S3 or equivalent)
- API gateways

### 5.3 AI & Intelligence Layer (This Project)

Responsible for:

- Content understanding
- Moderation
- Ranking
- Deduplication
- Escalation scoring
- Abuse prevention

---

## 6. AI/ML Responsibilities (Detailed)

### 6.1 Content Ingestion Pipeline

When a user submits an issue:

1. Text, images, and metadata are extracted
2. Text is cleaned and normalized
3. Media is pre‑processed for downstream analysis

### 6.2 Issue Classification

Each post is automatically classified into:

- Issue category (infrastructure, health, safety, governance, environment, etc.)
- Severity level (low, medium, high, critical)
- Temporal nature (one‑time, recurring, ongoing)

This allows structured filtering and prioritization.

### 6.3 Duplicate & Near‑Duplicate Detection

A core challenge is preventing repost storms.

Approach:

- Generate semantic embeddings for issue text
- Compare embeddings within the same geographic boundary
- Use cosine similarity + temporal proximity
- Cluster near‑identical reports

Outcome:

- Users are redirected to existing issues
- Engagement is consolidated
- Authorities see a single amplified signal instead of noise

---

## 7. AI‑Driven Moderation System

### 7.1 Automated Content Filtering

Each post is scored across multiple dimensions:

- Spam likelihood
- Hate or abuse probability
- Misinformation risk
- Sensationalism / rage‑bait patterns

Posts may be:

- Published immediately
- Soft‑limited (reduced reach)
- Sent for human review
- Rejected with explanation

### 7.2 Context‑Aware Moderation

Moderation decisions consider:

- Local language usage
- Regional slang
- Crisis context (e.g., disasters)

This avoids over‑moderation during emergencies.

---

## 8. Ranking & Feed Intelligence

### 8.1 Issue Ranking Factors

Feeds are not chronological by default.

Ranking is computed using:

- Severity score
- Number of unique reporters
- Engagement quality (not raw likes)
- User credibility
- Freshness decay
- Geographic proximity

### 8.2 Trust & Credibility Modeling

Each user accumulates a **credibility score** based on:

- Historical accuracy of reports
- Community validation
- Moderator confirmations
- Account age & behavior patterns

High‑credibility users amplify issue visibility faster.

---

## 9. Escalation & Authority Routing

Issues automatically escalate when:

- Engagement crosses thresholds
- Severity remains unresolved over time
- Multiple localities report the same issue

Escalation triggers:

- District‑level visibility
- City or state dashboards
- External authority notifications (future scope)

---

## 10. Technology Stack

### 10.1 Core Languages

- Python (AI & ML pipelines)
- Kotlin / Java (Android client – external)

### 10.2 Machine Learning & NLP

- Transformer‑based language models
- Sentence embeddings for similarity search
- Topic modeling & clustering

### 10.3 Vector Storage

- **Qdrant** for semantic similarity and clustering
- 384-dimensional embeddings using `all-miniLM-L6-V2` model
- Cosine similarity for finding related content
- Real-time duplicate detection
- Retrieval-Augmented Generation (RAG) for learning from past decisions

### 10.4 Orchestration

- LangChain for pipeline composition

### 10.5 Infrastructure

- Azure cloud deployment
- Containerized services (Docker)
- REST / gRPC APIs

### 10.6 Storage

- Relational DB for metadata
- Object storage for media

---

## 11. Scalability & Performance Considerations

- Horizontal scaling of embedding services
- Async ingestion pipelines
- Caching of hot feeds
- Batched similarity searches

The system is designed to scale from a single city to national‑level traffic.

---

## 12. Security & Abuse Prevention

- Rate limiting per user & region
- Bot behavior detection
- Shadow banning for malicious actors
- Audit logs for moderation actions

---

## 13. Future Roadmap

- Multimodal issue understanding (image + text fusion)
- Authority dashboards
- Public transparency reports
- Predictive issue outbreak detection
- Cross‑region issue correlation

---

## 14. Conclusion

IssueSpotter is not just a posting platform; it is a **civic intelligence system**. By combining structured geography, AI‑driven moderation, and trust‑aware ranking, it aims to convert scattered citizen complaints into actionable, prioritized, and verifiable civic signals.

This repository defines the foundation for that intelligence layer and is built to evolve alongside real‑world governance complexity.

```arduino
issuespotter-backend/
│
├── app/
│   ├── main.py                # FastAPI entry
│   ├── config/
│   │   ├── settings.py        # env vars
│   │   └── logging.py
│   │
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── issues.py
│   │   │   ├── feed.py
│   │   │   └── moderation.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── issue.py
│   │   ├── report.py
│   │   └── moderation.py
│   │
│   ├── services/
│   │   ├── issue_service.py
│   │   ├── feed_service.py
│   │   ├── moderation_service.py
│   │
│   ├── pipelines/
│   │   ├── moderation/
│   │   │   ├── __init__.py
│   │   │   ├── rules.py
│   │   │   ├── preprocessor.py
│   │   │   ├── classifier.py      # placeholder
│   │   │   ├── decision.py
│   │   │   └── hitl.py
│   │
│   ├── workers/
│   │   ├── celery_app.py
│   │   ├── moderation_worker.py
│   │
│   ├── db/
│   │   ├── session.py
│   │   └── migrations/
│   │
│   └── utils/
│       ├── geo.py
│       ├── text.py
│       └── enums.py
│
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.worker
│   └── docker-compose.yml
│
├── tests/
│
└── README.md
```

---

<!--
## 15. Vector Database Integration (Phase 3)

### 15.1 Overview

The AI microservice now includes **VectorService**, a critical component that gives the system "long-term memory" through Qdrant vector database integration.

### 15.2 What VectorService Does

1. **Duplicate Detection**
   - Automatically detects when users report the same issue multiple times
   - Uses semantic similarity (90%+ threshold) to identify duplicates
   - Prevents spam and consolidates engagement

2. **Similar Issue Search**
   - Finds semantically similar posts based on content
   - Returns results ranked by cosine similarity
   - Supports time-based filtering (e.g., last 24 hours)

3. **Learning from Past Decisions (RAG)**
   - Queries similar past moderation decisions
   - Uses human moderator feedback to inform AI decisions
   - Continuously improves without model retraining

### 15.3 Architecture

```
Post Submission
    ↓
Text Embedder (all-miniLM-L6-V2)
    ↓
384-dimensional vector
    ↓
VectorService.upsert_embedding()
    ↓
Qdrant Collection
    ↓
[Future queries use similarity search]
```

### 15.4 Setup & Configuration

#### Docker Compose Setup

Qdrant is already configured in `docker/docker-compose.yml`:

```bash
cd docker
docker compose up -d qdrant
```

This starts Qdrant on:

- REST API: `http://localhost:6333`
- gRPC API: `http://localhost:6334`

#### Environment Variables

Add to your `.env` file:

```env
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=issue_embeddings
```

### 15.5 VectorService API

#### Initialize Collection

```python
from app.services.vector_service import VectorService

# Creates collection if it doesn't exist
VectorService.initialize_collection()
```

#### Store Embedding

```python
VectorService.upsert_embedding(
    issue_id="issue-123",
    embedding=[0.123, 0.456, ...],  # 384-dimensional vector
    metadata={
        "title": "Pothole on Main Street",
        "description": "Large pothole causing issues",
        "ai_decision": "APPROVE",
        "moderation_score": 0.85
    }
)
```

#### Find Similar Issues

```python
similar = VectorService.find_similar(
    embedding=query_embedding,
    limit=5,
    score_threshold=0.8,
    time_window_hours=24  # Optional: only search recent issues
)

# Returns:
# [
#   {
#     "issue_id": "issue-456",
#     "similarity_score": 0.95,
#     "title": "Big hole on Main Street",
#     "ai_decision": "APPROVE",
#     ...
#   }
# ]
```

#### Detect Duplicates

```python
duplicate = VectorService.detect_duplicates(
    embedding=query_embedding,
    similarity_threshold=0.90,
    time_window_hours=24
)

if duplicate:
    print(f"Duplicate of {duplicate['issue_id']}")
```

#### Get Similar Decisions (RAG)

```python
past_decisions = VectorService.get_similar_decisions(
    embedding=query_embedding,
    limit=3
)

# Use to inform AI decision based on past human feedback
```

### 15.6 Integration in Moderation Pipeline

The VectorService is integrated into the moderation workflow:

1. **Text Processing**: `AIClassifier` generates embeddings for title + description
2. **Duplicate Check**: Checks Qdrant for very similar recent posts
3. **RAG Lookup**: Finds similar past cases to inform decision
4. **Storage**: After moderation, embedding is stored in Qdrant
5. **Feedback Loop**: When moderators review, their decision updates the payload

### 15.7 Performance Characteristics

- **Query Latency**: ~10-50ms for similarity search
- **Scalability**: Handles millions of vectors efficiently
- **Accuracy**: Cosine similarity achieves 99%+ for identical content
- **Storage**: ~1.5KB per embedding (384 floats)

### 15.8 Testing

Run the basic VectorService test:

```bash
python test_vector_basic.py
```

Expected output:

```
✓ Collection initialized successfully
✓ Stored embedding for: Pothole on Main Street
Found 3 similar issues:
1. [0.998] Pothole on Main Street
```

### 15.9 Future Enhancements

- [ ] Multi-modal embeddings (text + image)
- [ ] Geographic clustering (find issues in same area)
- [ ] Temporal patterns (recurring issues)
- [ ] Authority dashboards showing duplicate clusters
- [ ] Cross-lingual similarity (multiple languages)

--- -->
