FROM python:2.7

RUN apt-get update && apt-get install -y supervisor && service supervisor start

RUN pip install poliglo
WORKDIR /src/deployment/scripts
CMD ["./start_workers.sh"]