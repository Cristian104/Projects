# cvManager — AI-Powered CV & Job Application Assistant

`cvManager` is an AI-powered job application assistant and CV matching dashboard built with **FastAPI**, **Gemini 3.6 Flash**, and **Jinja2**. It automatically fetches live job offers, ranks job matches against a candidate profile using AI, generates tailored cover letters (PL/EN), packages customized application ZIPs (.docx, .pdf, candidate CV), and tracks application history.

---

## 🌟 Key Features

- 📄 **Candidate Profile Parsing**: Automatically parses candidate CVs (`.pdf`, `.docx`) into structured profile JSON.
- 🎯 **AI Job Match Ranking**: Evaluates job descriptions against candidate qualifications using Gemini AI, scoring suitability, key highlights, and match reasoning.
- ✉️ **Tailored Cover Letter Generation**: Generates full, un-truncated cover letters in Polish or English tailored to specific roles and company profiles.
- 📦 **Application Package Builder**: Packages customized cover letters (`.docx` & `.pdf`) along with candidate CV into a single downloadable `.zip` package.
- 📊 **Tracking & CSV Export**: Track application lifecycle (`new`, `viewed`, `applied`, `dismissed`) with exportable CSV history.
- 🌐 **Web Dashboard UI**: Clean Jinja2/HTML/JS frontend interface for browsing, filtering, generating letters, and downloading packages.

---

## 🏗️ Architecture & Stack

- **Backend**: Python 3.11, FastAPI, Uvicorn, Pydantic
- **AI Integration**: Google Gemini 3.6 Flash (`google-generativeai` / HTTP requests)
- **Document Processing**: `pypdf`, `python-docx`, `fpdf2`, `beautifulsoup4`
- **Containerization**: Docker, Docker Compose (exposing port `8010:8000`)

---

## 🚀 Environment & Setup

### Environment Variables (`.env`)

Create a `.env` file in the root of `cvManager` (based on `.env.example`):

```env
# Gemini API Key (Required for AI matching & cover letter generation)
GEMINI_API_KEY=your_gemini_api_key_here

# Candidate CV File Path (Optional, defaults to CV_KAMILA_DREWNIAK.pdf)
CV_FILE_PATH=CV_KAMILA_DREWNIAK.pdf
```

---

## 🛠️ Local Development

### 1. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Application

```bash
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## 🐳 Docker & Production Deployment

### Docker Build & Run

```bash
docker compose up -d --build
```
The application will be accessible on host port **`8010`** (`http://localhost:8010`).

---

## 🔌 API Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Main Dashboard UI |
| `GET` | `/api/profile` | Returns parsed candidate profile |
| `GET` | `/api/jobs` | Get ranked jobs (`?scope=all\|local\|country`, `?work_mode=all\|hybrid\|remote`, `?refresh=true`) |
| `POST` | `/api/jobs/{job_id}/status` | Update job tracking status (`viewed`, `applied`, `dismissed`) |
| `GET` | `/api/jobs/{job_id}/cover-letter` | Generate AI cover letter (`?lang=pl\|en`) |
| `POST` | `/api/jobs/extend-search` | Trigger live job search fetch |
| `GET` | `/api/download-package/{job_id}` | Download ZIP application package (`?lang=pl\|en&include_cv=true`) |
| `GET` | `/api/export-csv` | Export application history to CSV |
| `POST` | `/api/generate-blurb` | Custom job description AI evaluation on demand |
