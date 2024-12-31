import streamlit as st
from LangChainChatClient import LangChainChatClient
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain.prompts import ChatPromptTemplate
from nltk.tokenize import word_tokenize
from rank_bm25 import BM25Okapi

class RagAgent:
    def __init__(self,file_handler,gcp_handler):
        self.name = "RagAgent"
        self.age = 0
        self.selected_embedding_models = st.session_state["selected_embedding_models"]
        self.selected_llm_models = st.session_state["selected_llm_models"]
        self.messages = StreamlitChatMessageHistory(key="chat_messages")

        self.prompt_default = """
You are an expert assistant tasked with answering questions based on provided documents. Follow these guidelines for each response:
1. **Primary Source Check**: Always look for answers in the provided documents first. Use the content of these documents as your primary source, and include relevant information from them in your response. If there are multiple documents, combine the information thoughtfully and concisely.
2. **External Knowledge (Secondary Source)**: If the answer isn’t fully covered in the provided documents, use other information you have access to in order to complete the response. Make it clear when additional information is being included.
3. **Detailed and Structured Responses**: Provide answers in a detailed and organized manner. Use numbered steps to guide the reader through your response logically, highlighting key points and important details.
4. **Clarity and Completeness**: Ensure each response is clear and complete. Avoid unnecessary details but make sure to cover the main aspects of the question thoroughly.
5. **Reference**: Whenever possible, indicate which part of the provided documents your answer is drawn from, using quotes or summaries as needed.
Use this structure to create responses that are thorough, organized, and insightful.
"""
        self.propmt_context = """

{context}
---
Answer the question based on the above context: 

{question}

if this is not a question, please ask the user to rephrase it as a question.

"""
        self.temperature = 0.1
        self.top_k = 3
        self.llm = LangChainChatClient(temperature=self.temperature)
        self.file_handler = file_handler
        self.gcp_handler = gcp_handler
        self.PROMPT_TEMPLATE = self.prompt_default + self.propmt_context
        self.prompt_template = ChatPromptTemplate.from_template(self.PROMPT_TEMPLATE)

    def load_files_from_gcs_subdirectory(self,subdirectory):
        return self.gcp_handler.get_subdirectory_blobs(subdirectory)

    def retrieve_with_bm25(self,chunk_directory,query,top_k):
        CHUNK_PATH = chunk_directory
        #load chunks from directory
        corpus = self.load_files_from_gcs_subdirectory(chunk_directory)
        if len(corpus) == 0:
            return []
    # Tokenize each document in the corpus
        tokenized_corpus = [word_tokenize(doc.lower()) for doc in corpus] # should store this somewhere for easy retrieval
        bm25 = BM25Okapi(tokenized_corpus)
        tokenized_query = word_tokenize(query.lower())
        #use the bm25 to query the chunks
        return bm25.get_top_n(tokenized_query, corpus, n=top_k)

    def combine_chunks(self,chunks_bm25, chunks_vector_db, top_k=20):
        """given output from bm25 and vector database, combine them to only include unique chunks"""
        retrieved_chunks = []
        for chunk1, chunk2 in zip(chunks_bm25, chunks_vector_db):
            chunk1 = chunk1.replace("'", '"')
            chunk2 = chunk2.replace("'", '"')
            if chunk1 not in retrieved_chunks:
                retrieved_chunks.append(chunk1)
            if chunk2 not in retrieved_chunks:
                retrieved_chunks.append(chunk2)
        return retrieved_chunks

    def get_embedding(self,text):
        embedding = self.llm.create_embedding(text)        
        return embedding

    def get_relevant_chunks(self,query, top_k=3):
        from_pincone = self.file_handler.get_from_pincone(query, top_k)
        from_bm25 = self.retrieve_with_bm25("chunks",query,top_k)

        return self.combine_chunks(from_bm25, from_pincone, top_k=top_k)


    def generate_response(self,user,system_message):
        response = self.llm.batch_chat(user,system_message)
        response_content = response.choices[0].message.content.strip()
        input_cost = response.usage.prompt_tokens
        output_cost = response.usage.completion_tokens 
        usage = {"prompt_tokens": input_cost, "completion_tokens": output_cost}
        return response_content, usage


    def get_prompt(self,query_text: str):
        results = self.get_relevant_chunks(query_text, top_k=self.top_k)
        context_text = "\n\n---\n\n".join(results)
        prompt = self.prompt_template.format(context=context_text, question=query_text)
        return prompt , results
    
    def chat_model(self,model_messages):
        response = self.llm.chat_model(model_messages)
        return response
    
    def update_parameters(self,prompt_default,temperature,top_k):
        self.prompt_default = prompt_default
        self.temperature = temperature
        self.top_k = top_k
        self.llm = LangChainChatClient(temperature=self.temperature)
        self.PROMPT_TEMPLATE = self.prompt_default + self.propmt_context
        self.prompt_template = ChatPromptTemplate.from_template(self.PROMPT_TEMPLATE)

    def update_llm_model(self,model):
        self.llm.update_model(model)



