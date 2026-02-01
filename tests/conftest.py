"""
Pytest Configuration and Shared Fixtures

This file is automatically loaded by pytest and provides fixtures
that are available to all tests in the test suite.
"""
import pytest
import numpy as np


# ============================================================================
# AI Component Fixtures (Session-scoped for performance)
# ============================================================================

@pytest.fixture(scope="session")
def text_embedder():
    """
    Load TextEmbedder model once per test session.
    
    Session scope ensures the model (all-MiniLM-L6-v2) is only loaded once,
    significantly speeding up test execution.
    """
    from app.ai.text_embedder import TextEmbedder
    print("\n[Fixture] Loading TextEmbedder (session scope)...")
    embedder = TextEmbedder()
    print("[Fixture] TextEmbedder ready")
    return embedder


@pytest.fixture(scope="session")
def image_analyzer():
    """
    Load ImageAnalyzer (NudeNet) once per test session.
    """
    from app.ai.image_analyser import ImageAnalyzer
    print("\n[Fixture] Loading ImageAnalyzer (session scope)...")
    analyzer = ImageAnalyzer()
    print("[Fixture] ImageAnalyzer ready")
    return analyzer


# ============================================================================
# Vector Service Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def vector_service():
    """
    Provide VectorService instance for tests.
    
    Module scope allows initialization once per test module,
    balancing isolation and performance.
    """
    from app.services.vector_service import VectorService
    return VectorService


@pytest.fixture
def mock_embedding():
    """
    Generate a deterministic mock 384-dimensional embedding.
    
    Uses a fixed seed for reproducibility in tests.
    """
    np.random.seed(42)
    return np.random.rand(384).tolist()


@pytest.fixture
def sample_embeddings():
    """
    Generate a set of sample embeddings for batch testing.
    """
    np.random.seed(42)
    return {
        "embedding_1": np.random.rand(384).tolist(),
        "embedding_2": np.random.rand(384).tolist(),
        "embedding_3": np.random.rand(384).tolist(),
    }


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_issue_data():
    """
    Provide sample issue data for testing.
    """
    return {
        "pothole": {
            "id": "test-pothole-001",
            "title": "Pothole on Main Street",
            "description": "Large pothole near intersection causing traffic issues",
        },
        "similar_pothole": {
            "id": "test-pothole-002",
            "title": "Big hole in the road on Main Street",
            "description": "Dangerous hole needs immediate attention",
        },
        "unrelated": {
            "id": "test-park-001",
            "title": "Park cleanup event",
            "description": "Community cleanup at the local park",
        },
    }


# ============================================================================
# Qdrant Availability Check
# ============================================================================

def is_qdrant_available() -> bool:
    """Check if Qdrant is running and accessible."""
    try:
        import requests
        response = requests.get("http://localhost:6333/healthz", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def qdrant_available():
    """
    Session fixture to check Qdrant availability once.
    """
    return is_qdrant_available()


# Pytest marker for integration tests requiring Qdrant
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "requires_qdrant: mark test as requiring Qdrant to be running"
    )
