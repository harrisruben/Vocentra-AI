import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
from app.models.models import Knowledge
from app.core.logger import logger
from app.core.config import settings

class VectorStore:
    @staticmethod
    async def add_knowledge(
        organization_id: int,
        title: str,
        content_type: str,
        text_content: str,
        embedding: list,
        db: AsyncSession
    ) -> Knowledge:
        """Saves a knowledge chunk along with its vector embedding."""
        chunk = Knowledge(
            organization_id=organization_id,
            title=title,
            content_type=content_type,
            text_content=text_content,
            embedding=embedding
        )
        db.add(chunk)
        await db.commit()
        await db.refresh(chunk)
        logger.info(f"VectorStore: Logged knowledge chunk id={chunk.id} for org={organization_id}")
        return chunk

    @staticmethod
    async def similarity_search(
        organization_id: int,
        query_embedding: list,
        limit: int,
        db: AsyncSession
    ) -> list:
        """Executes semantic similarity search.

        Funnels to pgvector on Postgres, falling back to python-based
        cosine dot-products on SQLite.
        """
        logger.info(f"VectorStore: Executing semantic search (limit={limit})")
        
        # 1. Native Postgres pgvector query
        if settings.DATABASE_URL.startswith("postgresql"):
            try:
                # <=> represents cosine distance operator in pgvector
                query = (
                    select(Knowledge)
                    .filter(Knowledge.organization_id == organization_id)
                    .order_by(text("embedding <=> :emb"))
                    .params(emb=str(query_embedding))
                    .limit(limit)
                )
                result = await db.execute(query)
                return list(result.scalars().all())
            except Exception as e:
                logger.error(f"PostgreSQL pgvector search failed: {str(e)}. Using fallback matching.")
                
        # 2. Local Python matching (for SQLite testing and Postgres failover)
        query = select(Knowledge).filter(Knowledge.organization_id == organization_id)
        result = await db.execute(query)
        chunks = result.scalars().all()
        
        scored_chunks = []
        for chunk in chunks:
            if not chunk.embedding:
                continue
            # Cosine similarity for L2-normalized float lists is simply the dot product
            similarity = np.dot(query_embedding, chunk.embedding)
            scored_chunks.append((similarity, chunk))
            
        # Sort desc by score
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        logger.info(f"VectorStore: Match scores calculated for {len(scored_chunks)} items.")
        
        return [chunk for score, chunk in scored_chunks[:limit]]
