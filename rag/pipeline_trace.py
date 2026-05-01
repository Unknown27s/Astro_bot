"""
IMS AstroBot — Pipeline Trace (Terminal Explainability)
Prints a beautiful, step-by-step trace of the RAG pipeline to the server terminal.
Designed for jury demos: shows exactly what happens internally when a query is processed.
"""

import sys
import io
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── ANSI Color Codes (supported in Windows 10+ terminals) ──
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_CYAN = "\033[96m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_MAGENTA = "\033[95m"
_BLUE = "\033[94m"
_RED = "\033[91m"
_WHITE = "\033[97m"
_BG_DARK = "\033[48;5;235m"
_ORANGE = "\033[38;5;208m"


def _bar(width: int = 70, char: str = "=") -> str:
    return f"{_DIM}{_CYAN}{char * width}{_RESET}"


def _section(icon: str, title: str, time_ms: float = None) -> str:
    time_str = f"  {_DIM}({time_ms:.1f}ms){_RESET}" if time_ms is not None else ""
    return f"\n{_BOLD}{_CYAN}{icon} {title}{_RESET}{time_str}"


def _kv(key: str, value, indent: int = 4) -> str:
    pad = " " * indent
    return f"{pad}{_DIM}{key}:{_RESET} {_WHITE}{value}{_RESET}"


def _chunk_block(rank: int, source: str, heading: str, similarity: float, text_preview: str,
                 distance: Optional[float] = None) -> str:
    """Format a single retrieved chunk for terminal display."""
    # Color-code similarity: green(>90%), yellow(>75%), red(<75%)
    if similarity >= 0.90:
        score_color = _GREEN
        bar_fill = "####################"
    elif similarity >= 0.75:
        score_color = _YELLOW
        bar_fill = "#############-------"
    else:
        score_color = _RED
        bar_fill = "########------------"

    lines = [
        f"      {_BOLD}#{rank}{_RESET} {_DIM}------------------------------------------{_RESET}",
        f"      {_DIM}Source:{_RESET}     {_MAGENTA}{source}{_RESET}",
    ]
    if heading:
        lines.append(f"      {_DIM}Section:{_RESET}    {heading}")
    if distance is not None:
        lines.append(
            f"      {_DIM}Distance:{_RESET}   {distance:.4f} {_DIM}(similarity = 1 - distance/2){_RESET}"
        )
    lines.append(f"      {_DIM}Similarity:{_RESET} {score_color}{similarity:.1%}{_RESET}  {_DIM}[{bar_fill}]{_RESET}")
    # Truncate preview text
    preview = text_preview[:150].replace('\n', ' | ')
    if len(text_preview) > 150:
        preview += "..."
    lines.append(f"      {_DIM}Text:{_RESET}       {_DIM}\"{preview}\"{_RESET}")
    return "\n".join(lines)


def _safe_print(text: str):
    """Print text safely to terminal, handling Windows encoding issues."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback: write to stdout with utf-8 encoding, replacing bad chars
        safe_text = text.encode('ascii', errors='replace').decode('ascii')
        print(safe_text)


class PipelineTrace:
    """
    Collects step-by-step info during a RAG query and prints it to the terminal.
    
    Usage:
        trace = PipelineTrace(query, username)
        # ... pass trace through pipeline steps, each step calls trace methods ...
        trace.print_summary()
    """

    def __init__(self, query: str, username: str = "unknown"):
        self.query = query
        self.username = username
        self.start_time = time.time()
        self._steps = []

        # Data collected during pipeline
        self.embedding_model = None
        self.embedding_dims = None
        self.embedding_preview = None
        self.embedding_time_ms = None

        self.memory_checked = False
        self.memory_hit = False
        self.memory_best_similarity = None
        self.memory_threshold = None
        self.memory_time_ms = None

        self.collection_size = None
        self.top_k = None
        self.search_time_ms = None
        self.retrieved_chunks = []   # list of dicts
        self.route_mode = None
        self.route_confidence = None
        self.route_reason = None

        self.context_char_count = None
        self.system_prompt_preview = None
        self.user_message_preview = None

        self.provider_used = None
        self.model_used = None
        self.temperature = None
        self.max_tokens = None
        self.generation_time_ms = None
        self.providers_tried = []    # list of (name, success: bool)

        self.response_length = None
        self.unique_sources = None
        self.from_memory = False

        self.expanded_queries = []
        self.query_expansion_checked = False
        self.query_expansion_enabled = False
        self.query_expansion_reason = None

    def record_embedding(self, model: str, dims: int, preview: list, time_ms: float):
        """Record query embedding step."""
        self.embedding_model = model
        self.embedding_dims = dims
        self.embedding_preview = preview[:5]  # first 5 values
        self.embedding_time_ms = time_ms

    def record_expansion(self, enabled: bool, expansions: list = None, reason: str = None):
        """Record query expansion step."""
        self.query_expansion_checked = True
        self.query_expansion_enabled = enabled
        self.query_expansion_reason = reason
        if expansions:
            self.expanded_queries = expansions

    def record_memory_check(self, hit: bool, best_similarity: float = None,
                            threshold: float = None, time_ms: float = None):
        """Record semantic memory cache check."""
        self.memory_checked = True
        self.memory_hit = hit
        self.memory_best_similarity = best_similarity
        self.memory_threshold = threshold
        self.memory_time_ms = time_ms

    def record_search(self, collection_size: int, top_k: int, time_ms: float):
        """Record ChromaDB vector search step."""
        self.collection_size = collection_size
        self.top_k = top_k
        self.search_time_ms = time_ms

    def record_route(self, route_mode: str, confidence: float = None, reason: str = None):
        """Record the query routing decision."""
        self.route_mode = route_mode
        self.route_confidence = confidence
        self.route_reason = reason

    def record_chunk(self, rank: int, source: str, heading: str, similarity: float,
                     text: str, distance: float = None):
        """Record a single retrieved chunk."""
        self.retrieved_chunks.append({
            "rank": rank,
            "source": source,
            "heading": heading,
            "similarity": similarity,
            "distance": distance,
            "text": text,
        })

    def record_prompt(self, system_prompt: str, user_message: str, context_chars: int):
        """Record LLM prompt construction."""
        self.system_prompt_preview = system_prompt[:100]
        self.user_message_preview = user_message[:150]
        self.context_char_count = context_chars

    def record_generation(self, provider: str, model: str, temperature: float,
                          max_tokens: int, time_ms: float, providers_tried: list = None):
        """Record LLM generation step."""
        self.provider_used = provider
        self.model_used = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.generation_time_ms = time_ms
        if providers_tried:
            self.providers_tried = providers_tried

    def record_response(self, response_length: int, unique_sources: int, from_memory: bool = False):
        """Record final response assembly."""
        self.response_length = response_length
        self.unique_sources = unique_sources
        self.from_memory = from_memory

    def print_summary(self):
        """Print the complete pipeline trace to terminal."""
        total_ms = (time.time() - self.start_time) * 1000
        lines = []

        # ── Header ──
        lines.append("")
        lines.append(_bar())
        lines.append(f"{_BOLD}{_CYAN}  [TRACE] RAG PIPELINE TRACE{_RESET}")
        lines.append(_bar())

        # ── Step 1: Query Received ──
        lines.append(_section("Step 1 | [QUERY]", "QUERY RECEIVED"))
        lines.append(_kv("User", self.username))
        lines.append(_kv("Query", f'"{self.query}"'))

        # ── Step 2: Query Embedding ──
        if self.embedding_model:
            lines.append(_section("Step 2 | [EMBED]", "QUERY EMBEDDING", self.embedding_time_ms))
            lines.append(_kv("Model", self.embedding_model))
            lines.append(_kv("Dimensions", f"{self.embedding_dims}-dimensional vector"))
            if self.embedding_preview:
                preview_str = ", ".join(f"{v:.4f}" for v in self.embedding_preview)
                lines.append(_kv("Vector Preview", f"[{preview_str}, ...]"))

        # ── Step 3: Query Routing ──
        if self.route_mode:
            lines.append(_section("Step 3 | [ROUTE]", "QUERY ROUTING"))
            lines.append(_kv("Mode", self.route_mode))
            if self.route_confidence is not None:
                lines.append(_kv("Confidence", f"{self.route_confidence:.0%}"))
            if self.route_reason:
                lines.append(_kv("Reason", self.route_reason))

        # ── Step 3b: Query Expansion ──
        if self.query_expansion_checked:
            lines.append(_section("Step 3b| [EXPAND]", "QUERY EXPANSION"))
            if self.query_expansion_reason:
                lines.append(_kv("Reason", self.query_expansion_reason))
            if not self.query_expansion_enabled:
                lines.append(_kv("Status", f"{_DIM}Disabled in config (or LLM skipped){_RESET}"))
            elif self.expanded_queries:
                lines.append(_kv("Status", f"{_GREEN}Enabled - Generated {len(self.expanded_queries)} variants{_RESET}"))
                for i, eq in enumerate(self.expanded_queries, 1):
                    lines.append(_kv(f"Variant {i}", f'"{_MAGENTA}{eq}{_RESET}"'))
            else:
                lines.append(_kv("Status", f"{_YELLOW}Enabled but LLM failed to generate variants{_RESET}"))

        # ── Step 4: Memory Check ──
        if self.memory_checked:
            lines.append(_section("Step 4 | [CACHE]", "SEMANTIC MEMORY CHECK", self.memory_time_ms))
            if self.memory_hit:
                lines.append(_kv("Result", f"{_GREEN}[HIT] CACHE HIT{_RESET}"))
                lines.append(_kv("Action", "Returning cached response -- skipping LLM"))
            else:
                sim_str = f"{self.memory_best_similarity:.3f}" if self.memory_best_similarity else "N/A"
                thr_str = f"{self.memory_threshold:.2f}" if self.memory_threshold else "N/A"
                lines.append(_kv("Result", f"{_YELLOW}[MISS] CACHE MISS{_RESET}"))
                lines.append(_kv("Best Match", f"{sim_str} similarity (threshold: {thr_str})"))
                lines.append(_kv("Action", "Proceeding to LLM generation"))

        # ── Step 5: ChromaDB Vector Search ──
        if self.collection_size is not None:
            lines.append(_section("Step 5 | [SEARCH]", "CHROMADB VECTOR SEARCH", self.search_time_ms))
            lines.append(_kv("Collection Size", f"{self.collection_size:,} vectors stored"))
            lines.append(_kv("Search Strategy", f"Cosine similarity, top-{self.top_k}"))
            lines.append(_kv("Chunks Found", f"{len(self.retrieved_chunks)} results"))

        # ── Step 6: Retrieved Chunks ──
        if self.retrieved_chunks:
            lines.append(_section("Step 6 | [CHUNKS]", "RETRIEVED CHUNKS (Ranked by Relevance)"))
            for chunk in self.retrieved_chunks:
                lines.append(_chunk_block(
                    rank=chunk["rank"],
                    source=chunk["source"],
                    heading=chunk["heading"],
                    similarity=chunk["similarity"],
                    text_preview=chunk["text"],
                    distance=chunk.get("distance"),
                ))

        # ── Step 7: Prompt Construction ──
        if self.context_char_count is not None:
            lines.append(_section("Step 7 | [PROMPT]", "LLM PROMPT CONSTRUCTION"))
            lines.append(_kv("System Prompt", f'"{self.system_prompt_preview}..."'))
            lines.append(_kv("Context Size", f"{self.context_char_count:,} characters from {len(self.retrieved_chunks)} chunks"))
            lines.append(_kv("User Message", f'"{self.user_message_preview}..."'))

        # ── Step 8: LLM Generation ──
        if self.provider_used:
            lines.append(_section("Step 8 | [LLM]", "LLM GENERATION", self.generation_time_ms))
            lines.append(_kv("Provider", f"{_GREEN}{self.provider_used}{_RESET}"))
            lines.append(_kv("Model", self.model_used))
            lines.append(_kv("Temperature", self.temperature))
            lines.append(_kv("Max Tokens", self.max_tokens))
            if self.providers_tried:
                tried_str = " -> ".join(
                    f"{_GREEN}{name} [OK]{_RESET}" if ok else f"{_RED}{name} [FAIL]{_RESET}"
                    for name, ok in self.providers_tried
                )
                lines.append(_kv("Fallback Chain", tried_str))

        # ── Step 8: Final Summary ──
        lines.append(_section("Step 8 | [DONE]", "RESPONSE ASSEMBLED", total_ms))
        if self.from_memory:
            lines.append(_kv("Source", f"{_GREEN}[CACHED] From semantic cache{_RESET}"))
        else:
            lines.append(_kv("Source", "Fresh LLM generation"))
        if self.response_length:
            lines.append(_kv("Response Length", f"{self.response_length} characters"))
        if self.unique_sources is not None:
            lines.append(_kv("Sources Cited", f"{self.unique_sources} unique documents"))
        lines.append(_kv("Total Time", f"{_BOLD}{total_ms:.1f}ms{_RESET}"))

        # ── Footer ──
        lines.append("")
        lines.append(_bar())
        lines.append("")

        # Print all at once (safe for Windows terminals)
        output = "\n".join(lines)
        _safe_print(output)
