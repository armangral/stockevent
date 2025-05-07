FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy


ENV PYTHONUNBUFFERED=1

# Install necessary dependencies
RUN apt-get update

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY . /app

EXPOSE 8000
