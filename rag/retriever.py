"""
IMS AstroBot — RAG Retriever
Performs semantic search against ChromaDB to find relevant document chunks.
"""

from ingestion.embedder import get_collection, generate_embeddings
from config import TOP_K_RESULTS


def retrieve_context(query: str, top_k: int = TOP_K_RESULTS) -> list[dict]:
    """
    Retrieve the most relevant document chunks for a given query.
    
    Args:
        query: The user's question
        top_k: Number of results to return
    
    Returns:
        List of dicts with keys: text, source, heading, score
    """
    collection = get_collection()

    if collection.count() == 0:
        return []

    # Generate query embedding
    query_embedding = generate_embeddings([query])[0]

    # Search ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    # Format results
    context_chunks = []
    if results and results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else 0

            # ChromaDB cosine distance: 0 = identical, 2 = opposite
            # Convert to similarity score (1 = identical, 0 = orthogonal)
            similarity = 1 - (distance / 2)

            context_chunks.append({
                "text": doc,
                "source": metadata.get("source", "Unknown"),
                "heading": metadata.get("heading", ""),
                "score": round(similarity, 4),
                "doc_id": metadata.get("doc_id", ""),
            })

    return context_chunks


def format_context_for_llm(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a context string for the LLM prompt.
    """
    if not chunks:
        return "No relevant documents found in the knowledge base."

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source_info = f"[Source: {chunk['source']}"
        if chunk.get("heading"):
            source_info += f" > {chunk['heading']}"
        source_info += f" | Relevance: {chunk['score']:.0%}]"

        context_parts.append(f"--- Context {i} {source_info} ---\n{chunk['text']}")

    return "\n\n".join(context_parts)


def get_source_citations(chunks: list[dict]) -> str:
    """Format source citations for display."""
    if not chunks:
        return ""

    seen = set()
    citations = []
    for chunk in chunks:
        source = chunk.get("source", "Unknown")
        if source not in seen:
            seen.add(source)
            heading = chunk.get("heading", "")
            score = chunk.get("score", 0)
            citation = f"📄 **{source}**"
            if heading:
                citation += f" — {heading}"
            citation += f" ({score:.0%} match)"
            citations.append(citation)

    return "\n".join(citations)
