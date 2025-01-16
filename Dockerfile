FROM python:3.12-alpine
EXPOSE 8080
WORKDIR /orchestrator
COPY ./requirements.txt /orchestrator/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /orchestrator/requirements.txt
COPY ./app /orchestrator/app
ENTRYPOINT ["fastapi", "run", "app/main.py", "--port"]
CMD ["8080"]