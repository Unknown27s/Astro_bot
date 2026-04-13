# Query to Vector Search Flow in AstroBot

This document explains exactly how AstroBot converts a user query into numerical vectors, how it searches stored vectors, and which tools are used.

---

## 1. Big Picture

AstroBot uses Retrieval-Augmented Generation (RAG):

1. Convert documents into vector embeddings during upload.
2. Convert user query into a vector at runtime.
3. Run vector similarity search in ChromaDB.
4. Send top matching chunks to the LLM for grounded answer generation.

Core runtime path:

- API entry: `POST /api/chat` in `api_server.py`
- Retrieval: `rag/retriever.py`
- Embedding + vector DB: `ingestion/embedder.py`
- Generation: `rag/generator.py`

---

## 2. Document Side (How Stored Data Becomes Searchable)

Before query search can work, uploaded documents are indexed:

1. File upload endpoint receives a document (`/api/documents/upload`).
2. Text is extracted by parser (`ingestion/parser.py`).
3. Text is split into chunks (`ingestion/chunker.py`).
4. Each chunk is embedded by `generate_embeddings()`.
5. Chunks + embeddings + metadata are saved to ChromaDB collection `ims_documents`.
6. Upload pipeline also generates suggested user questions from headings/content and stores them for autocomplete.

Important chunk metadata stored with vectors:

- source file name
- heading/section
- chunk index
- doc_id

This is implemented by `store_chunks()` in `ingestion/embedder.py`.

---

## 3. Query Side (How Query Becomes Vector)

When a user sends a question to `POST /api/chat`:

1. API calls `retrieve_context(query, ...)`.
2. `retrieve_context()` calls:
   - `generate_embeddings([query])[0]`
3. `generate_embeddings()` uses Sentence Transformers model from config (`EMBEDDING_MODEL`, default `all-MiniLM-L6-v2`).
4. Embeddings are generated with `normalize_embeddings=True`.

So the query text becomes a dense float vector, typically 384 dimensions for `all-MiniLM-L6-v2`.

Example shape (illustrative):

- query: "what is the leave policy"
- vector: `[0.021, -0.114, 0.337, ..., -0.045]` (length = 384)

---

## 4. How Vector Search Works in Stored Data

The retriever then searches ChromaDB:

1. Get collection `ims_documents` from persistent client.
2. Run `collection.query(...)` with:
   - `query_embeddings=[query_embedding]`
   - `n_results=min(top_k, collection_size)`
   - `include=["documents", "metadatas", "distances"]`
3. ChromaDB returns nearest vectors by cosine distance.

Collection is created with:

- `metadata={"hnsw:space": "cosine"}`

This means nearest-neighbor search is cosine-based.

Distance is converted to a user-facing similarity score in `rag/retriever.py`:

- `similarity = 1 - (distance / 2)`

The same conversion is now printed in terminal trace output for each retrieved chunk:

- raw `distance`
- converted `similarity`
- formula note `similarity = 1 - distance/2`

Then each result is returned as:

- text (chunk content)
- source
- heading
- score
- doc_id

### Hybrid Retrieval Mode (Dense + BM25)

AstroBot now supports a hybrid retrieval mode in `rag/retriever.py`:

1. Dense retrieval from ChromaDB cosine similarity.
2. BM25 keyword retrieval over indexed chunk text.
3. Weighted fusion + reranking.

Fusion score:

- `final_score = HYBRID_DENSE_WEIGHT * dense_score + (1 - HYBRID_DENSE_WEIGHT) * bm25_score`

This helps when user questions are indirect, short, or keyword-heavy.

### HyDE Fallback (Low-Confidence Retrieval)

AstroBot now supports conditional HyDE in `rag/retriever.py`.

Flow:

1. Run normal retrieval (`dense` or `hybrid`).
2. If top score is below `HYDE_TRIGGER_SCORE`, generate a hypothetical passage from the user question.
3. Re-run retrieval using that hypothetical text.
4. Merge and rerank original + HyDE results.

This improves recall for indirect or ambiguous queries where direct user wording does not match document language.

---

## 5. What Happens After Retrieval

1. Retrieved chunks are formatted into a context block.
2. Context is passed to `generate_response(...)`.
3. LLM generates the final answer grounded in retrieved context.
4. Citations are built from chunk metadata and returned to client.

---

## 6. Tools Used in This Pipeline

### Embedding and Vector Search

- sentence-transformers
  - model: `all-MiniLM-L6-v2` (default)
  - used for converting text to dense numerical vectors
- ChromaDB (`chromadb.PersistentClient`)
  - persistent local vector store
  - stores embeddings, chunk text, metadata
- HNSW cosine index (via collection metadata)
  - fast nearest-neighbor similarity search

### API and App Layer

- FastAPI
  - serves upload, chat, health, and admin endpoints
- Pydantic
  - request/response validation models

### Supporting Components

- SQLite
  - users, documents metadata, query logs, memory metadata
- Chunker and parser modules
  - convert raw files into retrieval-ready chunks
- PDF parsing for table-heavy documents
  - `pdfplumber` is the primary PDF extractor (text + table rows)
  - `PyPDF2` remains as a fallback text extractor and encryption validator

---

## 7. Key Configuration That Controls This

From `config.py`:

- `EMBEDDING_MODEL` (default: `all-MiniLM-L6-v2`)
- `TOP_K_RESULTS` (default: 5)
- `CHROMA_PERSIST_DIR` (vector store path)
- `CHUNK_SIZE` (default: 500)
- `CHUNK_OVERLAP` (default: 50)
- `RETRIEVAL_MODE` (`dense` or `hybrid`)
- `HYBRID_DENSE_WEIGHT` (default: 0.7)
- `HYBRID_DENSE_CANDIDATES` (default: 20)
- `HYBRID_BM25_CANDIDATES` (default: 40)
- `HYDE_ENABLED` (`true` or `false`)
- `HYDE_TRIGGER_SCORE` (default: 0.58)
- `HYDE_SCORE_BLEND` (default: 0.6)
- `HYDE_MAX_TOKENS` (default: 180)
- `HYDE_MAX_CHARS` (default: 1400)
- `HYDE_TEMPERATURE` (default: 0.2)

These can be changed in `.env` (and some via admin settings endpoints).

---

## 8. Minimal Mental Model

You can think of AstroBot retrieval as:

1. Text -> vector (for both documents and query)
2. Query vector compared with stored vectors
3. Closest vectors = most relevant document chunks
4. LLM answers using those chunks

That is the core reason semantic search works even when query wording differs from document wording.

---

## 9. Source Files to Read Next

- `api_server.py`
- `rag/retriever.py`
- `rag/pipeline_trace.py`
- `ingestion/embedder.py`
- `ingestion/chunker.py`
- `ingestion/question_suggester.py`
- `ingestion/parser.py`
- `rag/generator.py`
- `rag/memory.py` (semantic cache path)
