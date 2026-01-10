FROM python:3.11-slim

WORKDIR /app

# 필수 라이브러리 설치를 위한 준비 (requirements.txt 생성 후 주석 해제 예정)
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY ./app ./app

# 실행 (FastAPI)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]