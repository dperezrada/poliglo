FROM python:2.7

ADD backend/setup.py /src/backend/
WORKDIR /src/backend
RUN python setup.py develop

EXPOSE 9015
CMD ["python", "poliglo_server/__init__.py"]