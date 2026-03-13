---
name: rag-pipeline
description: Use this skill when building retrieval-augmented generation (RAG) systems — document ingestion, chunking, embedding, vector search, and grounded responses.
source: https://github.com/anthropics/anthropic-cookbook/tree/main/third_party/Pinecone
---

# RAG Pipeline

## Overview

Retrieval-Augmented Generation (RAG) pipeline: ingest documents, chunk them, generate embeddings, store in a vector DB, and retrieve relevant context for Claude to answer questions grounded in your data.

## Document Ingestion

```python
import anthropic
from pathlib import Path

client = anthropic.Anthropic()

def chunk_document(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks

def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """Generate embeddings using a compatible embedding model."""
    # Use OpenAI, Cohere, or local embeddings alongside Claude
    import openai
    oe = openai.OpenAI()
    response = oe.embeddings.create(
        model="text-embedding-3-small",
        input=chunks
    )
    return [e.embedding for e in response.data]
```

## Vector Storage (Chroma)

```python
import chromadb

def setup_vector_db(collection_name: str = "documents"):
    client = chromadb.Client()
    return client.get_or_create_collection(collection_name)

def index_document(collection, doc_path: str) -> int:
    text = Path(doc_path).read_text()
    chunks = chunk_document(text)
    embeddings = embed_chunks(chunks)

    ids = [f"{doc_path}_{i}" for i in range(len(chunks))]
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=[{"source": doc_path, "chunk": i} for i in range(len(chunks))]
    )
    return len(chunks)
```

## RAG Query

```python
def rag_query(collection, question: str, n_results: int = 5) -> str:
    # Embed the question
    query_embedding = embed_chunks([question])[0]

    # Retrieve relevant chunks
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    context = "\n\n".join(results["documents"][0])

    # Ask Claude with retrieved context
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system="""Answer questions based on the provided context.
        If the answer isn't in the context, say so — don't hallucinate.""",
        messages=[{
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}"
        }]
    )
    return response.content[0].text
```

## Quick Start

```python
collection = setup_vector_db("my-docs")

# Index your docs
for doc in Path("docs/").glob("**/*.md"):
    n = index_document(collection, str(doc))
    print(f"Indexed {doc}: {n} chunks")

# Query
answer = rag_query(collection, "How do I configure authentication?")
print(answer)
```

## Quick Reference

| Step | Function | Notes |
|------|----------|-------|
| Chunk | `chunk_document()` | 500 words, 50 overlap |
| Embed | `embed_chunks()` | any embedding model |
| Index | `index_document()` | Chroma/Pinecone/Weaviate |
| Query | `rag_query()` | retrieve + generate |
