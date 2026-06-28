import os
from dotenv import load_dotenv

load_dotenv()

Gemini_API = os.getenv("GEMINI_API_KEY", "")
