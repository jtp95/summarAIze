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
