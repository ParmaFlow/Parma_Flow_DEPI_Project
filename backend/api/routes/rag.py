from fastapi import APIRouter, Depends, HTTPException

from backend.api.schemas import RAGContextRequest, RAGChatRequest, RAGChatResponse, UserProfile, UserRole
from backend.api.security import require_roles

router = APIRouter(prefix="/rag", tags=["rag"])

@router.post("/chat", response_model=RAGChatResponse)
def chat_with_rag(
    request: RAGChatRequest,
    _: UserProfile = Depends(require_roles(UserRole.ADMIN, UserRole.PHARMACIST, UserRole.EXECUTIVE)),
):
    try:
        from backend.rag.pipeline import RAGPipeline
        from backend.core.llm import LLMModel
        from backend.config.settings import settings
        import os
        import json

        # Get context
        try:
            pipeline = RAGPipeline()
            chunks = pipeline.retrieve_context(request.message, k=request.k)
        except Exception:
            chunks = []
        
        # Build LLM
        api_key = settings.groq_api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is required for RAG chat.")
        llm = LLMModel(api_key)
        
        system_prompt = (
            "You are the Pharma-Flow AI Assistant. Answer the user's question using "
            "the provided medical context and inventory context if applicable. Reply in a helpful, concise tone. "
            "You must return a raw JSON object with exactly one key 'response' containing your answer string."
        )
        
        user_data = {
            "user_query": request.message,
            "retrieved_medical_context": chunks,
            "current_inventory_context": request.inventory_context or "No inventory context provided."
        }
        
        result_json = llm.get_decision(system_prompt, user_data)
        data = json.loads(result_json)
        
        return RAGChatResponse(
            response=data.get("response", "Could not generate a conversational response."),
            context_used=bool(chunks)
        )
    except Exception as exc:
        return RAGChatResponse(
            response=f"I encountered an error: {str(exc)}",
            context_used=False
        )


@router.post("/context")
def retrieve_context(
    request: RAGContextRequest,
    _: UserProfile = Depends(require_roles(UserRole.ADMIN, UserRole.PHARMACIST)),
):
    try:
        from backend.rag.pipeline import RAGPipeline

        pipeline = RAGPipeline()
        chunks = pipeline.retrieve_context(request.query, k=request.k)
    except Exception as exc:  # noqa: BLE001 - optional RAG boundary
        return {
            "available": False,
            "query": request.query,
            "chunks": [
                f"Fallback shortage protocol context for query: {request.query}"
            ],
            "detail": str(exc),
        }

    if not chunks:
        raise HTTPException(status_code=404, detail="No matching RAG context found.")

    return {"available": True, "query": request.query, "chunks": chunks}




