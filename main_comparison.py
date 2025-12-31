"""
COMPARISON FILE: main.py Before and After Alteration
=====================================================

This file shows the original version (BEFORE) and the modified version (AFTER)
of the generate_summary function in main.py.

The change was made to limit summaries to 5-10 lines instead of longer summaries.
"""

# ============================================================================
# BEFORE ALTERATION (Original Version)
# # ============================================================================

# def generate_summary_BEFORE(text, api_key):
#     if not text:
#         return "No text to summarize."
    
#     try:
#         genai.configure(api_key=api_key)
#         # Using a model that is confirmed to be available and support generateContent
#         model = genai.GenerativeModel('gemini-2.5-flash')
#         prompt = f"""
#         Please summarize the following project document. 
#         Focus on:
#         1. Purpose of the document
#         2. Key processes
#         3. Important contacts / ownership
#         4. Key decisions

#         Document Content:
#         {text[:10000]}
#         """
#         response = model.generate_content(prompt)
#         return response.text
#     except Exception as e:
#         return f"Error generating summary: {e}"


# ============================================================================
# AFTER ALTERATION (Modified Version)
# ============================================================================

# def generate_summary_AFTER(text, api_key):
#     if not text:
#         return "No text to summarize."
    
#     try:
#         genai.configure(api_key=api_key)
#         # Using a model that is confirmed to be available and support generateContent
#         model = genai.GenerativeModel('gemini-2.5-flash')
#         prompt = f"""
#         Please provide a concise summary of the following project document in 5-10 lines maximum. 
#         Focus on:
#         1. Purpose of the document
#         2. Key processes
#         3. Important contacts / ownership
#         4. Key decisions

#         Keep the summary brief and to the point. Each point should be 1-2 lines.

#         Document Content:
#         {text[:10000]}
#         """
#         response = model.generate_content(prompt)
#         return response.text
#     except Exception as e:
#         return f"Error generating summary: {e}"


# ============================================================================
# FULL FILE CONTENTS (Current Version - After Alteration)
# ============================================================================

import streamlit as st  # pyright: ignore[reportMissingImports]
import google.generativeai as genai  # pyright: ignore[reportMissingImports]
import os
import tempfile
from pathlib import Path
import pypdf  # pyright: ignore[reportMissingImports]
import docx  # pyright: ignore[reportMissingImports]

# --- Configuration & Setup ---
st.set_page_config(page_title="KT App", layout="wide")

# Ensure upload directory exists
UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Session State Initialization ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'documents' not in st.session_state:
    st.session_state.documents = {}  # {filename: {'text': ..., 'summary': ..., 'metadata': ...}}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# --- Helper Functions ---

def read_pdf(file_path):
    text = ""
    try:
        reader = pypdf.PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
    return text

def read_docx(file_path):
    text = ""
    try:
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        st.error(f"Error reading DOCX: {e}")
    return text

def read_txt(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        st.error(f"Error reading TXT: {e}")
        return ""

def process_file(uploaded_file):
    # Save to disk
    file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Extract Text
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    text = ""
    if ext == ".pdf":
        text = read_pdf(file_path)
    elif ext == ".docx":
        text = read_docx(file_path)
    elif ext == ".txt":
        text = read_txt(file_path)
    
    return file_path, text

def generate_summary(text, api_key):
    if not text:
        return "No text to summarize."
    
    try:
        genai.configure(api_key=api_key)
        # Using a model that is confirmed to be available and support generateContent
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        Please provide a concise summary of the following project document in 5-10 lines maximum. 
        Focus on:
        1. Purpose of the document
        2. Key processes
        3. Important contacts / ownership
        4. Key decisions

        Keep the summary brief and to the point. Each point should be 1-2 lines.

        Document Content:
        {text[:10000]}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating summary: {e}"

# def generate_summary(text, api_key):
#     if not text:
#         return "No text to summarize."
    
#     try:
#         genai.configure(api_key=api_key)
#         # Using a model that is confirmed to be available and support generateContent
#         model = genai.GenerativeModel('gemini-2.5-flash')
#         prompt = f"""
#         Please provide a concise summary of the following project document in 5-10 lines maximum. 
#         Focus on:
#         1. Purpose of the document
#         2. Key processes
#         3. Important contacts / ownership
#         4. Key decisions

#         Keep the summary brief and to the point. Each point should be 1-2 lines.

#         Document Content:
#         {text[:10000]}
#         """
#         response = model.generate_content(prompt)
#         return response.text
#     except Exception as e:
#         return f"Error generating summary: {e}"

def chat_with_docs(query, docs_context, chat_history, api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Construct Context from all docs
        context_str = ""
        for filename, doc_data in docs_context.items():
            context_str += f"\n--- Document: {filename} ---\n"
            context_str += f"Summary: {doc_data['summary']}\n"
            context_str += f"Content: {doc_data['text'][:20000]}\n" 

        prompt = f"""
        You are a Knowledge Transfer (KT) assistant. Answer the user's question using ONLY the provided document context.
        If the information is not available in the uploaded documents, say "This information is not available in the uploaded documents."
        
        Context:
        {context_str}

        Chat History:
        {chat_history}

        User Question: {query}
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating response: {e}"

# --- Authentication ---
def login_page():
    st.title("KT App Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if email and password: # Mock auth
            st.session_state.authenticated = True
            st.session_state.username = email
            st.rerun()
        else:
            st.error("Please enter email and password")

# --- Main App ---
def main_app():
    st.sidebar.title(f"Welcome, {st.session_state.get('username', 'User')}")
    
    # API Key Handling
    api_key = "AIzaSyCUyGSDCNQwWosIttg52jxVFPvoAFmZOms"
    
    tab1, tab2, tab3 = st.tabs(["Upload & Process", "Summaries", "Chatbot"])

    # --- Tab 1: Upload ---
    with tab1:
        st.header("Document Hub")
        uploaded_files = st.file_uploader("Upload Project Documents (PDF, DOCX, TXT)", accept_multiple_files=True)
        
        if uploaded_files:
            if st.button("Process Documents"):
                if not api_key:
                    st.error("API Key required for summarization.")
                else:
                    progress_bar = st.progress(0)
                    for i, uploaded_file in enumerate(uploaded_files):
                        if uploaded_file.name not in st.session_state.documents:
                            with st.spinner(f"Processing {uploaded_file.name}..."):
                                file_path, text = process_file(uploaded_file)
                                summary = generate_summary(text, api_key)
                                
                                st.session_state.documents[uploaded_file.name] = {
                                    "text": text,
                                    "summary": summary,
                                    "uploaded_by": st.session_state.username,
                                    "file_path": file_path
                                }
                        progress_bar.progress((i + 1) / len(uploaded_files))
                    st.success("Documents processed successfully!")

        st.divider()
        st.subheader("Uploaded Documents")
        if st.session_state.documents:
            for filename, data in st.session_state.documents.items():
                st.text(f"📄 {filename} (Uploaded by {data['uploaded_by']})")
        else:
            st.info("No documents uploaded yet.")

    # --- Tab 2: Summaries ---
    with tab2:
        st.header("Document Summaries")
        if st.session_state.documents:
            for filename, data in st.session_state.documents.items():
                with st.expander(f"Summary: {filename}"):
                    st.markdown(data['summary'])
        else:
            st.info("No summaries available. Upload and process documents first.")

    # --- Tab 3: Chatbot ---
    with tab3:
        st.header("KT Assistant")
        
        # Display chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask a question about the project..."):
            if not api_key:
                st.error("API Key required.")
            else:
                # Add user message
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Generate response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response = chat_with_docs(
                            prompt, 
                            st.session_state.documents, 
                            st.session_state.chat_history[:-1], # Pass history excluding current prompt to avoid duplication in prompt logic if needed
                            api_key
                        )
                        st.markdown(response)
                
                # Add assistant message
                st.session_state.chat_history.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    if not st.session_state.authenticated:
        login_page()
    else:
        main_app()

