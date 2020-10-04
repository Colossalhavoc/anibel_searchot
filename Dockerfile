FROM python:3

RUN mkdir -p /usr/src/app/

WORKDIR /usr/src/app

COPY main.py /usr/src/app/main.py
COPY requirements.txt /usr/src/app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "./main.py"]