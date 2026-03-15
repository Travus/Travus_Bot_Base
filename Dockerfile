FROM python:3.14-slim
WORKDIR /usr/src/app

COPY pyproject.toml .
COPY *.py .
COPY config.yml .
COPY modules/ modules/

RUN pip install --no-cache-dir .
CMD ["python", "/usr/src/app/main.py"]