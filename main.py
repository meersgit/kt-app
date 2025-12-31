import streamlit as st  # pyright: ignore[reportMissingImports]
import google.generativeai as genai  # pyright: ignore[reportMissingImports]
import os
import json
import tempfile
from pathlib import Path
import pypdf  # pyright: ignore[reportMissingImports]
import docx  # pyright: ignore[reportMissingImports]
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime
import boto3
# Load environment variables
load_dotenv()

# Initialize S3 client only if AWS credentials are provided
s3_client = None
S3_BUCKET = None
S3_USERS_KEY = 'users/credentials.json'

aws_access_key = os.getenv('AWS_ACCESS_KEY_ID', '').strip()
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY', '').strip()
aws_region = os.getenv('AWS_REGION', '').strip()
s3_bucket_name = os.getenv('S3_BUCKET_NAME', '').strip()

if aws_access_key and aws_secret_key and aws_region and s3_bucket_name:
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region,
            verify=True,
            use_ssl=True,
            config=boto3.session.Config(
                signature_version='s3v4',
                retries={'max_attempts': 3},
            )
        )
        S3_BUCKET = s3_bucket_name
    except Exception as e:
        print(f"Warning: Could not initialize S3 client: {e}")
        s3_client = None


# --- Configuration & Setup ---
st.set_page_config(page_title="KT App", layout="wide")

# Ensure upload directory exists
UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_users_from_s3() -> dict:
    """
    Load user credentials from S3.
    
    Returns:
        dict: Dictionary containing username-password pairs
    """
    if not s3_client or not S3_BUCKET:
        return {}  # S3 not configured, return empty dict
    
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=S3_USERS_KEY)
        users_data = json.loads(response['Body'].read().decode('utf-8'))
        return users_data
    except s3_client.exceptions.NoSuchKey:
        # If file doesn't exist, return empty dict
        return {}
    except Exception as e:
        st.error(f"Error accessing S3: {str(e)}")
        return {}

def save_users_to_s3(users_data: dict) -> bool:
    """
    Save user credentials to S3.
    
    Args:
        users_data (dict): Dictionary containing username-password pairs
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not s3_client or not S3_BUCKET:
        return False  # S3 not configured
    
    try:
        users_json = json.dumps(users_data)
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=S3_USERS_KEY,
            Body=users_json
        )
        return True
    except Exception as e:
        st.error(f"Error saving to S3: {str(e)}")
        return False

        
# --- Supabase Setup ---
def get_supabase_client():
    """Initialize and return Supabase client"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if url and key:
        return create_client(url, key)
    return None

def store_user_login(email):
    """Store user login in Supabase - updates if user exists, inserts if new"""
    supabase = get_supabase_client()
    if supabase:
        try:
            current_time = datetime.now().isoformat()
            
            # Check if user already exists
            existing = supabase.table("user_logins").select("id, email").eq("email", email).execute()
            
            if existing.data:
                # User exists - update the login_time
                user_id = existing.data[0]['id']
                supabase.table("user_logins").update({
                    "login_time": current_time
                }).eq("id", user_id).execute()
            else:
                # New user - insert
                supabase.table("user_logins").insert({
                    "email": email,
                    "login_time": current_time
                }).execute()
        except Exception as e:
            st.error(f"Error storing login: {e}")

def store_file_upload(email, filename, file_path):
    """Store file upload information in Supabase"""
    supabase = get_supabase_client()
    if supabase:
        try:
            supabase.table("file_uploads").insert({
                "email": email,
                "filename": filename,
                "file_path": file_path,
                "upload_time": datetime.now().isoformat()
            }).execute()
        except Exception as e:
            st.error(f"Error storing file upload: {e}")

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
        if email and password:
            # Load existing users from S3
            users = get_users_from_s3()
            
            # Check if user exists and password matches
            if email in users:
                if users[email] == password:
                    st.session_state.authenticated = True
                    st.session_state.username = email
                    # Store user login in Supabase
                    store_user_login(email)
                    st.rerun()
                else:
                    st.error("Invalid password")
            else:
                # New user - try to save to S3 (but don't block login if it fails)
                users[email] = password
                s3_saved = save_users_to_s3(users)
                
                # Allow login regardless of S3 save status
                st.session_state.authenticated = True
                st.session_state.username = email
                # Store user login in Supabase
                store_user_login(email)
                
                if s3_saved:
                    st.success(f"New user {email} created and saved to S3!")
                else:
                    st.warning(f"New user {email} created! (S3 not configured - user saved locally only)")
                st.rerun()
        else:
            st.error("Please enter email and password")

# --- Main App ---
def main_app():
    st.sidebar.title(f"Welcome, {st.session_state.get('username', 'User')}")
    
    # API Key Handling - Get from environment variable (optional)
    api_key = os.getenv('GEMINI_API_KEY', '').strip()
    
    tab1, tab2, tab3 = st.tabs(["Upload & Process", "Summaries", "Chatbot"])

    # --- Tab 1: Upload ---
    with tab1:
        st.header("Document Hub")
        uploaded_files = st.file_uploader("Upload Project Documents (PDF, DOCX, TXT)", accept_multiple_files=True)
        
        if uploaded_files:
            if st.button("Process Documents"):
                if not api_key:
                    st.warning("⚠️ API Key not configured. Documents will be uploaded but not summarized.")
                    # Process documents without summarization
                    progress_bar = st.progress(0)
                    for i, uploaded_file in enumerate(uploaded_files):
                        if uploaded_file.name not in st.session_state.documents:
                            with st.spinner(f"Processing {uploaded_file.name}..."):
                                file_path, text = process_file(uploaded_file)
                                summary = "Summary not available - API key not configured."
                                
                                st.session_state.documents[uploaded_file.name] = {
                                    "text": text,
                                    "summary": summary,
                                    "uploaded_by": st.session_state.username,
                                    "file_path": file_path
                                }
                                # Store file upload in Supabase
                                store_file_upload(st.session_state.username, uploaded_file.name, file_path)
                        progress_bar.progress((i + 1) / len(uploaded_files))
                    st.success("Documents processed successfully! (Note: Summaries not generated - API key needed)")
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
                                # Store file upload in Supabase
                                store_file_upload(st.session_state.username, uploaded_file.name, file_path)
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
                st.warning("⚠️ Chat feature requires API key. Please configure GEMINI_API_KEY in .env file.")
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
