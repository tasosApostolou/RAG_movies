#!/bin/bash
set -e

# Περιμένουμε να σηκωθεί η MySQL (αντικατάστησε το db με το όνομα του service στο compose)
echo "Waiting for MySQL to start..."
while ! nc -z db 3306; do
  sleep 0.5
done
echo "MySQL is up and running!"

# execute admin script (χρησιμοποιώντας το uv run για να έχει τα dependencies)
echo "Running database initialization and admin creation..."
# uv run --no-project python -m app.init_admin
uv run --frozen python -m app.init_admin

# echo "Running database initialization and admin creation..."
# uv run python -m app.init_admin

# Εκκίνηση της κύριας εφαρμογής FastAPI
# echo "Starting FastAPI application..."
# exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
echo "Starting FastAPI application..."
# exec uv run --no-project uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
exec uv run --frozen uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload




# #!/bin/bash
# set -e

# echo "Waiting for MySQL to start..."

# while ! nc -z db 3306; do
#     sleep 0.5
# done

# echo "MySQL is up!"

# echo "Running database initialization..."
# uv run --frozen python -m app.init_admin

# echo "Starting FastAPI..."
# exec uv run --frozen uvicorn app.main:app \
#     --host 0.0.0.0 \
#     --port 8000