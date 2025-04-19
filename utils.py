import feedparser    
import json
import os
import subprocess
import socket
import json
import time

OLLAMA_MODEL = "llama3"
SAVE_FILE = "saved_papers.json"

#==================== Paper ====================#
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
        try:
            with open(SAVE_FILE, "r") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except Exception as e:
            print("Error loading saved_papers.json:", e)
            return []
    return []


def save_papers(papers):
    with open(SAVE_FILE, "w") as f:
        json.dump(papers, f, indent=2)

#==================== Llamma Query ====================#
def run_llama_prompt(prompt, model="llama3"):
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.stdout.decode().strip()
    except Exception as e:
        return f"Error running LLaMA: {e}"

#==================== Ollamma Setup ====================#

def is_ollama_running(host="localhost", port=11434):
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False

def start_ollama():
    try:
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print("Failed to start Ollama:", e)
        return False

def is_model_pulled(model=OLLAMA_MODEL):
    try:
        result = subprocess.run(["ollama", "list", "--json"], stdout=subprocess.PIPE)
        models = json.loads(result.stdout.decode())
        return any(m["name"].startswith(model) for m in models)
    except Exception as e:
        print("Could not list Ollama models:", e)
        return False

def pull_model(model=OLLAMA_MODEL):
    try:
        subprocess.run(["ollama", "pull", model], check=True)
        return True
    except Exception as e:
        print("Failed to pull model:", e)
        return False

def ensure_ollama_and_model():
    # Start Ollama if not running
    if not is_ollama_running():
        start_ollama()
        time.sleep(3)
        if not is_ollama_running():
            return False, "Ollama could not be started."

    # Check and pull model
    if not is_model_pulled():
        print("Model not found. Pulling...")
        pull_model()
    
    return True, "Ollama and model are ready."