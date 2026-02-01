from fastapi.types import ModelNameMap
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List
import logging

import sentence_transformers
from torch import embedding

logger = logging.getLogger(__name__)

class TextEmbedder:

    def __init__(self, model_name: str = "all-miniLM-L6-V2"):
        #Initialise the embedding model,
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"model initialised ====> {model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.model = None

    def embed_text(self, text: str) -> np.ndarray:
        ## Generate embedding for single text

        if not self.model:
            return np.zeros(384)
        
        try: 
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding

        except Exception as e:
            logger.error(f"Embedding faile: {e}")
            return np.zeros(384)
        
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        ## Generate embeddings for multiple texts

        if not self.model:
            return np.zeros((len(texts), 384))
        
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.error(f"Batch embedding failed as {e}")
            return np.zeros((len(texts), 384))

    def similarity(self, text1: str, text2: str) -> float:
        # Calculate cosine sim

        emb1 = self.embed_text(text1)
        emb2 = self.embed_text(text2)

        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)

        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))