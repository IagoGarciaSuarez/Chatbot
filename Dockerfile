# syntax=docker/dockerfile:1
FROM python:3.8-slim-buster
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY  {*agent.py, credentials.json, requirements.txt, run_agent.sh} ./
CMD ./run_agent.sh