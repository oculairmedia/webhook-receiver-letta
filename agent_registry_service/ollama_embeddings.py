"""
Simple Ollama Embedding Client for Agent Registry

Provides embeddings using Ollama API endpoint matching the toolselector setup.
"""

import os
import requests
from typing import List
import logging

logger = logging.getLogger(__name__)


class OllamaEmbeddingProvider:
    """Simple Ollama embedding provider."""
    
    def __init__(
        self,
        base_url: str = None,
        model: str = None,
        dimensions: int = None
    ):
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://192.168.50.80:11434")
        self.model = model or os.environ.get("OLLAMA_EMBEDDING_MODEL", "dengcao/Qwen3-Embedding-4B:Q4_K_M")
        self.dimensions = dimensions or int(os.environ.get("EMBEDDING_DIMENSION", "2560"))
        self.endpoint = f"{self.base_url}/api/embeddings"
        
        logger.info(f"[OllamaEmbedding] Initialized: {self.model} @ {self.base_url}")
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        try:
            response = requests.post(
                self.endpoint,
                json={
                    "model": self.model,
                    "prompt": text
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            embedding = result.get("embedding", [])
            
            if len(embedding) != self.dimensions:
                logger.warning(
                    f"[OllamaEmbedding] Expected {self.dimensions} dimensions, "
                    f"got {len(embedding)}"
                )
            
            return embedding
            
        except Exception as e:
            logger.error(f"[OllamaEmbedding] Error getting embedding: {e}")
            raise
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            embedding = self.get_embedding(text)
            embeddings.append(embedding)
        return embeddings
