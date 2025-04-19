import feedparser    
import json
import os

SAVE_FILE = "saved_papers.json"

# Extract the arXiv ID from the URL
def fetch_arxiv_metadata(url):
    try:
        arxiv_id = url.strip().split("/")[-1]
        api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
        feed = feedparser.parse(api_url)
        entry = feed.entries[0]
        return {
            "id": arxiv_id, 
            "title": entry.title,
            "authors": ", ".join(author.name for author in entry.authors),
            "summary": entry.summary,
            "published": entry.published,
            "link": entry.link
        }
    except Exception as e:
        print("Error: ", e)
        return None
    
def format_authors(author_string):
    authors = [name.strip() for name in author_string.split(",")]
    if len(authors) <= 2:
        return ", ".join(authors)
    else:
        return ", ".join(authors[:2]) + ", et al."

def load_saved_papers():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return []

def save_papers(papers):
    with open(SAVE_FILE, "w") as f:
        json.dump(papers, f, indent=2)
