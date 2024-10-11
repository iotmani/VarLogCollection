FROM python:3.12.4-alpine

ADD log_collection log_collection

RUN pip install Flask==3.0.3

ENTRYPOINT [ "flask", "--app", "log_collection.app", "run", "--host=0.0.0.0", "--port=5100" ]