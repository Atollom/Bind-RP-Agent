FROM python:3.12-slim

# Evitar escritura de bytecode de python y forzar stdout sin buffer
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production

WORKDIR /app

# Crear usuario no root para mayor seguridad
RUN addgroup --system appgroup && adduser --system --group appuser

# Instalar dependencias (solo las de requirements)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar todo el código backend
COPY . .

# Cambiar permisos y cambiar a usuario sin privilegios
RUN chown -R appuser:appgroup /app
USER appuser

# Exponer el puerto interno de fastapi
EXPOSE 8000

# Lanzar Uvicorn
# 2 workers = estable en 512MB RAM (Render free). Subir a 4 en plan pago.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]
