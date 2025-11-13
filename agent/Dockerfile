FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x ./healthcheck_wait.sh || true
EXPOSE 8000
CMD ["/bin/sh", "-c", "./healthcheck_wait.sh && uvicorn agent_enhanced_full:app --host 0.0.0.0 --port 8000"]
