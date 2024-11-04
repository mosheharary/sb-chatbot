from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

import tiktoken
from SqliteClient import SqliteClient
from datetime import datetime
import streamlit as st





class LangChainChatClient:
    def add_usage_entry(self, tokens_used, request_type):
        t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sqlite_data = {
            "request_timestamp": t,
            "request_tokens": tokens_used,
            "request_type": request_type
        }
        sqlient = SqliteClient ("sb-docs")
        sqlient.insert_data(sqlite_data,"api_usage_data")

    def __init__(self,temperature=0):
        api_key = st.secrets['OPENAI_API_KEY']
        model = st.session_state.params["selected_llm_models"]
        embedding_model = st.session_state.params['selected_embedding_models']
        self.llm = ChatOpenAI(
            openai_api_key=api_key,
            model=model,
            temperature=temperature
        )
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=api_key,
            model=embedding_model
        )
        self.temperature = temperature
        self.model = model
        self.embedding_model = embedding_model

    def chat(self, user_input, system_message=None):
        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=user_input))
        try:
            response = self.llm.invoke(messages) 
            total_tokens = response.response_metadata["token_usage"]["total_tokens"]  
            self.add_usage_entry(total_tokens, f"prompt-{self.model}")          
            return response.content
        except Exception as e:
            return f"Error: {e}"
        
    def stream_chat(self, user_input, system_message=None):
        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=user_input))

        try:
            for chunk in self.llm.stream(messages):
                yield chunk.content        
        except Exception as e:
            yield f"Error: {e}"

    def batch_chat(self, inputs, system_message=None):
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", "{question}")
        ])
        questions = []
        for user_input in inputs:
            questions.append(HumanMessage(content=user_input))
        try:            
            prompts = [prompt_template.format_prompt(question=q) for q in questions]
            responses = self.llm.batch(prompts)
            return responses
        except Exception as e:
            return f"Error: {e}"
    
    def create_embedding(self, text):
        try:
            embedding = self.embeddings.embed_query(text)
            encoding = tiktoken.encoding_for_model(self.embedding_model)
            total_tokens = len(encoding.encode(text))
            self.add_usage_entry(total_tokens, f"embedding-{self.embedding_model}") 
        except Exception as e:
            return f"Error: {e}"
        return embedding
    
    def chat_model(self,model_messages):
        try:            
            response = self.llm.invoke(model_messages)
            self.add_usage_entry(response.response_metadata["token_usage"]["total_tokens"], f"chat-{self.model}")
            return response
        except Exception as e:
            return f"Error: {e}"