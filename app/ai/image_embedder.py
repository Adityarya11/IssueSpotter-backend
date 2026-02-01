"""
Image Embedder using CLIP (Contrastive Language-Image Pre-Training)

Converts images into 512-dimensional vectors that can be:
- Compared for similarity (duplicate detection)
- Stored in Qdrant for retrieval
- Used for learning from past moderation decisions

CLIP allows semantic understanding - it "knows" that a photo of a
pothole and a photo of road damage are related concepts.
"""

import io
import logging
from typing import List, Optional, Union
import numpy as np
import requests
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel

logger = logging.getLogger(__name__)


class ImageEmbedder:
    """
    Generate semantic embeddings for images using CLIP.
    
    Uses openai/clip-vit-base-patch32 model:
    - Fast inference (~50ms per image)
    - 512-dimensional vectors
    - Good balance of speed vs accuracy
    """
    
    _instance = None
    _model = None
    _processor = None
    _device = None
    
    def __new__(cls):
        """Singleton pattern - only load model once."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Load CLIP model and processor."""
        try:
            # Use GPU if available
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"ImageEmbedder using device: {self._device}")
            
            # Load CLIP model (downloads on first run ~600MB)
            model_name = "openai/clip-vit-base-patch32"
            logger.info(f"Loading CLIP model: {model_name}")
            
            self._model = CLIPModel.from_pretrained(model_name)
            self._processor = CLIPProcessor.from_pretrained(model_name)
            
            # Move model to device
            self._model.to(self._device)
            self._model.eval()  # Set to evaluation mode
            
            logger.info("CLIP model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize CLIP: {e}")
            raise
    
    def _load_image(self, image_source: Union[str, Image.Image, bytes]) -> Optional[Image.Image]:
        """
        Load image from various sources.
        
        Args:
            image_source: URL string, PIL Image, or bytes
            
        Returns:
            PIL Image in RGB format, or None if failed
        """
        try:
            if isinstance(image_source, Image.Image):
                return image_source.convert("RGB")
            
            elif isinstance(image_source, bytes):
                return Image.open(io.BytesIO(image_source)).convert("RGB")
            
            elif isinstance(image_source, str):
                if image_source.startswith(("http://", "https://")):
                    # Download from URL
                    response = requests.get(image_source, timeout=10)
                    response.raise_for_status()
                    return Image.open(io.BytesIO(response.content)).convert("RGB")
                else:
                    # Load from file path
                    return Image.open(image_source).convert("RGB")
            
            else:
                logger.error(f"Unsupported image source type: {type(image_source)}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            return None
    
    def embed_image(self, image_source: Union[str, Image.Image, bytes]) -> Optional[np.ndarray]:
        """
        Generate embedding vector for a single image.
        
        Args:
            image_source: URL, file path, PIL Image, or bytes
            
        Returns:
            512-dimensional numpy array, or None if failed
        """
        image = self._load_image(image_source)
        if image is None:
            return None
        
        try:
            # Process image for CLIP
            inputs = self._processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self._device) for k, v in inputs.items()}
            
            # Generate embedding
            with torch.no_grad():
                image_features = self._model.get_image_features(**inputs)
            
            # Normalize to unit vector (for cosine similarity)
            embedding = image_features.cpu().numpy()[0]
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate image embedding: {e}")
            return None
    
    def embed_batch(self, image_sources: List[Union[str, Image.Image, bytes]]) -> List[Optional[np.ndarray]]:
        """
        Generate embeddings for multiple images.
        
        Args:
            image_sources: List of image sources
            
        Returns:
            List of embeddings (None for failed images)
        """
        embeddings = []
        
        # Load all valid images
        images = []
        valid_indices = []
        
        for i, source in enumerate(image_sources):
            image = self._load_image(source)
            if image is not None:
                images.append(image)
                valid_indices.append(i)
        
        if not images:
            return [None] * len(image_sources)
        
        try:
            # Batch process
            inputs = self._processor(images=images, return_tensors="pt", padding=True)
            inputs = {k: v.to(self._device) for k, v in inputs.items()}
            
            with torch.no_grad():
                image_features = self._model.get_image_features(**inputs)
            
            # Normalize all embeddings
            batch_embeddings = image_features.cpu().numpy()
            norms = np.linalg.norm(batch_embeddings, axis=1, keepdims=True)
            batch_embeddings = batch_embeddings / norms
            
            # Map back to original indices
            result = [None] * len(image_sources)
            for idx, emb in zip(valid_indices, batch_embeddings):
                result[idx] = emb
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return [None] * len(image_sources)
    
    def similarity(self, image1: Union[str, Image.Image, bytes], 
                   image2: Union[str, Image.Image, bytes]) -> float:
        """
        Calculate cosine similarity between two images.
        
        Returns:
            Similarity score 0-1 (1 = identical)
        """
        emb1 = self.embed_image(image1)
        emb2 = self.embed_image(image2)
        
        if emb1 is None or emb2 is None:
            return 0.0
        
        # Cosine similarity (embeddings are already normalized)
        return float(np.dot(emb1, emb2))
    
    def text_image_similarity(self, text: str, image_source: Union[str, Image.Image, bytes]) -> float:
        """
        Calculate similarity between text description and image.
        
        CLIP's unique ability: compare text and images in the same vector space.
        Useful for checking if an image matches its caption/description.
        
        Returns:
            Similarity score 0-1
        """
        image = self._load_image(image_source)
        if image is None:
            return 0.0
        
        try:
            # Process both text and image
            inputs = self._processor(
                text=[text],
                images=image,
                return_tensors="pt",
                padding=True
            )
            inputs = {k: v.to(self._device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self._model(**inputs)
                
            # Get similarity from logits
            logits_per_image = outputs.logits_per_image
            similarity = torch.softmax(logits_per_image, dim=1)[0][0].item()
            
            return similarity
            
        except Exception as e:
            logger.error(f"Failed to calculate text-image similarity: {e}")
            return 0.0
    
    @property
    def embedding_dim(self) -> int:
        """Return the dimension of embeddings (512 for CLIP)."""
        return 512
