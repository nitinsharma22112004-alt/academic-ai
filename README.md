# Academic AI — RAG Question Answering System 🎓

A prototype demonstration of **Retrieval-Augmented Generation (RAG)** built for a **B.Tech CSE Project / Demo**.

This system allows students and professors to upload study materials (PDFs), index them into a vector database, and ask academic questions. The system retrieves relevant passages from the study material and uses an LLM to generate grounded, fact-based answers with exact source citations (file name and page numbers).

---

## 🏗️ Folder Structure

```text
academic-rag-prototype/
│
├── backend/
│   ├── main.py                  # FastAPI web server (POST /upload, POST /ask)
│   ├── rag.py                   # RAG pipeline: chunking, embeddings, ChromaDB, LLM
│   ├── requirements.txt         # Backend Python dependencies
│   ├── create_sample_pdf.py     # Helper to generate test DBMS_Notes.pdf
│   ├── uploads/                 # Storage for uploaded PDFs
│   └── chroma_db/               # Persistent Chroma vector store
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main academic UI component
│   │   ├── main.jsx             # React entry point
│   │   └── index.css            # Light academic styling (blue/purple theme)
│   ├── index.html               # HTML document template
│   ├── package.json             # Frontend Node dependencies
│   └── vite.config.js           # Vite dev server configuration
│
├── sample_documents/
│   └── DBMS_Notes.pdf           # Ready-to-use 3-page study notes PDF
│
├── .env                         # Environment variables (API keys)
└── README.md                    # Project documentation & presentation guide
```

---

## 🔄 RAG Workflow Architecture

```text
+-----------------------+
|  1. Upload Study PDF  | (e.g., DBMS_Notes.pdf)
+-----------+-----------+
            |
            v
+-----------------------+
|  2. Extract Text      | (PyPDF extracting text + page numbers)
+-----------+-----------+
            |
            v
+-----------------------+
|  3. Split into Chunks | (RecursiveCharacterTextSplitter: 800 chars, 120 overlap)
+-----------+-----------+
            |
            v
+-----------------------+
| 4. Generate Embeddings| (Hugging Face 'all-MiniLM-L6-v2' vector representations)
+-----------+-----------+
            |
            v
+-----------------------+
| 5. Store in ChromaDB  | (Persistent vector database collection)
+-----------+-----------+
            |
            v
+-----------------------+
| 6. User Asks Question | ("What is normalization in DBMS?")
+-----------+-----------+
            |
            v
+-----------------------+
| 7. Similarity Search  | (ChromaDB cosine/L2 distance search for top relevant chunks)
+-----------+-----------+
            |
            v
+-----------------------+
| 8. Grounded Prompt    | (Academic system prompt + retrieved context)
+-----------+-----------+
            |
            v
+-----------------------+
| 9. LLM Answer Gen     | (Groq / Gemini / OpenAI)
+-----------+-----------+
            |
            v
+-----------------------+
| 10. Display to User   | (Factual Answer + Source file + Page #)
+-----------------------+
```

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 18 + Vite | Interactive, responsive student UI |
| **Styling** | Modern CSS3 | Clean academic theme with purple/blue accents |
| **Backend API** | FastAPI + Uvicorn | High-performance asynchronous REST endpoints |
| **PDF Extraction** | PyPDF | Extracts text while tracking page numbers |
| **Text Splitter** | LangChain Text Splitters | Chunks document preserving context boundaries |
| **Embeddings** | Hugging Face (`all-MiniLM-L6-v2`) | Converts academic text into dense 384-d vectors |
| **Vector DB** | ChromaDB | Stores chunk embeddings and retrieves nearest matches |
| **LLM Inference** | Groq / Gemini / OpenAI | Synthesizes final academic answer with strict guardrails |

---

## 🔑 Environment Configuration (`.env`)

Create or update the `.env` file in the root project folder (or in `backend/.env`):

```env
# ============================================================
# Academic AI — RAG Prototype Configuration
# ============================================================

# Option 1: Groq (Recommended for students: 100% Free & Fast: https://console.groq.com)
GROQ_API_KEY=gsk_your_groq_api_key_here

# Option 2: Google Gemini (Free tier available: https://aistudio.google.com)
GEMINI_API_KEY=your_gemini_api_key_here

# Option 3: OpenAI (https://platform.openai.com)
OPENAI_API_KEY=sk_your_openai_api_key_here

# Backend Network Settings
HOST=127.0.0.1
PORT=8000
```

> **Note:** You only need **one** of the API keys above. If you don't have an API key yet, the system still runs vector similarity retrieval and displays the top extracted chunks and page numbers!

---

## 💻 Step-by-Step Installation & Run Guide

### 1. Prerequisites
- **Python**: Version 3.10, 3.11, 3.12, or 3.13
- **Node.js**: Version 18+ (comes with `npm`)
- **VS Code**: With terminal access

---

### 2. Backend Setup

Open a terminal in the `backend/` folder:

```bash
# 1. Navigate to backend directory
cd backend

# 2. (Recommended) Create and activate a Python virtual environment
# On Windows:
python -m venv venv
venv\Scripts\activate

# On macOS/Linux:
python3 -m venv venv
source venv/bin/activate

# 3. Install backend dependencies
pip install -r requirements.txt

# 4. Start the FastAPI server
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The backend server will start at: **`http://127.0.0.1:8000`**
Interactive API Swagger docs are available at: **`http://127.0.0.1:8000/docs`**

---

### 3. Frontend Setup

Open a second terminal in the `frontend/` folder:

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install Node dependencies
npm install

# 3. Start the Vite development server
npm run dev
```

The frontend will run at: **`http://localhost:5173`**

---

## 🧪 How to Test the Prototype

1. Open your web browser at **`http://localhost:5173`**.
2. Under **Upload Study Material**, click **Choose PDF** and select the provided sample file:
   `sample_documents/DBMS_Notes.pdf` (or any study PDF you have).
3. Click **Process PDF**. You will see:
   ```text
   ✓ PDF processed successfully
   ```
4. In the **Ask Your Question** section, enter:
   `What is normalization in DBMS?`
5. Click **Ask Question**.
6. The system will display:
   - **AI Answer**: A concise, academic explanation of normalization, normal forms (1NF, 2NF, 3NF, BCNF), and redundancy reduction.
   - **Sources**:
     ```text
     📄 DBMS_Notes.pdf
     Page 2
     ```
7. Try asking another question:
   `What are ACID properties?`
   - It will return Atomicity, Consistency, Isolation, Durability from **Page 3**.

---

## 🎓 B.Tech Project Viva & Presentation Questions

When presenting this project to your college viva panel, here is how you can explain each component:

### 1. What is RAG and why is it better than fine-tuning for study materials?
> **Answer:** Retrieval-Augmented Generation (RAG) is a pattern that grounds an LLM's answers on external documents without modifying the model's weights. Fine-tuning takes time, is expensive, and can still hallucinate. RAG allows instant updates when new PDFs are uploaded and provides verifiable source citations (page numbers).

### 2. Why do we split text into chunks?
> **Answer:** LLMs and embedding models have maximum token context limits. Moreover, chunking ensures that vector similarity search retrieves only the specific paragraphs relevant to the student's question rather than the entire textbook. Overlapping (e.g., 120 characters) prevents definitions from being cut in half across chunk boundaries.

### 3. What role does ChromaDB play?
> **Answer:** ChromaDB is a vector database. It stores the 384-dimensional mathematical embeddings generated by Hugging Face (`all-MiniLM-L6-v2`). When the user asks a question, ChromaDB compares the question's embedding with all stored chunk embeddings using cosine similarity to find the top $k$ nearest matches in milliseconds.

### 4. How does the system prevent AI hallucination?
> **Answer:** We use prompt guardrails:
> *"You are an academic assistant. Answer the question using only the retrieved context from the uploaded study material. If the answer is not present in the retrieved context, say that the answer was not found in the uploaded material. Do not make up information."*
> If a student asks something not in the PDF (e.g., "Who won the 2024 cricket world cup?"), the system refuses to guess and informs them that the answer was not found in their notes.

# academic-ai

## Deploy

The frontend is deployed to Vercel and the FastAPI backend to Render. The backend uses a Render persistent disk for uploaded PDFs and the Chroma database.

1. Push the project source to GitHub. `.gitignore` excludes `.env` files, local uploads, Chroma data, and build artifacts.
2. In Render, create a Blueprint from the repository root. The root `render.yaml` creates the API service and persistent disk. Set `GROQ_API_KEY` when prompted; never commit it.
3. In Vercel, import the same repository and set the project Root Directory to `frontend`.
4. Set Vercel's `VITE_API_URL` environment variable to the deployed Render API URL, without a trailing slash, then deploy or redeploy.
5. Check `<Render API URL>/health` and confirm `available_providers.groq` is `true`.

The Render service uses a paid plan because persistent disks are not available on the free web-service plan. Deploying only the Vercel frontend will not enable PDF upload or question answering.
