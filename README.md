# AI Resume Screening System

A polished Flask web app that ranks uploaded resumes against a job description using TF-IDF vectorization and cosine similarity.

## Why This Project

Recruiters and hiring teams often review many resumes for a single role. This project helps speed up first-level screening by:

- Extracting text from PDF and DOCX resumes
- Comparing each resume to a target job description
- Returning ranked match scores in percentage form

## Live Experience

The UI is optimized for demo/showcase use:

- Clean, responsive multi-page interface
- Drag-and-drop multi-file resume upload
- File chips for selected files
- Real-time character count for job description
- Score bars and sorted ranking cards
- Dedicated pages for Project overview, User guide, and Contact form

## Tech Stack

- Backend: Flask
- NLP/Scoring: scikit-learn (TF-IDF + cosine similarity)
- File parsing:
  - PyMuPDF for PDF
  - python-docx for DOCX
- Frontend: HTML, CSS, JavaScript

## Project Structure

```text
NEW MINOR PROJECT/
|-- app.py
|-- requirements.txt
|-- README.md
|-- static/
|   |-- css/
|   |   `-- style.css
|   `-- js/
|       `-- main.js
|-- templates/
|   |-- base.html
|   |-- contact.html
|   |-- index.html
|   |-- project.html
|   `-- user.html
`-- uploads/
    `-- computer-engineering-resume-example.pdf
```

## Available Pages

- `/` - Home page for resume screening workflow
- `/project` - Project information and live app stats
- `/user` - User guide and recommendation scale
- `/contact` - Frontend form connected to Python backend

## How It Works

1. User submits a job description and uploads one or more resumes.
2. The backend saves files to the `uploads/` directory.
3. Text is extracted from each file:
   - `.pdf` via PyMuPDF
   - `.docx` via python-docx
4. TF-IDF vectors are generated for:
   - Job description
   - Resume text
5. Cosine similarity is computed and converted to a percentage score.
6. Results are sorted in descending order and displayed in ranked cards.

## Supported File Types

- `.pdf`
- `.doc`
- `.docx`

Note: The backend parser currently extracts text from `.pdf` and `.docx` files. `.doc` files are accepted in the UI but may need conversion to `.docx` for best compatibility.

## Setup and Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the app

```bash
python app.py
```

The app runs at:

- http://127.0.0.1:5000

`app.py` is configured to open the URL in your default browser automatically when launched.

## Demo Flow

For a clean demonstration:

1. Start the app.
2. Paste a realistic job description with required skills.
3. Upload 2-5 resumes.
4. Click **Analyze Matches**.
5. Present the ranked output and score bars.

## Security and Implementation Notes

- Uploaded file names are sanitized using Werkzeug `secure_filename`.
- The app currently runs in Flask debug mode for development.
- Uploaded files remain in `uploads/` until removed.

## Potential Enhancements

- Add extraction support for legacy `.doc` files server-side
- Add keyword highlighting in matched resumes
- Add downloadable report (CSV/PDF)
- Add authentication and candidate/job history
- Add model explainability (top matching terms)

## Author

Created by Kartik Shrivastava
