"""
================================================================================
Academic AI — RAG (Retrieval-Augmented Generation) Pipeline Module
================================================================================
Purpose:
  This module implements the core RAG workflow for an academic B.Tech project:
    1. Extract Text from PDF (with page tracking)
    2. Split Text into manageable chunks with overlap
    3. Generate Vector Embeddings using Hugging Face (all-MiniLM-L6-v2)
    4. Store chunks in ChromaDB vector database
    5. Perform Vector Similarity Search for user queries
    6. Formulate Academic Prompt with context & strict guardrails
    7. Generate factual response via LLM (Groq / Gemini / OpenAI)
================================================================================
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Step 1 & 2 dependencies: PDF extraction and chunking
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Step 3 & 4 dependencies: Vector store & Embeddings
import chromadb
from chromadb.utils import embedding_functions
from langchain_community.vectorstores import Chroma

# Base paths
BASE_DIR = Path(__file__).resolve().parent
CHROMA_DIR = os.getenv("CHROMA_DIR", str(BASE_DIR / "chroma_db"))
UPLOADS_DIR = os.getenv("UPLOADS_DIR", str(BASE_DIR / "uploads"))

os.makedirs(CHROMA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)


class HuggingFaceMiniLMEmbeddings:
    """
    Step 3: Hugging Face all-MiniLM-L6-v2 Embedding Model.
    Provides 384-dimensional dense semantic vector representations
    using the optimized ONNX runtime.
    """
    def __init__(self):
        self._fn = embedding_functions.DefaultEmbeddingFunction()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._fn(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._fn([text])[0]


# Cache embedding model instance for fast reuse
_cached_embeddings = None


class LLMProviderError(Exception):
    """Raised when a configured language model provider cannot complete a request."""


class LLMConfigurationError(Exception):
    """Raised when no language model provider is configured."""


def get_embedding_function():
    global _cached_embeddings
    if _cached_embeddings is None:
        _cached_embeddings = HuggingFaceMiniLMEmbeddings()
    return _cached_embeddings


def extract_and_chunk_pdf(file_path: str, filename: str) -> List[Document]:
    """
    Step 1 & 2:
      - Reads the PDF page-by-page using PyPDF.
      - Attaches source file name and 1-indexed page number to each chunk's metadata.
      - Splits the text into overlapping chunks using RecursiveCharacterTextSplitter.
    """
    reader = PdfReader(file_path)
    page_docs: List[Document] = []

    # Step 1: Extract text per page
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            page_docs.append(
                Document(
                    page_content=text,
                    metadata={"file": filename, "page": idx + 1}
                )
            )

    if not page_docs:
        raise ValueError("No extractable text found in the uploaded PDF.")

    # Step 2: Split text into chunks
    # chunk_size=800 characters, chunk_overlap=120 characters preserves context
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_documents(page_docs)
    return chunks


def process_and_index_pdf(file_path: str, filename: str) -> int:
    """
    Step 4: Store in ChromaDB.
    Cleans previous collection and indexes newly extracted chunks.
    """
    chunks = extract_and_chunk_pdf(file_path, filename)
    embeddings = get_embedding_function()

    # Reset collection for the newly uploaded study PDF
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        client.delete_collection("academic_rag")
    except Exception:
        pass

    # Create vector database with chunks and embeddings
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name="academic_rag"
    )

    return len(chunks)


def call_llm(question: str, context: str) -> str:
    """
    Step 6 & 7: Query the LLM with strictly grounded academic instructions.
    Supports Groq, Google Gemini, or OpenAI based on available API key in .env.
    """
    # Required Academic Assistant System Prompt
    system_instruction = (
        "You are an academic assistant. Answer the question using only the retrieved "
        "context from the uploaded study material. If the answer is not present in the "
        "retrieved context, say that the answer was not found in the uploaded material. "
        "Do not make up information."
    )

    # 1. Groq (Free & fast for students: https://console.groq.com)
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
    if groq_api_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_api_key)
            completion = client.chat.completions.create(
                model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b").strip(),
                messages=[
                    {"role": "system", "content": system_instruction},
                    {
                        "role": "user",
                        "content": f"Context from Study Material:\n{context}\n\nQuestion: {question}\n\nAnswer:"
                    }
                ],
                temperature=0.2,
                max_tokens=600
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            error = str(e).replace(groq_api_key, "[redacted]")
            raise LLMProviderError(f"Groq request failed: {error}") from e

    # 2. Google Gemini
    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()
    if gemini_api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            full_prompt = (
                f"{system_instruction}\n\n"
                f"Context from Study Material:\n{context}\n\n"
                f"Question: {question}\n\n"
                f"Answer:"
            )
            response = model.generate_content(full_prompt)
            return response.text.strip()
        except Exception as e:
            return f"Error connecting to Google Gemini LLM: {str(e)}"

    # 3. OpenAI
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if openai_api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {
                        "role": "user",
                        "content": f"Context from Study Material:\n{context}\n\nQuestion: {question}\n\nAnswer:"
                    }
                ],
                temperature=0.2,
                max_tokens=600
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error connecting to OpenAI: {str(e)}"

    raise LLMConfigurationError(
        "No language model is configured. Set GROQ_API_KEY in the project .env and restart the backend."
    )


def ask_rag(question: str) -> Dict[str, Any]:
    """
    Step 5, 6, 7:
      - Vector Similarity Search in ChromaDB (Retrieves Top 3 Chunks)
      - Extracts unique file & page sources
      - Sends retrieved context to LLM
      - Returns answer and sources list
    """
    embeddings = get_embedding_function()
    vector_store = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_name="academic_rag"
    )

    try:
        count = vector_store._collection.count()
        if count == 0:
            return {
                "answer": "No study material has been processed yet. Please upload and process a PDF first.",
                "sources": []
            }
    except Exception:
        return {
            "answer": "No vector database found. Please upload and process a study PDF first.",
            "sources": []
        }

    # Retrieve top 3 relevant chunks based on vector distance
    top_docs = vector_store.similarity_search(question, k=3)

    if not top_docs:
        return {
            "answer": "The answer was not found in the uploaded material.",
            "sources": []
        }

    # Extract text and deduplicate sources
    context_chunks = []
    sources = []
    seen = set()

    for doc in top_docs:
        context_chunks.append(doc.page_content.strip())
        file_name = doc.metadata.get("file", "Uploaded Document")
        page_num = doc.metadata.get("page", 1)
        source_key = (file_name, page_num)
        if source_key not in seen:
            seen.add(source_key)
            sources.append({"file": file_name, "page": page_num})

    context_combined = "\n\n---\n\n".join(context_chunks)

    # Generate answer with LLM
    answer = call_llm(question, context_combined)

    return {
        "answer": answer,
        "sources": sources
    }
