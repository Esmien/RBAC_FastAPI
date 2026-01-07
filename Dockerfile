FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .

# прод-версия
#RUN pip install --no-cache-dir --upgrade pip && \
#    pip install --no-cache-dir -r requirements.txt

# дев-версия
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

RUN chmod +x scripts/start.sh

CMD ["./scripts/start.sh"]