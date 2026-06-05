# 🌟 Mutual Fund AI Assistant (RAG Pipeline)

A highly structured, facts-only Retrieval-Augmented Generation (RAG) system for Indian Mutual Funds. This assistant extracts mutual fund data, strictly adheres to factual responses (no advisory), constraints output to 3 sentences, and attributes data directly to its source.

## 🚀 Features

- **Facts-Only Guardrails**: A zero-shot Intent Classifier intercepts non-factual queries (e.g. "Should I buy?", "Is this good?") and blocks them.
- **Context-Aware Semantic Retrieval**: Retrieves only the most accurate context from ChromaDB using `all-MiniLM-L6-v2` embeddings.
- **Strictly Formatted Outputs**: Guarantees all responses are ≤ 3 sentences and end with `Last updated from sources: <date>`.
- **Beautiful Glassmorphism UI**: A gorgeous, dark-themed Vite/React Chat Interface with smooth animations.
- **High-Speed Inference**: Powered by the Groq API (`llama-3.3-70b-versatile`) for blazing fast generation.

---

## 🛠️ Project Architecture

```
RAG-Milestone/
├── data/                  # Contains parsed .txt and .json files for 15 Mutual Funds
├── chroma_db/             # Local Vector Database for context retrieval
├── docs/                  # Architecture & Implementation Plans
├── ui/                    # Vite + React Frontend
│   ├── src/
│   │   ├── App.jsx        # Main Chat UI Component
│   │   └── index.css      # Custom Vanilla CSS with Glassmorphism 
├── src/                   # Python Backend Core
│   ├── api.py             # FastAPI Server 
│   ├── rag.py             # End-to-End RAG Pipeline (Retrieval + Generation)
│   ├── guardrails.py      # LLM Intent Router
│   ├── ingestion.py       # Data Extraction & Chunking Logic
│   └── config.py          # Environment Variables & Configurations
└── .env                   # API Keys (Groq)
```

---

## 🚦 Getting Started

### 1. Prerequisites
- Python 3.10+
- Node.js (v18+)

### 2. Backend Setup (FastAPI)
1. Set up your Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies (if not already installed):
   ```bash
   pip install -r requirements.txt
   # OR: pip install fastapi uvicorn pydantic langchain langchain-groq langchain-huggingface sentence-transformers chromadb beautifulsoup4 python-dotenv
   ```
3. Set your Groq API Key:
   Ensure you have a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_actual_key_here
   ```
4. Start the FastAPI Server:
   ```bash
   cd src
   ../venv/bin/uvicorn api:app --reload --port 8000
   ```
   *The API will be available at `http://localhost:8000`*

### 3. Frontend Setup (React/Vite)
1. Navigate to the `ui` folder:
   ```bash
   cd ui
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite Development Server:
   ```bash
   npm run dev
   ```
   *The UI will typically be available at `http://localhost:5173`*

---

## 🧪 Testing the Pipeline

You can run the built-in test scripts to verify the Guardrails and the RAG logic without spinning up the server:

```bash
cd src
../venv/bin/python test_guardrails.py
../venv/bin/python test_rag.py
```

## 🔒 Limitations & Rules
- **No Advisory**: The AI is strictly prohibited from providing financial advice or comparing funds subjectively.
- **Fixed URLs**: The knowledge base is explicitly limited to the 15 predefined HDFC/Groww mutual fund pages.
- **Short Responses**: The AI truncates any response that naturally exceeds 3 sentences.
