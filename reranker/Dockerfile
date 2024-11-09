FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8089

CMD ["uvicorn", "inference:app", "--host", "0.0.0.0", "--port", "8089"]

