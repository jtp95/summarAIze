import os
import json
from utils import *

SUMMARY_FILE = "summary_cache.json"

#==================== Summaries ====================#
def load_summary_cache():
    if os.path.exists(SUMMARY_FILE):
        try:
            with open(SUMMARY_FILE, "r") as f:
                cache = json.load(f)
                if isinstance(cache, dict):
                    return cache
        except Exception as e:
            print("Failed to load summary cache:", e)
    return {}

def save_summary_cache(cache):
    with open(SUMMARY_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def summarize_paper(paper_id, abstract, cache):
    if paper_id in cache:
        return cache[paper_id]

    prompt = f"Summarize this research abstract in 1-2 concise sentences and give 3-5 key terms:\n\n{abstract}\n\nReturn only the summary followed by keywords in this format:\nSummary: ...\nKeywords: ..."

    result = run_llama_prompt(prompt)
    lines = result.strip().split("\n")

    summary_line = next((l for l in lines if l.lower().startswith("summary:")), "Summary: ...")
    keywords_line = next((l for l in lines if l.lower().startswith("keywords:")), "Keywords: ...")

    summary = summary_line.replace("Summary:", "").strip()
    keywords = keywords_line.replace("Keywords:", "").strip()

    cache[paper_id] = {"summary": summary, "keywords": keywords}
    save_summary_cache(cache)
    return cache[paper_id]