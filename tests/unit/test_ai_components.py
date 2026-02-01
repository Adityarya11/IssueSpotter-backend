"""
Unit Tests for AI Components

Tests for TextEmbedder and ImageAnalyzer functionality.
These tests verify the core AI models work correctly.
"""
import pytest
import numpy as np


class TestTextEmbedder:
    """Test suite for TextEmbedder functionality."""

    def test_embedding_generation(self, text_embedder):
        """Test that embedder produces correct vector dimensions."""
        text = "This is a test issue report."
        embedding = text_embedder.embed_text(text)

        assert isinstance(embedding, np.ndarray), "Embedding should be numpy array"
        assert embedding.shape == (384,), f"Expected 384 dims, got {embedding.shape}"

    def test_embedding_consistency(self, text_embedder):
        """Test that same text produces identical embeddings."""
        text = "Pothole on Main Street"
        
        embedding_1 = text_embedder.embed_text(text)
        embedding_2 = text_embedder.embed_text(text)

        np.testing.assert_array_almost_equal(
            embedding_1, embedding_2,
            err_msg="Same text should produce identical embeddings"
        )

    def test_semantic_similarity_high(self, text_embedder):
        """Test that semantically similar texts have high similarity scores."""
        text_1 = "Pothole on Main Street"
        text_2 = "Big hole in the road on Main Street"

        similarity = text_embedder.similarity(text_1, text_2)

        assert similarity > 0.7, f"Similar texts should score > 0.7, got {similarity:.3f}"

    def test_semantic_similarity_low(self, text_embedder):
        """Test that unrelated texts have low similarity scores."""
        text_1 = "Pothole on Main Street"
        text_2 = "Beautiful sunset at the beach today"

        similarity = text_embedder.similarity(text_1, text_2)

        assert similarity < 0.5, f"Unrelated texts should score < 0.5, got {similarity:.3f}"

    def test_empty_text_handling(self, text_embedder):
        """Test that empty text is handled gracefully."""
        embedding = text_embedder.embed_text("")
        
        assert embedding is not None
        assert embedding.shape == (384,)

    def test_long_text_handling(self, text_embedder):
        """Test that long texts are handled correctly."""
        long_text = "This is a test issue. " * 100  # ~2000 chars
        embedding = text_embedder.embed_text(long_text)

        assert embedding.shape == (384,), "Long text should still produce 384-dim vector"


class TestImageAnalyzer:
    """Test suite for ImageAnalyzer (NudeNet) functionality."""

    def test_analyzer_initialization(self, image_analyzer):
        """Test that NudeNet model loads correctly."""
        assert image_analyzer.nsfw_detector is not None, "NSFW detector should be initialized"

    def test_analyzer_has_check_method(self, image_analyzer):
        """Test that check_nsfw method exists and is callable."""
        assert hasattr(image_analyzer, "check_nsfw"), "Should have check_nsfw method"
        assert callable(image_analyzer.check_nsfw), "check_nsfw should be callable"
