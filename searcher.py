# searcher.py

import re
from typing import List, Dict
from utils import extract_and_cache_pdf_text, run_llama_prompt
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")


def find_relevant_chunks(query: str, papers: List[dict], project: str, top_k: int = 3):
    query_vec = model.encode(query)
    candidates = []

    for paper in papers:
        pages = extract_and_cache_pdf_text(paper, project)
        for page_num, text in pages.items():
            chunks = [chunk.strip() for chunk in text.split("\n\n") if len(chunk.strip()) > 50]
            for chunk in chunks:
                chunk_vec = model.encode(chunk)
                score = cosine_similarity([query_vec], [chunk_vec])[0][0]
                candidates.append({
                    "score": score,
                    "chunk": chunk,
                    "paper": paper,
                    "page": page_num
                })

    top_chunks = sorted(candidates, key=lambda x: x["score"], reverse=True)[:top_k]
    return top_chunks


def llama_extract_answer(query: str, chunk: str, paper: dict, page: int):
    prompt = f"""
You are an academic research assistant. Given a question and a passage from a paper,
extract the exact sentence(s) from the passage that best answer the question.
If no answer is found in the passage, reply: "Not found."

Question:
{query}

Paper: {paper['title']} (Page {page})

Passage:
{chunk}

Answer:
"""
    response = run_llama_prompt(prompt)
    return response.strip()


def search_with_semantic_filter(query: str, papers: List[dict], project: str, top_k: int = 3):
    chunks = find_relevant_chunks(query, papers, project, top_k)
    results = []
    for c in chunks:
        answer = llama_extract_answer(query, c["chunk"], c["paper"], c["page"])
        results.append({
            "answer": answer,
            "chunk": c["chunk"],
            "paper": c["paper"],
            "page": c["page"],
            "score": c["score"]
        })
    return results