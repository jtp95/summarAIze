import feedparser    
import json
import os
import subprocess
import socket
import json
import time
import streamlit as st
import datetime
import fitz
import requests

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

#==================== PDFs ====================#

def get_pdf_path(paper, project):
    folder = os.path.join("projects", project, "pdfs")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, f"{paper['id'].replace('/', '_')}.pdf")

def get_cache_path(paper, project):
    folder = os.path.join("projects", project, "cache")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, f"{paper['id'].replace('/', '_')}.json")

def download_pdf(paper, project):
    pdf_url = None

    # 1. Try existing links (e.g., from arXiv metadata)
    for link in paper.get("links", []):
        if isinstance(link, dict) and link.get("type") == "application/pdf":
            pdf_url = link["href"]
            break

    # 2. Try fallback: build PDF URL manually if it's an arXiv page
    if "arxiv.org" in paper.get("link", ""):
        arxiv_path = paper["link"].split("arxiv.org/abs/")[-1] 
        pdf_url = f"https://arxiv.org/pdf/{arxiv_path}.pdf"

    # 3. Try direct .pdf link if available
    if not pdf_url and paper.get("link", "").endswith(".pdf"):
        pdf_url = paper["link"]

    if not pdf_url:
        raise ValueError(f"PDF link not found for paper: {paper.get('title', 'Unknown')}")

    # Download PDF to local project path
    pdf_path = get_pdf_path(paper, project)
    if not os.path.exists(pdf_path):
        r = requests.get(pdf_url)
        if r.status_code == 200:
            with open(pdf_path, "wb") as f:
                f.write(r.content)
        else:
            raise ValueError(f"Failed to fetch PDF from {pdf_url}")

    return pdf_path


def extract_and_cache_pdf_text(paper, project):
    cache_path = get_cache_path(paper, project)
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            return json.load(f)

    pdf_path = download_pdf(paper, project)
    doc = fitz.open(pdf_path)

    text_by_page = {}
    for i, page in enumerate(doc):
        text_by_page[str(i + 1)] = page.get_text()

    with open(cache_path, "w") as f:
        json.dump(text_by_page, f)

    return text_by_page


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
            "id": arxiv_id.split('v')[0],
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
        
def delete_paper_by_id(paper_id, state_key="papers"):
    papers = st.session_state.get(state_key, [])
    updated = [p for p in papers if p.get("id") != paper_id]
    st.session_state[state_key] = updated
    return updated

def get_next_citation_id(papers):
    used_ids = sorted(p.get("citation_id") for p in papers if "citation_id" in p)
    for i in range(1, len(used_ids) + 2):  # +2 so we can go one past max
        if i not in used_ids:
            return i

def add_paper_to_session(paper):
    existing_ids = [p["id"] for p in st.session_state.papers]
    if paper["id"] in existing_ids:
        return "duplicate"

    # Assign next citation ID
    paper["citation_id"] = get_next_citation_id(st.session_state.papers)
    st.session_state.papers.append(paper)
    save_papers(st.session_state.papers, st.session_state.current_project)
    return "added"

def detect_citation_gaps(papers):
    ids = sorted(p["citation_id"] for p in papers if "citation_id" in p)
    expected = list(range(1, len(ids) + 1))
    if ids != expected:
        st.warning("`Citation IDs have gaps. These will be reused in future additions.`")

#==================== Llamma Query ====================#
def run_llama_prompt(prompt, model="llama3"):
    try:
        result = subprocess.run(
            ["ollama", "run", model],  # system prompt reset
            input=prompt.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.stdout.decode().strip()
    except Exception as e:
        return f"Error: {e}"

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

#==================== Designs ====================#

def button_setup():
    button_style = """
        <style>
        .stButton > button {
            width: 100% !important;
            min-width: 80px;
            max-width: 100px;
        }
        </style>
    """

    st.markdown(button_style, unsafe_allow_html=True)
    
#==================== Citation ====================#
    
def generate_apa_citation(paper):
    try:
        authors = paper["authors"].split(", ")
        if len(authors) > 1:
            author_str = ", ".join(authors[:-1]) + f", & {authors[-1]}"
        else:
            author_str = authors[0]

        year = datetime.datetime.strptime(paper["published"], "%Y-%m-%dT%H:%M:%SZ").year
        title = paper["title"].rstrip(".")
        link = paper["link"]

        return f"{author_str} ({year}). *{title}*. arXiv. {link}"
    except Exception as e:
        return "Failed to generate citation"