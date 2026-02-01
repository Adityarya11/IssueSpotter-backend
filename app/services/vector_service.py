from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, QueryRequest
from typing import List, Dict, Optional
import logging
import uuid
from datetime import datetime, timedelta
from app.config.settings import settings

logger = logging.getLogger(__name__)

class VectorService:
    """
    Service for managing vector embeddings in Qdrant.
    Enables similarity search, duplicate detection, and RAG.
    """
    
    _client: Optional[QdrantClient] = None
    _collection_name = settings.QDRANT_COLLECTION_NAME
    
    @classmethod
    def get_client(cls) -> QdrantClient:
        """Get or create Qdrant client (singleton pattern)"""
        if cls._client is None:
            try:
                cls._client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT
                )
                logger.info(f"Connected to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
            except Exception as e:
                logger.error(f"Failed to connect to Qdrant: {e}")
                raise
        return cls._client
    
    @classmethod
    def initialize_collection(cls):
        """
        Create the collection if it doesn't exist.
        Collection stores 384-dimensional vectors (from all-miniLM-L6-V2)
        """
        client = cls.get_client()
        
        try:
            # Check if collection exists
            collections = client.get_collections().collections
            exists = any(c.name == cls._collection_name for c in collections)
            
            if not exists:
                client.create_collection(
                    collection_name=cls._collection_name,
                    vectors_config=VectorParams(
                        size=384,  # all-miniLM-L6-V2 embedding dimension
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {cls._collection_name}")
            else:
                logger.info(f"Qdrant collection already exists: {cls._collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise
    
    @classmethod
    def upsert_embedding(
        cls,
        issue_id: str,
        embedding: List[float],
        metadata: Dict
    ) -> bool:
        """
        Store or update an issue embedding in Qdrant.
        
        Args:
            issue_id: Unique identifier for the issue
            embedding: 384-dimensional vector
            metadata: Additional information (title, description, ai_decision, etc.)
        
        Returns:
            True if successful
        """
        client = cls.get_client()
        
        try:
            # Ensure collection exists
            cls.initialize_collection()
            
            # Create point
            point = PointStruct(
                id=str(uuid.uuid4()),  # Qdrant point ID
                vector=embedding,
                payload={
                    "issue_id": issue_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    **metadata
                }
            )
            
            # Upsert to Qdrant
            client.upsert(
                collection_name=cls._collection_name,
                points=[point]
            )
            
            logger.info(f"Stored embedding for issue {issue_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert embedding for issue {issue_id}: {e}")
            return False
    
    @classmethod
    def find_similar(
        cls,
        embedding: List[float],
        limit: int = 5,
        score_threshold: float = 0.8,
        time_window_hours: Optional[int] = 24
    ) -> List[Dict]:
        """
        Find similar issues based on embedding similarity.
        
        Args:
            embedding: Query vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score (0-1)
            time_window_hours: Only search within last N hours (None = no limit)
        
        Returns:
            List of similar issues with scores and metadata
        """
        client = cls.get_client()
        
        try:
            # Build filter for time window
            query_filter = None
            if time_window_hours:
                cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="timestamp",
                            range={
                                "gte": cutoff_time.isoformat()
                            }
                        )
                    ]
                )
            
            # Search using query_points (new Qdrant API)
            results = client.query_points(
                collection_name=cls._collection_name,
                query=embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )
            
            # Format results
            similar_issues = []
            for hit in results.points:
                similar_issues.append({
                    "issue_id": hit.payload.get("issue_id"),
                    "similarity_score": hit.score,
                    "ai_decision": hit.payload.get("ai_decision"),
                    "human_decision": hit.payload.get("human_decision"),
                    "timestamp": hit.payload.get("timestamp"),
                    "title": hit.payload.get("title", ""),
                    "description": hit.payload.get("description", "")
                })
            
            logger.info(f"Found {len(similar_issues)} similar issues")
            return similar_issues
            
        except Exception as e:
            logger.error(f"Failed to search for similar issues: {e}")
            return []
    
    @classmethod
    def detect_duplicates(
        cls,
        embedding: List[float],
        similarity_threshold: float = 0.90,
        time_window_hours: int = 24
    ) -> Optional[Dict]:
        """
        Check if a very similar issue was reported recently.
        
        Args:
            embedding: Query vector
            similarity_threshold: High threshold for duplicates (default 0.90)
            time_window_hours: Look back window
        
        Returns:
            Dict with duplicate info if found, None otherwise
        """
        similar = cls.find_similar(
            embedding=embedding,
            limit=1,
            score_threshold=similarity_threshold,
            time_window_hours=time_window_hours
        )
        
        if similar:
            duplicate = similar[0]
            logger.warning(
                f"Potential duplicate detected: {duplicate['issue_id']} "
                f"(similarity: {duplicate['similarity_score']:.3f})"
            )
            return duplicate
        
        return None
    
    @classmethod
    def get_similar_decisions(
        cls,
        embedding: List[float],
        limit: int = 3
    ) -> List[Dict]:
        """
        Get past moderation decisions for similar issues (for RAG/learning).
        
        Used by AI to learn from human moderator feedback.
        """
        return cls.find_similar(
            embedding=embedding,
            limit=limit,
            score_threshold=0.75,  # Lower threshold for learning
            time_window_hours=None  # Search all history
        )
