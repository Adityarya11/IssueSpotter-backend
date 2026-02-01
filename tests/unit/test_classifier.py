"""
Unit Tests for Three-Tier Classification System

Tests the GREEN/YELLOW/RED decision thresholds.
"""
import pytest


class TestDecisionThresholds:
    """Test the three-tier threshold constants and logic."""
    
    def test_threshold_values(self):
        """Test that thresholds are set correctly."""
        from app.pipelines.moderation.classifier import THRESHOLD_GREEN, THRESHOLD_RED
        
        assert THRESHOLD_GREEN == 0.3, "GREEN threshold should be 0.3"
        assert THRESHOLD_RED == 0.8, "RED threshold should be 0.8"
        assert THRESHOLD_GREEN < THRESHOLD_RED, "GREEN must be less than RED"
    
    def test_score_to_decision_green(self):
        """Test that low scores result in GREEN decision."""
        from app.pipelines.moderation.classifier import _score_to_decision, Decision
        
        assert _score_to_decision(0.0) == Decision.GREEN.value
        assert _score_to_decision(0.1) == Decision.GREEN.value
        assert _score_to_decision(0.29) == Decision.GREEN.value
    
    def test_score_to_decision_yellow(self):
        """Test that middle scores result in YELLOW decision."""
        from app.pipelines.moderation.classifier import _score_to_decision, Decision
        
        assert _score_to_decision(0.3) == Decision.YELLOW.value
        assert _score_to_decision(0.5) == Decision.YELLOW.value
        assert _score_to_decision(0.79) == Decision.YELLOW.value
    
    def test_score_to_decision_red(self):
        """Test that high scores result in RED decision."""
        from app.pipelines.moderation.classifier import _score_to_decision, Decision
        
        assert _score_to_decision(0.8) == Decision.RED.value
        assert _score_to_decision(0.9) == Decision.RED.value
        assert _score_to_decision(1.0) == Decision.RED.value
    
    def test_decision_enum_values(self):
        """Test Decision enum has correct values."""
        from app.pipelines.moderation.classifier import Decision
        
        assert Decision.GREEN.value == "GREEN"
        assert Decision.YELLOW.value == "YELLOW"
        assert Decision.RED.value == "RED"


class TestContentType:
    """Test ContentType enum."""
    
    def test_content_type_values(self):
        """Test ContentType enum has correct values."""
        from app.pipelines.moderation.classifier import ContentType
        
        assert ContentType.TEXT.value == "TEXT"
        assert ContentType.IMAGE.value == "IMAGE"
        assert ContentType.VIDEO.value == "VIDEO"


class TestAnalysisResult:
    """Test AnalysisResult dataclass."""
    
    def test_analysis_result_creation(self):
        """Test creating analysis result."""
        from app.pipelines.moderation.classifier import AnalysisResult
        
        result = AnalysisResult(
            content_type="TEXT",
            score=0.1,
            decision="GREEN",
            details={"test": "value"}
        )
        
        assert result.content_type == "TEXT"
        assert result.score == 0.1
        assert result.decision == "GREEN"
        assert result.embedding is None  # Optional field
    
    def test_analysis_result_with_embedding(self):
        """Test analysis result with embedding."""
        from app.pipelines.moderation.classifier import AnalysisResult
        
        embedding = [0.1] * 384
        result = AnalysisResult(
            content_type="TEXT",
            score=0.0,
            decision="GREEN",
            details={},
            embedding=embedding
        )
        
        assert result.embedding is not None
        assert len(result.embedding) == 384


class TestClassificationResult:
    """Test ClassificationResult dataclass."""
    
    def test_classification_result_creation(self):
        """Test creating classification result."""
        from app.pipelines.moderation.classifier import ClassificationResult
        
        result = ClassificationResult(
            post_id="test-123",
            final_decision="GREEN",
            final_score=0.1,
            reason="Content passed all checks"
        )
        
        assert result.post_id == "test-123"
        assert result.final_decision == "GREEN"
        assert result.duplicate_detected is False
    
    def test_classification_result_to_dict(self):
        """Test converting classification result to dict."""
        from app.pipelines.moderation.classifier import ClassificationResult
        
        result = ClassificationResult(
            post_id="test-123",
            final_decision="YELLOW",
            final_score=0.5,
            reason="Needs review"
        )
        
        d = result.to_dict()
        
        assert d["post_id"] == "test-123"
        assert d["final_decision"] == "YELLOW"
        assert d["final_score"] == 0.5
        assert d["duplicate_detected"] is False


class TestLegacyCompatibility:
    """Test backward compatibility with legacy API."""
    
    def test_decision_mapping(self):
        """Test that decisions map correctly to legacy format."""
        from app.pipelines.moderation.classifier import Decision
        
        # The legacy API uses APPROVE/ESCALATE/REJECT
        decision_map = {
            Decision.GREEN.value: "APPROVE",
            Decision.YELLOW.value: "ESCALATE",
            Decision.RED.value: "REJECT"
        }
        
        assert decision_map["GREEN"] == "APPROVE"
        assert decision_map["YELLOW"] == "ESCALATE"
        assert decision_map["RED"] == "REJECT"
