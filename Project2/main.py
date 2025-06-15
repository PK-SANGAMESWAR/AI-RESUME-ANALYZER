from flask import Flask, request, send_from_directory, render_template_string
import os
import fitz  # PyMuPDF
import openai
from dotenv import load_dotenv

# Configuration
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
FRONTEND_FOLDER = 'Frontend'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def extract_text_from_pdf(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_file(filepath):
    if filepath.lower().endswith('.pdf'):
        return extract_text_from_pdf(filepath)
    elif filepath.lower().endswith('.txt'):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return ""

def analyze_resume(resume_text, job_title):
    prompt = f"""
    You are an expert resume reviewer. The candidate is applying for: "{job_title}".

    Resume:
    {resume_text}

    Provide:
    - Skill match
    - Areas of improvement
    - Summary rating out of 10
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600
    )

    return response.choices[0].message.content

@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    if request.method == "POST":
        job_title = request.form.get("job_title")
        file = request.files.get("resume")

        if file and (file.filename.lower().endswith(".pdf") or file.filename.lower().endswith(".txt")):
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)

            resume_text = extract_text_from_file(filepath)
            result = analyze_resume(resume_text, job_title)

    # Load the HTML file
    with open(os.path.join(FRONTEND_FOLDER, "index.html"), "r") as f:
        html_content = f.read()

    if result:
        html_content = html_content.replace("<!--RESULT-->", f"<div class='ai-result'><h2>AI Feedback:</h2><p>{result}</p></div>")

    return render_template_string(html_content)

@app.route("/style.css")
def serve_css():
    return send_from_directory(FRONTEND_FOLDER, "index.css")

@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory(os.path.join(FRONTEND_FOLDER, "assets"), filename)

if __name__ == "__main__":
    app.run(debug=True)
