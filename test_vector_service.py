"""
Test script for VectorService integration with Qdrant
"""
from app.services.vector_service import VectorService
from app.ai.text_embedder import TextEmbedder
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_vector_service():
    """Test VectorService operations"""
    
    print("\n" + "="*60)
    print("Testing VectorService Integration with Qdrant")
    print("="*60 + "\n")
    
    # Initialize text embedder
    print("1. Initializing TextEmbedder...")
    embedder = TextEmbedder()
    
    # Test 1: Initialize collection
    print("\n2. Initializing Qdrant collection...")
    try:
        VectorService.initialize_collection()
        print("✓ Collection initialized successfully")
    except Exception as e:
        print(f"✗ Collection initialization failed: {e}")
        return
    
    # Test 2: Store embeddings
    print("\n3. Testing embedding storage...")
    
    test_posts = [
        {
            "id": "test-001",
            "title": "Pothole on Main Street",
            "description": "There's a large pothole near the intersection causing traffic issues"
        },
        {
            "id": "test-002", 
            "title": "Big hole in the road on Main Street",
            "description": "Dangerous hole in the street at Main and 5th, needs immediate attention"
        },
        {
            "id": "test-003",
            "title": "Beautiful park cleanup today",
            "description": "Community came together to clean up the local park"
        }
    ]
    
    for post in test_posts:
        combined_text = f"{post['title']} {post['description']}"
        embedding = embedder.embed_text(combined_text)
        
        success = VectorService.upsert_embedding(
            issue_id=post["id"],
            embedding=embedding.tolist(),
            metadata={
                "title": post["title"],
                "description": post["description"],
                "ai_decision": "APPROVE",
                "moderation_score": 0.85
            }
        )
        
        if success:
            print(f"✓ Stored embedding for: {post['title'][:50]}...")
        else:
            print(f"✗ Failed to store: {post['title'][:50]}...")
    
    # Test 3: Similarity search
    print("\n4. Testing similarity search...")
    query_text = "Hole in road on Main Street needs fixing"
    query_embedding = embedder.embed_text(query_text)
    
    similar = VectorService.find_similar(
        embedding=query_embedding.tolist(),
        limit=3,
        score_threshold=0.5
    )
    
    print(f"\nQuery: '{query_text}'")
    print(f"Found {len(similar)} similar issues:\n")
    
    for i, result in enumerate(similar, 1):
        print(f"{i}. [{result['similarity_score']:.3f}] {result['title']}")
        print(f"   ID: {result['issue_id']}")
        print(f"   Decision: {result['ai_decision']}")
        print()
    
    # Test 4: Duplicate detection
    print("5. Testing duplicate detection...")
    duplicate_text = "Large pothole on Main Street intersection"
    duplicate_embedding = embedder.embed_text(duplicate_text)
    
    duplicate = VectorService.detect_duplicates(
        embedding=duplicate_embedding.tolist(),
        similarity_threshold=0.85,
        time_window_hours=24
    )
    
    if duplicate:
        print(f"✓ Duplicate detected!")
        print(f"   Original: {duplicate['issue_id']}")
        print(f"   Similarity: {duplicate['similarity_score']:.3f}")
        print(f"   Title: {duplicate['title']}")
    else:
        print("✓ No duplicates found (threshold not met)")
    
    # Test 5: Get similar decisions for RAG
    print("\n6. Testing RAG - Similar decision lookup...")
    similar_decisions = VectorService.get_similar_decisions(
        embedding=query_embedding.tolist(),
        limit=2
    )
    
    print(f"Found {len(similar_decisions)} similar past decisions for learning:")
    for decision in similar_decisions:
        print(f"  - {decision['title'][:50]}... (score: {decision['similarity_score']:.3f})")
    
    print("\n" + "="*60)
    print("✓ All VectorService tests completed!")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_vector_service()
