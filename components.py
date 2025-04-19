import streamlit as st

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
    st.markdown(f"#### {paper['title']}")
    summary_data = summary_cache.get(paper["id"])
    if summary_data:
        st.caption(summary_data["summary"] or summary_data["keywords"])
    else:
        st.caption("Generating summary...")
    if st.button("View Details", key=f"view_{paper['id']}"):
        st.session_state.selected_paper = paper
        st.rerun()