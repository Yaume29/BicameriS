FROM python:3.11-slim

WORKDIR /aetheris

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p memory agents tools workspace

RUN useradd -m -u 1000 aetheris
RUN chown -R aetheris:aetheris /aetheris
USER aetheris

ENV LM_STUDIO_URL=http://host.docker.internal:1234

CMD ["python", "-c", "import interface"]