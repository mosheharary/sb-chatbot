import PyPDF2
import io
import streamlit as st
import tiktoken
import json
from jinja2 import Environment, FileSystemLoader
from LangChainChatClient import LangChainChatClient
from google.oauth2 import service_account
from google.cloud import storage
from  pinecone import Pinecone






class SkyboxPdfHandler:

    def load_files_from_gcs_subdirectory(self, subdirectory):
        bucket = self.gcp_client.bucket(self.bucket_name)
        blobs = list(bucket.list_blobs(prefix=subdirectory))
        
        if not blobs:
            return []  # or you could raise an exception or return a special value
        
        texts = []
        for blob in blobs:
            if blob.name.endswith('/'):  # Skip directory markers
                continue
            content = blob.download_as_text()
            texts.append(f"File: {blob.name}\nContent: {content}\n")
        
        return texts

    def get_embedding(self, text):
        llm = LangChainChatClient()
        embedding = llm.create_embedding(text)        
        return embedding
    
    def prompt_gpt(self,prompt):
        #messages = [{"role": "user", "content": prompt}]
        messages = prompt
        llm = LangChainChatClient()
        content = llm.chat(messages)
        return content


    def get_add_context_prompt(self, chunk):
        file_loader = FileSystemLoader('./templates')
        env = Environment(loader=file_loader)
        template = env.get_template('create_context_prompt.j2')
        data = {
            'WHOLE_DOCUMENT': self.text,  # Leave blank for default or provide a name
            'CHUNK_CONTENT': chunk  # You can set any score here
        }
        output = template.render(data)
        return self.prompt_gpt(output)

    def create_embedding(self, chunk, chunk_index):
        chunk_with_context = self.get_add_context_prompt(chunk) + "\n\n" + chunk
        embedding = self.get_embedding(chunk_with_context)
        id = f"{self.name.split('.')[0]}_{chunk_index}.json"
        txt_file_name = f"{self.name.split('.')[0]}.txt"
        json_object = {
            "id": id,
            "filename": txt_file_name,
            "chunk_idx": chunk_index,
            "chunk_text": chunk_with_context,
            "chunk_embedding": embedding
        }        
        text_blob_name = f"chunks/{self.base_blob_name}_{chunk_index}.txt"
        text_file = io.BytesIO(chunk_with_context.encode('utf-8'))
        self.text_files.append(tuple([text_blob_name,text_file]))

        json_blob_name = f"embeddings/{self.base_blob_name}_{chunk_index}.json"
        json_file = io.BytesIO(json.dumps(json_object).encode('utf-8'))
        self.json_files.append(tuple([json_blob_name,json_file]))

        self.json_objects.append(json_object)


    def split_text(self):
        encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(self.text)
        overlap = self.chunk_overlap
        chunks = []
        for i in range(0, len(tokens), self.chunk_size - overlap):
            chunk = tokens[i:i + self.chunk_size]
            chunks.append(encoding.decode(chunk))
        self.chunks=chunks

    def pdf_to_text(self):
        pdf_reader = PyPDF2.PdfReader(self.uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        self.text = text
        self.text_file = io.BytesIO(text.encode('utf-8'))

    def __init__(self, uploaded_file=None):
        if uploaded_file:
            self.uploaded_file = uploaded_file
            self.name = uploaded_file.name
            self.pdf_blob_name = f"pdfs/{uploaded_file.name}"
            self.txt_blob_name = f"texts/{uploaded_file.name.rsplit('.', 1)[0]}.txt"
            self.base_blob_name = f"{uploaded_file.name.rsplit('.', 1)[0]}"
            self.embeddings_base_name = f"embeddings/{uploaded_file.name.rsplit('.', 1)[0]}"

        self.bucket_name = "sb-docs"
        self.chunk_size = st.session_state.params["chunk_size"]
        self.chunk_overlap = st.session_state.params["chunk_overlap"]
        self.selected_embedding_models = st.session_state.params["selected_embedding_models"]
        self.selected_llm_models = st.session_state.params["selected_llm_models"]
        self.json_files = []    
        self.text_files = []
        self.json_objects = []
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        self.gcp_client = storage.Client(credentials=credentials)
        pinecone = Pinecone(api_key=st.secrets['PINECONE_API_KEY'])
        index_name = "skybox-docs"
        self.index = pinecone.Index(index_name)



    def process_pdf(self):
        self.split_text()
        for i, chunk in enumerate(self.chunks):        
            self.create_embedding(chunk, i)

    def upload_to_gcs(self, file, bucket_name, destination_blob_name):
        bucket = self.gcp_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_file(file)

    def save(self):
        self.upload_to_gcs(self.text_file, self.bucket_name, self.txt_blob_name)
        self.uploaded_file.seek(0)
        self.upload_to_gcs(self.uploaded_file, self.bucket_name, self.pdf_blob_name)
        for i, json_file in enumerate(self.json_files):
            json_blob_name = json_file[0]
            file = json_file[1]
            self.upload_to_gcs(file, self.bucket_name, json_blob_name)

        for i, text_file in enumerate(self.text_files):
            text_blob_name = text_file[0]
            file = text_file[1]
            self.upload_to_gcs(file, self.bucket_name, text_blob_name)
        
        for json_object in self.json_objects:
            self.upload_to_pinecone(json_object)

    def upload_to_pinecone(self,json_object):
        id = json_object["id"]
        chunk_embedding = json_object["chunk_embedding"]
        filename = json_object["filename"]
        chunk_idx = json_object["chunk_idx"]
        chunk_text = json_object["chunk_text"]
        try:
            self.index.upsert(vectors=[
                (
                    id,
                    chunk_embedding,
                    {
                        "filename": filename,
                        "chunk_idx": chunk_idx,
                        "chunk_text": chunk_text
                    }
                )
            ])
        except Exception as e:
            st.error(f"Error: {e}")

    def get_from_pincone(self,query,top_k=3):
        query_embedding = self.get_embedding(query)
        results = self.index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
        from_pincone = [result.metadata["chunk_text"] for result in results.matches]        
        return from_pincone
        

    def get_page(self, page_number):
        self.page = self.pdf.load_page(page_number)
        return self.page

    def get_text(self):
        return self.page.get_text()

    def get_text_lines(self):
        return self.page.get_text("text")

    def get_text_blocks(self):
        return self.page.get_text("blocks")
