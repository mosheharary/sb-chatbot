import PyPDF2
import io
import streamlit as st
import tiktoken
import json
from jinja2 import Environment, FileSystemLoader
from LangChainChatClient import LangChainChatClient
from VectorDatabaseClient import VectorDatabaseClient


class SkyboxPdfHandler:

    def load_files_from_gcs_subdirectory(self, subdirectory):
        return self.gcp_client.get_subdirectory_blobs(subdirectory)
        
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
        self.gcp_client.add_chunk(chunk_with_context)


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

    def __init__(self, gcp_client, uploaded_file=None):
        if uploaded_file:
            self.uploaded_file = uploaded_file
            self.name = uploaded_file.name
            self.pdf_blob_name = f"pdfs/{uploaded_file.name}"
            self.txt_blob_name = f"texts/{uploaded_file.name.rsplit('.', 1)[0]}.txt"
            self.base_blob_name = f"{uploaded_file.name.rsplit('.', 1)[0]}"
            self.embeddings_base_name = f"embeddings/{uploaded_file.name.rsplit('.', 1)[0]}"

        self.bucket_name = "sb-docs"
        self.chunk_size = st.session_state["chunk_size"]
        self.chunk_overlap = st.session_state["chunk_overlap"]
        self.selected_embedding_models = st.session_state["selected_embedding_models"]
        self.selected_llm_models = st.session_state["selected_llm_models"]
        self.json_files = []    
        self.text_files = []
        self.json_objects = []
        self.gcp_client = gcp_client
        self.index = VectorDatabaseClient()



    def process_pdf(self):
        self.split_text()
        for i, chunk in enumerate(self.chunks):        
            self.create_embedding(chunk, i)

    def upload_to_gcs(self, file, destination_blob_name):
        self.gcp_client.upload_from_file(file,destination_blob_name)

    def save(self):
        self.upload_to_gcs(self.text_file, self.txt_blob_name)
        self.uploaded_file.seek(0)
        self.upload_to_gcs(self.uploaded_file, self.pdf_blob_name)
        for i, json_file in enumerate(self.json_files):
            json_blob_name = json_file[0]
            file = json_file[1]
            self.upload_to_gcs(file, json_blob_name)

        for i, text_file in enumerate(self.text_files):
            text_blob_name = text_file[0]
            file = text_file[1]
            self.upload_to_gcs(file, text_blob_name)
        
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
        try:
            results = self.index.query(query_embedding, top_k)
            from_pincone = [result.metadata["chunk_text"] for result in results.matches]        
        except Exception as e:
            st.error(f"Error: {e}")            
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
