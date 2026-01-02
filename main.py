import os
from flask import Flask, render_template, request
import PyPDF2
from google import genai
from dotenv import load_dotenv


app = Flask(__name__)

# 🔑 Load environment variables from .env file
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

# Initialize the Gemini Client
client = genai.Client(api_key=api_key)

# ---------------- PDF TEXT EXTRACTION ----------------
def extract_text_from_pdf(pdf_path):
    extracted_text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return extracted_text


# ---------------- ATS ANALYSIS ----------------
def ats_analysis(resume_text):
    # Note: Using "gemini-1.5-flash" as it is the current stable version
    prompt = f"""
Analyze the resume and return ONLY in this exact format.
Do not use stars, markdown, or extra text.

SCORE: <number between 0 and 100>

PROS:
- point one
- point two
- point three

CONS:
- point one
- point two
- point three

Resume:
{resume_text}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        text = response.text.strip()
    except Exception as e:
        print(f"API Error: {e}")
        return "N/A", ["Error calling API"], []

    # ---------------- PARSING ----------------
    score = "0"
    pros = []
    cons = []

    section = None
    for line in text.splitlines():
        line = line.strip()
        if not line: continue

        if line.startswith("SCORE:"):
            score = line.replace("SCORE:", "").strip()
        elif line.startswith("PROS:"):
            section = "pros"
        elif line.startswith("CONS:"):
            section = "cons"
        elif line.startswith("-"):
            item = line[1:].strip()
            if section == "pros":
                pros.append(item)
            elif section == "cons":
                cons.append(item)

    return score, pros, cons


# ---------------- ROUTE ----------------
@app.route("/", methods=["GET", "POST"])
def index():
    score = None
    pros = []
    cons = []

    if request.method == "POST":
        file = request.files.get("resume")

        if file and file.filename.lower().endswith(".pdf"):
            # Ensure the file is saved properly
            file_path = os.path.join(os.getcwd(), "uploaded_resume.pdf")
            file.save(file_path)

            resume_text = extract_text_from_pdf(file_path)
            
            if resume_text.strip():
                score, pros, cons = ats_analysis(resume_text)
            else:
                score = "Error"
                pros = ["Could not extract text from PDF."]

    return render_template(
        "index.html",
        score=score,
        pros=pros,
        cons=cons
    )

if __name__ == "__main__":
    app.run(debug=True)