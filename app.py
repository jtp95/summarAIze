import streamlit as st
from utils import *
from summarizer import *
from components import render_paper_card, render_logo, display_summary

# === Session Setup ===
if "selected_paper" not in st.session_state:
    st.session_state.selected_paper = None

if "generating_summaries" not in st.session_state:
    st.session_state.generating_summaries = set()

if "current_project" not in st.session_state:
    st.session_state.current_project = None

if "project_selected" not in st.session_state:
    st.session_state.project_selected = False

# === Project Selection ===
if not st.session_state.project_selected:
    render_logo()
    st.title("Select or Create a Project")

    project_list = list_projects()
    col1, col2 = st.columns([3, 1])
    with col1:
        selected = st.selectbox("Choose a project:", options=project_list)
    with col2:
        if st.button("Use Project"):
            st.session_state.current_project = selected
            st.session_state.project_selected = True
            st.rerun()

    st.markdown("---")

    # === Add New Project ===
    st.subheader("Create a New Project")
    with st.form("create_project_form"):
        new_project = st.text_input("Project name")
        create = st.form_submit_button("Create")
        if create:
            if new_project and new_project not in project_list:
                os.makedirs(get_project_path(new_project), exist_ok=True)

                # Create default config with title = folder name
                default_config = {
                    "title": new_project,
                    "description": "",
                    "keywords": []
                }
                save_project_config(new_project, default_config)

                st.success(f"Project '{new_project}' created!")
                st.session_state.current_project = new_project
                st.session_state.project_selected = True
                st.rerun()
            else:
                st.error("Project name invalid or already exists.")


    # === Delete Project ===
    st.subheader("Delete Existing Project")
    with st.form("delete_project_form"):
        to_delete = st.selectbox("Select project to delete", options=project_list)
        confirm = st.checkbox(f"Yes, delete '{to_delete}' permanently")
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
    
    # === Main View ===
    if st.session_state.selected_paper is None:
        render_logo()
        st.markdown(f"## Project: {st.session_state.current_project}")
        config = load_project_config(st.session_state.current_project)

        with st.expander("Project Info & Keywords", expanded=True):
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

                    # Rename project if title changed
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


        st.button("← Exit Project", on_click=lambda: st.session_state.update({"project_selected": None}))
        
        
        # Input Form
        with st.form("add_paper_form"):
            url = st.text_input("Paste arXiv paper URL:", key="url_input")
            submitted = st.form_submit_button("Add Paper")

        if submitted and "arxiv.org/abs" in url:
            paper = fetch_arxiv_metadata(url)
            if paper and paper["id"] not in [p["id"] for p in st.session_state.papers]:
                st.session_state.papers.append(paper)
                save_papers(st.session_state.papers, st.session_state.current_project)
                st.success("Paper added.")
            elif not paper:
                st.error("Failed to fetch paper metadata.")
            else:
                st.info("Paper already added.")

        st.divider()
        st.markdown("## Saved Papers")

        for paper in st.session_state.papers:
            render_paper_card(paper, summary_cache)
            st.divider()

    # === Detail View ===
    else:
        st.components.v1.html('''
        <script>
            var body = window.parent.document.querySelector(".main");
            body.scrollTop = 0;
        </script>
        ''')

        paper = st.session_state.selected_paper
        st.title(paper["title"])
        st.write(f"**Authors:** {paper['authors']}")
        st.write(f"**Published:** {paper['published']}")

        st.divider()
        display_summary(paper, summary_cache)
        st.divider()

        st.write(f"**Abstract:** {paper['summary']}")
        st.markdown(f"[View on arXiv]({paper['link']})")

        st.button("← Go Back", on_click=lambda: st.session_state.update({"selected_paper": None}))

    # === Post-render Summary Generation ===
    for paper in st.session_state.papers:
        pid = paper["id"]
        if pid in st.session_state.generating_summaries:
            if pid not in summary_cache:
                result = summarize_paper(pid, paper["summary"], summary_cache, st.session_state.current_project)
                summary_cache[pid] = result
                save_summary_cache(summary_cache, st.session_state.current_project)
            st.session_state.generating_summaries.remove(pid)
            st.rerun()