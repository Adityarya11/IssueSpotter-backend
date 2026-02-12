"""
AI Classifier for IssueSpotter Guardian

The core decision-making component that:
1. Analyzes text (title, description) for toxicity
2. Analyzes images for NSFW content
3. Analyzes videos frame-by-frame
4. Detects duplicates using vector similarity
5. Learns from past moderator decisions (RAG)

Three-Tier Decision System:
- GREEN (score < 0.3): Auto-approve, safe content
- YELLOW (score 0.3-0.8): Escalate to human moderator
- RED (score > 0.8): Auto-reject, clearly violating
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Decision(Enum):
    """Three-tier moderation decision."""
    GREEN = "GREEN"    # Auto-approve (score < 0.3)
    YELLOW = "YELLOW"  # Needs human review (score 0.3-0.8)
    RED = "RED"        # Auto-reject (score > 0.8)


class ContentType(Enum):
    """Type of content being analyzed."""
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"


# Threshold constants
THRESHOLD_GREEN = 0.3   # Below this = auto-approve
THRESHOLD_RED = 0.8     # Above this = auto-reject


@dataclass
class AnalysisResult:
    """Result from analyzing a single piece of content."""
    content_type: str  # Use string for JSON serialization
    score: float
    decision: str  # Use string for JSON serialization
    details: Dict = field(default_factory=dict)
    embedding: Optional[List[float]] = None


@dataclass
class ClassificationResult:
    """Complete classification result for a post."""
    post_id: str
    final_decision: str  # GREEN, YELLOW, RED
    final_score: float
    reason: str
    
    text_analysis: Optional[AnalysisResult] = None
    image_analyses: List[AnalysisResult] = field(default_factory=list)
    video_analyses: List[AnalysisResult] = field(default_factory=list)
    
    duplicate_detected: bool = False
    duplicate_info: Optional[Dict] = None
    
    similar_cases: List[Dict] = field(default_factory=list)
    
    # Embeddings for storage
    text_embedding: Optional[List[float]] = None
    image_embeddings: List[Optional[List[float]]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "post_id": self.post_id,
            "final_decision": self.final_decision,
            "final_score": self.final_score,
            "reason": self.reason,
            "text_analysis": asdict(self.text_analysis) if self.text_analysis else None,
            "image_analyses": [asdict(a) for a in self.image_analyses],
            "video_analyses": [asdict(a) for a in self.video_analyses],
            "duplicate_detected": self.duplicate_detected,
            "duplicate_info": self.duplicate_info,
            "similar_cases": self.similar_cases,
            "has_text_embedding": self.text_embedding is not None,
            "image_embedding_count": len([e for e in self.image_embeddings if e]),
        }


def _score_to_decision(score: float) -> str:
    """Convert numeric score to three-tier decision string."""
    if score >= THRESHOLD_RED:
        return Decision.RED.value
    elif score >= THRESHOLD_GREEN:
        return Decision.YELLOW.value
    else:
        return Decision.GREEN.value


@dataclass
class ModerationRequest:
    """Request object for content moderation."""
    issue_id: str
    title: str
    description: str
    image_paths: Optional[List[str]] = None
    video_paths: Optional[List[str]] = None
    
    
@dataclass
class ModerationResult:
    """Result of moderation analysis."""
    issue_id: str
    decision: str  # GREEN, YELLOW, RED
    confidence: float
    reason: str
    scores: Optional[Dict] = None
    classification_result: Optional[ClassificationResult] = None


class AIClassifier:
    """
    Main AI classifier for the IssueSpotter Guardian.
    
    Singleton pattern for model instances to avoid reloading.
    """
    
    # Singleton instances
    _image_analyzer = None
    _image_embedder = None
    _text_embedder = None
    _video_analyzer = None
    
    @classmethod
    def _get_image_analyzer(cls):
        if cls._image_analyzer is None:
            from app.ai.image_analyser import ImageAnalyzer
            cls._image_analyzer = ImageAnalyzer()
        return cls._image_analyzer
    
    @classmethod
    def _get_image_embedder(cls):
        if cls._image_embedder is None:
            from app.ai.image_embedder import ImageEmbedder
            cls._image_embedder = ImageEmbedder()
        return cls._image_embedder
    
    @classmethod
    def _get_text_embedder(cls):
        if cls._text_embedder is None:
            from app.ai.text_embedder import TextEmbedder
            cls._text_embedder = TextEmbedder()
        return cls._text_embedder
    
    @classmethod
    def _get_video_analyzer(cls):
        if cls._video_analyzer is None:
            from app.ai.video_analyzer import VideoAnalyzer
            cls._video_analyzer = VideoAnalyzer(enable_embeddings=True)
        return cls._video_analyzer
    
    @classmethod
    def _analyze_text(cls, title: str, description: str) -> AnalysisResult:
        """
        Analyze text content.
        
        Currently generates embeddings for similarity.
        Future: Add toxicity detection.
        """
        try:
            embedder = cls._get_text_embedder()
            combined_text = f"{title} {description}"
            embedding = embedder.embed_text(combined_text)
            
            # TODO: Add text toxicity model here
            # For now, text is always GREEN unless duplicated
            
            return AnalysisResult(
                content_type=ContentType.TEXT.value,
                score=0.0,  # Will be adjusted by duplicate check
                decision=Decision.GREEN.value,
                details={
                    "title_length": len(title),
                    "description_length": len(description),
                    "embedding_generated": True
                },
                embedding=embedding.tolist()
            )
            
        except Exception as e:
            logger.error(f"Text analysis failed: {e}")
            return AnalysisResult(
                content_type=ContentType.TEXT.value,
                score=0.5,  # Escalate on error
                decision=Decision.YELLOW.value,
                details={"error": str(e)}
            )
    
    @classmethod
    def _analyze_image(cls, image_url: str) -> AnalysisResult:
        """Analyze a single image for NSFW content and generate embedding."""
        try:
            # NSFW detection
            analyzer = cls._get_image_analyzer()
            nsfw_result = analyzer.check_nsfw(image_url)
            
            nsfw_score = nsfw_result.get("confidence", 0.0)
            
            # Generate embedding
            embedding = None
            try:
                embedder = cls._get_image_embedder()
                emb = embedder.embed_image(image_url)
                if emb is not None:
                    embedding = emb.tolist()
            except Exception as e:
                logger.error(f"Image embedding failed: {e}")
            
            return AnalysisResult(
                content_type=ContentType.IMAGE.value,
                score=nsfw_score,
                decision=_score_to_decision(nsfw_score),
                details={
                    "is_nsfw": nsfw_result.get("is_nsfw", False),
                    "detections": nsfw_result.get("detections", []),
                    "url": image_url
                },
                embedding=embedding
            )
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return AnalysisResult(
                content_type=ContentType.IMAGE.value,
                score=0.5,  # Escalate on error
                decision=Decision.YELLOW.value,
                details={"error": str(e), "url": image_url}
            )
    
    @classmethod
    def _analyze_video(cls, video_url: str) -> AnalysisResult:
        """Analyze a video for NSFW content."""
        try:
            analyzer = cls._get_video_analyzer()
            result = analyzer.analyze_video(video_url)
            
            # Get first frame embedding as representative
            embedding = None
            if result.embeddings and len(result.embeddings) > 0:
                embedding = result.embeddings[0]
            
            return AnalysisResult(
                content_type=ContentType.VIDEO.value,
                score=result.max_nsfw_score,
                decision=result.decision,  # Already a string
                details={
                    "duration_seconds": result.metadata.duration_seconds,
                    "frames_analyzed": result.total_frames_analyzed,
                    "flagged_frame_count": len(result.flagged_frames),
                    "url": video_url,
                    "error": result.error
                },
                embedding=embedding
            )
            
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            return AnalysisResult(
                content_type=ContentType.VIDEO.value,
                score=0.5,
                decision=Decision.YELLOW.value,
                details={"error": str(e), "url": video_url}
            )
    
    @classmethod
    def _check_duplicates(cls, embedding: List[float]) -> Optional[Dict]:
        """Check if similar content was already posted."""
        try:
            from app.services.vector_service import VectorService
            
            duplicate = VectorService.detect_duplicates(
                embedding=embedding,
                similarity_threshold=0.90,  # Very high = definite duplicate
                time_window_hours=24
            )
            
            return duplicate
            
        except Exception as e:
            logger.error(f"Duplicate check failed: {e}")
            return None
    
    @classmethod
    def _get_similar_decisions(cls, embedding: List[float]) -> List[Dict]:
        """Get past moderator decisions for similar content (RAG)."""
        try:
            from app.services.vector_service import VectorService
            
            similar = VectorService.get_similar_decisions(
                embedding=embedding,
                limit=3
            )
            
            return similar
            
        except Exception as e:
            logger.error(f"Similar decisions lookup failed: {e}")
            return []
    
    @classmethod
    async def classify(cls, request: ModerationRequest) -> ModerationResult:
        """
        Classify a moderation request and return simplified result.
        
        Args:
            request: ModerationRequest with issue details
            
        Returns:
            Moderation result with GREEN/YELLOW/RED decision
        """
        # Run full classification
        result = cls.classify_full(
            post_id=request.issue_id,
            title=request.title,
            description=request.description,
            images=request.image_paths,
            videos=request.video_paths
        )
        
        # Return simplified result
        return ModerationResult(
            issue_id=request.issue_id,
            decision=result.final_decision,
            confidence=result.final_score,
            reason=result.reason,
            scores={
                "text_score": result.text_analysis.score if result.text_analysis else 0.0,
                "image_scores": [a.score for a in result.image_analyses],
                "final_score": result.final_score
            },
            classification_result=result
        )
    
    @classmethod
    def classify_full(
        cls,
        post_id: str,
        title: str,
        description: str,
        images: Optional[List[str]] = None,
        videos: Optional[List[str]] = None
    ) -> ClassificationResult:
        """
        Run full AI classification on a post.
        
        Args:
            post_id: Unique identifier for the post
            title: Post title
            description: Post description
            images: List of image URLs
            videos: List of video URLs
            
        Returns:
            ClassificationResult with decision and all analysis details
        """
        images = images or []
        videos = videos or []
        
        logger.info(f"Classifying post {post_id}: {len(images)} images, {len(videos)} videos")
        
        # Initialize result
        result = ClassificationResult(
            post_id=post_id,
            final_decision=Decision.GREEN.value,
            final_score=0.0,
            reason="Content passed all checks"
        )
        
        all_scores = []
        reasons = []
        
        # 1. Analyze text
        text_result = cls._analyze_text(title, description)
        result.text_analysis = text_result
        result.text_embedding = text_result.embedding
        
        if text_result.decision != Decision.GREEN.value:
            all_scores.append(text_result.score)
            reasons.append(f"Text: {text_result.details}")
        
        # 2. Analyze images
        for image_url in images:
            img_result = cls._analyze_image(image_url)
            result.image_analyses.append(img_result)
            
            if img_result.embedding:
                result.image_embeddings.append(img_result.embedding)
            
            all_scores.append(img_result.score)
            
            if img_result.decision == Decision.RED.value:
                reasons.append(f"Image flagged RED: {image_url}")
            elif img_result.decision == Decision.YELLOW.value:
                reasons.append(f"Image needs review: {image_url}")
        
        # 3. Analyze videos
        for video_url in videos:
            vid_result = cls._analyze_video(video_url)
            result.video_analyses.append(vid_result)
            
            all_scores.append(vid_result.score)
            
            if vid_result.decision == Decision.RED.value:
                reasons.append(f"Video flagged RED: {video_url}")
            elif vid_result.decision == Decision.YELLOW.value:
                reasons.append(f"Video needs review: {video_url}")
        
        # 4. Check for duplicates (using text embedding)
        if result.text_embedding:
            duplicate = cls._check_duplicates(result.text_embedding)
            if duplicate:
                result.duplicate_detected = True
                result.duplicate_info = duplicate
                all_scores.append(duplicate["similarity_score"])
                reasons.append(f"Duplicate of {duplicate['issue_id']} (similarity: {duplicate['similarity_score']:.1%})")
        
        # 5. Get similar past decisions (RAG)
        if result.text_embedding:
            similar = cls._get_similar_decisions(result.text_embedding)
            result.similar_cases = similar
            
            # Check if similar cases were rejected by humans
            if similar:
                rejections = sum(1 for s in similar if s.get("human_decision") == "REJECT")
                if rejections > len(similar) / 2:
                    all_scores.append(0.6)  # Push towards YELLOW
                    reasons.append(f"Similar past cases rejected by moderators ({rejections}/{len(similar)})")
        
        # 6. Calculate final decision
        if all_scores:
            result.final_score = max(all_scores)  # Worst score wins
        else:
            result.final_score = 0.0
        
        result.final_decision = _score_to_decision(result.final_score)
        
        if reasons:
            result.reason = "; ".join(reasons)
        else:
            result.reason = "Content passed all checks"
        
        logger.info(f"Post {post_id} classified as {result.final_decision} (score: {result.final_score:.2f})")
        
        return result
    
    @classmethod
    def classify_legacy(cls, title: str, description: str, images: List[str]) -> Dict:
        """
        Legacy classify method for backward compatibility.
        
        Maps new ClassificationResult to old dict format.
        """
        result = cls.classify_full(
            post_id="legacy",
            title=title,
            description=description,
            images=images
        )
        
        # Map to legacy format
        decision_map = {
            Decision.GREEN.value: "APPROVE",
            Decision.YELLOW.value: "ESCALATE",
            Decision.RED.value: "REJECT"
        }
        
        return {
            "stage": "AI_CLASSIFIER",
            "decision": decision_map.get(result.final_decision, "ESCALATE"),
            "confidence": result.final_score,
            "reason": result.reason,
            "image_analysis": {
                "has_nsfw": any(a.decision != Decision.GREEN.value for a in result.image_analyses),
                "max_nsfw_score": max([a.score for a in result.image_analyses], default=0.0),
                "results": [a.details for a in result.image_analyses]
            },
            "text_analysis": result.text_analysis.details if result.text_analysis else {},
            "text_embedding": result.text_embedding,
            "duplicate_detected": result.duplicate_detected,
            "duplicate_issue_id": result.duplicate_info.get("issue_id") if result.duplicate_info else None,
            "similar_cases": {
                "count": len(result.similar_cases),
                "cases": result.similar_cases
            }
        }