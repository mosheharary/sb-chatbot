import streamlit as st
from nltk.tokenize import word_tokenize
from rank_bm25 import BM25Okapi
from LangChainChatClient import LangChainChatClient
from main import check_authentication
from SkyboxPdfHandler import SkyboxPdfHandler
from langchain.prompts import ChatPromptTemplate
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain.schema import SystemMessage, HumanMessage, AIMessage


selected_embedding_models = st.session_state.params["selected_embedding_models"]
selected_llm_models = st.session_state.params["selected_llm_models"]
messages = StreamlitChatMessageHistory(key="chat_messages")

st.set_page_config(page_title="Skybox Assistant", page_icon="🤖")
st.sidebar.header("Parameters")
prompt_default = st.sidebar.text_area(
    "Default Prompt", 
    value="""
    Act as a conversational assistant.
    Answer the question based only on the following context:
    """,height=150)
temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.0, value=0.5, step=0.1)

llm = LangChainChatClient(temperature=temperature)


PROMPT_TEMPLATE = prompt_default + """

{context}

---
Answer the question based on the above context: 
{question}

if this is not a question, please ask the user to rephrase it as a question.
"""


def load_files_from_gcs_subdirectory(bucket_name, subdirectory):
    file_handler = SkyboxPdfHandler()
    return file_handler.load_files_from_gcs_subdirectory(subdirectory)

def retrieve_with_bm25(chunk_directory,query,top_k):
    CHUNK_PATH = chunk_directory
    #load chunks from directory
    corpus = load_files_from_gcs_subdirectory("sb-docs", chunk_directory)
    if len(corpus) == 0:
        return []
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
    llm = LangChainChatClient()
    embedding = llm.create_embedding(text)        
    return embedding

def get_relevant_chunks(query, top_k=3):
    file_handler = SkyboxPdfHandler()    
    from_pincone = file_handler.get_from_pincone(query, top_k)
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


def generate_response(user,system_message):
    llm = LangChainChatClient(temperature = 0.2)
    response = llm.batch_chat(user,system_message)


    response_content = response.choices[0].message.content.strip()
    input_cost = response.usage.prompt_tokens
    output_cost = response.usage.completion_tokens 
    usage = {"prompt_tokens": input_cost, "completion_tokens": output_cost}
    return response_content, usage


def get_prompt(query_text: str):
    results = get_relevant_chunks(query_text)

    context_text = "\n\n---\n\n".join(results)
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    return prompt


def main():
    st.subheader("Skybox Knowledge Base", divider="red", anchor=False)
    for msg in messages.messages:
        if isinstance(msg, AIMessage):
            st.chat_message("assistant").write(msg.content)
        elif isinstance(msg, HumanMessage):
            st.chat_message("human").write(msg.content)
    
    if prompt := st.chat_input("Enter a prompt here..."):
        try:
            with st.spinner("Thinking..."):
                messages.add_message(HumanMessage(content=prompt))
                st.chat_message("human").write(prompt)
                system_message = SystemMessage(content=get_prompt(prompt))
                model_messages = [system_message] + messages.messages            
                ai_response = llm.chat_model(model_messages)

            messages.add_message(AIMessage(content=ai_response.content))
            st.chat_message("assistant").write(ai_response.content)
        except Exception as e:
            st.error(e, icon="⛔️")

    if st.sidebar.button("Clear Chat History"):
        messages.clear()

    st.sidebar.success("You are currently on the Contextual Chatbot page.")
         
check_authentication()
main()
st.stop() 
