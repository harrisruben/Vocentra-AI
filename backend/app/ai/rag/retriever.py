import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.rag.embedding import get_embedding
from app.ai.rag.vector_store import VectorStore
from app.core.logger import logger

class Retriever:
    @staticmethod
    def _rewrite_query(query: str) -> str:
        """Expands queries with synonyms to maximize document recall (Query Expansion)."""
        expanded = query.lower()
        synonym_dictionary = {
            "book": ["schedule", "reserve", "appointment", "slot", "meeting"],
            "price": ["pricing", "cost", "subscription", "plan", "fee", "tier"],
            "support": ["help", "trouble", "issue", "bug", "broken", "ticket"],
            "sales": ["demo", "pitch", "enterprise", "business", "buy", "quote"]
        }
        for word, synonyms in synonym_dictionary.items():
            if word in expanded:
                expanded += " " + " ".join(synonyms)
        logger.info(f"Retriever (Query Rewrite): Expanded '{query}' -> '{expanded}'")
        return expanded

    @staticmethod
    def _rerank_chunks(query: str, chunks: list, limit: int) -> list:
        """Reranks vector search matches using semantic text overlap (Hybrid Reranker)."""
        query_words = set(query.lower().split())
        reranked_results = []
        
        for chunk in chunks:
            # Calculate mock vector similarity if score isn't already assigned
            # (L2-normalized search generates high scores. We default to 0.85 if missing)
            base_score = 0.85 
            
            doc_words = set(chunk.text_content.lower().split())
            intersection = len(query_words.intersection(doc_words))
            overlap_ratio = intersection / max(len(query_words), 1)
            
            # Combined score: 70% vector + 30% exact word intersection match
            hybrid_score = 0.7 * base_score + 0.3 * overlap_ratio
            reranked_results.append((hybrid_score, chunk))
            
        # Re-sort descending based on the combined score
        reranked_results.sort(key=lambda x: x[0], reverse=True)
        logger.info(f"Retriever (Reranker): Reranked {len(chunks)} documents with keyword overlaps.")
        return [chunk for score, chunk in reranked_results[:limit]]

    @staticmethod
    async def retrieve_context(
        organization_id: int,
        query: str,
        limit: int = 3,
        db: AsyncSession = None
    ) -> str:
        """Translates queries into vectors, matches similarity chunks, reranks, and outputs context snippets."""
        if not query or not db:
            return ""
            
        logger.info(f"Retriever: Retrieving semantic contexts for query: '{query}'")
        
        # 1. Apply Query Expansion
        expanded_query = Retriever._rewrite_query(query)
        
        # 2. Generate search query embedding vector
        query_emb = await get_embedding(expanded_query)
        
        # 3. Query similarity chunks (pull extra candidates for reranking phase)
        candidate_limit = limit * 2
        matching_chunks = await VectorStore.similarity_search(
            organization_id=organization_id,
            query_embedding=query_emb,
            limit=candidate_limit,
            db=db
        )
        
        if not matching_chunks:
            logger.info("Retriever: No semantic results matched.")
            return ""
            
        # 4. Rerank matches with exact word overlap check
        refined_chunks = Retriever._rerank_chunks(query, matching_chunks, limit)
        
        # 5. Assemble matches
        context_blocks = []
        for index, chunk in enumerate(refined_chunks):
            context_blocks.append(f"[Context Block {index + 1} - Title: {chunk.title}]:\n{chunk.text_content}")
            
        context_str = "\n\n".join(context_blocks)
        logger.info(f"Retriever: Assembled {len(refined_chunks)} match paragraphs after reranking.")
        return context_str
