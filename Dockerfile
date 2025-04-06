FROM python:3.12-alpine

COPY ./requirements.txt /orchestrator/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /orchestrator/requirements.txt

COPY src /orchestrator/src

EXPOSE 8080
WORKDIR /orchestrator
ENTRYPOINT ["fastapi", "run", "src/main.py", "--port", "8080"]