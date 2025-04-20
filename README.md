## SummarAIze

A desktop research assistant that helps you collect, summarize, and search academic papers.

---

## Motivation

Academic research is overwhelming, especially when collecting and processing dozens of papers. SummarAIze is built to solve this by acting as a local research companion. It helps you:

- Organize papers by project
- Automatically summarize each paper
- Suggest new related sources
- Extract answers to research questions with citations
- Take personal notes for each paper

All processing is done locally, so your data and queries stay private.

---

## How LLaMA Is Used

SummarAIze uses a local LLaMA model (via [Ollama](https://ollama.com)) to:

- Generate a 1-sentence summary and keywords for each paper after it is loaded
- Select the best candidate papers for a given question and project information
- Answer research questions using selected papers

Unlike traditional retrieval methods that use embeddings, the app uses LLaMA directly for context-aware, text-based reasoning.

---

## Features

### Project Organization
- Create, rename, and delete research projects
- Save papers per project with metadata

### Paper Summarization
- 1-sentence summary and keyword extraction for quick reference
- Automatically generated using local LLaMA model

### Paper Search
- Ask a research question, and the app extracts exact answer sentences from papers
- Context is shown with source, page number, and match score

### Find Papers
- Suggests related sources using a secondary LLaMA query
- Accept or reject suggested papers

### Citation Management
- APA-style citation generator
- Assign and edit citation IDs for each paper

### Personal Notes
- Add and save private notes per paper for reflection or reminders

---

## Installation and Running

### 1. Clone the Repository

```bash
git clone https://github.com/jtp95/summaraize.git
cd summaraize
```

### 2. Create a Virtual Environment and Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Set Up Ollama for Local LLaMA Model

This app assumes you are using [Ollama](https://ollama.com/) to run your LLaMA model locally.

#### Install Ollama

Download from https://ollama.com/download and install for your platform.

#### Pull a Model

```bash
ollama pull llama3
```

Note that this program use llama3 model.


#### Run the Ollama Server

In a separate terminal:

```bash
ollama serve
```

This must be running before launching the app.

### 4. Run the App

```bash
streamlit run app.py
```

The app will open in your default browser. Select or create a project and start uploading papers.

---

## Notes
- All data (papers, notes, summaries) are stored locally under the `projects/` directory.
- Ollama requests are made via a Python wrapper to a local endpoint.
- Make sure the PDF text is extractable (not scanned images) for best results.

