from dotenv import load_dotenv
import os
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise SystemExit("GEMINI_API_KEY 환경변수가 설정돼 있어야 합니다.")

with genai.Client(api_key=api_key) as client:
    for model in client.models.list():
        label = (
            model.display_name
            or model.description
            or "설명 없음"
        )
        print(f"{model.name}: {label}")
