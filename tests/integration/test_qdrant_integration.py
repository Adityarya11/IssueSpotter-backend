"""
Integration Tests for Qdrant Vector Database

These tests require Qdrant to be running on localhost:6333.
Run with: docker-compose up qdrant
"""
import pytest
import uuid
import time
import numpy as np


# Skip all tests in this module if Qdrant is not available
pytestmark = pytest.mark.requires_qdrant


def is_qdrant_running() -> bool:
    """Check if Qdrant is available."""
    try:
        import requests
        response = requests.get("http://localhost:6333/healthz", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


# Skip marker for the entire module
if not is_qdrant_running():
    pytestmark = pytest.mark.skip(reason="Qdrant not running on localhost:6333")


class TestQdrantConnection:
    """Test Qdrant connection and collection initialization."""

    def test_collection_initialization(self, vector_service):
        """Test that collection can be initialized."""
        try:
            vector_service.initialize_collection()
            assert True, "Collection initialized successfully"
        except Exception as e:
            pytest.fail(f"Collection initialization failed: {e}")


class TestVectorServiceOperations:
    """Test VectorService CRUD operations with Qdrant."""

    @pytest.fixture(autouse=True)
    def setup_collection(self, vector_service):
        """Ensure collection is initialized before each test."""
        vector_service.initialize_collection()

    def test_upsert_embedding(self, vector_service, mock_embedding):
        """Test storing an embedding in Qdrant."""
        issue_id = f"test-{uuid.uuid4()}"
        
        success = vector_service.upsert_embedding(
            issue_id=issue_id,
            embedding=mock_embedding,
            metadata={
                "title": "Test Issue",
                "description": "Test description",
                "ai_decision": "APPROVE",
                "moderation_score": 0.85,
            }
        )

        assert success is True, "Upsert should return True on success"

    def test_find_similar_returns_results(self, vector_service, text_embedder, sample_issue_data):
        """Test similarity search returns results."""
        # Store a test embedding
        issue = sample_issue_data["pothole"]
        text = f"{issue['title']} {issue['description']}"
        embedding = text_embedder.embed_text(text).tolist()

        vector_service.upsert_embedding(
            issue_id=issue["id"],
            embedding=embedding,
            metadata={
                "title": issue["title"],
                "description": issue["description"],
                "ai_decision": "APPROVE",
                "moderation_score": 0.9,
            }
        )

        # Wait for Qdrant consistency
        time.sleep(0.5)

        # Search with the same embedding
        results = vector_service.find_similar(
            embedding=embedding,
            limit=5,
            score_threshold=0.5,
        )

        assert len(results) > 0, "Should find at least one similar result"

    def test_self_similarity_high_score(self, vector_service, text_embedder):
        """Test that searching for exact same content returns high similarity."""
        unique_id = f"self-sim-{uuid.uuid4()}"
        text = f"Unique test issue {unique_id}"
        embedding = text_embedder.embed_text(text).tolist()

        vector_service.upsert_embedding(
            issue_id=unique_id,
            embedding=embedding,
            metadata={
                "title": text,
                "ai_decision": "APPROVE",
            }
        )

        time.sleep(0.5)

        results = vector_service.find_similar(
            embedding=embedding,
            limit=1,
            score_threshold=0.0,
        )

        assert len(results) > 0, "Should find the stored embedding"
        assert results[0]["similarity_score"] > 0.99, "Self-similarity should be ~1.0"


class TestDuplicateDetection:
    """Test duplicate detection functionality."""

    @pytest.fixture(autouse=True)
    def setup_collection(self, vector_service):
        """Ensure collection is initialized."""
        vector_service.initialize_collection()

    def test_detect_exact_duplicate(self, vector_service, text_embedder):
        """Test detection of exact duplicate content."""
        unique_suffix = str(uuid.uuid4())[:8]
        original_text = f"Pothole on Main Street {unique_suffix}"
        
        embedding = text_embedder.embed_text(original_text).tolist()

        # Store original
        vector_service.upsert_embedding(
            issue_id=f"original-{unique_suffix}",
            embedding=embedding,
            metadata={"title": original_text, "ai_decision": "APPROVE"}
        )

        time.sleep(0.5)

        # Check for duplicate (same embedding)
        duplicate = vector_service.detect_duplicates(
            embedding=embedding,
            similarity_threshold=0.9,
        )

        assert duplicate is not None, "Should detect the exact duplicate"
        assert duplicate["similarity_score"] > 0.99, "Exact match should have score ~1.0"

    def test_no_duplicate_for_unrelated(self, vector_service, text_embedder):
        """Test that unrelated content is not flagged as duplicate."""
        # Store a pothole issue
        pothole_text = "Pothole on Main Street needs repair"
        pothole_embedding = text_embedder.embed_text(pothole_text).tolist()
        
        vector_service.upsert_embedding(
            issue_id="pothole-unique-001",
            embedding=pothole_embedding,
            metadata={"title": pothole_text, "ai_decision": "APPROVE"}
        )

        time.sleep(0.5)

        # Check with completely unrelated text
        unrelated_text = "Beautiful sunset at the beach photography"
        unrelated_embedding = text_embedder.embed_text(unrelated_text).tolist()

        duplicate = vector_service.detect_duplicates(
            embedding=unrelated_embedding,
            similarity_threshold=0.9,
        )

        assert duplicate is None, "Unrelated content should not be flagged as duplicate"


class TestRAGDecisionLookup:
    """Test Retrieval-Augmented Generation decision lookup."""

    @pytest.fixture(autouse=True)
    def setup_collection(self, vector_service):
        """Ensure collection is initialized."""
        vector_service.initialize_collection()

    def test_get_similar_decisions(self, vector_service, text_embedder):
        """Test retrieving similar past decisions for RAG."""
        # Store several decisions
        decisions = [
            ("Pothole issue 1", "APPROVE", 0.9),
            ("Pothole issue 2", "APPROVE", 0.85),
            ("Spam content", "REJECT", 0.1),
        ]

        for i, (title, decision, score) in enumerate(decisions):
            embedding = text_embedder.embed_text(title).tolist()
            vector_service.upsert_embedding(
                issue_id=f"rag-test-{i}",
                embedding=embedding,
                metadata={
                    "title": title,
                    "ai_decision": decision,
                    "moderation_score": score,
                }
            )

        time.sleep(0.5)

        # Query for similar decisions
        query_text = "New pothole reported"
        query_embedding = text_embedder.embed_text(query_text).tolist()

        similar_decisions = vector_service.get_similar_decisions(
            embedding=query_embedding,
            limit=2,
        )

        assert len(similar_decisions) > 0, "Should find similar past decisions"
        
        # Pothole issues should rank higher than spam
        for decision in similar_decisions:
            assert "pothole" in decision.get("title", "").lower() or decision["similarity_score"] < 0.5


class TestFullVectorLifecycle:
    """End-to-end integration test for the complete vector workflow."""

    def test_complete_workflow(self, vector_service, text_embedder):
        """
        Integration Test: Complete workflow from storage to RAG lookup.
        
        1. Initialize collection
        2. Store embeddings
        3. Search for similar
        4. Detect duplicates
        5. Get RAG decisions
        """
        # 1. Initialize
        vector_service.initialize_collection()

        # 2. Store test data
        unique_id = str(uuid.uuid4())[:8]
        test_text = f"Integration test pothole {unique_id}"
        embedding = text_embedder.embed_text(test_text).tolist()

        success = vector_service.upsert_embedding(
            issue_id=f"integration-{unique_id}",
            embedding=embedding,
            metadata={
                "title": test_text,
                "ai_decision": "APPROVE",
                "moderation_score": 0.92,
            }
        )
        assert success, "Step 2 Failed: Upsert should succeed"

        time.sleep(0.5)

        # 3. Search for similar
        results = vector_service.find_similar(
            embedding=embedding,
            limit=1,
            score_threshold=0.5,
        )
        assert len(results) > 0, "Step 3 Failed: Should find similar results"
        assert results[0]["similarity_score"] > 0.99, "Step 3: Self-match should be ~1.0"

        # 4. Duplicate detection
        duplicate = vector_service.detect_duplicates(
            embedding=embedding,
            similarity_threshold=0.9,
        )
        assert duplicate is not None, "Step 4 Failed: Should detect itself as duplicate"

        # 5. RAG lookup
        rag_results = vector_service.get_similar_decisions(
            embedding=embedding,
            limit=1,
        )
        assert len(rag_results) > 0, "Step 5 Failed: Should get RAG results"

        print(f"\n✓ Full lifecycle test passed for ID: integration-{unique_id}")
