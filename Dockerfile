FROM python:3.13-slim-bookworm
LABEL maintainer="Freelancercrib API"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY ./requirements.txt /requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /requirements.txt

RUN mkdir /app
WORKDIR /app
COPY . /app

RUN adduser --disabled-password --no-create-home django-user
USER django-user
