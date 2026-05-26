FROM python:3.14-slim
WORKDIR /usr/src/app

COPY pyproject.toml .
# config.yml is optional: bake it in by placing it in the build context, or leave it out and
# mount one at runtime. The bracket glob skips it silently when absent instead of failing the
# build, and *.py guarantees the COPY always has at least one matching source.
COPY *.py config.ym[l] ./
COPY modules/ modules/

RUN pip install --no-cache-dir .
RUN test -f config.yml || echo "WARNING: no config.yml baked into image; mount one to /usr/src/app/config.yml at runtime or the bot will exit on startup."
CMD ["python", "/usr/src/app/main.py"]