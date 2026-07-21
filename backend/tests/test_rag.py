import pytest
from app.ai.rag.chunker import split_text
from app.ai.rag.embedding import get_mock_embedding
from app.ai.rag.vector_store import VectorStore
from app.ai.rag.retriever import Retriever

def test_chunker() -> None:
    """Verifies that the character chunker splits texts with appropriate overlaps."""
    long_doc = "A" * 1200
    chunks = split_text(long_doc, chunk_size=500, chunk_overlap=100)
    # Expected: Chunks at 0-500, 400-900, 800-1200 => 3 chunks
    assert len(chunks) == 3
    assert len(chunks[0]) == 500
    assert len(chunks[1]) == 500
    assert len(chunks[2]) == 400

@pytest.mark.asyncio
async def test_vector_search_and_retrieval(db) -> None:
    """Verifies storing mock embeddings and executing similarity retrieves."""
    text_booking = "How to book an appointment with Vocentra AI voice calendar"
    text_pricing = "Pricing details for our enterprise voice agent tier subscriptions"
    
    emb_booking = get_mock_embedding(text_booking)
    emb_pricing = get_mock_embedding(text_pricing)
    
    # 1. Add chunks to db
    await VectorStore.add_knowledge(
        organization_id=1,
        title="Booking Guide FAQ",
        content_type="faq",
        text_content=text_booking,
        embedding=emb_booking,
        db=db
    )
    
    await VectorStore.add_knowledge(
        organization_id=1,
        title="Pricing Plan FAQ",
        content_type="faq",
        text_content=text_pricing,
        embedding=emb_pricing,
        db=db
    )
    
    # 2. Query retriever for keywords matching booking document
    context = await Retriever.retrieve_context(
        organization_id=1,
        query="how to book an appointment with voice AI",
        limit=1,
        db=db
    )
    
    assert "Booking Guide FAQ" in context
    assert "Pricing Plan FAQ" not in context # verified reranker successfully promoted booking FAQ
