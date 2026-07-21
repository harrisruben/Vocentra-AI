import os
import hashlib
import httpx
import numpy as np
from typing import List
from app.core.logger import logger
from app.core.config import settings

def get_mock_embedding(text: str, dimension: int = 1536) -> List[float]:
    """Generates L2-normalized deterministic vector based on text MD5 hash."""
    seed = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16) % (2**32)
    rng = np.random.default_rng(seed)
    vector = rng.uniform(-1.0, 1.0, dimension)
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    return vector.tolist()

async def get_embedding(text: str) -> List[float]:
    """Retrieves embedding vector from OpenAI, falling back to deterministic local mock."""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        # Default mock fallback to prevent crash and enable offline testing
        return get_mock_embedding(text)
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": text,
                    "model": "text-embedding-3-small"
                },
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                return data["data"][0]["embedding"]
            else:
                logger.warning(f"OpenAI Embeddings API returned {response.status_code}. Using mock fallback.")
                return get_mock_embedding(text)
    except Exception as e:
        logger.error(f"OpenAI Embeddings request failed: {str(e)}. Using mock fallback.")
        return get_mock_embedding(text)
