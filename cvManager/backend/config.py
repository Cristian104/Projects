import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
CV_FILE_PATH = os.environ.get("CV_FILE_PATH", "CV_KAMILA_DREWNIAK.pdf")
DEFAULT_CITY = "Częstochowa"
DEFAULT_COUNTRY = "Polska"
PREFERRED_WORK_MODES = ["Hybrid", "On-site"]
PREFERRED_ROLES = [
    "Customer Support Specialist PL/EN",
    "KYC / Compliance Agent",
    "Team Leader / Gastronomy Manager",
    "Office / Administrative Coordinator",
    "Hospitality / Tourism Resident"
]
