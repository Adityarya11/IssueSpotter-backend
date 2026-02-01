from typing import Dict, List
import logging
from app.ai.image_analyser import ImageAnalyzer
from app.ai.text_embedder import TextEmbedder
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)

class AIClassifier:
    
    # Singleton instances (loaded once, reused)
    _image_analyzer = None
    _text_embedder = None
    
    @classmethod
    def _get_image_analyzer(cls):
        if cls._image_analyzer is None:
            cls._image_analyzer = ImageAnalyzer()
        return cls._image_analyzer
    
    @classmethod
    def _get_text_embedder(cls):
        if cls._text_embedder is None:
            cls._text_embedder = TextEmbedder()
        return cls._text_embedder
    
    @classmethod
    def classify(cls, title: str, description: str, images: List[str]) -> Dict:
        """
        Run AI classification on post.
        
        Checks:
        1. NSFW content in images
        2. Text-image relevance (coming soon)
        3. Text toxicity (placeholder for now)
        """
        
        results = {
            "stage": "AI_CLASSIFIER",
            "image_analysis": {},
            "text_analysis": {},
            "decision": "APPROVE",
            "confidence": 0.0
        }
        
        # 1. Image Analysis
        if images and len(images) > 0:
            try:
                image_analyzer = cls._get_image_analyzer()
                image_results = image_analyzer.analyse_batch(images)
                
                results["image_analysis"] = image_results
                
                # Decision logic for images
                if image_results.get("has_nsfw", False):
                    nsfw_score = image_results.get("max_nsfw_score", 0.0)
                    
                    if nsfw_score > 0.8:
                        results["decision"] = "REJECT"
                        results["confidence"] = nsfw_score
                        results["reason"] = "High confidence NSFW content detected"
                    elif nsfw_score > 0.6:
                        results["decision"] = "ESCALATE"
                        results["confidence"] = nsfw_score
                        results["reason"] = "Possible NSFW content - needs review"
                
            except Exception as e:
                logger.error(f"Image analysis failed: {e}")
                results["image_analysis"] = {"error": str(e)}
        
        # 2. Text Analysis (Embeddings)
        try:
            text_embedder = cls._get_text_embedder()
            combined_text = f"{title} {description}"
            
            # Generate embedding (we'll store this for future similarity search)
            embedding = text_embedder.embed_text(combined_text)
            
            results["text_analysis"] = {
                "embedding_generated": True,
                "embedding_dim": len(embedding),
                "text_length": len(combined_text)
            }
            
            # Store embedding as list for JSON serialization
            results["text_embedding"] = embedding.tolist()
            
            # Check for duplicates
            try:
                duplicate = VectorService.detect_duplicates(
                    embedding=embedding.tolist(),
                    similarity_threshold=0.90,
                    time_window_hours=24
                )
                
                if duplicate:
                    results["decision"] = "ESCALATE"
                    results["confidence"] = duplicate["similarity_score"]
                    results["reason"] = f"Potential duplicate of issue {duplicate['issue_id']} (similarity: {duplicate['similarity_score']:.2%})"
                    results["duplicate_detected"] = True
                    results["duplicate_issue_id"] = duplicate["issue_id"]
                    logger.info(f"Duplicate detected: {duplicate['issue_id']}")
            except Exception as e:
                logger.error(f"Duplicate detection failed: {e}")
                results["duplicate_detected"] = False
            
            # Get similar past decisions for learning (RAG)
            try:
                similar_decisions = VectorService.get_similar_decisions(
                    embedding=embedding.tolist(),
                    limit=3
                )
                
                if similar_decisions:
                    # Use past decisions to inform current decision
                    human_approvals = sum(1 for d in similar_decisions if d.get("human_decision") == "APPROVE")
                    human_rejections = sum(1 for d in similar_decisions if d.get("human_decision") == "REJECT")
                    
                    results["similar_cases"] = {
                        "count": len(similar_decisions),
                        "human_approvals": human_approvals,
                        "human_rejections": human_rejections,
                        "cases": similar_decisions
                    }
                    
                    # Adjust confidence based on historical patterns
                    if human_rejections > human_approvals and results["decision"] == "APPROVE":
                        logger.info("Similar cases were rejected by humans - escalating for review")
                        results["decision"] = "ESCALATE"
                        results["reason"] = f"Similar past cases were rejected ({human_rejections}/{len(similar_decisions)})"
                    
            except Exception as e:
                logger.error(f"Similar decision lookup failed: {e}")
            
        except Exception as e:
            logger.error(f"Text analysis failed: {e}")
            results["text_analysis"] = {"error": str(e)}
        
        # 3. Set default confidence if not set by image analysis
        if results["confidence"] == 0.0:
            results["confidence"] = 0.7  # Default confidence for approved posts
        
        return results