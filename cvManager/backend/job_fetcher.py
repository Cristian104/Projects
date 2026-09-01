import os
import json
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from backend.config import DEFAULT_CITY, DEFAULT_COUNTRY

CACHE_FILE = "cached_live_jobs.json"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7'
}

# Multi-source job dataset targeting Częstochowa, Śląsk, and Poland Hybrid
MULTI_SOURCE_SAMPLE_JOBS: List[Dict[str, Any]] = [
    {
        "id": "xkom-101",
        "title": "Customer Service Specialist (E-commerce)",
        "company": "x-kom",
        "location": "Częstochowa",
        "scope": "local",
        "work_mode": "Hybrid",
        "salary": "5,500 - 7,200 PLN brutto",
        "source": "Pracuj.pl",
        "apply_url": "https://www.pracuj.pl/praca/customer-service-specialist-czestochowa-x-kom",
        "published": "Dzisiaj",
        "description": """
Lider branży e-commerce w Polsce poszukuje Specjalisty ds. Obsługi Klienta w centrali w Częstochowie!
Praca hybrydowa (2 dni biuro w Częstochowie, 3 dni praca z domu).

Zakres obowiązków:
- Wielokanałowa obsługa klientów (telefon, e-mail, czat)
- Rozpatrywanie zgłoszeń reklamacyjnych i zapytań dotyczących zamówień
- Praca w systemach CRM i pakiecie biurowym
- Współpraca z działem logistyki i serwisu

Wymagania:
- Komunikatywność, cierpliwość oraz wysoka kultura osobista
- Znajomość języka angielskiego (min. B2/C1)
- Umiejętność sprawnego pisania i pracy pod presją czasu
"""
    },
    {
        "id": "guess-102",
        "title": "Kierownik Sklepu (Store Manager)",
        "company": "Guess Poland - Galeria Jurajska",
        "location": "Częstochowa",
        "scope": "local",
        "work_mode": "On-site",
        "salary": "7,000 - 9,500 PLN brutto",
        "source": "Pracuj.pl",
        "apply_url": "https://www.pracuj.pl/praca/kierownik-sklepu-czestochowa-guess",
        "published": "1 dzień temu",
        "description": """
Międzynarodowa marka modowa Guess poszukuje Kierownika Sklepu w Galerii Jurajskiej w Częstochowie.

Zakres obowiązków:
- Zarządzanie zespołem sprzedawców (rekrutacja, szkolenia, motywowanie)
- Tworzenie grafik czasów pracy i rozliczanie wyników sklepu
- Dbałość o najwyższe standardy obsługi klienta i visual merchandising
- Negocjacje i współpraca z centralą firmy

Wymagania:
- Min. 2 lata doświadczenia w zarządzaniu zespołem w handlu, gastronomi lub turystyce
- Dobra znajomość języka angielskiego
- Prawo jazdy kat. B (mile widziane)
"""
    },
    {
        "id": "fintech-103",
        "title": "Junior KYC & AML Operations Analyst",
        "company": "Revolut / FinCrime Europe",
        "location": "Katowice / Częstochowa (Hybrid)",
        "scope": "country",
        "work_mode": "Hybrid",
        "salary": "7,500 - 10,000 PLN brutto",
        "source": "NoFluffJobs",
        "apply_url": "https://nofluffjobs.com/pl/job/junior-kyc-aml-operations-analyst-katowice",
        "published": "Dzisiaj",
        "description": """
Młodszy Analityk ds. Zgodności Prawnej i KYC/AML w międzynarodowej firmie FinTech.
Oferujemy pracę w trybie hybrydowym z dowolnego miejsca w Polsce (oraz biuro w Katowicach).

Zakres obowiązków:
- Analiza i weryfikacja dokumentów tożsamości klientów indywidualnych i biznesowych (KYC)
- Tłumaczenie dokumentacji klienta (Polski -> Angielski)
- Korespondencja z działem prawnym, ryzyka i obsługą klienta
- Praca w wewnętrznych systemach CRM i z bazami danych compliance

Wymagania:
- Biegły język angielski (min. C1) w mowie i piśmie
- Studia wyższe (lingwistyka, język biznesu, finanse lub prawo)
- Bardzo dobra organizacja pracy i skrupulatność
"""
    },
    {
        "id": "jji-104",
        "title": "Customer Experience Specialist (PL/EN)",
        "company": "Booksy Polska",
        "location": "Polska (Hybrid / Remote)",
        "scope": "country",
        "work_mode": "Hybrid",
        "salary": "6,500 - 8,500 PLN brutto",
        "source": "JustJoin.it",
        "apply_url": "https://justjoin.it/offers/booksy-customer-experience-specialist",
        "published": "2 dni temu",
        "description": """
Booksy poszukuje Specjalisty ds. Relacji z Klientem w zespole Customer Experience.
Praca hybrydowa z elastycznymi godzinami.

Zakres obowiązków:
- Wsparcie użytkowników platformy w Polsce i za granicą
- Pomoc w konfiguracji usług i rozwiązywanie bieżących zgłoszeń
- Tłumaczenie materiałów pomocniczych PL/EN
- Utrzymywanie wysokiego wskaźnika satysfakcji klientów (CSAT)

Wymagania:
- Angielski na poziomie C1
- Doświadczenie w obsłudze klienta lub branży usługowej
- Otwartość i wyrozumiałość w kontakcie z ludźmi
"""
    }
]

SEARCH_CONFIGS = [
    {"keywords": "Customer Service", "location": "Czestochowa, Silesian, Poland", "scope": "local"},
    {"keywords": "Obsługa Klienta", "location": "Czestochowa, Silesian, Poland", "scope": "local"},
    {"keywords": "Store Manager", "location": "Czestochowa, Silesian, Poland", "scope": "local"},
    {"keywords": "Office Coordinator", "location": "Czestochowa, Silesian, Poland", "scope": "local"},
    {"keywords": "KYC Compliance", "location": "Poland", "scope": "country"},
    {"keywords": "Customer Support Hybrid", "location": "Poland", "scope": "country"}
]

def scrape_linkedin_job_details(job_id: str) -> str:
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            desc_div = soup.find('div', class_='show-more-less-html__markup')
            if desc_div:
                return desc_div.text.strip()
    except Exception as e:
        print(f"Error fetching detail {job_id}: {e}")
    return "Szczegóły oferty dostępne na stronie ogłoszenia."

def detect_work_mode(title: str, description: str, location: str) -> str:
    combined = f"{title} {description} {location}".lower()
    if 'hybryd' in combined or 'hybrid' in combined or 'zdaln' in combined or 'remote' in combined:
        return 'Hybrid'
    return 'On-site'

def fetch_live_linkedin_jobs(limit_per_query: int = 2) -> List[Dict[str, Any]]:
    all_jobs: List[Dict[str, Any]] = []
    seen_job_ids = set()

    for cfg in SEARCH_CONFIGS:
        keywords = cfg["keywords"]
        location = cfg["location"]
        search_url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keywords.replace(' ', '%20')}&location={location.replace(' ', '%20')}&start=0"
        
        try:
            res = requests.get(search_url, headers=HEADERS, timeout=6)
            if res.status_code != 200:
                continue

            soup = BeautifulSoup(res.text, 'html.parser')
            job_cards = soup.find_all('li')

            count = 0
            for card in job_cards:
                if count >= limit_per_query:
                    break

                link_elem = card.find('a', class_='base-card__full-link')
                title_elem = card.find('h3', class_='base-search-card__title')
                company_elem = card.find('h4', class_='base-search-card__subtitle')
                loc_elem = card.find('span', class_='job-search-card__location')

                if not (title_elem and company_elem and link_elem):
                    continue

                raw_link = link_elem['href']
                job_id_match = re.search(r'-(\d+)\?', raw_link) or re.search(r'view/(\d+)', raw_link)
                job_id = job_id_match.group(1) if job_id_match else raw_link

                if job_id in seen_job_ids:
                    continue
                seen_job_ids.add(job_id)

                title = title_elem.text.strip()
                company = company_elem.text.strip()
                job_loc = loc_elem.text.strip() if loc_elem else location

                description = scrape_linkedin_job_details(job_id)
                work_mode = detect_work_mode(title, description, job_loc)

                is_local = 'częstochowa' in job_loc.lower() or 'czestochowa' in job_loc.lower()
                scope_tag = "local" if is_local else "country"

                all_jobs.append({
                    "id": f"linkedin-{job_id}",
                    "title": title,
                    "company": company,
                    "location": job_loc,
                    "scope": scope_tag,
                    "work_mode": work_mode,
                    "salary": "Wynagrodzenie do uzgodnienia",
                    "source": "LinkedIn Jobs",
                    "apply_url": raw_link,
                    "published": "Świeża oferta",
                    "description": description
                })
                count += 1
        except Exception as e:
            print(f"Error fetching LinkedIn search {keywords}: {e}")

    # Combine with multi-source offerings (Pracuj.pl, NoFluffJobs, JustJoin.it)
    combined_jobs = all_jobs + MULTI_SOURCE_SAMPLE_JOBS
    
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(combined_jobs, f, ensure_ascii=False, indent=2)

    return combined_jobs

def fetch_jobs(scope: str = "all", work_mode: str = None) -> List[Dict[str, Any]]:
    jobs = []
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                jobs = json.load(f)
        except Exception:
            pass

    if not jobs:
        jobs = fetch_live_linkedin_jobs()

    if scope and scope.lower() == "local":
        jobs = [j for j in jobs if j.get("scope") == "local" or 'częstochowa' in j["location"].lower() or 'czestochowa' in j["location"].lower()]
    elif scope and scope.lower() == "country":
        jobs = [j for j in jobs if j.get("scope") == "country" or ('częstochowa' not in j["location"].lower() and 'czestochowa' not in j["location"].lower())]

    if work_mode and work_mode.lower() != "all":
        jobs = [j for j in jobs if j["work_mode"].lower() == work_mode.lower()]

    return jobs
