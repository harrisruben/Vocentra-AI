from typing import List
from app.core.logger import logger

def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """Splits input text into fixed-size overlapping chunks."""
    if not text:
        return []
        
    logger.info(f"Chunker: Splitting text block of length {len(text)} characters (size={chunk_size}, overlap={chunk_overlap})")
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        # Advance starting window
        start += chunk_size - chunk_overlap
        
    logger.info(f"Chunker: Generated {len(chunks)} text chunks.")
    return chunks
