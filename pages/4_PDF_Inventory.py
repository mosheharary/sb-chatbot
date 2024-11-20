import streamlit as st
from google.cloud import storage
import tempfile
import os
from PyPDF2 import PdfReader
import io
from main import get_resources
from main import check_authentication
check_authentication()

client = get_resources()['gcp']

def display_pdf(file_path):
    blob = client.get_blob(file_path)
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        blob.download_to_filename(temp_file.name)
        with open(temp_file.name, 'rb') as file:
            pdf_reader = PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                st.write(f"Page {page_num + 1}")
                st.write(page.extract_text())


def main():
    st.set_page_config(page_title="Inventory", layout="wide")
    
    st.title("Inventory")
    
    # Replace with your bucket name and subdirectory
    subdirectory = "pdfs/"
    
    files = client.list_files_in_bucket(subdirectory)
    selected_file = st.selectbox("Select a file", files)
    
    if st.button("Open PDF"):
        if selected_file:
            st.write(f"Displaying: {selected_file}")
            display_pdf(selected_file)
        else:
            st.warning("Please select a file.")

if __name__ == "__main__":
    main()