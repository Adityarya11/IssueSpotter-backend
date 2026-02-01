# VectorService API Documentation

## Overview

The `VectorService` provides a high-level interface to Qdrant vector database for semantic similarity search, duplicate detection, and Retrieval-Augmented Generation (RAG) in the IssueSpotter AI moderation system.

## Core Concepts

### Embeddings
- **Dimension**: 384 (from `all-miniLM-L6-V2` model)
- **Distance Metric**: Cosine Similarity
- **Format**: Python list of floats `List[float]`

### Similarity Scores
- Range: 0.0 to 1.0
- **0.90+**: Likely duplicate
- **0.75-0.90**: Semantically similar
- **0.50-0.75**: Related but distinct
- **< 0.50**: Unrelated

## API Reference

### `initialize_collection()`

Creates the Qdrant collection if it doesn't exist.

**Parameters**: None

**Returns**: None

**Raises**: Exception if connection fails

**Example**:
```python
from app.services.vector_service import VectorService

VectorService.initialize_collection()
```

**Note**: This is called automatically by other methods, so explicit initialization is optional.

---

### `upsert_embedding(issue_id, embedding, metadata)`

Store or update an issue embedding in Qdrant.

**Parameters**:
- `issue_id` (str): Unique identifier for the issue
- `embedding` (List[float]): 384-dimensional vector
- `metadata` (Dict): Additional information to store with the vector

**Returns**: `bool` - True if successful, False otherwise

**Example**:
```python
success = VectorService.upsert_embedding(
    issue_id="550e8400-e29b-41d4-a716-446655440000",
    embedding=[0.123, 0.456, ...],  # 384 floats
    metadata={
        "title": "Pothole on Main Street",
        "description": "Large pothole near intersection",
        "ai_decision": "APPROVE",
        "human_decision": None,  # Set by moderator later
        "moderation_score": 0.85,
        "confidence": 0.92
    }
)
```

**Metadata Fields** (recommended):
- `title` (str): Issue title
- `description` (str): Issue description
- `ai_decision` (str): AI's moderation decision (APPROVE, REJECT, ESCALATE)
- `human_decision` (str, optional): Moderator's decision
- `moderation_score` (float): Overall moderation score
- `confidence` (float): AI confidence level
- `timestamp` (str, ISO format): Automatically added if not provided

---

### `find_similar(embedding, limit, score_threshold, time_window_hours)`

Find similar issues based on embedding similarity.

**Parameters**:
- `embedding` (List[float]): Query vector
- `limit` (int, default=5): Maximum number of results
- `score_threshold` (float, default=0.8): Minimum similarity score (0-1)
- `time_window_hours` (int, optional): Only search within last N hours

**Returns**: `List[Dict]` - List of similar issues with scores and metadata

**Example**:
```python
similar = VectorService.find_similar(
    embedding=query_embedding,
    limit=10,
    score_threshold=0.75,
    time_window_hours=24  # Last 24 hours only
)

for result in similar:
    print(f"{result['similarity_score']:.2%} - {result['title']}")
    print(f"  Previous decision: {result['ai_decision']}")
```

**Returns**:
```python
[
    {
        "issue_id": "550e8400-...",
        "similarity_score": 0.95,
        "ai_decision": "APPROVE",
        "human_decision": "APPROVE",
        "timestamp": "2026-02-01T14:22:01.086Z",
        "title": "Large pothole on Main Street",
        "description": "Dangerous hole near intersection",
        "moderation_score": 0.85
    },
    ...
]
```

---

### `detect_duplicates(embedding, similarity_threshold, time_window_hours)`

Check if a very similar issue was reported recently.

**Parameters**:
- `embedding` (List[float]): Query vector
- `similarity_threshold` (float, default=0.90): High threshold for duplicates
- `time_window_hours` (int, default=24): Look-back window

**Returns**: `Dict` or `None` - Duplicate info if found, None otherwise

**Example**:
```python
duplicate = VectorService.detect_duplicates(
    embedding=new_issue_embedding,
    similarity_threshold=0.92,
    time_window_hours=12
)

if duplicate:
    print(f"⚠️ Duplicate of issue {duplicate['issue_id']}")
    print(f"   Similarity: {duplicate['similarity_score']:.2%}")
    print(f"   Original title: {duplicate['title']}")
else:
    print("✓ No duplicates found")
```

**Use Case**: Prevent users from reporting the same issue multiple times.

---

### `get_similar_decisions(embedding, limit)`

Get past moderation decisions for similar issues (for RAG/learning).

**Parameters**:
- `embedding` (List[float]): Query vector
- `limit` (int, default=3): Maximum number of results

**Returns**: `List[Dict]` - Similar issues with moderation decisions

**Example**:
```python
past_decisions = VectorService.get_similar_decisions(
    embedding=current_issue_embedding,
    limit=5
)

# Analyze patterns in past moderation
human_approvals = sum(1 for d in past_decisions if d.get("human_decision") == "APPROVE")
human_rejections = sum(1 for d in past_decisions if d.get("human_decision") == "REJECT")

if human_rejections > human_approvals:
    # Similar cases were rejected - escalate for review
    decision = "ESCALATE"
```

**Use Case**: Enable AI to learn from human moderator feedback without retraining.

---

## Integration Examples

### Example 1: Duplicate Detection in Moderation Pipeline

```python
from app.ai.text_embedder import TextEmbedder
from app.services.vector_service import VectorService

# Generate embedding
embedder = TextEmbedder()
embedding = embedder.embed_text(f"{title} {description}")

# Check for duplicates
duplicate = VectorService.detect_duplicates(
    embedding=embedding.tolist(),
    similarity_threshold=0.90,
    time_window_hours=24
)

if duplicate:
    return {
        "decision": "ESCALATE",
        "reason": f"Potential duplicate of issue {duplicate['issue_id']}",
        "duplicate_info": duplicate
    }
```

### Example 2: Learning from Past Decisions (RAG)

```python
# Get similar past cases
similar_cases = VectorService.get_similar_decisions(
    embedding=embedding.tolist(),
    limit=5
)

# Count human moderator decisions
approved = sum(1 for c in similar_cases if c.get("human_decision") == "APPROVE")
rejected = sum(1 for c in similar_cases if c.get("human_decision") == "REJECT")

# Inform AI decision
if rejected > approved and ai_decision == "APPROVE":
    ai_decision = "ESCALATE"
    reason = f"Similar cases were rejected by humans ({rejected}/{len(similar_cases)})"
```

### Example 3: Storing Moderation Results

```python
# After moderation is complete
VectorService.upsert_embedding(
    issue_id=str(issue.id),
    embedding=text_embedding,
    metadata={
        "title": issue.title,
        "description": issue.description,
        "ai_decision": ai_decision,
        "moderation_score": moderation_score,
        "confidence": confidence,
        "timestamp": datetime.utcnow().isoformat()
    }
)
```

---

## Configuration

### Environment Variables

Set these in your `.env` file:

```env
# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=issue_embeddings
```

### Docker Setup

Start Qdrant using Docker Compose:

```bash
cd docker
docker compose up -d qdrant
```

Verify it's running:

```bash
curl http://localhost:6333/healthz
# Expected: "healthz check passed"
```

---

## Performance Considerations

### Query Performance
- **Typical latency**: 10-50ms
- **With 10K vectors**: ~20ms
- **With 1M vectors**: ~50-100ms

### Optimization Tips
1. **Use time windows**: Limit searches to recent data when possible
2. **Set appropriate thresholds**: Higher thresholds = faster queries
3. **Limit results**: Only request the number of results you need
4. **Batch operations**: When possible, batch multiple queries

### Storage
- Each vector: ~1.5KB (384 floats + metadata)
- 100K issues: ~150MB
- 1M issues: ~1.5GB

---

## Error Handling

All VectorService methods include error handling and logging:

```python
try:
    similar = VectorService.find_similar(embedding)
except Exception as e:
    logger.error(f"Vector search failed: {e}")
    # Returns empty list on failure
    similar = []
```

Key error scenarios:
- **Connection failure**: Check if Qdrant is running
- **Collection not found**: Automatically created on first use
- **Invalid embedding**: Must be exactly 384 dimensions
- **Timeout**: Network or Qdrant server issues

---

## Testing

Run the test suite:

```bash
# Basic functionality test
python test_vector_basic.py

# Full integration test (requires model download)
python test_vector_service.py
```

---

## Future Roadmap

- [ ] Multi-modal embeddings (text + image)
- [ ] Batch upsert for efficiency
- [ ] Async query support
- [ ] Geographic-aware similarity
- [ ] Weighted metadata filtering
- [ ] Automated collection optimization

---

## Support

For issues or questions:
- File an issue on GitHub
- Check Qdrant documentation: https://qdrant.tech/documentation/
- Review moderation pipeline code: `app/pipelines/moderation/`
