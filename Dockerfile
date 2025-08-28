# Phase 1: Build stage avec Poetry pour exporter les dépendances
FROM python:3.13-slim as builder

# Installer Poetry et le plugin d'export
RUN pip install poetry poetry-plugin-export

# Configurer Poetry pour ne pas créer d'environnement virtuel
ENV POETRY_VENV_IN_PROJECT=false
ENV POETRY_NO_INTERACTION=1

# Copier les fichiers de configuration Poetry
WORKDIR /app
COPY pyproject.toml poetry.lock ./

# Exporter les dépendances vers requirements.txt
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Phase 2: Image finale pour l'exécution
FROM python:3.13-slim

# Variables d'environnement Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Répertoire de travail
WORKDIR /app

# Copier requirements.txt depuis la phase de build
COPY --from=builder /app/requirements.txt .

# Installer les dépendances système et Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*

# Copier le code source
COPY src/ ./src/

# Exposer le port
EXPOSE 8000

# Lancer l'application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
