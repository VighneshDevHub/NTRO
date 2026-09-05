FROM python:3.12-slim

WORKDIR /app

# build-essential needed for cryptography's C extensions on some
# platforms/architectures during pip install.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# In production, drop --reload (this is already the compose default).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
