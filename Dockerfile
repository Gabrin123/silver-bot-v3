FROM python:3.11-slim


WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY silver_chart_bot.py .

CMD ["python", "silver_chart_bot.py"]
