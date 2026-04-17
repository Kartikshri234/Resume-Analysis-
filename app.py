from flask import Flask, abort, render_template, request, send_file
import os
import csv
import json
import re
import sqlite3
from datetime import datetime
from io import BytesIO, StringIO
from typing import Any, cast
import fitz  # PyMuPDF
import docx
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from werkzeug.utils import secure_filename
import webbrowser

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
DB_PATH = "screening.db"

SKILL_KEYWORDS = {
    "python", "java", "javascript", "typescript", "c++", "c#", "sql", "mysql", "postgresql",
    "mongodb", "flask", "django", "fastapi", "react", "angular", "node", "node.js", "html",
    "css", "bootstrap", "git", "github", "rest", "api", "docker", "kubernetes", "aws", "azure",
    "gcp", "linux", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "power bi",
    "excel", "tableau", "nlp", "machine learning", "deep learning", "data analysis", "oop",
}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS screening_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                job_description TEXT NOT NULL,
                candidate_count INTEGER NOT NULL,
                results_json TEXT NOT NULL
            )
            """
        )

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


def normalize_text(text):
    return re.sub(r"\s+", " ", text.lower()).strip()


def extract_required_skills(job_desc):
    normalized_jd = normalize_text(job_desc)
    return sorted(skill for skill in SKILL_KEYWORDS if skill in normalized_jd)


def get_skill_coverage(job_desc, resume_text):
    required_skills = extract_required_skills(job_desc)
    normalized_resume = normalize_text(resume_text)
    matched_skills = sorted(skill for skill in required_skills if skill in normalized_resume)
    missing_skills = sorted(skill for skill in required_skills if skill not in normalized_resume)

    if not required_skills:
        return matched_skills, missing_skills, 0.0

    coverage_score = round((len(matched_skills) / len(required_skills)) * 100, 2)
    return matched_skills, missing_skills, coverage_score


# -------- Compute similarity --------
def get_similarity(job_desc, resume_text):
    if not job_desc.strip() or not resume_text.strip():
        return 0.0

    vectorizer = TfidfVectorizer(stop_words='english')
    vectors = vectorizer.fit_transform([job_desc, resume_text])
    dense_vectors = cast(Any, vectors).toarray()
    score = cosine_similarity(dense_vectors[0:1], dense_vectors[1:2])
    return round(float(score[0][0]) * 100, 2)


def get_recommendation(overall_score):
    if overall_score >= 75:
        return "Shortlist"
    if overall_score >= 50:
        return "Consider"
    return "Reject"


def save_session(job_desc, results):
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO screening_sessions (created_at, job_description, candidate_count, results_json)
            VALUES (?, ?, ?, ?)
            """,
            (created_at, job_desc, len(results), json.dumps(results)),
        )
        return int(cursor.lastrowid)


def get_recent_sessions(limit=8):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, created_at, candidate_count
            FROM screening_sessions
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def load_session(session_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT id, created_at, job_description, results_json
            FROM screening_sessions
            WHERE id = ?
            """,
            (session_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "job_description": row["job_description"],
        "results": json.loads(row["results_json"]),
    }


def get_latest_session_or_404():
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT id
            FROM screening_sessions
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    if row is None:
        abort(404, description="No screening session found yet.")

    loaded = load_session(int(row[0]))
    if loaded is None:
        abort(404, description="No screening session found yet.")
    return loaded


def clip_text(value, max_len):
    if len(value) <= max_len:
        return value
    return value[: max_len - 3] + "..."


init_db()


@app.route("/export/csv")
def export_csv():
    loaded = get_latest_session_or_404()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Rank", "File Name", "Overall Score", "Semantic Score", "Skill Coverage",
        "Matched Skills", "Missing Skills", "Recommendation"
    ])

    for rank, item in enumerate(loaded["results"], start=1):
        writer.writerow([
            rank,
            item["name"],
            item["score"],
            item["semantic_score"],
            item["skill_coverage_score"],
            ", ".join(item["matched_skills"]),
            ", ".join(item["missing_skills"]),
            item["recommendation"],
        ])

    memory_file = BytesIO(output.getvalue().encode("utf-8"))
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"screening_results_session_{loaded['id']}.csv",
    )


@app.route("/export/pdf")
def export_pdf():
    loaded = get_latest_session_or_404()
    memory_file = BytesIO()
    pdf = canvas.Canvas(memory_file, pagesize=A4)
    page_width, page_height = A4
    x = 40
    y = page_height - 40

    pdf.setTitle("AI Resume Screening Report")
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(x, y, "AI Resume Screening Report")
    y -= 20
    pdf.setFont("Helvetica", 10)
    pdf.drawString(x, y, f"Session ID: {loaded['id']}")
    y -= 14
    pdf.drawString(x, y, f"Created At: {loaded['created_at']}")
    y -= 18

    for rank, item in enumerate(loaded["results"], start=1):
        if y < 120:
            pdf.showPage()
            y = page_height - 40
            pdf.setFont("Helvetica", 10)

        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(x, y, f"{rank}. {clip_text(item['name'], 65)}")
        y -= 14
        pdf.setFont("Helvetica", 10)
        pdf.drawString(x, y, f"Overall: {item['score']}% | Semantic: {item['semantic_score']}% | Skill Coverage: {item['skill_coverage_score']}%")
        y -= 14
        pdf.drawString(x, y, f"Recommendation: {item['recommendation']}")
        y -= 14
        pdf.drawString(x, y, f"Matched Skills: {clip_text(', '.join(item['matched_skills']) or 'None', 95)}")
        y -= 14
        pdf.drawString(x, y, f"Missing Skills: {clip_text(', '.join(item['missing_skills']) or 'None', 95)}")
        y -= 18

    pdf.save()
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"screening_results_session_{loaded['id']}.pdf",
    )

# -------- Home route --------
@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    job_desc = ""
    selected_session = None

    if request.method == "POST":
        job_desc = request.form["job_description"]
        files = request.files.getlist("resumes")
        required_skills = extract_required_skills(job_desc)

        for file in files:
            if file:
                original_name = file.filename or ""
                safe_name = secure_filename(original_name)
                if not safe_name:
                    continue

                file_path = os.path.join(UPLOAD_FOLDER, safe_name)
                file.save(file_path)

                resume_text = read_resume(file_path)
                semantic_score = get_similarity(job_desc, resume_text)
                matched_skills, missing_skills, skill_coverage_score = get_skill_coverage(job_desc, resume_text)
                overall_score = round((0.7 * semantic_score) + (0.3 * skill_coverage_score), 2)
                recommendation = get_recommendation(overall_score)

                results.append({
                    "name": safe_name,
                    "score": overall_score,
                    "semantic_score": semantic_score,
                    "skill_coverage_score": skill_coverage_score,
                    "required_skills": required_skills,
                    "matched_skills": matched_skills,
                    "missing_skills": missing_skills,
                    "recommendation": recommendation,
                })

        # Sort by score
        results = sorted(results, key=lambda x: x["score"], reverse=True)
        if results:
            selected_session = save_session(job_desc, results)

    session_id = request.args.get("session_id")
    if request.method == "GET" and session_id:
        loaded = load_session(int(session_id)) if session_id.isdigit() else None
        if loaded is not None:
            job_desc = loaded["job_description"]
            results = loaded["results"]
            selected_session = loaded["id"]

    recent_sessions = get_recent_sessions()

    return render_template(
        "index.html",
        results=results,
        job_desc=job_desc,
        recent_sessions=recent_sessions,
        selected_session=selected_session,
        page_title="Home",
    )


@app.route("/project")
def project_page():
    stats = {
        "known_skills": len(SKILL_KEYWORDS),
        "recent_sessions": len(get_recent_sessions()),
        "uploaded_files": len(os.listdir(UPLOAD_FOLDER)) if os.path.exists(UPLOAD_FOLDER) else 0,
    }
    return render_template("project.html", stats=stats, page_title="Project")


@app.route("/user")
def user_page():
    quick_steps = [
        "Open Home and paste a detailed job description.",
        "Upload multiple PDF/DOCX resumes.",
        "Click Analyze Matches to generate ranked results.",
        "Review skill gaps and export CSV/PDF reports.",
    ]
    return render_template("user.html", quick_steps=quick_steps, page_title="User Guide")


@app.route("/contact", methods=["GET", "POST"])
def contact_page():
    submitted = False
    form_data = {"name": "", "email": "", "message": ""}

    if request.method == "POST":
        form_data = {
            "name": request.form.get("name", "").strip(),
            "email": request.form.get("email", "").strip(),
            "message": request.form.get("message", "").strip(),
        }
        submitted = all(form_data.values())

    return render_template(
        "contact.html",
        submitted=submitted,
        form_data=form_data,
        page_title="Contact",
    )

if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True)

