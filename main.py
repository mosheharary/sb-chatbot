import streamlit as st
import nltk
from datetime import datetime, time, timedelta
from SqliteClient import SqliteClient
from StorageClient import StorageClient
from RagAgent import RagAgent
from SkyboxPdfHandler import SkyboxPdfHandler


nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

@st.cache_resource
def get_resources():
    gcp = StorageClient(st.secrets["gcs_bucket_name"])
    rag = RagAgent(SkyboxPdfHandler(gcp),gcp)
    return {
        "gcp": gcp,
        "rag": rag
    }

def get_gcp():
    return get_resources()['gcp']

def get_rag():
    return get_resources()['rag']


def init_slqitecloud():
    sqlient = SqliteClient ("sb-docs")
    sqlient.create_table("api_usage_data","request_timestamp TEXT,request_tokens INTEGER,request_type TEXT")
    sqlient.create_table("rag_evaluation","question TEXT,reference_answer TEXT, rag_response TEST,rouge1_score REAL,rougeL_score REAL,bert_score REAL")

# Define the authentication function
def authenticate(username, password):
    return (username == st.secrets["auth_username"] and 
            password == st.secrets["auth_password"])

# Main application
def main():    
    st.set_page_config(page_title="Skybox Assistant", page_icon="🏠")

    # Initialize session state for authentication
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # Sidebar for login/logout
    with st.sidebar:
        if not st.session_state.authenticated:
            st.title("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                if authenticate(username, password):
                    st.session_state.authenticated = True
                    st.success("Logged in successfully!")
                    init_slqitecloud()
                else:
                    st.error("Invalid username or password")
        else:
            st.title("Navigation")
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.success("Logged out successfully!")
    # Main content
    if st.session_state.authenticated:
        st.title("Welcome to Skybox Assistant")


        # Display available pages
        st.sidebar.page_link("pages/1_Upload_Pdf.py", label="Skybox PDF Upload")
        st.sidebar.page_link("pages/2_Skybox_Assistant.py", label="Skybox Assistant")
        st.sidebar.page_link("pages/3_OpenAI_Analytics.py", label="OpenAI Analytics")
        st.sidebar.page_link("pages/4_PDF_Inventory.py", label="PDF Inventory")
        st.sidebar.page_link("pages/5_Rag_Evaluation.py", label="Rag Evaluation")

        if 'chunk_size' not in st.session_state:
            st.session_state['chunk_size'] = st.number_input(
                "Chunk Size (1000 to 7000):",
                min_value=1000,
                max_value=7000,
                value=6000,  # Default value
                step=100,
                help="Enter a chunk size between 500 and 7000. This parameter will take effect when you upload a PDF file."
            )

    # Input for chunk overlap
        if 'chunk_overlap' not in st.session_state:
            st.session_state['chunk_overlap'] = st.number_input(
                "Chunk Overlap (100 to 500):",
                min_value=100,
                max_value=500,
                value=500,  # Default value
                step=50,
                help="Enter a chunk overlap between 100 and 1000. This parameter will take effect when you upload a PDF file."
            )

        embedding_models = [
            "text-embedding-3-large",
            "text-embedding-3-small"
        ]
    
        if 'selected_embedding_models' not in st.session_state:
            st.session_state['selected_embedding_models'] = st.selectbox(
                "Select Embedding Model:",
                options=embedding_models,
                index=0,  # Default selection
                help="Choose an embedding model from the list. This parameter will take effect when you upload a PDF file."
            )

        llm_models = [
            "gpt-4o-mini",
            "gpt-4o",
            "o1-preview"
        ]
    
        if 'selected_llm_models' not in st.session_state:
            st.session_state['selected_llm_models'] = st.selectbox(
                "Select OpenAI  Model:",
                options=llm_models,
                index=0,  # Default selection
                help="Choose an OpenAI LLM model from the list. This parameter will take effect when you ask a question."
            )

        st.sidebar.success("Select a page above.")
    else:
        st.title("Welcome to Skybox Assistant")
        st.write("Please log in to access the application.")

# Disable pages if not authenticated
def check_authentication():
    if not st.session_state.get('authenticated', False):
        st.error("Please log in to access this page.")
        st.stop()


if 'params' not in st.session_state:
    st.session_state.params = {
        'selected_embedding_models': '',
        'selected_llm_models': '',
        'chunk_size': (1000, 7000),
        'chunk_overlap': (100, 500)
    }


if __name__ == "__main__":
    main()
