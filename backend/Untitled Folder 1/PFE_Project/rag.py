from manus_client import query_manus
import logging

logging.basicConfig(level=logging.INFO)

async def ask_rag(question: str, knowledge_base_id: str) -> str:
    """
    Ask a RAG-based model for document-specific answers.
    """
    logging.info(f"Asking RAG: {question}")
    try:
        answer = await query_manus(question, knowledge_base_id)
        return answer
    except Exception as e:
        logging.error(f"RAG call failed: {e}", exc_info=True)
        return f"Error querying RAG: {e}"