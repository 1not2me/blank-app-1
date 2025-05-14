import streamlit as st
from openai import OpenAI
import PyPDF2
import requests
from bs4 import BeautifulSoup

# קריאת מפתח ה-API מסודות
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# חילוץ טקסט מקובץ PDF
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# חילוץ טקסט מקישור
def extract_text_from_url(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        return "\n".join([p.get_text() for p in paragraphs])
    except Exception as e:
        return f"Error extracting text: {e}"

# קביעת מספר tokens לפי סגנון הסיכום
def get_token_limit(style):
    return {
        "short": 400,
        "detailed": 800,
        "bullet points": 1000
    }.get(style, 600)

# סיכום טקסט בעזרת GPT
def summarize_text(text, style="short"):
    prompt = f"Summarize the following text in a {style} style:\n\n{text}"
    max_tokens = get_token_limit(style)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content

# מענה לשאלות על הטקסט
def answer_question(text, question):
    prompt = f"""Answer the following question based on the text below:\n
Text: {text}\n\n
Question: {question}\n
Answer:"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=300
    )
    return response.choices[0].message.content

# ממשק המשתמש
st.title("📄 AI Document Analyzer")

source = st.radio("Choose document source:", ["Upload PDF/TXT", "Enter URL"])
text = ""

if source == "Upload PDF/TXT":
    uploaded_file = st.file_uploader("Upload a file", type=["pdf", "txt"])
    if uploaded_file:
        if uploaded_file.name.endswith(".pdf"):
            text = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.name.endswith(".txt"):
            text = uploaded_file.read().decode("utf-8")

elif source == "Enter URL":
    url = st.text_input("Enter the webpage URL:")
    if url:
        text = extract_text_from_url(url)

if text:
    st.subheader("📚 Extracted Text (preview):")
    st.text_area("Text Preview", value=text[:1000], height=200)

    summary_style = st.selectbox("Choose summary style:", ["short", "detailed", "bullet points"])
    if st.button("Summarize"):
        summary = summarize_text(text, summary_style)
        st.subheader("📝 Summary:")
        st.write(summary)

    st.subheader("❓ Ask a question about the document:")
    user_question = st.text_input("Enter your question here:")
    if st.button("Get Answer"):
        if user_question:
            answer = answer_question(text, user_question)
            st.write("💬 Answer:", answer)
        else:
            st.warning("Please enter a question.")
