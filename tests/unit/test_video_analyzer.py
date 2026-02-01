"""
Unit Tests for Video Analyzer

Tests video frame extraction and analysis without requiring full video files.
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict


class TestVideoMetadata:
    """Test VideoMetadata dataclass."""
    
    def test_metadata_creation(self):
        """Test creating video metadata."""
        from app.ai.video_analyzer import VideoMetadata
        
        metadata = VideoMetadata(
            duration_seconds=30.0,
            fps=30.0,
            width=1920,
            height=1080,
            frame_count=900,
            file_size_mb=25.5
        )
        
        assert metadata.duration_seconds == 30.0
        assert metadata.fps == 30.0
        assert metadata.width == 1920
        assert metadata.height == 1080
        assert metadata.frame_count == 900
        assert metadata.file_size_mb == 25.5


class TestFrameResult:
    """Test FrameResult dataclass."""
    
    def test_frame_result_creation(self):
        """Test creating frame analysis result."""
        from app.ai.video_analyzer import FrameResult
        
        result = FrameResult(
            frame_number=0,
            timestamp_seconds=0.0,
            is_nsfw=False,
            nsfw_score=0.1,
            detections=[]
        )
        
        assert result.frame_number == 0
        assert result.is_nsfw is False
        assert result.nsfw_score == 0.1


class TestVideoAnalysisResult:
    """Test VideoAnalysisResult dataclass."""
    
    def test_green_decision(self):
        """Test GREEN decision for safe content."""
        from app.ai.video_analyzer import VideoAnalysisResult, VideoMetadata
        
        metadata = VideoMetadata(10.0, 30.0, 1920, 1080, 300, 5.0)
        
        result = VideoAnalysisResult(
            is_safe=True,
            decision="GREEN",
            max_nsfw_score=0.15,
            flagged_frames=[],
            total_frames_analyzed=5,
            metadata=metadata
        )
        
        assert result.is_safe is True
        assert result.decision == "GREEN"
        assert result.max_nsfw_score < 0.3

    def test_yellow_decision(self):
        """Test YELLOW decision for borderline content."""
        from app.ai.video_analyzer import VideoAnalysisResult, VideoMetadata
        
        metadata = VideoMetadata(10.0, 30.0, 1920, 1080, 300, 5.0)
        
        result = VideoAnalysisResult(
            is_safe=False,
            decision="YELLOW",
            max_nsfw_score=0.55,
            flagged_frames=[],
            total_frames_analyzed=5,
            metadata=metadata
        )
        
        assert result.is_safe is False
        assert result.decision == "YELLOW"
        assert 0.3 <= result.max_nsfw_score < 0.8

    def test_red_decision(self):
        """Test RED decision for unsafe content."""
        from app.ai.video_analyzer import VideoAnalysisResult, VideoMetadata
        
        metadata = VideoMetadata(10.0, 30.0, 1920, 1080, 300, 5.0)
        
        result = VideoAnalysisResult(
            is_safe=False,
            decision="RED",
            max_nsfw_score=0.92,
            flagged_frames=[],
            total_frames_analyzed=5,
            metadata=metadata
        )
        
        assert result.is_safe is False
        assert result.decision == "RED"
        assert result.max_nsfw_score >= 0.8


class TestVideoAnalyzerLimits:
    """Test video processing limits."""
    
    def test_max_duration_constant(self):
        """Test that max duration is set correctly."""
        from app.ai.video_analyzer import MAX_DURATION_SECONDS
        assert MAX_DURATION_SECONDS == 60
    
    def test_max_file_size_constant(self):
        """Test that max file size is set correctly."""
        from app.ai.video_analyzer import MAX_FILE_SIZE_MB
        assert MAX_FILE_SIZE_MB == 50
    
    def test_frame_interval_constant(self):
        """Test that frame interval is set correctly."""
        from app.ai.video_analyzer import FRAME_INTERVAL_SECONDS
        assert FRAME_INTERVAL_SECONDS == 2
