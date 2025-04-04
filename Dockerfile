FROM python:3.12-alpine
WORKDIR /orchestrator

COPY ./requirements.txt /orchestrator/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /orchestrator/requirements.txt

COPY src /orchestrator/app

ENTRYPOINT ["python"]
CMD ["app/main.py"]