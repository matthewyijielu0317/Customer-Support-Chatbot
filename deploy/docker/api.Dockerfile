FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml requirements.txt /app/
RUN pip install -r requirements.txt

COPY . /app

EXPOSE 8000
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]


