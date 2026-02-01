"""
Simple test for VectorService without requiring model downloads
"""
from app.services.vector_service import VectorService
import logging
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_vector_service_basic():
    """Test VectorService operations with mock embeddings"""
    
    print("\n" + "="*60)
    print("Testing VectorService Basic Operations")
    print("="*60 + "\n")
    
    # Test 1: Initialize collection
    print("1. Initializing Qdrant collection...")
    try:
        VectorService.initialize_collection()
        print("✓ Collection initialized successfully")
    except Exception as e:
        print(f"✗ Collection initialization failed: {e}")
        return
    
    # Test 2: Store embeddings with mock data
    print("\n2. Testing embedding storage...")
    
    # Create mock embeddings (384-dimensional vectors)
    np.random.seed(42)
    
    test_posts = [
        {
            "id": "mock-001",
            "title": "Pothole on Main Street",
            "description": "Large pothole causing issues",
            "embedding": np.random.rand(384).tolist()
        },
        {
            "id": "mock-002", 
            "title": "Hole in road on Main Street",
            "description": "Dangerous hole needs fixing",
            "embedding": np.random.rand(384).tolist()
        },
        {
            "id": "mock-003",
            "title": "Park cleanup event",
            "description": "Community cleanup at the park",
            "embedding": np.random.rand(384).tolist()
        }
    ]
    
    for post in test_posts:
        success = VectorService.upsert_embedding(
            issue_id=post["id"],
            embedding=post["embedding"],
            metadata={
                "title": post["title"],
                "description": post["description"],
                "ai_decision": "APPROVE",
                "moderation_score": 0.85
            }
        )
        
        if success:
            print(f"✓ Stored embedding for: {post['title']}")
        else:
            print(f"✗ Failed to store: {post['title']}")
    
    # Test 3: Similarity search
    print("\n3. Testing similarity search...")
    # Use a vector similar to the first one
    np.random.seed(42)
    query_embedding = (np.random.rand(384) + np.random.rand(384) * 0.1).tolist()
    
    similar = VectorService.find_similar(
        embedding=query_embedding,
        limit=3,
        score_threshold=0.0  # Lower threshold to see results
    )
    
    print(f"Query embedding (mock)")
    print(f"Found {len(similar)} similar issues:\n")
    
    for i, result in enumerate(similar, 1):
        print(f"{i}. [{result['similarity_score']:.3f}] {result['title']}")
        print(f"   ID: {result['issue_id']}")
        print(f"   Decision: {result['ai_decision']}")
        print()
    
    # Test 4: Test get_similar_decisions
    print("4. Testing get_similar_decisions (for RAG)...")
    similar_decisions = VectorService.get_similar_decisions(
        embedding=query_embedding,
        limit=2
    )
    
    print(f"Found {len(similar_decisions)} similar past decisions:")
    for decision in similar_decisions:
        print(f"  - {decision['title']} (score: {decision['similarity_score']:.3f})")
    
    print("\n" + "="*60)
    print("✓ Basic VectorService tests completed!")
    print("="*60 + "\n")
    
    return True

if __name__ == "__main__":
    success = test_vector_service_basic()
    exit(0 if success else 1)
