from flask import Flask, render_template, request
import os
from typing import Any, cast
import fitz  # PyMuPDF
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from werkzeug.utils import secure_filename
import webbrowser

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# -------- Extract text from PDF --------
def extract_text_from_pdf(file_path):
    text_parts = []
    pdf = fitz.open(file_path)
    for page in pdf:
        page_text = page.get_text("text")
        text_parts.append(page_text if isinstance(page_text, str) else "")
    return " ".join(text_parts)

# -------- Extract text from DOCX --------
def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    return " ".join([para.text for para in doc.paragraphs])

# -------- Read resume --------
def read_resume(file_path):
    if file_path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith(".docx"):
        return extract_text_from_docx(file_path)
    return ""

# -------- Compute similarity --------
def get_similarity(job_desc, resume_text):
    vectorizer = TfidfVectorizer(stop_words='english')
    vectors = vectorizer.fit_transform([job_desc, resume_text])
    dense_vectors = cast(Any, vectors).toarray()
    score = cosine_similarity(dense_vectors[0:1], dense_vectors[1:2])
    return round(float(score[0][0]) * 100, 2)

# -------- Home route --------
@app.route("/", methods=["GET", "POST"])
def index():
    results = []

    if request.method == "POST":
        job_desc = request.form["job_description"]
        files = request.files.getlist("resumes")

        for file in files:
            if file:
                original_name = file.filename or ""
                safe_name = secure_filename(original_name)
                if not safe_name:
                    continue

                file_path = os.path.join(UPLOAD_FOLDER, safe_name)
                file.save(file_path)

                resume_text = read_resume(file_path)
                score = get_similarity(job_desc, resume_text)

                results.append({
                    "name": safe_name,
                    "score": score
                })

        # Sort by score
        results = sorted(results, key=lambda x: x["score"], reverse=True)

    return render_template("index.html", results=results)

if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True)   

