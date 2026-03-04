import os
import re
import math
import uuid
from typing import List, Dict, Any, Tuple

import chromadb
from chromadb.config import Settings as ChromaSettings


def _normalize(vec: List[float]) -> List[float]:
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def _hash_embed(text: str, dim: int = 384) -> List[float]:
    """
    Very light local embedding (hashing trick). No external models. No cost.
    Good enough for demo + academic pipeline; later you can swap embeddings.
    """
    vec = [0.0] * dim
    tokens = re.findall(r"[A-Za-z0-9_]+", (text or "").lower())
    for t in tokens:
        idx = hash(t) % dim
        vec[idx] += 1.0
    return _normalize(vec)


def _chunk_text(text: str, chunk_words: int = 220, overlap_words: int = 40) -> List[str]:
    words = (text or "").split()
    if not words:
        return []
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i + chunk_words]
        chunks.append(" ".join(chunk))
        i += max(1, chunk_words - overlap_words)
    return chunks


def _read_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()

    # TXT/MD
    if ext in [".txt", ".md", ".csv", ".json"]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    # PDF (optional)
    if ext == ".pdf":
        try:
            import PyPDF2
            text = []
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for p in reader.pages:
                    text.append(p.extract_text() or "")
            return "\n".join(text)
        except Exception:
            return ""

    # DOCX (optional)
    if ext == ".docx":
        try:
            import docx
            d = docx.Document(path)
            return "\n".join([p.text for p in d.paragraphs])
        except Exception:
            return ""

    return ""


class VectorStore:
    def __init__(self, persist_dir: str, collection_name: str = "docs"):
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_files(self, file_paths: List[str]) -> int:
        """
        Reads files, chunks them, stores chunks in Chroma.
        Returns number of chunks added.
        """
        ids = []
        docs = []
        metas = []
        embeddings = []

        for fp in file_paths:
            text = _read_file(fp)
            if not text.strip():
                continue

            chunks = _chunk_text(text)
            for j, ch in enumerate(chunks):
                cid = str(uuid.uuid4())
                ids.append(cid)
                docs.append(ch)
                metas.append({"source_file": os.path.basename(fp), "chunk_index": j})
                embeddings.append(_hash_embed(ch))

        if ids:
            self.collection.add(
                ids=ids,
                documents=docs,
                metadatas=metas,
                embeddings=embeddings
            )
        return len(ids)

    def query(self, query_text: str, top_k: int = 4) -> List[Dict[str, Any]]:
        emb = _hash_embed(query_text)
        res = self.collection.query(
            query_embeddings=[emb],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        out = []
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]

        for d, m, dist in zip(docs, metas, dists):
            out.append({"text": d, "meta": m, "distance": dist})
        return out


def build_context_snippet(hits: List[Dict[str, Any]], max_chars: int = 2200) -> str:
    """
    Create compact context block for RAG. Keeps token usage low.
    """
    parts = []
    total = 0
    for h in hits:
        src = h["meta"].get("source_file", "file")
        idx = h["meta"].get("chunk_index", 0)
        chunk = h["text"].strip()
        block = f"[{src} | chunk {idx}]\n{chunk}\n"
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    return "\n".join(parts).strip()