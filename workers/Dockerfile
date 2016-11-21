FROM python:2.7

RUN pip install poliglo
WORKDIR /src/deployment/scripts
CMD ["./start_workers.sh", "-w=write_numbers_to_file"]