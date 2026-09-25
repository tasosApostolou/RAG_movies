FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONPATH=/app UV_SYSTEM_PYTHON=1 UV_PROJECT_ENVIRONMENT=/opt/venv

# UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

# Εγκατάσταση του netcat (χρειάζεται για να ελέγξουμε αν άνοιξε η MySQL)
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . .


# Μετατροπή του entrypoint script σε εκτελέσιμο
# RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]







# # Χρήση της επίσημης εικόνας του uv με Python 3.12 (ή όποια έκδοση έχεις)
# FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# # Ρύθμιση του uv να μην δημιουργεί virtual environment μέσα στο container, 
# # αλλά να εγκαθιστά τα πακέτα απευθείας στο σύστημα (system Python) του Docker.
# ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# # Ορισμός φακέλου εργασίας
# WORKDIR /app

# # Αντιγραφή ΜΟΝΟ των αρχείων ρυθμίσεων για να εκμεταλλευτούμε το Docker Caching
# COPY pyproject.toml uv.lock ./

# # Εγκατάσταση των dependencies. 
# # Το --no-install-project λέει στο uv να μην ψάξει να εγκαταστήσει τον ίδιο τον κώδικά μας ως πακέτο ακόμα.
# RUN uv sync --frozen --no-install-project --no-dev

# # Αντιγραφή του υπόλοιπου κώδικα της εφαρμογής (συμπεριλαμβανομένου του φακέλου app/)
# COPY . .

# # Άνοιγμα της πόρτας 8000
# EXPOSE 8000

# # Εκτέλεση της εφαρμογής χρησιμοποιώντας τη σωστή διαδρομή app.main:app
# #  Στο Docker βάζουμε host 0.0.0.0 για να δέχεται εξωτερικές συνδέσεις
# CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
