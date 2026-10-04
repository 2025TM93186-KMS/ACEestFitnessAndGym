# Multi-stage optimized, lightweight baseline image
FROM python:3.10-alpine

WORKDIR /app

# Install native system build requirements and clear package manager cache immediately
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Remove temporary build dependencies to minimize image layer size footprint
RUN apk del .build-deps

COPY . .



CMD ["python", "app.py"]
