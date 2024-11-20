from  pinecone import Pinecone
import streamlit as st

class VectorDatabaseClient:
    def __init__(self):
        pinecone = Pinecone(api_key=st.secrets['PINECONE_API_KEY'])
        index_name = "skybox-docs"
        self.index = pinecone.Index(index_name)

    def upsert(self,vectors):
        self.index.upsert(vectors=vectors)

    def query(self,vector,top_k,include_metadata=True):
        return self.index.query(vector=vector, top_k=top_k, include_metadata=include_metadata)
    
    def delete(self,ids=None):
        if ids:
            self.index.delete(ids)            
        else:
            self.index.delete_all()
