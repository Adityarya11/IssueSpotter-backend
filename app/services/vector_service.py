from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, 
    VectorParams, 
    PointStruct, 
    Filter, 
    FieldCondition, 
    MatchValue,
    PayloadSchemaType
)
from typing import List, Dict, Optional
import logging
import uuid
from datetime import datetime, timedelta
from app.config.settings import settings

logger = logging.getLogger(__name__)


# Collection names
TEXT_COLLECTION = settings.QDRANT_COLLECTION_NAME  # 384-dim (text embeddings)
IMAGE_COLLECTION = "image_embeddings"  # 512-dim (CLIP embeddings)

# Embedding dimensions
TEXT_EMBEDDING_DIM = 384   # all-MiniLM-L6-v2
IMAGE_EMBEDDING_DIM = 512  # CLIP ViT-B/32


class VectorService:
    """
    Service for managing vector embeddings in Qdrant.
    
    Supports both text embeddings (384-dim) and image embeddings (512-dim).
    Enables similarity search, duplicate detection, and RAG.
    """
    
    _client: Optional[QdrantClient] = None
    
    @classmethod
    def get_client(cls) -> QdrantClient:
        """Get or create Qdrant client (singleton pattern)"""
        if cls._client is None:
            try:
                # Use cloud configuration if available
                if settings.QDRANT_API_URL and settings.QDRANT_API_KEY:
                    cls._client = QdrantClient(
                        url=settings.QDRANT_API_URL,
                        api_key=settings.QDRANT_API_KEY
                    )
                    logger.info(f"Connected to Qdrant Cloud at {settings.QDRANT_API_URL}")
                else:
                    # Fallback to local Qdrant
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
    def initialize_collection(cls, collection_name: str = TEXT_COLLECTION, dimension: int = TEXT_EMBEDDING_DIM):
        """
        Create a collection if it doesn't exist.
        
        Args:
            collection_name: Name of the Qdrant collection
            dimension: Vector dimension (384 for text, 512 for images)
        """
        client = cls.get_client()
        
        try:
            collections = client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)
            
            if not exists:
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {collection_name} (dim={dimension})")
                
                # Create payload index for timestamp field (required for time-based filtering)
                client.create_payload_index(
                    collection_name=collection_name,
                    field_name="timestamp",
                    field_schema=PayloadSchemaType.FLOAT
                )
                logger.info(f"Created timestamp index for {collection_name}")
            else:
                logger.info(f"Qdrant collection already exists: {collection_name}")
                # Ensure timestamp index exists even for existing collections
                try:
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name="timestamp",
                        field_schema=PayloadSchemaType.FLOAT
                    )
                    logger.info(f"Created timestamp index for existing {collection_name}")
                except Exception:
                    # Index might already exist, that's fine
                    pass
                
        except Exception as e:
            logger.error(f"Failed to initialize collection {collection_name}: {e}")
            raise
    
    @classmethod
    def initialize_all_collections(cls):
        """Initialize both text and image collections."""
        cls.initialize_collection(TEXT_COLLECTION, TEXT_EMBEDDING_DIM)
        cls.initialize_collection(IMAGE_COLLECTION, IMAGE_EMBEDDING_DIM)
        logger.info("All vector collections initialized")
    
    @classmethod
    def upsert_embedding(
        cls,
        issue_id: str,
        embedding: List[float],
        metadata: Dict,
        collection_name: str = TEXT_COLLECTION
    ) -> bool:
        """
        Store or update an embedding in Qdrant.
        
        Args:
            issue_id: Unique identifier for the issue
            embedding: Vector (384-dim for text, 512-dim for images)
            metadata: Additional information (title, description, ai_decision, etc.)
            collection_name: Which collection to store in
        
        Returns:
            True if successful
        """
        client = cls.get_client()
        
        try:
            # Ensure collection exists with correct dimension
            dim = len(embedding)
            cls.initialize_collection(collection_name, dim)
            
            # Create point
            point = PointStruct(
                id=str(uuid.uuid4()),  # Qdrant point ID
                vector=embedding,
                payload={
                    "issue_id": issue_id,
                    "timestamp": datetime.utcnow().timestamp(),  # Store as Unix timestamp (numeric)
                    **metadata
                }
            )
            
            # Upsert to Qdrant
            client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            
            logger.info(f"Stored embedding for issue {issue_id} in {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert embedding for issue {issue_id}: {e}")
            return False
    
    @classmethod
    def upsert_image_embedding(
        cls,
        issue_id: str,
        image_url: str,
        embedding: List[float],
        metadata: Dict
    ) -> bool:
        """
        Store an image embedding in the image collection.
        
        Args:
            issue_id: Issue this image belongs to
            image_url: URL of the image
            embedding: 512-dim CLIP vector
            metadata: Additional info (ai_decision, nsfw_score, etc.)
        """
        full_metadata = {
            "image_url": image_url,
            **metadata
        }
        return cls.upsert_embedding(
            issue_id=issue_id,
            embedding=embedding,
            metadata=full_metadata,
            collection_name=IMAGE_COLLECTION
        )
    
    @classmethod
    def find_similar(
        cls,
        embedding: List[float],
        limit: int = 5,
        score_threshold: float = 0.8,
        time_window_hours: Optional[int] = 24,
        collection_name: str = TEXT_COLLECTION
    ) -> List[Dict]:
        """
        Find similar items based on embedding similarity.
        
        Args:
            embedding: Query vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score (0-1)
            time_window_hours: Only search within last N hours (None = no limit)
            collection_name: Which collection to search
        
        Returns:
            List of similar items with scores and metadata
        """
        client = cls.get_client()
        
        try:
            # Build filter for time window
            query_filter = None
            if time_window_hours:
                cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
                # Convert to Unix timestamp (Qdrant expects numeric value)
                cutoff_timestamp = cutoff_time.timestamp()
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="timestamp",
                            range={
                                "gte": cutoff_timestamp
                            }
                        )
                    ]
                )
            
            # Search using search() method (stable Qdrant API)
            results = client.search(
                collection_name=collection_name,
                query_vector=embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )
            
            # Format results
            similar_items = []
            for hit in results:
                similar_items.append({
                    "issue_id": hit.payload.get("issue_id"),
                    "similarity_score": hit.score,
                    "ai_decision": hit.payload.get("ai_decision"),
                    "human_decision": hit.payload.get("human_decision"),
                    "timestamp": hit.payload.get("timestamp"),
                    "title": hit.payload.get("title", ""),
                    "description": hit.payload.get("description", ""),
                    "image_url": hit.payload.get("image_url", ""),
                })
            
            logger.info(f"Found {len(similar_items)} similar items in {collection_name}")
            return similar_items
            
        except Exception as e:
            logger.error(f"Failed to search for similar items: {e}")
            return []
    
    @classmethod
    def find_similar_images(
        cls,
        embedding: List[float],
        limit: int = 5,
        score_threshold: float = 0.85,
        time_window_hours: Optional[int] = None
    ) -> List[Dict]:
        """
        Find similar images using CLIP embeddings.
        
        Args:
            embedding: 512-dim CLIP vector
            limit: Max results
            score_threshold: Minimum similarity (default 0.85 for images)
            time_window_hours: Time window (None = all time)
        """
        return cls.find_similar(
            embedding=embedding,
            limit=limit,
            score_threshold=score_threshold,
            time_window_hours=time_window_hours,
            collection_name=IMAGE_COLLECTION
        )
    
    @classmethod
    def detect_duplicates(
        cls,
        embedding: List[float],
        similarity_threshold: float = 0.90,
        time_window_hours: int = 24,
        collection_name: str = TEXT_COLLECTION
    ) -> Optional[Dict]:
        """
        Check if a very similar item was reported recently.
        
        Args:
            embedding: Query vector
            similarity_threshold: High threshold for duplicates (default 0.90)
            time_window_hours: Look back window
            collection_name: Which collection to check
        
        Returns:
            Dict with duplicate info if found, None otherwise
        """
        similar = cls.find_similar(
            embedding=embedding,
            limit=1,
            score_threshold=similarity_threshold,
            time_window_hours=time_window_hours,
            collection_name=collection_name
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
    def detect_image_duplicates(
        cls,
        embedding: List[float],
        similarity_threshold: float = 0.92,
        time_window_hours: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Check if a similar image was already submitted.
        
        Uses higher threshold for images (0.92 vs 0.90 for text)
        since CLIP embeddings are very precise.
        """
        return cls.detect_duplicates(
            embedding=embedding,
            similarity_threshold=similarity_threshold,
            time_window_hours=time_window_hours,
            collection_name=IMAGE_COLLECTION
        )
    
    @classmethod
    def get_similar_decisions(
        cls,
        embedding: List[float],
        limit: int = 3,
        collection_name: str = TEXT_COLLECTION
    ) -> List[Dict]:
        """
        Get past moderation decisions for similar items (for RAG/learning).
        
        Used by AI to learn from human moderator feedback.
        """
        return cls.find_similar(
            embedding=embedding,
            limit=limit,
            score_threshold=0.75,  # Lower threshold for learning
            time_window_hours=None,  # Search all history
            collection_name=collection_name
        )
    
    @classmethod
    def update_human_decision(
        cls,
        issue_id: str,
        human_decision: str,
        moderator_notes: Optional[str] = None,
        collection_name: str = TEXT_COLLECTION
    ) -> bool:
        """
        Update an existing embedding with human moderator decision.
        
        This is how the AI learns from HITL feedback.
        
        Args:
            issue_id: ID of the issue to update
            human_decision: APPROVE or REJECT
            moderator_notes: Optional notes from moderator
            collection_name: Which collection to update
        """
        client = cls.get_client()
        
        try:
            # Find the point by issue_id
            results = client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="issue_id",
                            match=MatchValue(value=issue_id)
                        )
                    ]
                ),
                limit=1
            )
            
            points = results[0]
            if not points:
                logger.warning(f"No embedding found for issue {issue_id}")
                return False
            
            point = points[0]
            
            # Update payload
            updated_payload = {
                **point.payload,
                "human_decision": human_decision,
                "human_reviewed_at": datetime.utcnow().timestamp(),  # Store as Unix timestamp
            }
            
            if moderator_notes:
                updated_payload["moderator_notes"] = moderator_notes
            
            # Overwrite the point with updated payload
            client.overwrite_payload(
                collection_name=collection_name,
                payload=updated_payload,
                points=[point.id]
            )
            
            logger.info(f"Updated human decision for issue {issue_id}: {human_decision}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update human decision: {e}")
            return False
    
    @classmethod
    def get_pending_reviews(
        cls,
        limit: int = 50,
        collection_name: str = TEXT_COLLECTION
    ) -> List[Dict]:
        """
        Get items that need human review (YELLOW zone with no human decision yet).
        
        Returns items where ai_decision is ESCALATE/YELLOW and human_decision is missing.
        """
        client = cls.get_client()
        
        try:
            # Find points with ESCALATE/YELLOW decision and no human decision
            results = client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="ai_decision",
                            match=MatchValue(value="YELLOW")
                        )
                    ],
                    must_not=[
                        FieldCondition(
                            key="human_decision",
                            match=MatchValue(value="APPROVE")
                        ),
                        FieldCondition(
                            key="human_decision",
                            match=MatchValue(value="REJECT")
                        )
                    ]
                ),
                limit=limit
            )
            
            pending = []
            for point in results[0]:
                pending.append({
                    "issue_id": point.payload.get("issue_id"),
                    "title": point.payload.get("title", ""),
                    "description": point.payload.get("description", ""),
                    "ai_decision": point.payload.get("ai_decision"),
                    "ai_score": point.payload.get("ai_score", 0.0),
                    "timestamp": point.payload.get("timestamp"),
                    "image_url": point.payload.get("image_url", ""),
                })
            
            logger.info(f"Found {len(pending)} items pending human review")
            return pending
            
        except Exception as e:
            logger.error(f"Failed to get pending reviews: {e}")
            return []
