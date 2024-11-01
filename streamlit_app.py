import streamlit as st
import os
from openai import OpenAI
import PyPDF2
import tiktoken
from jinja2 import Environment, FileSystemLoader
import json



CHUNK_SIZE = 7000
CHUNK_OVERLAP = 500
TEXT_EMBEDDING_MODEL = "text-embedding-3-large"
GPT_MODEL = "gpt-4o-mini"


PDF_FILEPATHS = r"/tmp/docs"
TKT_FILEPATHS = r"/tmp/txt"
CHUNKS_SAVE_PATH = r"/tmp/chunks"
CHUNKS_EMBEDDINGS_SAVE_PATH=r"/tmp/chunks_embeddings"
DOCUMENT_TYPE = "skybox"

def prompt_gpt(prompt, openai_client):
    messages = [{"role": "user", "content": prompt}]
    response = openai_client.chat.completions.create(
        model=GPT_MODEL,  # Ensure correct model name is used
        messages=messages,
        temperature=0,
    )
    content = response.choices[0].message.content
    return content


def get_add_context_prompt(chunk_text, document_text):
    file_loader = FileSystemLoader('./templates')
    env = Environment(loader=file_loader)
    template = env.get_template('create_context_prompt.j2')
    data = {
        'WHOLE_DOCUMENT': document_text,  # Leave blank for default or provide a name
        'CHUNK_CONTENT': chunk_text  # You can set any score here
    }
    output = template.render(data)
    return output


def split_text_into_chunks_with_overlap(text):
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(text)  # Tokenize the input text
    chunks = []
    # Loop through the tokens, creating chunks with overlap
    for i in range(0, len(tokens), CHUNK_SIZE - CHUNK_OVERLAP):
        chunk_tokens = tokens[i:i + CHUNK_SIZE]  # Include overlap by adjusting start point
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
    return chunks


def dump_docs_to_chuncs(document_dir,chunk_dir, openai_client):
    tot_price=0
    document_filenames = os.listdir(document_dir)
    for filename in document_filenames:
        with open(f"{document_dir}/{filename}", "r", encoding="utf-8") as f:
            document_text = f.read()
        chunks = split_text_into_chunks_with_overlap(document_text)
        for idx, chunk in enumerate(chunks):
            fname = filename.split(".")[0]
            chunk_save_filename = f"{fname}_{idx}.json"
            chunk_save_path = f"{chunk_dir}/{chunk_save_filename}"
            if os.path.exists(chunk_save_path):
                continue
            prompt = get_add_context_prompt(chunk, document_text)
            context = prompt_gpt(prompt, openai_client)
            chunk_info = {
                "id" : f"{filename}_{int(idx)}",
                "chunk_text" : context + "\n\n" + chunk,
                "chunk_idx" : idx,
                "filename" : filename,
                "document_type": DOCUMENT_TYPE
            }
            with open(chunk_save_path, "w", encoding="utf-8") as f:
                json.dump(chunk_info, f, indent=4)


def convert_to_txt(filename):
    pdf_path = os.path.join(PDF_FILEPATHS, filename)
    txt_path = os.path.join(TKT_FILEPATHS, filename[:-4] + '.txt')
    try:
                # Open the PDF file
        with open(pdf_path, 'rb') as pdf_file:
                    # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(pdf_file)
                    
                    # Extract text from each page
            text = ''
            for page in pdf_reader.pages:
                text += page.extract_text()

                # Write the extracted text to a new text file
        with open(txt_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write(text)

        print(f"Successfully converted {filename} to text.")

    except Exception as e:
        print(f"Error converting {filename}: {str(e)}")




def save_uploadedfile(uploadedfile):
     with open(os.path.join(PDF_FILEPATHS,uploadedfile.name),"wb") as f:
         f.write(uploadedfile.getbuffer())
         convert_to_txt(uploadedfile.name)
     return st.success("Saved File:{} to {}".format(uploadedfile.name,PDF_FILEPATHS))


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
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    dump_docs_to_chuncs(PDF_FILEPATHS,CHUNKS_SAVE_PATH,openai_client)
        

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