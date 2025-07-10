import streamlit as st
import openai
import PyPDF2
import docx
import os
from io import StringIO

st.set_page_config(page_title="Resume Matcher AI", layout="wide")

# Sidebar
st.sidebar.title("🔐 API Settings")
api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")
if api_key:
    openai.api_key = api_key
else:
    st.sidebar.warning("Please enter your OpenAI API key.")

st.title("📄 AI Resume Ranker")
st.markdown("Upload resumes and provide a job description. This app will rank resumes based on relevance using OpenAI.")

# Input: Job Description
job_description = st.text_area("📝 Paste the Job Description Here", height=250)

# Input: Resume Files
uploaded_files = st.file_uploader("📂 Upload Resumes (PDF, DOCX, or TXT)", accept_multiple_files=True, type=["pdf", "docx", "txt"])

# --- Helper Functions ---
def extract_text(file):
    if file.name.endswith(".pdf"):
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    elif file.name.endswith(".txt"):
        return file.read().decode("utf-8")
    return ""

def get_relevance_score(resume_text, job_description):
    prompt = f"""
You are an expert recruiter. Evaluate the following resume against the job description and provide a score from 0 to 100 with a short justification.

Job Description:
{job_description}

Resume:
{resume_text}

Respond in this JSON format: {{"score": <number>, "justification": "<brief explanation>"}}
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are an expert HR assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        output = response['choices'][0]['message']['content']
        return eval(output)  # Ensure response is a dict
    except Exception as e:
        return {"score": 0, "justification": f"Error: {str(e)}"}


# Helper for download
import pandas as pd
import io
def convert_to_csv(data):
    df = pd.DataFrame(data)
    output = io.StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()
    
# --- Main Logic ---
if st.button("🔍 Rank Resumes"):
    if not api_key:
        st.error("Please enter your OpenAI API key.")
    elif not job_description:
        st.error("Please paste a job description.")
    elif not uploaded_files:
        st.error("Please upload at least one resume.")
    else:
        results = []
        with st.spinner("Analyzing resumes..."):
            for file in uploaded_files:
                resume_text = extract_text(file)
                result = get_relevance_score(resume_text, job_description)
                results.append({
                    "Filename": file.name,
                    "Score": result.get("score", 0),
                    "Justification": result.get("justification", "No reason provided.")
                })

        # Sort by score
        results = sorted(results, key=lambda x: x["Score"], reverse=True)

        # Display Results
        st.success("✅ Ranking Complete!")
        st.subheader("📊 Ranked Resumes")
        st.dataframe(results, use_container_width=True)

        # Download option
        st.download_button(
            "📥 Download Results as CSV",
            data=convert_to_csv(results),
            file_name="ranked_resumes.csv",
            mime="text/csv"
        )



