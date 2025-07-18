# syntax=docker/dockerfile:1.4
FROM --platform=$BUILDPLATFORM python:3.10-alpine AS builder

WORKDIR /charge_bot

COPY requirements.txt /charge_bot
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -U pip && \
    pip install -r requirements.txt

COPY . /charge_bot

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run the application
CMD ["flask", "run"]

