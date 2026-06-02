FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV PYTHONPATH=/app/src \
    FLASK_APP=see_the_growth.api.local_web_app:create_app \
    SEE_THE_GROWTH_PORT=5000

EXPOSE 5000

CMD ["sh", "-c", "exec python -m flask run --host=0.0.0.0 --port=${SEE_THE_GROWTH_PORT}"]
