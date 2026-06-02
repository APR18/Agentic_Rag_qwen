#!/usr/bin/env python
import sys
import warnings
from datetime import datetime
import streamlit as st
import os
import tempfile
import gc
import base64
import time
from tools.custom_tool import SearchTool
from crew import AgenticRag
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")




def reset_chat():
    f"""
    Resets the messages in session state and runs garbage
    collection to free memory
    """
    st.session_state.messages=[]
    gc.collect()

def display_pdf(file_bytes,file_name):
    base64_pdf = base64.b64encode(file_bytes).decode("utf-8")
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" ...>'
    st.markdown(pdf_display,unsafe_allow_html=True)
def main():
    if "messages" not in st.session_state:
        st.session_state.messages = []  

    if "pdf_tool" not in st.session_state:
        st.session_state.pdf_tool = None 

    if "crew" not in st.session_state:
        st.session_state.crew = None 

    st.title("🤖 Agentic RAG with qwen2.5:7b")
    st.caption(
        "Ask a question — I'll search your documents first, "
        "then fall back to the web if needed."
    )
    with st.sidebar:
        st.header("Upload an image")
        uploaded_file = st.file_uploader("Choose a file",type=['pdf'])
        if uploaded_file is not None:
            if st.session_state.pdf_tool is None:
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_file_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(temp_file_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    with st.spinner("Indexing PDF... Please wait..."):
                        st.session_state.pdf_tool = SearchTool(file_path=temp_file_path)
                st.success("PDF is Indexed. Ready to chat!")
        st.button("Clear chat", on_click=reset_chat)
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    prompt = st.chat_input("Ask a question about your pdf....")
    if prompt: 
        st.session_state.messages.append({"role": "user","content":prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        if st.session_state.crew is None:
             st.session_state.crew = AgenticRag(st.session_state.pdf_tool).crew()
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            with st.spinner("Thinking..."):
                inputs = {"query":prompt}
                result = st.session_state.crew.kickoff(inputs=inputs).raw

            lines = result.split("\n")
            for i,line in enumerate(lines):
                full_response += line
                if i < len(lines) - 1:
                    full_response+= '\n'
                message_placeholder.markdown(full_response+ "▌")
                time.sleep(0.15)
            
            message_placeholder.markdown(full_response)
        
        st.session_state.messages.append({"role":"assistant","content":result})

if __name__ == "__main__":  
    main()