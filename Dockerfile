FROM python:3.10-slim

WORKDIR /app

RUN pip install flask

COPY . .

CMD ["python", "app.py"]