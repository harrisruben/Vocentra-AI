from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.models import User, Knowledge
from app.schemas.schemas import StandardResponse
from app.api.deps import get_current_user
from app.ai.rag.chunker import split_text
from app.ai.rag.embedding import get_embedding
from app.ai.rag.vector_store import VectorStore
from app.core.logger import logger
import os

router = APIRouter(prefix="/rag", tags=["RAG Knowledge Base"])

@router.get("/documents", response_model=StandardResponse[list])
async def get_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    org_id = current_user.organization_id
    query = select(Knowledge).filter(Knowledge.organization_id == org_id).order_by(Knowledge.created_at.desc())
    result = await db.execute(query)
    docs = result.scalars().all()
    
    docs_mapped = [{
        "id": doc.id,
        "title": doc.title,
        "content_type": doc.content_type,
        "text_preview": doc.text_content[:200] + "..." if len(doc.text_content) > 200 else doc.text_content,
        "created_at": doc.created_at.isoformat()
    } for doc in docs]
    
    return StandardResponse(
        success=True,
        message="Knowledge base documents loaded successfully",
        data=docs_mapped
    )

@router.post("/upload", response_model=StandardResponse[dict])
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    org_id = current_user.organization_id
    logger.info(f"RAG API: Uploading document {file.filename} for org {org_id}")
    
    try:
        content_bytes = await file.read()
        content_text = content_bytes.decode("utf-8", errors="ignore")
        
        # 1. Chunk content
        chunks = split_text(content_text)
        if not chunks:
            chunks = [content_text] if content_text.strip() else ["Empty document"]
            
        # 2. Embed chunks and save
        full_text = content_text
        embedding = await get_embedding(full_text[:1000] if full_text else "Empty")
        
        # Determine content type from filename extension
        ext = file.filename.split(".")[-1].lower() if "." in file.filename else "text"
        content_type = "pdf" if ext == "pdf" else ("faq" if "faq" in file.filename.lower() else "text")
        
        # Add to vector store
        await VectorStore.add_knowledge(
            organization_id=org_id,
            title=file.filename,
            content_type=content_type,
            text_content=full_text,
            embedding=embedding,
            db=db
        )
        
        return StandardResponse(
            success=True,
            message=f"Document '{file.filename}' processed and indexed successfully.",
            data={"filename": file.filename}
        )
    except Exception as e:
        logger.error(f"Failed to process and upload RAG document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")
