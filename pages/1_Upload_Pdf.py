import streamlit as st
from VectorDatabaseClient import VectorDatabaseClient
from SkyboxPdfHandler import SkyboxPdfHandler
#from main import add_usage_entry
from main import check_authentication
from main import get_resources
check_authentication()

st.set_page_config(page_title="File Upload, Chunking, Embedding, and Pinecone Upload", page_icon="📁")

st.title("File Upload, Chunking, Embedding, and Pinecone Upload")


client = get_resources()['gcp']
index = VectorDatabaseClient()

if st.button("Delete all uploaded data !!!"):
    bucket_name = "sb-docs"
    try:
        client.clean()
        index.delete(delete_all=True, namespace="default")
        st.success("All uploaded data deleted.")
    except Exception as e:
        if "Namespace not found" in str(e):
            st.success("All uploaded data deleted.")
        else:
            st.error(f"{e.body}")
else:
    # File uploader
    uploaded_file = st.file_uploader("Upload Skybox PDF file", type=["pdf"])

    if uploaded_file is not None:
        st.write("File details:")
        st.write(f"Filename: {uploaded_file.name}")
        st.write(f"File size: {uploaded_file.size} bytes")

        # Upload button
        if st.button("Upload, Process, Embed, and Upload to Pinecone"):
            bucket_name = "sb-docs"
            
            try:
                if uploaded_file.type == "application/pdf":
                    sb_file=SkyboxPdfHandler(client, uploaded_file)
                    sb_file.pdf_to_text()
                    sb_file.process_pdf()
                    sb_file.save()                
                    st.success(f"File processed and split into {len(sb_file.chunks)} chunks. Embeddings stored in GCS and uploaded to Pinecone with metadata.")
                else:
                    st.error("Please upload a PDF file.")
                # Process, embed chunks, and upload to Pinecone
            
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    st.sidebar.success("You are currently on the File Upload, Chunking, Embedding, and Pinecone Upload page.")
