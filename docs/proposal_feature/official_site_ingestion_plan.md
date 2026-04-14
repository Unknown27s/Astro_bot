# Official Site Ingestion Plan

## Status

Phase 1 is implemented and Phase 2 has started:

- a FastAPI endpoint can fetch and ingest one official-site URL
- website chunks are tagged with `source_type=official_site`
- the Spring Boot gateway proxies the new ingestion endpoint
- the React admin Documents page now exposes a URL ingest form
- chat routing now prefers official-site chunks for public campus questions and uploaded-doc chunks for document questions

The remaining plan items are broader crawl/sitemap support and richer admin controls.

## Goal

Add a new ingestion path for official college website content so AstroBot can answer general campus questions like:

- How is this college?
- What courses are available?
- What is the admission process?
- What facilities does the college have?

The existing RAG pipeline stays in place for document, policy, and accuracy-critical questions. The new capability is an additional source layer, not a replacement.

---

## Why this is needed

The current system only ingests uploaded documents and local HTML files. It does not crawl or sync live website pages.

That means:

- general public-facing information is not guaranteed to be in the local knowledge base
- users asking about college overview or course offerings may get weaker answers unless those pages are already uploaded manually
- the model itself should not be treated as a live web browser

---

## What already exists in the repo

Current ingestion support includes:

- PDF, DOCX, TXT, XLSX, CSV, PPTX, and HTML parsing in `ingestion/parser.py`
- HTML cleanup using BeautifulSoup
- chunking in `ingestion/chunker.py`
- embeddings and ChromaDB storage in `ingestion/embedder.py`
- document-derived question suggestions in `ingestion/question_suggester.py`

Important limitation:

- `parse_html()` only parses a saved HTML file
- there is no live `fetch URL -> crawl -> ingest` pipeline yet

---

## Recommended architecture

### 1. Official-site source ingestion

Add a new ingestion module, for example:

- `ingestion/web_ingest.py`

Responsibilities:

- fetch allowed URLs
- remove boilerplate navigation/footer/script content
- normalize titles, headings, and text
- chunk the cleaned content
- embed and store the chunks
- tag each chunk as `official_site`

### 2. Source metadata

Store extra metadata for website chunks:

- `source_type = official_site`
- `source_url`
- `page_title`
- `domain`
- `crawl_time`
- `robots_allowed`
- optional `content_hash`

This helps with citation quality and re-crawl detection.

### 3. Query routing layer

Add an intent router before retrieval/generation:

- `document` questions -> current RAG pipeline
- `official_site` questions -> official-site knowledge base
- `hybrid` questions -> merge both sources
- `unclear` questions -> either ask a clarification or use best-effort hybrid routing

### 4. Admin controls

Add settings for:

- allowed domain list
- refresh interval
- page allowlist or sitemap URL
- enable/disable official-site mode
- source priority rules

---

## Suggested ingestion flow

1. Admin enters a domain or sitemap URL.
2. System validates the domain is allowed.
3. A crawler collects URLs from sitemap, seed page, or curated list.
4. Each page is fetched with HTTP GET.
5. HTML is cleaned and converted to plain text.
6. Chunker splits the text into retrieval-ready pieces.
7. Embeddings are generated and stored in ChromaDB.
8. Metadata records the page URL and crawl time.
9. A refresh job re-crawls pages periodically.

---

## Query routing design

Use a lightweight classifier or rule-based router first.

Example signals:

- general campus words: college, campus, facility, hostel, placement, courses, fees, admission, address, contact
- document words: policy, handbook, syllabus, circular, regulation, notice, timetable, exam, leave, attendance
- technical words: code, API, error, function, config, database, retrieval

Example rule:

- if query is public-facing and not document-specific, prefer official-site search
- if query mentions policy, documents, or exact rules, prefer RAG
- if query contains both types, use hybrid mode

---

## Can this be free?

### Yes, if done locally

You can build this without paid third-party services if you:

- crawl pages yourself with `requests` or similar
- parse HTML locally with BeautifulSoup
- embed locally with SentenceTransformers
- store locally in ChromaDB and SQLite

That is the cheapest and most controlled option.

### What may still cost money

- server/VM hosting
- bandwidth and storage
- maintenance time
- any external search or crawling API

### When it stops being free

If you use paid tools such as:

- search APIs
- hosted web extraction services
- managed crawling services

then you may incur usage costs or quotas.

---

## Best implementation options

### Option A: Official-site RAG ingestion only

Best default choice.

Pros:

- free if self-hosted
- stable and citeable
- faster than live browsing
- good for college/course information

Cons:

- needs a refresh job
- only covers allowed pages

### Option B: Live web search API

Use a search API at query time.

Pros:

- faster to prototype
- can answer with current public web information

Cons:

- often paid or quota-limited
- less deterministic
- harder to cite cleanly

### Option C: Hybrid route

Use RAG for documents, official-site ingestion for public campus content, and live web search only as fallback.

This is the strongest long-term design.

---

## Recommended implementation phases

### Phase 1: Discovery and policy

- define allowed domain list
- decide whether sitemap-based crawl is enough
- define crawl frequency
- define what content should never be crawled

### Phase 2: Ingestion module

- build HTML fetcher
- add boilerplate removal
- extract title and body text
- store source metadata

### Phase 3: Storage and retrieval

- store official-site chunks in ChromaDB
- label chunks by source type
- update retriever to filter by source type

### Phase 4: Query router

- classify query intent
- route to document RAG, official-site RAG, or hybrid
- return the selected mode to the frontend
- scope conversation memory to the selected route so results stay consistent

### Phase 5: Admin UI and refresh job

- add crawl management screen
- show crawl status and last refresh time
- support manual re-index

### Phase 6: Evaluation

- compare answer quality for general campus questions
- compare latency and source coverage
- test ambiguity handling

---

## Files likely to change

- `ingestion/parser.py`
- `ingestion/chunker.py`
- `ingestion/embedder.py`
- `rag/retriever.py`
- `rag/generator.py`
- `api_server.py`
- `database/db.py`
- `react-frontend/src/services/api.js`
- `react-frontend/src/pages/admin/*`
- `docs/architecture/QUERY_TO_VECTOR_SEARCH.md`

New files likely needed:

- `ingestion/web_ingest.py`
- `ingestion/url_discovery.py`
- `docs/proposal_feature/official_site_ingestion_plan.md` is this document

---

## Risks

- Crawling too much content can create noisy search results.
- Unfiltered website content can mix marketing text with useful information.
- Some pages may block bots or require JS rendering.
- Public website content can change often, so stale answers are possible.
- Live web search may return inconsistent or unverified sources.

---

## Recommendation

Build official-site ingestion as a local, controlled source layer first.

That gives you:

- no per-query search cost
- better citations
- better control over source quality
- less dependency on external APIs

Then add live web search only as a fallback if the official-site knowledge base cannot answer the question.
