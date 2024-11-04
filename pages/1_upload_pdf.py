import streamlit as st
from jinja2 import Environment, FileSystemLoader
from google.oauth2 import service_account
from google.cloud import storage
import PyPDF2
import io
import tiktoken
import json
from openai import OpenAI
from  pinecone import Pinecone
import os
from main import add_usage_entry
from main import check_authentication
check_authentication()


st.set_page_config(page_title="File Upload, Chunking, Embedding, and Pinecone Upload", page_icon="📁")

st.title("File Upload, Chunking, Embedding, and Pinecone Upload")

# Create a Google Cloud Storage client using service account info from secrets
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = storage.Client(credentials=credentials)

key="PINECONE_API_KEY"
PINECONE_API_KEY=os.getenv(key)
pinecone = Pinecone(api_key=PINECONE_API_KEY)
index_name = "skybox-docs"
index = pinecone.Index(index_name)

key="OPENAI_API_KEY"
OPENAI_API_KEY=os.getenv(key)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def pdf_to_text(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def upload_to_gcs(file, bucket_name, destination_blob_name):
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(file)

def convert_and_upload_pdf(pdf_file, bucket_name, pdf_blob_name, txt_blob_name):
    upload_to_gcs(pdf_file, bucket_name, pdf_blob_name)
    pdf_file.seek(0)
    text = pdf_to_text(pdf_file)
    text_file = io.BytesIO(text.encode('utf-8'))
    upload_to_gcs(text_file, bucket_name, txt_blob_name)
    return text

def split_text(text):
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    chunk_size = 7000
    overlap = 500
    chunks = []
    for i in range(0, len(tokens), chunk_size - overlap):
        chunk = tokens[i:i + chunk_size]
        chunks.append(encoding.decode(chunk))
    return chunks

def get_embedding(text):
    response = openai_client.embeddings.create(input = [text], model="text-embedding-3-large")
    add_usage_entry(response.usage.total_tokens, "get_embedding") 
    return response.data[0].embedding

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

def prompt_gpt(prompt):
    messages = [{"role": "user", "content": prompt}]
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",  # Ensure correct model name is used
        messages=messages,
        temperature=0,
    )
    add_usage_entry(response.usage.total_tokens, "prompt_gpt") 
    content = response.choices[0].message.content
    return content


def create_and_upload_embedding(chunk, chunk_index, filename, bucket_name, base_blob_name, document_text):
    prompt = get_add_context_prompt(chunk, document_text)
    context = prompt_gpt(prompt)
    chunk_with_context = context + "\n\n" + chunk
    text_file = io.BytesIO(chunk_with_context.encode('utf-8'))
    txt_blob_name = f"chunks/{base_blob_name.split('/')[1]}_{chunk_index}.txt"
    upload_to_gcs(text_file, bucket_name, txt_blob_name)

    embedding = get_embedding(chunk_with_context)
    id = f"{filename.split('.')[0]}_{chunk_index}.json"
    txt_file_name = f"{filename.split('.')[0]}.txt"
    json_object = {
        "id": id,
        "filename": txt_file_name,
        "chunk_idx": chunk_index,
        "chunk_text": chunk_with_context,
        "chunk_embedding": embedding
    }
    json_blob_name = f"{base_blob_name}_{chunk_index}.json"
    json_file = io.BytesIO(json.dumps(json_object).encode('utf-8'))
    upload_to_gcs(json_file, bucket_name, json_blob_name)
    return json_object

def upload_to_pinecone(json_object):
    index.upsert(vectors=[
        (
            json_object["id"],
            json_object["chunk_embedding"],
            {
                "filename": json_object["filename"],
                "chunk_idx": json_object["chunk_idx"],
                "chunk_text": json_object["chunk_text"]
            }
        )
    ])

def process_embed_and_upload_chunks(text, filename, bucket_name, base_blob_name):
    chunks = split_text(text)
    for i, chunk in enumerate(chunks):
        json_object = create_and_upload_embedding(chunk, i, filename, bucket_name, base_blob_name,text)
        upload_to_pinecone(json_object)
    return len(chunks)

# File uploader
uploaded_file = st.file_uploader("Choose a file to upload", type=["pdf", "txt"])

if uploaded_file is not None:
    st.write("File details:")
    st.write(f"Filename: {uploaded_file.name}")
    st.write(f"File size: {uploaded_file.size} bytes")

    # Upload button
    if st.button("Upload, Process, Embed, and Upload to Pinecone"):
        bucket_name = "sb-docs"
        
        try:
            if uploaded_file.type == "application/pdf":
                pdf_blob_name = f"pdfs/{uploaded_file.name}"
                txt_blob_name = f"texts/{uploaded_file.name.rsplit('.', 1)[0]}.txt"
                text = convert_and_upload_pdf(uploaded_file, bucket_name, pdf_blob_name, txt_blob_name)
                embeddings_base_name = f"embeddings/{uploaded_file.name.rsplit('.', 1)[0]}"
                num_chunks = process_embed_and_upload_chunks(text, uploaded_file.name, bucket_name, embeddings_base_name)
            
                st.success(f"File processed and split into {num_chunks} chunks. Embeddings stored in GCS and uploaded to Pinecone with metadata.")
            else:
                st.error("Please upload a PDF file.")
            # Process, embed chunks, and upload to Pinecone
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

st.sidebar.success("You are currently on the File Upload, Chunking, Embedding, and Pinecone Upload page.")
