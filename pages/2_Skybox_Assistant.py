import streamlit as st
from openai import OpenAI
from pinecone import Pinecone
import tiktoken
import os
from google.oauth2 import service_account
from google.cloud import storage
import nltk
from nltk.tokenize import word_tokenize
from rank_bm25 import BM25Okapi
from main import check_authentication
check_authentication()



st.set_page_config(page_title="Skybox Assistant", page_icon="🤖")


# Initialize Pinecone
key="PINECONE_API_KEY"
PINECONE_API_KEY=os.getenv(key)
pinecone = Pinecone(api_key=PINECONE_API_KEY)
index_name = "skybox-docs"
index = pinecone.Index(index_name)

key="OPENAI_API_KEY"
OPENAI_API_KEY=os.getenv(key)
openai_client = OpenAI(api_key=OPENAI_API_KEY)


# Initialize tokenizer
tokenizer = tiktoken.get_encoding("cl100k_base")
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = storage.Client(credentials=credentials)


def load_files_from_gcs_subdirectory(bucket_name, subdirectory):
    bucket = client.bucket(bucket_name)
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

def retrieve_with_bm25(chunk_directory,query,top_k):

    CHUNK_PATH = chunk_directory
    #load chunks from directory
    corpus = load_files_from_gcs_subdirectory("sb-docs", chunk_directory)

# Tokenize each document in the corpus
    tokenized_corpus = [word_tokenize(doc.lower()) for doc in corpus] # should store this somewhere for easy retrieval
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_query = word_tokenize(query.lower())
    #use the bm25 to query the chunks
    doc_scores = bm25.get_top_n(tokenized_query, corpus, n=top_k)
    return doc_scores

def combine_chunks(chunks_bm25, chunks_vector_db, top_k=20):
    """given output from bm25 and vector database, combine them to only include unique chunks"""
    retrieved_chunks = []
    for chunk1, chunk2 in zip(chunks_bm25, chunks_vector_db):
        if chunk1 not in retrieved_chunks:
            retrieved_chunks.append(chunk1)
            if len(retrieved_chunks) >= top_k:
                break
        if chunk2 not in retrieved_chunks:
            retrieved_chunks.append(chunk2)
            if len(retrieved_chunks) >= top_k:
                break
    return retrieved_chunks

def get_embedding(text):
    return openai_client.embeddings.create(input = [text], model="text-embedding-3-large").data[0].embedding

def get_relevant_chunks(query, top_k=3):
    query_embedding = get_embedding(query)
    results = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
    from_pincone = [result.metadata["chunk_text"] for result in results.matches]
    from_bm25 = retrieve_with_bm25("chunks",query,top_k)

    combined_both_chunks = combine_chunks(from_bm25, from_pincone)

    list_of_chunks = []
        #since chunks are stored in diff way , we move it to one list of texts
    for chunk in combined_both_chunks:
        if isinstance(chunk, dict):
            list_of_chunks.append(chunk["chunk_text"])
        else:
            list_of_chunks.append(chunk)
    return list_of_chunks


def generate_response(messages):
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=2000
    )
    response_content = response.choices[0].message.content.strip()
    input_cost = response.usage.prompt_tokens
    output_cost = response.usage.completion_tokens 
    usage = {"prompt_tokens": input_cost, "completion_tokens": output_cost}
    return response_content, usage

st.title("Contextual Chatbot")

# Initialize session state
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

if "context" not in st.session_state:
    st.session_state.context = ""

# Display chat messages
for message in st.session_state.chat_messages[1:]:  # Skip the system message
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
user_input = st.chat_input("Type your message here...")

if user_input:
    # Add user message to chat history
    st.session_state.chat_messages.append({"role": "user", "content": user_input})

    # Retrieve relevant chunks from Pinecone
    relevant_chunks = get_relevant_chunks(user_input)
    
    # Update context
    st.session_state.context = "\n".join(relevant_chunks)

    # Prepare messages for OpenAI
    messages_for_openai = [
        {"role": "system", "content": "You are a helpful assistant. Use the following context to answer the user's question: " + st.session_state.context},
        *st.session_state.chat_messages[1:]  # Include all user and assistant messages
    ]

    # Generate response
    response, usage = generate_response(messages_for_openai)

    # Add assistant response to chat history
    st.session_state.chat_messages.append({"role": "assistant", "content": response})

    # Display assistant response
    with st.chat_message("assistant"):
        st.write(response)

    # Display token usage
    st.info(f"Input tokens: {usage['prompt_tokens']}, Output tokens: {usage['completion_tokens']}")

# Clear chat button
if st.button("Clear Chat"):
    st.session_state.conversation = None
    st.session_state.chat_history = None
    st.session_state.chat_messages = [{"role": "system", "content": "You are a helpful assistant."}]
    st.session_state.context = ""
    st.success("Chat cleared.")

st.sidebar.success("You are currently on the Contextual Chatbot page.")
