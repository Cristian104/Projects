import os
import json
import pypdf
from google import genai
from backend.config import GEMINI_API_KEY, CV_FILE_PATH

PROFILE_CACHE_FILE = "parsed_profile.json"

def extract_text_from_pdf(pdf_path: str = CV_FILE_PATH) -> str:
    """Extract raw text from PDF CV using pypdf."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"CV file not found: {pdf_path}")
    
    reader = pypdf.PdfReader(pdf_path)
    text_pages = [page.extract_text() for page in reader.pages if page.extract_text()]
    return "\n".join(text_pages)

def parse_cv_with_gemini(cv_text: str) -> dict:
    """Pass CV text to Gemini 3.6 Flash and receive structured candidate profile JSON."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in environment or .env file.")
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
Analyze the following candidate CV written in Polish and output a comprehensive JSON object describing the candidate.
Ensure all key details are captured accurately.

CV Content:
---
{cv_text}
---

Return ONLY a valid JSON object matching this schema:
{{
  "name": "Full Name",
  "headline": "Professional headline summarizing key strengths and experience",
  "location": "City, Country",
  "contact": {{
    "email": "Email address",
    "phone": "Phone number"
  }},
  "work_preferences": {{
    "modes": ["Hybrid", "On-site"],
    "target_roles": ["List 4-6 target roles based on background"],
    "preferred_cities": ["Częstochowa", "Katowice", "Śląsk", "Remote/Hybrid Poland"]
  }},
  "summary": "Concise candidate profile summary in Polish",
  "education": [
    {{
      "institution": "University / School name",
      "degree": "Licencjat / Master / High School",
      "field_of_study": "Field of study",
      "years": "Start - End years"
    }}
  ],
  "experience": [
    {{
      "role": "Job Title",
      "company": "Company Name & Location",
      "dates": "Start - End dates",
      "responsibilities": ["List key duties and achievements"]
    }}
  ],
  "languages": [
    {{
      "language": "Language name",
      "level": "Native / C1 / A2 / etc."
    }}
  ],
  "skills": ["List technical and soft skills"],
  "certifications": ["Driver license, barista courses, etc."]
}}
"""
    
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )
    
    try:
        profile_data = json.loads(response.text)
        return profile_data
    except json.JSONDecodeError:
        # Fallback cleanup if markdown backticks were returned
        clean_text = response.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean_text)

def get_candidate_profile(force_reparse: bool = False) -> dict:
    """Get candidate profile, using cache if available."""
    if not force_reparse and os.path.exists(PROFILE_CACHE_FILE):
        try:
            with open(PROFILE_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    cv_text = extract_text_from_pdf()
    profile = parse_cv_with_gemini(cv_text)
    
    with open(PROFILE_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
        
    return profile

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("Parsing candidate CV...")
    prof = get_candidate_profile(force_reparse=True)
    print(json.dumps(prof, indent=2, ensure_ascii=False))
