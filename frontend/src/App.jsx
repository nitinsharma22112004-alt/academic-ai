import React, { useState, useRef, useEffect } from "react";

const BACKEND_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

export default function App() {
  // File state
  const [selectedFile, setSelectedFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processSuccess, setProcessSuccess] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const fileInputRef = useRef(null);

  // Question & Answer state
  const [question, setQuestion] = useState("");
  const [isAsking, setIsAsking] = useState(false);
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [groqStatus, setGroqStatus] = useState("checking");

  // Error handling
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let isMounted = true;

    fetch(`${BACKEND_URL}/health`)
      .then((response) => {
        if (!response.ok) throw new Error("Backend health check failed");
        return response.json();
      })
      .then((data) => {
        if (isMounted) {
          setGroqStatus(data.available_providers?.groq ? "configured" : "missing");
        }
      })
      .catch(() => {
        if (isMounted) setGroqStatus("offline");
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // Handle PDF file selection
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setErrorMessage("Please select a valid PDF file.");
        return;
      }
      setSelectedFile(file);
      setProcessSuccess(false);
      setUploadMessage("");
      setAnswer("");
      setSources([]);
      setErrorMessage("");
    }
  };

  // Upload and process the PDF via Backend API (POST /upload)
  const handleProcessPdf = async () => {
    if (!selectedFile) {
      setErrorMessage("Please choose a PDF file first.");
      return;
    }

    setIsProcessing(true);
    setErrorMessage("");
    setProcessSuccess(false);
    setAnswer("");
    setSources([]);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch(`${BACKEND_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to process PDF");
      }

      const data = await response.json();
      setProcessSuccess(true);
      setUploadMessage(data.message || "PDF processed successfully");
    } catch (err) {
      setErrorMessage(
        err.message || "Could not connect to backend. Make sure the FastAPI server is running."
      );
    } finally {
      setIsProcessing(false);
    }
  };

  // Ask question via Backend API (POST /ask)
  const handleAskQuestion = async (e) => {
    e.preventDefault();

    if (!question.trim()) {
      setErrorMessage("Please enter a question to ask.");
      return;
    }

    setIsAsking(true);
    setErrorMessage("");

    try {
      const response = await fetch(`${BACKEND_URL}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: question.trim() }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to retrieve answer");
      }

      const data = await response.json();
      setAnswer(data.answer);
      setSources(data.sources || []);
    } catch (err) {
      setErrorMessage(
        err.message || "Could not get an answer from the backend server."
      );
    } finally {
      setIsAsking(false);
    }
  };

  return (
    <div className="app-container">
      {/* 1. Header */}
      <header className="app-header">
        <span className="app-badge">🎓 B.Tech CSE Project Demo</span>
        <h1 className="app-title">Academic AI — RAG Question Answering System</h1>
        <p className="app-subtitle">Ask questions from your study material</p>
      </header>

      {groqStatus === "missing" && (
        <div className="status-error" role="status">
          Groq is not configured. Revoke the key shared in chat, add a rotated key as GROQ_API_KEY in .env, and restart the backend.
        </div>
      )}
      {groqStatus === "configured" && (
        <div className="status-success" role="status">Groq API key is configured.</div>
      )}
      {groqStatus === "offline" && (
        <div className="status-error" role="status">Backend is unavailable. Start the FastAPI server on port 8000.</div>
      )}

      {/* Global Error Banner */}
      {errorMessage && (
        <div className="status-error">
          <span>⚠️ {errorMessage}</span>
        </div>
      )}

      {/* 2. PDF Upload Section */}
      <section className="academic-card">
        <h2 className="card-title">
          <span>📁</span> Upload Study Material
        </h2>

        <div className="upload-row">
          <div className="file-picker-wrapper">
            <input
              type="file"
              accept=".pdf"
              ref={fileInputRef}
              onChange={handleFileChange}
              className="file-input-hidden"
              id="pdf-upload-input"
            />
            <label htmlFor="pdf-upload-input" className="btn-choose">
              📄 Choose PDF
            </label>

            <span className="selected-file-label">
              Selected file:{" "}
              {selectedFile ? (
                <span className="selected-file-highlight">{selectedFile.name}</span>
              ) : (
                "None selected"
              )}
            </span>
          </div>

          <div>
            <button
              onClick={handleProcessPdf}
              disabled={!selectedFile || isProcessing}
              className="btn-primary"
            >
              {isProcessing ? (
                <>
                  <span className="spinner"></span> Processing PDF...
                </>
              ) : (
                "Process PDF"
              )}
            </button>
          </div>
        </div>

        {/* Processed confirmation */}
        {processSuccess && (
          <div className="status-success">
            <span>✓ {uploadMessage}</span>
          </div>
        )}
      </section>

      {/* 3. Question Section */}
      <section className="academic-card">
        <h2 className="card-title">
          <span>❓</span> Ask Your Question
        </h2>

        <form onSubmit={handleAskQuestion} className="question-form">
          <input
            type="text"
            className="question-input"
            placeholder="What is normalization in DBMS?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={isAsking}
          />

          <div>
            <button
              type="submit"
              disabled={isAsking || !question.trim() || !processSuccess}
              className="btn-primary"
            >
              {isAsking ? (
                <>
                  <span className="spinner"></span> Searching & Generating Answer...
                </>
              ) : (
                processSuccess ? "Ask Question" : "Process PDF First"
              )}
            </button>
          </div>
        </form>
      </section>

      {/* 4. Answer Section */}
      {answer && (
        <section className="academic-card">
          <h2 className="card-title">
            <span>💡</span> AI Answer
          </h2>
          <div className="answer-box">
            {answer}
          </div>
        </section>
      )}

      {/* 5. Sources Section */}
      {sources && sources.length > 0 && (
        <section className="academic-card">
          <h2 className="card-title">
            <span>📚</span> Sources
          </h2>
          <div className="sources-list">
            {sources.map((src, index) => (
              <div key={index} className="source-item">
                <div className="source-file" title={src.file}>
                  📄 {src.file}
                </div>
                <div className="source-page">Page {src.page}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Academic Project Presentation Footer */}
      <footer className="demo-footer">
        <p>
          RAG Pipeline: PDF Text Extraction ➔ Chunking ➔ Hugging Face Embeddings ➔ ChromaDB Vector Store ➔ LLM Response
        </p>
      </footer>
    </div>
  );
}
