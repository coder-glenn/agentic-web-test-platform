FROM mcr.microsoft.com/playwright/python:v1.46.0-focal
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 3000
CMD ["uvicorn", "executor_service:app", "--host", "0.0.0.0", "--port", "3000"]
