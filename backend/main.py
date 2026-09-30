"""
================================================================================
Academic AI — FastAPI Backend Server
================================================================================
Provides endpoints for:
  - POST /upload : Receives and processes study PDF into ChromaDB
  - POST /ask    : Runs RAG similarity search and generates LLM answer
  - GET  /health : Verifies server status and configuration
================================================================================
"""

import os
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from rag import (
    process_and_index_pdf,
    ask_rag,
    UPLOADS_DIR,
    LLMConfigurationError,
    LLMProviderError,
)

# Load environment configuration
load_dotenv()

app = FastAPI(
    title="Academic AI — RAG Question Answering System",
    description="FastAPI Backend for Academic RAG College Project Demo",
    version="1.0.0"
)

# Enable CORS for React Vite frontend (running typically on port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Academic AI RAG Prototype",
        "endpoints": {
            "upload": "POST /upload",
            "ask": "POST /ask",
            "health": "GET /health"
        }
    }


@app.get("/health")
def health_check():
    """Checks environment configuration status."""
    has_groq = bool(os.getenv("GROQ_API_KEY", "").strip())
    has_gemini = bool(os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip())
    has_openai = bool(os.getenv("OPENAI_API_KEY", "").strip())

    return {
        "status": "healthy",
        "llm_configured": has_groq or has_gemini or has_openai,
        "available_providers": {
            "groq": has_groq,
            "gemini": has_gemini,
            "openai": has_openai
        }
    }


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    1. Upload PDF Endpoint:
       - Validates that the uploaded file is a PDF.
       - Saves the file to backend/uploads/.
       - Extracts text, splits into chunks, and indexes in ChromaDB.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Save uploaded file locally
    saved_file_path = os.path.join(UPLOADS_DIR, file.filename)
    try:
        with open(saved_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Run RAG processing (extract, chunk, embed, store)
    try:
        chunk_count = process_and_index_pdf(saved_file_path, file.filename)
        return {
            "message": "PDF processed successfully",
            "filename": file.filename,
            "chunks_count": chunk_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF during RAG indexing: {str(e)}"
        )


@app.post("/ask")
async def ask_question(payload: QuestionRequest):
    """
    2. Ask Question Endpoint:
       - Receives user query: { "question": "..." }
       - Searches ChromaDB for top relevant context chunks
       - Calls LLM with academic instructions
       - Returns:
         {
           "answer": "...",
           "sources": [
             { "file": "DBMS_Notes.pdf", "page": 24 }
           ]
         }
    """
    cleaned_question = payload.question.strip()
    if not cleaned_question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        response_data = ask_rag(cleaned_question)
        return response_data
    except LLMConfigurationError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except LLMProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating answer: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    print(f"Starting Academic AI RAG Server on http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)
