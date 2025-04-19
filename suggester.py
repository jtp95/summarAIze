import requests
import feedparser
from utils import run_llama_prompt
from duckduckgo_search import DDGS
import hashlib
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
}


def generate_search_queries_from_project(config):
    title = config.get("title", "")
    desc = config.get("description", "")
    keywords = ", ".join(config.get("keywords", []))

    prompt = f"""
    You are helping find academic research papers for a project.
    Project Title: {title}
    Project Description: {desc}
    Keywords: {keywords}

    Based on this information, generate 3 to 5 concise search queries that could be used to find relevant papers on arXiv or the web.
    Only output the queries, one per line, no numbering.
    """

    output = run_llama_prompt(prompt)
    queries = [line.strip() for line in output.splitlines() if line.strip()]
    return queries[:5]


def fetch_arxiv_papers(query, max_results=5):
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }

    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        return []

    feed = feedparser.parse(response.content)
    results = []
    for entry in feed.entries:
        results.append({
            "id": entry.id.split("/")[-1].split("v")[0],
            "title": entry.title.replace("\n", " ").strip(),
            "summary": entry.summary.replace("\n", " ").strip(),
            "authors": ", ".join(a.name for a in entry.authors),
            "published": entry.published,
            "link": entry.link,
            "source": "arXiv"
        })
    
    return results

def fetch_web_papers(query, max_results=5):
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(f"{query} filetype:pdf", max_results=max_results * 2):
            href = r.get("href")
            if href and href.endswith(".pdf"):
                results.append({
                    "title": r["title"] or href.split("/")[-1].replace(".pdf", ""),
                    "summary": r.get("body", "(PDF file, abstract unavailable)"),
                    "authors": "?",
                    "published": "?",
                    "link": href,
                    "source": "web"
                })
            if len(results) >= max_results:
                break
    return results



def is_semantically_relevant(project_config, paper):
    prompt = f"""
    Project: {project_config['title']}
    Description: {project_config['description']}

    Candidate Paper Title: {paper['title']}
    Abstract: {paper['summary']}

    Is this paper directly relevant to introducing fundamental quantum physics (not quantum computing or algorithmic approaches)? Only answer YES or NO.
    """
    result = run_llama_prompt(prompt).lower()
    return "yes" in result


def clean_text(text):
    return re.sub(r"\s+", " ", text.strip())

def generate_live_suggestions(config):
    queries = generate_search_queries_from_project(config)
    print("Queries:", queries)

    suggested = []
    seen_ids = set()

    for query in queries:
        arxiv = fetch_arxiv_papers(query)
        web = [] #fetch_web_papers(query) # Disabled for now
        papers = arxiv + web

        for paper in papers:
            # Clean up
            paper["title"] = clean_text(paper.get("title", "Untitled"))
            paper["summary"] = clean_text(paper.get("summary", ""))
            paper["authors"] = clean_text(paper.get("authors", "?"))

            # Generate fallback ID from URL or title hash
            pid = paper.get("id") or paper.get("link") or hashlib.md5(paper["title"].encode()).hexdigest()
            paper["id"] = pid

            if pid in seen_ids:
                continue

            if is_semantically_relevant(config, paper):
                suggested.append(paper)
                seen_ids.add(pid)

    return suggested
