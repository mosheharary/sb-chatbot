import streamlit as st
from google.oauth2 import service_account
from google.cloud import storage
import re

class StorageClient:
    def __init__(self,bucket_name):
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        self.bucket_name = bucket_name
        self.client = storage.Client(credentials=credentials)
        self.list_blobs = self.client.list_blobs(bucket_name)
        self.bucket = self.client.bucket(bucket_name)
        self.items = {}

    def list_blobs(self):        
        return self.list_blobs
    
    def get_blob(self,blob_name):
        return self.bucket.blob(blob_name)

    def list_files_in_bucket(self,subdirectory):
        blobs = self.bucket.list_blobs(prefix=subdirectory)
        return [blob.name for blob in blobs if not blob.name.endswith('/')]

    
    def get_subdirectory_blobs(self,subdirectory):
        if subdirectory in self.items:
            return self.items[subdirectory]        
        blobs = list(self.bucket.list_blobs(prefix=subdirectory))
        if not blobs:
            return []
        texts = []
        for blob in blobs:
            if blob.name.endswith('/'):  # Skip directory markers
                continue
            content = blob.download_as_text()
            texts.append(f"{content}")

        self.items[subdirectory] = texts
        return texts
        
    
    def bucket(self):
        return self.bucket
    
    def upload_from_file(self,file,destination_blob_name):
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_file(file)

    def add_chunk(self,chunk):
        if 'chunks' not in self.items:
            self.items['chunks'] = []
        if chunk not in self.items['chunks']:
            self.items['chunks'].append(chunk)

    def clean(self):
        for blob in self.list_blobs():
            blob.delete()
        self.list_blobs = self.client.list_blobs(self.bucket_name)
        self.items = {}
