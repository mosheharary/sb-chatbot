import streamlit as st
from nltk.tokenize import word_tokenize
from main import check_authentication
from main import get_resources

from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain.schema import SystemMessage, HumanMessage, AIMessage

selected_embedding_models = st.session_state.params["selected_embedding_models"]
selected_llm_models = st.session_state.params["selected_llm_models"]
messages = StreamlitChatMessageHistory(key="chat_messages")

st.set_page_config(page_title="Skybox Assistant", page_icon="🤖")


st.sidebar.header("Parameters")
prompt_default = st.sidebar.text_area(
    "Default Prompt", 
    value="""You are an expert assistant tasked with answering questions based on provided documents. Follow these guidelines for each response:
1. **Primary Source Check**: Always look for answers in the provided documents first. Use the content of these documents as your primary source, and include relevant information from them in your response. If there are multiple documents, combine the information thoughtfully and concisely.
2. **External Knowledge (Secondary Source)**: If the answer isn’t fully covered in the provided documents, use other information you have access to in order to complete the response. Make it clear when additional information is being included.
3. **Detailed and Structured Responses**: Provide answers in a detailed and organized manner. Use numbered steps to guide the reader through your response logically, highlighting key points and important details. If the question is in the form of multiple choice questions and there are several options to answer , please response only the text of the answer chosen and nothing else .
4. **Clarity and Completeness**: Ensure each response is clear and complete. Avoid unnecessary details but make sure to cover the main aspects of the question thoroughly.
5. **Reference**: Whenever possible, indicate which part of the provided documents your answer is drawn from, using quotes or summaries as needed.
Use this structure to create responses that are thorough, organized, and insightful.
6. **If the questions is in the form of multiple choice question , just return the answer , nothing more and nothing less

    """,height=150)
temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.0, value=0.1, step=0.1)
top_k = st.sidebar.slider("Top K", min_value=1, max_value=10, value=3, step=1)

llm_models = [
            "gpt-4o-mini",
            "gpt-4o",
            "o1-preview"
]

selected_llm_models = st.selectbox(
    "Select OpenAI  Model:",
    options=llm_models,
    index=0,  # Default selection
    help="Choose an OpenAI LLM model from the list. This parameter will take effect when you ask a question."
)

rag = get_resources()['rag']
rag.update_parameters(prompt_default, temperature, top_k)
rag.update_llm_model(selected_llm_models)

def format_chunk(chunk):
    # Split the chunk into lines and join with newlines to preserve formatting
    return chunk.strip().split('\n')

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
                sys_message_content , picked_chunks = rag.get_prompt(prompt)
                st.session_state.current_chunks = picked_chunks
                system_message = SystemMessage(content=sys_message_content)
                model_messages = [system_message] + messages.messages         
                ai_response = rag.chat_model(model_messages)   

            messages.add_message(AIMessage(content=ai_response.content))
            st.chat_message("assistant").write(ai_response.content)
        except Exception as e:
            st.error(e, icon="⛔️")
    
    st.divider()

    with st.expander("View Reference Chunks", expanded=False):
        if "current_chunks" not in st.session_state:
            st.session_state['current_chunks'] = []
        if st.session_state.current_chunks:
            for i, chunk in enumerate(st.session_state.current_chunks):
                # Format the chunk text to preserve formatting
                formatted_lines = format_chunk(chunk)
                st.text_area(f"Chunk {i+1}", value='\n'.join(formatted_lines), height=150)
        else:
            st.info("No reference chunks available. Ask a question to see relevant document chunks.")


    if st.sidebar.button("Clear Chat History"):
        messages.clear()

    st.sidebar.success("You are currently on the Contextual Chatbot page.")
         
check_authentication()
main()
st.stop() 
