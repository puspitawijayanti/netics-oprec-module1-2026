FROM python:3.11-slim

WORKDIR /src

RUN pip install --no-cache-dir flask

COPY main.py .

EXPOSE 3000

CMD ["python", "main.py"]