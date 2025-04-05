# app.py

import streamlit as st
from policy_loader import extract_text_from_pdf, chunk_text
from vector_store import create_vector_store, load_vector_store
from rag_engine import get_rag_qa_chain
import os

st.set_page_config(page_title="Insurance Policy RAG", layout="wide")
st.title("📄 Insurance Policy Understanding System")

if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None

with st.sidebar:
    st.header("📂 Upload Insurance Policy")
    uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
    if uploaded_file:
        file_path = os.path.join("temp_policy.pdf")
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())
        text = extract_text_from_pdf(file_path)
        chunks = chunk_text(text)
        st.session_state.vectorstore = create_vector_store(chunks)
        st.success("✅ Policy processed and indexed!")

st.markdown("### Ask any question about your policy:")

query = st.text_input("🔍 Your Question")

if query and st.session_state.vectorstore:
    rag_chain = get_rag_qa_chain(st.session_state.vectorstore)
    result = rag_chain({"query": query})
    
    st.markdown("#### 🤖 Answer:")
    st.write(result["result"])

    st.markdown("#### 📑 Relevant Clauses:")
    for doc in result['source_documents']:
        st.markdown(f"> {doc.page_content}")
