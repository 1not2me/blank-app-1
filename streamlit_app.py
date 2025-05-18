import streamlit as st
import openai
import PyPDF2
import requests
from bs4 import BeautifulSoup
from openai.error import RateLimitError, AuthenticationError

# הגדרת מפתח API מתוך secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# חילוץ טקסט מקובץ PDF
def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text if text else "❗ לא נמצא טקסט בקובץ PDF."
    except Exception as e:
        return f"שגיאה בקריאת PDF: {e}"

# חילוץ טקסט מאתר אינטרנט
def extract_text_from_url(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        return "\n".join([p.get_text(strip=True) for p in paragraphs])
    except Exception as e:
        return f"שגיאה בעיבוד הקישור: {e}"

# הגדרת מספר תווים מקסימלי לפי סגנון
def get_token_limit(style):
    return {
        "short": 400,
        "detailed": 800,
        "bullet points": 1000
    }.get(style, 600)

# סיכום טקסט
def summarize_text(text, style="short"):
    prompt = f"Summarize the following text in a {style} style:\n\n{text}"
    max_tokens = get_token_limit(style)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except RateLimitError:
        return "❌ עומס על המערכת. נסי שוב בעוד רגע."
    except AuthenticationError:
        return "🔐 בעיה באימות המפתח. בדקי את OPENAI_API_KEY."
    except Exception as e:
        return f"שגיאה כללית: {e}"

# מענה על שאלה מתוך טקסט
def answer_question(text, question):
    prompt = f"""Answer the following question based on the text below:\n\nText: {text}\n\nQuestion: {question}\nAnswer:"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except RateLimitError:
        return "❌ כרגע יש עומס. נסי שוב בעוד רגע."
    except AuthenticationError:
        return "🔐 בעיה בזיהוי המפתח. בדקי את OPENAI_API_KEY."
    except Exception as e:
        return f"שגיאה כללית: {e}"

# ---------------- ממשק משתמש ----------------

st.set_page_config(page_title="AI Document Analyzer", page_icon="📄")
st.title("📄 AI Document Analyzer")

source = st.radio("בחר מקור למסמך:", ["העלאת קובץ PDF/TXT", "הזנת קישור אינטרנט"])
text = ""

# מקור קובץ
if source == "העלאת קובץ PDF/TXT":
    uploaded_file = st.file_uploader("העלה קובץ", type=["pdf", "txt"])
    if uploaded_file:
        if uploaded_file.name.endswith(".pdf"):
            text = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.name.endswith(".txt"):
            try:
                text = uploaded_file.read().decode("utf-8")
            except:
                text = "❗ שגיאה בקריאת קובץ הטקסט."

# מקור קישור
elif source == "הזנת קישור אינטרנט":
    url = st.text_input("הכנס כתובת אתר:")
    if url:
        text = extract_text_from_url(url)

# הצגת טקסט ופעולות
if text:
    st.subheader("📚 טקסט שחולץ (תצוגה מקדימה):")
    st.text_area("תצוגה", value=text[:1000], height=200)

    summary_style = st.selectbox("בחר סגנון סיכום:", ["short", "detailed", "bullet points"])
    if st.button("📝 צור סיכום"):
        summary = summarize_text(text, summary_style)
        st.subheader("✨ סיכום הטקסט:")
        st.write(summary)

    st.subheader("❓ שאל שאלה על המסמך:")
    user_question = st.text_input("הקלד שאלה כאן:")
    if st.button("💬 קבל תשובה"):
        if user_question:
            answer = answer_question(text, user_question)
            st.write("🔍 תשובה:", answer)
        else:
            st.warning("יש להזין שאלה.")
