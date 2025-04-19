import streamlit as st
from utils import *
from suggester import generate_live_suggestions
from summarizer import load_summary_cache
import hashlib

#==================== Summary ====================#

def display_summary(paper, summary_cache):
    paper_id = paper["id"]
    
    summary_box = st.empty()
    keywords_box = st.empty()

    summary_data = summary_cache.get(paper_id)
    
    if summary_data:
        summary_box.markdown(f"**Summary:** {summary_data['summary']}")
        keywords_box.markdown(f"**Keywords:** {summary_data['keywords']}")
    elif paper_id in st.session_state.generating_summaries:
        summary_box.markdown("Generating summary...")
        keywords_box.markdown("Generating keywords...")
    else:
        # Trigger generation
        st.session_state.generating_summaries.add(paper_id)
        summary_box.markdown("Generating summary...")
        keywords_box.markdown("Generating keywords...")
        st.rerun()


#==================== Logo ====================#

def render_logo():
    st.markdown("""
    <h1 style='font-size:24px; margin-bottom:10px;'><span style='color:#4B8BBE;'>SummarAIze</span></h1>
    """, unsafe_allow_html=True)

#==================== Card ====================#

def render_paper_card(paper, summary_cache):
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"#### [{paper.get('citation_id', '?')}] {paper['title']}")
        summary_data = summary_cache.get(paper["id"])
        if summary_data:
            st.caption(summary_data["summary"] or summary_data["keywords"])
        else:
            st.caption("Generating summary...")
            
    with col2:
        st.markdown("<div style='margin-top: 0.3rem'></div>", unsafe_allow_html=True)
        if st.button("View", key=f"view_{paper['id']}"):
            st.session_state.selected_paper = paper
            st.rerun()
            
        delete_key = f"delete_confirm_{paper['id']}"
        if st.session_state.get(delete_key):  # already armed
            if st.button("Confirm", key=f"confirm_{paper['id']}", type="primary"):
                delete_paper_by_id(paper["id"])
                save_papers(st.session_state.papers, st.session_state.current_project)
                st.session_state.pop(delete_key)
                st.success("Paper deleted.")
                st.rerun()
        else:
            if st.button("Delete", key=f"delete_{paper['id']}"):
                st.session_state[delete_key] = True
                st.rerun()
        
#==================== Tabs ====================#

def render_tab_add():
    with st.form("add_paper_form"):
        url = st.text_input("Paste arXiv paper URL:", key="url_input")
        submitted = st.form_submit_button("Add Paper")

    if submitted and "arxiv.org/abs" in url:
        paper = fetch_arxiv_metadata(url)
        if paper:
            result = add_paper_to_session(paper)
            if result == "added":
                st.success(f"Paper added as citation [{paper['citation_id']}]")
            elif result == "duplicate":
                st.info("Paper already added.")
        else:
            st.error("Failed to fetch paper metadata.")



def render_tab_find():
    st.subheader("Find Suggested Sources")

    custom_query = st.text_input("Add a specific query to improve suggestions", key="custom_query")

    if st.button("Find"):
        with st.spinner("Thinking..."):
            project_config = load_project_config(st.session_state.current_project)
            project_config["custom_query"] = custom_query  # add this line
            suggestions = generate_live_suggestions(project_config)
            st.session_state.temp_suggestions = suggestions
            if len(st.session_state.temp_suggestions) == 0:
                st.markdown("None found; Try again")
    
    

    for paper in st.session_state.temp_suggestions:
        st.markdown(f"**{paper['title']}**")
        st.caption(f"{format_authors(paper['authors'])} — {paper['published'][:10] if 'published' in paper else '?'}")
        st.markdown(paper['summary'])

        col1, col2 = st.columns([1, 1])
        paper_id = paper.get("id", paper.get("link", hashlib.md5(paper["title"].encode()).hexdigest()))

        with col1:
            if st.button("Accept", key=f"accept_{paper_id}"):
                paper["id"] = paper_id  # ensure paper has ID if it came from web
                result = add_paper_to_session(paper)
                if result == "added":
                    st.success(f"Added as citation [{paper['citation_id']}]")
                st.session_state.temp_suggestions = [
                    p for p in st.session_state.temp_suggestions if p.get("id") != paper_id
                ]
                st.rerun()
        
        with col2:
            if st.button("Reject", key=f"reject_{paper_id}"):
                st.session_state.temp_suggestions = [
                    p for p in st.session_state.temp_suggestions if p.get("id") != paper_id
                ]
                st.rerun()



def render_tab_paper():
    sorted_papers = sorted(
        st.session_state.papers,
        key=lambda p: p.get("citation_id", float("inf"))  # put missing IDs last
    )

    for i, paper in enumerate(sorted_papers):
        summary_cache = load_summary_cache(st.session_state.current_project)
        render_paper_card(paper, summary_cache)
        st.markdown("<hr style='margin: 0.3rem 0;'>", unsafe_allow_html=True)


