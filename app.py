import streamlit as st
from utils import *
from summarizer import *
from components import *
from suggester import *
import os
import sys
import types
import torch

# Patch to avoid torch.classes introspection error with Streamlit
if not hasattr(torch, "classes"):
    torch.classes = types.SimpleNamespace()
setattr(torch.classes, "__path__", [])


os.environ["TOKENIZERS_PARALLELISM"] = "false"

# === Session Setup ===
if "selected_paper" not in st.session_state:
    st.session_state.selected_paper = None

if "generating_summaries" not in st.session_state:
    st.session_state.generating_summaries = set()

if "project_selected" not in st.session_state:
    st.session_state.project_selected = False

if not st.session_state.project_selected:
    st.session_state.current_project = None
    st.session_state.papers = []


if "project_selected" not in st.session_state:
    st.session_state.project_selected = False

if "last_loaded_project" not in st.session_state:
    st.session_state.last_loaded_project = None

if "temp_suggestions" not in st.session_state:
    st.session_state.temp_suggestions = []

button_setup()

# === Project Selection ===
def clear_temp_suggestions():
    st.session_state.temp_suggestions = []

if not st.session_state.project_selected:
    render_logo()
    col1, col2 = st.columns([5,1])
    with col1:
        st.title("Select Project")
    
    project_list = list_projects()
    selected = st.selectbox("Choose a project:", options=project_list)
    
    with col2:
        st.markdown("<div style='margin-top: 2rem'></div>", unsafe_allow_html=True)
        if st.button("Select"):
            st.session_state.current_project = selected
            st.session_state.project_selected = True
            st.session_state.last_loaded_project = selected
            st.session_state.papers = load_saved_papers(selected)
            st.session_state.generating_summaries = set()
            st.session_state.selected_paper = None
            clear_temp_suggestions()
            st.rerun()

    st.divider()

    st.subheader("Create New Project")
    with st.form("create_project_form"):
        new_project = st.text_input("Project name")
        create = st.form_submit_button("Create")
        if create:
            if new_project and new_project not in project_list:
                os.makedirs(get_project_path(new_project), exist_ok=True)
                default_config = {
                    "title": new_project,
                    "description": "",
                    "keywords": []
                }
                save_project_config(new_project, default_config)
                st.success(f"Project '{new_project}' created!")
                st.session_state.current_project = new_project
                st.session_state.project_selected = True
                st.session_state.last_loaded_project = new_project
                clear_temp_suggestions()
                st.rerun()
            else:
                st.error("Project name invalid or already exists.")

    st.divider()
    
    st.subheader("Delete Existing Project")
    with st.form("delete_project_form"):
        to_delete = st.selectbox("Select project to delete", options=project_list)
        col1, col2 = st.columns([6,1])
        with col1:
            confirm = st.checkbox(f"Yes, delete permanently")
        with col2:
            delete = st.form_submit_button("Delete")
        if delete and confirm:
            import shutil
            shutil.rmtree(get_project_path(to_delete))
            st.success(f"Project '{to_delete}' deleted.")
            if st.session_state.current_project == to_delete:
                st.session_state.current_project = None
                st.session_state.project_selected = False
            st.rerun()

# === Project View ===
if st.session_state.project_selected and st.session_state.current_project:
    if "papers" not in st.session_state:
        st.session_state.papers = load_saved_papers(st.session_state.current_project)

    summary_cache = load_summary_cache(st.session_state.current_project)
    render_logo()

    # === Detail View ===
    if st.session_state.selected_paper:
        st.components.v1.html('''<script>var body = window.parent.document.querySelector(".main"); body.scrollTop = 0;</script>''')
        paper = st.session_state.selected_paper
        st.title(paper["title"])
        
        col1, col2 = st.columns([5,1])
        with col1:
            st.write(f"**Authors:** {paper['authors']}")
            st.write(f"**Published:** {paper['published']}")
        with col2:
            st.button("Back", on_click=lambda: st.session_state.update({"selected_paper": None}))
        
        st.divider()
        display_summary(paper, summary_cache)
        st.divider()
        st.write(f"**Abstract:** {paper['summary']}")
        st.markdown(f"[View on arXiv]({paper['link']})")
        
        st.divider()
        st.markdown("**Citation (APA)**")
        st.code(generate_apa_citation(paper), language="markdown")
        new_id = st.number_input(
            "Edit citation ID",
            min_value=1,
            value=paper["citation_id"],
            step=1,
            key="edit_citation_id"
        )

        if new_id != paper["citation_id"]:
            # Check for conflict
            if any(p["citation_id"] == new_id for p in st.session_state.papers if p["id"] != paper["id"]):
                st.warning(f"Citation ID [{new_id}] is already used.")
            else:
                # Update
                paper["citation_id"] = new_id
                save_papers(st.session_state.papers, st.session_state.current_project)
                st.success(f"Citation ID updated to [{new_id}]")
                st.rerun()
        
        st.button("Back ", on_click=lambda: st.session_state.update({"selected_paper": None}))

        st.stop()

    # === Main View ===
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"## Project: {st.session_state.current_project}")
    with col2:
        st.markdown("<div style='margin-top: 0.5rem'></div>", unsafe_allow_html=True)
        st.button("Exit", on_click=lambda: st.session_state.update({
            "project_selected": False,
            "current_project": None,
            "papers": [],
            "selected_paper": None
        }))
        
    config = load_project_config(st.session_state.current_project)

    with st.expander("Project Info", expanded=False):
        with st.form("project_metadata_form"):
            title = st.text_input("Project Title", value=config.get("title", ""))
            description = st.text_area("Project Description", value=config.get("description", ""))
            keywords = st.text_input("Keywords (comma-separated)", value=", ".join(config.get("keywords", [])))
            submitted = st.form_submit_button("Save")
            if submitted:
                new_title = title.strip()
                config["title"] = new_title
                config["description"] = description.strip()
                config["keywords"] = [k.strip() for k in keywords.split(",") if k.strip()]
                if new_title and new_title != st.session_state.current_project:
                    success = rename_project_folder(st.session_state.current_project, new_title)
                    if success:
                        st.session_state.current_project = new_title
                        save_project_config(new_title, config)
                        st.success(f"Project renamed to '{new_title}' and updated.")
                        st.rerun()
                    else:
                        st.warning("Could not rename project — it may already exist.")
                else:
                    save_project_config(st.session_state.current_project, config)
                    st.success("Project info updated.")
    
    tab_paper, tab_find, tab_add, tab_search = st.tabs(["Papers", "Find", "Add", "Search"])

    with tab_add:
        render_tab_add()

    with tab_find:
        render_tab_find()

    with tab_paper:
        with st.expander("APA Citations", expanded=False):
            for paper in sorted(st.session_state.papers, key=lambda p: p["citation_id"]):
                citation = generate_apa_citation(paper)
                st.markdown(f"**[{paper['citation_id']}]** {citation}")
            
        detect_citation_gaps(st.session_state.papers)
        render_tab_paper()
        
    with tab_search:
        render_tab_search()
        
    for paper in st.session_state.papers:
        pid = paper["id"]
        if pid in st.session_state.generating_summaries:
            if pid not in summary_cache:
                result = summarize_paper(pid, paper["summary"], summary_cache, st.session_state.current_project)
                summary_cache[pid] = result
                save_summary_cache(summary_cache, st.session_state.current_project)
            st.session_state.generating_summaries.remove(pid)
            st.rerun()
