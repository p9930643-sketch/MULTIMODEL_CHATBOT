import logging
from typing import List
import numpy as np
import google.generativeai as genai
from core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingEngine:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generates 768-dimensional embedding using Gemini text-embedding-004.
        Returns fallback pseudo-embedding if API key is not configured or network error occurs.
        """
        if not text or not text.strip():
            return [0.0] * 768

        if self.api_key:
            try:
                response = genai.embed_content(
                    model=settings.GEMINI_EMBEDDING_MODEL,
                    content=text,
                    task_type="retrieval_document"
                )
                if "embedding" in response:
                    return response["embedding"]
            except Exception as e:
                logger.warning("Gemini embedding API failed (%s); using deterministic fallback.", e)

        # Deterministic feature hash fallback for offline or unauthenticated mode
        return self._generate_fallback_vector(text)

    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generates query embedding for semantic search.
        """
        if not query or not query.strip():
            return [0.0] * 768

        if self.api_key:
            try:
                response = genai.embed_content(
                    model=settings.GEMINI_EMBEDDING_MODEL,
                    content=query,
                    task_type="retrieval_query"
                )
                if "embedding" in response:
                    return response["embedding"]
            except Exception as e:
                logger.warning("Gemini query embedding failed (%s); using deterministic fallback.", e)

        return self._generate_fallback_vector(query)

    def _generate_fallback_vector(self, text: str, dim: int = 768) -> List[float]:
        """
        Generates normalized deterministic feature vector based on char n-grams.
        Guarantees non-empty vector for cosine similarity calculations when offline.
        """
        vec = np.zeros(dim, dtype=np.float32)
        for i, ch in enumerate(text.lower()):
            idx = (ord(ch) * 31 + i * 17) % dim
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Computes cosine similarity between two float vectors."""
        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

embedding_engine = EmbeddingEngine()
