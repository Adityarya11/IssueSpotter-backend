"""
Video Analyzer for IssueSpotter AI Microservice

Processes videos by:
1. Extracting frames at intervals (1 frame per 2 seconds)
2. Running NSFW detection on each frame
3. Generating embeddings for video content
4. Enforcing limits (max 60s, max 50MB)

If ANY frame is flagged, the entire video is flagged.
"""

import io
import os
import tempfile
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import requests
import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


# Video processing limits
MAX_DURATION_SECONDS = 60
MAX_FILE_SIZE_MB = 50
FRAME_INTERVAL_SECONDS = 2


@dataclass
class VideoMetadata:
    """Video file metadata."""
    duration_seconds: float
    fps: float
    width: int
    height: int
    frame_count: int
    file_size_mb: float


@dataclass
class FrameResult:
    """Result of analyzing a single frame."""
    frame_number: int
    timestamp_seconds: float
    is_nsfw: bool
    nsfw_score: float
    detections: List[Dict]
    embedding: Optional[List[float]] = None


@dataclass
class VideoAnalysisResult:
    """Complete video analysis result."""
    is_safe: bool
    decision: str  # GREEN, YELLOW, RED
    max_nsfw_score: float
    flagged_frames: List[FrameResult]
    total_frames_analyzed: int
    metadata: VideoMetadata
    error: Optional[str] = None
    embeddings: Optional[List[List[float]]] = None


class VideoAnalyzer:
    """
    Analyze videos for NSFW content and generate embeddings.
    
    Uses frame extraction + ImageAnalyzer for NSFW detection,
    and optionally ImageEmbedder for semantic embeddings.
    """
    
    def __init__(self, enable_embeddings: bool = True):
        """
        Initialize VideoAnalyzer.
        
        Args:
            enable_embeddings: Whether to generate CLIP embeddings for frames
        """
        self._image_analyzer = None
        self._image_embedder = None
        self._enable_embeddings = enable_embeddings
        
    def _get_image_analyzer(self):
        """Lazy load ImageAnalyzer."""
        if self._image_analyzer is None:
            from app.ai.image_analyser import ImageAnalyzer
            self._image_analyzer = ImageAnalyzer()
        return self._image_analyzer
    
    def _get_image_embedder(self):
        """Lazy load ImageEmbedder."""
        if self._image_embedder is None and self._enable_embeddings:
            from app.ai.image_embedder import ImageEmbedder
            self._image_embedder = ImageEmbedder()
        return self._image_embedder
    
    def _download_video(self, url: str) -> Optional[str]:
        """
        Download video from URL to temporary file.
        
        Returns:
            Path to temporary file, or None if failed
        """
        try:
            # Stream download to check size
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Check content length if available
            content_length = response.headers.get('content-length')
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                if size_mb > MAX_FILE_SIZE_MB:
                    logger.error(f"Video too large: {size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB")
                    return None
            
            # Create temp file
            suffix = ".mp4"  # Default extension
            if "." in url.split("/")[-1]:
                suffix = "." + url.split(".")[-1].split("?")[0]
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            
            # Download with size limit
            downloaded = 0
            max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
            
            for chunk in response.iter_content(chunk_size=8192):
                downloaded += len(chunk)
                if downloaded > max_bytes:
                    temp_file.close()
                    os.unlink(temp_file.name)
                    logger.error(f"Video exceeds size limit during download")
                    return None
                temp_file.write(chunk)
            
            temp_file.close()
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Failed to download video: {e}")
            return None
    
    def _get_video_metadata(self, video_path: str) -> Optional[VideoMetadata]:
        """Extract metadata from video file."""
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                logger.error("Failed to open video file")
                return None
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            duration = frame_count / fps if fps > 0 else 0
            file_size = os.path.getsize(video_path) / (1024 * 1024)
            
            cap.release()
            
            return VideoMetadata(
                duration_seconds=duration,
                fps=fps,
                width=width,
                height=height,
                frame_count=frame_count,
                file_size_mb=file_size
            )
            
        except Exception as e:
            logger.error(f"Failed to get video metadata: {e}")
            return None
    
    def _extract_frames(self, video_path: str, interval_seconds: float = FRAME_INTERVAL_SECONDS) -> List[Tuple[int, float, np.ndarray]]:
        """
        Extract frames at regular intervals.
        
        Args:
            video_path: Path to video file
            interval_seconds: Extract one frame every N seconds
            
        Returns:
            List of (frame_number, timestamp, frame_array) tuples
        """
        frames = []
        
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                logger.error("Failed to open video for frame extraction")
                return frames
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            # Enforce duration limit
            max_duration = min(duration, MAX_DURATION_SECONDS)
            
            # Calculate frame interval
            frame_interval = int(fps * interval_seconds)
            if frame_interval < 1:
                frame_interval = 1
            
            current_frame = 0
            
            while True:
                # Set position
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
                
                ret, frame = cap.read()
                if not ret:
                    break
                
                timestamp = current_frame / fps
                if timestamp > max_duration:
                    break
                
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append((current_frame, timestamp, frame_rgb))
                
                current_frame += frame_interval
            
            cap.release()
            logger.info(f"Extracted {len(frames)} frames from video")
            
        except Exception as e:
            logger.error(f"Frame extraction failed: {e}")
        
        return frames
    
    def _analyze_frame(self, frame: np.ndarray, frame_number: int, timestamp: float) -> FrameResult:
        """
        Analyze a single frame for NSFW content.
        
        Args:
            frame: RGB numpy array
            frame_number: Frame index
            timestamp: Timestamp in seconds
            
        Returns:
            FrameResult with NSFW detection
        """
        try:
            # Save frame to temp file for NudeNet (it expects file path)
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                    temp_path = f.name
                    pil_image = Image.fromarray(frame)
                    pil_image.save(f.name, "JPEG")
                
                # Run NSFW detection
                analyzer = self._get_image_analyzer()
                result = analyzer.check_nsfw(temp_path)
                
                return FrameResult(
                    frame_number=frame_number,
                    timestamp_seconds=timestamp,
                    is_nsfw=result.get("is_nsfw", False),
                    nsfw_score=result.get("confidence", 0.0),
                    detections=result.get("detections", [])
                )
                
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Frame analysis failed: {e}")
            return FrameResult(
                frame_number=frame_number,
                timestamp_seconds=timestamp,
                is_nsfw=False,
                nsfw_score=0.0,
                detections=[{"error": str(e)}]
            )
    
    def _generate_frame_embeddings(self, frames: List[Tuple[int, float, np.ndarray]]) -> List[Optional[List[float]]]:
        """Generate CLIP embeddings for extracted frames."""
        if not self._enable_embeddings:
            return [None] * len(frames)
        
        try:
            embedder = self._get_image_embedder()
            if embedder is None:
                return [None] * len(frames)
            
            # Convert frames to PIL images
            pil_images = [Image.fromarray(f[2]) for f in frames]
            
            # Batch embed
            embeddings = embedder.embed_batch(pil_images)
            
            return [e.tolist() if e is not None else None for e in embeddings]
            
        except Exception as e:
            logger.error(f"Frame embedding generation failed: {e}")
            return [None] * len(frames)
    
    def analyze_video(self, video_source: str) -> VideoAnalysisResult:
        """
        Analyze a video for NSFW content.
        
        Args:
            video_source: URL or file path to video
            
        Returns:
            VideoAnalysisResult with decision and details
        """
        temp_file = None
        
        try:
            # Handle URL vs file path
            if video_source.startswith(("http://", "https://")):
                temp_file = self._download_video(video_source)
                if temp_file is None:
                    return VideoAnalysisResult(
                        is_safe=False,
                        decision="RED",
                        max_nsfw_score=0.0,
                        flagged_frames=[],
                        total_frames_analyzed=0,
                        metadata=VideoMetadata(0, 0, 0, 0, 0, 0),
                        error="Failed to download video or video exceeds size limit"
                    )
                video_path = temp_file
            else:
                video_path = video_source
            
            # Get metadata
            metadata = self._get_video_metadata(video_path)
            if metadata is None:
                return VideoAnalysisResult(
                    is_safe=False,
                    decision="RED",
                    max_nsfw_score=0.0,
                    flagged_frames=[],
                    total_frames_analyzed=0,
                    metadata=VideoMetadata(0, 0, 0, 0, 0, 0),
                    error="Failed to read video metadata"
                )
            
            # Check duration limit
            if metadata.duration_seconds > MAX_DURATION_SECONDS:
                logger.warning(f"Video duration {metadata.duration_seconds}s exceeds limit, analyzing first {MAX_DURATION_SECONDS}s only")
            
            # Extract frames
            frames = self._extract_frames(video_path)
            if not frames:
                return VideoAnalysisResult(
                    is_safe=False,
                    decision="YELLOW",  # Escalate if we couldn't analyze
                    max_nsfw_score=0.0,
                    flagged_frames=[],
                    total_frames_analyzed=0,
                    metadata=metadata,
                    error="Failed to extract frames from video"
                )
            
            # Analyze each frame
            frame_results = []
            flagged_frames = []
            max_nsfw_score = 0.0
            
            for frame_num, timestamp, frame_array in frames:
                result = self._analyze_frame(frame_array, frame_num, timestamp)
                frame_results.append(result)
                
                if result.nsfw_score > max_nsfw_score:
                    max_nsfw_score = result.nsfw_score
                
                if result.is_nsfw:
                    flagged_frames.append(result)
            
            # Generate embeddings for key frames (optional)
            embeddings = None
            if self._enable_embeddings:
                embeddings = self._generate_frame_embeddings(frames)
            
            # Determine decision based on three-tier threshold
            if max_nsfw_score >= 0.8:
                decision = "RED"
                is_safe = False
            elif max_nsfw_score >= 0.3:
                decision = "YELLOW"
                is_safe = False  # Needs human review
            else:
                decision = "GREEN"
                is_safe = True
            
            return VideoAnalysisResult(
                is_safe=is_safe,
                decision=decision,
                max_nsfw_score=max_nsfw_score,
                flagged_frames=flagged_frames,
                total_frames_analyzed=len(frames),
                metadata=metadata,
                embeddings=embeddings
            )
            
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            return VideoAnalysisResult(
                is_safe=False,
                decision="YELLOW",  # Escalate on error
                max_nsfw_score=0.0,
                flagged_frames=[],
                total_frames_analyzed=0,
                metadata=VideoMetadata(0, 0, 0, 0, 0, 0),
                error=str(e)
            )
            
        finally:
            # Cleanup temp file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass
    
    def analyze_batch(self, video_sources: List[str]) -> List[VideoAnalysisResult]:
        """
        Analyze multiple videos.
        
        Note: Videos are processed sequentially to manage memory.
        """
        results = []
        for source in video_sources:
            result = self.analyze_video(source)
            results.append(result)
        return results
