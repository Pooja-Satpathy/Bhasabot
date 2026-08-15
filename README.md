# BhasaBot 🌐

> **Multilingual RAG-powered PDF Question Answering — Ask in Hindi,English,Odia,Hinglish,Odilish.**

BhashaBot lets you upload any PDF document and ask questions about it in your native language. It uses **multilingual-e5-large** embeddings for cross-lingual semantic search, **ChromaDB** as a local vector database, and **Google Gemini** for intelligent response generation.

---

## ✨ Features

- 📄 **PDF Ingestion** — Upload any PDF via drag-and-drop
- 🌍 **Multilingual** — Ask in Hindi,English,,Odia,Hinglish,Odilish.
- 🔍 **Semantic Search** — `intfloat/multilingual-e5-large` embeddings for accurate retrieval
- 🤖 **Gemini Answers** — Google Gemini 1.5 Flash generates context-grounded responses
- 📌 **Source Citations** — Every answer shows which chunks it was derived from
- 🔤 **Language Detection** — Automatic query language detection via `langdetect`
- 🇮🇳 **IndicTrans2 Ready** — Placeholder hooks for AI4Bharat's IndicTrans2 model
- 💾 **Persistent Storage** — ChromaDB persists vectors across server restarts

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        BhasaBot                            │
│                                                             │
│  ┌───────────────┐         ┌─────────────────────────────┐  │
│  │   React UI    │ ──API── │      FastAPI Backend        │  │
│  │   (Port 3000) │         │      (Port 8000)            │  │
│  └───────────────┘         │                             │  │
│                            │  PDF Parser (PyMuPDF)       │  │
│                            │  Embedder (E5-large)        │  │
│                            │  ChromaDB (Vector Store)    │  │
│                            │  Gemini API (LLM)           │  │
│                            └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
bhashabot/
├── backend/
│   ├── main.py                   # FastAPI app with CORS
│   ├── routes/
│   │   ├── upload.py             # POST /api/upload
│   │   └── chat.py               # POST /api/chat
│   ├── services/
│   │   ├── pdf_parser.py         # PyMuPDF text extraction
│   │   ├── chunker.py            # 500-token overlapping chunks
│   │   ├── embedder.py           # multilingual-e5-large embeddings
│   │   ├── vector_store.py       # ChromaDB storage & retrieval
│   │   ├── translator.py         # Language detection + IndicTrans2 placeholder
│   │   └── rag_chain.py          # RAG pipeline + Gemini API call
│   ├── models/
│   │   └── schemas.py            # Pydantic request/response models
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── public/index.html
    ├── src/
    │   ├── pages/Home.jsx
    │   ├── components/
    │   │   ├── FileUpload.jsx
    │   │   ├── ChatWindow.jsx
    │   │   ├── MessageBubble.jsx
    │   │   └── LangBadge.jsx
    │   ├── api/client.js
    │   ├── App.jsx
    │   ├── index.js
    │   └── index.css
    ├── tailwind.config.js
    └── package.json
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- A Google Gemini API key ([get one here](https://aistudio.google.com/app/apikey))

---

### Backend Setup

```bash
cd D:\bhashabot\backend

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

copy .env.example .env
# Edit .env → add your GEMINI_API_KEY

uvicorn main:app --reload --port 8000
```

> **Note:** The `multilingual-e5-large` model (~560MB) downloads automatically on first run.

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`

---

### Frontend Setup

```bash
cd D:\bhashabot\frontend

npm install

copy .env.example .env

npm start
```

App opens at `http://localhost:3000`

---

## 🔑 API Reference

### `POST /api/upload`
Upload a PDF for processing.

### `POST /api/chat`
Ask a question about the uploaded document.

```json
{ "query": "इस दस्तावेज़ का सारांश दें", "session_id": "uuid-string" }
```

---

## 🌏 Supported Languages

Hindi,English,Odia ,Hinglish,Odilish

---

## 🛣️ Roadmap

- [ ] IndicTrans2 integration
- [ ] Multi-document sessions
- [ ] Streaming responses
- [ ] Docker Compose setup

---

## 📄 License

MIT License
