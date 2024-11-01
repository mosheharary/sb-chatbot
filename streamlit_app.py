import streamlit as st
import os

def get_pdf_text(files):
    return "Processed text from PDF"

def main():
    files_directory = 'predefined_files'
    
    if 'initialized' not in st.session_state or not st.session_state.initialized:
        file_paths = [os.path.join(files_directory, f) for f in os.listdir(files_directory) if f.endswith('.pdf')]
        pdffiles = []  # This would be a list of file paths or file objects
        
        for file_path in file_paths:
            pdffiles.append(file_path)  # Adjust this part to open the file if needed for processing
        
        raw_text = get_pdf_text(pdffiles)
        st.session_state.initialized = True  # Mark initialization as done to avoid re-running
        
        st.write(raw_text)
    else:
        st.write("Initialization already done.")

if __name__ == "__main__":
    main()