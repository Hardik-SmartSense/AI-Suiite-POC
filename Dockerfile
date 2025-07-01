FROM python:3.12-slim

COPY . .

RUN apt-get update && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY requirements.txt .
RUN pip install -r requirements.txt

EXPOSE 8051:8051

CMD ["streamlit", "run", "main.py", "--server.port=8051"]