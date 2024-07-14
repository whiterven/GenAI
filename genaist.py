"""
Install the necessary packages

$ pip install streamlit google-generativeai
"""

import os
import time
import streamlit as st
import google.generativeai as genai

# Configure the API key for Google Generative AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Function to upload files to Gemini
def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini and returns the file object."""
    file = genai.upload_file(path, mime_type=mime_type)
    st.write(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file

# Function to wait for files to be processed
def wait_for_files_active(files):
    """Waits for the given files to be active."""
    st.write("Waiting for file processing...")
    for file in files:
        file_info = genai.get_file(file.name)
        while file_info.state.name == "PROCESSING":
            st.write(".", end="", flush=True)
            time.sleep(10)
            file_info = genai.get_file(file.name)
        if file_info.state.name != "ACTIVE":
            raise Exception(f"File {file.name} failed to process")
    st.write("...all files ready")

# Create the generative model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
)

# Initialize Streamlit app
st.title("Streamlit Chatbot with File Processing")
st.sidebar.title("Upload Files")

uploaded_files = st.sidebar.file_uploader(
    "Upload your files (images, videos, PDFs, etc.)", 
    type=["png", "jpg", "jpeg", "mp4", "pdf", "docx", "ogg"], 
    accept_multiple_files=True
)

user_input = st.text_input("Enter your message here:")

if st.button("Send"):
    if uploaded_files:
        files = [upload_to_gemini(f.name, mime_type=f.type) for f in uploaded_files]
        wait_for_files_active(files)
        chat_history = [
            {"role": "user", "parts": [file]} for file in files
        ]
    else:
        chat_history = []

    chat_history.append({"role": "user", "parts": [user_input]})

    chat_session = model.start_chat(history=chat_history)
    with st.spinner("Thinking..."):
        response = chat_session.send_message(user_input)
    
    st.write("Response from chatbot:")
    st.write(response.text)

# Display example files (optional)
example_files = [
    "example_video.mp4",
    "example_image.jpeg",
    "example_document.pdf"
]

st.sidebar.write("Example files you can upload:")
for example_file in example_files:
    st.sidebar.write(f"- {example_file}")
