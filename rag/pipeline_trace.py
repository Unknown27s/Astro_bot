"""
IMS AstroBot — Pipeline Trace (Terminal Explainability)
Prints a beautiful, step-by-step trace of the RAG pipeline to the server terminal.
Designed for jury demos: shows exactly what happens internally when a query is processed.

Fixes applied:
  1. Duplicate "Step 8" label — Final Summary is now "Step 9".
  2. _safe_print ASCII fallback — strips ANSI codes properly before printing,
     instead of replacing every escape byte with '?'.
  3. _chunk_block progress bar — dynamically generated from the actual similarity
     value instead of three hardcoded strings.
  4. record_chunk rank param — auto-incremented internally; callers no longer
     need to track rank themselves (old rank= kwarg still accepted for compat).
  5. Step 3b label — renamed "Step 3.5" in output and reorganised step numbering
     so the sequence reads cleanly.
  6. _kv None handling — None values are rendered as a dimmed "—" instead of
     the plain white string "None".
  7. to_dict() — serialises the full trace for file/DB logging.
"""

import re
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── ANSI Color Codes (supported in Windows 10+ terminals) ──────────────────
_RESET   = "\033[0m"
_BOLD    = "\033[1m"
_DIM     = "\033[2m"
_CYAN    = "\033[96m"
_GREEN   = "\033[92m"
_YELLOW  = "\033[93m"
_MAGENTA = "\033[95m"
_BLUE    = "\033[94m"
_RED     = "\033[91m"
_WHITE   = "\033[97m"
_ORANGE  = "\033[38;5;208m"

# Regex that matches any ANSI escape sequence — used by _safe_print fallback
_ANSI_ESCAPE = re.compile(r"\033\[[0-9;]*[mGKHF]")


# ── Formatting helpers ──────────────────────────────────────────────────────

def _bar(width: int = 70, char: str = "=") -> str:
    return f"{_DIM}{_CYAN}{char * width}{_RESET}"


def _section(icon: str, title: str, time_ms: float = None) -> str:
    time_str = f"  {_DIM}({time_ms:.1f}ms){_RESET}" if time_ms is not None else ""
    return f"\n{_BOLD}{_CYAN}{icon} {title}{_RESET}{time_str}"


def _kv(key: str, value, indent: int = 4) -> str:
    """
    Key-value line.  Fix 6: None values render as a dimmed dash instead of
    the literal white string "None".
    """
    pad = " " * indent
    if value is None:
        rendered = f"{_DIM}—{_RESET}"
    else:
        rendered = f"{_WHITE}{value}{_RESET}"
    return f"{pad}{_DIM}{key}:{_RESET} {rendered}"


def _chunk_block(
    rank: int,
    source: str,
    heading: str,
    similarity: float,
    text_preview: str,
    distance: Optional[float] = None,
) -> str:
    """
    Format a single retrieved chunk for terminal display.

    Fix 3: progress bar is built dynamically from the actual similarity value
    so the fill fraction always reflects the real score.
    """
    # Color-code similarity
    if similarity >= 0.90:
        score_color = _GREEN
    elif similarity >= 0.75:
        score_color = _YELLOW
    else:
        score_color = _RED

    # Fix 3: dynamic bar — 20 chars wide, filled proportionally
    bar_width = 20
    filled = round(similarity * bar_width)
    bar_fill = "#" * filled + "-" * (bar_width - filled)

    lines = [
        f"      {_BOLD}#{rank}{_RESET} {_DIM}------------------------------------------{_RESET}",
        f"      {_DIM}Source:{_RESET}     {_MAGENTA}{source}{_RESET}",
    ]
    if heading:
        lines.append(f"      {_DIM}Section:{_RESET}    {heading}")
    if distance is not None:
        lines.append(
            f"      {_DIM}Distance:{_RESET}   {distance:.4f}"
            f" {_DIM}(similarity = 1 - distance/2){_RESET}"
        )
    lines.append(
        f"      {_DIM}Similarity:{_RESET} {score_color}{similarity:.1%}{_RESET}"
        f"  {_DIM}[{bar_fill}]{_RESET}"
    )
    preview = text_preview[:150].replace("\n", " | ")
    if len(text_preview) > 150:
        preview += "..."
    lines.append(f"      {_DIM}Text:{_RESET}       {_DIM}\"{preview}\"{_RESET}")
    return "\n".join(lines)


def _safe_print(text: str) -> None:
    """
    Print text safely to terminal.

    Fix 2: on UnicodeEncodeError the ANSI escape sequences are stripped first
    so the fallback is clean, readable plain text — not a flood of '?' chars.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        plain = _ANSI_ESCAPE.sub("", text)
        print(plain.encode("ascii", errors="replace").decode("ascii"))


# ── Main class ──────────────────────────────────────────────────────────────

class PipelineTrace:
    """
    Collects step-by-step info during a RAG query and prints it to the terminal.

    Usage::

        trace = PipelineTrace(query, username)
        # pass trace through pipeline; each step calls the appropriate record_*
        trace.print_summary()

    To persist the trace for logging / analytics::

        data = trace.to_dict()
    """

    def __init__(self, query: str, username: str = "unknown"):
        self.query = query
        self.username = username
        self.start_time = time.time()

        # Embedding
        self.embedding_model: Optional[str] = None
        self.embedding_dims: Optional[int] = None
        self.embedding_preview: Optional[list] = None
        self.embedding_time_ms: Optional[float] = None

        # Memory / cache
        self.memory_checked = False
        self.memory_hit = False
        self.memory_best_similarity: Optional[float] = None
        self.memory_threshold: Optional[float] = None
        self.memory_time_ms: Optional[float] = None

        # Vector search
        self.collection_size: Optional[int] = None
        self.top_k: Optional[int] = None
        self.search_time_ms: Optional[float] = None
        self.retrieved_chunks: list[dict] = []

        # Routing
        self.route_mode: Optional[str] = None
        self.route_confidence: Optional[float] = None
        self.route_reason: Optional[str] = None

        # Query expansion
        self.expanded_queries: list[str] = []
        self.query_expansion_checked = False
        self.query_expansion_enabled = False
        self.query_expansion_reason: Optional[str] = None

        # Prompt
        self.context_char_count: Optional[int] = None
        self.system_prompt_preview: Optional[str] = None
        self.user_message_preview: Optional[str] = None

        # LLM generation
        self.provider_used: Optional[str] = None
        self.model_used: Optional[str] = None
        self.temperature: Optional[float] = None
        self.max_tokens: Optional[int] = None
        self.generation_time_ms: Optional[float] = None
        self.providers_tried: list[tuple] = []

        # Final response
        self.response_length: Optional[int] = None
        self.unique_sources: Optional[int] = None
        self.from_memory = False

    # ── record_* helpers ────────────────────────────────────────────────────

    def record_embedding(self, model: str, dims: int, preview: list, time_ms: float) -> None:
        self.embedding_model = model
        self.embedding_dims = dims
        self.embedding_preview = preview[:5]
        self.embedding_time_ms = time_ms

    def record_expansion(
        self,
        enabled: bool,
        expansions: list = None,
        reason: str = None,
    ) -> None:
        self.query_expansion_checked = True
        self.query_expansion_enabled = enabled
        self.query_expansion_reason = reason
        if expansions:
            self.expanded_queries = expansions

    def record_memory_check(
        self,
        hit: bool,
        best_similarity: float = None,
        threshold: float = None,
        time_ms: float = None,
    ) -> None:
        self.memory_checked = True
        self.memory_hit = hit
        self.memory_best_similarity = best_similarity
        self.memory_threshold = threshold
        self.memory_time_ms = time_ms

    def record_search(self, collection_size: int, top_k: int, time_ms: float) -> None:
        self.collection_size = collection_size
        self.top_k = top_k
        self.search_time_ms = time_ms

    def record_route(
        self,
        route_mode: str,
        confidence: float = None,
        reason: str = None,
    ) -> None:
        self.route_mode = route_mode
        self.route_confidence = confidence
        self.route_reason = reason

    def record_chunk(
        self,
        source: str,
        heading: str,
        similarity: float,
        text: str,
        distance: float = None,
        rank: int = None,           # Fix 4: optional — auto-incremented if omitted
    ) -> None:
        """
        Record a single retrieved chunk.

        Fix 4: rank is auto-incremented from the current list length so callers
        no longer need to track it.  Passing rank= explicitly still works for
        backward compatibility.
        """
        auto_rank = rank if rank is not None else len(self.retrieved_chunks) + 1
        self.retrieved_chunks.append(
            {
                "rank": auto_rank,
                "source": source,
                "heading": heading,
                "similarity": similarity,
                "distance": distance,
                "text": text,
            }
        )

    def record_prompt(
        self,
        system_prompt: str,
        user_message: str,
        context_chars: int,
    ) -> None:
        self.system_prompt_preview = system_prompt[:100]
        self.user_message_preview = user_message[:150]
        self.context_char_count = context_chars

    def record_generation(
        self,
        provider: str,
        model: str,
        temperature: float,
        max_tokens: int,
        time_ms: float,
        providers_tried: list = None,
    ) -> None:
        self.provider_used = provider
        self.model_used = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.generation_time_ms = time_ms
        if providers_tried:
            self.providers_tried = providers_tried

    def record_response(
        self,
        response_length: int,
        unique_sources: int,
        from_memory: bool = False,
    ) -> None:
        self.response_length = response_length
        self.unique_sources = unique_sources
        self.from_memory = from_memory

    # ── Serialisation ────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """
        Fix 7: serialise the complete trace to a plain dict suitable for
        JSON logging, database storage, or test assertions.
        """
        return {
            "query": self.query,
            "username": self.username,
            "total_ms": round((time.time() - self.start_time) * 1000, 2),
            "embedding": {
                "model": self.embedding_model,
                "dims": self.embedding_dims,
                "time_ms": self.embedding_time_ms,
            },
            "routing": {
                "mode": self.route_mode,
                "confidence": self.route_confidence,
                "reason": self.route_reason,
            },
            "query_expansion": {
                "checked": self.query_expansion_checked,
                "enabled": self.query_expansion_enabled,
                "reason": self.query_expansion_reason,
                "variants": self.expanded_queries,
            },
            "memory_cache": {
                "checked": self.memory_checked,
                "hit": self.memory_hit,
                "best_similarity": self.memory_best_similarity,
                "threshold": self.memory_threshold,
                "time_ms": self.memory_time_ms,
            },
            "vector_search": {
                "collection_size": self.collection_size,
                "top_k": self.top_k,
                "time_ms": self.search_time_ms,
                "chunks_retrieved": len(self.retrieved_chunks),
            },
            "chunks": self.retrieved_chunks,
            "prompt": {
                "context_chars": self.context_char_count,
                "system_preview": self.system_prompt_preview,
                "user_preview": self.user_message_preview,
            },
            "generation": {
                "provider": self.provider_used,
                "model": self.model_used,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "time_ms": self.generation_time_ms,
                "providers_tried": self.providers_tried,
            },
            "response": {
                "length": self.response_length,
                "unique_sources": self.unique_sources,
                "from_memory": self.from_memory,
            },
        }

    # ── Print summary ────────────────────────────────────────────────────────

    def print_summary(self) -> None:
        """Print the complete pipeline trace to the terminal."""
        total_ms = (time.time() - self.start_time) * 1000
        lines: list[str] = []

        # ── Header ──────────────────────────────────────────────────────────
        lines.append("")
        lines.append(_bar())
        lines.append(f"{_BOLD}{_CYAN}  [TRACE] RAG PIPELINE TRACE{_RESET}")
        lines.append(_bar())

        # ── Step 1: Query Received ───────────────────────────────────────────
        lines.append(_section("Step 1 | [QUERY]", "QUERY RECEIVED"))
        lines.append(_kv("User", self.username))
        lines.append(_kv("Query", f'"{self.query}"'))

        # ── Step 2: Query Embedding ──────────────────────────────────────────
        if self.embedding_model:
            lines.append(_section("Step 2 | [EMBED]", "QUERY EMBEDDING", self.embedding_time_ms))
            lines.append(_kv("Model", self.embedding_model))
            lines.append(_kv("Dimensions", f"{self.embedding_dims}-dimensional vector"))
            if self.embedding_preview:
                preview_str = ", ".join(f"{v:.4f}" for v in self.embedding_preview)
                lines.append(_kv("Vector Preview", f"[{preview_str}, ...]"))

        # ── Step 3: Query Routing ────────────────────────────────────────────
        if self.route_mode:
            lines.append(_section("Step 3 | [ROUTE]", "QUERY ROUTING"))
            lines.append(_kv("Mode", self.route_mode))
            if self.route_confidence is not None:
                lines.append(_kv("Confidence", f"{self.route_confidence:.0%}"))
            lines.append(_kv("Reason", self.route_reason))

        # ── Step 3.5: Query Expansion  (Fix 5: cleaner label) ───────────────
        if self.query_expansion_checked:
            lines.append(_section("Step 3.5 | [EXPAND]", "QUERY EXPANSION"))
            lines.append(_kv("Reason", self.query_expansion_reason))
            if not self.query_expansion_enabled:
                lines.append(_kv("Status", f"{_DIM}Disabled in config (or LLM skipped){_RESET}"))
            elif self.expanded_queries:
                lines.append(
                    _kv("Status",
                        f"{_GREEN}Enabled — {len(self.expanded_queries)} variants generated{_RESET}")
                )
                for i, eq in enumerate(self.expanded_queries, 1):
                    lines.append(_kv(f"Variant {i}", f'"{_MAGENTA}{eq}{_RESET}"'))
            else:
                lines.append(
                    _kv("Status", f"{_YELLOW}Enabled but LLM failed to generate variants{_RESET}")
                )

        # ── Step 4: Memory Check ─────────────────────────────────────────────
        if self.memory_checked:
            lines.append(_section("Step 4 | [CACHE]", "SEMANTIC MEMORY CHECK", self.memory_time_ms))
            if self.memory_hit:
                lines.append(_kv("Result", f"{_GREEN}[HIT] CACHE HIT{_RESET}"))
                lines.append(_kv("Action", "Returning cached response — skipping LLM"))
            else:
                sim_str = f"{self.memory_best_similarity:.3f}" if self.memory_best_similarity is not None else "N/A"
                thr_str = f"{self.memory_threshold:.2f}" if self.memory_threshold is not None else "N/A"
                lines.append(_kv("Result", f"{_YELLOW}[MISS] CACHE MISS{_RESET}"))
                lines.append(_kv("Best Match", f"{sim_str} similarity (threshold: {thr_str})"))
                lines.append(_kv("Action", "Proceeding to LLM generation"))

        # ── Step 5: ChromaDB Vector Search ──────────────────────────────────
        if self.collection_size is not None:
            lines.append(_section("Step 5 | [SEARCH]", "CHROMADB VECTOR SEARCH", self.search_time_ms))
            lines.append(_kv("Collection Size", f"{self.collection_size:,} vectors stored"))
            lines.append(_kv("Search Strategy", f"Cosine similarity, top-{self.top_k}"))
            lines.append(_kv("Chunks Found", f"{len(self.retrieved_chunks)} results"))

        # ── Step 6: Retrieved Chunks ─────────────────────────────────────────
        if self.retrieved_chunks:
            lines.append(_section("Step 6 | [CHUNKS]", "RETRIEVED CHUNKS (Ranked by Relevance)"))
            for chunk in self.retrieved_chunks:
                lines.append(
                    _chunk_block(
                        rank=chunk["rank"],
                        source=chunk["source"],
                        heading=chunk["heading"],
                        similarity=chunk["similarity"],
                        text_preview=chunk["text"],
                        distance=chunk.get("distance"),
                    )
                )

        # ── Step 7: Prompt Construction ──────────────────────────────────────
        if self.context_char_count is not None:
            lines.append(_section("Step 7 | [PROMPT]", "LLM PROMPT CONSTRUCTION"))
            lines.append(_kv("System Prompt", f'"{self.system_prompt_preview}..."'))
            lines.append(
                _kv("Context Size",
                    f"{self.context_char_count:,} characters from {len(self.retrieved_chunks)} chunks")
            )
            lines.append(_kv("User Message", f'"{self.user_message_preview}..."'))

        # ── Step 8: LLM Generation ───────────────────────────────────────────
        if self.provider_used:
            lines.append(_section("Step 8 | [LLM]", "LLM GENERATION", self.generation_time_ms))
            lines.append(_kv("Provider", f"{_GREEN}{self.provider_used}{_RESET}"))
            lines.append(_kv("Model", self.model_used))
            lines.append(_kv("Temperature", self.temperature))
            lines.append(_kv("Max Tokens", self.max_tokens))
            if self.providers_tried:
                tried_str = " → ".join(
                    f"{_GREEN}{name} [OK]{_RESET}" if ok else f"{_RED}{name} [FAIL]{_RESET}"
                    for name, ok in self.providers_tried
                )
                lines.append(_kv("Fallback Chain", tried_str))

        # ── Step 9: Final Summary  (Fix 1: was also "Step 8") ───────────────
        lines.append(_section("Step 9 | [DONE]", "RESPONSE ASSEMBLED", total_ms))
        if self.from_memory:
            lines.append(_kv("Source", f"{_GREEN}[CACHED] From semantic cache{_RESET}"))
        else:
            lines.append(_kv("Source", "Fresh LLM generation"))
        lines.append(_kv("Response Length", f"{self.response_length} characters" if self.response_length else None))
        lines.append(_kv("Sources Cited", f"{self.unique_sources} unique documents" if self.unique_sources is not None else None))
        lines.append(_kv("Total Time", f"{_BOLD}{total_ms:.1f}ms{_RESET}"))

        # ── Footer ───────────────────────────────────────────────────────────
        lines.append("")
        lines.append(_bar())
        lines.append("")

        _safe_print("\n".join(lines))