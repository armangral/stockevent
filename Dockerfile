FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

ENV PYTHONUNBUFFERED=1

# Install necessary dependencies
RUN apt-get update && apt-get install -y wkhtmltopdf

# Install Celery BEFORE switching users
RUN pip3 install celery

# Create a non-root user
RUN useradd -m celery_user
USER celery_user

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY . /app

EXPOSE 8000
