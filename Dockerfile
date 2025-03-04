FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

ENV PYTHONUNBUFFERED=1
# RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y wkhtmltopdf


WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install --upgrade pip

RUN pip3 install -r requirements.txt

COPY . /app

EXPOSE 8000
