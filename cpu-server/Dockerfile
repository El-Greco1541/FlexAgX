FROM python:3.12-slim
WORKDIR /opt/flexagx
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY flexagx ./flexagx
COPY services ./services
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn","services.gateway:app","--host","0.0.0.0","--port","8000"]
