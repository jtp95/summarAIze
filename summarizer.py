import os
import json
from utils import *

SUMMARY_FILE = "summary_cache.json"

#==================== Summaries ====================#
def load_summary_cache(project_name):
    path = os.path.join(get_project_path(project_name), SUMMARY_FILE)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

def save_summary_cache(cache, project_name):
    os.makedirs(get_project_path(project_name), exist_ok=True)
    path = os.path.join(get_project_path(project_name), "summary_cache.json")
    with open(path, "w") as f:
        json.dump(cache, f, indent=2)


def summarize_paper(paper_id, abstract, cache, project_name):
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
    save_summary_cache(cache, project_name)
    return cache[paper_id]