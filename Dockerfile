FROM python:3.12-slim
WORKDIR /usr/src/app

COPY pyproject.toml .
COPY *.py .
COPY modules/ modules/

RUN pip install --no-cache-dir .
CMD ["python", "/usr/src/app/main.py"]