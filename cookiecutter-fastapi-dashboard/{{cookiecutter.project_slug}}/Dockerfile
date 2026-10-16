FROM python:{{ cookiecutter.python_version }}-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY requirements.txt ./
RUN uv venv .venv && \
    . .venv/bin/activate && \
    uv pip install -r requirements.txt

COPY . .

EXPOSE {{ cookiecutter.api_port }}

# .env injecté via variables d'environnement Docker/K8s — jamais copié (cf. .dockerignore)
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "{{ cookiecutter.api_port }}"]
