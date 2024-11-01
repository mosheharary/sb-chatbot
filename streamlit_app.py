import streamlit as st
import fitz
import os
from openai import OpenAI

PDF_FILEPATHS = r"/tmp/docs"
TKT_FILEPATHS = r"/tmp/txt"
CHUNKS_SAVE_PATH = r"/tmp/chunks"
CHUNKS_EMBEDDINGS_SAVE_PATH=r"/tmp/chunks_embeddings"
DOCUMENT_TYPE = "skybox"

def save_uploadedfile(uploadedfile):
     with open(os.path.join(PDF_FILEPATHS,uploadedfile.name),"wb") as f:
         f.write(uploadedfile.getbuffer())
     return st.success("Saved File:{} to {}".format(uploadedfile.name),PDF_FILEPATHS)


## PDF Upload and Processing

st.title("PDF Processor and ChatBot")

# File uploader for multiple PDFs
uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

# Skip option
skip_upload = st.checkbox("Skip file upload")

if not skip_upload and uploaded_files:
    os.makedirs(PDF_FILEPATHS, exist_ok=True)
    os.makedirs(CHUNKS_SAVE_PATH, exist_ok=True)
    os.makedirs(TKT_FILEPATHS, exist_ok=True)
    os.makedirs(CHUNKS_EMBEDDINGS_SAVE_PATH, exist_ok=True)

    for uploaded_file in uploaded_files:
        save_uploadedfile(uploaded_file)
        

## ChatBot Interface

st.header("ChatBot")

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for response in client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
        ):
            full_response += (response.choices[0].delta.content or "")
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})