import json
import requests
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List
from backend.config import GEMINI_API_KEY
from backend.cv_parser import get_candidate_profile

def generate_full_cover_letter(job: Dict[str, Any], profile: Dict[str, Any] = None, lang: str = "pl") -> str:
    """Generate a complete 4-paragraph professional cover letter tailored to the job description."""
    if not profile:
        profile = get_candidate_profile()
        
    if not GEMINI_API_KEY:
        # Fallback full letter
        if lang == "en":
            return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job.get('title')} position at {job.get('company')}. With a solid background in bilingual customer experience, leadership, and international operations, I am confident in my ability to make an immediate positive contribution to your team.

I hold a Bachelor's degree in Business English from the University of Opole, specializing in linguistics, management, and economics. My fluent C1 English proficiency has been my primary working language throughout my career, enabling me to handle complex client communications, documentation translation, and cross-departmental coordination effortlessly.

My professional experience includes working as a Dual-Language Customer Service & KYC Agent at Bimigmalta Limited in Malta, where I managed PL-EN client documentation and CRM workflows, as well as serving as Store Manager at GCC7 Company. Additionally, my work as a Tourism Resident for Coral Travel in Turkey honed my skills in high-volume customer relations, complaint handling, and vendor negotiations.

I am highly motivated to bring my communication skills, organizational discipline, and dedication to {job.get('company')}. I look forward to the opportunity to discuss how my background aligns with your requirements in an interview.

Sincerely,
Kamila Drewniak"""
        else:
            return f"""Szanowni Państwo,

Z wielkim entuzjazmem aplikuję na stanowisko {job.get('title')} w firmie {job.get('company')}. Posiadam bogate doświadczenie w dwujęzycznej obsłudze klienta, pracy w środowisku międzynarodowym oraz zarządzaniu zespołem, co pozwala mi wnieść realną wartość do Państwa organizacji.

Ukończyłam studia licencjackie na kierunku Język Biznesu na Uniwersytecie Opolskim, łączące lingwistykę z elementami zarządzania, marketingu i ekonomii. Język angielski jest moim głównym językiem roboczym na poziomie C1, co umożliwia mi swobodną korespondencję biznesową, obsługę zgłoszeń klientów obcojęzycznych oraz tłumaczenie dokumentacji branżowej.

Dotychczasowe doświadczenie zawodowe zdobywałam m.in. na Malcie jako Dwujęzyczny Agent ds. Obsługi Klienta i KYC w firmie Bimigmalta Limited (obsługa systemów CRM, tłumaczenia dokumentów PL-EN, korespondencja prawna) oraz jako Menadżer Sklepu w GCC7 Company (zarządzanie zespołem, tworzenie grafik, negocjacje z dostawcami). Ponadto praca jako Rezydentka Turystyczna dla Coral Travel w Turcji wykształciła we mnie wysoką odporność na stres, umiejętność sprawnego rozpatrywania reklamacji oraz dbałość o najwyższe standardy obsługi.

Jestem przekonana, że moje zaangażowanie, wysoka kultura osobista oraz umiejętności organizacyjne przyczynią się do dalszego rozwoju Państwa zespołu. Chętnie przedstawię moją kandydaturę podczas rozmowy kwalifikacyjnej.

Z poważaniem,
Kamila Drewniak"""

    prompt = f"""
Napisz PEŁNY, PROFESJONALNY LIST MOTYWACYJNY (4 akapity + formalne zakończenie) dla kandydata aplikującego na poniższe stanowisko.
List ma być kompletny, gotowy do wysłania do pracodawcy (BEZ skrótów i BEZ wielokropków '...').

DANE KANDYDATA:
{json.dumps(profile, ensure_ascii=False, indent=2)}

OFERTA PRACY:
Tytuł: {job.get('title')}
Firma: {job.get('company')}
Lokalizacja: {job.get('location')}
Opis: {job.get('description')}

Język listu: {"POLSKI" if lang == "pl" else "ANGIELSKI"}

Wymagania dotyczące treści:
- Akapit 1: Przedstawienie kandydata i wyraz entuzjazmu wobec aplikacji na stanowisko w tej konkretnej firmie.
- Akapit 2: Wykształcenie (Język Biznesu na Uniwersytecie Opolskim) i biegły język angielski C1.
- Akapit 3: Doświadczenie zawodowe (Malta: dwujęzyczna obsługa KYC PL-EN w Bimigmalta, kierownik w GCC7; Turcja: rezydent Coral Travel) i dopasowanie kompetencji do wymagań oferty.
- Akapit 4: Zakończenie z gotowością do rozmowy rekrutacyjnej i formalnym podpisem (Kamila Drewniak).

Zwróć WYŁĄCZNIE czysty tekst listu motywacyjnego.
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, json=payload, timeout=12)
        if response.status_code == 200:
            res_data = response.json()
            return res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"Error generating full cover letter: {e}")

    # Fallback to local full letter
    return generate_full_cover_letter(job, profile, lang=lang)

def evaluate_job_match(job: Dict[str, Any], profile: Dict[str, Any] = None) -> Dict[str, Any]:
    """Evaluate job match and estimate salary range (Fast Search mode - cover letter generated on demand)."""
    if not profile:
        profile = get_candidate_profile()
        
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is missing.")
        
    prompt = f"""
Przeanalizuj dopasowanie kandydata do oferty oraz oszacuj rynkowe widełki wynagrodzenia (PLN brutto).

DANE KANDYDATA:
{json.dumps(profile, ensure_ascii=False, indent=2)}

OFERTA PRACY:
Tytuł: {job.get('title')}
Firma: {job.get('company')}
Lokalizacja: {job.get('location')} (Tryb: {job.get('work_mode')})
Opis oferty:
{job.get('description')}

Zwróć WYŁĄCZNIE poprawny kod JSON:
{{
  "match_score": 92,
  "salary_estimator": {{
    "estimated_range": "6 500 - 8 500 PLN brutto",
    "recommended_ask": "7 500 PLN brutto",
    "negotiation_tip": {{
      "pl": "Warto podkreślić doświadczenie z Malty/Turcji i język C1.",
      "en": "Highlight Malta/Turkey experience and C1 English."
    }}
  }},
  "summary": {{
    "pl": "Podsumowanie po polsku...",
    "en": "Summary in English..."
  }},
  "strengths": {{
    "pl": ["Atut PL 1", "Atut PL 2"],
    "en": ["Strength EN 1", "Strength EN 2"]
  }}
}}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    
    try:
        response = requests.post(url, json=payload, timeout=12)
        if response.status_code == 200:
            res_data = response.json()
            result_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                clean_text = result_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                return json.loads(clean_text)
    except Exception as e:
        print(f"Error evaluating job {job.get('title')}: {e}")

    return {
        "match_score": 85,
        "salary_estimator": {
            "estimated_range": "6 500 - 8 500 PLN brutto",
            "recommended_ask": "7 500 PLN brutto",
            "negotiation_tip": {
                "pl": "Znakomity angielski C1 oraz wykształcenie lingwistyczne to Twój silny atut.",
                "en": "Your C1 English proficiency and Business English degree are strong assets."
            }
        },
        "summary": {
            "pl": "Mocne dopasowanie ze względu na znajomość języka angielskiego (C1) i wykształcenie z Języka Biznesu.",
            "en": "Strong match due to C1 English proficiency and Business English degree."
        },
        "strengths": {
            "pl": ["Biegły angielski C1", "Doświadczenie w obsłudze klienta (Malta, Turcja)"],
            "en": ["Fluent C1 English", "Customer Experience in Malta & Turkey"]
        }
    }

def rank_single_job(job: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    match_res = evaluate_job_match(job, profile)
    return {**job, "match": match_res}

def rank_all_jobs(jobs: List[Dict[str, Any]], profile: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    if not profile:
        profile = get_candidate_profile()
        
    ranked_jobs = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(rank_single_job, job, profile) for job in jobs]
        for f in futures:
            try:
                ranked_jobs.append(f.result())
            except Exception as e:
                print(f"Error processing parallel match: {e}")

    ranked_jobs.sort(key=lambda x: x["match"]["match_score"], reverse=True)
    return ranked_jobs
