import feedparser    
import json
import os
import subprocess
import socket
import json
import time

OLLAMA_MODEL = "llama3"
SAVE_FILE = "saved_papers.json"
PROJECTS_DIR = "projects"

#==================== Projects ====================#

def get_project_path(project_name):
    return os.path.join(PROJECTS_DIR, project_name)

def load_project_config(project_name):
    path = os.path.join(get_project_path(project_name), "project_config.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {"title": "", "description": "", "keywords": []}

def save_project_config(project_name, config):
    path = os.path.join(get_project_path(project_name), "project_config.json")
    with open(path, "w") as f:
        json.dump(config, f, indent=2)

def list_projects():
    if not os.path.exists(PROJECTS_DIR):
        os.makedirs(PROJECTS_DIR)
    return sorted([
        d for d in os.listdir(PROJECTS_DIR)
        if os.path.isdir(os.path.join(PROJECTS_DIR, d))
    ])
    
def load_project_config(project_name):
    path = os.path.join(get_project_path(project_name), "project_config.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {"title": "", "description": "", "keywords": []}

def save_project_config(project_name, config):
    path = os.path.join(get_project_path(project_name), "project_config.json")
    with open(path, "w") as f:
        json.dump(config, f, indent=2)

def rename_project_folder(old_name, new_name):
    old_path = get_project_path(old_name)
    new_path = get_project_path(new_name)
    if os.path.exists(old_path) and not os.path.exists(new_path):
        os.rename(old_path, new_path)
        return True
    return False


#==================== Paper ====================#

def fetch_arxiv_metadata(url):
    try:
        arxiv_id = url.strip().split("/")[-1]
        api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
        feed = feedparser.parse(api_url)
        entry = feed.entries[0]

        # Clean title and summary
        title = entry.title.replace("\n", " ").strip()
        summary = entry.summary.replace("\n", " ").strip()

        return {
            "id": arxiv_id,
            "title": title,
            "authors": ", ".join(author.name for author in entry.authors),
            "summary": summary,
            "published": entry.published,
            "link": entry.link
        }
    except Exception as e:
        print("Error:", e)
        return None

def format_authors(author_string):
    authors = [name.strip() for name in author_string.split(",")]
    if len(authors) <= 2:
        return ", ".join(authors)
    else:
        return ", ".join(authors[:2]) + ", et al."

def load_saved_papers(project_name):
    path = os.path.join(get_project_path(project_name), SAVE_FILE)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

def save_papers(papers, project_name):
    os.makedirs(get_project_path(project_name), exist_ok=True)
    path = os.path.join(get_project_path(project_name), "saved_papers.json")
    with open(path, "w") as f:
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