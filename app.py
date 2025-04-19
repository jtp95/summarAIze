import streamlit as st
from utils import *

# Store multiple papers
if "papers" not in st.session_state:
    st.session_state.papers = load_saved_papers()
    
if "selected_paper" not in st.session_state:
    st.session_state.selected_paper = None

# === MAIN VIEW ===
if st.session_state["selected_paper"] is None:
    st.title("SummarAIze")
    st.write("Your on-device AI citation organizer.")

    # URL input inside form (avoids rerun issues)
    with st.form("add_paper_form"):
        url = st.text_input("Paste arXiv paper URL:", key="url_input")
        submitted = st.form_submit_button("Add Paper")
    
    if submitted and "arxiv.org/abs" in url:
        paper = fetch_arxiv_metadata(url)
        if paper and paper["id"] not in [p["id"] for p in st.session_state.papers]:
            st.session_state.papers.append(paper) 
            save_papers(st.session_state.papers)
            st.success("Paper added.")
        elif not paper:
            st.error("Failed to fetch paper metadata.")
        else:
            st.info("Paper already added.")

    st.divider()
    st.header("Saved Papers")

    for i, paper in enumerate(st.session_state.papers):
        st.markdown(f"### {paper['title']}")
        st.markdown(f"*{format_authors(paper['authors'])}*  —  {paper['published'][:10]}")
        st.markdown("*1-sentence summary will go here*")

        # Create button to view this paper
        if st.button("View Details", key=f"view_{paper['id']}"):
            st.session_state.selected_paper = paper
            st.rerun()  # immediately rerun and render detail view

        st.divider()


# === DETAIL VIEW ===
else:
    st.components.v1.html('''
    <script>
        var body = window.parent.document.querySelector(".main");
        console.log(body);
        body.scrollTop = 0;
    </script>
    ''')
    
    paper = st.session_state.selected_paper
    st.title(paper["title"])
    st.write(f"**Authors:** {paper['authors']}")
    st.write(f"**Published:** {paper['published']}")
    st.write(f"**Abstract:** {paper['summary']}")
    st.markdown(f"[🔗 View on arXiv]({paper['link']})")

    st.button("← Go Back", on_click=lambda: st.session_state.update({"selected_paper": None}))
