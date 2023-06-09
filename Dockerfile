FROM python:3.11-slim-buster

# folder to put app in
WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

# copy everything to the app folder
COPY . .

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]