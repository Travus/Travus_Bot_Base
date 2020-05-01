FROM python:3
WORKDIR /usr/src/app

COPY . .
COPY ./modules ./temp_modules
RUN pip install --no-cache-dir -r requirements.txt
CMD ["sh", "/usr/src/app/start.sh"]