FROM python:3.12-slim
WORKDIR /usr/src/app

COPY pyproject.toml .
COPY *.py .
COPY config.yml .
COPY modules/ modules/

RUN apt-get update && apt-get install -y --no-install-recommends git
RUN pip install --no-cache-dir .
CMD ["python", "/usr/src/app/main.py"]